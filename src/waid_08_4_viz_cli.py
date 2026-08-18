#!/usr/bin/env python3

"""
@file waid_08_4_viz_cli.py
@brief CLI visualizer for WAID operational forecasts including ERA5 ground truth comparison from inference_quality.
@author AF
@date 2026
"""

import os
import sys
import sqlite3
import pandas as pd
from pathlib import Path
from loguru import logger

# Inject configuration path
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import (
    WaidBoot,
    WError,
    WaidExit,
)

def fetch_latest_forecasts(env: WaidBoot, hours: int = 12) -> pd.DataFrame:
    """Retrieves the latest forecast records joined with inference_quality ERA5 metrics."""
    query = f"""
        SELECT 
            t.timestamp,
            t.model_version,
            t.pred_temp, t.pred_rh, t.pred_pres, t.pred_wind, t.pred_rain, t.pred_solar,
            t.diff_temp, t.diff_rh, t.diff_pres, t.diff_wind, t.diff_rain, t.diff_solar,
            t.historical_bias_temp, t.historical_bias_rh, t.historical_bias_pres, 
            t.historical_bias_wind, t.historical_bias_rain, t.historical_bias_solar,
            t.drift_vs_bias_temp, t.drift_vs_bias_rh, t.drift_vs_bias_pres, 
            t.drift_vs_bias_wind, t.drift_vs_bias_rain, t.drift_vs_bias_solar,
            t.created_at,
            q.temp_era5, q.pres_era5, q.rh_era5, q.wind_era5, q.solar_era5, q.rain_era5,
            q.abs_error_temp, q.abs_error_pres, q.abs_error_rh, q.abs_error_wind, q.abs_error_solar, q.abs_error_rain
        FROM inference_forecast t
        LEFT JOIN inference_quality q ON t.timestamp = q.timestamp
        JOIN (
            SELECT timestamp, MAX(created_at) as max_created
            FROM inference_forecast
            WHERE created_at >= datetime('now', '-{hours} hours')
            GROUP BY timestamp
        ) latest ON t.timestamp = latest.timestamp AND t.created_at = latest.max_created
        ORDER BY t.timestamp ASC
    """
    try:
        with sqlite3.connect(env.waid_db) as conn:
            df = pd.read_sql_query(query, conn)
        return df
    except sqlite3.Error as e:
        raise WError(f"Database error while reading forecasts: {e}", code=WaidExit.DATA_FAIL)

def main() -> int:
    try:
        env = WaidBoot()
        df = fetch_latest_forecasts(env, hours=12)

        if df.empty:
            print("\n[WAID] No operational forecasts found. Run pipeline 07_1 first.\n")
            return WaidExit.SUCCESS

        # Timezone conversion
        local_tz = env.tz_timezone
        df['timestamp_local'] = pd.to_datetime(df['timestamp']).dt.tz_localize('UTC').dt.tz_convert(local_tz)
        df['created_at_local'] = pd.to_datetime(df['created_at']).dt.tz_localize('UTC').dt.tz_convert(local_tz)

        # Current local time for validation of past vs future records
        now_local = pd.Timestamp.now(local_tz)

        # Ensure numeric types for predictions, era5 ground truth, errors, and drifts
        feature_keys = ['temp', 'rh', 'pres', 'wind', 'rain', 'solar']
        numeric_cols = []
        for k in feature_keys:
            numeric_cols.extend([f'pred_{k}', f'{k}_era5', f'abs_error_{k}', f'historical_bias_{k}', f'drift_vs_bias_{k}'])
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Header
        print("\n" + "=" * 115)
        print(" WAID OPERATIONAL FORECAST MONITOR (ERA5 Quality Schema View - Last 12h)")
        print("=" * 115)
        print(f" Latest Run (Local)  : {df['created_at_local'].max().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f" Active Model         : {df['model_version'].iloc[0]}")
        print(f" Total Records        : {len(df)}")
        print("=" * 115)

        # Detailed View per record
        for _, row in df.iterrows():
            target_ts = row['timestamp_local']
            ts_str = target_ts.strftime('%Y-%m-%d %H:%M:%S')

            print(f"\n Target Time: {ts_str}")
            print("-" * 115)
            # Layout denso ma completo
            print(f" {'Feature':<14} | {'Pred':<7} | {'Act':<7} | {'Diff':<6} | {'ERA5':<7} | {'Err(E)':<7} | {'Bias':<6} | {'Drift Status'}")
            print("-" * 115)

            def fmt(val): return f"{val:+.2f}" if pd.notnull(val) else "-"
            def fmt_val(val): return f"{val:.2f}" if pd.notnull(val) else "-"

            features_meta = [
                ('Temperature', 'temp'), ('Humidity', 'rh'), ('Pressure', 'pres'),
                ('Wind Speed', 'wind'), ('Rainfall', 'rain'), ('Solar Rad.', 'solar')
            ]

            for label, key in features_meta:
                pred = row.get(f'pred_{key}')
                diff = row.get(f'diff_{key}')
                bias = row.get(f'historical_bias_{key}')
                drift = row.get(f'drift_vs_bias_{key}')
                era5 = row.get(f'{key}_era5')
                
                # Calcoli derivati
                actual = (pred - diff) if pd.notnull(pred) and pd.notnull(diff) else None
                err_era5 = (pred - era5) if pd.notnull(pred) and pd.notnull(era5) else None

                # Logica Drift
                drift_txt = f"DRIFT({fmt(drift)})" if pd.notnull(drift) and abs(drift) > 1.5 else (f"OK({fmt(drift)})" if pd.notnull(drift) else "-")

                print(f" {label:<14} | {fmt_val(pred):<7} | {fmt_val(actual):<7} | {fmt(diff):<6} | {fmt_val(era5):<7} | {fmt(err_era5):<7} | {fmt(bias):<6} | {drift_txt}")

        print("=" * 115 + "\n")
        return WaidExit.SUCCESS

    except WError as e:
        logger.warning(f"[WAID CLI WARNING] {e.message}")
        return WaidExit.SUCCESS
    except Exception:
        logger.exception("Unexpected error")
        return WaidExit.INTERNAL_ERROR

if __name__ == "__main__":
    sys.exit(main())