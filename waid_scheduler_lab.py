#!/usr/bin/env python3

"""
@file waid_scheduler_lab.py
@brief Continuous background scheduler with automatic initial backfill check and retroactive simulation support.
@details Operates as the long-running operational service for WAID or runs in retroactive simulation mode 
         iterating through historical periods step-by-step.
@author AF
@date 2026
"""

import time
import subprocess
import sys
import os
import argparse
from pathlib import Path
from loguru import logger
from datetime import datetime, timedelta

# Import WaidBoot configuration and utility classes
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import (
    WaidBoot,
    WError,
    WaidExit,
)


def check_initial_setup_needed(env: WaidBoot) -> bool:
    """
    Checks whether historical data or database setup is missing to trigger backfill.

    @param env WaidBoot configuration context.
    @return True if the database does not exist or requires initialization, False otherwise.
    """
    db_path = Path(env.waid_db)
    if not db_path.exists():
        return True
    return False


def run_pipeline(mode: str, extra_args: list = None) -> int:
    """
    Executes the WAID orchestration pipeline script with specific modes and arguments.

    @param mode Pipeline execution mode (e.g., 'backfill', 'incremental').
    @param extra_args Optional list of additional command-line arguments.
    @return Process return code integer.
    """
    cmd = [sys.executable, "waid_orchestrate_lab.py", "--run-mode", mode]
    
    if extra_args is None:
        extra_args = []

    raw_mock_now = os.environ.get("WAID_MOCK_NOW", "").strip()
    # Ensure raw_mock_now is treated as active only if it represents a valid string timestamp
    is_mock_active = bool(raw_mock_now) and raw_mock_now.lower() not in ("none", "null", "false")

    if mode == "incremental" and "--period" not in extra_args:
        if is_mock_active:
            current_month = raw_mock_now[:7]
        else:
            current_month = datetime.now().strftime("%Y-%m")
        extra_args.extend(["--period", current_month])
        
    if extra_args:
        cmd.extend(extra_args)

    # Propagate the simulation timestamp environment variable to the subprocess if active
    env_vars = os.environ.copy()
    if is_mock_active:
        env_vars["WAID_MOCK_NOW"] = raw_mock_now
    else:
        env_vars.pop("WAID_MOCK_NOW", None)

    result = subprocess.run(cmd, env=env_vars, check=False)
    return result.returncode


def main() -> int:
    """
    Main execution entry point for the continuous operational scheduler or retroactive simulator.

    @return int Execution exit code integer.
    """
    try:
        # CLI Argument Parsing for Retroactive Mode
        parser = argparse.ArgumentParser(description="WAID Operational Scheduler & Retroactive Simulator")
        parser.add_argument("--retroactive", action="store_true", help="Enable retroactive simulation mode")
        
        # Support both new and legacy argument naming conventions
        parser.add_argument("--mock-begin", "--begin-period", dest="mock_begin", type=str, help="Start timestamp for retroactive loop (YYYY-MM-DD HH:MM:SS)")
        parser.add_argument("--mock-end", "--end-period", dest="mock_end", type=str, help="End timestamp for retroactive loop (YYYY-MM-DD HH:MM:SS)")
        args = parser.parse_args()

        env = WaidBoot()

        # --- RETROACTIVE MODE ---
        if args.retroactive:
            if not args.mock_begin or not args.mock_end:
                logger.error("Both start (--mock-begin / --begin-period) and end (--mock-end / --end-period) timestamps are required in --retroactive mode.")
                return WaidExit.CONFIG_FAIL

            begin_dt = datetime.strptime(args.mock_begin, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(args.mock_end, "%Y-%m-%d %H:%M:%S")
            current_dt = begin_dt

            logger.info(f"WAID Retroactive Simulation started from {begin_dt} to {end_dt}")
            
            # Initial setup execution
            extra_passthrough = ["--only-setup"]
            code = run_pipeline("incremental", extra_args=extra_passthrough)
            if code != 0:
                logger.error(f"Pipeline failed at DBT setup step with exit code {code}")

            try:
                while current_dt <= end_dt:
                    mock_now_str = current_dt.strftime("%Y-%m-%d %H:%M:%S")
                    os.environ["WAID_MOCK_NOW"] = mock_now_str
                    
                    logger.info(f"=== [RETROACTIVE STEP] Processing timestamp: {mock_now_str} ===")
                    
                    # Pass simulation flags to the orchestrator
                    extra_passthrough = ["--skip-ingestion-deploy", "--mock-now", mock_now_str]
                    code = run_pipeline("incremental", extra_args=extra_passthrough)
                    
                    if code != 0:
                        logger.error(f"Pipeline failed at retroactive step {mock_now_str} with exit code {code}")
                    
                    # Advance by the configured interval
                    current_dt += timedelta(hours=env.mock_interval_hours)

                # Publication step at simulation end
                logger.info("Executing final publication step (waid_08_1_viz_streamlit_app)...")
                pub_code = run_pipeline("incremental", extra_args=["--start-from", "waid_08_1_viz_streamlit_app", "--skip-setup"])                
                if pub_code == 0:
                    logger.success("Final publication step completed successfully.")
                else:
                    logger.error(f"Publication step failed with code {pub_code}")

            finally:
                # Cleanup environment variables after simulation completion
                os.environ.pop("WAID_MOCK_NOW", None)
                logger.info("WAID Retroactive Simulation completed and environment cleaned up.")

            return WaidExit.SUCCESS

        # --- STANDARD / CONTINUOUS OPERATIONAL MODE ---
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