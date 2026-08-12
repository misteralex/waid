#!/usr/bin/env python3

"""
@file waid_orchestrate.py
@brief WAID Pipeline Orchestrator and Execution Engine.
@details Coordinates the end-to-end execution of the weather AI data pipeline.
         Handles environment setup, dbt integration, step sequencing, backfilling,
         incremental runs, and ML training/inference workflows.
@author AF
@date 2026
"""

import argparse
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger

# Single entry point for configuration and output constants
sys.path.append(str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config"))
from boot import (
    WaidBoot,
    validate_period,
    WError,
)


class PipelineRunner:
    """Handles execution of pipeline shell and dbt commands with logging and formatting."""

    def __init__(self, env: WaidBoot):
        self.env = env

    def get_dbt_base_args(self) -> list[str]:
        """Builds base dbt arguments including operational bias threshold variables.

        @return List of dbt command line arguments.
        """
        dbt_vars_dict = {
            "max_bias_temp": float(self.env.max_bias_temp),
            "max_bias_pres": float(self.env.max_bias_pres),
            "max_bias_rh": float(self.env.max_bias_rh),
            "max_bias_wind": float(self.env.max_bias_wind),
            "max_bias_solar": float(self.env.max_bias_solar),
            "max_bias_rain": float(self.env.max_bias_rain),
        }

        return [
            "--target",
            "dev",
            "--vars",
            json.dumps(dbt_vars_dict),
        ]

    def run_command(self, command: list[str], context: str = "", period: str = None) -> int:
        """Executes a subprocess command while capturing and standardizing its output logs.

        @param command List representing the command and its arguments.
        @param context Execution context label for logging.
        @param period Optional operational period string (YYYY-MM).
        @return Process return code integer.
        """
        caller_name = sys._getframe(1).f_code.co_name
        current_step = [int(x) for x in re.findall(r'\d+', caller_name)[:2]]
        if current_step:
            step_str = f"🔶 Step {current_step}"
            period_val = period
            
            if "--period" in command:
                try:
                    p_index = command.index("--period")
                    if p_index + 1 < len(command):
                        period_val = command[p_index + 1]
                except (ValueError, IndexError):
                    pass

            if period_val:
                step_str += f" - Period: {period_val}"
                
            logger.info(step_str)
            
        logger.info(f"Request from: {caller_name}")
        logger.debug(f"{' '.join(command)}")
        logger.info(f"--- Context: {context} ---")

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=self.env.waid_source_dir if "python" in command[0] else self.env.dbt_dir,
        )

        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

        for line in process.stdout:
            clean_line = line.strip()
            raw_line = ansi_escape.sub('', clean_line)
            target_level = "INFO"

            for lvl in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                if lvl in raw_line:
                    target_level = lvl
                    break

            if "dbt" in context.lower() and target_level in ["ERROR", "CRITICAL"]:
                if "TOTAL=" in raw_line or "PASS=" in raw_line:
                    target_level = "INFO"

            if " | " in raw_line and not raw_line.startswith("|"):
                message = raw_line.split(" | ")[-1].strip()
            else:
                message = raw_line

            if "[PASS" in raw_line:
                logger.success(f"[{context}] {message}")
            elif "cuda_platform" in raw_line:
                logger.info(f"[{context}] {message}")
            elif "[ERROR" in raw_line or "FAIL" in raw_line:
                logger.error(f"[{context}] {message}")
            else:
                logger.log(target_level, f"[{context}] {message}")

        process.wait()

        if process.returncode != 0:
            logger.error(f"Command failed on {context}. Code: {process.returncode}")

        return process.returncode


# ==============================================================================
# STEP 00: DBT SETUP (ATOMIC SUB-STEPS)
# ==============================================================================

def waid_00_1_dbt_clean(runner: PipelineRunner) -> int:
    """Cleans the dbt build environment."""
    logger.info("Cleaning dbt environment")
    return runner.run_command(["dbt", "clean"] + runner.get_dbt_base_args(), context="dbt-run")


def waid_00_2_dbt_deps(runner: PipelineRunner) -> int:
    """Installs missing dbt package dependencies."""
    logger.info("Installing missing package dependencies")
    return runner.run_command(["dbt", "deps"] + runner.get_dbt_base_args(), context="dbt-run")


