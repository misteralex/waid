#!/usr/bin/env python3

"""
@file waid_02_2_profile_era5.py
@brief WAID ERA5 NetCDF Data Profiling and Catalog Helper.
@details Validates the internal structure, dimensions, and variables of ERA5 files.
         Extracts a localized temporal slice based on coordinates to identify 
         potential data corruption or missing values (NaN data quality check).
@author AF
@date 2026
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import xarray as xr
from loguru import logger

# Inject configuration path into python execution environment
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import (
    WaidBoot,
    validate_period,
    WError,
)


def check_era5_data(env: WaidBoot, args: argparse.Namespace) -> int:
    """
    Performs metadata extraction and data profiling on a target NetCDF file.

    @param env WaidBoot configuration instance.
    @param args Validated command-line arguments.
    @return Exit status code.
    """
    period = args.period
    logger.info(f"--- Starting profiling (Month: {period.year}-{period.month:02d}) ---")

    data_full = False
    filename_base = f"era5_{period.year}_{period.month:02d}"
    data_file = env.era5_data_dir / f"{filename_base}.nc"

    if not data_file.exists():
        data_file = env.era5_data_dir / f"{filename_base}.full"
        data_full = True
        if not data_file.exists():
            logger.warning(f"[WAID SKIPPED/WARNING] No data found for {period.year}-{period.month:02d}. Skipping profiling.")
            return env.waid_exit.SUCCESS

    logger.info(f"Analyzing ERA5 file: {data_file}")
    
    try:
        # Load dataset
        with xr.open_dataset(data_file) as ds:
            # --- 1. Metadata & Header Extraction ---
            logger.info(" [HEADER & PARAMETERS]")
            logger.info(f"Dimensions: {dict(ds.sizes)}")

            data_vars = list(ds.data_vars)
            logger.info("Data Variables (Catalog mapping ready):")
            for var in data_vars:
                unit = ds[var].attrs.get("units", "n/a")
                long_name = ds[var].attrs.get("long_name", "n/a")
                logger.info(f"  - {var:10} | {unit:10} | {long_name}")

            # --- 2. Coordinate Validation ---
            logger.info(" [COORDINATE CHECK]")
            logger.info(f"Lat Range: {ds.latitude.values.min()} to {ds.latitude.values.max()}")
            logger.info(f"Lon Range: {ds.longitude.values.min()} to {ds.longitude.values.max()}")
            logger.info(f"Target from .env: {env.ecowitt_latitude}, {env.ecowitt_longitude}")

            # --- 3. Data Extraction & Validation ---
            logger.info(" [DATA PREVIEW & VALIDATION]")
            # Extract nearest point based on configuration
            df = ds.sel(
                latitude=env.ecowitt_latitude, 
                longitude=env.ecowitt_longitude, 
                method="nearest"
            ).to_dataframe().reset_index()

            # Check for NaN values
            nan_counts = df.isnull().sum()
            if nan_counts.any():
                logger.warning(f"Found missing values (NaN):\n{nan_counts[nan_counts > 0]}")
            else:
                logger.info("Data Quality: No missing values found in the selected point.")

            # Sample and basic stats
            logger.info(f"Sample Data (First 5 rows):\n{df.head(5)}")
            logger.info(f"Basic Stats:\n{df.describe().loc[['min', 'max', 'mean']]}")

            # Temporal status
            last_time = pd.to_datetime(df["valid_time"].max())
            logger.info(f"Most recent measurement: {last_time}")

            if data_full:
                logger.info("Dataset complete (archived .full month).")
            else:
                lag_days = (pd.Timestamp.now() - last_time).total_seconds() / 86400.0
                logger.warning(f"Partial dataset. Latency lag: {lag_days:.1f} days")

    except Exception as e:
        logger.error(f"Error during profiling: {e}")
        return env.waid_exit.DATA_FAIL

    return env.waid_exit.SUCCESS


def main() -> int:
    """
    Main execution entry point for ERA5 profiling.
    """
    try:
        env = WaidBoot()

        parser = argparse.ArgumentParser(
            description="ERA5 Data Profiling & Catalog Helper",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "--period",
            type=validate_period,
            required=True,
            help="Target month in YYYY-MM format",
        )

        args = parser.parse_args()
        return check_era5_data(env, args)

    except WError as e:
        logger.error(f"[WAID ERROR] {e}")
        return e.code
    except Exception:
        logger.exception("Unexpected error during ERA5 profiling process")
        return WaidBoot().waid_exit.INTERNAL_ERROR


if __name__ == "__main__":
    sys.exit(main())