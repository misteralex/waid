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
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import sys
import glob
import sqlite3
import numpy as np
import joblib
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Tuple
from loguru import logger
import tensorflow as tf
from tensorflow.keras import Sequential, Input
from tensorflow.keras.layers import LSTM, Dropout, Dense, Reshape 
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler

if not os.environ.get("WAID_SOURCE"):
    sys.exit("[CRITICAL] WAID_SOURCE environment variable is missing. Export it first.")

sys.path.append(str(Path(os.environ.get("WAID_SOURCE")) / "config"))
from boot import (
    WaidBoot,
    WError,
    WaidExit,
)

# Import shared utilities from Single Source of Truth
from waid_shared import get_station_metadata


def denormalize_predictions(y_scaler: StandardScaler, preds_scaled: np.ndarray) -> np.ndarray:
    """Denormalizes predictions using the provided y_scaler supporting 2D or 3D arrays.

    @param y_scaler Fitted StandardScaler instance for target outputs.
    @param preds_scaled Scaled prediction numpy array (2D or 3D).
    @return Denormalized numpy array matching original physical dimensions.
    """
    original_shape = preds_scaled.shape
    if len(original_shape) == 3:
        batch_size, horizon, n_features = original_shape
        preds_2d = preds_scaled.reshape(-1, n_features)
        preds_denorm_2d = y_scaler.inverse_transform(preds_2d)
        return preds_denorm_2d.reshape(batch_size, horizon, n_features)
    else:
        return y_scaler.inverse_transform(preds_scaled)


