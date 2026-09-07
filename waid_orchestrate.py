#!/usr/bin/env python3

"""
@file waid_orchestrate.py
@brief Standalone Prefect-based Orchestrator for WAID Pipeline.
@details Coordinates data ingestion, dbt transformations, machine learning, inference, and visualization workflows.
@author AF
@date 2026
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, Union, List
from loguru import logger
from datetime import datetime
import subprocess
import httpx
import httpcore
from prefect.exceptions import PrefectHTTPStatusError
from prefect import flow, task, get_run_logger
from prefect.context import TaskRunContext
from prefect.client.orchestration import get_client
from prefect.settings import PREFECT_API_URL, temporary_settings

# Import Boot Configuration
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import (
    WaidBoot,
    validate_period,
    WaidExit,
)

from waid_shared import generate_period_range

# ==============================================================================
# PREFECT TASKS (PYTHON & DBT EXECUTORS)
# ==============================================================================

@task(name="Python Step Task")
def run_python_step(
    script_name: str, 
    env_config: WaidBoot, 
    extra_args: Optional[Union[List[str], str]] = None,
) -> int:
    """
    @brief Executes an external Python script step as a Prefect task.
    @param script_name Name of the Python script to execute.
    @param env_config Environment configuration object (WaidBoot).
    @param extra_args Optional command line arguments to pass to the script.
    @return Exit status code of the subprocess execution.
    """
    ctx = TaskRunContext.get()
    if ctx:
        ctx.task_run.name = script_name
    logger = get_run_logger()
    logger.info(f"🔶 Step: {script_name}")
    
    if env_config and hasattr(env_config, "tools_dir") and env_config.tools_dir:
        working_dir = Path(env_config.tools_dir)
    else:
        working_dir = Path(env_config.waid_source_dir)
        
    script_path = working_dir / script_name

    if not script_path.exists():
        raise FileNotFoundError(f"Unable to locate Python script: {script_path}")

    cmd = [sys.executable, str(script_path)]
    
    if extra_args:
        if isinstance(extra_args, list):
            cmd.extend([str(a) for a in extra_args])
        else:
            cmd.append(str(extra_args))

    env_vars = None
    if env_config and hasattr(env_config, "env_dict"):
        env_vars = os.environ.copy()
        env_vars.update(env_config.env_dict)
            
    logger.info(f"Executing Python script in {working_dir}: {' '.join(cmd)}")
    
    # Execute without check=True to capture exit code without automatic exceptions
    result = subprocess.run(
        cmd,
        cwd=working_dir,
        env=env_vars,
        check=False,
        text=True
    )

    # Managed errors from pipeline. Expected exit code (e.g., Code 3 = DATA_FAIL / No data)
    """
    if result.returncode == 3:
        logger.error(f"The script {script_name} terminated with controlled status 3 (Data availability issue).")
        return result.returncode

    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, output=result.stdout, stderr=result.stderr)

    return result
    """
    
    if result.returncode != 0:
        logger.error(f"The script {script_name} terminated with error exit code: {result.returncode}")

    return result.returncode  


@task(
    name="dbt Step",
    task_run_name="dbt {command} {select}"
)
def run_dbt_step(
    command: str, 
    select: str = "",
    env_config: WaidBoot = None,
    full_refresh: bool = False,
    **kwargs
) -> int:
    """
    @brief Executes a dbt CLI command as a Prefect task.
    @param command dbt command to run (e.g., run, test, deps, compile).
    @param select Model selector string for dbt.
    @param env_config Environment configuration object (WaidBoot).
    @param full_refresh Whether to append --full-refresh flag to dbt.
    @return Exit status code of the dbt subprocess.
    """
    select_str = select if select else ""
    logger = get_run_logger()  
    logger.info(f"🔶 Step: dbt {command} {select_str}".strip())

    # dbt_project_dir = getattr(env_config, "dbt_dir", env_config.waid_source_dir / "dbt")
    # dbt_profiles_dir = getattr(env_config, "config_dir", env_config.waid_source_dir / "config")
    
    cmd = [
        str(env_config.dbt_bin), 
        command, 
        "--project-dir", str(env_config.dbt_dir),
        "--profiles-dir", str(env_config.dbt_profiles_dir)
    ]
    
    if full_refresh:
        cmd.append("--full-refresh")
    
    if command == "run-operation":
        if select and select.strip():
            cmd.append(select)
    else:
        if select and select.strip():
            cmd.extend(["--select", select])
        
    env_vars = os.environ.copy()
    if env_config and hasattr(env_config, "env_dict"):
        env_vars.update(env_config.env_dict)

    result = subprocess.run(
        cmd, 
        cwd=str(env_config.dbt_dir), 
        env=env_vars,
        check=False, 
        text=True
    )

    if result.returncode != 0:
        logger.error(f"The dbt command {command} {select_str} terminated with error status: {result.returncode}")

    return result.returncode


# ==============================================================================
# SUB-FLOWS (PREPARATION, ML, DEPLOYMENT)
# ==============================================================================

@flow(name="Data Ingestion Flow")
def data_ingestion_flow(
    env: WaidBoot, 
    period_args: List[str],
) -> int:
    """
    @brief Encapsulates raw data ingestion, sync, and profiling steps.
    @param env WaidBoot configuration instance.
    @param period_args List containing period arguments for scripts.
    @return Sub-flow execution exit code (0 if successful).
    """
    exit_code = run_python_step("waid_01_1_ingest_ecowitt.py", env, extra_args=period_args)
    if exit_code == 0:
        exit_code = run_python_step("waid_01_2_ingest_era5.py", env, extra_args=period_args)
    
    if exit_code == 0:
        exit_code = run_python_step("waid_01_3_profile_era5.py", env, extra_args=period_args)

    if exit_code == 0:
        exit_code = run_python_step("waid_02_1_sync_ecowitt.py", env, extra_args=period_args)

    return exit_code


@flow(name="Data Preparation Flow")
def data_preparation_flow(
    env: WaidBoot, 
    period_args: List[str],
) -> int:
    """
    @brief Encapsulates dbt compilation, model staging, dataset matching, and feature specs setup.
    @param env WaidBoot configuration instance.
    @param period_args List containing period arguments for scripts.
    @return Sub-flow execution exit code (0 if successful).
    """
    # 1. dbt Setup Steps
    exit_code = run_dbt_step("clean", "", env)
    
    if exit_code == 0:
        exit_code = run_dbt_step("deps", "", env)
        
    if exit_code == 0:   
        exit_code = run_dbt_step("compile", "", env)
    
    if exit_code == 0:
        exit_code = run_dbt_step("run-operation", "dump_vars", env)
        
    # 2. dbt Staging & Tests
    exit_code = run_dbt_step("run", "stg_ecowitt", env)
        
    if exit_code == 0:
        exit_code = run_dbt_step("test", "stg_ecowitt", env)

    if exit_code == 0:
        exit_code = run_python_step("waid_03_1_match_datasets.py", env, extra_args=period_args)
    
    if exit_code == 0:
        exit_code = run_dbt_step("run", "source:external_raw.match_records", env)
        
    if exit_code == 0:
        exit_code = run_dbt_step("test", "source:external_raw.match_records", env)

    if exit_code == 0:
        exit_code = run_dbt_step("run", "int_matches_bias", env)
        
    if exit_code == 0:   
        exit_code = run_dbt_step("test", "int_matches_bias", env)

    if exit_code == 0:
        exit_code = run_dbt_step("run", "station_metadata", env, full_refresh=True)
        
    if exit_code == 0:
        exit_code = run_python_step("waid_04_1_setup_specs.py", env, extra_args=period_args)

    return exit_code


@flow(name="ML and Inference Flow")
def ml_and_inference_flow(
    env: WaidBoot, 
    period_args: List[str],
) -> int:
    """
    @brief Encapsulates model training, inference execution, and quality check workflows.
    @param env WaidBoot configuration instance.
    @param period_args List containing period arguments for scripts.
    @return Sub-flow execution exit code (0 if successful).
    """
    exit_code = run_python_step("waid_05_1_ml_tensors.py", env, extra_args=period_args)
    
    if exit_code == 0:
        exit_code = run_python_step("waid_05_2_ml_train.py", env)

    if exit_code == 0:
        exit_code = run_python_step("waid_06_1_inference_forecast.py", env)
    
    if exit_code == 0:
        exit_code = run_dbt_step("run", "inference_stats", env)
    
    # Inference Quality (Isolated Full Refresh)
    if exit_code == 0:
        exit_code = run_dbt_step("run", "+inference_quality", env, full_refresh=True)
    
    if exit_code == 0:
        exit_code = run_python_step("waid_06_4_inference_quality.py", env)

    if exit_code == 0:
        exit_code = run_python_step("waid_07_1_export_deploy_db.py", env)

    return exit_code


@flow(name="Visualization and Docs Flow")
def viz_and_docs_flow(env: WaidBoot):
    """
    @brief Encapsulates Streamlit deployment and dbt documentation export.
    @param env WaidBoot configuration instance.
    """  
    exit_code = run_python_step("waid_08_1_viz_streamlit_app.py", env, extra_args=["--deploy"])
    
    if exit_code == 0:
        run_python_step("waid_08_2_doc_dbt_deploy.py", env)


# ==============================================================================
# MAIN PREFECT PIPELINE FLOW
# ==============================================================================
@flow(name="WAID Main Orchestrator Flow")
def waid_main_flow(
    period: Optional[str] = None, 
    skip_ingestion: bool = False,
    auto_backfill: bool = False
) -> int:
    """
    @brief Main entry point flow orchestrating the complete WAID processing pipeline.
    @param period Target month string in YYYY-MM format.
    @param skip_ingestion Flag to bypass ingestion and preparation sub-flows.
    @param auto_backfill Flag to execute historical backfill across configured month ranges.
    @return Overall execution status code (0 for success, WaidExit status on failure).
    """
    try:    
        env = WaidBoot()
        current_month = datetime.now().strftime("%Y-%m")
        
        # Safely parse CLI arguments without interfering with Prefect kwargs
        parsed_period = None
        parsed_skip = False
        parsed_backfill = False

        if len(sys.argv) > 1 and not os.getenv("PREFECT__FLOW_RUN_ID"):
            parser = argparse.ArgumentParser(description="WAID Standalone Prefect Orchestrator")
            parser.add_argument("--period", type=str, help="Target month in YYYY-MM format")
            parser.add_argument("--skip-ingestion", action="store_true")
            parser.add_argument("--auto-backfill", action="store_true")
            args, _ = parser.parse_known_args()
            parsed_period = getattr(args, "period", None)
            parsed_skip = getattr(args, "skip_ingestion", False)
            parsed_backfill = getattr(args, "auto_backfill", False)

        is_auto_backfill = auto_backfill or parsed_backfill
        should_skip_ingestion = skip_ingestion or parsed_skip

        db_path = os.getenv("WAID_DB_FILE")
        if should_skip_ingestion and (not db_path or not Path(db_path).exists()):
            logger.warning(f"Cannot skip Data Ingestion / Data Update. Required path: {db_path}")
            return WaidExit.INTERNAL_ERROR

        # ======================================================================
        # BRANCH 1: AUTO-BACKFILL (Ingestion and Data Preparation only / Steps 01-03)
        # ======================================================================
        if is_auto_backfill:
            start_period = (
                getattr(env, "backfill_begin_period_str", None)
                or os.getenv("SCHEDULER_BACKFILL_BEGIN_PERIOD", "2025-11")
            )
            end_period = (
                getattr(env, "backfill_end_period_str", None)
                or os.getenv("SCHEDULER_BACKFILL_END_PERIOD", current_month)
            )
            
            logger.info(f"🚀 Starting historical AUTO-BACKFILL from {start_period} to {end_period} (Steps 01-03)...")
            periods = generate_period_range(start_period, end_period)
            
            for p in periods:
                period_args = ["--period", p]
                logger.info(f"--- [BACKFILL] Processing period: {p} ---")
                
                if not should_skip_ingestion:
                    exit_code = data_ingestion_flow(env, period_args)
                    if exit_code != 0:
                        logger.error(f"Error during data ingestion for period {p}")
                        return exit_code
                        
                exit_code = data_preparation_flow(env, period_args)
                if exit_code != 0:
                    logger.error(f"Error during data preparation for period {p}")
                    return exit_code

            logger.info("✅ BACKFILL completed successfully. Database populated.")
            return 0

        # ======================================================================
        # BRANCH 2: STANDARD EXECUTION (Steps 01-06)
        # ======================================================================
        period_val = period or parsed_period or current_month
        period_args = ["--period", period_val]
        exit_code = 0

        logger.info(f"🚀 Starting standard execution for period: {period_val}")

        if not should_skip_ingestion:
            exit_code = data_ingestion_flow(env, period_args)
            if exit_code == 0:
                exit_code = data_preparation_flow(env, period_args)
        else:
            logger.warning("🔶 Skipping data ingestion and preparation flow (--skip-ingestion flag active)")

        if exit_code == 0:
            exit_code = ml_and_inference_flow(env, period_args)

        if exit_code == 0:
            exit_code = viz_and_docs_flow(env)

    except Exception:
        logger.exception("Pipeline failed unexpectedly")
        return WaidExit.INTERNAL_ERROR
        
    return exit_code


if __name__ == "__main__":
    # Temporarily disable HTTP endpoint for this execution.
    # Prefect will write directly to the local SQLite DB (~/.prefect/prefect.db).
    with temporary_settings({PREFECT_API_URL: None}):
        try:
            # 1. Run main flow capturing exit code without immediate termination
            exit_code = waid_main_flow()
            
            # 2. Handle controlled pipeline errors
            if exit_code != 0:
                logger.error(f"Pipeline terminated with abnormal exit code: {exit_code}")
                
            # 3. Clean exit returning actual pipeline exit code
            sys.exit(exit_code)

        except Exception:
            logger.exception("❌ Critical unhandled error during Prefect orchestrator execution.")
            sys.exit(WaidExit.INTERNAL_ERROR)