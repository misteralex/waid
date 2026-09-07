"""
@file waid_shared.py
@brief serves as the core utility and data processing engine for the Weather-AI project. It acts as a bridge between 
       raw meteorological data and machine learning pipelines by centralizing time-series resampling, astronomical 
       clear-sky calculations, and hardware-specific sensor calibration guardrails
@author AF
@date 2026
"""

import numpy as np
import pandas as pd
from datetime import datetime
import sqlite3
from pathlib import Path
from loguru import logger
import json
from boot import WaidBoot, WError, WaidExit

def calculate_theoretical_solar_radiation(
    timestamps: np.ndarray, 
    lat: float = None, 
    lon: float = None, 
    local_tz: str = None
) -> np.ndarray:
    """
    Computes theoretical clear-sky solar radiation based on UTC time of day,
    day of the year, and geographical coordinates to prevent daylight saving time shifts.

    Args:
        timestamps (np.ndarray): Array of timestamps.
        lat (float): Latitude of the station.
        lon (float): Longitude of the station.
        local_tz (str): Local timezone for localization.

    Returns:
        np.ndarray: Theoretical solar radiation values in W/m^2.
    """
    solar_rad = []
    
    dt_index = pd.to_datetime(timestamps)
    
    if dt_index.tz is None:
        dt_index = dt_index.tz_localize(local_tz, nonexistent='shift_forward').tz_convert("UTC")
    else:
        dt_index = dt_index.tz_convert("UTC")

    for dt in dt_index:
        hour = dt.hour + dt.minute / 60.0
        day_of_year = dt.dayofyear
        
        declination = 23.45 * np.sin(np.radians(360.0 * (284 + day_of_year) / 365.0))
        
        longitude_correction = (lon / 15.0)
        hour_angle = 15.0 * (hour - 12.0 + longitude_correction)
        
        lat_rad = np.radians(lat)
        dec_rad = np.radians(declination)
        ha_rad = np.radians(hour_angle)
        
        sin_elevation = (np.sin(lat_rad) * np.sin(dec_rad) + 
                         np.cos(lat_rad) * np.cos(dec_rad) * np.cos(ha_rad))
        
        elevation_angle = np.arcsin(np.clip(sin_elevation, -1.0, 1.0))
        
        if elevation_angle > 0:
            max_solar = 1000.0 * np.sin(elevation_angle)
            solar_rad.append(max(0.0, max_solar))
        else:
            solar_rad.append(0.0)
            
    return np.array(solar_rad, dtype=float)


