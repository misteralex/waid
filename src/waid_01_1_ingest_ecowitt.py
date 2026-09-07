#!/usr/bin/env python3

"""
@file waid_01_1_ingest_ecowitt.py
@brief WAID automated Ecowitt data ingestor.
@details Downloads split monthly CSV files directly from the station gateway web server
         using urllib. Validates sizes and handles connectivity/timeout constraints.
@author AF
@date 2026
"""

import os
import argparse
from datetime import datetime
from pathlib import Path
import sys
import urllib.request
import urllib.error
from loguru import logger

# Import WaidBoot configuration and utility classes
sys.path.append(str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config"))
from boot import (
    WaidBoot,
    validate_period,
    WError,
)


def check_url_exists(url: str, timeout: int = 30) -> bool:
    """
    @brief Checks if a URL exists using an HTTP GET request reading only the first bytes.
    @param url Target endpoint URL string.
    @param timeout Network request timeout in seconds.
    @return True if accessible with HTTP 200, False otherwise.
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status == 200:
                response.read(9)
                return True
    except Exception:
        return False
    return False


def download_ecowitt_data(
    env: WaidBoot,
    args: argparse.Namespace
) -> int:
    """
    @brief Downloads monthly CSV logs from the Ecowitt gateway server using urllib.
    @param env WaidBoot configuration and path context.
    @param args Parsed command line arguments containing period, IP, port, and timeout.
    @return Status exit code integer.
    """
    period = args.period
    ip = args.ip
    port = args.port
    timeout = args.timeout

    logger.info("Starting Ecowitt Download")
    logger.info(f"Period: {period.year}-{period.month:02d} | Station: {ip}:{port}")

    current_time = datetime.now()
    is_current_month = (
        period.year == current_time.year
        and period.month == current_time.month
    )

    base_name = f"{period.year}{period.month:02d}"
    existing_file = env.ecowitt_dir / f"{base_name}.csv"
    temp_file = env.ecowitt_dir / f"{base_name}.download"
    data_file = (
        env.ecowitt_dir / f"{base_name}.csv"
        if is_current_month
        else env.ecowitt_dir / f"{base_name}.full"
    )

    logger.info(f"Target file: {data_file.name}")

    # If the historical month is already complete, skip downloading
    if not is_current_month and data_file.exists():
        logger.warning(f"Data already complete: {data_file.name}")
        return env.waid_exit.SUCCESS
    
    chunk_name = f"{base_name}A.csv"
    url = f"http://{ip}:{port}/{chunk_name}"

    if not check_url_exists(url):
        logger.info(f"No data available ({chunk_name})")
        return env.waid_exit.DATA_FAIL

    logger.info(f"Downloading {chunk_name}")

    MIN_SIZE_BYTES = 100

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "WAID-Ingestor/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response, open(temp_file, "wb") as out_file:
            if response.status != 200:
                logger.error(f"HTTP error: {response.status}")
                return env.waid_exit.DATA_FAIL
            out_file.write(response.read())
    except (TimeoutError, urllib.error.URLError) as e:
        logger.error(f"Download timeout or network error: {e}")
        if temp_file.exists():
            temp_file.unlink()
        return env.waid_exit.DATA_FAIL
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        if temp_file.exists():
            temp_file.unlink()
        return env.waid_exit.DATA_FAIL

    download_ok = (
        temp_file.exists()
        and temp_file.stat().st_size >= MIN_SIZE_BYTES
    )

    if not download_ok:
        logger.error("Download failed or file too small")
        if temp_file.exists():
            temp_file.unlink()
        return env.waid_exit.DATA_FAIL

    # Update current file safely
    if existing_file.exists():
        existing_file.unlink()
    temp_file.rename(data_file)
    
    logger.info(f"Successfully created: {data_file.name}")
    return env.waid_exit.SUCCESS
        

def main() -> int:
    """
    @brief Main execution entry point for Ecowitt data downloading.
    @return Process exit code integer.
    """
    try:
        env = WaidBoot()
    
        parser = argparse.ArgumentParser(
            description="WAID: Automated Ecowitt telemetry ingestion downloader.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "--period",
            type=validate_period,
            help="Target month in YYYY-MM format",
        )
        
        logger.info(f"Default station IP: {env.ecowitt_gw_ip}")
        parser.add_argument("--ip", default=env.ecowitt_gw_ip, help="Station IP address")
        parser.add_argument("--port", default=env.ecowitt_gw_port, help="Station port")
        parser.add_argument("--timeout", type=int, default=env.ecowitt_gw_timeout_sec, help="Timeout in seconds")

        if len(sys.argv) == 1:
            parser.print_help()
            logger.error("You must specify a valid input")
            return env.waid_exit.INPUT_FAIL
 
        args = parser.parse_args()
        code = download_ecowitt_data(env, args)

        if code != env.waid_exit.SUCCESS:
            logger.error(f"Ecowitt download failed with status code: {code}")
            return code

    except WError as e:
        logger.error(e)
        return e.code

    except Exception:
        logger.exception("Unexpected error while downloading Ecowitt data")
        return env.waid_exit.INTERNAL_ERROR

    return env.waid_exit.SUCCESS


if __name__ == "__main__":
    sys.exit(main())