#!/usr/bin/env python3

"""
@file waid_06_5_inference_quality.py
@brief WAID Quality Check Script.
@details Validates inference records and quality metrics in the SQLite database.
@author AF
@date 2026
"""

import os
import sys
import sqlite3
from pathlib import Path
from loguru import logger
import argparse

sys.path.append(str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config"))
from boot import (
    WaidBoot,
    WError,
    validate_mock_timestamp,
)

def main() -> int:
    """
    Executes the inference quality check pipeline, verifying database tables and record counts.
    
    Returns:
        int: Process exit status code.
    """
    try:
        parser = argparse.ArgumentParser(description="WAID Inference Engine")
        parser.add_argument("--mock-now", type=str, default=None, help="Simulated current timestamp")
        args, _ = parser.parse_known_args()
        
        env = WaidBoot()
        
        if args.mock_now:
            env.mock_now = validate_mock_timestamp(args.mock_now)
            logger.info(f"Overriding mock_now with CLI argument: {env.mock_now}")

        logger.info(f"Starting quality check using DB: {env.waid_db}")
        conn = sqlite3.connect(env.waid_db)
        cursor = conn.cursor()

        # Verify existence of inference tables and check record counts
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inference_records';")
        if not cursor.fetchone():
            logger.error("Table 'inference_records' does not exist in the database.")
            conn.close()
            return env.waid_exit.DATA_FAIL
        
        cursor.execute("SELECT COUNT(*) FROM inference_records;")
        total_records = cursor.fetchone()[0]
        logger.info(f"Total inference records found: {total_records}")

        if total_records == 0:
            logger.warning("Inference records table is empty.")

        # Optional check on quality view/table if present
        cursor.execute("SELECT name FROM sqlite_master WHERE type in ('table', 'view') AND name='inference_quality';")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM inference_quality;")
            quality_count = cursor.fetchone()[0]
            logger.info(f"Total quality benchmark records found: {quality_count}")

        conn.close()
        logger.success("Quality check completed successfully.")

    except Exception as e:
        logger.error(f"Database failure during quality check: {e}")
        return env.waid_exit.INTERNAL_ERROR

    return env.waid_exit.SUCCESS

if __name__ == "__main__":
    sys.exit(main())