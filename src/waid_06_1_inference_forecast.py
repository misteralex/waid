#!/usr/bin/env python3

"""
@file waid_06_1_inference_forecast.py
@brief 6-hour meteorological inference engine using centralized physical guardrails 
       and incremental reconciliation. Supports --skip-ml for telemetry-only sync.
@details Executes model prediction, reconstructs absolute values, and leverages 
         waid_shared for strict physical bounds and quantization before persisting 
         to the inference_forecast table.
@author AF
@date 2026
"""

import os
import sys
import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, List, Dict, Any

import numpy as np
import pandas as pd
from loguru import logger

# Inject configuration path safely
logger.debug(f"Environment initialized: WAID_SOURCE={os.environ.get('WAID_SOURCE')}")

sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import (
    WaidBoot,
    WError,
    WaidExit,
    validate_mock_timestamp,
)

# Import shared utilities from Single Source of Truth
from waid_shared import (
    calculate_theoretical_solar_radiation, 
    fetch_and_resample_ecowitt, 
    get_station_metadata,
    apply_physics_guardrails,
)


def load_active_model_artifacts(env: WaidBoot) -> Tuple[Any, Any, Any]:
    """
    @brief Loads active ML model and scalar artifacts from registry or fallback directory.
    
    @param env WaidBoot application context instance.
    @return Tuple containing (model, x_scaler, y_scaler).
    @raises WError If model files or scalers do not exist or database fails.
    """
    import joblib
    import tensorflow as tf

    try:
        with sqlite3.connect(env.waid_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT model_path, x_scaler_path, y_scaler_path 
                FROM ml_model_registry 
                WHERE station_id = ? AND is_active = 1 
                LIMIT 1
            """, (env.ecowitt_station_id,))
            row = cursor.fetchone()

        if row:
            # Extract file name directly ignoring obsolete prefix paths
            model_path = str(env.ml_models_dir / Path(row[0]).name)
            x_scaler_path = str(env.ml_models_dir / Path(row[1]).name)
            y_scaler_path = str(env.ml_models_dir / Path(row[2]).name)
        else:
            model_path = str(env.ml_models_dir / Path(env.ml_model_h5_file).name)
            x_scaler_path = str(env.ml_models_dir / Path(env.ml_input_scaler_pkl_file).name)
            y_scaler_path = str(env.ml_models_dir / Path(env.ml_output_scaler_pkl_file).name)

        logger.info(f"Resolved model_path: {model_path}")
                     
        if not os.path.exists(model_path):
            raise WError(f"Trained model file not found at: {model_path}", code=WaidExit.DATA_FAIL)
        if not os.path.exists(x_scaler_path) or not os.path.exists(y_scaler_path):
            raise WError("Scaler artifacts not found.", code=WaidExit.DATA_FAIL)

        model = tf.keras.models.load_model(model_path, compile=False)
        x_scaler = joblib.load(x_scaler_path)
        y_scaler = joblib.load(y_scaler_path)

        logger.success("Active model and scalers loaded successfully.")
        return model, x_scaler, y_scaler

    except sqlite3.Error as e:
        raise WError(f"Database error while loading model registry: {e}", code=WaidExit.DATA_FAIL)


def fetch_recent_telemetry(env: WaidBoot) -> pd.DataFrame:
    """
    @brief Fetches and resamples recent telemetry data from Ecowitt source.
    
    @param env WaidBoot application context instance.
    @return Resampled telemetry DataFrame covering recent lookback.
    @raises WError If telemetry data is insufficient or fetching fails.
    """
    try:
        if env.mock_now:
            end_dt = pd.to_datetime(env.mock_now)
        else:
            end_dt = datetime.now()
            
        start_dt = end_dt - timedelta(days=3)
        
        start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")

        df_resampled = fetch_and_resample_ecowitt(env, start_str, end_str)

        df_resampled.rename(
            columns={
                "outdoor_temperature_c": "ecowitt_temp",
                "abs_pressure_hpa": "ecowitt_pres",
                "outdoor_humidity": "ecowitt_rh",
                "wind_m_s": "ecowitt_wind",
                "solar_rad_w_m2": "ecowitt_solar",
                "hourly_rain_mm": "ecowitt_rain",
            },
            inplace=True,
        )

        if df_resampled.empty or len(df_resampled) < env.forecast_horizon_hours:
            raise WError(f"Insufficient resampled telemetry rows found: got {len(df_resampled)}, expected at least {env.forecast_horizon_hours}.", code=WaidExit.DATA_FAIL)

        df_recent = df_resampled.tail(24).reset_index(drop=True)
        df_recent["timestamp"] = pd.to_datetime(df_recent["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        
        return df_recent

    except Exception as e:
        raise WError(f"Failed to fetch and resample recent telemetry: {e}", code=WaidExit.DATA_FAIL)


def add_cyclic_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    @brief Encodes cyclic diurnal and seasonal time features (sine/cosine).
    
    @param df Input DataFrame with timestamp column.
    @return DataFrame augmented with sine/cosine cyclic features.
    """
    ts = pd.to_datetime(df['timestamp'])
    hour = ts.dt.hour + ts.dt.minute / 60.0
    day_of_year = ts.dt.dayofyear
    
    df['hour_sin'] = np.sin(2 * np.pi * hour / 24.0)
    df['hour_cos'] = np.cos(2 * np.pi * hour / 24.0)
    df['doy_sin'] = np.sin(2 * np.pi * day_of_year / 365.25)
    df['doy_cos'] = np.cos(2 * np.pi * day_of_year / 365.25)
    return df


def build_inference_tensor(env: WaidBoot, df_raw: pd.DataFrame) -> np.ndarray:
    """
    @brief Constructs multi-dimensional input tensor for ML model inference.
    
    @param env WaidBoot application context instance.
    @param df_raw Raw resampled telemetry DataFrame.
    @return 3D NumPy array input tensor.
    @raises WError If input feature count does not match expected model schema.
    """
    df_engineered = add_cyclic_time_features(df_raw.copy())
    timestamps_arr = df_engineered['timestamp'].values
    
    theo_solar_vals = calculate_theoretical_solar_radiation(
        timestamps_arr, env.ecowitt_latitude, env.ecowitt_longitude, env.tz_timezone
    )
    logger.debug(
        f"Input Tensor - Theoretical Solar Range: "
        f"Min={theo_solar_vals.min():.2f} W/m², Max={theo_solar_vals.max():.2f} W/m²"
    )
    
    df_engineered['theo_solar'] = theo_solar_vals
    
    input_data = df_engineered[env.input_features_match].values
    if input_data.shape[1] != env.n_input_features:
        raise WError(f"Feature count mismatch: expected {env.n_input_features}, got {input_data.shape[1]}", code=WaidExit.DATA_FAIL)

    return np.expand_dims(input_data, axis=0)


def run_dynamic_reconciliation(cursor: sqlite3.Cursor, model_version: str, env: WaidBoot) -> None:
    """
    @brief Reconciles pending historical predictions against actual observed telemetry and bias records.
    
    @param cursor SQLite database connection cursor.
    @param model_version Identifier string of the model version.
    @param env WaidBoot application context instance.
    """
    logger.info("Starting dynamic reconciliation for all pending records with missing diffs...")

    cursor.execute("""
        SELECT timestamp 
        FROM inference_forecast 
        WHERE (diff_temp IS NULL OR diff_rh IS NULL OR diff_pres IS NULL 
           OR diff_rh = 0.0 OR diff_temp = 0.0)
          AND model_version = ?
        ORDER BY timestamp ASC
    """, (model_version,))
    pending_rows = cursor.fetchall()

    for row in pending_rows:
        ts = row[0]
        
        cursor.execute("""
            SELECT timestamp, temp_eco, pres_eco, rh_eco, wind_eco, solar_eco, rain_eco 
            FROM match_records 
            WHERE timestamp = ?
        """, (ts,))
        actual_row = cursor.fetchone()
        
        if not actual_row:
            continue
        
        _, a_temp, a_pres, a_rh, a_wind, a_solar, a_rain = actual_row
        
        if any(v is not None for v in [a_temp, a_rh, a_pres, a_wind, a_solar, a_rain]):
            actual_raw_arr = np.array([[
                a_temp if a_temp is not None else 0.0,
                a_rh if a_rh is not None else 0.0,
                a_pres if a_pres is not None else 0.0,
                a_wind if a_wind is not None else 0.0,
                a_solar if a_solar is not None else 0.0,
                a_rain if a_rain is not None else 0.0
            ]])
            actual_guarded = apply_physics_guardrails(
                actual_raw_arr, 
                future_timestamps=[ts], 
                env=env
            )[0]
            a_temp, a_rh, a_pres, a_wind, a_solar, a_rain = actual_guarded
            
        cursor.execute("""
            SELECT pred_temp, pred_rh, pred_pres, pred_wind, pred_solar, pred_rain 
            FROM inference_forecast 
            WHERE timestamp = ? AND model_version = ?
        """, (ts, model_version))
        pred_row = cursor.fetchone()
        
        cursor.execute("""
            SELECT bias_temp, bias_pres, bias_rh, bias_wind, bias_solar, bias_rain 
            FROM int_matches_bias WHERE timestamp = ?
        """, (ts,))
        bias_row = cursor.fetchone()
        
        if pred_row:
            p_temp, p_rh, p_pres, p_wind, p_solar, p_rain = pred_row
            
            b_temp  = float(bias_row[0]) if bias_row and bias_row[0] is not None else 0.0
            b_pres  = float(bias_row[1]) if bias_row and bias_row[1] is not None else 0.0
            b_rh    = float(bias_row[2]) if bias_row and bias_row[2] is not None else 0.0
            b_wind  = float(bias_row[3]) if bias_row and bias_row[3] is not None else 0.0
            b_solar = float(bias_row[4]) if bias_row and bias_row[4] is not None else 0.0
            b_rain  = float(bias_row[5]) if bias_row and bias_row[5] is not None else 0.0

            diff_temp  = float(p_temp)  - float(a_temp)  if p_temp  is not None and a_temp  is not None else None
            diff_rh    = float(p_rh)    - float(a_rh)    if p_rh    is not None and a_rh    is not None else None
            diff_pres  = float(p_pres)  - float(a_pres)  if p_pres  is not None and a_pres  is not None else None
            diff_wind  = float(p_wind)  - float(a_wind)  if p_wind  is not None and a_wind  is not None else None
            diff_solar = float(p_solar) - float(a_solar) if p_solar is not None and a_solar is not None else None
            diff_rain  = float(p_rain)  - float(a_rain)  if p_rain  is not None and a_rain  is not None else None

            drift_temp  = (diff_temp  - b_temp)  if diff_temp  is not None else None
            drift_rh    = (diff_rh    - b_rh)    if diff_rh    is not None else None
            drift_pres  = (diff_pres  - b_pres)  if diff_pres  is not None else None
            drift_wind  = (diff_wind  - b_wind)  if diff_wind  is not None else None
            drift_solar = (diff_solar - b_solar) if diff_solar is not None else None
            drift_rain  = (diff_rain  - b_rain)  if diff_rain  is not None else None

            cursor.execute("""
                UPDATE inference_forecast 
                SET diff_temp = ?, diff_rh = ?, diff_pres = ?, diff_wind = ?, diff_solar = ?, diff_rain = ?,
                    historical_bias_temp = ?, historical_bias_rh = ?, historical_bias_pres = ?, 
                    historical_bias_wind = ?, historical_bias_solar = ?, historical_bias_rain = ?,
                    drift_vs_bias_temp = ?, drift_vs_bias_rh = ?, drift_vs_bias_pres = ?, 
                    drift_vs_bias_wind = ?, drift_vs_bias_solar = ?, drift_vs_bias_rain = ?,
                    drift_vs_bias = ?
                WHERE timestamp = ? AND model_version = ?
            """, (
                diff_temp, diff_rh, diff_pres, diff_wind, diff_solar, diff_rain,
                b_temp, b_rh, b_pres, b_wind, b_solar, b_rain,
                drift_temp, drift_rh, drift_pres, drift_wind, drift_solar, drift_rain,
                drift_temp,
                ts, model_version
            ))


def sync_telemetry_only(env: WaidBoot, df_raw: pd.DataFrame) -> None:
    """
    @brief Populates telemetry observation timestamps and executes reconciliation without ML predictions.
    
    @param env WaidBoot application context instance.
    @param df_raw Raw resampled telemetry DataFrame.
    @raises WError If database synchronization fails.
    """
    logger.info("Executing telemetry-only sync for inference_forecast (--skip-ml mode active)...")
    try:
        with sqlite3.connect(env.waid_db) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inference_forecast(
                    timestamp TEXT,
                    model_version TEXT,
                    created_at TEXT,
                    ts_window_start TEXT,
                    ts_window_stop TEXT,
                    pred_temp REAL,
                    pred_rh REAL,
                    pred_pres REAL,
                    pred_wind REAL,
                    pred_rain REAL,
                    pred_solar REAL,
                    diff_temp REAL,
                    diff_rh REAL,
                    historical_bias_temp REAL,
                    drift_vs_bias REAL,
                    PRIMARY KEY (timestamp, model_version)
                )
            """)

            cursor.execute("PRAGMA table_info(inference_forecast)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            required_columns = {
                "created_at": "TEXT",
                "ts_window_start": "TEXT",
                "ts_window_stop": "TEXT",
                "diff_temp": "REAL", "diff_rh": "REAL", "diff_pres": "REAL", 
                "diff_wind": "REAL", "diff_solar": "REAL", "diff_rain": "REAL",
                "historical_bias_temp": "REAL", "historical_bias_rh": "REAL", "historical_bias_pres": "REAL", 
                "historical_bias_wind": "REAL", "historical_bias_solar": "REAL", "historical_bias_rain": "REAL",
                "drift_vs_bias_temp": "REAL", "drift_vs_bias_rh": "REAL", "drift_vs_bias_pres": "REAL", 
                "drift_vs_bias_wind": "REAL", "drift_vs_bias_solar": "REAL", "drift_vs_bias_rain": "REAL"
            }
            
            for col_name, col_type in required_columns.items():
                if col_name not in existing_columns:
                    cursor.execute(f"ALTER TABLE inference_forecast ADD COLUMN {col_name} {col_type}")

            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            model_version = "weather_model_full"
            timestamps = df_raw['timestamp'].tolist()
            window_start = timestamps[0]
            window_stop = timestamps[-1]

            for ts in timestamps:
                cursor.execute("""
                    INSERT INTO inference_forecast (
                        timestamp, model_version, created_at, ts_window_start, ts_window_stop
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(timestamp, model_version) DO UPDATE SET
                        created_at = excluded.created_at,
                        ts_window_start = excluded.ts_window_start,
                        ts_window_stop = excluded.ts_window_stop
                """, (ts, model_version, created_at, window_start, window_stop))

            run_dynamic_reconciliation(cursor, model_version, env)
            conn.commit()
            
        logger.success("Observation timestamps and reconciliation successfully processed.")
    except sqlite3.Error as e:
        raise WError(f"Failed to sync telemetry to inference_forecast: {e}", code=WaidExit.DATA_FAIL)


def persist_and_update_inference_forecast(
    env: WaidBoot, 
    future_timestamps: List[str], 
    preds_guarded: np.ndarray, 
    sensor_specs: Dict[str, Any],
    window_start: str,
    window_stop: str
) -> None:
    """
    @brief Persists physics-safe predictions to the permanent inference_forecast table and triggers reconciliation.
    
    @param env WaidBoot application context instance.
    @param future_timestamps List of future target UTC timestamps.
    @param preds_guarded Physics-guarded NumPy array of predictions.
    @param sensor_specs Dictionary reserved for station sensor configurations.
    @param window_start Lineage window start timestamp string.
    @param window_stop Lineage window stop timestamp string.
    @raises WError If database update fails.
    """
    try:
        with sqlite3.connect(env.waid_db) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inference_forecast(
                    timestamp TEXT,
                    model_version TEXT,
                    created_at TEXT,
                    ts_window_start TEXT,
                    ts_window_stop TEXT,
                    pred_temp REAL,
                    pred_rh REAL,
                    pred_pres REAL,
                    pred_wind REAL,
                    pred_rain REAL,
                    pred_solar REAL,
                    diff_temp REAL,
                    diff_rh REAL,
                    historical_bias_temp REAL,
                    drift_vs_bias REAL,
                    PRIMARY KEY (timestamp, model_version)
                )
            """)

            cursor.execute("PRAGMA table_info(inference_forecast)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            required_columns = {
                "created_at": "TEXT",
                "ts_window_start": "TEXT",
                "ts_window_stop": "TEXT",
                "diff_temp": "REAL", "diff_rh": "REAL", "diff_pres": "REAL", 
                "diff_wind": "REAL", "diff_solar": "REAL", "diff_rain": "REAL",
                "historical_bias_temp": "REAL", "historical_bias_rh": "REAL", "historical_bias_pres": "REAL", 
                "historical_bias_wind": "REAL", "historical_bias_solar": "REAL", "historical_bias_rain": "REAL",
                "drift_vs_bias_temp": "REAL", "drift_vs_bias_rh": "REAL", "drift_vs_bias_pres": "REAL", 
                "drift_vs_bias_wind": "REAL", "drift_vs_bias_solar": "REAL", "drift_vs_bias_rain": "REAL"
            }
            
            for col_name, col_type in required_columns.items():
                if col_name not in existing_columns:
                    cursor.execute(f"ALTER TABLE inference_forecast ADD COLUMN {col_name} {col_type}")

            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            model_version = "weather_model_full"
            preds = preds_guarded[0] if len(preds_guarded.shape) == 3 else preds_guarded

            for i, timestamp in enumerate(future_timestamps):
                p_temp, p_rh, p_pres, p_wind, p_solar, p_rain = preds[i]
                
                cursor.execute("""
                    SELECT timestamp FROM inference_forecast 
                    WHERE timestamp = ? AND model_version = ?
                """, (timestamp, model_version))
                row = cursor.fetchone()
                
                if not row:
                    cursor.execute("""
                        INSERT INTO inference_forecast (
                            timestamp, model_version,
                            created_at, ts_window_start, ts_window_stop,
                            pred_temp, pred_rh, pred_pres, pred_wind, pred_rain, pred_solar
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        timestamp, model_version,
                        created_at, window_start, window_stop,
                        float(p_temp), float(p_rh), float(p_pres),
                        float(p_wind), float(p_rain), float(p_solar)
                    ))
                else:
                    cursor.execute("""
                        UPDATE inference_forecast 
                        SET created_at = ?, ts_window_start = ?, ts_window_stop = ?,
                            pred_temp = ?, pred_rh = ?, pred_pres = ?, 
                            pred_wind = ?, pred_rain = ?, pred_solar = ?
                        WHERE timestamp = ? AND model_version = ?
                    """, (
                        created_at, window_start, window_stop,
                        float(p_temp), float(p_rh), float(p_pres),
                        float(p_wind), float(p_rain), float(p_solar),
                        timestamp, model_version
                    ))

            run_dynamic_reconciliation(cursor, model_version, env)
            conn.commit()

        logger.success("Permanent inference_forecast table successfully updated.")
    except sqlite3.Error as e:
        raise WError(f"Failed to update inference forecast table: {e}", code=WaidExit.DATA_FAIL)


def main() -> int:
    """
    @brief Main execution block for running 6-hour weather inference and reconciliation workflow.
    
    @return Exit code integer from WaidExit.
    """
    try:
        parser = argparse.ArgumentParser(description="WAID Inference Engine")
        parser.add_argument("--mock-now", type=str, default=None, help="Simulated current timestamp")
        parser.add_argument("--skip-ml", action="store_true", help="Skip ML model predictions and sync telemetry only")
        args, _ = parser.parse_known_args()
        
        env = WaidBoot()
        
        if args.mock_now:
            env.mock_now = validate_mock_timestamp(args.mock_now)
            logger.info(f"Overriding mock_now with CLI argument: {env.mock_now}")
        
        df_raw = fetch_recent_telemetry(env)

        if args.skip_ml:
            logger.info("Flag --skip-ml enabled: Syncing telemetry and performing reconciliation without ML inference.")
            sync_telemetry_only(env, df_raw)
            return WaidExit.SUCCESS

        logger.info(f"Environment initialized: WAID_ML_MODELS_DIR={os.environ.get('WAID_ML_MODELS_DIR')}")
        logger.info(f"Environment initialized: env.ml_model_h5_file={env.ml_model_h5_file}")
        logger.info(f"Environment initialized: env.ml_models_dir={env.ml_models_dir}")
        
        logger.info("Initializing 6-hour weather inference and strict physics-safe guardrail pipeline...")

        _, _, _, _, _, _ = get_station_metadata(env)

        model, x_scaler, y_scaler = load_active_model_artifacts(env)
        recent_timestamps = df_raw['timestamp'].tolist()

        # Extract lineage window timestamps
        window_start = recent_timestamps[0]
        window_stop = recent_timestamps[-1]

        X_infer = build_inference_tensor(env, df_raw)

        n_samples, n_timesteps, n_features = X_infer.shape
        X_2d = X_infer.reshape(-1, n_features)
        X_2d_scaled = x_scaler.transform(X_2d)
        X_scaled_3d = X_2d_scaled.reshape(n_samples, n_timesteps, n_features)

        preds_scaled = model.predict(X_scaled_3d, verbose=0)

        original_shape = preds_scaled.shape
        if len(original_shape) == 3:
            batch_size, horizon, n_targets = original_shape
            preds_2d = preds_scaled.reshape(-1, n_targets)
            preds_denorm_2d = y_scaler.inverse_transform(preds_2d)
            preds_deltas = preds_denorm_2d.reshape(batch_size, horizon, n_targets)
        else:
            preds_deltas = y_scaler.inverse_transform(preds_scaled)

        TARGET_FEATURES_ORDER = [
            'ecowitt_temp', 
            'ecowitt_rh', 
            'ecowitt_pres', 
            'ecowitt_wind', 
            'ecowitt_solar', 
            'ecowitt_rain'
        ]
        last_actual_series = df_raw[TARGET_FEATURES_ORDER].iloc[-1]
        last_actual_features = last_actual_series.values.astype(float)      

        preds_absolute = np.zeros_like(preds_deltas)
        if len(preds_deltas.shape) == 3:
            for h in range(preds_deltas.shape[1]):
                preds_absolute[0, h, :] = last_actual_features + preds_deltas[0, h, :]
        else:
            for h in range(preds_deltas.shape[0]):
                preds_absolute[h, :] = last_actual_features + preds_deltas[h, :]

        # Normalize the last telemetry timestamp ensuring conversion to UTC
        if env.mock_now:
            last_dt = pd.to_datetime(env.mock_now)
        else:
            last_dt = pd.to_datetime(recent_timestamps[-1])

        # Handle timezone resolution and convert to UTC
        if last_dt.tzinfo is None:
            utc_base_dt = last_dt.tz_localize(env.tz_timezone, ambiguous='NaT', nonexistent='shift_forward').tz_convert('UTC')
        else:
            utc_base_dt = last_dt.tz_convert('UTC')

        utc_base_dt_hourly = utc_base_dt.floor('h')

        # Generate future target timestamps in UTC starting from the base hourly offset
        future_timestamps = [
            (utc_base_dt_hourly + pd.Timedelta(hours=i+1)).strftime("%Y-%m-%d %H:%M:%S") 
            for i in range(env.forecast_horizon_hours)
        ]
        
        # Apply physics guardrails using the centralized function from waid_shared
        preds_guarded = apply_physics_guardrails(
            preds_absolute, 
            future_timestamps, 
            env=env
        )
        
        persist_and_update_inference_forecast(
            env, 
            future_timestamps, 
            preds_guarded, 
            {}, 
            window_start=window_start, 
            window_stop=window_stop
        )

        logger.success("6-hour absolute forecast outputs successfully generated, guarded, and stored.")
        return WaidExit.SUCCESS

    except WError as e:
        logger.error(f"[WAID ERROR] {e.message}")
        return e.code
    except Exception:
        logger.exception("Unexpected failure during inference execution")
        return WaidExit.INTERNAL_ERROR

if __name__ == "__main__":
    sys.exit(main())