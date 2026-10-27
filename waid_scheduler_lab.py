#!/usr/bin/env python3

"""
@file waid_scheduler_lab.py
@brief Continuous background scheduler with automatic initial backfill check and retroactive simulation support.
@details Operates as the long-running operational service for WAID or runs in retroactive simulation mode 
         iterating through historical periods step-by-step.
@author AF
@date 2026
"""

import os
import sys
from pathlib import Path
from config.boot import ( 
    WaidBoot,
    WError,
    WaidExit,
)
from src.waid_shared import (
    generate_period_range,
    get_last_inference_datetime,
)

import argparse
import requests
import websocket
import sqlite3
import subprocess
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from loguru import logger
from urllib.parse import urljoin


def check_initial_setup_needed(env: WaidBoot) -> bool:
    """
    @brief Checks whether historical data or database setup is missing to trigger backfill.
    @param env WaidBoot configuration instance.
    @return True if initial setup (database or historical data) is needed, False otherwise.
    """
    db_path = Path(env.waid_db_file)
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

    raw_retro_now = os.environ.get("WAID_RETRO_NOW", "").strip()
    is_mock_active = bool(raw_retro_now) and raw_retro_now.lower() not in (
        "none",
        "null",
        "false",
    )

    if mode == "incremental" and "--period" not in extra_args:
        if is_mock_active:
            current_month = raw_retro_now[:7]
        else:
            current_month = datetime.now().strftime("%Y-%m")
        extra_args.extend(["--period", current_month])

    if extra_args:
        cmd.extend(extra_args)

    env_vars = os.environ.copy()
    if is_mock_active:
        env_vars["WAID_RETRO_NOW"] = raw_retro_now
    else:
        env_vars.pop("WAID_RETRO_NOW", None)

    result = subprocess.run(cmd, env=env_vars, check=False)
    return result.returncode


