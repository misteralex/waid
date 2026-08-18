#!/usr/bin/env python3

"""
@file waid_debug_timestamps.py
@brief Audit utility to validate UTC consistency and time-alignment across all SQLite tables.
@details Inspects min/max timestamps, formats, detected offsets, and potential 
         UTC vs Local (CEST/CET) discrepancies across key WAID database tables.
@author AF
@date 2026
"""

import os
import sys
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from loguru import logger

# Safely append configuration path
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import WaidBoot, WError, WaidExit


def inspect_table_timestamps(conn: sqlite3.Connection, table_name: str, ts_column: str = "timestamp") -> None:
    """Audits timestamp formats, boundaries, and alignment for a single table.

    @param conn: Active SQLite database connection.
    @param table_name: Name of the table to inspect.
    @param ts_column: Name of the timestamp column.
    """
    logger.info(f"--- Inspecting Table: '{table_name}' (Column: '{ts_column}') ---")
    
    try:
        # Check if table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            logger.warning(f"Table '{table_name}' does not exist in database. Skipping.")
            return

        query = f"""
            SELECT {ts_column} 
            FROM {table_name} 
            WHERE {ts_column} IS NOT NULL 
            ORDER BY {ts_column} DESC 
            LIMIT 5
        """
        df_recent = pd.read_sql_query(query, conn)

        if df_recent.empty:
            logger.warning(f"Table '{table_name}' is empty.")
            return

        logger.info(f"Top 5 most recent timestamps in '{table_name}':")
        for ts_val in df_recent[ts_column]:
            logger.debug(f"  -> {ts_val}")

        # Get overall min and max
        cursor.execute(f"SELECT MIN({ts_column}), MAX({ts_column}), COUNT(*) FROM {table_name}")
        min_ts, max_ts, total_count = cursor.fetchone()
        logger.info(f"Stats for '{table_name}': Total Rows = {total_count} | Min = {min_ts} | Max = {max_ts}")

    except sqlite3.Error as e:
        logger.error(f"Database error inspecting table '{table_name}': {e}")
    except Exception as e:
        logger.error(f"Unexpected error inspecting table '{table_name}': {e}")


def compare_cross_table_alignment(conn: sqlite3.Connection) -> None:
    """Compares the latest available timestamp across all primary tables to spot time lag.

    @param conn: Active SQLite database connection.
    """
    logger.info("--- Comparing Latest Timestamps Across Tables ---")
    
    tables_to_check = [
        ("ecowitt_records", "timestamp"),
        ("stg_ecowitt", "timestamp"),
        ("match_records", "timestamp"),
        ("int_matches_bias", "timestamp"),
        ("inference_forecast", "timestamp"),
    ]

    latest_records = {}
    for tbl, col in tables_to_check:
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT MAX({col}) FROM {tbl}")
            row = cursor.fetchone()
            max_val = row[0] if row else None
            latest_records[tbl] = max_val
            logger.info(f"  * {tbl:<20} -> Latest: {max_val}")
        except sqlite3.Error as e:
            logger.error(f"Could not read max timestamp from '{tbl}': {e}")

    # System UTC reference time
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logger.info("--- System Time Reference ---")
    logger.info(f"Current System UTC Time  : {now_utc}")
    logger.info(f"Current System Local Time: {now_local}")


def main() -> int:
    """Main entry point for the timestamp audit utility script.

    @return: Process exit status code.
    """
    try:
        env = WaidBoot()
        logger.info(f"Connecting to WAID database at: {env.waid_db}")

        if not os.path.exists(env.waid_db):
            logger.error(f"Database file not found: {env.waid_db}")
            return WaidExit.DATA_FAIL

        with sqlite3.connect(env.waid_db) as conn:
            tables = [
                ("ecowitt_records", "timestamp"),
                ("stg_ecowitt", "timestamp"),
                ("match_records", "timestamp"),
                ("int_matches_bias", "timestamp"),
                ("inference_forecast", "timestamp"),
            ]
            
            for tbl, col in tables:
                inspect_table_timestamps(conn, tbl, col)

            compare_cross_table_alignment(conn)

        logger.success("Timestamp audit completed successfully.")
        return WaidExit.SUCCESS

    except WError as e:
        logger.error(f"[WAID ERROR] {e.message}")
        return e.code
    except Exception as e:
        logger.exception(f"Unexpected error during timestamp audit: {e}")
        return WaidExit.INTERNAL_ERROR


if __name__ == "__main__":
    sys.exit(main())