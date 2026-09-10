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

# Import WaidBoot configuration and utility classes
sys.path.append(
    str(
        Path(
            os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])
        ).resolve()
        / "config"
    )
)
from boot import WError, WaidBoot, WaidExit

# Import shared utilities from Single Source of Truth
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
        @brief Executes a subprocess command while capturing and standardizing its output logs.
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
                f"[MOCK MODE] Running with WAID_MOCK_NOW={self.mock_now}"
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

        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

        for line in process.stdout:
            clean_line = line.strip()
            raw_line = ansi_escape.sub("", clean_line)

            if (
                "cudart_stub.cc" in raw_line
                or "Could not find cuda drivers" in raw_line
            ):
                continue

            target_level = "INFO"

            for lvl in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                if lvl in raw_line:
                    target_level = lvl
                    break

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
# STATE INSPECTION HELPER
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

    # Retrieve the last valid inference timestamp using the shared module function
    last_ml_dt = get_last_inference_datetime(db_path, table_name="public_forecasts")

    if last_ml_dt is None:
        logger.info("No valid prior ML predictions found in DB. Full ML execution required.")
        return False

    # Determine current timestamp context
    if mock_now and str(mock_now).lower() not in ("none", ""):
        try:
            current_dt = datetime.strptime(mock_now, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            current_dt = datetime.now()
    else:
        current_dt = datetime.now()

    # Strip timezone metadata for naive datetime comparison
    if last_ml_dt.tzinfo is not None:
        last_ml_dt = last_ml_dt.replace(tzinfo=None)
    if current_dt.tzinfo is not None:
        current_dt = current_dt.replace(tzinfo=None)

    hours_diff = (current_dt - last_ml_dt).total_seconds() / 3600.0
    logger.info(f"Last ML prediction timestamp: {last_ml_dt} (Elapsed: {hours_diff:.2f}h)")

    if hours_diff < 6.0:
        logger.info("Last ML forecast is still valid (< 6h). Skipping ML inference.")
        return True
    else:
        logger.info("Last ML forecast is older than 6h. Full ML execution required.")
        return False


# ==============================================================================
# STEP DEFINITIONS
# ==============================================================================


def waid_00_1_dbt_clean(runner: PipelineRunner) -> int:
    """@brief Cleans dbt target directory and dependencies."""
    return runner.run_command(["dbt", "clean"] + runner.get_dbt_base_args(), is_dbt=True)


def waid_00_2_dbt_deps(runner: PipelineRunner) -> int:
    """@brief Downloads external dbt packages if not present locally."""
    packages_dir = Path("dbt_packages/dbt_utils")
    if packages_dir.exists():
        logger.info("dbt dependencies already present locally. Skipping download.")
        return 0

    return runner.run_command(["dbt", "deps"] + runner.get_dbt_base_args(), is_dbt=True)


def waid_00_3_dbt_compile(runner: PipelineRunner) -> int:
    """@brief Compiles dbt models into SQL executable files."""
    return runner.run_command(["dbt", "compile"] + runner.get_dbt_base_args(), is_dbt=True)


def waid_00_4_dbt_dump_vars(runner: PipelineRunner) -> int:
    """@brief Dumps current dbt execution parameters and variables."""
    return runner.run_command(
        ["dbt", "run-operation", "dump_vars"] + runner.get_dbt_base_args(),
        is_dbt=True,
    )


def waid_mock_update_ecowitt(runner: PipelineRunner, args: list) -> int:
    """@brief Generates mock Ecowitt observations in simulation mode."""
    cmd_args = list(args)
    if runner.mock_now and "--mock-now" not in cmd_args:
        cmd_args.extend(["--mock-now", runner.mock_now])

    return runner.run_command(
        ["python", str(runner.env.tools_dir / "utils/waid_mock_update_ecowitt.py"), *cmd_args]
    )


def waid_01_1_ingest_ecowitt(runner: PipelineRunner, args: list) -> int:
    """@brief Ingests raw observation records from Ecowitt API/sources."""
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_01_1_ingest_ecowitt.py"), *args]
    )


