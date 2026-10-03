"""
@file waid_shared.py
@brief Serves as the core utility and data processing engine for the Weather-AI project.
@details Centralizes time-series resampling, astronomical clear-sky calculations, 
         hardware-specific sensor calibration guardrails, and database query helpers.
@author AF
@date 2026
"""

from datetime import datetime
import json
from pathlib import Path
import sqlite3

from boot import WError, WaidBoot, WaidExit
from loguru import logger
import numpy as np
import pandas as pd


def calculate_theoretical_solar_radiation(
    timestamps: np.ndarray,
    humidity: np.ndarray = None,
    input_tz: str = "UTC",
    lat: float = None,
    lon: float = None,
    env: WaidBoot = None,
) -> np.ndarray:
    """
    @brief Computes atmospheric-attenuated theoretical solar radiation 
           integrating relative humidity (RH) and dynamic power scaling 
           retrieved from the SQLite model registry.

    @param timestamps Array of datetime objects or timestamps.
    @param humidity Optional array of relative humidity percentage values.
    @param input_tz Timezone string for naive timestamps (default "UTC").
    @param lat Station latitude coordinate in decimal degrees.
    @param lon Station longitude coordinate in decimal degrees.
    @param env Optional WaidBoot instance for database configuration.
    @return Array of theoretical solar radiation values (W/m²).
    """
    if lat is None or lon is None:
        raise ValueError("Latitude (lat) and Longitude (lon) must be provided.")

    dt_index = pd.to_datetime(timestamps)

    if dt_index.tz is None:
        dt_index = dt_index.tz_localize(input_tz, nonexistent="shift_forward")

    if str(dt_index.tz) != "UTC":
        dt_index = dt_index.tz_convert("UTC")

    day_of_year = dt_index.dayofyear.values
    dt_utc_hours = (
        dt_index.hour.values 
        + dt_index.minute.values / 60.0 
        + dt_index.second.values / 3600.0
    )

    b = np.radians(360.0 * (day_of_year - 81) / 365.0)
    eot = 9.87 * np.sin(2 * b) - 7.53 * np.cos(b) - 1.5 * np.sin(b)

    solar_time = dt_utc_hours + (lon / 15.0) + (eot / 60.0)
    hour_angle = (solar_time - 12.0) * 15.0
    declination = 23.45 * np.sin(np.radians(360.0 * (284 + day_of_year) / 365.0))

    lat_rad = np.radians(lat)
    dec_rad = np.radians(declination)
    ha_rad = np.radians(hour_angle)

    sin_elevation = np.sin(lat_rad) * np.sin(dec_rad) + np.cos(lat_rad) * np.cos(dec_rad) * np.cos(ha_rad)
    elevation_angle = np.arcsin(np.clip(sin_elevation, -1.0, 1.0))

    base_solar = 1000.0 * np.maximum(0.0, np.sin(elevation_angle))

    # Apply humidity-based atmospheric extinction if humidity array is provided
    if humidity is not None:
        rh_arr = np.asarray(humidity, dtype=float)
        rh_fraction = np.clip(rh_arr / 100.0, 0.0, 1.0)
        attenuation_factor = np.exp(-0.35 * rh_fraction)
        solar_rad = base_solar * attenuation_factor
    else:
        solar_rad = base_solar

    cleaned_solar = np.maximum(0.0, solar_rad)
    
    return cleaned_solar


