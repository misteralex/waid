#!/usr/bin/env python3

"""
@file waid_scheduler_lab.py
@brief Continuous background scheduler with automatic initial backfill check and retroactive simulation support.
@details Operates as the long-running operational service for WAID or runs in retroactive simulation mode 
         iterating through historical periods step-by-step.
@author AF
@date 2026
"""

import argparse
import os
import requests
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from loguru import logger
from urllib.parse import urljoin

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
    is_mock_active = bool(raw_mock_now) and raw_mock_now.lower() not in (
        "none",
        "null",
        "false",
    )

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


def ping_streamlit(env: WaidBoot, timeout: int = 15) -> None:
    """
    @brief Sends HTTP GET requests to Streamlit endpoints (_stcore/health and main URL) to maintain app activity.
    @param env WaidBoot configuration instance containing the target Streamlit URL.
    @param timeout HTTP request timeout in seconds (default is 15 seconds).
    @return None
    """
    base_url = env.streamlit_url
    health_url = urljoin(base_url if base_url.endswith("/") else f"{base_url}/", "_stcore/health")
    
    logger.info(
        f"Keep-alive ping for Streamlit ({base_url}) with a timeout of {timeout} seconds..."
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Cache-Control": "no-cache",
    }

    try:
        with requests.Session() as session:
            # 1. Ping primary entrypoint
            res_main = session.get(base_url, headers=headers, timeout=timeout)
            
            # 2. Ping internal healthcheck endpoint
            res_health = session.get(health_url, headers=headers, timeout=timeout)
            
            logger.info(
                f"[Keep-Alive] Streamlit ping successful! Main: {res_main.status_code}, Health: {res_health.status_code}"
            )
    except Exception as e:
        logger.error(f"[Keep-Alive] Error during Streamlit ping: {e}")


def clean_target_range(
    env: WaidBoot, start_dt: datetime, end_dt: datetime
) -> None:
    """
    @brief Atomically cleans predictions written within the interval [start_dt, end_dt]
           in local SQLite databases. Remote Supabase cleanup is bypassed in favor of 
           downstream UPSERT transfers.
    @param env WaidBoot configuration instance.
    @param start_dt Range start datetime.
    @param end_dt Range end datetime.
    @return None
    """
    local_tz = ZoneInfo(env.tz_timezone)
    utc_tz = ZoneInfo("UTC")

    start_dt_local = (
        start_dt.replace(tzinfo=local_tz)
        if start_dt.tzinfo is None
        else start_dt.astimezone(local_tz)
    )
    end_dt_local = (
        end_dt.replace(tzinfo=local_tz)
        if end_dt.tzinfo is None
        else end_dt.astimezone(local_tz)
    )

    start_dt_utc = start_dt_local.astimezone(utc_tz)
    end_dt_utc = end_dt_local.astimezone(utc_tz)

    str_begin_utc = start_dt_utc.strftime("%Y-%m-%d %H:%M:%S")
    str_end_utc = end_dt_utc.strftime("%Y-%m-%d %H:%M:%S")

    str_begin_loc = start_dt_local.strftime("%Y-%m-%d %H:%M:%S")
    str_end_loc = end_dt_local.strftime("%Y-%m-%d %H:%M:%S")

    logger.warning(
        f"[RETRO_CLEAN] Target Local: {str_begin_loc} -> {str_end_loc} | "
        f"Converted UTC: {str_begin_utc} -> {str_end_utc}"
    )

    # 1. LAB DB (SQLite)
    lab_db_path = Path(env.waid_db)
    if lab_db_path.exists():
        with sqlite3.connect(lab_db_path) as conn:
            cursor = conn.cursor()
            lab_tables = [
                "inference_forecast",
                "inference_stats",
                "inference_quality",
            ]
            for table in lab_tables:
                cursor.execute(
                    f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
                )
                if cursor.fetchone():
                    cursor.execute(
                        f"""
                        DELETE FROM {table} 
                        WHERE datetime(timestamp) BETWEEN datetime(?) AND datetime(?)
                        """,
                        (str_begin_utc, str_end_utc),
                    )
            conn.commit()

    # 2. LOCAL DEPLOY DB (SQLite)
    deploy_db_path = Path(env.deploy_db_file)
    if deploy_db_path.exists():
        with sqlite3.connect(deploy_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='public_forecasts'"
            )
            if cursor.fetchone():
                cursor.execute(
                    """
                    DELETE FROM public_forecasts 
                    WHERE datetime(timestamp) BETWEEN datetime(?) AND datetime(?)
                       OR datetime(created_at) BETWEEN datetime(?) AND datetime(?)
                    """,
                    (str_begin_utc, str_end_utc, str_begin_loc, str_end_loc),
                )
                conn.commit()

    # 3. SUPABASE CLOUD (PostgreSQL) - BYPASSED
    logger.info(
        "[RETRO_CLEAN] Remote Supabase cleanup bypassed. Deduplication will be handled by UPSERT during deploy."
    )