def waid_01_2_ingest_era5(runner: PipelineRunner, args: list) -> int:
    """@brief Ingests ERA5 reanalysis weather data."""
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_01_2_ingest_era5.py"), *args]
    )


def waid_01_3_profile_era5(runner: PipelineRunner, args: list) -> int:
    """@brief Profiles ERA5 datasets for quality and metric thresholds."""
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_01_3_profile_era5.py"), *args]
    )


def waid_02_1_sync_ecowitt(runner: PipelineRunner, args: list) -> int:
    """@brief Synchronizes Ecowitt observations into staging storage."""
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_02_1_sync_ecowitt.py"), *args]
    )


def waid_02_2_dbt_staging_ecowitt(runner: PipelineRunner, args: list) -> int:
    """@brief Executes and tests dbt staging models for Ecowitt."""
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
    """@brief Matches and aligns station observations with ERA5 grid data."""
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_03_1_match_datasets.py"), *args]
    )


def waid_03_2_dbt_matches(runner: PipelineRunner, args: list) -> int:
    """@brief Runs and tests matched datasets in dbt."""
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
    """@brief Computes observation vs model bias metrics via dbt."""
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
    """@brief Debug utility step to analyze dataset bias distributions."""
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "utils/waid_analyze_bias.py"), *args]
    )


def waid_04_1_setup_metadata(runner: PipelineRunner, args: list) -> int:
    """@brief Builds station metadata tables and generates feature specs."""
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
    """@brief Prepares training and evaluation tensor datasets for ML models."""
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_05_1_ml_tensors.py"), *args]
    )


def waid_05_2_ml_train(runner: PipelineRunner) -> int:
    """@brief Trains machine learning model architectures."""
    return runner.run_command(
        ["python", str(runner.env.tools_dir / "waid_05_2_ml_train.py")]
    )


def waid_06_1_inference_forecast(runner: PipelineRunner, args: list) -> int:
    """@brief Generates model inferences and forecast predictions."""
    cmd = [
        "python",
        str(runner.env.tools_dir / "waid_06_1_inference_forecast.py"),
        *args,
    ]
    if runner.mock_now and "--mock-now" not in cmd:
        cmd.extend(["--mock-now", runner.mock_now])

    return runner.run_command(cmd)


def waid_06_2_inference_stats(runner: PipelineRunner) -> int:
    """@brief Calculates statistical metrics for generated forecast inferences."""
    return runner.run_command(
        ["dbt", "run", "--select", "inference_stats"] + runner.get_dbt_base_args(),
        is_dbt=True,
    )


def waid_06_3_dbt_inference_quality(runner: PipelineRunner) -> int:
    """@brief Evaluates forecast inference quality via dbt models."""
    return runner.run_command(
        ["dbt", "run", "--select", "+inference_quality", "--full-refresh"] + runner.get_dbt_base_args(),
        is_dbt=True,
    )


def waid_06_4_inference_quality(runner: PipelineRunner, args: list) -> int:
    """@brief Analyzes inference quality metrics and exports evaluation reports."""
    cmd = [
        "python",
        str(runner.env.tools_dir / "waid_06_4_inference_quality.py"),
    ]
    if runner.mock_now:
        cmd.extend(["--mock-now", runner.mock_now])

    return runner.run_command(cmd)


def waid_07_1_export_deploy_db(runner: PipelineRunner, args: list) -> int:
    """@brief Exports clean deployment database artifacts."""
    cmd = [
        "python",
        str(runner.env.tools_dir / "waid_07_1_export_deploy_db.py"),
    ]
    if runner.mock_now:
        cmd.extend(["--mock-now", runner.mock_now])

    return runner.run_command(cmd)


def waid_08_1_viz_streamlit_app(runner: PipelineRunner, args: list) -> int:
    """@brief Launches or deploys Streamlit visualization dashboard."""
    cmd = [
        "python",
        str(runner.env.tools_dir / "waid_08_1_viz_streamlit_app.py"),
        "--deploy",
    ]
    return runner.run_command(cmd)


def waid_08_2_doc_dbt_deploy(runner: PipelineRunner, args: list) -> int:
    """@brief Deploys updated dbt documentation artifacts."""
    cmd = [
        "python",
        str(runner.env.tools_dir / "waid_08_2_doc_dbt_deploy.py"),
    ]
    return runner.run_command(cmd)


