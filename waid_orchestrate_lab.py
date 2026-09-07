#!/usr/bin/env python3

"""
@file waid_orchestrate_lab.py
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

# Import WaidBoot configuration and utility classes
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import (
    WaidBoot,
    WError,
    WaidExit,
)

from waid_shared import generate_period_range

class PipelineRunner:
    """Handles execution of pipeline shell and dbt commands with logging and formatting."""

    def __init__(self, env: WaidBoot, mock_now: str = None):
        """
        Initializes the PipelineRunner with environment settings and optional mock timestamp.
        
        Args:
            env (WaidBoot): The bootstrap configuration environment instance.
            mock_now (str, optional): Simulated timestamp string for retroactive execution.
        """
        self.env = env
        self.mock_now = mock_now

    def get_dbt_base_args(self) -> list[str]:
        """Builds base dbt arguments including operational bias threshold variables,
        profiles directory, and project directory.

        @return List of dbt command line argument strings.
        """
        dbt_vars_dict = {
            "max_bias_temp": float(self.env.max_bias_temp),
            "max_bias_pres": float(self.env.max_bias_pres),
            "max_bias_rh": float(self.env.max_bias_rh),
            "max_bias_wind": float(self.env.max_bias_wind),
            "max_bias_solar": float(self.env.max_bias_solar),
            "max_bias_rain": float(self.env.max_bias_rain),
        }

        # Insert mock parameter only if it is valid and not 'None'
        if self.mock_now and str(self.mock_now).lower() not in ("none", ""):
            dbt_vars_dict["waid_mock_now"] = str(self.mock_now)

        profiles_dir = str(getattr(self.env, "config_dir", self.env.waid_source_dir / "config"))
        dbt_dir = str(getattr(self.env, "dbt_dir", self.env.waid_source_dir / "dbt"))

        return [
            "--profiles-dir",
            profiles_dir,
            "--project-dir",
            dbt_dir,
            "--target",
            "dev",
            "--vars",
            json.dumps(dbt_vars_dict),
        ]

    def run_command(self, command: list[str], is_dbt: bool = False, period: str = None) -> int:
        """Executes a subprocess command while capturing and standardizing its output logs.

        @param command List representing the command and its arguments.
        @param is_dbt Boolean flag indicating if the command is a dbt operation.
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

        if self.mock_now:
            logger.info(f"[MOCK MODE] Running with WAID_MOCK_NOW={self.mock_now}")

        # Configure environment for child process, propagating WAID_MOCK_NOW if present
        proc_env = os.environ.copy()
        if self.mock_now:
            proc_env["WAID_MOCK_NOW"] = self.mock_now
        else:
            proc_env.pop("WAID_MOCK_NOW", None)

        python_bin = str(sys.executable)
        cmd = list(command)
        if cmd[0] == "python":
            cmd[0] = python_bin
        elif cmd[0] == "dbt":
            cmd[0] = self.env.dbt_bin
    
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=self.env.waid_source_dir if "python" in command[0] else self.env.dbt_dir,
            env=proc_env,
        )

        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

        for line in process.stdout:
            clean_line = line.strip()
            raw_line = ansi_escape.sub('', clean_line)

            # Filter out non-useful CUDA logs
            if "cudart_stub.cc" in raw_line or "Could not find cuda drivers" in raw_line:
                continue

            target_level = "INFO"

            for lvl in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                if lvl in raw_line:
                    target_level = lvl
                    break

            # Clean operational handling using boolean flag
            if is_dbt and target_level in ["ERROR", "CRITICAL"]:
                if "TOTAL=" in raw_line or "PASS=" in raw_line:
                    target_level = "INFO"

            if " | " in raw_line and not raw_line.startswith("|"):
                message = raw_line.split(" | ")[-1].strip()
            else:
                message = raw_line

            if "[PASS" in raw_line:
                logger.success(message)
            elif "cuda_platform" in raw_line:
                logger.info(message)
            elif "[ERROR" in raw_line or "FAIL" in raw_line:
                logger.error(message)
            else:
                logger.log(target_level, message)

        process.wait()

        if process.returncode != 0:
            logger.error(f"Command failed. Code: {process.returncode}")

        return process.returncode


