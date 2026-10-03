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
           (hour_sin, hour_cos, doy_sin, doy_cos) and theoretical solar radiation. 
           Total 11 features per timestep.
         - Target Matrix (Y): 3D local feature delta dynamics for the subsequent 
           forecast horizon relative to current time t:
           Y_h = Feature(t + h) - Feature(t), for h in [1..horizon]

@author AF
@date 2026
"""

import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import sys
import argparse
from loguru import logger
from pathlib import Path
from typing import Tuple, List

import numpy as np
import pandas as pd
import joblib
import sqlite3

if not os.environ.get("WAID_SOURCE"):
    sys.exit("[CRITICAL] WAID_SOURCE environment variable is missing. Export it first.")

sys.path.append(str(Path(os.environ.get("WAID_SOURCE")) / "config"))
from boot import (
    WaidBoot,
    WError,
    WaidExit,
    validate_period,
)

# Import shared utilities from Single Source of Truth
from waid_shared import calculate_theoretical_solar_radiation

# ==============================================================================
# CORE DATA PROCESSING FUNCTIONS
# ==============================================================================

def load_ecowitt_telemetry(env: WaidBoot, period: pd.Timestamp) -> pd.DataFrame:
    """Extracts, cleans, and enforces hourly temporal continuity for Ecowitt sensor telemetry.

    Extends start boundary by lookback_hours and end boundary by forecast_horizon_hours
    to preserve complete monthly coverage for 3D tensor generation.

    @param env Initialized framework environment context (WaidBoot).
    @param period Target month as pd.Timestamp (YYYY-MM).
    @return Cleaned, hourly-reindexed DataFrame containing target features.
    """
    if not os.path.exists(env.waid_db):
        raise WError(f"Database file not found at: {env.waid_db}", code=WaidExit.INPUT_FAIL)

    conn = sqlite3.connect(env.waid_db)
    
    month_start = pd.Timestamp(period.strftime("%Y-%m-01 00:00:00"))
    month_end = period + pd.offsets.MonthEnd(1)
    
    # Extended boundaries for lookback and forecast windows
    extended_start = month_start - pd.Timedelta(hours=env.lookback_hours)
    extended_end = month_end + pd.Timedelta(hours=env.forecast_horizon_hours)
    
    start_date = extended_start.strftime("%Y-%m-%d %H:%M:%S")
    end_date = extended_end.strftime("%Y-%m-%d %H:%M:%S")

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
        raise WError(
            f"No records found in 'stg_ecowitt' for period {start_date} to {end_date}", 
            code=WaidExit.INPUT_FAIL
        )

    # Standardize datetime objects and eliminate chronological duplicates
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').drop_duplicates(subset=['timestamp']).reset_index(drop=True)

    # Construct strict hourly grid based on start and end timestamps
    full_range = pd.date_range(start=df['timestamp'].min(), end=df['timestamp'].max(), freq='1h')
    missing_timestamps = full_range.difference(df['timestamp'])

    # Handle temporal gaps if detected
    if not missing_timestamps.empty:
        logger.warning(
            f"Detected {len(missing_timestamps)} missing hourly records in telemetry timeline. "
            "Reindexing to strict 1h grid and applying linear interpolation."
        )
        logger.debug(f"Missing timestamps: {missing_timestamps.strftime('%Y-%m-%d %H:%M').tolist()}")
        
        # Reindex dataframe to complete hourly range
        df = df.set_index('timestamp').reindex(full_range)
        df.index.name = 'timestamp'
        
        # Interpolate feature values linearly
        df[standard_features] = df[standard_features].interpolate(method='linear')
        
        # Check for unhandled NaNs in standard features prior to boundary fill
        nan_cols = df[standard_features].isna().sum()
        missing_features = nan_cols[nan_cols > 0]

        if not missing_features.empty:
            details = ", ".join(
                f"{feat}: {count} missing"
                for feat, count in missing_features.items()
            )
            logger.warning(
                f"NaN values detected in telemetry boundary features. "
                "Applying forward and backward fill (ffill/bfill) to preserve timeline integrity."
            )
            logger.debug(f"Missing feature details -> [{details}]")
            
            df[standard_features] = df[standard_features].ffill().bfill()
        
        df = df.reset_index()
    else:
        logger.info("Timeline continuity check passed: no missing hourly records.")

    logger.info(
        f"Loaded {len(df)} validated hourly observations (including lookback/forecast buffers) "
        f"for period {period.strftime('%Y-%m')}."
    )
    return df


def compute_temporal_embeddings(
    env: WaidBoot, 
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Computes sine/cosine cyclical transformations and theoretical solar radiation.

    Encodes 'Hour of Day' (0-23) and 'Day of Year' (1-365) as continuous
    2D cyclical coordinates and calculates deterministic clear-sky solar radiation.

    @param env Initialized framework environment context (WaidBoot).
    @param df Input DataFrame containing a validated 'timestamp' column and meteorological features.
    @return Copy of input DataFrame enriched with 5 additional feature columns.
    """
    df = df.copy()
    hour = df['timestamp'].dt.hour
    doy = df['timestamp'].dt.dayofyear

    df['hour_sin'] = np.sin(2 * np.pi * hour / 24.0)
    df['hour_cos'] = np.cos(2 * np.pi * hour / 24.0)
    df['doy_sin'] = np.sin(2 * np.pi * doy / 365.25)
    df['doy_cos'] = np.cos(2 * np.pi * doy / 365.25)

    # Compute theoretical solar radiation aligned with UTC timeline
    ts_utc = df['timestamp']
    if ts_utc.dt.tz is None:
        ts_utc = ts_utc.dt.tz_localize('UTC')
    else:
        ts_utc = ts_utc.dt.tz_convert('UTC')

    humidity_vals = df['outdoor_humidity'].values if 'outdoor_humidity' in df.columns else df['humidity'].values

    df['theo_solar'] = calculate_theoretical_solar_radiation(
        ts_utc.values,
        humidity=humidity_vals,
        input_tz="UTC",
        lat=env.ecowitt_latitude,
        lon=env.ecowitt_longitude
    )

    return df


