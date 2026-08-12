#!/usr/bin/env python3

"""
@file waid_05_2_ml_train.py
@brief WAID Machine Learning Model Training and Registry Synchronization.
@details Loads 3D raw tensors across available periods using a memory-efficient tf.data pipeline, 
         enriches inputs with physics-informed theoretical solar radiation, scales features incrementally, 
         trains an LSTM network, and updates the SQLite Feature Store Model Registry with frequency guardrails.
@author AF
@date 2026
"""

import os
import sys
import glob
import sqlite3
import numpy as np
import joblib
import json
from pathlib import Path
from datetime import datetime
from loguru import logger
import tensorflow as tf
from tensorflow.keras import Sequential, Input
from tensorflow.keras.layers import LSTM, Dropout, Dense, Reshape 
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler

# Inject configuration path into python execution environment
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import (
    WaidBoot,
    WError,
    WaidExit,
)

# Import shared utilities from Single Source of Truth
from waid_utils import calculate_theoretical_solar_radiation, get_station_metadata

def denormalize_predictions(y_scaler, preds_scaled: np.ndarray) -> np.ndarray:
    """Denormalizes predictions using the provided y_scaler supporting 2D or 3D arrays."""
    original_shape = preds_scaled.shape
    if len(original_shape) == 3:
        batch_size, horizon, n_features = original_shape
        preds_2d = preds_scaled.reshape(-1, n_features)
        preds_denorm_2d = y_scaler.inverse_transform(preds_2d)
        return preds_denorm_2d.reshape(batch_size, horizon, n_features)
    else:
        return y_scaler.inverse_transform(preds_scaled)


def ensure_model_registry_schema(env: WaidBoot) -> None:
    """Ensures ml_model_registry table exists before performing registration operations."""
    create_model_registry_stmt = """
    CREATE TABLE IF NOT EXISTS ml_model_registry (
        model_version TEXT PRIMARY KEY,
        station_id TEXT NOT NULL,
        trained_at TEXT NOT NULL,
        last_ecowitt_timestamp TEXT NOT NULL,
        train_samples_count INTEGER NOT NULL,
        x_scaler_path TEXT NOT NULL,
        y_scaler_path TEXT NOT NULL,
        model_path TEXT NOT NULL,
        metrics_mse REAL,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (station_id) REFERENCES station_metadata(station_id)
    );
    """
    try:
        with sqlite3.connect(env.waid_db) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute(create_model_registry_stmt)
            conn.commit()
    except sqlite3.Error as e:
        raise WError(f"Failed to initialize ml_model_registry schema: {e}", code=WaidExit.DATA_FAIL)


def get_max_timestamp(env: WaidBoot) -> str:
    """Retrieves maximum Ecowitt timestamp from staging database."""
    query = "SELECT MAX(timestamp) FROM stg_ecowitt"
    last_ecowitt_ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with sqlite3.connect(env.waid_db) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            if row and row[0]:
                last_ecowitt_ts = str(row[0])
    except sqlite3.Error as e:
        logger.warning(f"Could not query max timestamp from DB ({e}). Using fallback.")

    return last_ecowitt_ts


def check_retrain_required(
    env: WaidBoot, 
    station_id: str, 
    station_name: str, 
    latest_available_period: str, 
    min_training_days: int
) -> bool:
    """Checks if a new training run is required based on registry status and minimum training interval."""
    logger.info(f"Checking ML model registry status for Station: '{station_name}' ({station_id})...")

    query = """
        SELECT trained_at, last_ecowitt_timestamp 
        FROM ml_model_registry 
        WHERE station_id = ? AND is_active = 1 
        ORDER BY trained_at DESC LIMIT 1
    """
    try:
        with sqlite3.connect(env.waid_db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (station_id,))
            row = cursor.fetchone()

        if not row or not row[0]:
            logger.info("No active model registry record found. Proceeding with initial model training.")
            return True

        last_trained_at_str, last_trained_ts = row
        last_trained_at = datetime.strptime(last_trained_at_str, "%Y-%m-%d %H:%M:%S")
        days_since_last_training = (datetime.utcnow() - last_trained_at).days

        logger.info(f"Last model trained at: [{last_trained_at_str}] ({days_since_last_training} days ago)")
        logger.info(f"Minimum training interval / days guardrail: [{min_training_days}] days")

        # Guardrail: Do not retrain if fewer days have passed than min_training_days
        if days_since_last_training < min_training_days:
            logger.success(
                f"Retraining skipped: Only {days_since_last_training} days passed since last training, "
                f"which is less than the required minimum interval of {min_training_days} days."
            )
            return False

        if latest_available_period > last_trained_ts[:7]:
            logger.info("Newer telemetry period detected and training interval met! Triggering ML retraining...")
            return True

        logger.success(f"Current registered ML model for '{station_name}' is up to date. Training skipped.")
        return False

    except sqlite3.Error as e:
        logger.warning(f"Could not query model registry ({e}). Defaulting to retraining.")
        return True


