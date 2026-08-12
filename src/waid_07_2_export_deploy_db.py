#!/usr/bin/env python3

"""
@file waid_07_2_export_deploy_db.py
@brief ETL script to extract, transform, and export public weather data from the lab database to WAID_DB_DEPLOY_FILE using WaidBoot exit codes.
@author AF
@date 2026
"""

import os
import sys
import sqlite3
import pandas as pd
from pathlib import Path
from loguru import logger

# Inject configuration path safely
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import WaidBoot, WaidExit

def main() -> int:
    """Extracts operational forecast and quality metrics from lab DB and populates WAID_DB_DEPLOY_FILE."""
    try:
        env = WaidBoot()
        waid_db_dir = Path(env.waid_db)
        
        # Resolve public db path with strict check
        if hasattr(env, 'waid_db_deploy_file') and env.waid_data_dir:
            public_db_path = Path(env.waid_data_dir) / env.waid_db_deploy_file
        else:
            raise WError("Missing required configuration: WAID_DB_DEPLOY_FILE or WAID_DATA_DIR is not defined.", code=WaidExit.CONFIG_FAIL)
    except Exception as e:
        logger.error(f"Failed to initialize WaidBoot configuration: {e}")
        return WaidExit.CONFIG_FAIL

    if not waid_db_dir.exists():
        logger.error(f"Lab database not found at: {waid_db_dir}")
        return WaidExit.DATA_FAIL

    logger.info(f"Connecting to lab database: {waid_db_dir}")
    
    query = """
        SELECT 
            t.timestamp, 
            t.created_at, 
            t.model_version,
            t.pred_temp, t.pred_rh, t.pred_pres, t.pred_wind, t.pred_rain, t.pred_solar,
            t.diff_temp, t.diff_rh, t.diff_pres, t.diff_wind, t.diff_rain, t.diff_solar,
            t.historical_bias_temp, t.historical_bias_rh, t.historical_bias_pres, 
            t.historical_bias_wind, t.historical_bias_rain, t.historical_bias_solar,
            t.drift_vs_bias_temp, t.drift_vs_bias_rh, t.drift_vs_bias_pres, 
            t.drift_vs_bias_wind, t.drift_vs_bias_rain, t.drift_vs_bias_solar,
            q.temp_era5, q.rh_era5, q.pres_era5, q.wind_era5, q.rain_era5, q.solar_era5,
            q.abs_error_temp, q.abs_error_rh, q.abs_error_pres, q.abs_error_wind, q.abs_error_rain, q.abs_error_solar
        FROM inference_forecast t
        LEFT JOIN inference_quality q ON t.timestamp = q.timestamp
        ORDER BY t.timestamp ASC
    """

    try:
        with sqlite3.connect(waid_db_dir) as src_conn:
            df = pd.read_sql_query(query, src_conn)
    except Exception as e:
        logger.error(f"Failed to read from lab database: {e}")
        return WaidExit.DATA_FAIL

    if df.empty:
        logger.warning("No records found in the lab database to export.")
        return WaidExit.DATA_FAIL

    logger.info(f"Extracted {len(df)} records. Preparing public database export...")

    public_db_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sqlite3.connect(public_db_path) as dest_conn:
            df.to_sql("public_forecasts", dest_conn, if_exists="replace", index=False)
        logger.success(f"Public database successfully updated at: {public_db_path}")
    except Exception as e:
        logger.error(f"Failed to write to public database: {e}")
        return WaidExit.DATA_FAIL

    return 0

if __name__ == "__main__":
    sys.exit(main())