def waid_00_3_dbt_compile(runner: PipelineRunner) -> int:
    """Compiles the dbt project."""
    logger.info("Compiling dbt project")
    return runner.run_command(["dbt", "compile"] + runner.get_dbt_base_args(), context="dbt-run")


def waid_00_4_dbt_dump_vars(runner: PipelineRunner) -> int:
    """Validates and dumps dbt shared variables."""
    logger.info("DBT check up shared variables")
    return runner.run_command(["dbt", "run-operation", "dump_vars"] + runner.get_dbt_base_args(), context="dbt-run")


# ==============================================================================
# DATA INGESTION & MATCHING STEPS
# ==============================================================================

def waid_mock_update_ecowitt(runner: PipelineRunner, args: list) -> int:
    """Simulates Ecowitt and ERA5 data for testing."""
    logger.info("Simulating Ecowitt and ERA5 data")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "utils/waid_mock_update_ecowitt.py"), *args],
        context="Download",
    )


def waid_01_1_ingest_ecowitt(runner: PipelineRunner, args: list) -> int:
    """Ingests raw Ecowitt weather station data."""
    logger.info("Downloading Ecowitt data")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_01_1_ingest_ecowitt.py"), *args],
        context="Download",
    )


def waid_01_2_ingest_era5(runner: PipelineRunner, args: list) -> int:
    """Ingests ERA5 reanalysis data files."""
    logger.info("Downloading ERA5 data")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_01_2_ingest_era5.py"), *args],
        context="Download",
    )


def waid_02_1_sync_ecowitt(runner: PipelineRunner, args: list) -> int:
    """Synchronizes raw Ecowitt telemetry into the SQLite database."""
    logger.info("Synchronizing Ecowitt with SQLite database")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_02_1_sync_ecowitt.py"), *args],
        context="Ingestion",
    )
    

def waid_02_2_profile_era5(runner: PipelineRunner, args: list) -> int:
    """Profiles ERA5 NetCDF structure and data quality."""
    logger.info("Profiling ERA5 data")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_02_2_profile_era5.py"), *args],
        context="Profiling",
    )


def waid_02_3_dbt_clean_ecowitt(runner: PipelineRunner, args: list) -> int:
    """Runs dbt staging model and tests for cleaned Ecowitt telemetry."""
    logger.info("Staging table for cleaned and casted Ecowitt data")
    logger.debug(f"Extra arguments: {args}")
    code = runner.run_command(
        ["dbt", "run", "--select", "stg_ecowitt"] + runner.get_dbt_base_args(),
        context="dbt-run", period=args[args.index('--period') + 1]
    )
    if code != runner.env.waid_exit.SUCCESS:
        return code

    return runner.run_command(
        ["dbt", "test", "--select", "stg_ecowitt", "--store-failures"] + runner.get_dbt_base_args(),
        context="dbt-test", period=args[args.index('--period') + 1]
    )
    

def waid_03_1_match_datasets(runner: PipelineRunner, args: list) -> int:
    """Matches and synchronizes Ecowitt and ERA5 datasets into Feature Store."""
    logger.info("Data matching between ERA5 and Ecowitt")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_03_1_match_datasets.py"), *args],
        context="Matching",
    )
    

def waid_03_2_dbt_matches(runner: PipelineRunner, args: list) -> int:
    """Runs dbt tests on matched raw data records."""
    logger.info("Bias Calculation (Discrepancy Analysis)")
    code = runner.run_command(
        ["dbt", "run", "--select", "source:external_raw.match_records"] + runner.get_dbt_base_args(),
        context="dbt-run", period=args[args.index('--period') + 1]
    )
    if code != runner.env.waid_exit.SUCCESS:
        return code

    return runner.run_command(
        ["dbt", "test", "--select", "source:external_raw.match_records"] + runner.get_dbt_base_args(),
        context="dbt-test",
    )
    
    
def waid_03_3_dbt_matches_bias(runner: PipelineRunner, args: list) -> int:
    """Calculates and validates operational bias between Ecowitt and ERA5."""
    logger.info("Bias Calculation (Discrepancy Analysis)")
    code = runner.run_command(
        ["dbt", "run", "--select", "int_matches_bias"] + runner.get_dbt_base_args(),
        context="dbt-run", period=args[args.index('--period') + 1]
    )
    if code != runner.env.waid_exit.SUCCESS:
        return code

    return runner.run_command(
        ["dbt", "test", "--select", "int_matches_bias"] + runner.get_dbt_base_args(),
        context="dbt-test", period=args[args.index('--period') + 1]
    )