def generate_sliding_window_tensors(
    env: WaidBoot, 
    df: pd.DataFrame, 
    lookback: int, 
    forecast: int,
) -> Tuple[np.ndarray, np.ndarray, pd.Series]:
    """Vectorized construction of multi-feature 3D input tensors (X) and 3D target delta tensors (Y).

    @param env Initialized framework environment context (WaidBoot).
    @param df Processed DataFrame containing telemetry, embeddings, and solar features.
    @param lookback Number of historical timesteps (hours) per input window.
    @param forecast Number of future timesteps (hours) per target horizon.
    @return Tuple containing:
            - X (np.ndarray): 3D input tensor of shape (samples, lookback, 11), dtype float32.
            - Y (np.ndarray): 3D target deltas array of shape (samples, forecast, 6), dtype float32.
            - timestamps_series (pd.Series): Timestamps corresponding to current reference time t.
    """
    standard_features = [feature["standard"] for feature in env.output_features]
    feature_matrix = df[standard_features].values.astype(np.float32)
    
    cyclical_matrix = df[['hour_sin', 'hour_cos', 'doy_sin', 'doy_cos']].values.astype(np.float32)
    theo_solar_matrix = df[['theo_solar']].values.astype(np.float32)
    
    combined_features = np.concatenate([feature_matrix, cyclical_matrix, theo_solar_matrix], axis=1)
    
    total_records = len(df)
    num_samples = total_records - lookback - forecast + 1

    if num_samples <= 0:
        return (
            np.empty((0, lookback, 11), dtype=np.float32),
            np.empty((0, forecast, 6), dtype=np.float32),
            pd.Series([], name="timestamp_t", dtype="datetime64[ns]")
        )

    # Generate 3D input windows X (shape: num_samples, lookback, 11)
    X_views = np.lib.stride_tricks.sliding_window_view(
        combined_features, window_shape=(lookback, combined_features.shape1 if hasattr(combined_features, 'shape1') else combined_features.shape[1])
    )
    X = X_views[:num_samples, 0, :, :].copy()

    # Generate 3D future feature windows
    Y_views = np.lib.stride_tricks.sliding_window_view(
        feature_matrix, window_shape=(forecast, feature_matrix.shape[1])
    )
    future_features = Y_views[lookback : lookback + num_samples, 0, :, :]

    # Current features at t (index lookback - 1)
    current_features = feature_matrix[lookback - 1 : lookback - 1 + num_samples, np.newaxis, :]

    # Target deltas Y (shape: num_samples, forecast, 6)
    Y = future_features - current_features

    # Reference timestamps t
    t_curr_indices = np.arange(lookback - 1, lookback - 1 + num_samples)
    timestamps_series = df['timestamp'].iloc[t_curr_indices].reset_index(drop=True)
    timestamps_series.name = "timestamp_t"

    return X, Y, timestamps_series


# ==============================================================================
# WORKFLOW ACTIONS
# ==============================================================================

def prepare_raw_data(env: WaidBoot, args: argparse.Namespace) -> int:
    """Generates and serializes 3D feature and target tensors to disk.

    @param env Initialized environment context (WaidBoot).
    @param args Parsed command line arguments containing the target period.
    @return Exit status code (WaidExit).
    """
    logger.info(f"Starting 3D raw data preparation for period: {args.period.strftime('%Y-%m')}")
    
    df_raw = load_ecowitt_telemetry(env, args.period)
    df_features = compute_temporal_embeddings(env, df_raw)

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
    """Performs verification and logs metadata about the generated 3D tensors.

    @param env Initialized environment context (WaidBoot).
    @param args Parsed command line arguments containing the target period.
    @return None
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
    """Main entry point for the tensor preparation step.

    @return Process exit code matching WaidExit enum.
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