def fetch_and_resample_ecowitt(
    env: WaidBoot, start_date: str, end_date: str
) -> pd.DataFrame:
    """
    @brief Extracts raw Ecowitt station data, applies numeric type casting, 
           resampling to uniform time slots, and bounded time interpolation.

    @param env WaidBoot configuration instance.
    @param start_date Start window string for data extraction.
    @param end_date End window string for data extraction.
    @return Processed and resampled pandas DataFrame containing hourly sensor data.
    """
    logger.info(f"Connecting to Ecowitt Database: {env.waid_db}")
    if not Path(env.waid_db).exists():
        raise RuntimeError(f"WAID DB file not found at: {env.waid_db}")

    try:
        logger.info(
            f"Querying Ecowitt DB for window: [{start_date}] to [{end_date}]"
        )
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
            df_eco_raw = pd.read_sql_query(
                query, conn, params=(start_date, end_date)
            )

    except Exception as e:
        raise RuntimeError(f"Database extraction or SQL query failure: {e}")

    if df_eco_raw.empty:
        raise RuntimeError(
            "No local station records retrieved from database for the specified window."
        )

    df_eco_raw["timestamp"] = (
        pd.to_datetime(df_eco_raw["timestamp"], utc=True)
        .dt.tz_localize(None)
    )

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
            df_eco_raw[field] = pd.to_numeric(
                df_eco_raw[field], errors="coerce"
            )

    # Apply passive solar radiation thermal offset (-1.5 °C correction)
    if "outdoor_temperature_c" in df_eco_raw.columns:
        df_eco_raw["outdoor_temperature_c"] = df_eco_raw["outdoor_temperature_c"] - 1.5

    resample_freq = f"{env.resample_interval_min} min"
    logger.info(
        f"Resampling local telemetry into {resample_freq} synchronized slots..."
    )

    agg_rules = {
        "outdoor_temperature_c": "mean",
        "abs_pressure_hpa": "mean",
        "outdoor_humidity": "mean",
        "wind_m_s": "mean",
        "solar_rad_w_m2": "mean",
        "hourly_rain_mm": "max",
    }
    present_rules = {
        col: agg for col, agg in agg_rules.items() if col in df_eco_raw.columns
    }

    df_eco_hourly = df_eco_raw.resample(resample_freq, on="timestamp").agg(
        present_rules
    )

    max_steps = int(
        (env.max_interpolate_hours * 60) / env.resample_interval_min
    )
    if max_steps > 0:
        logger.info(
            f"Applying bounded time interpolation (max threshold: {env.max_interpolate_hours}h / {max_steps} steps)..."
        )
        df_eco_hourly = df_eco_hourly.interpolate(
            method="time", limit=max_steps
        )

        # Apply physical domain guardrails using unified function
        for col, feat in [
            ("hourly_rain_mm", "rain"),
            ("outdoor_humidity", "rh"),
            ("solar_rad_w_m2", "solar"),
            ("wind_m_s", "wind"),
        ]:
            if col in df_eco_hourly.columns:
                df_eco_hourly[col] = apply_physics_guardrails(
                    df_eco_hourly[col], feature=feat
                )
    else:
        logger.warning(
            "Time interpolation is disabled (max_interpolate_hours = 0). Raw NaN values will persist."
        )

    # Check for unhandled NaNs in resampled telemetry regardless of interpolation configuration
    nan_summary = df_eco_hourly.isna().sum()
    problematic_cols = nan_summary[nan_summary > 0]

    if not problematic_cols.empty:
        details = ", ".join(
            f"{col}: {count} missing"
            for col, count in problematic_cols.items()
        )
        logger.warning(
            f"Unresolved NaNs detected in resampled telemetry"
        )
        logger.debug(f"Missing telemetry details -> [{details}]")

    return df_eco_hourly.reset_index()


# Hardware Nominal Default Specifications
NOMINAL_SENSOR_SPECS = {
    "ecowitt_temp": {"resolution": 0.1, "deadband": 0.0},
    "ecowitt_rh": {"resolution": 1.0, "deadband": 0.0},
    "ecowitt_pres": {"resolution": 0.1, "deadband": 0.0},
    "ecowitt_wind": {"resolution": 0.1, "deadband": 0.2},
    "ecowitt_solar": {"resolution": 0.1, "deadband": 0.0},
    "ecowitt_rain": {"resolution": 0.1, "deadband": 0.2},
}


