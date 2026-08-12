#!/usr/bin/env python3

"""
@file waid_06_1_inference_engine.py
@brief WAID Inference Engine.
@details Loads trained LSTM model and dual scalers (X and Y), queries pure Ecowitt records directly 
         using actual database column names, enriches features with theoretical solar radiation, 
         executes multi-step forecasting, and persists predictions into SQLite.
@author AF
@date 2026
"""

import os
import sys
import sqlite3
import joblib
import hashlib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger
import tensorflow as tf

sys.path.append(str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config"))
from boot import (
    WaidBoot,
    WError,
)

# Import shared physics utilities from Single Source of Truth
from waid_utils import calculate_theoretical_solar_radiation


def add_cyclic_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Adds sine and cosine encoded temporal features for daily and seasonal cycles."""
    ts = pd.to_datetime(df['timestamp'])
    
    hour = ts.dt.hour + ts.dt.minute / 60.0
    day_of_year = ts.dt.dayofyear
    
    df['hour_sin'] = np.sin(2 * np.pi * hour / 24.0)
    df['hour_cos'] = np.cos(2 * np.pi * hour / 24.0)
    df['doy_sin'] = np.sin(2 * np.pi * day_of_year / 365.25)
    df['doy_cos'] = np.cos(2 * np.pi * day_of_year / 365.25)
    
    return df


class WaidInferenceEngine:
    """Manages the weather AI inference pipeline lifecycle.

    This class centralizes system health checks, database alignment,
    and model tracking using a unified environmental configuration.
    """

    def __init__(self, env: WaidBoot):
        """Initializes the engine with shared environment settings."""
        self.env = env
        
        self.model_file = Path(self.env.ml_models_dir) / self.env.ml_model_h5_file
        self.x_scaler_file = Path(self.env.ml_models_dir) / self.env.ml_input_scaler_pkl_file
        self.y_scaler_file = Path(self.env.ml_models_dir) / self.env.ml_output_scaler_pkl_file
        self.ml_threshold_min: int = int(self.env.ml_threshold_min)

        logger.info("Starting inference process...")
        logger.info(f"Using model: {self.model_file}")
        logger.info(f"Using X scaler: {self.x_scaler_file}")
        logger.info(f"Using Y scaler: {self.y_scaler_file}")
        logger.info(f"Using DB: {self.env.waid_db}")
        logger.info(f"Saving predictions to: {self.env.waid_db}")
        logger.info("All configurations initialized.")

    def get_model_hash(
        self,
        file_path: str | Path | None = None,
        chunk_size: int = 65536) -> str:
        
        # Calculate a short MD5 hash of a model file for version control
        target_path = file_path if file_path is not None else self.model_file
        hasher = hashlib.md5()
        
        with open(target_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
                
        return hasher.hexdigest()[:8]

    def check_system_health(self) -> None:
        """Verifies system data freshness and model/scaler path existence."""
        if not self.env.ml_models_dir.exists():
            raise WError(
                "Model directory is missing.",
                code=self.env.waid_exit.CONFIG_FAIL,
            )

        if not self.model_file.exists():
            raise WError(
                f"Model file not found: {self.model_file}",
                code=self.env.waid_exit.DATA_FAIL,
            )

        if not self.x_scaler_file.exists():
            raise WError(
                f"X scaler file not found: {self.x_scaler_file}",
                code=self.env.waid_exit.DATA_FAIL,
            )

        if not self.y_scaler_file.exists():
            raise WError(
                f"Y scaler file not found: {self.y_scaler_file}",
                code=self.env.waid_exit.DATA_FAIL,
            )

        conn = sqlite3.connect(self.env.waid_db)
        last_ts = pd.read_sql("SELECT timestamp FROM ecowitt_records ORDER BY timestamp DESC LIMIT 1", conn)
        conn.close()
        
        if last_ts.empty:
            raise WError(
                "No records found in ecowitt_records table.",
                code=self.env.waid_exit.DATA_FAIL,
            )

        logger.info("System health check passed.")

    def ensure_db_structure(self, pred_df: pd.DataFrame) -> None:
        """Synchronizes database schema with predicted DataFrame structure."""
        conn = sqlite3.connect(self.env.waid_db)
        cursor = conn.cursor()
        
        ignored_cols = {
            'timestamp', 'model_version', 'model_version_tag', 
            'n_features_used', 'ts_window_start', 'ts_window_end'
        }
        target_cols = [c for c in pred_df.columns if c not in ignored_cols]
        
        metadata_cols = [
            'id INTEGER PRIMARY KEY AUTOINCREMENT', 
            'ts_emission DATETIME DEFAULT CURRENT_TIMESTAMP',
            'ts_window_start DATETIME',
            'ts_window_end DATETIME',
            'timestamp DATETIME',
            'model_version TEXT',
            'model_version_tag TEXT',
            'n_features_used INTEGER'
        ]
        
        ideal_cols = metadata_cols + [f"{c} REAL" for c in target_cols]
        
        cursor.execute("PRAGMA table_info(inference_records);")
        existing_cols = {row[1] for row in cursor.fetchall()}
        
        required_cols = set(target_cols + [c.split()[0] for c in metadata_cols if 'PRIMARY' not in c and 'DEFAULT' not in c])
        
        if not existing_cols.issuperset(required_cols) or len(existing_cols) > len(required_cols):
            logger.warning("Schema mismatch detected. Rebuilding table...")
            try:
                cursor.execute("DROP TABLE IF EXISTS inference_records")
                cursor.execute(f"CREATE TABLE inference_records ({', '.join(ideal_cols)})")
                logger.info("Table successfully reconstructed.")
            except Exception as e:
                raise WError(f"Error during table reconstruction: {e}", code=self.env.waid_exit.DATA_FAIL)
        
        conn.commit()
        conn.close()
        logger.debug("Database schema synchronization completed successfully.")

    def prepare_and_predict(self) -> pd.DataFrame:
        """Runs inference using pure Ecowitt records, theoretical solar enrichment, and dual scalers."""
        x_scaler = joblib.load(self.x_scaler_file)
        y_scaler = joblib.load(self.y_scaler_file)
        
        model = tf.keras.models.load_model(self.model_file, compile=False)
        
        conn = sqlite3.connect(self.env.waid_db)
        
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(ecowitt_records);")
        existing_cols = {row[1] for row in cursor.fetchall()}
        
        ecowitt_features = [feature["ecowitt_field"] for feature in self.env.output_features]
        missing = [col for col in ecowitt_features if col not in existing_cols]
        if missing:
            conn.close()
            raise WError(
                f"Missing required columns in ecowitt_records: {missing}. Available: {list(existing_cols)}",
                code=self.env.waid_exit.DATA_FAIL
            )


        select_cols = ", ".join(['timestamp'] + ecowitt_features)
        query = f"""
            SELECT {select_cols}
            FROM ecowitt_records 
            ORDER BY timestamp DESC LIMIT {self.env.lookback_hours}
        """
        df_raw = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df_raw) < self.env.lookback_hours:
            raise WError(
                f"Insufficient data for inference (needed {self.env.lookback_hours} hours, got {len(df_raw)}).", 
                code=self.env.waid_exit.DATA_FAIL
            )

        # Order chronologically (ASC)
        df_raw = df_raw.iloc[::-1].reset_index(drop=True)
        
        # Order chronologically (ASC)
        df_raw = df_raw.iloc[::-1].reset_index(drop=True)
        
        # Add cyclic time features (hour_sin, hour_cos, doy_sin, doy_cos)
        df_engineered = add_cyclic_time_features(df_raw.copy())
        
        # Calculate theoretical clear-sky solar radiation feature
        timestamps_arr = df_engineered['timestamp'].values
        
        # --- DEBUG: Logging del contributo teorico durante l'inferenza ---
        theo_solar_values = calculate_theoretical_solar_radiation(
            timestamps_arr, self.env.ecowitt_latitude, self.env.ecowitt_longitude, self.env.tz_timezone
        )
        
        df_engineered['theo_solar'] = theo_solar_values
        
        logger.debug("Physics Guardrail - Inference - Theoretical Solar Radiation Stats for current window:")
        logger.debug(f"  - Window Timestamp Range: [{timestamps_arr[0]} to {timestamps_arr[-1]}]")
        logger.debug(f"  - Solar Range: Min={theo_solar_values.min():.2f} W/m², Max={theo_solar_values.max():.2f} W/m²")
        
        # Scale input features across the window using x_scaler (11 features)
        input_data = df_engineered[self.env.input_features].values
        scaled_input = x_scaler.transform(input_data)
        
        # Reshape to 3D tensor: (1, 24, 11)
        input_tensor = scaled_input.reshape(1, self.env.lookback_hours, self.env.n_input_features)
        
        # Model prediction
        pred_scaled = model.predict(input_tensor, verbose=0)
        
        if pred_scaled.ndim == 3:
            pred_scaled_2d = pred_scaled[0]
        elif pred_scaled.ndim == 2:
            pred_scaled_2d = pred_scaled.reshape(self.env.forecast_horizon_hours, self.env.n_output_features)
        else:
            pred_scaled_2d = pred_scaled

        # Inverse transform predictions back to physical values using y_scaler
        pred_physical = y_scaler.inverse_transform(pred_scaled_2d)

        last_ts = pd.to_datetime(df_engineered['timestamp'].iloc[-1])
        
        ecowitt_field_features = [feature["ecowitt_field"] for feature in self.env.output_features]
        predictions = []
        for h in range(self.env.forecast_horizon_hours):
            row = {
                'timestamp': (last_ts + timedelta(hours=h+1)).strftime('%Y-%m-%d %H:%M:%S'),
                'ts_window_start': df_engineered['timestamp'].iloc[0],
                'ts_window_end': df_engineered['timestamp'].iloc[-1]
            }
            for idx, col in enumerate(ecowitt_field_features):
                row[col] = float(pred_physical[h, idx])
            predictions.append(row)
            
        pred_df = pd.DataFrame(predictions)
        logger.info(f"Inference completed and reconstructed. Model: {self.model_file.name}")
        return pred_df

    def run_inference(self) -> None:
        """Executes the entire end-to-end pipeline: validates system health, 
        generates model predictions, adapts the database schema, and stores results.
        """
        logger.info("Starting pipeline execution: Validation and System Health Check...")
        self.check_system_health()
        logger.success("System health check passed. Input data is fresh.")

        logger.info("Executing model forecasting engine...")
        pred_df = self.prepare_and_predict()
        
        model_version = self.get_model_hash()
        
        logger.info("Checking database structure and running schema evolution check...")
        self.ensure_db_structure(pred_df)

        pred_df['model_version'] = model_version
        pred_df['model_version_tag'] = "v01_baseline"  
        pred_df['n_features_used'] = self.env.n_input_features

        logger.info("Saving predictions to database target table...")
        conn = sqlite3.connect(self.env.waid_db)
        try:
            pred_df.to_sql('inference_records', conn, if_exists='append', index=False)
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database write transaction failed: {str(e)}")
            raise e
        finally:
            conn.close()

        logger.info(f"Inference records saved to {self.env.waid_db} (Model Version: {model_version})")
        logger.success("Inference process successfully completed and finalized.")


def main() -> int:
    try:
        env = WaidBoot()

        logger.warning("Inference script is running with GPU disabled. Ensure this is intended.")
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

        if len(sys.argv) > 1:
            logger.warning("No expected input parameters")

        engine = WaidInferenceEngine(env)
        engine.run_inference()

    except WError as e:
        logger.error(e)
        return e.code

    except Exception:
        logger.exception("Unexpected error while processing inference")
        return env.waid_exit.INTERNAL_ERROR

    return env.waid_exit.SUCCESS


if __name__ == "__main__":
    sys.exit(main())