def debug_waid_analyze_bias(runner: PipelineRunner, args: list) -> int:
    """Analyzes and reports performance matching metrics."""
    logger.info("Report matching between Ecowitt and ERA5 data")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "utils/waid_analyze_bias.py"), *args],
        context="Profiling",
    )


def waid_04_1_setup_metadata(runner: PipelineRunner, args: list) -> int:
    """Sets up station metadata via dbt."""
    logger.info("Setting up station metadata")
    code = runner.run_command(
        ["dbt", "run", "--select", "station_metadata", "--full-refresh"] + runner.get_dbt_base_args(),
        context="dbt-run",
    )
    if code != runner.env.waid_exit.SUCCESS:
        return code
    
    logger.info("Setting up sensor specifications")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_04_1_setup_specs.py"), *args],
        context="Profiling",
    )


# ==============================================================================
# MACHINE LEARNING & INFERENCE STEPS
# ==============================================================================

def waid_05_1_ml_tensors(runner: PipelineRunner, args: list) -> int:
    """Generates feature tensors for machine learning."""
    logger.info("Generating ML Tensors")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_05_1_ml_tensors.py"), *args],
        context="Profiling",
    )


def waid_05_2_ml_train(runner: PipelineRunner) -> int:
    """Trains the baseline machine learning model."""
    logger.info("Training ML Model")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_05_2_ml_train.py")],
        context="Profiling",
    )


def waid_06_1_inference_engine(runner: PipelineRunner) -> int:
    """Executes the ML inference engine."""
    logger.info("Executing inference")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_06_1_inference_engine.py")],
        context="Profiling",
    )


def waid_06_2_inference_stats(runner: PipelineRunner) -> int:
    """Updates inference statistical parameters via dbt."""
    logger.info("Updating inference statistics parameters")
    return runner.run_command(
        ["dbt", "run", "--select", "inference_stats"] + runner.get_dbt_base_args(),
        context="dbt-run",
    )


def waid_06_3_inference_prediction(runner: PipelineRunner) -> int:
    """Generates full-refresh inference prediction models."""
    logger.info("Performing inference prediction")
    return runner.run_command(
        ["dbt", "run", "--select", "inference_prediction", "--full-refresh"] + runner.get_dbt_base_args(),
        context="dbt-run",
    )


def waid_06_4_dbt_inference_quality(runner: PipelineRunner) -> int:
    """Updates inference quality metrics downstream of Ecowitt."""
    logger.info("Updating inference quality metrics by Ecowitt")
    return runner.run_command(
        ["dbt", "run", "--select", "+inference_quality"] + runner.get_dbt_base_args(),
        context="dbt-run",
    )


def waid_06_5_inference_quality(runner: PipelineRunner) -> int:
    """Checks inference quality metrics."""
    logger.info("Checking inference quality")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_06_5_inference_quality.py")],
        context="Profiling",
    )


def waid_07_1_inference_forecast(runner: PipelineRunner) -> int:
    """Evaluates 6-hour forecast inference quality."""
    logger.info("Checking 6h forecast inference quality")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_07_1_inference_forecast.py")],
        context="Profiling",
    )



def waid_07_2_export_public_db(runner: PipelineRunner) -> int:
    """Exports public weather data to the public database."""
    logger.info("Exporting public weather data")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_07_2_export_public_db.py")],
        context="Profiling",
    )
    

# ==============================================================================
# PIPELINE EXECUTION ENGINE & UTILS
# ==============================================================================

def generate_period_range(begin_period: str, end_period: str) -> list[str]:
    """Generates a list of YYYY-MM periods from start to end inclusive.

    @param begin_period Start month string (YYYY-MM).
    @param end_period End month string (YYYY-MM).
    @return List of period strings.
    """
    start_date = datetime.strptime(begin_period, "%Y-%m")
    end_date = datetime.strptime(end_period, "%Y-%m")
    
    periods = []
    curr = start_date
    while curr <= end_date:
        periods.append(curr.strftime("%Y-%m"))
        if curr.month == 12:
            curr = datetime(curr.year + 1, 1, 1)
        else:
            curr = datetime(curr.year, curr.month + 1, 1)
    return periods


