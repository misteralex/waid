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
import sqlite3

if not os.environ.get("WAID_SOURCE"):
    sys.exit("[CRITICAL] WAID_SOURCE environment variable is missing. Export it first.")

sys.path.append(str(Path(os.environ.get("WAID_SOURCE")) / "config"))
from boot import (
    WaidBoot,
    WError,
    WaidExit,
)

sys.path.append(str(Path(os.environ.get("WAID_SOURCE")) / "src"))
from waid_shared import (
    generate_period_range,
    get_last_inference_datetime,
)

def check_initial_setup_needed(env: WaidBoot) -> bool:
    """
    @brief Checks whether historical data or database setup is missing to trigger backfill.
    @param env WaidBoot configuration instance.
    @return True if initial setup (database or historical data) is needed, False otherwise.
    """
    db_path = Path(env.waid_db)
    return not db_path.exists()


def run_pipeline(mode: str, extra_args: list = None) -> int:
    """
    @brief Executes the WAID orchestration pipeline script with specific modes and arguments.
    @param mode The run mode for the pipeline (e.g., "incremental", "backfill").
    @param extra_args Optional; a list of additional arguments to pass to the pipeline script.
    @return The exit code of the subprocess execution.
    """
    cmd = [sys.executable, "waid_orchestrate_lab.py", "--run-mode", mode]
    
    if extra_args is None:
        extra_args = []

    raw_mock_now = os.environ.get("WAID_MOCK_NOW", "").strip()
    is_mock_active = bool(raw_mock_now) and raw_mock_now.lower() not in ("none", "null", "false")

    if mode == "incremental" and "--period" not in extra_args:
        if is_mock_active:
            current_month = raw_mock_now[:7]
        else:
            current_month = datetime.now().strftime("%Y-%m")
        extra_args.extend(["--period", current_month])
        
    if extra_args:
        cmd.extend(extra_args)

    env_vars = os.environ.copy()
    if is_mock_active:
        env_vars["WAID_MOCK_NOW"] = raw_mock_now
    else:
        env_vars.pop("WAID_MOCK_NOW", None)

    result = subprocess.run(cmd, env=env_vars, check=False)
    return result.returncode


def clean_target_range(env: WaidBoot, start_dt: datetime, end_dt: datetime) -> None:
    """
    @brief Atomically cleans all predictions written within the interval [start_dt, end_dt]
           across Lab DB, Local Deploy DB, and Supabase Cloud.
    @param env WaidBoot configuration instance.
    @param start_dt Start datetime for the cleaning range.
    @param end_dt End datetime for the cleaning range.
    @return None
    """
    str_begin = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    str_end = end_dt.strftime("%Y-%m-%d %H:%M:%S")

    logger.warning(f"[RETRO_CLEAN] Cleaning target range from {str_begin} to {str_end}...")
    
    # 1. LAB DB (inference_forecast, inference_stats, inference_quality)
    lab_db_path = Path(env.waid_db)
    if lab_db_path.exists():
        with sqlite3.connect(lab_db_path) as conn:
            cursor = conn.cursor()
            lab_tables = ["inference_forecast", "inference_stats", "inference_quality"]
            logger.debug(f"[RETRO_CLEAN] Cleaning Lab DB tables: {lab_tables}")
            for table in lab_tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    cursor.execute(
                        f"DELETE FROM {table} WHERE datetime(timestamp) BETWEEN datetime(?) AND datetime(?)",
                        (str_begin, str_end)
                    )
            conn.commit()

    # 2. LOCAL DEPLOY DB (public_forecasts in waid_deploy.db)
    deploy_db_path = Path(env.waid_data_dir) / env.deploy_db_file
    if deploy_db_path.exists():
        with sqlite3.connect(deploy_db_path) as conn:
            logger.debug(f"[RETRO_CLEAN] Cleaning Local Deploy DB tables: public_forecasts")
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='public_forecasts'")
            if cursor.fetchone():
                cursor.execute(
                    "DELETE FROM public_forecasts WHERE datetime(timestamp) BETWEEN datetime(?) AND datetime(?)",
                    (str_begin, str_end)
                )
                conn.commit()

    # 3. SUPABASE CLOUD (public_forecasts)
    if env.deploy_mode == "cloud":
        try:
            from sqlalchemy import create_engine, text
            from sqlalchemy.pool import NullPool
            
            db_config = env.active_db_config
            schema_name = env.db_schema_target.lower()
            supabase_url = (
                f"postgresql+psycopg2://{db_config.user}:{db_config.password}"
                f"@{db_config.host}:{db_config.port}/{db_config.dbname}?sslmode=require"
            )
            
            engine = create_engine(supabase_url, poolclass=NullPool)
            with engine.connect() as conn:
                logger.debug(f"[RETRO_CLEAN] Cleaning Supabase DB tables: {schema_name}.public_forecasts")
                delete_stmt = text(f"""
                    DELETE FROM {schema_name}.public_forecasts 
                    WHERE timestamp::timestamp BETWEEN :start_ts::timestamp AND :end_ts::timestamp;
                """)
                conn.execute(delete_stmt, {"start_ts": str_begin, "end_ts": str_end})
                conn.commit()
        except Exception as e:
            logger.error(f"[RETRO_CLEAN] Failed to clean Supabase DB: {e}")


