#!/usr/bin/env python3

"""
@file waid_06_4_inference_quality.py
@brief WAID Quality Check Script.
@details Validates inference records and quality metrics in the SQLite database.
@author AF
@date 2026
"""

from config.boot import (
    WaidBoot,
    WError,
    WaidExit,
    validate_mock_timestamp,
)
from src.waid_shared import (
    check_db_table_exists,
)
import sys
import sqlite3
from loguru import logger
import argparse


def main() -> int:
    """
    @brief Executes the inference quality check pipeline, verifying database tables and record counts.
    @return Process exit status code integer.
    """
    try:
        parser = argparse.ArgumentParser(description="WAID Inference Engine")
        parser.add_argument("--retro-now", type=str, default=None, help="Simulated current timestamp")
        args, _ = parser.parse_known_args()
        
        env = WaidBoot()
        
        if args.retro_now:
            env.retro_now = validate_mock_timestamp(args.retro_now)
            logger.info(f"Overriding retro_now with CLI argument: {env.retro_now}")

        logger.info(f"Starting quality check using DB: {env.waid_db_file}")
        conn = sqlite3.connect(env.waid_db_file)
        cursor = conn.cursor()

        if not check_db_table_exists(env, env.db.inference_quality):
            logger.warning(f"The table {env.db.inference_quality} does not exist.")
            
        # Check quality benchmark table/view (inference quality table)
        cursor.execute("SELECT name FROM sqlite_master WHERE type in ('table', 'view') AND name='inference_quality';")
        if cursor.fetchone():
            cursor.execute(f"SELECT COUNT(*) FROM {env.db.inference_quality};")
            quality_count = cursor.fetchone()[0]
            logger.info(f"Total quality benchmark records found: {quality_count}")
        else:
            logger.warning(f"Table/View '{env.db.inference_quality}' does not exist in the database.")

        conn.close()
        logger.success("Quality check completed successfully.")

    except Exception as e:
        logger.error(f"Database failure during quality check: {e}")
        return env.waid_exit.INTERNAL_ERROR

    return env.waid_exit.SUCCESS

if __name__ == "__main__":
    sys.exit(main())