def run_step_sequence(steps: list, runner: PipelineRunner, extra_args: list[str], start_from: str = None) -> int:
    """Executes a sequence of step functions with optional fast-forwarding.

    @param steps List of step callables.
    @param runner PipelineRunner instance.
    @param extra_args Additional command line arguments to pass.
    @param start_from Optional step function name to fast-forward execution.
    @return Execution status return code integer.
    """
    if start_from:
        step_names = [s.__name__ for s in steps]
        if start_from in step_names:
            start_idx = step_names.index(start_from)
            logger.info(f"Fast-forwarding sequence to step: {start_from}")
            steps = steps[start_idx:]
        else:
            logger.warning(f"Target step '{start_from}' not found in current sequence. Executing all.")

    code = runner.env.waid_exit.SUCCESS
    for step_func in steps:
        # check if the step is a debug step and skip if debug mode is not enabled
        if step_func.__name__.split("_", 1)[0] == "debug":
            if runner.env.debug_mode:
                logger.debug(f"Executing debug step: {step_func.__name__}")
            else:
                logger.info(f"Skipping debug step: {step_func.__name__}")
                continue     

        sig = inspect.signature(step_func)
        if len(sig.parameters) > 1:
            code = step_func(runner, extra_args)
        else:
            logger.debug(f"NO extra arguments passed to step '{step_func.__name__}' (expects only runner)")
            code = step_func(runner)
            
        if code != runner.env.waid_exit.SUCCESS:
            logger.error(f"Step '{step_func.__name__}' failed with return code: {code}")
            break

    return code


def parse_arguments():
    """Parses command-line arguments for the pipeline orchestrator."""
    parser = argparse.ArgumentParser(description="WAID Pipeline Orchestrator")
    
    parser.add_argument(
        "--run-mode",
        choices=["incremental", "backfill"],
        default="incremental",
        help="Execution mode: 'incremental' (single period) or 'backfill' (multi-period historical prep + ML)"
    )
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip initial dbt setup steps (00_1 to 00_4)"
    )
    parser.add_argument(
        "--start-from",
        type=str,
        default=None,
        help="Start execution directly from a specific step name (e.g., waid_03_1_match_datasets)"
    )
    parser.add_argument(
        "--period",
        type=str,
        default=None,
        help="Target period YYYY-MM for incremental run mode"
    )
    parser.add_argument(
        "--begin-period",
        type=str,
        default=None,
        help="Start period YYYY-MM for backfill mode"
    )
    parser.add_argument(
        "--end-period",
        type=str,
        default=None,
        help="End period YYYY-MM for backfill mode"
    )

    return parser.parse_known_args()


