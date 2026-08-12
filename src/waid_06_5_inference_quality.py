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

sys.path.append(str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config"))
from boot import (
    WaidBoot,
    WError,
)

def main() -> int:
    try:
        env = WaidBoot()
        db_path = env.waid_db
        logger.info(f"Starting quality check using DB: {db_path}")

        conn = sqlite3.connect(db_path)
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