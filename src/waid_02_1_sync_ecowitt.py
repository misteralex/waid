#!/usr/bin/env python3

"""
@file waid_02_1_sync_ecowitt.py
@brief Batch aggregator for Ecowitt CSV files into a central SQLite database.
@details Scans the data folder for CSVs, converts local time (configured via TZ) 
         to UTC timestamps, and performs idempotent upserts into SQLite.
@author AF
@date 2026
"""

import os
import sys
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd
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


def ensure_table_exists(env: WaidBoot) -> dict:
    """Ensures target SQLite database table exists with correct schema mapping.

    @param env WaidBoot configuration instance.
    @return Dictionary mapping CSV raw headers to database column names.
    """
    column_map = {
        "Time": "timestamp",
        "Timestamp": "epoch_timestamp",
        "Indoor Temperature(°C)": "indoor_temperature_c",
        "Indoor Humidity(%)": "indoor_humidity",
        "Outdoor Temperature(°C)": "outdoor_temperature_c",
        "Outdoor Humidity(%)": "outdoor_humidity",
        "Dew Point(°C)": "dew_point_c",
        "Feels Like(°C)": "feels_like_c",
        "VPD(kPa)": "vpd_kpa",
        "Wind(m/s)": "wind_m_s",
        "Gust(m/s)": "gust_m_s",
        "Wind Direction(deg)": "wind_direction_deg",
        "ABS Pressure(hPa)": "abs_pressure_hpa",
        "REL Pressure(hPa)": "rel_pressure_hpa",
        "Solar Rad(W/m2)": "solar_rad_w_m2",
        "UV-Index": "uv_index",
        "Rain Rate(mm/Hr)": "rain_rate_mm_hr",
        "Hourly Rain(mm)": "hourly_rain_mm",
        "Event Rain(mm)": "event_rain_mm",
        "Daily Rain(mm)": "daily_rain_mm",
        "Weekly Rain(mm)": "weekly_rain_mm",
        "Monthly Rain(mm)": "monthly_rain_mm",
        "Yearly Rain(mm)": "yearly_rain_mm",
        "Piezo Rate(mm/Hr)": "piezo_rate_mm_hr",
        "Piezo Hourly Rain(mm)": "piezo_hourly_rain_mm",
        "Piezo Event Rain(mm)": "piezo_event_rain_mm",
        "Piezo Daily Rain(mm)": "piezo_daily_rain_mm",
        "Piezo Weekly Rain(mm)": "piezo_weekly_rain_mm",
        "Piezo Monthly Rain(mm)": "piezo_monthly_rain_mm",
        "Piezo Yearly Rain(mm)": "piezo_yearly_rain_mm",
    }

    try:
        logger.info(f"Checking current Ecowitt table schema ({env.ecowitt_table})...")
        normalized_cols = list(column_map.values())

        pk_col = normalized_cols[0]
        epoch_col = normalized_cols[1]
        other_cols = [f'"{c}" REAL' for c in normalized_cols[2:]]

        create_stmt = f"""
        CREATE TABLE IF NOT EXISTS {env.ecowitt_table} (
            "{pk_col}" TEXT PRIMARY KEY,
            "{epoch_col}" INTEGER,
            {', '.join(other_cols)}
        );
        """

        with sqlite3.connect(env.waid_db) as conn:
            conn.execute(create_stmt)

        logger.info(f"Table sanity check successfully completed ({env.ecowitt_table}).")
        return column_map

    except sqlite3.Error as e:
        logger.error(f"Database error during schema initialization: {e}")
        raise WError(
            "Critical error during sanity check of the Ecowitt table",
            code=WaidExit.DATA_FAIL,
        )


