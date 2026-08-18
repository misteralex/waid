#!/usr/bin/env python3

"""
@file refresh_mock_shifted.py
@brief WAID Mock Database Refresh and Shifting Simulation Pipeline.
@details Refreshes the local mock database by copying production data, shifting historical 
         telemetry records forward to match current timestamps, and rebuilding staging tables.
@author AF
@date 2026
"""

import sqlite3
import pandas as pd
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger

# Inject configuration path safely if boot is available, otherwise fallback cleanly
sys_path_added = False
config_path = Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])) / "config"
if config_path.exists():
    sys.path.append(str(config_path.resolve()))
    from boot import WaidBoot, WError, WaidExit
    sys_path_added = True


def refresh_mock_shifted() -> int:
    """Refreshes the mock database, shifts telemetry records to current time, and updates staging tables.

    @return: Status code indicating success or failure.
    """
    try:
        waid_source = os.environ.get("WAID_SOURCE")
        if not waid_source:
            logger.error("Environment variable WAID_SOURCE is not defined.")
            return 1

        source_db = Path(waid_source) / "data/waid.db"
        mock_db = Path(waid_source) / "data/waid_mock.db"
        
        if not source_db.exists():
            logger.error(f"Source database not found at: {source_db}")
            return 1

        now = datetime.now()
        logger.info("Starting mock database refresh process...")
        
        saved_forecasts_df = None
        if mock_db.exists():
            try:
                with sqlite3.connect(mock_db) as conn_old:
                    saved_forecasts_df = pd.read_sql("SELECT * FROM inference_forecast", conn_old)
                logger.info("Preserved existing 'inference_forecast' history from old mock DB.")
            except Exception:
                pass
            
            logger.info(f"Removing old mock database: {mock_db}")
            mock_db.unlink()
            
        logger.info("Copying source database to mock database...")
        shutil.copy2(source_db, mock_db)
        
        with sqlite3.connect(mock_db) as conn_mock:
            if saved_forecasts_df is not None and not saved_forecasts_df.empty:
                saved_forecasts_df.to_sql('inference_forecast', conn_mock, if_exists='replace', index=False)
                logger.info("Restored 'inference_forecast' into new mock DB.")

            query_max_ts = "SELECT MAX(timestamp) as last_ts FROM ecowitt_records"
            last_ts_df = pd.read_sql(query_max_ts, conn_mock)
            
            if pd.isna(last_ts_df['last_ts'].iloc[0]):
                logger.error("CRITICAL: The source database is completely empty. No data to replicate.")
                return 1

            last_ts = pd.to_datetime(last_ts_df['last_ts'].iloc[0])
            logger.info(f"Last recorded timestamp in raw DB: {last_ts}")
            logger.info(f"Target timestamp (Now): {now}")

            total_records_added = 0

            while last_ts < now:
                gap = now - last_ts
                lookback = min(timedelta(days=7), gap)
                start_lookback = last_ts - lookback
                
                query = """
                    SELECT * FROM ecowitt_records 
                    WHERE timestamp > ? AND timestamp <= ?
                    ORDER BY timestamp ASC
                """
                df_chunk = pd.read_sql(query, conn_mock, params=(str(start_lookback), str(last_ts)))
                
                if df_chunk.empty:
                    fallback_start = last_ts - timedelta(hours=24)
                    df_chunk = pd.read_sql(query, conn_mock, params=(str(fallback_start), str(last_ts)))
                    if df_chunk.empty:
                        logger.warning("CRITICAL: Not enough continuous historical data. Aborting loop.")
                        break
                    lookback = timedelta(hours=24)
                    
                df_chunk['timestamp'] = pd.to_datetime(df_chunk['timestamp']) + lookback
                
                # 1. Filter out records beyond the current time
                df_chunk = df_chunk[df_chunk['timestamp'] <= now]
                
                # 2. Convert to string and remove overlaps based on unique constraints
                df_chunk['timestamp'] = df_chunk['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # Read already inserted timestamps and exclude exact duplicates
                existing_ts = pd.read_sql(
                    "SELECT timestamp FROM ecowitt_records WHERE timestamp >= ?",
                    conn_mock, params=(df_chunk['timestamp'].min(),)
                )['timestamp'].tolist()
                
                df_chunk = df_chunk[~df_chunk['timestamp'].isin(existing_ts)].drop_duplicates(subset=['timestamp'])
                
                if df_chunk.empty:
                    break
                    
                df_chunk.to_sql('ecowitt_records', conn_mock, if_exists='append', index=False)
                
                records_added = len(df_chunk)
                total_records_added += records_added
                last_ts = pd.to_datetime(df_chunk['timestamp'].max())
                logger.info(f"  -> Appended {records_added} raw records. New latest timestamp: {last_ts}")

            # Build/Update staging table stg_ecowitt
            logger.info("Building/updating 'stg_ecowitt' staging table...")
            df_raw_all = pd.read_sql("SELECT * FROM ecowitt_records ORDER BY timestamp ASC", conn_mock)
            if not df_raw_all.empty:
                df_raw_all['timestamp'] = pd.to_datetime(df_raw_all['timestamp'])
                
                df_stg = df_raw_all.resample('60min', on='timestamp').agg({
                    'outdoor_temperature_c': 'mean',
                    'abs_pressure_hpa': 'mean',
                    'outdoor_humidity': 'mean',
                    'wind_m_s': 'mean',
                    'solar_rad_w_m2': 'mean',
                    'hourly_rain_mm': 'max'
                }).reset_index()

                df_stg.rename(columns={
                    'outdoor_temperature_c': 'temperature',
                    'abs_pressure_hpa': 'pressure_hpa',
                    'outdoor_humidity': 'humidity',
                    'wind_m_s': 'wind_speed',
                    'solar_rad_w_m2': 'solar_radiation',
                    'hourly_rain_mm': 'hourly_rain'
                }, inplace=True)

                df_stg.dropna(subset=['temperature'], inplace=True)
                df_stg['timestamp'] = df_stg['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                df_stg.to_sql('stg_ecowitt', conn_mock, if_exists='replace', index=False)
                logger.success(f"'stg_ecowitt' updated successfully with {len(df_stg)} hourly records up to {df_stg['timestamp'].max()}.")

        logger.success("Success: Mock refresh complete!")
        return 0

    except Exception as e:
        logger.exception(f"Unexpected failure during mock database refresh: {e}")
        return 1


if __name__ == "__main__":
    
    sys.exit(refresh_mock_shifted())