def get_station_metadata(
    env: WaidBoot,
) -> tuple[str, str, float, int, int, dict]:
    """
    @brief Retrieves station metadata and configuration parameters from the database.

    @param env WaidBoot configuration instance.
    @return Tuple containing (station_id, station_name, elevation, min_days, retrain_window, sensor_specs).
    """
    station_id = getattr(env, "ecowitt_station_id", "STATION_01")
    station_name = "Local Home Weather Station"
    elevation = 0.0
    min_days = 14
    retrain_window = 30
    sensor_specs = NOMINAL_SENSOR_SPECS.copy()

    try:
        with sqlite3.connect(env.waid_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT station_id, station_name, elevation_m, min_training_days, 
                       retrain_window_days, sensor_specs 
                FROM station_metadata 
                LIMIT 1
            """
            )
            row = cursor.fetchone()

            if row:
                station_id = row[0] or station_id
                station_name = row[1] or station_name
                elevation = float(row[2]) if row[2] is not None else elevation
                min_days = int(row[3]) if row[3] is not None else min_days
                retrain_window = (
                    int(row[4]) if row[4] is not None else retrain_window
                )

                if row[5]:
                    try:
                        sensor_specs = json.loads(row[5])
                    except json.JSONDecodeError:
                        logger.warning(
                            "Invalid JSON in sensor_specs column. Falling back to nominal defaults."
                        )

    except sqlite3.Error as e:
        logger.warning(
            f"Could not load station metadata from DB ({e}). Using system defaults."
        )

    logger.info(
        f"Loaded Station Metadata from DB: '{station_name}' ({station_id}) | "
        f"Elevation: {elevation}m | Guardrails: Min Days={min_days}, Retrain Window={retrain_window}"
    )

    return (
        station_id,
        station_name,
        elevation,
        min_days,
        retrain_window,
        sensor_specs,
    )


def apply_physics_guardrails(
    data,
    feature: str = None,
    sensor_specs: dict = None,
    env=None,
    future_timestamps: list = None,
) -> np.ndarray:
    """
    @brief Unified engine for physics-based guardrails, hardware resolution quantization,
           and noise suppression.
    @details Handles individual scalar values, Pandas Series, or multi-dimensional prediction tensors,
             applying rules based on feature type and hardware specifications.

    @param data Input data (scalar, Pandas Series, or numpy array).
    @param feature Optional feature name ("temp", "rh", "solar", "wind", "rain", "pres").
    @param sensor_specs Dictionary containing sensor resolution and deadband bounds.
    @param env WaidBoot environment instance for astronomical solar checks.
    @param future_timestamps List of target future timestamps for clear-sky boundaries.
    @return Processed numpy array, Pandas Series, or scalar value.
    """
    # 1. Load default specs if not provided
    if sensor_specs is None:
        sensor_specs = {
            "ecowitt_temp": {"resolution": 0.1, "deadband": 0.0},
            "ecowitt_rh": {"resolution": 0.1, "deadband": 0.0},  # Set to 0.1 to preserve dynamics
            "ecowitt_pres": {"resolution": 0.1, "deadband": 0.0},
            "ecowitt_wind": {"resolution": 0.1, "deadband": 0.2},
            "ecowitt_solar": {"resolution": 1.0, "deadband": 0.0},
            "ecowitt_rain": {"resolution": 0.1, "deadband": 0.2},
        }

    # 2. Handle Dashboard / Single-feature mode
    if feature:
        spec = sensor_specs.get(
            f"ecowitt_{feature}", {"resolution": 0.1, "deadband": 0.0}
        )
        res = spec["resolution"]

        is_scalar = np.isscalar(data)
        val = np.asarray(data, dtype=float)

        # Non-negativity constraint for strictly positive physical variables
        if feature in ["wind", "solar", "rain", "rh"]:
            val = np.maximum(0.0, val)

        # Zero-threshold suppression for rain, wind, and solar
        if feature in ["wind", "solar", "rain"]:
            threshold = res / 2.0
            val = np.where(val < threshold, 0.0, val)

        # Quantization to sensor resolution
        quantized = np.round(val / res) * res
        return quantized.item() if is_scalar else quantized

    # 3. Handle Full Batch Inference mode
    data_arr = np.asarray(data, dtype=float)
    is_batch = data_arr.ndim == 3
    preds = data_arr[0].copy() if is_batch else data_arr.copy()

    # Pre-calculate theoretical clear-sky solar boundaries
    theo_solar_future = None
    if env is not None and future_timestamps is not None:
        ts_index = pd.to_datetime(future_timestamps)
        if ts_index.tz is None:
            ts_index = ts_index.tz_localize("UTC")
        else:
            ts_index = ts_index.tz_convert("UTC")

        theo_solar_future = calculate_theoretical_solar_radiation(
            ts_index.values,
            input_tz="UTC",
            lat=env.ecowitt_latitude,
            lon=env.ecowitt_longitude,
        )

    features = ["temp", "rh", "pres", "wind", "solar", "rain"]

    for j, feat in enumerate(features):
        spec = sensor_specs.get(
            f"ecowitt_{feat}", {"resolution": 0.1, "deadband": 0.0}
        )
        res = spec["resolution"]

        col = preds[:, j]

        # A) Absolute Physical Bounds Clipping
        if feat in ["wind", "solar", "rain"]:
            col = np.maximum(0.0, col)
        elif feat == "rh":
            col = np.clip(col, 0.0, 100.0)

        # B) Clear-Sky Solar Boundary & Night Clipping
        if feat == "solar" and theo_solar_future is not None:
            col = np.where(
                theo_solar_future <= 0.0, 0.0, np.minimum(col, theo_solar_future)
            )

        # C) Noise Suppression selective zero-clipping
        if feat in ["wind", "rain", "solar"]:
            threshold = res / 2.0
            col = np.where(col < threshold, 0.0, col)

        # D) Precision Quantization
        if feat in ["temp", "rh", "pres"]:
            preds[:, j] = np.round(col, decimals=1)
        else:
            preds[:, j] = np.round(col / res) * res

    return np.expand_dims(preds, axis=0) if is_batch else preds


def generate_period_range(begin_period: str, end_period: str) -> list[str]:
    """
    @brief Generates a contiguous list of YYYY-MM periods from start to end month inclusive.

    @param begin_period Start month string in YYYY-MM format.
    @param end_period End month string in YYYY-MM format.
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


def get_last_inference_datetime(
    db_path: Path, table_name: str = "inference_forecast"
) -> datetime | None:
    """
    @brief Retrieves the execution timestamp of the last generated ML forecast as a datetime object.
           Acts as the single source of truth for both inference orchestration skipping 
           and UI status labeling.

    @param db_path Path to the target SQLite database file.
    @param table_name Target forecast database table name (default: "inference_forecast").
    @return Datetime object of the last valid inference or None if empty or missing.
    """
    if not db_path or not Path(db_path).exists():
        return None

    try:
        with sqlite3.connect(db_path) as conn:
            query = f"SELECT MAX(created_at) AS last_ts FROM {table_name}"
            try:
                df_res = pd.read_sql_query(query, conn)
            except Exception:
                query = f"SELECT MAX(timestamp) AS last_ts FROM {table_name}"
                df_res = pd.read_sql_query(query, conn)

            if not df_res.empty and pd.notnull(df_res["last_ts"].iloc[0]):
                return pd.to_datetime(df_res["last_ts"].iloc[0]).to_pydatetime()
    except Exception as e:
        logger.debug(
            f"Failed to query last inference timestamp from {table_name}: {e}"
        )

    return None


def is_in_docker() -> bool:
    """
    @brief Detects whether execution is occurring inside a Docker container.
    
    @return True if executing inside Docker, False otherwise.
    """
    if Path("/.dockerenv").exists():
        return True
    try:
        with open("/proc/1/cgroup", "rt", encoding="utf-8") as f:
            content = f.read()
            return "docker" in content or "containerd" in content
    except Exception:
        return False