# ==============================================================================
# STEP 00: DBT SETUP (ATOMIC SUB-STEPS)
# ==============================================================================

def waid_00_1_dbt_clean(runner: PipelineRunner) -> int:
    """Cleans the dbt build environment."""
    logger.info("Cleaning dbt environment")
    return runner.run_command(["dbt", "clean"] + runner.get_dbt_base_args(), is_dbt=True)


def waid_00_2_dbt_deps(runner: PipelineRunner) -> int:
    """Installs missing dbt package dependencies."""
    packages_dir = Path("dbt_packages/dbt_utils")
    if packages_dir.exists():
        logger.info("dbt dependencies already present locally. Skipping download.")
        return 0

    logger.info("Installing missing package dependencies")
    return runner.run_command(["dbt", "deps"] + runner.get_dbt_base_args(), is_dbt=True)
    

def waid_00_3_dbt_compile(runner: PipelineRunner) -> int:
    """Compiles the dbt project."""
    logger.info("Compiling dbt project")
    return runner.run_command(["dbt", "compile"] + runner.get_dbt_base_args(), is_dbt=True)


def waid_00_4_dbt_dump_vars(runner: PipelineRunner) -> int:
    """Validates and dumps dbt shared variables."""
    logger.info("DBT check up shared variables")
    return runner.run_command(["dbt", "run-operation", "dump_vars"] + runner.get_dbt_base_args(), is_dbt=True)


# ==============================================================================
# DATA INGESTION & MATCHING STEPS
# ==============================================================================

def waid_mock_update_ecowitt(runner: PipelineRunner, args: list) -> int:
    """Simulates Ecowitt and ERA5 data for testing."""
    logger.info("Simulating Ecowitt and ERA5 data")
    cmd_args = list(args)
    if runner.mock_now and "--mock-now" not in cmd_args:
        cmd_args.extend(["--mock-now", runner.mock_now])

    return runner.run_command(
        ["python", str(runner.env.tools_dir / "utils/waid_mock_update_ecowitt.py"), *cmd_args],
    )


def waid_01_1_ingest_ecowitt(runner: PipelineRunner, args: list) -> int:
    """Ingests raw Ecowitt weather station data."""
    logger.info("Downloading Ecowitt data")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_01_1_ingest_ecowitt.py"), *args],
    )


def waid_01_2_ingest_era5(runner: PipelineRunner, args: list) -> int:
    """Ingests ERA5 reanalysis data files."""
    logger.info("Downloading ERA5 data")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_01_2_ingest_era5.py"), *args],
    )


def waid_01_3_profile_era5(runner: PipelineRunner, args: list) -> int:
    """Profiles ERA5 NetCDF structure and data quality."""
    logger.info("Profiling ERA5 data")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_01_3_profile_era5.py"), *args],
    )


def waid_02_1_sync_ecowitt(runner: PipelineRunner, args: list) -> int:
    """Synchronizes raw Ecowitt telemetry into the SQLite database."""
    logger.info("Synchronizing Ecowitt with SQLite database")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_02_1_sync_ecowitt.py"), *args],
    )
    

def waid_02_2_dbt_staging_ecowitt(runner: PipelineRunner, args: list) -> int:
    """Runs dbt staging model and tests for cleaned Ecowitt telemetry."""
    logger.info("Staging table for cleaned and casted Ecowitt data")
    period_val = args[args.index('--period') + 1] if '--period' in args else None
    
    code = runner.run_command(
        ["dbt", "run", "--select", "stg_ecowitt"] + runner.get_dbt_base_args(),
        is_dbt=True, period=period_val
    )
    if code != runner.env.waid_exit.SUCCESS:
        return code

    return runner.run_command(
        ["dbt", "test", "--select", "stg_ecowitt"] + runner.get_dbt_base_args(),
        is_dbt=True, period=period_val
    )
    