def register_trained_model(
    env: WaidBoot,
    station_id: str,
    station_name: str,
    latest_period: str,
    train_samples_count: int,
    val_loss_mse: float
) -> None:
    """Registers the newly trained model version and artifacts into SQLite Feature Store."""
    waid_version = getattr(env, "waid_version", "v1.0.0")
    
    now = datetime.utcnow()
    trained_at = now.strftime("%Y-%m-%d %H:%M:%S")
    timestamp_tag = now.strftime("%Y%m%d_%H%M")
    
    model_version = f"{waid_version}_{latest_period}_{timestamp_tag}"
    
    model_path = str(env.ml_models_dir /  env.ml_model_h5_file)
    x_scaler_path = str(env.ml_models_dir / env.ml_input_scaler_pkl_file)
    y_scaler_path = str(env.ml_models_dir / env.ml_output_scaler_pkl_file)
    
    last_ecowitt_ts = get_max_timestamp(env)

    try:
        with sqlite3.connect(env.waid_db) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            
            cursor.execute(
                "UPDATE ml_model_registry SET is_active = 0 WHERE station_id = ?",
                (station_id,)
            )

            upsert_query = """
            INSERT INTO ml_model_registry (
                model_version, station_id, trained_at,
                last_ecowitt_timestamp, train_samples_count, x_scaler_path, 
                y_scaler_path, model_path, metrics_mse, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(model_version) DO UPDATE SET
                trained_at = excluded.trained_at,
                last_ecowitt_timestamp = excluded.last_ecowitt_timestamp,
                train_samples_count = excluded.train_samples_count,
                x_scaler_path = excluded.x_scaler_path,
                y_scaler_path = excluded.y_scaler_path,
                model_path = excluded.model_path,
                metrics_mse = excluded.metrics_mse,
                is_active = 1;
            """
            cursor.execute(upsert_query, (
                model_version, station_id, trained_at,
                last_ecowitt_ts, train_samples_count, x_scaler_path,
                y_scaler_path, model_path, float(val_loss_mse)
            ))
            conn.commit()

        logger.success(
            f"Model registered for '{station_name}' ({station_id})! "
            f"Version: '{model_version}' | Samples: {train_samples_count} | Validation MSE: {val_loss_mse:.6f}"
        )

    except sqlite3.Error as e:
        raise WError(f"Failed to register model in SQLite Feature Store: {e}", code=WaidExit.DATA_FAIL)


