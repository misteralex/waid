#!/usr/bin/env python3

"""
@file waid_orchestrate_lab.py
@brief WAID Pipeline Orchestrator and Execution Engine (Lab Version).
@details Coordinates the end-to-end execution of the weather AI data pipeline.
         Automatically inspects DB state in public_forecasts to dynamically 
         toggle ML inference vs telemetry-only sync.
@author AF
@date 2026
"""

import argparse
import inspect
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger

if not os.environ.get("WAID_SOURCE"):
    sys.exit("[CRITICAL] WAID_SOURCE environment variable is missing. Export it first.")

sys.path.append(str(Path(os.environ.get("WAID_SOURCE")) / "config"))
from boot import (
    WaidBoot,
    WError,
    WaidExit,
    validate_period,
)

sys.path.append(str(Path(os.environ.get("WAID_SOURCE")) / "src"))
from waid_shared import (
    generate_period_range,
    get_last_inference_datetime,
)


class PipelineRunner:
    """
    @brief Handles execution of pipeline shell and dbt commands with logging and formatting.
    """

    def __init__(self, env: WaidBoot, mock_now: str = None):
        """
        @brief Initializes the PipelineRunner with environment settings and optional mock timestamp.
        @param env The bootstrap configuration environment instance (WaidBoot).
        @param mock_now Simulated timestamp string for retroactive execution (YYYY-MM-DD HH:MM:SS).
        """
        self.env = env
        self.mock_now = mock_now

    def get_dbt_base_args(self) -> list[str]:
        """
        @brief Builds base dbt arguments including operational bias threshold variables,
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

        if self.mock_now and str(self.mock_now).lower() not in ("none", ""):
            dbt_vars_dict["waid_mock_now"] = str(self.mock_now)

        profiles_dir = str(
            getattr(
                self.env, "config_dir", self.env.waid_source_dir / "config"
            )
        )
        dbt_dir = str(
            getattr(self.env, "dbt_dir", self.env.waid_source_dir / "dbt")
        )

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

    def run_command(
        self, command: list[str], is_dbt: bool = False, period: str = None
    ) -> int:
        """
        @brief Executes a subprocess command while streaming its raw output directly to stdout.
        @param command List representing the command and its arguments.
        @param is_dbt Boolean flag indicating if the command is a dbt operation.
        @param period Optional operational period string (YYYY-MM).
        @return Process return code integer (0 on success).
        """
        caller_name = sys._getframe(1).f_code.co_name
        current_step = [int(x) for x in re.findall(r"\d+", caller_name)[:2]]
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
            logger.info(
                f"[MOCK_MODE] Running with WAID_MOCK_NOW={self.mock_now}"
            )

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
            cwd=self.env.waid_source_dir
            if "python" in command[0]
            else self.env.dbt_dir,
            env=proc_env,
        )

        # STREAM PASSTHROUGH: Direct forwarding of stdout without string alterations or splitting on '|'
        if process.stdout:
            for line in iter(process.stdout.readline, ""):
                sys.stdout.write(line)
                sys.stdout.flush()

        process.wait()

        if process.returncode != 0:
            logger.error(f"Command failed. Code: {process.returncode}")

        return process.returncode


# ==============================================================================
# STATE INSPECTION & DBT INITIALIZATION HELPERS
# ==============================================================================


def should_skip_ml_inference(env: WaidBoot, mock_now: str = None) -> bool:
    """
    @brief Checks database state using get_last_inference_datetime to determine
           if ML model execution can be bypassed.
    @param env WaidBoot configuration instance.
    @param mock_now Optional simulated current timestamp string.
    @return True if the last valid forecast is less than 6 hours old, False otherwise.
    """
    db_path = Path(env.waid_db)
    if not db_path.exists():
        logger.info("Database file not found. Full ML execution required.")
        return False

    last_ml_dt = get_last_inference_datetime(db_path, table_name="inference_forecasts")

    if last_ml_dt is None:
        logger.info("No valid prior ML predictions found in DB. Full ML execution required.")
        return False

    if mock_now and str(mock_now).lower() not in ("none", ""):
        try:
            current_dt = datetime.strptime(mock_now, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            current_dt = datetime.now()
    else:
        current_dt = datetime.now()

    if last_ml_dt.tzinfo is not None:
        last_ml_dt = last_ml_dt.replace(tzinfo=None)
    if current_dt.tzinfo is not None:
        current_dt = current_dt.replace(tzinfo=None)

    hours_diff = (current_dt - last_ml_dt).total_seconds() / 3600.0
    logger.info(f"Last ML prediction timestamp: {last_ml_dt} (Elapsed: {hours_diff:.2f}h)")

    if hours_diff < env.mock_interval_hours:
        logger.info(f"Last ML forecast is still valid (< {env.mock_interval_hours}h). Skipping ML inference.")
        return True
    else:
        logger.info(f"Last ML forecast is older than {env.mock_interval_hours}h. Full ML execution required.")
        return False


def ensure_dbt_setup(runner: PipelineRunner) -> int:
    """
    @brief Ensures dbt dependencies and target manifest are properly compiled before execution.
    @details Triggered when starting execution from an intermediate step or skipping main setup.
    @param runner PipelineRunner instance to execute dbt setup operations.
    @return Return code integer (0 on success).
    """
    target_manifest = Path(runner.env.dbt_dir) / "target" / "manifest.json"
    if not target_manifest.exists():
        logger.info("dbt compilation target missing. Automatically running required dbt setup commands...")
        code = runner.run_command(["dbt", "deps"] + runner.get_dbt_base_args(), is_dbt=True)
        if code != runner.env.waid_exit.SUCCESS:
            return code
        code = runner.run_command(["dbt", "compile"] + runner.get_dbt_base_args(), is_dbt=True)
        if code != runner.env.waid_exit.SUCCESS:
            return code
        code = runner.run_command(
            ["dbt", "run-operation", "dump_vars"] + runner.get_dbt_base_args(),
            is_dbt=True,
        )
        return code
    return runner.env.waid_exit.SUCCESS


# ==============================================================================
# STEP DEFINITIONS
# ==============================================================================

def waid_mock_update_ecowitt(runner: PipelineRunner, args: list) -> int:
    """
    @brief Generates mock Ecowitt observations in simulation mode.
    @param runner PipelineRunner instance to execute commands.
    @param args List of additional command-line arguments.
    @return Process return code integer.
    """
    cmd_args = list(args)
    if runner.mock_now and "--mock-now" not in cmd_args:
        cmd_args.extend(["--mock-now", runner.mock_now])

    return runner.run_command(
        ["python", str(runner.env.tools_dir / "utils/waid_mock_update_ecowitt.py"), *cmd_args]
    )


def waid_01_1_ingest_ecowitt(runner: PipelineRunner, args: list) -> int:
    """
    @brief Ingests raw observation records from Ecowitt API/sources.
    @param runner PipelineRunner instance to execute commands.
    @param args List of additional command-line arguments.
    @return Process return code integer.
    """
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_01_1_ingest_ecowitt.py"), *args]
    )


def waid_01_2_ingest_era5(runner: PipelineRunner, args: list) -> int:
    """
    @brief Ingests ERA5 reanalysis weather data.
    @param runner PipelineRunner instance to execute commands.
    @param args List of additional command-line arguments.
    @return Process return code integer.
    """
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_01_2_ingest_era5.py"), *args]
    )


def waid_01_3_profile_era5(runner: PipelineRunner, args: list) -> int:
    """
    @brief Profiles ERA5 datasets for quality and metric thresholds.
    @param runner PipelineRunner instance to execute commands.
    @param args List of additional command-line arguments.
    @return Process return code integer.
    """
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_01_3_profile_era5.py"), *args]
    )


def waid_02_0_dbt_clean(runner: PipelineRunner) -> int:
    """
    @brief Cleans dbt target directory and dependencies.
    @param runner PipelineRunner instance to execute commands.
    @return Process return code integer.
    """
    return runner.run_command(["dbt", "clean"] + runner.get_dbt_base_args(), is_dbt=True)


def waid_02_0_dbt_deps(runner: PipelineRunner) -> int:
    """
    @brief Downloads external dbt packages if not present locally.
    @param runner PipelineRunner instance to execute commands.
    @return Process return code integer.
    """
    packages_dir = Path("dbt_packages/dbt_utils")
    if packages_dir.exists():
        logger.info("dbt dependencies already present locally. Skipping download.")
        return 0

    return runner.run_command(["dbt", "deps"] + runner.get_dbt_base_args(), is_dbt=True)


def waid_02_0_dbt_compile(runner: PipelineRunner) -> int:
    """
    @brief Compiles dbt models into SQL executable files.
    @param runner PipelineRunner instance to execute commands.
    @return Process return code integer.
    """
    return runner.run_command(["dbt", "compile"] + runner.get_dbt_base_args(), is_dbt=True)


def waid_02_0_dbt_dump_vars(runner: PipelineRunner) -> int:
    """
    @brief Dumps current dbt execution parameters and variables.
    @param runner PipelineRunner instance to execute commands.
    @return Process return code integer.
    """
    return runner.run_command(
        ["dbt", "run-operation", "dump_vars"] + runner.get_dbt_base_args(),
        is_dbt=True,
    )


def waid_02_1_sync_ecowitt(runner: PipelineRunner, args: list) -> int:
    """
    @brief Synchronizes Ecowitt observations into staging storage.
    @param runner PipelineRunner instance to execute commands.
    @param args List of additional command-line arguments.
    @return Process return code integer.
    """
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_02_1_sync_ecowitt.py"), *args]
    )


def waid_02_2_dbt_staging_ecowitt(runner: PipelineRunner, args: list) -> int:
    """
    @brief Executes and tests dbt staging models for Ecowitt.
    @param runner PipelineRunner instance to execute commands.
    @param args List of additional command-line arguments.
    @return Process return code integer.
    """
    period_val = args[args.index("--period") + 1] if "--period" in args else None

    code = runner.run_command(
        ["dbt", "run", "--select", "stg_ecowitt"] + runner.get_dbt_base_args(),
        is_dbt=True,
        period=period_val,
    )
    if code != runner.env.waid_exit.SUCCESS:
        return code

    return runner.run_command(
        ["dbt", "test", "--select", "stg_ecowitt"] + runner.get_dbt_base_args(),
        is_dbt=True,
        period=period_val,
    )


def waid_03_1_match_datasets(runner: PipelineRunner, args: list) -> int:
    """
    @brief Matches and aligns station observations with ERA5 grid data.
    @param runner PipelineRunner instance to execute commands.
    @param args List of additional command-line arguments.
    @return Process return code integer.
    """
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_03_1_match_datasets.py"), *args]
    )


def waid_03_2_dbt_matches(runner: PipelineRunner, args: list) -> int:
    """
    @brief Runs and tests matched datasets in dbt.
    @param runner PipelineRunner instance to execute commands.
    @param args List of additional command-line arguments.
    @return Process return code integer.
    """
    period_val = args[args.index("--period") + 1] if "--period" in args else None

    code = runner.run_command(
        ["dbt", "run", "--select", "source:external_raw.match_records"] + runner.get_dbt_base_args(),
        is_dbt=True,
        period=period_val,
    )
    if code != runner.env.waid_exit.SUCCESS:
        return code

    return runner.run_command(
        ["dbt", "test", "--select", "source:external_raw.match_records"] + runner.get_dbt_base_args(),
        is_dbt=True,
        period=period_val,
    )


def waid_03_3_dbt_matches_bias(runner: PipelineRunner, args: list) -> int:
    """
    @brief Computes observation vs model bias metrics via dbt.
    @param runner PipelineRunner instance to execute commands.
    @param args List of additional command-line arguments.
    @return Process return code integer.
    """
    period_val = args[args.index("--period") + 1] if "--period" in args else None

    code = runner.run_command(
        ["dbt", "run", "--select", "int_matches_bias"] + runner.get_dbt_base_args(),
        is_dbt=True,
        period=period_val,
    )
    if code != runner.env.waid_exit.SUCCESS:
        return code

    return runner.run_command(
        ["dbt", "test", "--select", "int_matches_bias"] + runner.get_dbt_base_args(),
        is_dbt=True,
        period=period_val,
    )


def debug_waid_analyze_bias(runner: PipelineRunner, args: list) -> int:
    """
    @brief Debug utility step to analyze dataset bias distributions.
    @param runner PipelineRunner instance to execute commands.
    @param args List of additional command-line arguments.
    @return Process return code integer.
    """
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "utils/waid_analyze_bias.py"), *args]
    )


def waid_04_1_setup_metadata(runner: PipelineRunner, args: list) -> int:
    """
    @brief Builds station metadata tables and generates feature specs.
    @param runner PipelineRunner instance to execute commands.
    @param args List of additional command-line arguments.
    @return Process return code integer.
    """
    code = runner.run_command(
        ["dbt", "run", "--select", "station_metadata", "--full-refresh"] + runner.get_dbt_base_args(),
        is_dbt=True,
    )
    if code != runner.env.waid_exit.SUCCESS:
        return code

    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_04_1_setup_specs.py"), *args]
    )

    
def waid_05_1_ml_tensors(runner: PipelineRunner, args: list) -> int:
    """
    @brief Prepares training and evaluation tensor datasets for ML models.
    @param runner PipelineRunner instance to execute commands.
    @param args List of additional command-line arguments.
    @return Process return code integer.
    """
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_05_1_ml_tensors.py"), *args]
    )


def waid_05_2_ml_train(runner: PipelineRunner) -> int:
    """
    @brief Trains machine learning model architectures.
    @param runner PipelineRunner instance to execute commands.
    @return Process return code integer.
    """
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_05_2_ml_train.py")]
    )


def waid_05_3_ml_sanity_check(runner: PipelineRunner) -> int:
    """
    @brief Conducts sanity checks and evaluation on trained ML model weights.
    @param runner PipelineRunner instance to execute commands.
    @return Process return code integer.
    """
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_05_3_ml_sanity_check.py")]
    )


def waid_06_1_inference_forecast(runner: PipelineRunner, args: list) -> int:
    """
    @brief Generates model inferences and forecast predictions.
    @param runner PipelineRunner instance to execute commands.
    @param args List of additional command-line arguments.
    @return Process return code integer.
    """
    cmd = [
        "python",
        str(runner.env.tools_dir / "waid_06_1_inference_forecast.py"),
        *args,
    ]
    if runner.mock_now and "--mock-now" not in cmd:
        cmd.extend(["--mock-now", runner.mock_now])

    return runner.run_command(cmd)


def waid_06_2_inference_stats(runner: PipelineRunner) -> int:
    """
    @brief Calculates statistical metrics for generated forecast inferences.
    @param runner PipelineRunner instance to execute commands.
    @return Process return code integer.
    """
    return runner.run_command(
        ["dbt", "run", "--select", "inference_stats"] + runner.get_dbt_base_args(),
        is_dbt=True,
    )


def waid_06_3_dbt_inference_quality(runner: PipelineRunner) -> int:
    """
    @brief Evaluates forecast inference quality via dbt models.
    @param runner PipelineRunner instance to execute commands.
    @return Process return code integer.
    """
    return runner.run_command(
        ["dbt", "run", "--select", "+inference_quality", "--full-refresh"] + runner.get_dbt_base_args(),
        is_dbt=True,
    )


def waid_06_4_inference_quality(runner: PipelineRunner, args: list) -> int:
    """
    @brief Analyzes inference quality metrics and exports evaluation reports.
    @param runner PipelineRunner instance to execute commands.
    @param args List of additional command-line arguments.
    @return Process return code integer.
    """
    cmd = [
        "python",
        str(runner.env.tools_dir / "waid_06_4_inference_quality.py"),
    ]
    if runner.mock_now and "--mock-now" not in args:
        cmd.extend(["--mock-now", runner.mock_now])

    return runner.run_command(cmd)


def waid_07_1_export_deploy_db(runner: PipelineRunner, args: list) -> int:
    """
    @brief Exports clean deployment database artifacts.
    @param runner PipelineRunner instance to execute commands.
    @param args List of additional command-line arguments.
    @return Process return code integer.
    """
    cmd = [
        "python",
        str(runner.env.tools_dir / "waid_07_1_export_deploy_db.py"),
    ]
    if runner.mock_now and "--mock-now" not in args:
        cmd.extend(["--mock-now", runner.mock_now])

    return runner.run_command(cmd)


def waid_08_1_viz_streamlit_app(runner: PipelineRunner, args: list) -> int:
    """
    @brief Launches or deploys Streamlit visualization dashboard.
    @param runner PipelineRunner instance to execute commands.
    @param args List of additional command-line arguments.
    @return Process return code integer.
    """
    cmd = [
        "python",
        str(runner.env.tools_dir / "waid_08_1_viz_streamlit_app.py"),
        "--deploy",
    ]
    return runner.run_command(cmd)


def waid_08_2_doc_dbt_deploy(runner: PipelineRunner, args: list) -> int:
    """
    @brief Deploys updated dbt documentation artifacts.
    @param runner PipelineRunner instance to execute commands.
    @param args List of additional command-line arguments.
    @return Process return code integer.
    """
    cmd = [
        "python",
        str(runner.env.tools_dir / "waid_08_2_doc_dbt_deploy.py"),
    ]
    return runner.run_command(cmd)


# ==============================================================================
# PIPELINE EXECUTION ENGINE & UTILS
# ==============================================================================


def find_matching_step_index(steps: list, target: str) -> int:
    """
    @brief Searches for a step index by matching exact name or step prefix.
    @param steps List of step functions.
    @param target Target string (e.g. 'waid_07_1_export_deploy_db', 'waid_07_1', or '07_1').
    @return Index integer if found, -1 otherwise.
    """
    cleaned_target = target.strip()
    if cleaned_target.startswith("waid_"):
        cleaned_target = cleaned_target[5:]

    for idx, step in enumerate(steps):
        name = step.__name__
        cleaned_name = name[5:] if name.startswith("waid_") else name

        if name == target or cleaned_name.startswith(cleaned_target):
            return idx
    return -1


def run_step_sequence(
    steps: list,
    runner: PipelineRunner,
    extra_args: list[str],
    start_from: str = None,
) -> int:
    """
    @brief Sequentially executes a list of pipeline step functions.
    @param steps List of executable step functions.
    @param runner PipelineRunner instance to execute commands.
    @param extra_args List of extra CLI arguments to pass to steps.
    @param start_from Optional step name or prefix to fast-forward execution to.
    @return Return code integer (0 if all steps succeed).
    """
    if start_from:
        start_idx = find_matching_step_index(steps, start_from)
        if start_idx != -1:
            matched_name = steps[start_idx].__name__
            logger.info(f"Fast-forwarding sequence to step: {matched_name} (matched by '{start_from}')")
            steps = steps[start_idx:]

            setup_code = ensure_dbt_setup(runner)
            if setup_code != runner.env.waid_exit.SUCCESS:
                logger.error("dbt environment initialization failed before fast-forwarding.")
                return setup_code
        else:
            logger.warning(
                f"Target step '{start_from}' not found in current sequence. Executing all."
            )

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
            logger.debug(
                f"NO extra arguments passed to step '{step_func.__name__}' (expects only runner)"
            )
            code = step_func(runner)

        if code != runner.env.waid_exit.SUCCESS:
            logger.error(
                f"Step '{step_func.__name__}' failed with return code: {code}"
            )
            break

    return code


def parse_and_validate_arguments():
    """
    @brief Parses and validates command-line flags and parameters.
    @return Tuple containing (parsed_arguments, extra_passthrough_arguments).
    """
    parser = argparse.ArgumentParser(description="WAID Pipeline Orchestrator")

    parser.add_argument(
        "--run-mode",
        choices=["incremental", "backfill"],
        default="incremental",
        help="Execution mode: 'incremental' (single period) or 'backfill' (multi-period historical prep + ML)",
    )
    parser.add_argument(
        "--skip-ingestion",
        action="store_true",
        help="Skip data ingestion and profiling steps (01_1, 01_2, 01_3)",
    )
    parser.add_argument(
        "--skip-ingestion-ml-deploy",
        action="store_true",
        help="Skip ingestion, ML training, and deploy/viz steps (executes inference & quality sequence only)",
    )
    parser.add_argument(
        "--mock-now",
        type=str,
        default=None,
        help="Simulated current timestamp for retroactive execution (YYYY-MM-DD HH:MM:SS)",
    )
    parser.add_argument(
        "--start-from",
        type=str,
        default=None,
        help="Start execution directly from a specific step name or suffix (e.g., waid_07_1, 07_1, waid_03_1_match_datasets)",
    )
    parser.add_argument(
        "--period",
        type=str,
        default=None,
        help="Target period YYYY-MM for incremental run mode (defaults to current month if omitted)",
    )
    parser.add_argument(
        "--begin-period",
        type=str,
        default=None,
        help="Start period YYYY-MM for backfill mode",
    )
    parser.add_argument(
        "--end-period",
        type=str,
        default=None,
        help="End period YYYY-MM for backfill mode",
    )

    parsed_args, extra_passthrough_args = parser.parse_known_args()

    unrecognized = [
        arg for arg in extra_passthrough_args if arg.startswith("-")
    ]
    if unrecognized:
        sys.stderr.write(
            f"Error: Unrecognized option(s) or typo in flags: {', '.join(unrecognized)}\n"
        )
        sys.exit(2)

    period_pattern = re.compile(r"^\d{4}-\d{2}$")

    if not parsed_args.period and parsed_args.run_mode == "incremental":
        parsed_args.period = datetime.now(timezone.utc).strftime("%Y-%m")

    if parsed_args.period and not period_pattern.match(parsed_args.period):
        sys.stderr.write(
            f"Error: Invalid --period format '{parsed_args.period}'. Expected YYYY-MM.\n"
        )
        sys.exit(2)

    if parsed_args.begin_period and not period_pattern.match(
        parsed_args.begin_period
    ):
        sys.stderr.write(
            f"Error: Invalid --begin-period format '{parsed_args.begin_period}'. Expected YYYY-MM.\n"
        )
        sys.exit(2)

    if parsed_args.end_period and not period_pattern.match(
        parsed_args.end_period
    ):
        sys.stderr.write(
            f"Error: Invalid --end-period format '{parsed_args.end_period}'. Expected YYYY-MM.\n"
        )
        sys.exit(2)

    if parsed_args.run_mode == "backfill":
        start_p = parsed_args.begin_period or parsed_args.period
        end_p = parsed_args.end_period or parsed_args.period

        if not start_p or not end_p:
            sys.stderr.write(
                "Error: Backfill mode requires --period YYYY-MM (or both --begin-period and --end-period).\n"
            )
            sys.exit(2)

    return parsed_args, extra_passthrough_args


def main() -> int:
    """
    @brief Main orchestrator execution entry point.
    @return System exit code integer.
    """
    parsed_args, extra_passthrough_args = parse_and_validate_arguments()

    env = WaidBoot()
    runner = PipelineRunner(env, mock_now=parsed_args.mock_now)

    db_path = env.waid_db
    
    if parsed_args.skip_ingestion_ml_deploy and not Path(db_path).exists():
        logger.warning(
            f"Cannot run inference-only mode. Required DB path not found: {db_path}"
        )
        sys.exit(runner.env.waid_exit.INPUT_FAIL)

    if env.waid_sim_mode:
        logger.warning(
            f"Simulation mode active. Running mock data generation using mock database ({env.waid_db})"
        )

    if parsed_args.skip_ingestion_ml_deploy:
        logger.warning(
            "Skipping Ingestion, ML Training, and Deploy (--skip-ingestion-ml-deploy active). Running Inference sequence only."
        )
        setup_code = ensure_dbt_setup(runner)
        if setup_code != env.waid_exit.SUCCESS:
            return setup_code
    else:
        data_dir = Path(env.waid_data_dir)
        backup_dir = data_dir / "backups"

        logger.info(f"🔶 Regime Mode: {env.setup_mode}")
        if env.setup_mode in [1, 2]:
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp_str = datetime.now(timezone.utc).strftime(
                "%Y%m%d_%H%M%S"
            )

            if env.setup_mode == 2:
                logger.warning(
                    f"--- HARD RESET (Mode 2): Purging ALL data in {data_dir} ---"
                )
                backup_name = backup_dir / f"backup_hard_reset_{timestamp_str}"

                logger.info(
                    f"Creating full backup archive at {backup_name}.zip ..."
                )
                shutil.make_archive(
                    str(backup_name), "zip", data_dir, root_dir=data_dir
                )

                for item in data_dir.iterdir():
                    if item.name == "backups":
                        continue
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        item.unlink(missing_ok=True)

                shutil.rmtree(env.dbt_dir / "target", ignore_errors=True)

            elif env.setup_mode == 1:
                logger.info(
                    f"--- SOFT RESET (Mode 1): Preserving raw data, resetting DB & ML artifacts ---"
                )
                backup_name = backup_dir / f"backup_soft_reset_{timestamp_str}"

                logger.info(f"Creating lightweight backup at {backup_name} ...")
                curr_backup_sub = Path(backup_name)
                curr_backup_sub.mkdir(exist_ok=True)

                for item in data_dir.iterdir():
                    is_db = item.suffix == ".db"
                    is_mock_db = is_db and "mock" in item.name.lower()
                    is_artifact = item.name in ["models", "tensors"]

                    should_process = False
                    if env.waid_sim_mode:
                        should_process = is_mock_db
                    else:
                        should_process = (
                            is_db and not is_mock_db
                        ) or is_artifact

                    if should_process:
                        dest = curr_backup_sub / item.name

                        if item.is_dir():
                            shutil.copytree(item, dest, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, dest)

                        if item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                        else:
                            item.unlink(missing_ok=True)

                shutil.rmtree(env.dbt_dir / "target", ignore_errors=True)

    # ==============================================================================
    # PIPELINE MASTER SEQUENCE ASSEMBLY
    # ==============================================================================
    
    master_steps = []

    # 1. Ingestion Stage
    if parsed_args.skip_ingestion or parsed_args.skip_ingestion_ml_deploy:
        logger.warning("Skipping raw data ingestion and profiling steps.")
    else:
        if env.waid_sim_mode:
            master_steps.append(waid_mock_update_ecowitt)
        else:
            master_steps.append(waid_01_1_ingest_ecowitt)

        master_steps.extend([
            waid_01_2_ingest_era5,
            waid_01_3_profile_era5,
        ])

    # 2. Core Preparation & Transformation Stage
    if not parsed_args.skip_ingestion_ml_deploy:
        master_steps.extend([
            waid_02_0_dbt_clean,
            waid_02_0_dbt_deps,
            waid_02_0_dbt_compile,
            waid_02_0_dbt_dump_vars,
            waid_02_1_sync_ecowitt,
            waid_02_2_dbt_staging_ecowitt,
            waid_03_1_match_datasets,
            waid_03_2_dbt_matches,
            waid_03_3_dbt_matches_bias,
            debug_waid_analyze_bias,
            waid_04_1_setup_metadata,
        ])

    # 3. ML & Inference Stage
    skip_ml_inference = should_skip_ml_inference(env, mock_now=parsed_args.mock_now)
    
    if parsed_args.skip_ingestion_ml_deploy:
        master_steps.extend([
            waid_06_1_inference_forecast,
            waid_06_2_inference_stats,
            waid_06_3_dbt_inference_quality,
            waid_06_4_inference_quality,
        ])
    else:
        if not skip_ml_inference:
            master_steps.extend([
                waid_05_1_ml_tensors,
                waid_05_2_ml_train,
                waid_05_3_ml_sanity_check,
            ])
        else:
            logger.warning("ML predictions skipped based on DB state. Steps from 05_1 to 05_3 omitted.")
            
        master_steps.extend([
            waid_06_1_inference_forecast,
            waid_06_2_inference_stats,
            waid_06_3_dbt_inference_quality,
            waid_06_4_inference_quality,
        ])

    # 4. Export & Visualization Stage
    if not parsed_args.skip_ingestion_ml_deploy:
        master_steps.append(waid_07_1_export_deploy_db)
        master_steps.extend([
            waid_08_1_viz_streamlit_app,
            waid_08_2_doc_dbt_deploy,
        ])

    # Preliminary check on --start-from
    if parsed_args.start_from:
        start_idx = find_matching_step_index(master_steps, parsed_args.start_from)
        if start_idx == -1:
            step_names = [s.__name__ for s in master_steps]
            logger.error(
                f"Error: Specified step/prefix '{parsed_args.start_from}' does not exist or is not included in the current sequence."
            )
            logger.info(f"Available steps: {', '.join(step_names)}")
            return env.waid_exit.INPUT_FAIL
    
    # ==============================================================================
    # PIPELINE EXECUTION
    # ==============================================================================
    execution_args = list(extra_passthrough_args)
    if parsed_args.period:
        execution_args.extend(["--period", parsed_args.period])
    
    if parsed_args.run_mode == "backfill":
        start_p = parsed_args.begin_period or parsed_args.period
        end_p = parsed_args.end_period or parsed_args.period
        periods = generate_period_range(start_p, end_p)
        logger.debug(f"Starting BACKFILL execution for periods: {periods}")

        for p in periods:
            logger.info(f"--- Processing Data Preparation for period: {p} ---")
            period_args = extra_passthrough_args + ["--period", p]
            code = run_step_sequence(
                master_steps,
                runner,
                period_args,
                start_from=parsed_args.start_from,
            )
            if code != runner.env.waid_exit.SUCCESS:
                logger.error(f"Backfill halted due to error in period {p}")
                return code
    else:
        logger.debug("Starting INCREMENTAL execution")
        code = run_step_sequence(
            master_steps,
            runner,
            execution_args,
            start_from=parsed_args.start_from,
        )

    if code == runner.env.waid_exit.SUCCESS:
        logger.success("--- Pipeline successfully terminated ---")
    else:
        logger.error(f"--- Pipeline terminated with error (code={code}) ---")

    return code


if __name__ == "__main__":
    sys.exit(main())