def waid_03_1_match_datasets(runner: PipelineRunner, args: list) -> int:
    """Matches and synchronizes Ecowitt and ERA5 datasets into Feature Store."""
    logger.info("Data matching between ERA5 and Ecowitt")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_03_1_match_datasets.py"), *args],
    )
    

def waid_03_2_dbt_matches(runner: PipelineRunner, args: list) -> int:
    """Runs dbt tests on matched raw data records."""
    logger.info("Bias Calculation (Discrepancy Analysis)")
    period_val = args[args.index('--period') + 1] if '--period' in args else None
    
    code = runner.run_command(
        ["dbt", "run", "--select", "source:external_raw.match_records"] + runner.get_dbt_base_args(),
        is_dbt=True, period=period_val
    )
    if code != runner.env.waid_exit.SUCCESS:
        return code

    return runner.run_command(
        ["dbt", "test", "--select", "source:external_raw.match_records"] + runner.get_dbt_base_args(),
        is_dbt=True, period=period_val
    )
    
    
def waid_03_3_dbt_matches_bias(runner: PipelineRunner, args: list) -> int:
    """Calculates and validates operational bias between Ecowitt and ERA5."""
    logger.info("Bias Calculation (Discrepancy Analysis)")
    period_val = args[args.index('--period') + 1] if '--period' in args else None
    
    code = runner.run_command(
        ["dbt", "run", "--select", "int_matches_bias"] + runner.get_dbt_base_args(),
        is_dbt=True, period=period_val
    )
    if code != runner.env.waid_exit.SUCCESS:
        return code

    return runner.run_command(
        ["dbt", "test", "--select", "int_matches_bias"] + runner.get_dbt_base_args(),
        is_dbt=True, period=period_val
    )


def debug_waid_analyze_bias(runner: PipelineRunner, args: list) -> int:
    """Analyzes and reports performance matching metrics."""
    logger.info("Report matching between Ecowitt and ERA5 data")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "utils/waid_analyze_bias.py"), *args],
    )


def waid_04_1_setup_metadata(runner: PipelineRunner, args: list) -> int:
    """Sets up station metadata via dbt."""
    logger.info("Setting up station metadata")
    code = runner.run_command(
        ["dbt", "run", "--select", "station_metadata", "--full-refresh"] + runner.get_dbt_base_args(),
        is_dbt=True,
    )
    if code != runner.env.waid_exit.SUCCESS:
        return code
    
    logger.info("Setting up sensor specifications")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_04_1_setup_specs.py"), *args],
    )


# ==============================================================================
# MACHINE LEARNING & INFERENCE STEPS
# ==============================================================================

def waid_05_1_ml_tensors(runner: PipelineRunner, args: list) -> int:
    """Generates feature tensors for machine learning."""
    logger.info("Generating ML Tensors")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_05_1_ml_tensors.py"), *args],
    )


def waid_05_2_ml_train(runner: PipelineRunner) -> int:
    """Trains the baseline machine learning model."""
    logger.info("Training ML Model")
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_05_2_ml_train.py")],
    )


def waid_06_1_inference_forecast(runner: PipelineRunner, args: list) -> int:
    """Evaluates 6-hour forecast inference quality."""
    logger.info("Checking 6h forecast inference quality")
    
    cmd = ["python", str(runner.env.tools_dir / "waid_06_1_inference_forecast.py")]
    if runner.mock_now:
        cmd.extend(["--mock-now", runner.mock_now])
        
    return runner.run_command(cmd)


def waid_06_2_inference_stats(runner: PipelineRunner) -> int:
    """Updates inference statistical parameters via dbt."""
    logger.info("Updating inference statistics parameters")
    return runner.run_command(
        ["dbt", "run", "--select", "inference_stats"] + runner.get_dbt_base_args(),
        is_dbt=True,
    )


