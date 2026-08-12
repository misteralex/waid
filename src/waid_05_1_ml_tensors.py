#!/usr/bin/env python3

"""
@file waid_05_1_ml_tensors.py
@brief Multi-feature 3D tensor generator for the WAID engine.
@details Constructs historical 3D input feature tensors (X) and multi-step 3D target 
         delta arrays (Y) for Weather AI Deterministic-nowcasting (WAID).
         
         Operational Principles:
         - Local Autonomy: Relies strictly on local Ecowitt station telemetry 
           from SQLite staging.
         - Input Features (X): 3D sliding window (lookback x features) across 6 key 
           meteorological variables combined with cyclical temporal embeddings 
           (hour_sin, hour_cos, doy_sin, doy_cos). Total 10 features per timestep.
         - Target Matrix (Y): 3D local feature delta dynamics for the subsequent 
           forecast horizon relative to current time t:
           Y_h = Feature(t + h) - Feature(t), for h in [1..horizon]

@author WAID Core Team
@date 2026
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Tuple, List

import numpy as np
import pandas as pd
import joblib
import sqlite3

# Inject configuration path into python execution environment
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import (
    WaidBoot,
    validate_period,
    WError,
    WaidExit,
)

# Logger setup initialized by framework environment
logger = logging.getLogger(__name__)

# ==============================================================================
# CORE DATA PROCESSING FUNCTIONS
# ==============================================================================

def load_ecowitt_telemetry(env: WaidBoot, period: pd.Timestamp) -> pd.DataFrame:
    """
    Extracts and cleans hourly Ecowitt sensor telemetry from SQLite for a given period.
    Extends the start query boundary by lookback_hours (t - lookback) to avoid 
    dropping tensors for the first day of the target month.

    Args:
        env (WaidBoot): Initialized framework environment context.
        period (pd.Timestamp): Target month in YYYY-MM format.

    Returns:
        pd.DataFrame: Cleaned DataFrame containing all target features and timestamps.

    Raises:
        WError: If table access fails or no valid records are found.
    """
    if not os.path.exists(env.waid_db):
        raise WError(f"Database file not found at: {env.waid_db}", code=WaidExit.INPUT_FAIL)

    conn = sqlite3.connect(env.waid_db)
    
    # Define start boundary with lookback buffer to preserve full first-day samples
    month_start = pd.Timestamp(period.strftime("%Y-%m-01 00:00:00"))
    extended_start = month_start - pd.Timedelta(hours=env.lookback_hours)
    
    start_date = extended_start.strftime("%Y-%m-%d %H:%M:%S")
    end_date = (period + pd.offsets.MonthEnd(1)).strftime("%Y-%m-%d 23:59:59")

    standard_features = [feature["standard"] for feature in env.output_features]
    cols_sql = ", ".join(["timestamp"] + standard_features)
    query = f"""
        SELECT {cols_sql}
        FROM stg_ecowitt
        WHERE timestamp >= '{start_date}' AND timestamp <= '{end_date}'
        ORDER BY timestamp ASC
    """
    
    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()

    if df.empty:
        raise WError(f"No records found in 'stg_ecowitt' for period {start_date} to {end_date}", code=WaidExit.INPUT_FAIL)

    # Enforce datetime type and eliminate chronological duplicates
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').drop_duplicates(subset=['timestamp']).reset_index(drop=True)

    logger.info(f"Loaded {len(df)} validated observations (including lookback buffer) for period {period.strftime('%Y-%m')}.")
    return df


def compute_temporal_embeddings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes sine/cosine cyclical transformations for temporal variables.

    Encodes 'Hour of Day' (0-23) and 'Day of Year' (1-365) as continuous
    2D cyclical coordinates to preserve temporal continuity across boundaries.

    Args:
        df (pd.DataFrame): DataFrame containing a validated 'timestamp' column.

    Returns:
        pd.DataFrame: Copy of input DataFrame enriched with 4 cyclical feature columns.
    """
    df = df.copy()
    hour = df['timestamp'].dt.hour
    doy = df['timestamp'].dt.dayofyear

    df['hour_sin'] = np.sin(2 * np.pi * hour / 24.0)
    df['hour_cos'] = np.cos(2 * np.pi * hour / 24.0)
    df['doy_sin'] = np.sin(2 * np.pi * doy / 365.25)
    df['doy_cos'] = np.cos(2 * np.pi * doy / 365.25)

    return df