def process_timestamps_to_utc(df: pd.DataFrame, local_tz: str) -> pd.DataFrame:
    """Converts local datetime strings into standardized UTC timestamps and Epoch values.

    @param df Input Pandas DataFrame containing the 'timestamp' column.
    @param local_tz Target local timezone string (e.g., 'Europe/Rome').
    @return Cleaned DataFrame with UTC timestamps.
    """
    logger.info(f"Converting raw timestamps from local timezone ('{local_tz}') to UTC...")

    # Convert to datetime series
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Localize naive local time to target TimeZone handling ambiguity
    df["timestamp"] = df["timestamp"].dt.tz_localize(
        local_tz, ambiguous="NaT", nonexistent="shift_forward"
    )

    # Drop rows with invalid dates if any
    df.dropna(subset=["timestamp"], inplace=True)

    # Compute Unix Epoch (seconds since 1970-01-01 00:00:00 UTC)
    df["epoch_timestamp"] = (df["timestamp"].astype("int64") // 10**9).astype(int)

    # Convert to UTC string representation (YYYY-MM-DD HH:MM:SS)
    df["timestamp"] = df["timestamp"].dt.tz_convert("UTC").dt.strftime("%Y-%m-%d %H:%M:%S")

    return df


def sync_ecowitt_with_db(
    env: WaidBoot,
    args: argparse.Namespace,
    fields: dict,
) -> None:
    """Orchestrates CSV loading, UTC conversion, and SQLite idempotent upsert.

    @param env Boot environment instance.
    @param args Validated CLI arguments.
    @param fields Mapping of original columns to database schema names.
    """
    period: datetime = args.period
    data_dir: Path = env.ecowitt_dir

    if not data_dir.exists():
        logger.error(f"Data folder does not exist at path: {data_dir}")
        raise WError(f"Directory not found: {data_dir}", code=WaidExit.INPUT_FAIL)

    filename_prefix = f"{period.year}{period.month:02d}"
    current_time = datetime.now()

    is_current_month = (
        period.year == current_time.year and period.month == current_time.month
    )
    extension = ".csv" if is_current_month else ".full"
    data_file = data_dir / f"{filename_prefix}{extension}"

    logger.info(f"Looking for Ecowitt data file: {data_file}")
    if not data_file.exists():
        logger.critical(f"No matching files found for path: {data_file}")
        raise WError("Source dataset file missing", code=WaidExit.INPUT_FAIL)

    # Load raw dataframe and rename columns
    df = pd.read_csv(data_file)
    df.rename(columns=fields, inplace=True)

    # Standardize Timestamps to UTC
    df = process_timestamps_to_utc(df, env.tz_timezone)

    total_added = 0
    sql_query = ""

    with sqlite3.connect(str(env.waid_db)) as conn:
        try:
            # Stage data to temporary SQLite table
            df.to_sql("staging_ecowitt", conn, if_exists="replace", index=False)

            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({env.ecowitt_table})")
            db_cols = [row[1] for row in cursor.fetchall()]

            # Keep only columns defined in target database schema
            df_cols = [c for c in df.columns if c in db_cols]

            if not df_cols:
                logger.error("No matching schema columns found between CSV file and SQLite Database!")
                return

            cols_str = ", ".join([f'"{c}"' for c in df_cols])

            sql_query = f"""
                INSERT OR IGNORE INTO {env.ecowitt_table} ({cols_str}) 
                SELECT {cols_str} FROM staging_ecowitt
            """

            cursor.execute(sql_query)
            total_added = cursor.rowcount
            conn.commit()

        except sqlite3.Error as e:
            logger.error(f"Database transaction error: {e}")
            raise WError(
                f"Synchronization failure. SQL Query: {sql_query}",
                code=WaidExit.DATA_FAIL,
            )
        finally:
            conn.execute("DROP TABLE IF EXISTS staging_ecowitt")
            conn.commit()

    logger.info(f"Aggregation complete. Total new UTC records inserted: {total_added}")


def main() -> int:
    """Main execution entry point for Ecowitt data synchronization.

    @return Process exit status code.
    """
    try:
        env = WaidBoot()

        parser = argparse.ArgumentParser(
            description="WAID: Sync local Ecowitt station telemetry CSV to SQLite database (UTC normalized)",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "--period",
            type=validate_period,
            required=True,
            help="Target month in YYYY-MM format (e.g., 2026-01)",
        )

        args = parser.parse_args()

        map_column_names = ensure_table_exists(env)
        sync_ecowitt_with_db(env, args, map_column_names)

    except WError as e:
        logger.error(f"[WAID ERROR] {e.message}")
        return e.code

    except Exception:
        logger.exception("Unexpected error while synchronizing Ecowitt data with SQLite")
        return WaidExit.INTERNAL_ERROR

    return WaidExit.SUCCESS


if __name__ == "__main__":
    sys.exit(main())