def waid_06_3_dbt_inference_quality(runner: PipelineRunner) -> int:
    """Updates inference quality metrics downstream of Ecowitt."""
    logger.info("Updating inference quality metrics by Ecowitt")
    return runner.run_command(
        ["dbt", "run", "--select", "+inference_quality", "--full-refresh"] + runner.get_dbt_base_args(),
        is_dbt=True,
    )


def waid_06_4_inference_quality(runner: PipelineRunner, args: list) -> int:
    """Checks inference quality metrics."""
    logger.info("Checking inference quality")
    
    cmd = ["python", str(runner.env.tools_dir / "waid_06_4_inference_quality.py")]
    if runner.mock_now:
        cmd.extend(["--mock-now", runner.mock_now])
        
    return runner.run_command(cmd)


def waid_07_1_export_deploy_db(runner: PipelineRunner, args: list) -> int:
    """Exports public weather data to the public database."""
    logger.info("Exporting public weather data")
    
    cmd = ["python", str(runner.env.tools_dir / "waid_07_1_export_deploy_db.py")]
    if runner.mock_now:
        cmd.extend(["--mock-now", runner.mock_now])
        
    return runner.run_command(cmd)


def waid_08_1_viz_streamlit_app(runner: PipelineRunner, args: list) -> int:
    """Updates and pushes public dashboard analytics data with deployment setup."""
    logger.info("Updating Streamlit dashboard analytics data and staging deployment package")
    
    cmd = [ "python", str(runner.env.tools_dir / "waid_08_1_viz_streamlit_app.py"), "--deploy" ]
    return runner.run_command(cmd)


def waid_08_2_doc_dbt_deploy(runner: PipelineRunner, args: list) -> int:
    """Generate and deploy the automated Markdown data dictionary from dbt data models."""
    logger.info("Generate and deploy the automated Markdown data dictionary from dbt data models.")
    
    cmd = [ "python", str(runner.env.tools_dir / "waid_08_2_doc_dbt_deploy.py") ]
    return runner.run_command(cmd)


# ==============================================================================
# PIPELINE EXECUTION ENGINE & UTILS
# ==============================================================================

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