def fetch_and_resample_ecowitt(env, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Extracts Ecowitt raw data, applies type casting, resampling, and bounded interpolation.

    Args:
        env (WaidBoot): Environment configuration.
        start_date (str): Start window for extraction.
        end_date (str): End window for extraction.

    Returns:
        pd.DataFrame: Processed hourly sensor data.
    """
    logger.info(f"Connecting to Ecowitt Database: {env.waid_db}")
    if not Path(env.waid_db).exists():
        raise RuntimeError(f"WAID DB file not found at: {env.waid_db}")

    try:
        logger.info(f"Querying Ecowitt DB for window: [{start_date}] to [{end_date}]")
        with sqlite3.connect(env.waid_db) as conn:
            query = f"""
                SELECT
                    timestamp, 
                    outdoor_temperature_c, 
                    abs_pressure_hpa, 
                    outdoor_humidity,
                    wind_m_s,
                    solar_rad_w_m2,
                    hourly_rain_mm
                FROM {env.ecowitt_table}
                WHERE timestamp >= ? AND timestamp <= ?
            """
            df_eco_raw = pd.read_sql_query(query, conn, params=(start_date, end_date))

    except Exception as e:
        raise RuntimeError(f"Database extraction or SQL query failure: {e}")

    if df_eco_raw.empty:
        raise RuntimeError("No local station records retrieved from database for the specified window.")

    target_tz = env.tz_timezone
    df_eco_raw["timestamp"] = pd.to_datetime(df_eco_raw["timestamp"], utc=True).dt.tz_convert(target_tz).dt.tz_localize(None)

    target_numeric_fields = [
        "outdoor_temperature_c",
        "abs_pressure_hpa",
        "outdoor_humidity",
        "wind_m_s",
        "solar_rad_w_m2",
        "hourly_rain_mm",
    ]
    for field in target_numeric_fields:
        if field in df_eco_raw.columns:
            df_eco_raw[field] = pd.to_numeric(df_eco_raw[field], errors="coerce")

    resample_freq = f"{env.resample_interval_min} min"
    logger.info(f"Resampling local telemetry into {resample_freq} synchronized slots...")

    agg_rules = {
        "outdoor_temperature_c": "mean",
        "abs_pressure_hpa": "mean",
        "outdoor_humidity": "mean",
        "wind_m_s": "mean",
        "solar_rad_w_m2": "mean",
        "hourly_rain_mm": "max",
    }
    present_rules = {col: agg for col, agg in agg_rules.items() if col in df_eco_raw.columns}

    df_eco_hourly = (
        df_eco_raw.resample(resample_freq, on="timestamp")
        .agg(present_rules)
    )

    max_steps = int((env.max_interpolate_hours * 60) / env.resample_interval_min)
    if max_steps > 0:
        logger.info(
            f"Applying bounded time interpolation (max threshold: {env.max_interpolate_hours}h / {max_steps} steps)..."
        )
        df_eco_hourly = df_eco_hourly.interpolate(method="time", limit=max_steps)
        
        # Apply physical domain guardrails using the unified function
        for col, feat in [("hourly_rain_mm", "rain"), ("outdoor_humidity", "rh"), 
                          ("solar_rad_w_m2", "solar"), ("wind_m_s", "wind")]:
            if col in df_eco_hourly.columns:
                df_eco_hourly[col] = apply_physics_guardrails(df_eco_hourly[col], feature=feat)
            
    return df_eco_hourly.reset_index()


def get_station_metadata(env: WaidBoot) -> tuple[str, str, int, int, int, dict]:
    """
    Queries station metadata, guardrails, and empirical sensor specs 
    from the SQLite Feature Store station_metadata table.
    """
    station_id = env.ecowitt_station_id
    query = """
        SELECT station_name, elevation_m, min_training_days, retrain_window_days, sensor_specs
        FROM station_metadata
        WHERE station_id = ?
    """
    try:
        with sqlite3.connect(env.waid_db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (station_id,))
            row = cursor.fetchone()

        if not row:
            raise WError(
                f"Station '{station_id}' not found in 'station_metadata'. Ensure setup pipeline has executed.",
                code=WaidExit.DATA_FAIL
            )

        station_name, elevation_m, min_training_days, retrain_window_days, sensor_specs_json = row
        
        default_specs = {
            'ecowitt_temp': {'resolution': 0.1, 'deadband': 0.0},
            'ecowitt_rh': {'resolution': 1.0, 'deadband': 0.0},
            'ecowitt_pres': {'resolution': 0.1, 'deadband': 0.0},
            'ecowitt_wind': {'resolution': 0.1, 'deadband': 0.2},
            'ecowitt_solar': {'resolution': 1.0, 'deadband': 0.0},
            'ecowitt_rain': {'resolution': 0.1, 'deadband': 0.1}
        }
        
        sensor_specs = json.loads(sensor_specs_json) if sensor_specs_json else default_specs

        logger.info(
            f"Loaded Station Metadata from DB: '{station_name}' ({station_id}) | "
            f"Elevation: {elevation_m}m | Guardrails: Min Days={min_training_days}, Retrain Window={retrain_window_days}"
        )
        return station_id, str(station_name), int(elevation_m), int(min_training_days), int(retrain_window_days), sensor_specs

    except sqlite3.OperationalError as e:
        raise WError(f"Failed to access 'station_metadata' table ({e}).", code=WaidExit.DATA_FAIL)
    except sqlite3.Error as e:
        raise WError(f"Database error while fetching station metadata: {e}", code=WaidExit.DATA_FAIL)


def apply_physics_guardrails(
    data, 
    feature: str = None, 
    sensor_specs: dict = None, 
    env: WaidBoot = None, 
    future_timestamps: list = None
) -> np.ndarray:
    """
    Unified function for physics-based guardrails, hardware resolution, and noise suppression.
    
    Can handle single values, Pandas Series (for dashboard), or full prediction batches (for inference).

    Args:
        data (np.ndarray|pd.Series|float): Input data to clean.
        feature (str, optional): The feature type (e.g., 'temp', 'wind').
        sensor_specs (dict, optional): Hardware sensor specifications.
        env (WaidBoot, optional): Environment context (required for full batch inference).
        future_timestamps (list, optional): Timestamps (required for full batch inference).

    Returns:
        np.ndarray: Cleaned and quantized data.
    """
    # Load default specs if not provided
    if sensor_specs is None:
        sensor_specs = {
            'ecowitt_temp': {'resolution': 0.1, 'deadband': 0.0},
            'ecowitt_rh': {'resolution': 1.0, 'deadband': 0.0},
            'ecowitt_pres': {'resolution': 0.1, 'deadband': 0.0},
            'ecowitt_wind': {'resolution': 0.1, 'deadband': 0.2},
            'ecowitt_solar': {'resolution': 1.0, 'deadband': 0.0},
            'ecowitt_rain': {'resolution': 0.2, 'deadband': 0.2}
        }

    # Handle Dashboard / Single-feature mode
    if feature:
        spec = sensor_specs.get(f'ecowitt_{feature}', {'resolution': 0.1, 'deadband': 0.0})
        res, db = spec['resolution'], spec['deadband']
        
        # Apply non-negativity (for all except temperature)
        val = data if feature == 'temp' else np.maximum(0.0, data)
        
        # Use resolution directly as the sensitivity threshold instead of an aggressive deadband
        threshold = res / 2.0
        val = np.where(val < threshold, 0.0, val)
        
        # Apply quantization based on sensor resolution
        return np.round(val / res) * res

    # Handle Full Batch Inference mode
    is_batch = len(data.shape) == 3
    preds = data[0].copy() if is_batch else data.copy()
    
    theo_solar_future = calculate_theoretical_solar_radiation(
        np.array(future_timestamps), env.ecowitt_latitude, env.ecowitt_longitude, env.tz_timezone
    )
    
    features = ['temp', 'rh', 'pres', 'wind', 'solar', 'rain']
    for i in range(preds.shape[0]):
        for j, feat in enumerate(features):
            # Apply guardrails iteratively for each feature
            val = preds[i, j]
            
            # Special case for solar (clear-sky limit)
            if feat == 'solar':
                if theo_solar_future[i] <= 0.0:
                    preds[i, j] = 0.0
                else:
                    val = min(val, theo_solar_future[i])
                    preds[i, j] = apply_physics_guardrails(val, feature=feat, sensor_specs=sensor_specs)
            else:
                preds[i, j] = apply_physics_guardrails(val, feature=feat, sensor_specs=sensor_specs)
                
    return np.expand_dims(preds, axis=0) if is_batch else preds


def generate_period_range(begin_period: str, end_period: str) -> list[str]:
    """Generates a list of YYYY-MM periods from start to end inclusive.

    @param begin_period Start month string (YYYY-MM).
    @param end_period End month string (YYYY-MM).
    @return List of period strings.
    """
    start_date = datetime.strptime(begin_period, "%Y-%m")
    end_date = datetime.strptime(end_period, "%Y-%m")
    
    periods = []
    curr = start_date
    while curr <= end_date:
        periods.append(curr.strftime("%Y-%m"))
        if curr.month == 12:
            curr = datetime(curr.year + 1, 1, 1)
        else:
            curr = datetime(curr.year, curr.month + 1, 1)
    return periods