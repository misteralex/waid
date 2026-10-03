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

if not os.environ.get("WAID_SOURCE"):
    sys.exit("[CRITICAL] WAID_SOURCE environment variable is missing. Export it first.")

sys.path.append(str(Path(os.environ.get("WAID_SOURCE")) / "config"))
from boot import (
    WaidBoot,
    WError,
    WaidExit,
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
    """Derives UTC timestamps from the station's Unix epoch (source of truth).

    @param df Input DataFrame containing raw station timestamps and epoch column.
    @param local_tz String representation of the local station timezone (e.g., 'Europe/Paris').
    @return Processed DataFrame with standardized UTC 'timestamp' strings and integer 'epoch_timestamp'.
    """
    epoch = df["epoch_timestamp"].astype("int64")

    # Sanity check: the CSV local label must agree with the epoch
    label = pd.to_datetime(df["timestamp"])
    true_local = (
        pd.to_datetime(epoch, unit="s", utc=True)
        .dt.tz_convert(local_tz).dt.tz_localize(None).dt.floor("min")
    )
    bad = int((label != true_local).sum())
    if bad:
        logger.warning(f"{bad} rows have a local label that disagrees with the epoch")

    df["timestamp"] = pd.to_datetime(epoch, unit="s", utc=True).dt.strftime("%Y-%m-%d %H:%M:00")
    df["epoch_timestamp"] = epoch
    return df


def report_gaps(
    df: pd.DataFrame,
    min_gap_min: int = 2,
    max_missing_ratio: float = 0.02,
    max_gap_min: int = 180,
) -> pd.DataFrame:
    """Detects gaps in the 1-minute Ecowitt telemetry (UTC 'timestamp' column).
 
    Read-only: logs the gaps and returns them, it does NOT fill anything.
 
    @param df DataFrame after process_timestamps_to_utc().
    @param min_gap_min Minimum number of consecutive missing minutes to log.
    @param max_missing_ratio Warn if missing/expected exceeds this ratio.
    @param max_gap_min Warn if the longest gap exceeds this many minutes.
    @return DataFrame with columns start, end, missing_min.
    """
    s = (
        pd.Series(pd.to_datetime(df["timestamp"], utc=True))
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )
    if len(s) < 2:
        return pd.DataFrame(columns=["start", "end", "missing_min"])
 
    step = pd.Timedelta(minutes=1)
    delta_min = s.diff().dt.total_seconds() / 60
    mask = delta_min > 1.5  # tolerate small jitter
 
    gaps = pd.DataFrame(
        {
            "start": s.shift(1)[mask] + step,
            "end": s[mask] - step,
            "missing_min": (delta_min[mask] - 1).round().astype(int),
        }
    ).reset_index(drop=True)
 
    expected = int((s.iloc[-1] - s.iloc[0]) / step) + 1
    missing = int(gaps["missing_min"].sum())
    ratio = missing / expected if expected else 0.0
 
    for g in gaps[gaps["missing_min"] >= min_gap_min].itertuples():
        logger.warning(
            f"Gap of {g.missing_min} min: {g.start:%Y-%m-%d %H:%M} UTC -> {g.end:%Y-%m-%d %H:%M} UTC"
        )
 
    longest = int(gaps["missing_min"].max()) if len(gaps) else 0
    logger.info(
        f"Gap summary: {missing}/{expected} minutes missing ({ratio:.2%}), "
        f"{len(gaps)} gaps, longest {longest} min"
    )
    if ratio > max_missing_ratio or longest > max_gap_min:
        logger.warning(
            f"Data quality threshold exceeded (ratio>{max_missing_ratio:.0%} or gap>{max_gap_min} min)"
        )
    return gaps


def sync_ecowitt_with_db(
    env: WaidBoot,
    args: argparse.Namespace,
    fields: dict,
) -> None:
    """Orchestrates CSV loading, UTC conversion, and SQLite idempotent upsert.

    @param env Boot environment instance.
    @param args Validated CLI arguments.
    @param fields Mapping of original columns to database schema names.
    @return None
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

    # Standardize Timestamps to UTC and check gaps
    df = process_timestamps_to_utc(df, env.tz_timezone)
    report_gaps(df)

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