# ==============================================================================
# PIPELINE EXECUTION ENGINE & UTILS
# ==============================================================================


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
    @param start_from Optional step name to fast-forward execution to.
    @return Return code integer (0 if all steps succeed).
    """
    if start_from:
        step_names = [s.__name__ for s in steps]
        if start_from in step_names:
            start_idx = step_names.index(start_from)
            logger.info(f"Fast-forwarding sequence to step: {start_from}")
            steps = steps[start_idx:]
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
        "--skip-setup",
        action="store_true",
        help="Skip initial dbt setup steps (00_1 to 00_4)",
    )
    parser.add_argument(
        "--skip-ingestion",
        action="store_true",
        help="Skip data ingestion and profiling steps (01_1, 01_2, 01_3)",
    )
    parser.add_argument(
        "--skip-ingestion-deploy",
        action="store_true",
        help="Skip raw data ingestion and final visualization/deployment steps (01 and 08)",
    )
    parser.add_argument(
        "--mock-now",
        type=str,
        default=None,
        help="Simulated current timestamp for retroactive execution (YYYY-MM-DD HH:MM:SS)",
    )
    parser.add_argument(
        "--only-setup",
        action="store_true",
        help="Run ONLY the initial dbt setup steps (00_1 to 00_4) and exit",
    )
    parser.add_argument(
        "--start-from",
        type=str,
        default=None,
        help="Start execution directly from a specific step name (e.g., waid_03_1_match_datasets)",
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

    db_path = (
        os.getenv("WAID_DB_MOCK_FILE")
        if env.waid_sim_mode
        else os.getenv("WAID_DB_FILE")
    )
    if parsed_args.skip_ingestion_deploy and not Path(db_path).exists():
        logger.warning(
            f"Cannot skip Data Ingestion / Mock Update. Required path: {db_path}"
        )
        sys.exit(runner.env.waid_exit.INPUT_FAIL)

    if env.waid_sim_mode:
        logger.warning(
            f"Simulation mode active. Running mock data generation using mock database ({env.waid_db})"
        )

    if parsed_args.skip_ingestion_deploy:
        logger.warning(
            "Skipping data ingestion and final viz/deploy steps (--skip-ingestion-deploy flag active)"
        )
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

        if parsed_args.skip_setup:
            logger.warning("Skipping DBT setup steps (--skip-setup flag active)")
            code = runner.env.waid_exit.SUCCESS
        else:
            setup_steps = [
                waid_00_1_dbt_clean,
                waid_00_2_dbt_deps,
                waid_00_3_dbt_compile,
                waid_00_4_dbt_dump_vars,
            ]

            code = run_step_sequence(
                setup_steps,
                runner,
                extra_passthrough_args,
                start_from=parsed_args.start_from,
            )
            if code == runner.env.waid_exit.SUCCESS:
                logger.success("--- Setup successfully completed ---")
            else:
                logger.error(f"--- Setup failed with error (code={code}) ---")

        if parsed_args.only_setup:
            logger.info(
                "--- Executing ONLY DBT Setup steps (--only-setup active) ---"
            )
            return code

    # Data Preparation Steps
    data_prep_steps = []

    if env.waid_sim_mode:
        data_prep_steps.append(waid_mock_update_ecowitt)
    elif parsed_args.skip_ingestion or parsed_args.skip_ingestion_deploy:
        logger.warning(
            "Skipping raw data ingestion and profiling steps (--skip-ingestion or --skip-ingestion-deploy active)"
        )
    else:
        data_prep_steps.extend(
            [
                waid_01_1_ingest_ecowitt,
                waid_01_2_ingest_era5,
                waid_01_3_profile_era5,
            ]
        )

    data_prep_steps.extend(
        [
            waid_02_1_sync_ecowitt,
            waid_02_2_dbt_staging_ecowitt,
            waid_03_1_match_datasets,
            waid_03_2_dbt_matches,
            waid_03_3_dbt_matches_bias,
            debug_waid_analyze_bias,
            waid_04_1_setup_metadata,
        ]
    )

    # State-driven ML decision: inspect public_forecasts DB table
    skip_ml_inference = should_skip_ml_inference(env, mock_now=parsed_args.mock_now)

    if skip_ml_inference:
        logger.warning(
            "ML predictions skipped based on DB state. Steps 05_1/05_2 omitted, 06_1 will run with --skip-ml."
        )
        ml_and_inference_steps = [
            waid_06_1_inference_forecast,
            waid_06_2_inference_stats,
            waid_06_3_dbt_inference_quality,
            waid_06_4_inference_quality,
        ]
        # Pass --skip-ml specifically to 06_1
        step_06_1_args = list(extra_passthrough_args)
        if "--skip-ml" not in step_06_1_args:
            step_06_1_args.append("--skip-ml")
    else:
        ml_and_inference_steps = [
            waid_05_1_ml_tensors,
            waid_05_2_ml_train,
            waid_06_1_inference_forecast,
            waid_06_2_inference_stats,
            waid_06_3_dbt_inference_quality,
            waid_06_4_inference_quality,
        ]
        step_06_1_args = extra_passthrough_args

    export_and_deploy_steps = [
        waid_07_1_export_deploy_db,
    ]

    viz_steps = [
        waid_08_1_viz_streamlit_app,
        waid_08_2_doc_dbt_deploy,
    ]

    # ==============================================================================
    # PIPELINE EXECUTION LOGIC
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
                logger.info(
                    f"--- Processing Data Preparation for period: {p} ---"
                )
                period_args = extra_passthrough_args + ["--period", p]
                code = run_step_sequence(
                    data_prep_steps,
                    runner,
                    period_args,
                    start_from=parsed_args.start_from,
                )
                if code != runner.env.waid_exit.SUCCESS:
                    logger.error(f"Backfill halted due to error in period {p}")
                    return code

            logger.info(
                "Data preparation backfill completed. Starting Global Machine Learning & Deployment."
            )
            ml_args = ["--period", end_p] if end_p else []
            code = run_step_sequence(
                ml_and_inference_steps + export_and_deploy_steps,
                runner,
                ml_args,
                start_from=parsed_args.start_from,
            )

        else:  # Incremental Mode
            logger.debug("Starting INCREMENTAL execution")
            code = run_step_sequence(
                data_prep_steps,
                runner,
                incremental_args,
                start_from=parsed_args.start_from,
            )
            if code != runner.env.waid_exit.SUCCESS:
                return code

            # Execute ML & Inference steps (passing --skip-ml to 06_1 if required)
            for step_func in ml_and_inference_steps:
                args_to_pass = (
                    step_06_1_args
                    if step_func.__name__ == "waid_06_1_inference_forecast"
                    else incremental_args
                )
                code = run_step_sequence(
                    [step_func],
                    runner,
                    args_to_pass,
                    start_from=parsed_args.start_from,
                )
                if code != runner.env.waid_exit.SUCCESS:
                    return code

            code = run_step_sequence(
                export_and_deploy_steps + viz_steps,
                runner,
                incremental_args,
                start_from=parsed_args.start_from,
            )
    else:
        code = run_step_sequence(
            data_prep_steps,
            runner,
            incremental_args,
            start_from=parsed_args.start_from,
        )
        if code != runner.env.waid_exit.SUCCESS:
            return code

        for step_func in ml_and_inference_steps:
            args_to_pass = (
                step_06_1_args
                if step_func.__name__ == "waid_06_1_inference_forecast"
                else incremental_args
            )
            code = run_step_sequence(
                [step_func],
                runner,
                args_to_pass,
                start_from=parsed_args.start_from,
            )
            if code != runner.env.waid_exit.SUCCESS:
                return code

        code = run_step_sequence(
            export_and_deploy_steps,
            runner,
            incremental_args,
            start_from=parsed_args.start_from,
        )

    if code == runner.env.waid_exit.SUCCESS:
        logger.success("--- Pipeline successfully terminated ---")
    else:
        logger.error(f"--- Pipeline terminated with error (code={code}) ---")

    return code


if __name__ == "__main__":
    sys.exit(main())