def main() -> int:
    """
    @brief Main execution entry point for the continuous operational scheduler or retroactive simulator.
    @return An integer representing the exit status (0 for success, non-zero for failure).
    """
    try:
        parser = argparse.ArgumentParser(
            description="WAID Operational Scheduler & Retroactive Simulator"
        )
        parser.add_argument(
            "--retroactive",
            action="store_true",
            help="Enable retroactive simulation mode",
        )
        parser.add_argument(
            "--mock-begin",
            "--begin-period",
            dest="mock_begin",
            type=str,
            help="Start timestamp for retroactive loop (YYYY-MM-DD HH:MM:SS)",
        )
        parser.add_argument(
            "--mock-end",
            "--end-period",
            dest="mock_end",
            type=str,
            help="End timestamp for retroactive loop (YYYY-MM-DD HH:MM:SS)",
        )
        args = parser.parse_args()

        env = WaidBoot()

        # --- RETROACTIVE MODE ---
        if args.retroactive:
            if not args.mock_begin or not args.mock_end:
                logger.error(
                    "Both start (--mock-begin / --begin-period) and end (--mock-end / --end-period) timestamps are required in --retroactive mode."
                )
                return WaidExit.CONFIG_FAIL

            local_tz = ZoneInfo(env.tz_timezone)

            # Preserve native local datetimes for mock clock orchestration
            begin_dt_local = datetime.strptime(
                args.mock_begin, "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=local_tz)
            end_dt_local = datetime.strptime(
                args.mock_end, "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=local_tz)

            logger.warning(
                f"[RETRO] Executing retroactive simulation from {begin_dt_local} to {end_dt_local}..."
            )

            try:
                # Initial broad cleanup across the target interval
                if env.retro_cleanup:
                    logger.warning(
                        f"[RETRO CLEAN] Executing initial broad cleaning from {begin_dt_local} to {end_dt_local}..."
                    )
                    clean_target_range(env, begin_dt_local, end_dt_local)

                # Sequential retroactive simulation loop
                current_dt = begin_dt_local
                while current_dt < end_dt_local:
                    mock_now_str = current_dt.strftime("%Y-%m-%d %H:%M:%S")
                    os.environ["WAID_MOCK_NOW"] = mock_now_str

                    logger.info(
                        f"=== [RETROACTIVE STEP] Processing timestamp: {mock_now_str} ==="
                    )

                    extra_passthrough = [
                        "--skip-ingestion-ml-deploy",
                        "--mock-now",
                        mock_now_str,
                    ]
                    code = run_pipeline(
                        "incremental", extra_args=extra_passthrough
                    )

                    if code != 0:
                        logger.error(
                            f"Pipeline failed at retroactive step {mock_now_str} with exit code {code}"
                        )

                    current_dt += timedelta(hours=env.mock_interval_hours)

                # Final publication step
                logger.info(
                    "Executing final publication step (waid_07_1_export_deploy_db)..."
                )
                pub_code = run_pipeline(
                    "incremental",
                    extra_args=[
                        "--start-from",
                        "waid_07_1_export_deploy_db",
                    ],
                )
                if pub_code == 0:
                    logger.success(
                        "Final publication step completed successfully."
                    )
                else:
                    logger.error(
                        f"Publication step failed with code {pub_code}"
                    )

            finally:
                os.environ.pop("WAID_MOCK_NOW", None)
                logger.info(
                    "WAID Retroactive Simulation completed and environment cleaned up."
                )

            return WaidExit.SUCCESS

        # --- STANDARD / CONTINUOUS OPERATIONAL MODE ---
        logger.info("WAID Continuous Operational Scheduler started.")
        interval_hours = env.scheduled_interval_hours

        if check_initial_setup_needed(env):
            logger.warning(
                "Initial setup detected: No database or historical data found."
            )
            logger.info("Triggering initial BACKFILL phase...")
            backfill_code = run_pipeline(
                "backfill",
                [
                    "--begin-period",
                    env.backfill_begin_period.strftime("%Y-%m"),
                    "--end-period",
                    env.backfill_end_period.strftime("%Y-%m"),
                ],
            )
            if backfill_code != 0:
                logger.error("Initial backfill failed. Check logs for details.")
        else:
            logger.info(
                "Existing environment detected. Skipping initial backfill."
            )

        while True:
            ping_streamlit(env, 30)

            logger.info("Triggering scheduled incremental WAID pipeline run...")
            try:
                code = run_pipeline("incremental")
                if code == 0:
                    logger.success(
                        "Scheduled incremental run completed successfully."
                    )
                else:
                    logger.error(
                        f"Pipeline run finished with non-zero exit code: {code}"
                    )
            except Exception as e:
                logger.error(f"Critical error during pipeline execution: {e}")
                return WaidExit.CRITICAL_FAIL

            logger.info(
                f"Sleeping for {interval_hours:.0f} hours until next execution..."
            )
            time.sleep(interval_hours * 3600)

    except WError as e:
        logger.error(f"[WAID ERROR] {e.message}")
        return e.code
    except Exception:
        logger.exception("Unexpected failure during scheduler execution")
        return WaidExit.INTERNAL_ERROR


if __name__ == "__main__":
    sys.exit(main())