def train_model(env: WaidBoot, station_id: str, station_name: str, periods: list[str], min_training_days: int) -> int:
    """Executes incremental feature scaling, builds tf.data pipeline, compiles LSTM network, performs training, and saves model artifacts."""
    
    # 1. Fetch all timestamps from stg_ecowitt for global theoretical solar calculation
    query = "SELECT timestamp FROM stg_ecowitt ORDER BY timestamp ASC"
    try:
        with sqlite3.connect(env.waid_db) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            db_timestamps = [row[0] for row in rows]
    except sqlite3.Error as e:
        raise WError(f"Failed to fetch timestamps for theoretical solar feature: {e}", code=WaidExit.DATA_FAIL)

    if not db_timestamps:
        raise WError("No timestamps found in 'stg_ecowitt' for feature enrichment.", code=WaidExit.DATA_FAIL)

    logger.info("Calculating theoretical clear-sky solar radiation for tensor enrichment...")
    theoretical_all = calculate_theoretical_solar_radiation(
        np.array(db_timestamps), 
        env.ecowitt_latitude, 
        env.ecowitt_longitude, 
        env.tz_timezone
    )
    
    # --- DEBUG: Verifica del range del contributo solare teorico ---
    logger.debug(f"Physics Guardrail - Theoretical Solar Radiation calculation summary:")
    logger.debug(f"  - Count: {len(theoretical_all)}")
    logger.debug(f"  - Range: Min={theoretical_all.min():.2f} W/m², Max={theoretical_all.max():.2f} W/m²")

    # 2. Pass 1: Incremental Scaler Fitting (partial_fit) period by period to avoid OOM
    x_scaler = StandardScaler()
    y_scaler = StandardScaler()
    
    global_idx = 0
    total_samples = 0
    
    for p in periods:
        path_x = env.ml_tensors_dir / f'X_raw_{p}.pkl'
        path_y = env.ml_tensors_dir / f'Y_raw_{p}.pkl'
        
        if not path_x.exists() or not path_y.exists():
            raise WError(f"Missing raw tensor files for period: {p}", code=WaidExit.DATA_FAIL)
            
        X = joblib.load(path_x)
        y = joblib.load(path_y)
        n_samples, n_timesteps, _ = X.shape
        total_samples += n_samples
        
        theo_solar_3d = np.zeros((n_samples, n_timesteps, 1))
        for i in range(n_samples):
            curr_idx = global_idx + i
            if curr_idx + n_timesteps <= len(theoretical_all):
                theo_solar_3d[i, :, 0] = theoretical_all[curr_idx : curr_idx + n_timesteps]
            else:
                theo_solar_3d[i, :, 0] = theoretical_all[-n_timesteps:]
            logger.debug(f"Physics Guardrail - Period {p}: Sample {i} theoretical range [{theo_solar_3d[i].min():.1f} - {theo_solar_3d[i].max():.1f}]")
            
        X_enriched = np.concatenate([X, theo_solar_3d], axis=2)
        global_idx += n_samples
        
        # Validates tensor shapes for learning
        if X_enriched.shape[2] != env.n_input_features:
            raise WError(
                f"Input Feature Mismatch! Expected {env.n_input_features}, got {X_enriched.shape[2]}",
                code=WaidExit.DATA_FAIL
            )
            
        if y.shape[2] != env.n_output_features:
            raise WError(
                f"Target Feature Mismatch! Expected {env.n_output_features}, got {y.shape[2]}",
                code=WaidExit.DATA_FAIL
            )

        x_scaler.partial_fit(X_enriched.reshape(-1, env.n_input_features))
        y_scaler.partial_fit(y.reshape(-1, env.n_output_features))

    # Save Scalers
    os.makedirs(env.ml_models_dir, exist_ok=True)
    joblib.dump(x_scaler, env.ml_models_dir / env.ml_input_scaler_pkl_file)
    joblib.dump(y_scaler, env.ml_models_dir / env.ml_output_scaler_pkl_file)

    min_required_samples = min_training_days * 24
    logger.info(f"Total dataset samples across periods {periods}: {total_samples}")
    if total_samples < min_required_samples:
        raise WError(
            f"Guardrail Triggered: Available samples ({total_samples}) "
            f"< minimum required ({min_required_samples} samples for {min_training_days} days). Training aborted.",
            code=WaidExit.DATA_FAIL
        )

    # 3. Pass 2: Build tf.data.Dataset pipeline period by period
    datasets = []
    global_idx = 0
    
    for p in periods:
        path_x = env.ml_tensors_dir / f'X_raw_{p}.pkl'
        path_y = env.ml_tensors_dir / f'Y_raw_{p}.pkl'
        
        X = joblib.load(path_x)
        y = joblib.load(path_y)
        n_samples, n_timesteps, _ = X.shape
        
        theo_solar_3d = np.zeros((n_samples, n_timesteps, 1))
        for i in range(n_samples):
            curr_idx = global_idx + i
            if curr_idx + n_timesteps <= len(theoretical_all):
                theo_solar_3d[i, :, 0] = theoretical_all[curr_idx : curr_idx + n_timesteps]
            else:
                theo_solar_3d[i, :, 0] = theoretical_all[-n_timesteps:]
        X_enriched = np.concatenate([X, theo_solar_3d], axis=2)
        global_idx += n_samples
        
        X_scaled = x_scaler.transform(X_enriched.reshape(-1, env.n_input_features)).reshape(n_samples, n_timesteps, env.n_input_features)
        y_scaled = y_scaler.transform(y.reshape(-1, env.n_output_features)).reshape(n_samples, y.shape[1], env.n_output_features)
        
        ds_period = tf.data.Dataset.from_tensor_slices((X_scaled, y_scaled))
        datasets.append(ds_period)

    full_ds = datasets[0]
    for ds in datasets[1:]:
        full_ds = full_ds.concatenate(ds)

    # Train / Validation Split (80% / 20%)
    train_size = int(total_samples * 0.8)
    val_size = total_samples - train_size
    
    train_ds = full_ds.take(train_size).shuffle(buffer_size=10000).batch(32).prefetch(tf.data.AUTOTUNE)
    val_ds = full_ds.skip(train_size).take(val_size).batch(32).prefetch(tf.data.AUTOTUNE)

    # 4. Neural Network Architecture Definition
    TOTAL_OUTPUT_NODES = env.forecast_horizon_hours * env.n_output_features

    model = Sequential([
        Input(shape=(n_timesteps, env.n_input_features)),
        LSTM(64, return_sequences=False),
        Dropout(0.2),
        Dense(TOTAL_OUTPUT_NODES),
        Reshape((env.forecast_horizon_hours, env.n_output_features))
    ])
    
    model.compile(optimizer='adam', loss='mse')
    
    early_stopping = EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True
    )
    
    logger.info(f"Training Architecture: Input({n_timesteps}x{env.n_input_features}) -> Output({env.forecast_horizon_hours}x{env.n_output_features})")
    
    history = model.fit(
        train_ds, 
        epochs=30, 
        validation_data=val_ds,
        callbacks=[early_stopping],
        verbose=1
    )
    
    best_val_loss = min(history.history['val_loss'])
    
    # Evaluate validation performance in physical units using batched datasets
    val_preds_scaled = model.predict(val_ds)
    val_preds_denorm = denormalize_predictions(y_scaler, val_preds_scaled)
    
    y_val_list = []
    for _, y_batch in full_ds.skip(train_size).take(val_size).batch(1024):
        y_val_list.append(y_batch.numpy())
    y_val_arr = np.concatenate(y_val_list, axis=0)
    y_val_denorm = denormalize_predictions(y_scaler, y_val_arr)
    
    val_rmse = np.sqrt(np.mean((val_preds_denorm - y_val_denorm) ** 2))
    logger.info(f"Validation RMSE in original physical units: {val_rmse:.4f}")

    # Save Trained Model
    model_output_path = env.ml_models_dir / env.ml_model_h5_file
    
    model.save(model_output_path)
    logger.success(f"Model successfully saved to: {model_output_path.name}")

    # Update Registry
    latest_period = periods[-1]
    register_trained_model(env, station_id, station_name, latest_period, total_samples, best_val_loss)

    return WaidExit.SUCCESS