def ping_streamlit(env: WaidBoot, timeout: int = 15) -> None:
    """
    @brief Sends HTTP GET requests to Streamlit endpoints (_stcore/health and main URL) to maintain app activity.
    @param env WaidBoot configuration instance containing the target Streamlit URL.
    @param timeout HTTP request timeout in seconds (default is 15 seconds).
    @return None
    """
    base_url = env.streamlit_url.rstrip("/")
    ws_url = base_url.replace("https://", "wss://").replace("http://", "ws://")
    ws_url += "/~/+/_stcore/stream"  # On Community Cloud the path includes the /~/+/ prefix

    logger.info(f"[Keep-Alive] Pinging Streamlit app: {base_url}")

    try:
        # 1) Standard GET request: wakes/routes the app and detects sleep status
        response = requests.get(base_url, timeout=timeout, allow_redirects=True)
        logger.info(f"[Keep-Alive] HTTP status={response.status_code}, url={response.url}")
        response.raise_for_status()

        if "gone to sleep" in response.text.lower():
            logger.warning("[Keep-Alive] App has gone to sleep: browser interaction required to wake it up")

        # 2) WebSocket connection: counts as a real visitor session
        ws = websocket.create_connection(ws_url, timeout=timeout)
        ws.close()
        logger.info("[Keep-Alive] WebSocket session opened")

    except Exception as exc:
        logger.warning(f"[Keep-Alive] Streamlit ping failed: {exc}")


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
    lab_db_path = Path(env.waid_db_file)
    if lab_db_path.exists():
        with sqlite3.connect(lab_db_path) as conn:
            cursor = conn.cursor()
            lab_tables = [
                env.db.inference_forecast,
                env.db.inference_stats,
                env.db.inference_quality,
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


def check_and_bridge_gap(env: WaidBoot) -> None:
    """
    @brief Checks for any missing inference gaps by comparing continuous telemetry
           with existing forecasts, ensuring already present valid inferences are untouched.
    @param env WaidBoot configuration instance.
    @return None
    """
    lab_db_path = Path(env.waid_db_file)
    if not lab_db_path.exists():
        return

    try:
        with sqlite3.connect(lab_db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Get all inference timestamps to find continuous blocks
            cursor.execute(f"SELECT timestamp FROM {env.db.inference_forecast} ORDER BY timestamp ASC")
            inf_rows = cursor.fetchall()
            inf_timestamps = {row[0] for row in inf_rows} if inf_rows else set()

            # 2. Get latest telemetry timestamp from stg_ecowitt
            cursor.execute(f"SELECT MAX(timestamp) FROM {env.db.stg_ecowitt}")
            row_tel = cursor.fetchone()
            last_tel_str = row_tel[0] if row_tel and row_tel[0] else None

        if not last_tel_str:
            return

        local_tz = ZoneInfo(env.tz_timezone)
        utc_tz = ZoneInfo("UTC")
        last_tel_dt = datetime.strptime(last_tel_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=utc_tz)

        # Determine the last continuous inference timestamp (ignoring isolated future outliers)
        sorted_inf = sorted([datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=utc_tz) for ts in inf_timestamps])
        
        last_continuous_inf_dt = None
        if sorted_inf:
            last_continuous_inf_dt = sorted_inf[0]
            expected_interval = timedelta(hours=env.scheduled_interval_hours)
            for i in range(1, len(sorted_inf)):
                if sorted_inf[i] - sorted_inf[i-1] <= expected_interval + timedelta(minutes=15):
                    last_continuous_inf_dt = sorted_inf[i]
                else:
                    break
        
        if not last_continuous_inf_dt:
            last_continuous_inf_dt = sorted_inf[0] if sorted_inf else None

        if not last_continuous_inf_dt:
            logger.warning("[AUTO-BRIDGE] No valid inference history found. Skipping gap bridge.")
            return

        # Check gap between the end of the continuous chain and latest telemetry
        gap_delta = last_tel_dt - last_continuous_inf_dt
        threshold_hours = env.scheduled_interval_hours + 1

        if gap_delta > timedelta(hours=threshold_hours):
            logger.warning(
                f"[AUTO-BRIDGE] Continuous gap detected! Last continuous inference: {last_continuous_inf_dt} UTC, "
                f"Latest telemetry: {last_tel_dt} UTC (Delta: {gap_delta}). Bridging missing range..."
            )

            retro_begin_dt = last_continuous_inf_dt + timedelta(hours=env.scheduled_interval_hours)
            retro_end_dt = last_tel_dt.replace(minute=0, second=0, microsecond=0)

            if retro_begin_dt <= retro_end_dt:
                logger.info(f"[AUTO-BRIDGE] Executing catch-up retroactively from {retro_begin_dt} to {retro_end_dt}...")
                
                begin_dt_local = retro_begin_dt.astimezone(local_tz)
                end_dt_local = retro_end_dt.astimezone(local_tz)

                current_dt = begin_dt_local
                while current_dt <= end_dt_local:
                    mock_now_str = current_dt.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Fill only missing hourly slots, leaving existing valid inferences untouched
                    if mock_now_str not in inf_timestamps:
                        os.environ["WAID_RETRO_NOW"] = mock_now_str
                        logger.info(f"=== [AUTO-BRIDGE STEP] Processing missing timestamp: {mock_now_str} ===")
                        extra_passthrough = [
                            "--skip-ingestion-ml-deploy",
                            "--retro-now",
                            mock_now_str,
                        ]
                        code = run_pipeline("incremental", extra_args=extra_passthrough)
                        if code != 0:
                            logger.error(f"Pipeline failed at auto-bridge step {mock_now_str} with exit code {code}")

                    current_dt += timedelta(hours=env.mock_interval_hours)

                os.environ.pop("WAID_RETRO_NOW", None)
                logger.success("[AUTO-BRIDGE] Gap successfully bridged while preserving existing inferences.")
            else:
                logger.info("[AUTO-BRIDGE] Calculated bridge interval is empty or invalid. Skipping.")
        else:
            logger.info("[AUTO-BRIDGE] No significant continuous gap detected between inferences and telemetry.")

    except Exception as exc:
        logger.error(f"[AUTO-BRIDGE] Failed to check or bridge gap: {exc}")
        os.environ.pop("WAID_RETRO_NOW", None)
        
        
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
            "--retro-begin",
            "--begin-period",
            dest="retro_begin",
            type=str,
            help="Start timestamp for retroactive loop (YYYY-MM-DD HH:MM:SS)",
        )
        parser.add_argument(
            "--retro-end",
            "--end-period",
            dest="retro_end",
            type=str,
            help="End timestamp for retroactive loop (YYYY-MM-DD HH:MM:SS)",
        )
        args = parser.parse_args()

        env = WaidBoot()

        # --- RETROACTIVE MODE ---
        if args.retroactive:
            if not args.retro_begin or not args.retro_end:
                logger.error(
                    "Both start (--retro-begin / --begin-period) and end (--retro-end / --end-period) timestamps are required in --retroactive mode."
                )
                return WaidExit.CONFIG_FAIL

            local_tz = ZoneInfo(env.tz_timezone)

            # Preserve native local datetimes for mock clock orchestration
            begin_dt_local = datetime.strptime(
                args.retro_begin, "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=local_tz)
            end_dt_local = datetime.strptime(
                args.retro_end, "%Y-%m-%d %H:%M:%S"
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
                    os.environ["WAID_RETRO_NOW"] = mock_now_str

                    logger.info(
                        f"=== [RETROACTIVE STEP] Processing timestamp: {mock_now_str} ==="
                    )

                    extra_passthrough = [
                        "--skip-ingestion-ml-deploy",
                        "--retro-now",
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
                os.environ.pop("WAID_RETRO_NOW", None)
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

        # Check and bridge any recent downtime gap before starting the live loop
        check_and_bridge_gap(env)
        
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