def parse_and_validate_arguments():
    """
    Parses and validates command-line arguments BEFORE bootstrap and execution.
    
    Returns:
        tuple: Parsed known arguments and extra unknown passthrough arguments.
    """
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
        "--skip-ingestion",
        action="store_true",
        help="Skip data ingestion and profiling steps (01_1, 01_2, 01_3)"
    )
    parser.add_argument(
        "--skip-ingestion-deploy",
        action="store_true",
        help="Skip raw data ingestion and final visualization/deployment steps (01 and 08)"
    )
    parser.add_argument(
        "--mock-now",
        type=str,
        default=None,
        help="Simulated current timestamp for retroactive execution (YYYY-MM-DD HH:MM:SS)"
    )
    parser.add_argument(
        "--only-setup",
        action="store_true",
        help="Run ONLY the initial dbt setup steps (00_1 to 00_4) and exit"
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
        help="Target period YYYY-MM for incremental run mode (defaults to current month if omitted)"
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

    parsed_args, extra_passthrough_args = parser.parse_known_args()

    # --- Catch Typography / Unknown Arguments Early ---
    unrecognized = [arg for arg in extra_passthrough_args if arg.startswith("-")]
    if unrecognized:
        sys.stderr.write(f"Error: Unrecognized option(s) or typo in flags: {', '.join(unrecognized)}\n")
        sys.exit(2)

    # --- Early Validation & Default Enforcement ---
    period_pattern = re.compile(r"^\d{4}-\d{2}$")

    # 1. Fallback for --period (if missing, default to TODAY/Current YYYY-MM)
    if not parsed_args.period and parsed_args.run_mode == "incremental":
        parsed_args.period = datetime.now(timezone.utc).strftime("%Y-%m")

    # 2. Format validation for periods
    if parsed_args.period and not period_pattern.match(parsed_args.period):
        sys.stderr.write(f"Error: Invalid --period format '{parsed_args.period}'. Expected YYYY-MM.\n")
        sys.exit(2)

    if parsed_args.begin_period and not period_pattern.match(parsed_args.begin_period):
        sys.stderr.write(f"Error: Invalid --begin-period format '{parsed_args.begin_period}'. Expected YYYY-MM.\n")
        sys.exit(2)

    if parsed_args.end_period and not period_pattern.match(parsed_args.end_period):
        sys.stderr.write(f"Error: Invalid --end-period format '{parsed_args.end_period}'. Expected YYYY-MM.\n")
        sys.exit(2)

    # 3. Backfill argument completeness check
    if parsed_args.run_mode == "backfill":
        start_p = parsed_args.begin_period or parsed_args.period
        end_p = parsed_args.end_period or parsed_args.period

        if not start_p or not end_p:
            sys.stderr.write("Error: Backfill mode requires --period YYYY-MM (or both --begin-period and --end-period).\n")
            sys.exit(2)

    return parsed_args, extra_passthrough_args


def main() -> int:
    """Main execution entry point for the WAID pipeline orchestrator.

    @return Execution exit code integer.
    """
    # Parse and validate CLI arguments first before running boot sequence
    parsed_args, extra_passthrough_args = parse_and_validate_arguments()

    env = WaidBoot()
    runner = PipelineRunner(env, mock_now=parsed_args.mock_now)
    
    db_path = os.getenv("WAID_DB_MOCK_FILE") if env.waid_sim_mode else os.getenv("WAID_DB_FILE")
    if parsed_args.skip_ingestion_deploy and not Path(db_path).exists():
        logger.warning(f"Cannot skip Data Ingestion / Mock Update. Required path: {db_path}")
        sys.exit(runner.env.waid_exit.INPUT_FAIL)

    if env.waid_sim_mode:
        logger.warning(f"Simulation mode active. Running mock data generation using mock database ({env.waid_db})")
        
    if parsed_args.skip_ingestion_deploy:
        logger.warning("Skipping data ingestion and final viz/deploy steps (--skip-ingestion-deploy flag active)")
    else:
        # ==============================================================================
        # SETUP MODE HANDLING (0: Regime, 1: Soft Reset, 2: Hard Reset / Purge)
        # ==============================================================================
        data_dir = Path(env.waid_data_dir)
        backup_dir = data_dir / "backups"

        logger.info(f"🔶 Regime Mode: {env.setup_mode}")
        if env.setup_mode in [1, 2]:
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

            if env.setup_mode == 2:
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

            elif env.setup_mode == 1:
                logger.info(f"--- SOFT RESET (Mode 1): Preserving raw data, resetting DB & ML artifacts ---")
                backup_name = backup_dir / f"backup_soft_reset_{timestamp_str}"
                
                logger.info(f"Creating lightweight backup at {backup_name} ...")
                curr_backup_sub = Path(backup_name)
                curr_backup_sub.mkdir(exist_ok=True)
                
                for item in data_dir.iterdir():
                    is_db = item.suffix == ".db"
                    is_mock_db = is_db and "mock" in item.name.lower()
                    is_artifact = item.name in ["models", "tensors"]

                    # Define what to backup and clear based on context
                    should_process = False
                    if env.waid_sim_mode:
                        # In simulation mode, we only touch databases explicitly containing "mock"
                        should_process = is_mock_db
                    else:
                        # In real/production mode, we process standard DBs (non-mock) and artifacts
                        should_process = (is_db and not is_mock_db) or is_artifact

                    if should_process:
                        dest = curr_backup_sub / item.name
                        
                        # 1. Backup phase
                        if item.is_dir():
                            shutil.copytree(item, dest, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, dest)

                        # 2. Cleanup phase
                        if item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                        else:
                            item.unlink(missing_ok=True)
                            
                shutil.rmtree(env.dbt_dir / "target", ignore_errors=True)

        if parsed_args.skip_setup:
                logger.warning("Skipping DBT setup steps (--skip-setup flag active)")
                code = runner.env.waid_exit.SUCCESS
        else:
            # 1. Setup Phase Steps (00_1 to 00_4)
            setup_steps = [
                waid_00_1_dbt_clean,
                waid_00_2_dbt_deps,
                waid_00_3_dbt_compile,
                waid_00_4_dbt_dump_vars,
            ]

            code = run_step_sequence(setup_steps, runner, extra_passthrough_args, start_from=parsed_args.start_from)
            if code == runner.env.waid_exit.SUCCESS:
                logger.success("--- Setup successfully completed ---")
            else:
                logger.error(f"--- Setup failed with error (code={code}) ---")

        if parsed_args.only_setup:
            logger.info("--- Executing ONLY DBT Setup steps (--only-setup active) ---")
            return code

    # Data Preparation Steps
    data_prep_steps = []

    if env.waid_sim_mode:           
        data_prep_steps.append(waid_mock_update_ecowitt)
    elif parsed_args.skip_ingestion or parsed_args.skip_ingestion_deploy:
        logger.warning("Skipping raw data ingestion and profiling steps (--skip-ingestion or --skip-ingestion-deploy active)")
    else:
        data_prep_steps.extend([
            waid_01_1_ingest_ecowitt,
            waid_01_2_ingest_era5,
            waid_01_3_profile_era5,
        ])
            
    data_prep_steps.extend([
        waid_02_1_sync_ecowitt,
        waid_02_2_dbt_staging_ecowitt,
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
        waid_06_1_inference_forecast,
        waid_06_2_inference_stats,
        waid_06_3_dbt_inference_quality,
        waid_06_4_inference_quality,
        waid_07_1_export_deploy_db,
    ]
    
    viz_steps = [
        waid_08_1_viz_streamlit_app,
        waid_08_2_doc_dbt_deploy,   
    ]

    # ==============================================================================
    # PIPELINE RUN MODES LOGIC
    # ==============================================================================
    incremental_args = list(extra_passthrough_args)
    if parsed_args.period:
        incremental_args.extend(["--period", parsed_args.period])
        
    if not parsed_args.skip_ingestion_deploy:
        if parsed_args.run_mode == "backfill":
            start_p = parsed_args.begin_period or parsed_args.period
            end_p = parsed_args.end_period or parsed_args.period

            periods = generate_period_range(start_p, end_p)
            logger.debug(f"Starting BACKFILL execution for periods: {periods}")

            for p in periods:
                logger.info(f"--- Processing Data Preparation for period: {p} ---")
                period_args = extra_passthrough_args + ["--period", p]
                code = run_step_sequence(data_prep_steps, runner, period_args, start_from=parsed_args.start_from)
                if code != runner.env.waid_exit.SUCCESS:
                    logger.error(f"Backfill halted due to error in period {p}")
                    return code

            logger.info("Data preparation backfill completed. Starting Global Machine Learning & Inference.")
            ml_args = ["--period", end_p] if end_p else []
            code = run_step_sequence(ml_and_inference_steps, runner, ml_args, start_from=parsed_args.start_from)

        else:  # Incremental Mode
            logger.debug("Starting INCREMENTAL execution")
            full_pipeline = data_prep_steps + ml_and_inference_steps + viz_steps
            code = run_step_sequence(full_pipeline, runner, incremental_args, start_from=parsed_args.start_from)
    else:
        # Skipping data ingestion, preparation (running data prep chain up to 04) and viz steps (08)
        pipeline_skip_deploy = data_prep_steps + ml_and_inference_steps
        code = run_step_sequence(pipeline_skip_deploy, runner, incremental_args, start_from=parsed_args.start_from)

    if code == runner.env.waid_exit.SUCCESS:
        logger.success("--- Pipeline successfully terminated ---")
    else:
        logger.error(f"--- Pipeline terminated with error (code={code}) ---")

    return code


if __name__ == "__main__":
    sys.exit(main())