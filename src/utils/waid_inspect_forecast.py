#!/usr/bin/env python3
"""
@file utils/waid_inspect_forecast.py
@brief CLI Inspector for WAID operational forecasts & retroactive experiments.
@author AF
@date 2026
"""

import os
import sys
import argparse
import sqlite3
import pandas as pd
from pathlib import Path
from loguru import logger

# Inject configuration path
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import WaidBoot, WError, WaidExit


def fetch_forecasts(env: WaidBoot, limit: int = 10, exp_id: str | None = None) -> pd.DataFrame:
    """Retrieves forecast records optionally filtered by experiment_id or limited by count."""
    
    # Switch target database if exp_id is requested or fallback to waid_db
    db_path = env.waid_deploy_db if exp_id else env.waid_db

    where_clause = f"WHERE t.experiment_id = '{exp_id}'" if exp_id else ""

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
            q.temp_era5, q.pres_era5, q.rh_era5, q.wind_era5, q.solar_era5, q.rain_era5
        FROM inference_forecast t
        LEFT JOIN inference_quality q ON t.timestamp = q.timestamp
        {where_clause}
        ORDER BY t.timestamp DESC
        LIMIT {limit}
    """
    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
        return df.iloc[::-1].reset_index(drop=True)  # Reverse to show chronological order
    except sqlite3.Error as e:
        raise WError(f"Database error while reading forecasts: {e}", code=WaidExit.DATA_FAIL)


def print_summary_view(df: pd.DataFrame) -> None:
    """Prints a quick aggregated summary table instead of line-by-line breakdown."""
    features = ['temp', 'rh', 'pres', 'wind', 'rain', 'solar']
    print("\n" + "=" * 80)
    print(" 📊 EXECUTIVE DRIFT & ERROR SUMMARY")
    print("=" * 80)
    print(f" {'Feature':<15} | {'Avg Pred':<10} | {'Avg Diff':<10} | {'Drift Count (>1.5)':<20}")
    print("-" * 80)

    for key in features:
        pred_col = f'pred_{key}'
        diff_col = f'diff_{key}'
        drift_col = f'drift_vs_bias_{key}'

        avg_pred = df[pred_col].mean() if pred_col in df else float('nan')
        avg_diff = df[diff_col].mean() if diff_col in df else float('nan')
        
        drift_cnt = 0
        if drift_col in df:
            drift_cnt = (df[drift_col].abs() > 1.5).sum()

        print(f" {key.upper():<15} | {avg_pred:<10.2f} | {avg_diff:<+10.2f} | {drift_cnt}/{len(df)}")
    print("=" * 80 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="WAID Operational Forecast CLI Inspector")
    parser.add_argument("-n", "--limit", type=int, default=5, help="Number of latest target periods to display (default: 5)")
    parser.add_argument("--exp", type=str, default=None, help="Experiment ID to query from deploy DB")
    parser.add_argument("--summary", action="store_true", help="Display only an aggregated summary")
    args = parser.parse_args()

    try:
        env = WaidBoot()
        df = fetch_forecasts(env, limit=args.limit, exp_id=args.exp)

        if df.empty:
            print("\n[WAID] No forecast records found matching query criteria.\n")
            return WaidExit.SUCCESS

        # Timezone conversion
        local_tz = env.tz_timezone
        df['timestamp_local'] = pd.to_datetime(df['timestamp']).dt.tz_localize('UTC').dt.tz_convert(local_tz)
        df['created_at_local'] = pd.to_datetime(df['created_at']).dt.tz_localize('UTC').dt.tz_convert(local_tz)

        # Header
        print("\n" + "=" * 115)
        print(f" WAID OPERATIONAL FORECAST INSPECTOR {'(EXP: ' + args.exp + ')' if args.exp else ''}")
        print("=" * 115)
        print(f" Latest Run (Local)  : {df['created_at_local'].max().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f" Active Model         : {df['model_version'].iloc[0]}")
        print(f" Displaying Records   : {len(df)} (Limit: {args.limit})")
        print("=" * 115)

        if args.summary:
            print_summary_view(df)
            return WaidExit.SUCCESS

        # Detailed View per record
        features_meta = [
            ('Temperature', 'temp'), ('Humidity', 'rh'), ('Pressure', 'pres'),
            ('Wind Speed', 'wind'), ('Rainfall', 'rain'), ('Solar Rad.', 'solar')
        ]

        for _, row in df.iterrows():
            target_ts = row['timestamp_local']
            print(f"\n Target Time: {target_ts.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 115)
            print(f" {'Feature':<14} | {'Pred':<7} | {'Act':<7} | {'Diff':<6} | {'ERA5':<7} | {'Err(E)':<7} | {'Bias':<6} | {'Drift Status'}")
            print("-" * 115)

            def fmt(val): return f"{val:+.2f}" if pd.notnull(val) else "-"
            def fmt_val(val): return f"{val:.2f}" if pd.notnull(val) else "-"

            for label, key in features_meta:
                pred = row.get(f'pred_{key}')
                diff = row.get(f'diff_{key}')
                bias = row.get(f'historical_bias_{key}')
                drift = row.get(f'drift_vs_bias_{key}')
                era5 = row.get(f'{key}_era5')
                
                actual = (pred - diff) if pd.notnull(pred) and pd.notnull(diff) else None
                err_era5 = (pred - era5) if pd.notnull(pred) and pd.notnull(era5) else None

                drift_txt = f"DRIFT({fmt(drift)})" if pd.notnull(drift) and abs(drift) > 1.5 else (f"OK({fmt(drift)})" if pd.notnull(drift) else "-")

                print(f" {label:<14} | {fmt_val(pred):<7} | {fmt_val(actual):<7} | {fmt(diff):<6} | {fmt_val(era5):<7} | {fmt(err_era5):<7} | {fmt(bias):<6} | {drift_txt}")

        print("=" * 115 + "\n")
        return WaidExit.SUCCESS

    except WError as e:
        logger.warning(f"[WAID CLI WARNING] {e.message}")
        return WaidExit.SUCCESS
    except Exception:
        logger.exception("Unexpected error during CLI inspection")
        return WaidExit.INTERNAL_ERROR


if __name__ == "__main__":
    sys.exit(main())