def get_available_periods(env: WaidBoot) -> list[str]:
    """Scans raw_tensors directory and returns a sorted list of period strings."""
    files = glob.glob(str(env.ml_tensors_dir / 'X_raw_*.pkl'))
    periods = sorted([os.path.basename(f).replace('X_raw_', '').replace('.pkl', '') for f in files])

    if not periods:
        raise WError(f"No valid tensor dataset files found in {env.ml_tensors_dir}", code=WaidExit.CRITICAL_FAIL)

    logger.info(f"Detected period datasets: {periods}")
    return periods


def main() -> int:
    try:
        env = WaidBoot()
    
        # Read setup mode from environment (0: normal, 1: reset db, 2: reset all, 3: force ML training)
        setup_mode = int(os.getenv("WAID_SETUP_MODE", "0"))

        # Inspect Hardware Accelerators
        gpus = tf.config.list_physical_devices('GPU')
        if not gpus:
            logger.warning("No hardware GPU detected: Training will proceed on CPU.")
        else:
            logger.info(f"Hardware GPU accelerator detected: count = {len(gpus)}")
            for gpu in gpus:
                logger.info(f" - {gpu}")

        # Fetch pre-computed station metadata from dbt table
        station_id, station_name, total_elevation, min_training_days, retrain_window_days, sensor_specs = get_station_metadata(env)
        
        # Ensure Model Registry schema exists
        ensure_model_registry_schema(env)

        # Detect Available Datasets
        periods_to_train = get_available_periods(env)
        latest_period = periods_to_train[-1]

        # Check if retraining is required based on guardrails or forced by setup_mode == 3
        if setup_mode == 3:
            logger.warning("WAID_SETUP_MODE=3 detected: Forcing ML model retraining, bypassing minimum training interval guardrails.")
        else:
            if not check_retrain_required(env, station_id, station_name, latest_period, min_training_days):
                return WaidExit.SUCCESS

        logger.info(
            f"Executing model training for station '{station_name}' (Elevation: {total_elevation}m) "
            f"across periods: {periods_to_train}"
        )
        return train_model(env, station_id, station_name, periods_to_train, min_training_days)

    except WError as e:
        logger.error(f"[WAID ERROR] {e.message}")
        return e.code

    except Exception:
        logger.exception("Unexpected failure during model training execution")
        return WaidExit.INTERNAL_ERROR


if __name__ == "__main__":
    sys.exit(main())