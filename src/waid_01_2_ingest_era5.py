#!/usr/bin/env python3

"""
@file download_era5.py
@brief WAID automated ERA5 atmospheric reanalysis data downloader.
@details Connects directly to the Copernicus Climate Data Store (CDS) API.
         Extracts and merges multi-stream historical single-level NetCDF matrices
         in UTC timestamp standards to match station telemetry.
@author AF
@date 2026
"""

import os
import sys
import shutil
import zipfile
import calendar
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd
import xarray as xr
import cdsapi
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


def download_era5(env: WaidBoot, args: argparse.Namespace) -> bool:
    """Requests and consolidates ERA5 NetCDF reanalysis matrices from Copernicus CDS.

    @param env WaidBoot configuration instance.
    @param args Validated command-line arguments.
    @return True if downloaded/present successfully, False if skipped due to unavailability.
    """
    period: datetime = args.period
    lat: float = args.lat
    lon: float = args.lon
    elevation: int = args.elevation

    logger.info(f"Starting ERA5 Download (Month: {period.year}-{period.month:02d})")
    logger.info(f"Target UTC Coordinates: ({lat}, {lon}) | Elevation: {elevation}m")

    cds_url = env.era5_api_url
    cds_key = env.era5_api_key

    try:
        c = cdsapi.Client(url=cds_url, key=cds_key)
    except Exception as e:
        logger.error(f"Failed to initialize CDS Client: {e}")
        raise WError("CDS API Client Initialization Failed", code=WaidExit.CRITICAL_FAIL)

    # 0.5° Bounding Box centered on location
    area_filter = [lat + 0.25, lon - 0.25, lat - 0.25, lon + 0.25]
    env.era5_data_dir.mkdir(parents=True, exist_ok=True)

    filename_base = f"era5_{period.year}_{period.month:02d}"
    data_file = env.era5_data_dir / f"{filename_base}.nc"
    data_file_full = env.era5_data_dir / f"{filename_base}.full"

    # Skip if full month archive already present
    if data_file_full.exists() and data_file_full.stat().st_size > 0:
        logger.warning(f"Data already available: {data_file_full}. Skipping download.")
        return True

    # Clean partial file if present
    if data_file.exists():
        try:
            data_file.unlink()
        except OSError as e:
            logger.error(f"Cannot remove existing incomplete file {data_file}: {e}")
            raise WError("File permission error", code=WaidExit.CRITICAL_FAIL)

    logger.info(f"Requesting ERA5 variables for {period.year}-{period.month:02d} in UTC...")

    target_variables = [
        "2m_temperature",
        "2m_dewpoint_temperature",
        "surface_pressure",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "surface_solar_radiation_downwards",
        "total_precipitation",
        "geopotential",  
    ]

    try:
        days_in_month = calendar.monthrange(period.year, period.month)[1]
        c.retrieve(
            "reanalysis-era5-single-levels",
            {
                "product_type": "reanalysis",
                "format": "netcdf",
                "variable": target_variables,
                "year": str(period.year),
                "month": f"{period.month:02d}",
                "day": [f"{i:02d}" for i in range(1, days_in_month + 1)],
                "time": [f"{i:02d}:00" for i in range(24)],
                "area": area_filter,
            },
            str(data_file),
        )

        if zipfile.is_zipfile(data_file):
            logger.info("Server-side multi-file ZIP encapsulation detected. Consolidating parameter streams...")
            temp_extract_dir = env.era5_data_dir / f"temp_extract_{period.year}_{period.month:02d}"
            temp_extract_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(data_file, "r") as zip_ref:
                zip_ref.extractall(temp_extract_dir)
                nc_files = [temp_extract_dir / f for f in zip_ref.namelist() if f.endswith(".nc")]

                if nc_files:
                    logger.info(f"Combining {len(nc_files)} NetCDF stream components...")
                    datasets = [xr.open_dataset(f) for f in nc_files]

                    last_time = max(ds.valid_time.max().values for ds in datasets)
                    last_time_dt = pd.to_datetime(last_time)
                    logger.info(f"Latest record timestamp (UTC): {last_time_dt}")

                    merged_ds = xr.merge(datasets, compat="override")

                    for ds in datasets:
                        ds.close()

                    merged_ds.to_netcdf(data_file)
                    merged_ds.close()
                    logger.info("Parameter streams merged successfully into single NetCDF dataset.")

                    if days_in_month == last_time_dt.day:
                        shutil.move(data_file, data_file_full)
                        data_file = data_file_full
                        logger.info("Full month dataset confirmed and finalized.")
                else:
                    logger.error("Critical: No .nc components discovered within ZIP payload.")
                    raise WError("Invalid ZIP payload", code=WaidExit.DATA_FAIL)

            if temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir)
        else:
            logger.info("Standard uncompressed NetCDF payload received directly from CDS.")

        logger.info(f"Success! Ready data file: {data_file}")

    except Exception as e:
        error_msg = str(e)
        # Se i dati non sono ancora disponibili sul server, avvisiamo ma non blocchiamo la pipeline
        if "not of the data you have requested is available yet" in error_msg.lower() or "bad request" in error_msg.lower():
            logger.warning(f"[WAID SKIPPED/WARNING] ERA5 data for {period.year}-{period.month:02d} is not yet available on CDS: {e}")
            if data_file.exists():
                try:
                    data_file.unlink()
                except OSError:
                    pass
            return False

        logger.error(f"Error during ERA5 retrieval or extraction: {e}")
        if data_file.exists():
            try:
                data_file.unlink()
            except OSError:
                pass
        raise WError(f"ERA5 Download failed: {e}", code=WaidExit.DATA_FAIL)

    logger.info("--- ERA5 Download process completed ---")
    return True


def main() -> int:
    try:
        env = WaidBoot()

        parser = argparse.ArgumentParser(
            description="WAID: Download ERA5 Reanalysis data (UTC normalized) from Copernicus CDS",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "--period",
            type=validate_period,
            required=True,
            help="Target month in YYYY-MM format (e.g., 2026-01)",
        )

        parser.add_argument(
            "--lat",
            type=float,
            default=env.ecowitt_latitude,
            help="Latitude target coordinate",
        )
        parser.add_argument(
            "--lon",
            type=float,
            default=env.ecowitt_longitude,
            help="Longitude target coordinate",
        )
        parser.add_argument(
            "--elevation",
            type=int,
            default=env.ecowitt_elevation_m,
            help="Station elevation in meters above sea level",
        )

        args = parser.parse_args()

        if not env.era5_api_url or not env.era5_api_key:
            logger.error("Missing ERA5 API credentials in environment configuration.")
            return WaidExit.CONFIG_FAIL

        download_era5(env, args)

    except WError as e:
        logger.error(f"[WAID ERROR] {e.message}")
        return e.code

    except Exception:
        logger.exception("Unexpected error during ERA5 download process")
        return WaidExit.INTERNAL_ERROR

    return WaidExit.SUCCESS


if __name__ == "__main__":
    sys.exit(main())