def main() -> int:
    """Main execution entry point for the WAID pipeline orchestrator.

    @return Execution exit code integer.
    """
    parsed_args, extra_passthrough_args = parse_arguments()

    env = WaidBoot()
    runner = PipelineRunner(env)

    # ==============================================================================
    # SETUP MODE HANDLING (0: Regime, 1: Soft Reset, 2: Hard Reset / Purge)
    # ==============================================================================
    setup_mode = int(os.getenv("WAID_SETUP_MODE", "0"))
    data_dir = Path(env.waid_data_dir)
    backup_dir = data_dir / "backups"

    if setup_mode in [1, 2]:
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        if setup_mode == 2:
            logger.warning(f"--- HARD RESET (Mode 2): Purging ALL data in {data_dir} ---")
            backup_name = backup_dir / f"backup_hard_reset_{timestamp_str}"
            
            logger.info(f"Creating full backup archive at {backup_name}.zip ...")
            shutil.make_archive(str(backup_name), 'zip', data_dir, root_dir=data_dir)
            
            for item in data_dir.iterdir():
                if item.name == "backups":
                    continue
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink(missing_ok=True)
                    
            shutil.rmtree(env.dbt_dir / "target", ignore_errors=True)

        elif setup_mode == 1:
            logger.info(f"--- SOFT RESET (Mode 1): Preserving raw data, resetting DB & ML artifacts ---")
            backup_name = backup_dir / f"backup_soft_reset_{timestamp_str}"
            
            logger.info(f"Creating lightweight backup at {backup_name} ...")
            curr_backup_sub = Path(backup_name)
            curr_backup_sub.mkdir(exist_ok=True)
            
            for item in data_dir.iterdir():
                if item.suffix == ".db" or item.name in ["models", "tensors"]:
                    dest = curr_backup_sub / item.name
                    if item.is_dir():
                        shutil.copytree(item, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, dest)

            for item in data_dir.iterdir():
                if item.suffix == ".db" or item.name in ["models", "tensors"]:
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        item.unlink(missing_ok=True)
                        
            shutil.rmtree(env.dbt_dir / "target", ignore_errors=True)

    else:
        logger.info("--- REGIME MODE (Mode 0): Incremental execution ---")

    # 1. Setup Phase Steps (00)
    setup_steps = [
        waid_00_1_dbt_clean,
        waid_00_2_dbt_deps,
        waid_00_3_dbt_compile,
        waid_00_4_dbt_dump_vars,
    ]

    if not parsed_args.skip_setup:
        code = run_step_sequence(setup_steps, runner, extra_passthrough_args, start_from=parsed_args.start_from)
        if code != runner.env.waid_exit.SUCCESS:
            return code
    else:
        logger.info("⏩ Skipping DBT Setup steps (--skip-setup flag active)")

    # 2. Data Preparation Steps (01 to 05_1)
    data_prep_steps = []
    if runner.env.waid_sim_mode:
        logger.info("Simulation mode active. Using mock data generation.")
        data_prep_steps.append(waid_mock_update_ecowitt)
    else:
        data_prep_steps.extend([
            waid_01_1_ingest_ecowitt,
            waid_01_2_ingest_era5,
        ])

    data_prep_steps.extend([
        waid_02_1_sync_ecowitt,
        waid_02_2_profile_era5,
        waid_02_3_dbt_clean_ecowitt,
        waid_03_1_match_datasets,
        waid_03_2_dbt_matches,
        waid_03_3_dbt_matches_bias,
        debug_waid_analyze_bias,
        waid_04_1_setup_metadata,
    ])

    # 3. Machine Learning & Inference Steps (05_2 to 07_1)
    ml_and_inference_steps = [
        waid_05_1_ml_tensors,
        waid_05_2_ml_train,
        waid_06_1_inference_engine,
        waid_06_2_inference_stats,
        waid_06_3_inference_prediction,
        waid_06_4_dbt_inference_quality,
        waid_06_5_inference_quality,
        waid_07_1_inference_forecast,
        waid_07_2_export_public_db,
    ]

    # ==============================================================================
    # PIPELINE RUN MODES LOGIC
    # ==============================================================================

    if parsed_args.run_mode == "backfill":
        start_p = parsed_args.begin_period or parsed_args.period
        end_p = parsed_args.end_period or parsed_args.period

        if not start_p or not end_p:
            logger.error("Backfill mode requires --period YYYY-MM (or both --begin-period and --end-period)")
            return runner.env.waid_exit.INPUT_FAIL

        periods = generate_period_range(start_p, end_p)
        logger.info(f"Starting BACKFILL execution for periods: {periods}")

        for p in periods:
            logger.info(f"--- Processing Data Preparation for period: {p} ---")
            period_args = extra_passthrough_args + ["--period", p]
            code = run_step_sequence(data_prep_steps, runner, period_args, start_from=parsed_args.start_from)
            if code != runner.env.waid_exit.SUCCESS:
                logger.error(f"Backfill halted due to error in period {p}")
                return code

        logger.info("Data preparation backfill completed. Starting Global Machine Learning & Inference.")
        code = run_step_sequence(ml_and_inference_steps, runner, extra_passthrough_args, start_from=parsed_args.start_from)

    else:  # Incremental Mode
        logger.info("Starting INCREMENTAL execution")
        incremental_args = list(extra_passthrough_args)
        if parsed_args.period:
            incremental_args.extend(["--period", parsed_args.period])

        full_pipeline = data_prep_steps + ml_and_inference_steps
        code = run_step_sequence(full_pipeline, runner, incremental_args, start_from=parsed_args.start_from)

    if code == runner.env.waid_exit.SUCCESS:
        logger.success("--- Pipeline successfully terminated ---")
    else:
        logger.error(f"--- Pipeline terminated with error (code={code}) ---")

    return code


if __name__ == "__main__":
    sys.exit(main())