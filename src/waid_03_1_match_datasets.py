#!/usr/bin/env python3

"""
@file waid_03_1_match_datasets.py
@brief WAID Data Synchronization and Feature Store Alignment.
@details Performs Phase 3 (Transform/Alignment) of the data pipeline. Queries
         consolidated station data directly from SQLite, resamples telemetry to hourly intervals,
         handles ERA5 global reanalysis data integration via left-join (decoupling Ecowitt freshness
         from ERA5 multi-day latency), and populates the centralized Feature Store match table.
@author AF
@date 2026
"""

import os
import sys
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import xarray as xr
from loguru import logger

# Inject configuration path into python execution environment
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import (
    WaidBoot,
    WaidExit,
    WError,
    validate_period,
)

from waid_utils import fetch_and_resample_ecowitt


def ensure_table_exists(env: WaidBoot) -> bool:
    """
    @brief Ensures the target match table exists in the SQLite Feature Store.
    @param env WaidBoot configuration context.
    @return True if table exists and is verified, False otherwise.
    """
    create_stmt = f"""
    CREATE TABLE IF NOT EXISTS {env.ml_matches_table} (
        timestamp TEXT PRIMARY KEY,
        
        temp_era5 REAL, 
        pres_era5 REAL, 
        rh_era5 REAL, 
        wind_era5 REAL, 
        solar_era5 REAL, 
        rain_era5 REAL,
        
        temp_eco REAL, 
        pres_eco REAL, 
        rh_eco REAL, 
        wind_eco REAL, 
        solar_eco REAL, 
        rain_eco REAL    
    );
    """

    try:
        with sqlite3.connect(env.waid_db) as conn:
            conn.execute(create_stmt)
            conn.commit()
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{env.ml_matches_table}'"
            )
            return cursor.fetchone()[0] == 1
    except sqlite3.Error as e:
        logger.error(f"Failed to verify Feature Store schema: {e}")
        return False


def calculate_rh(temperature, dew_point) -> np.ndarray:
    """
    @brief Calculates Relative Humidity using the Magnus-Tetens approximation.
    @param temperature Temperature array in Celsius.
    @param dew_point Dew point array in Celsius.
    @return Numpy array of relative humidity values clipped between 0 and 100.
    """
    temperature = np.asarray(temperature)
    dew_point = np.asarray(dew_point)

    if np.any(~np.isfinite(temperature)) or np.any(~np.isfinite(dew_point)):
        raise WError(
            "Please provide a valid array of temperature and dew point",
            code=WaidExit.DATA_FAIL,
        )

    if np.any(np.isclose(temperature, -243.04)) or np.any(np.isclose(dew_point, -243.04)):
        raise WError(
            "The temperature or dew point cannot be equal to -243.04°C.",
            code=WaidExit.DATA_FAIL,
        )

    if temperature.shape != dew_point.shape:
        raise WError(
            "Temperature and dew point must have the same shape.",
            code=WaidExit.DATA_FAIL,
        )

    numerator = np.exp((17.625 * dew_point) / (243.04 + dew_point))
    denominator = np.exp((17.625 * temperature) / (243.04 + temperature))

    rh = 100 * (numerator / denominator)
    return np.clip(rh, 0, 100)