def main() -> int:
    """
    @brief Main execution entry point for the continuous operational scheduler or retroactive simulator.
    @return An integer representing the exit status (0 for success, non-zero for failure).
    """
    try:
        parser = argparse.ArgumentParser(description="WAID Operational Scheduler & Retroactive Simulator")
        parser.add_argument("--retroactive", action="store_true", help="Enable retroactive simulation mode")
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
            logger.warning(f"[RETRO] Executing retroactive simulation from {begin_dt} to {end_dt}...")
            
            # Initial DBT setup
            extra_passthrough = ["--only-setup"]
            code = run_pipeline("incremental", extra_args=extra_passthrough)
            if code != 0:
                logger.error(f"Pipeline failed at DBT setup step with exit code {code}")

            try:
                # 1. Initial Broad Cleaning of the entire interval
                if env.retro_cleanup:
                    logger.warning(f"[RETRO CLEAN] Executing initial broad cleaning from {begin_dt} to {end_dt}...")
                    clean_target_range(env, begin_dt, end_dt)

                # 2. Retroactive loop with preventive cleaning at each step
                while current_dt < end_dt:
                    mock_now_str = current_dt.strftime("%Y-%m-%d %H:%M:%S")
                    os.environ["WAID_MOCK_NOW"] = mock_now_str
                    
                    # Calculate the forecast horizon interval for this step
                    forecast_horizon_end = current_dt + timedelta(hours=env.mock_interval_hours)
                    
                    # Preventive cleaning of the window we are about to overwrite
                    clean_target_range(env, current_dt, forecast_horizon_end)
                    
                    logger.info(f"=== [RETROACTIVE STEP] Processing timestamp: {mock_now_str} ===")
                    
                    extra_passthrough = ["--skip-ingestion-ml-deploy", "--mock-now", mock_now_str]
                    code = run_pipeline("incremental", extra_args=extra_passthrough)
                    
                    if code != 0:
                        logger.error(f"Pipeline failed at retroactive step {mock_now_str} with exit code {code}")
                    
                    current_dt += timedelta(hours=env.mock_interval_hours)

                # Final publication step
                logger.info("Executing final publication step (waid_08_1_viz_streamlit_app)...")
                pub_code = run_pipeline("incremental", extra_args=["--start-from", "waid_08_1_viz_streamlit_app", "--skip-setup"])                
                if pub_code == 0:
                    logger.success("Final publication step completed successfully.")
                else:
                    logger.error(f"Publication step failed with code {pub_code}")

            finally:
                os.environ.pop("WAID_MOCK_NOW", None)
                logger.info("WAID Retroactive Simulation completed and environment cleaned up.")

            return WaidExit.SUCCESS

        # --- STANDARD / CONTINUOUS OPERATIONAL MODE ---
        logger.info("WAID Continuous Operational Scheduler started.")
        interval_hours = env.scheduled_interval_hours

        if check_initial_setup_needed(env):
            logger.warning("Initial setup detected: No database or historical data found.")
            logger.info("Triggering initial BACKFILL phase...")
            backfill_code = run_pipeline(
                "backfill", 
                ["--begin-period", env.backfill_begin_period.strftime("%Y-%m"), 
                 "--end-period", env.backfill_end_period.strftime("%Y-%m")]
            )
            if backfill_code != 0:
                logger.error("Initial backfill failed. Check logs for details.")
        else:
            logger.info("Existing environment detected. Skipping initial backfill.")

        while True:
            logger.info("Triggering scheduled incremental WAID pipeline run...")
            try:
                extra_passthrough = ["--skip-ingestion-ml-deploy"]
                code = run_pipeline("incremental", extra_args=extra_passthrough)
                if code == 0:
                    logger.success("Scheduled incremental run completed successfully.")
                else:
                    logger.error(f"Pipeline run finished with non-zero exit code: {code}")
            except Exception as e:
                logger.error(f"Critical error during pipeline execution: {e}")
                return WaidExit.CRITICAL_FAIL
                
            logger.info(f"Sleeping for {interval_hours :.0f} hours until next execution...")
            time.sleep(interval_hours * 3600)
        
    except WError as e:
        logger.error(f"[WAID ERROR] {e.message}")
        return e.code
    except Exception:
        logger.exception("Unexpected failure during scheduler execution")
        return WaidExit.INTERNAL_ERROR


if __name__ == "__main__":
    sys.exit(main())