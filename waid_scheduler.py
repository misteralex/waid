#!/usr/bin/env python3

"""
@file waid_scheduler.py
@brief Continuous background scheduler with automatic initial backfill check.
@details Operates as the long-running operational service for WAID. It checks
         for the existence of the core SQLite database upon startup to decide
         whether an initial historical backfill is required. Once initialized,
         it continuously executes incremental pipeline runs at configured intervals.
@author AF
@date 2026
"""

import time
import subprocess
import sys
import os
from pathlib import Path
from loguru import logger
from datetime import datetime

# Single entry point for configuration and output constants
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import (
    WaidBoot,
    WError,
    WaidExit,
)


def check_initial_setup_needed(env: WaidBoot) -> bool:
    """Checks whether historical data or database setup is missing to trigger backfill.

    @param env WaidBoot configuration context.
    @return True if the database does not exist or requires initialization, False otherwise.
    """
    db_path = Path(env.waid_db)
    if not db_path.exists():
        return True
    return False


def run_pipeline(mode: str, extra_args: list = None) -> int:
    """Executes the WAID orchestration pipeline script with specific modes and arguments.

    @param mode Pipeline execution mode (e.g., 'backfill', 'incremental').
    @param extra_args Optional list of additional command-line arguments.
    @return Process return code integer.
    """
    cmd = [sys.executable, "waid_orchestrate.py", "--run-mode", mode]
    
    if extra_args is None:
        extra_args = []
        
    # Dynamically pass the current month for incremental runs if not specified
    if mode == "incremental" and "--period" not in extra_args:
        current_month = datetime.now().strftime("%Y-%m")
        extra_args.extend(["--period", current_month])
        
    if extra_args:
        cmd.extend(extra_args)
    
    result = subprocess.run(cmd, check=False)
    return result.returncode


def main() -> int:
    """Main execution entry point for the continuous operational scheduler.

    @return Execution exit code integer.
    """
    try:
        env = WaidBoot()
        logger.info("WAID Continuous Operational Scheduler started.")
        
        interval_sec = env.scheduled_interval_sec

        # 1. Handle Initial Setup / Backfill on first boot
        if check_initial_setup_needed(env):
            logger.warning("Initial setup detected: No database or historical data found.")
            logger.info("Triggering initial BACKFILL phase...")
            logger.info(
                f"Backfill period: {env.backfill_begin_period.strftime('%Y-%m')} to {env.backfill_end_period.strftime('%Y-%m')}"
            )
            backfill_code = run_pipeline(
                "backfill", 
                ["--begin-period", env.backfill_begin_period.strftime("%Y-%m"), 
                 "--end-period", env.backfill_end_period.strftime("%Y-%m")]
            )
            
            if backfill_code == 0:
                logger.success("Initial backfill completed successfully. Model trained and ready.")
            else:
                logger.error("Initial backfill failed. Check logs for details.")
        else:
            logger.info("Existing environment detected. Skipping initial backfill.")

        # 2. Continuous Operational Loop (Incremental & Forecasting)
        while True:
            logger.info("Triggering scheduled incremental WAID pipeline run...")
            try:
                code = run_pipeline("incremental")
                if code == 0:
                    logger.success("Scheduled incremental run completed successfully.")
                else:
                    logger.error(f"Pipeline run finished with non-zero exit code: {code}")
                    
            except Exception as e:
                logger.error(f"Critical error during pipeline execution: {e}")
                return WaidExit.CRITICAL_FAIL
                
            logger.info(f"Sleeping for {interval_sec / 60:.0f} minutes until next execution...")
            time.sleep(interval_sec)
        
    except WError as e:
        logger.error(f"[WAID ERROR] {e.message}")
        return e.code
    except Exception:
        logger.exception("Unexpected failure during scheduler execution")
        return WaidExit.INTERNAL_ERROR


if __name__ == "__main__":
    sys.exit(main())