def perform_matching_with_ecowitt(
    env: WaidBoot,
    df_era5: pd.DataFrame,
    period: datetime,
) -> pd.DataFrame:
    """
    @brief Extracts Ecowitt hourly data and performs a left-join with ERA5, decoupling Ecowitt from ERA5 latency.
    @param env WaidBoot configuration context.
    @param df_era5 DataFrame containing ERA5 reanalysis data (may be empty if ERA5 is unavailable).
    @param period Target operational month datetime.
    @return Merged DataFrame containing hourly Ecowitt records and available ERA5 benchmark fields.
    """
    start_date = period.strftime("%Y-%m-01 00:00:00")
    
    # Determine upper bound: current time if current month, otherwise end of month
    current_time = datetime.now()
    if period.year == current_time.year and period.month == current_time.month:
        end_date = current_time.strftime("%Y-%m-%d %H:%M:%S")
    else:
        end_date = (period + pd.offsets.MonthEnd(1)).strftime("%Y-%m-%d 23:59:59")

    logger.info(f"Fetching Ecowitt hourly resampled data from {start_date} to {end_date}")
    df_eco_hourly = fetch_and_resample_ecowitt(env, start_date, end_date)

    if df_eco_hourly.empty:
        raise WError(f"No Ecowitt telemetry records found for period {period.strftime('%Y-%m')}.", code=WaidExit.DATA_FAIL)

    df_eco_hourly.rename(
        columns={
            "outdoor_temperature_c": "temp_eco",
            "abs_pressure_hpa": "pres_eco",
            "outdoor_humidity": "rh_eco",
            "wind_m_s": "wind_eco",
            "solar_rad_w_m2": "solar_eco",
            "hourly_rain_mm": "rain_eco",
        },
        inplace=True,
    )

    # Ensure timestamp format alignment
    df_eco_hourly["timestamp"] = pd.to_datetime(df_eco_hourly["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")

    if not df_era5.empty:
        resample_freq = f"{env.resample_interval_min}min"
        df_era5["timestamp"] = (
            pd.to_datetime(df_era5["timestamp"], utc=True)
            .dt.tz_localize(None)
            .dt.floor(resample_freq)
            .dt.strftime("%Y-%m-%d %H:%M:%S")
        )
        logger.info("Merging Ecowitt station measurements with ERA5 model data (Left Join)...")
        df_match = pd.merge(df_eco_hourly, df_era5, on="timestamp", how="left")
    else:
        logger.warning("No ERA5 dataset available for this period. Populating match table with Ecowitt actuals only.")
        df_match = df_eco_hourly.copy()
        for col in ["temp_era5", "pres_era5", "rh_era5", "wind_era5", "solar_era5", "rain_era5"]:
            df_match[col] = np.nan

    logger.success(f"Synchronization complete! Total synchronized records: {len(df_match)} rows.")

    # Calculate biases only for rows where ERA5 data is present
    df_with_era5 = df_match.dropna(subset=["temp_era5"])

    if not df_with_era5.empty and env.debug_mode:
        df_with_era5["bias_temp"] = df_with_era5["temp_eco"] - df_with_era5["temp_era5"]
        df_with_era5["bias_pres"] = df_with_era5["pres_eco"] - df_with_era5["pres_era5"]
        df_with_era5["bias_rh"] = df_with_era5["rh_eco"] - df_with_era5["rh_era5"]
        df_with_era5["bias_wind"] = df_with_era5["wind_eco"] - df_with_era5["wind_era5"]
        df_with_era5["bias_solar"] = df_with_era5["solar_eco"] - df_with_era5["solar_era5"]
        df_with_era5["bias_rain"] = df_with_era5["rain_eco"] - df_with_era5["rain_era5"]

        logger.debug(f"--- BIAS REPORT FOR PERIOD: {period.year}-{period.month:02d} (Matched Subset: {len(df_with_era5)}) ---")
        logger.debug(f"Mean Temp Bias       : {df_with_era5['bias_temp'].mean():+.2f} °C")
        logger.debug(f"Mean Pressure Bias   : {df_with_era5['bias_pres'].mean():+.2f} hPa")
        logger.debug(f"Mean Humidity Bias   : {df_with_era5['bias_rh'].mean():+.2f} %")
        logger.debug(f"Mean Wind Speed Bias : {df_with_era5['bias_wind'].mean():+.2f} m/s")
        logger.debug(f"Mean Solar Rad Bias  : {df_with_era5['bias_solar'].mean():+.2f} W/m2")
        logger.debug(f"Mean Hourly Rain Bias: {df_with_era5['bias_rain'].mean():+.2f} mm")

    # Save CSV Checkpoint
    env.ml_matches_dir.mkdir(parents=True, exist_ok=True)
    output_csv_path = env.ml_matches_dir / f"matched_{period.year}-{period.month:02d}.csv"
    df_match.to_csv(output_csv_path, index=False)
    logger.success(f"Monthly checkpoint saved to CSV: {output_csv_path.name}")

    return df_match


def perform_matching_with_era5(env: WaidBoot, period: datetime) -> int:
    """
    @brief Loads ERA5 NetCDF if available, extracts grid data, and synchronizes with Ecowitt into Feature Store.
    @param env WaidBoot configuration context.
    @param period Target operational month datetime.
    @return Execution status exit code integer.
    """
    filename = env.era5_data_dir / f"era5_{period.year}_{period.month:02d}"
    data_file_era5 = filename.with_suffix(".nc")

    df_era5 = pd.DataFrame()

    if not data_file_era5.exists():
        data_file_era5 = filename.with_suffix(".full")
        
    if data_file_era5.exists():
        logger.info(f"Using ERA5 Dataset: {data_file_era5.name}")
        try:
            ds = xr.open_dataset(data_file_era5)
            logger.info(
                f"Extracting grid variables for Target Location ("
                f"Lat: {env.ecowitt_latitude}, Lon: {env.ecowitt_longitude})"
            )
            df_era5 = (
                ds.sel(
                    latitude=env.ecowitt_latitude,
                    longitude=env.ecowitt_longitude,
                    method="nearest",
                )
                .to_dataframe()
                .reset_index()
            )

            time_col = next((c for c in ["valid_time", "timestamp"] if c in df_era5.columns), None)
            if time_col:
                df_era5["timestamp"] = pd.to_datetime(df_era5[time_col], utc=True).dt.tz_localize(None)

                # ERA5 Conversions
                df_era5["temp_era5"] = df_era5["t2m"] - 273.15
                df_era5["dew_era5"] = df_era5["d2m"] - 273.15
                df_era5["pres_era5"] = df_era5["sp"] / 100.0
                df_era5["rh_era5"] = calculate_rh(df_era5["temp_era5"], df_era5["dew_era5"])

                if "u10" in df_era5.columns and "v10" in df_era5.columns:
                    df_era5["wind_era5"] = np.sqrt(df_era5["u10"] ** 2 + df_era5["v10"] ** 2)
                else:
                    df_era5["wind_era5"] = 0.0

                if "ssrd" in df_era5.columns:
                    df_era5["solar_era5"] = df_era5["ssrd"] / 3600.0
                else:
                    df_era5["solar_era5"] = 0.0

                if "tp" in df_era5.columns:
                    df_era5["rain_era5"] = df_era5["tp"] * 1000.0
                else:
                    df_era5["rain_era5"] = 0.0

                keep_era5 = [
                    "timestamp",
                    "temp_era5",
                    "pres_era5",
                    "rh_era5",
                    "wind_era5",
                    "solar_era5",
                    "rain_era5",
                ]
                df_era5 = df_era5[[c for c in keep_era5 if c in df_era5.columns]]
            ds.close()
            logger.info(f"ERA5 extracted successfully. Records: {len(df_era5)}")
        except Exception as e:
            logger.warning(f"Failed to process ERA5 dataset, proceeding with Ecowitt-only matching: {e}")
            df_era5 = pd.DataFrame()
    else:
        logger.warning(
            f"[WAID INFO] No ERA5 data found for period {period.year}-{period.month:02d}. Proceeding with Ecowitt-only synchronization."
        )

    df_match = perform_matching_with_ecowitt(env, df_era5, period)

    # --- Synchronize into Central Feature Store using Explicit Queries ---
    logger.info(f"Synchronizing aligned dataset into Feature Store: {env.ml_matches_table}")

    try:
        with sqlite3.connect(env.waid_db) as conn:
            cursor = conn.cursor()

            start_date = period.strftime("%Y-%m-01 00:00:00")
            current_time = datetime.now()
            if period.year == current_time.year and period.month == current_time.month:
                end_date = current_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                end_date = (period + pd.offsets.MonthEnd(1)).strftime("%Y-%m-%d 23:59:59")

            # Pulizia preventiva del range temporale
            cursor.execute(
                f"DELETE FROM {env.ml_matches_table} WHERE timestamp >= ? AND timestamp <= ?",
                (start_date, end_date),
            )
            deleted_rows = cursor.rowcount
            if deleted_rows > 0:
                logger.warning(f"Cleared {deleted_rows} overlapping historical rows from {env.ml_matches_table}.")

            # Preparazione dei record convertendo i NaN in None (gestiti come NULL da SQLite)
            records = []
            for _, row in df_match.iterrows():
                ts = pd.to_datetime(row["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                records.append((
                    ts,
                    row.get("temp_era5") if pd.notnull(row.get("temp_era5")) else None,
                    row.get("pres_era5") if pd.notnull(row.get("pres_era5")) else None,
                    row.get("rh_era5") if pd.notnull(row.get("rh_era5")) else None,
                    row.get("wind_era5") if pd.notnull(row.get("wind_era5")) else None,
                    row.get("solar_era5") if pd.notnull(row.get("solar_era5")) else None,
                    row.get("rain_era5") if pd.notnull(row.get("rain_era5")) else None,
                    row.get("temp_eco") if pd.notnull(row.get("temp_eco")) else None,
                    row.get("pres_eco") if pd.notnull(row.get("pres_eco")) else None,
                    row.get("rh_eco") if pd.notnull(row.get("rh_eco")) else None,
                    row.get("wind_eco") if pd.notnull(row.get("wind_eco")) else None,
                    row.get("solar_eco") if pd.notnull(row.get("solar_eco")) else None,
                    row.get("rain_eco") if pd.notnull(row.get("rain_eco")) else None,
                ))

            # Inserimento esplicito con query parametrizzata
            insert_query = f"""
                INSERT OR REPLACE INTO {env.ml_matches_table} (
                    timestamp,
                    temp_era5, pres_era5, rh_era5, wind_era5, solar_era5, rain_era5,
                    temp_eco, pres_eco, rh_eco, wind_eco, solar_eco, rain_eco
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.executemany(insert_query, records)
            conn.commit()

        logger.success(
            f"Feature Store table '{env.ml_matches_table}' updated! "
            f"Inserted {len(records)} synchronized records."
        )
        return WaidExit.SUCCESS

    except Exception as e:
        raise WError(
            f"Failed to synchronize central Feature Store Database: {e}",
            code=WaidExit.CRITICAL_FAIL,
        )


def main() -> int:
    """
    @brief Main execution entry point for dataset synchronization.
    @return Execution exit code integer.
    """
    try:
        env = WaidBoot()

        parser = argparse.ArgumentParser(
            description="WAID: Advanced DB Synchronization between ERA5 and local Ecowitt data (Decoupled & UTC aligned)",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "--period",
            type=validate_period,
            required=True,
            help="Target month in YYYY-MM format",
        )

        args = parser.parse_args()

        if not ensure_table_exists(env):
            logger.error(f"Match table '{env.ml_matches_table}' missing or initialization failed.")
            return WaidExit.DATA_FAIL

        result = perform_matching_with_era5(env, args.period)
        if result == WaidExit.SUCCESS:
            return WaidExit.SUCCESS

    except WError as e:
        logger.error(f" [WAID ERROR] {e.message}")
        return e.code

    except Exception:
        logger.exception("Unexpected error during synchronization pipeline")
        return WaidExit.INTERNAL_ERROR

    return WaidExit.SUCCESS


if __name__ == "__main__":
    sys.exit(main())