def generate_sliding_window_tensors(
    env: WaidBoot, 
    df: pd.DataFrame, 
    lookback: int, 
    forecast: int
) -> Tuple[np.ndarray, np.ndarray, pd.Series]:
    """
    Constructs multi-feature 3D sliding window input tensors (X) and 3D target delta tensors (Y).

    Args:
        df (pd.DataFrame): Input DataFrame with meteo features and cyclical embeddings.
        lookback (int): Number of historical lookback hours.
        forecast (int): Number of future forecasting hours.

    Returns:
        Tuple[np.ndarray, np.ndarray, pd.Series]:
            - X (np.ndarray): 3D Input feature array of shape (samples, lookback, 10), dtype float32.
            - Y (np.ndarray): 3D Target deltas array of shape (samples, forecast, 6), dtype float32.
            - timestamps_t (pd.Series): Series of timestamps corresponding to current time t.
    """
    standard_features = [feature["standard"] for feature in env.output_features]
    feature_matrix = df[standard_features].values
    
    # Combine meteorological features with cyclical temporal embeddings per timestep
    cyclical_matrix = df[['hour_sin', 'hour_cos', 'doy_sin', 'doy_cos']].values  # Shape: (total_records, 4)
    combined_features = np.concatenate([feature_matrix, cyclical_matrix], axis=1)  # Shape: (total_records, 10)
    
    timestamps = df['timestamp']

    X_list = []
    Y_list = []
    timestamps_t = []

    total_records = len(df)
    max_valid_idx = total_records - lookback - forecast

    for i in range(max_valid_idx + 1):
        # Index of current time t (end of lookback window)
        t_curr_idx = i + lookback - 1
        
        # 3D input window: shape (lookback, 10)
        x_window = combined_features[i : i + lookback]
        
        # 3D target delta window: future features minus current features at t
        current_features = feature_matrix[t_curr_idx]
        future_features = feature_matrix[t_curr_idx + 1 : t_curr_idx + 1 + forecast]
        y_window = future_features - current_features  # Shape: (forecast, 6)

        X_list.append(x_window)
        Y_list.append(y_window)
        timestamps_t.append(timestamps.iloc[t_curr_idx])

    X = np.array(X_list, dtype=np.float32)
    Y = np.array(Y_list, dtype=np.float32)
    timestamps_series = pd.Series(timestamps_t, name="timestamp_t")

    return X, Y, timestamps_series


# ==============================================================================
# WORKFLOW ACTIONS
# ==============================================================================

def prepare_raw_data(env: WaidBoot, args: argparse.Namespace) -> int:
    """
    Generates and serializes 3D feature and target tensors to disk.

    Args:
        env (WaidBoot): Initialized environment context.
        args (argparse.Namespace): Parsed command line arguments.

    Returns:
        int: Execution result code.
    """
    logger.info(f"Starting 3D raw data preparation for period: {args.period.strftime('%Y-%m')}")
    
    df_raw = load_ecowitt_telemetry(env, args.period)
    df_features = compute_temporal_embeddings(df_raw)

    X, Y, timestamps_t = generate_sliding_window_tensors(
        env,
        df_features,
        lookback=env.lookback_hours, 
        forecast=env.forecast_horizon_hours
    )

    if len(X) == 0:
        logger.warning(f"No continuous temporal windows could be created for {args.period.strftime('%Y-%m')}.")
        return WaidExit.SUCCESS

    os.makedirs(env.ml_tensors_dir, exist_ok=True)

    x_path = Path(env.ml_tensors_dir) / f"X_raw_{args.period.strftime('%Y_%m')}.pkl"
    y_path = Path(env.ml_tensors_dir) / f"Y_raw_{args.period.strftime('%Y_%m')}.pkl"
    ts_path = Path(env.ml_tensors_dir) / f"timestamps_{args.period.strftime('%Y_%m')}.pkl"

    joblib.dump(X, x_path)
    joblib.dump(Y, y_path)
    joblib.dump(timestamps_t, ts_path)

    logger.info(f"Generated 3D tensors successfully - X: {X.shape}, Y: {Y.shape}")
    return WaidExit.SUCCESS


def inspect_tensors(env: WaidBoot, args: argparse.Namespace) -> None:
    """
    Performs verification and logs metadata about the generated 3D tensors.

    Args:
        env (WaidBoot): Initialized environment context.
        args (argparse.Namespace): Parsed command line arguments.
    """
    x_path = Path(env.ml_tensors_dir) / f"X_raw_{args.period.strftime('%Y_%m')}.pkl"
    if x_path.exists():
        X = joblib.load(x_path)
        logger.info(
            f"Tensor inspection - Shape: {X.shape} "
            f"(Samples: {X.shape[0]}, Timesteps/Lookback: {X.shape[1]}h, Features: {X.shape[2]})"
        )


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

def main() -> int:
    """
    Main entry point for the tensor preparation step.
    
    Returns:
        int: Process exit code matching WaidExit enum.
    """
    try:
        env = WaidBoot()
        
        parser = argparse.ArgumentParser(
            description="WAID: Prepare deterministic-nowcasting 3D training tensors with local telemetry",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "--period",
            type=validate_period,
            help="Target month in YYYY-MM format",
        )

        if len(sys.argv) == 1:
            parser.print_help()
            logger.error("You must specify a valid input")
            return WaidExit.INPUT_FAIL
        
        args = parser.parse_args()
        result = prepare_raw_data(env, args)
        
        if result != WaidExit.SUCCESS:
            return result
            
        inspect_tensors(env, args)
        logger.info(f"Raw 3D tensors saved under: {env.ml_tensors_dir}")
        logger.info(f"Processed period: {args.period.strftime('%Y-%m')}")
        
    except WError as e:
        logger.error(e)
        return e.code

    except Exception:
        logger.exception("Unexpected error during 3D tensor generation")
        return WaidExit.INTERNAL_ERROR

    return WaidExit.SUCCESS


if __name__ == "__main__":
    sys.exit(main())