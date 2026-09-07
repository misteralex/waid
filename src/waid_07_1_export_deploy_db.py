#!/usr/bin/env python3

"""
@file waid_07_1_export_deploy_db.py
@brief ETL script to extract, transform, and export public weather data from the lab database to local deployment DB (SQLite) and optionally sync to Supabase (Cloud mode).
@author AF
@date 2026
"""

import os
import sys
import sqlite3
import pandas as pd
from pathlib import Path
from loguru import logger
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

# Inject configuration path safely
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import (
    WaidBoot,
    WError,
    WaidExit,
    validate_mock_timestamp,
)


def export_to_supabase(env: WaidBoot, df: pd.DataFrame) -> None:
    """
    @brief Exports the prepared DataFrame directly to Supabase PostgreSQL database.
           Ensures the target schema exists before loading data.
    
    @param env WaidBoot configuration object.
    @param df Pandas DataFrame containing the public forecasts dataset.
    """
    logger.info("Starting sync to Supabase (Cloud Mode active)...")
    
    # 1. Dynamically retrieve configuration from the registry
    db_config = env.active_db_config
    
    if not all([db_config.user, db_config.password, db_config.host]):
        raise WError("Missing Supabase database credentials in environment.", code=WaidExit.CONFIG_FAIL)

    # Determine target schema (fallback to WAID_DB_SCHEMA_TARGET or 'draft')
    schema_name = env.db_schema_target.lower()
    
    supabase_url = (
        f"postgresql+psycopg2://{db_config.user}:{db_config.password}"
        f"@{db_config.host}:{db_config.port}/{db_config.dbname}?sslmode=require"
    )
    logger.info(f"Current Supabase target schema name: {schema_name}")
    safe_url = supabase_url.replace(db_config.password, "********")
    logger.debug(f"Connecting to Supabase with URL: {safe_url}")
    
    try:
        engine = create_engine(supabase_url, poolclass=NullPool)
        
        # 2. Automatically create target schema if it does not exist
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name};"))
            conn.commit()
            logger.info(f"Target schema '{schema_name}' verified/created on Supabase.")
        
        # 3. Upload DataFrame into the target schema
        df.to_sql(
            "public_forecasts", 
            engine, 
            schema=schema_name, 
            if_exists="replace", 
            index=False
        )
        
        # 4. Create performance index in the target schema
        with engine.connect() as conn:
            conn.execute(
                text(f"CREATE INDEX IF NOT EXISTS idx_public_forecasts_ts_model ON {schema_name}.public_forecasts (timestamp, model_version)")
            )
            conn.commit()
            
        logger.success(f"Supabase database ({schema_name}.public_forecasts) successfully updated and indexed.")
    except Exception as e:
        logger.error(f"Failed to write to Supabase database: {e}")
        raise WError(f"Supabase synchronization failed: {e}", code=WaidExit.DATA_FAIL)


def main() -> int:
    """
    @brief Extracts operational forecast and quality metrics from lab DB and populates WAID_DB_DEPLOY_FILE.
           Optionally synchronizes data with Supabase if WAID_DEPLOY_MODE is set to 'cloud'.
    
    @return int Process exit status code.
    """
    try:
        parser = argparse.ArgumentParser(description="WAID Inference Engine & DB Exporter")
        parser.add_argument("--mock-now", type=str, default=None, help="Simulated current timestamp")
        args, _ = parser.parse_known_args()
        
        env = WaidBoot()
        
        if args.mock_now:
            env.mock_now = validate_mock_timestamp(args.mock_now)
            logger.info(f"Overriding mock_now with CLI argument: {env.mock_now}")
        
        logger.info(f"🔶 Deploy Mode : {env.deploy_mode}")
        logger.info(f"🔶 DB Target   : {env.db_schema_target}")
            
        waid_db_dir = Path(env.waid_db)
         
        # Resolve public db path with strict check
        if hasattr(env, 'deploy_db_file') and env.waid_data_dir:
            waid_db_deploy_path = Path(env.waid_data_dir / env.deploy_db_file)
        else:
            raise WError("Required configuration is missing or does not match the expected contents.", code=WaidExit.CONFIG_FAIL)
        
    except Exception as e:
        logger.error(f"Failed to initialize WaidBoot configuration: {e}")
        return WaidExit.CONFIG_FAIL

    if not waid_db_dir.exists():
        logger.error(f"Lab database not found at: {waid_db_dir}")
        return WaidExit.DATA_FAIL

    logger.info(f"Connecting to lab database: {waid_db_dir}")
    
    # Updated the query to correctly handle the composite key (timestamp, model_version)
    query = """
        SELECT
            t.timestamp,
            t.created_at,
            t.model_version,

            t.pred_temp,
            t.pred_rh,
            t.pred_pres,
            t.pred_wind,
            t.pred_rain,
            t.pred_solar,

            t.diff_temp,
            t.diff_rh,
            t.diff_pres,
            t.diff_wind,
            t.diff_rain,
            t.diff_solar,

            t.historical_bias_temp,
            t.historical_bias_rh,
            t.historical_bias_pres,
            t.historical_bias_wind,
            t.historical_bias_rain,
            t.historical_bias_solar,

            t.drift_vs_bias_temp,
            t.drift_vs_bias_rh,
            t.drift_vs_bias_pres,
            t.drift_vs_bias_wind,
            t.drift_vs_bias_rain,
            t.drift_vs_bias_solar,

            q.temp_era5,
            q.rh_era5,
            q.pres_era5,
            q.wind_era5,
            q.rain_era5,
            q.solar_era5,

            q.abs_error_temp,
            q.abs_error_rh,
            q.abs_error_pres,
            q.abs_error_wind,
            q.abs_error_rain,
            q.abs_error_solar

        FROM inference_forecast AS t
        LEFT JOIN inference_quality AS q
            ON t.timestamp = q.timestamp
        AND t.model_version = q.model_version

        ORDER BY
            t.timestamp ASC,
            t.model_version ASC
    """

    try:
        with sqlite3.connect(waid_db_dir) as src_conn:
            df = pd.read_sql_query(query, src_conn)
    except Exception as e:
        logger.error(f"Failed to read from lab database: {e}")
        return WaidExit.DATA_FAIL

    if df.empty:
        logger.warning("No records found in the lab database to export.")
        return WaidExit.DATA_FAILED if 'DATA_FAILED' in dir(WaidExit) else WaidExit.DATA_FAIL

    logger.info(f"Extracted {len(df)} records. Preparing public database export...")

    # Step 1: Always update local deployment SQLite database
    waid_db_deploy_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sqlite3.connect(waid_db_deploy_path) as dest_conn:
            df.to_sql("public_forecasts", dest_conn, if_exists="replace", index=False)
        
            # Create an index on the exported table to reflect the composite key and optimize public queries
            cursor = dest_conn.cursor()
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_public_forecasts_ts_model ON public_forecasts (timestamp, model_version)")
            dest_conn.commit()

        logger.success(f"Local public database successfully updated at: {waid_db_deploy_path}")
    except Exception as e:
        logger.error(f"Failed to write to local public database: {e}")
        return WaidExit.DATA_FAIL

    # Step 2: If WAID_DEPLOY_MODE is 'cloud', also sync to Supabase 
    if env.deploy_mode == "cloud":
        try:
            export_to_supabase(env, df)
        except WError as e:
            return e.code
        except Exception as e:
            logger.error(f"Unexpected error during Supabase export: {e}")
            return WaidExit.DATA_FAIL

    return WaidExit.SUCCESS

if __name__ == "__main__":
    sys.exit(main())