def ensure_model_registry_schema(env: WaidBoot) -> None:
    """Ensures ml_model_registry table exists before performing registration operations.

    @param env Initialized framework environment context (WaidBoot).
    @return None
    """
    station_id = env.ecowitt_station_id
    
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
    """Retrieves maximum Ecowitt timestamp from staging database.

    @param env Initialized framework environment context (WaidBoot).
    @return ISO formatted maximum timestamp string or current UTC time fallback.
    """
    query = "SELECT MAX(timestamp) FROM stg_ecowitt"
    last_ecowitt_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

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
    """Checks if a new training run is required based on registry status and minimum training interval.

    @param env Initialized framework environment context (WaidBoot).
    @param station_id Identifier of target station.
    @param station_name Descriptive name of weather station.
    @param latest_available_period String representation of latest dataset period (YYYY_MM).
    @param min_training_days Minimum number of days required between training runs.
    @return True if retraining should proceed, False otherwise.
    """
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
        last_trained_at = datetime.strptime(last_trained_at_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        days_since_last_training = (datetime.now(timezone.utc) - last_trained_at).days

        logger.info(f"Last model trained at: [{last_trained_at_str}] ({days_since_last_training} days ago)")
        logger.info(f"Minimum training interval / days guardrail: [{min_training_days}] days")

        # Guardrail: Do not retrain if fewer days have passed than min_training_days
        if days_since_last_training < min_training_days:
            logger.success(
                f"Retraining skipped: Only {days_since_last_training} days passed since last training, "
                f"which is less than the required minimum interval of {min_training_days} days."
            )
            return False

        if latest_available_period.replace("_", "-") > last_trained_ts[:7]:
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
    """Registers the newly trained model version and artifacts into SQLite Feature Store.

    @param env Initialized framework environment context (WaidBoot).
    @param station_id Identifier of weather station.
    @param station_name Name of weather station.
    @param latest_period Most recent training period string.
    @param train_samples_count Total number of training sample windows.
    @param val_loss_mse Best validation Mean Squared Error.
    @return None
    """
    waid_version = getattr(env, "waid_version", "v1.0.0")
    
    now = datetime.now(timezone.utc)
    trained_at = now.strftime("%Y-%m-%d %H:%M:%S")
    timestamp_tag = now.strftime("%Y%m%d_%H%M")
    
    model_version = f"{waid_version}_{latest_period}_{timestamp_tag}"
    
    model_path = str(env.ml_models_dir / env.ml_model_h5_file)
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


def train_model(
    env: WaidBoot, 
    station_id: str, 
    station_name: str, 
    periods: List[str], 
    min_training_days: int
) -> int:
    """Executes model training pipeline including scaling, architecture setup, and registration.

    @param env Initialized framework environment context (WaidBoot).
    @param station_id Target station identifier.
    @param station_name Station descriptive name.
    @param periods List of period dataset keys available for training.
    @param min_training_days Guardrail training frequency limit.
    @return Execution status code (WaidExit).
    """
    # 1. Incremental Scaler Fitting (Directly from 11-feature Tensors on disk)
    x_scaler, y_scaler = StandardScaler(), StandardScaler()
    total_samples = 0
    
    for p in periods:
        X = joblib.load(env.ml_tensors_dir / f'X_raw_{p}.pkl')
        y = joblib.load(env.ml_tensors_dir / f'Y_raw_{p}.pkl')
        n_samples, n_timesteps, n_features = X.shape
        total_samples += n_samples
        
        # X already contains all 11 aligned input features
        x_scaler.partial_fit(X.reshape(-1, env.n_input_features))
        y_scaler.partial_fit(y.reshape(-1, env.n_output_features))

    # Save Scalers
    joblib.dump(x_scaler, env.ml_models_dir / env.ml_input_scaler_pkl_file)
    joblib.dump(y_scaler, env.ml_models_dir / env.ml_output_scaler_pkl_file)

    # 2. Build Dataset Pipeline
    datasets = []
    for p in periods:
        X = joblib.load(env.ml_tensors_dir / f'X_raw_{p}.pkl')
        y = joblib.load(env.ml_tensors_dir / f'Y_raw_{p}.pkl')
        n_samples, n_timesteps, _ = X.shape
        
        # Direct transformation using consistent Scaler
        X_scaled = x_scaler.transform(X.reshape(-1, env.n_input_features)).reshape(n_samples, n_timesteps, env.n_input_features)
        y_scaled = y_scaler.transform(y.reshape(-1, env.n_output_features)).reshape(n_samples, y.shape[1], env.n_output_features)
        
        datasets.append(tf.data.Dataset.from_tensor_slices((X_scaled, y_scaled)))

    full_ds = datasets[0]
    for ds in datasets[1:]:
        full_ds = full_ds.concatenate(ds)

    # Train / Validation Split (80% / 20%)
    train_size = int(total_samples * 0.8)
    val_size = total_samples - train_size
    
    train_ds = full_ds.take(train_size).shuffle(buffer_size=10000).batch(32).prefetch(tf.data.AUTOTUNE)
    val_ds = full_ds.skip(train_size).take(val_size).batch(32).prefetch(tf.data.AUTOTUNE)

    # 3. Neural Network Architecture Definition
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
    
    # Evaluate validation performance in physical units
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


def get_available_periods(env: WaidBoot) -> List[str]:
    """Scans raw_tensors directory and returns a sorted list of period strings.

    @param env Initialized framework environment context (WaidBoot).
    @return Sorted list of period strings detected in raw_tensors folder.
    """
    files = glob.glob(str(env.ml_tensors_dir / 'X_raw_*.pkl'))
    periods = sorted([os.path.basename(f).replace('X_raw_', '').replace('.pkl', '') for f in files])

    if not periods:
        raise WError(f"No valid tensor dataset files found in {env.ml_tensors_dir}", code=WaidExit.CRITICAL_FAIL)

    logger.info(f"Detected period datasets: {periods}")
    return periods


def main() -> int:
    """Main entry point for ML model training and feature store synchronization.

    @return Process exit status code matching WaidExit enum.
    """
    try:
        env = WaidBoot()

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

        # Read setup mode from environment (0: normal, 1: reset db, 2: reset all, 3: force ML training)
        # Check if retraining is required based on guardrails or forced by setup_mode == 3
        if env.setup_mode == 3:
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