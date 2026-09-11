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

if not os.environ.get("WAID_SOURCE"):
    sys.exit("[CRITICAL] WAID_SOURCE environment variable is missing. Export it first.")

sys.path.append(str(Path(os.environ.get("WAID_SOURCE")) / "config"))
from boot import (
    WaidBoot,
    WError,
    WaidExit,
    validate_mock_timestamp,
)

def export_to_supabase(env: WaidBoot, df: pd.DataFrame) -> None:
    """
    @brief Exports the prepared DataFrame directly to Supabase PostgreSQL database using UPSERT.
    @param env WaidBoot configuration object.
    @param df Pandas DataFrame containing the public forecasts dataset.
    @return None
    """
    logger.info("Starting sync to Supabase (Cloud Mode active)...")
    
    db_config = env.active_db_config
    if not all([db_config.user, db_config.password, db_config.host]):
        raise WError("Missing Supabase database credentials in environment.", code=WaidExit.CONFIG_FAIL)

    schema_name = env.db_schema_target.lower()
    
    supabase_url = (
        f"postgresql+psycopg2://{db_config.user}:{db_config.password}"
        f"@{db_config.host}:{db_config.port}/{db_config.dbname}?sslmode=require"
    )
    
    try:
        engine = create_engine(supabase_url, poolclass=NullPool)
        
        # Format datetimes & replace NaN/NaT with None for SQL NULL compatibility
        df_supabase = df.copy()
        for col in df_supabase.select_dtypes(include=['datetime', 'datetime64']).columns:
            df_supabase[col] = df_supabase[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        records = df_supabase.where(pd.notnull(df_supabase), None).to_dict(orient="records")
        
        with engine.connect() as conn:
            # 1. Ensure target schema and table with composite primary key exist
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name};"))
            
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.public_forecasts (
                    timestamp TEXT,
                    created_at TEXT,
                    model_version TEXT,
                    pred_temp DOUBLE PRECISION,
                    pred_rh DOUBLE PRECISION,
                    pred_pres DOUBLE PRECISION,
                    pred_wind DOUBLE PRECISION,
                    pred_rain DOUBLE PRECISION,
                    pred_solar DOUBLE PRECISION,
                    diff_temp DOUBLE PRECISION,
                    diff_rh DOUBLE PRECISION,
                    diff_pres DOUBLE PRECISION,
                    diff_wind DOUBLE PRECISION,
                    diff_rain DOUBLE PRECISION,
                    diff_solar DOUBLE PRECISION,
                    historical_bias_temp DOUBLE PRECISION,
                    historical_bias_rh DOUBLE PRECISION,
                    historical_bias_pres DOUBLE PRECISION,
                    historical_bias_wind DOUBLE PRECISION,
                    historical_bias_rain DOUBLE PRECISION,
                    historical_bias_solar DOUBLE PRECISION,
                    drift_vs_bias_temp DOUBLE PRECISION,
                    drift_vs_bias_rh DOUBLE PRECISION,
                    drift_vs_bias_pres DOUBLE PRECISION,
                    drift_vs_bias_wind DOUBLE PRECISION,
                    drift_vs_bias_rain DOUBLE PRECISION,
                    drift_vs_bias_solar DOUBLE PRECISION,
                    temp_era5 DOUBLE PRECISION,
                    rh_era5 DOUBLE PRECISION,
                    pres_era5 DOUBLE PRECISION,
                    wind_era5 DOUBLE PRECISION,
                    rain_era5 DOUBLE PRECISION,
                    solar_era5 DOUBLE PRECISION,
                    abs_error_temp DOUBLE PRECISION,
                    abs_error_rh DOUBLE PRECISION,
                    abs_error_pres DOUBLE PRECISION,
                    abs_error_wind DOUBLE PRECISION,
                    abs_error_rain DOUBLE PRECISION,
                    abs_error_solar DOUBLE PRECISION,
                    PRIMARY KEY (timestamp, model_version)
                );
            """))
            conn.commit()

            # 2. Execute UPSERT via ON CONFLICT DO UPDATE
            cols = list(df.columns)
            update_cols = [c for c in cols if c not in ("timestamp", "model_version")]
            
            set_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in update_cols])
            col_names = ", ".join(cols)
            val_placeholders = ", ".join([f":{c}" for c in cols])

            upsert_query = text(f"""
                INSERT INTO {schema_name}.public_forecasts ({col_names})
                VALUES ({val_placeholders})
                ON CONFLICT (timestamp, model_version) 
                DO UPDATE SET {set_clause};
            """)

            conn.execute(upsert_query, records)
            
            # 3. Create composite index for query performance
            conn.execute(
                text(f"CREATE INDEX IF NOT EXISTS idx_public_forecasts_ts_model ON {schema_name}.public_forecasts (timestamp, model_version)")
            )
            conn.commit()
            
        logger.success(f"Supabase database ({schema_name}.public_forecasts) successfully updated via UPSERT.")
    except Exception as e:
        logger.error(f"Failed to write to Supabase database: {e}")
        raise WError(f"Supabase synchronization failed: {e}", code=WaidExit.DATA_FAIL)


def main() -> int:
    """
    @brief Extracts operational forecast and quality metrics from lab DB and populates WAID_DB_DEPLOY_FILE.
           Optionally synchronizes data with Supabase if WAID_DEPLOY_MODE is set to 'cloud'.
    @return int Exit code representing success or failure status.
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

    # Step 1: Update local deployment SQLite database
    waid_db_deploy_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sqlite3.connect(waid_db_deploy_path) as dest_conn:
            cursor = dest_conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS public_forecasts (
                    timestamp TEXT,
                    created_at TEXT,
                    model_version TEXT,
                    pred_temp REAL, pred_rh REAL, pred_pres REAL, pred_wind REAL, pred_rain REAL, pred_solar REAL,
                    diff_temp REAL, diff_rh REAL, diff_pres REAL, diff_wind REAL, diff_rain REAL, diff_solar REAL,
                    historical_bias_temp REAL, historical_bias_rh REAL, historical_bias_pres REAL, historical_bias_wind REAL, historical_bias_rain REAL, historical_bias_solar REAL,
                    drift_vs_bias_temp REAL, drift_vs_bias_rh REAL, drift_vs_bias_pres REAL, drift_vs_bias_wind REAL, drift_vs_bias_rain REAL, drift_vs_bias_solar REAL,
                    temp_era5 REAL, rh_era5 REAL, pres_era5 REAL, wind_era5 REAL, rain_era5 REAL, solar_era5 REAL,
                    abs_error_temp REAL, abs_error_rh REAL, abs_error_pres REAL, abs_error_wind REAL, abs_error_rain REAL, abs_error_solar REAL,
                    PRIMARY KEY (timestamp, model_version)
                );
            """)
            
            # Sanitize NaNs to None for SQLite NULL handling
            cols = list(df.columns)
            placeholders = ", ".join(["?"] * len(cols))
            col_names = ", ".join(cols)
            
            records = df.where(pd.notnull(df), None).values.tolist()
            sql = f"INSERT OR REPLACE INTO public_forecasts ({col_names}) VALUES ({placeholders})"
            cursor.executemany(sql, records)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_public_forecasts_ts_model ON public_forecasts (timestamp, model_version)")
            dest_conn.commit()

        logger.success(f"Local public database successfully updated (UPSERT) at: {waid_db_deploy_path}")
        
    except Exception as e:
        logger.error(f"Failed to write to local public database: {e}")
        return WaidExit.DATA_FAIL

    # Step 2: Optionally sync to Supabase
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