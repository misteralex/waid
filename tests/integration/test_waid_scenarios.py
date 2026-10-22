#!/usr/bin/env python3

"""
@file test_waid_scenarios.py
@brief Integration test suite and CLI runner for WAID pipeline scenarios.
@details Validates isolated scenario setup and full end-to-end pipeline execution 
         via real-time streaming subprocess invocation with simulation flags.
"""

import os
import sys
from pathlib import Path
from config.boot import (
    WaidBoot,
    WError,
    WaidExit,
)
from mock.waid_scenario_generator import (
    WAIDScenarioGenerator,
)
import argparse
import subprocess
import pytest
import pandas as pd


@pytest.fixture
def scenario_generator() -> WAIDScenarioGenerator:
    """
    @brief Fixture providing initialized WAIDScenarioGenerator instance.
    @return WAIDScenarioGenerator initialized scenario generator object.
    """
    mock_base = str(waid_root / "mock")
    return WAIDScenarioGenerator(mock_base_dir=mock_base)


def execute_pipeline_with_streaming(env : WaidBoot, env_vars: dict) -> int:
    """
    @brief Executes the orchestration pipeline with real-time stdout streaming and proper environment isolation.
    @param env WaidBoot configuration instance.
    @param env_vars Dictionary containing operational environment variables.
    @return Process return code integer.
    """
    cmd = [sys.executable, str(env.waid_source_dir / "waid_orchestrate_lab.py")]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env_vars,
        cwd=str(env.waid_source_dir)
    )

    if process.stdout:
        for line in iter(process.stdout.readline, ""):
            sys.stdout.write(line)
            sys.stdout.flush()

    process.wait()
    return process.returncode


def test_scenario_no_data(env : WaidBoot, scenario_generator: WAIDScenarioGenerator) -> None:
    """
    @brief Tests 'no_data' scenario creation and full pipeline execution handling.
    @param scenario_generator Scenario generator fixture.
    @return None
    """
    data_path = scenario_generator.build_scenario(
        env,
        scenario_name="test_no_data_scenario",
        scenario_mode="no_data"
    )
    
    assert data_path.exists()
    assert (data_path / "ecowitt").exists()

    env_vars = os.environ.copy()
    env_vars["WAID_DATA_DIR"] = str(data_path)
    env_vars["WAID_RETRO_NOW"] = "2026-09-15 12:00:00"
    env_vars["WAID_SIM_MODE"] = "True"
    env_vars["WAID_ALLOW_ENV_OVERRIDE"] = "False"
    
    exit_code = execute_pipeline_with_streaming(env, env_vars)
    assert exit_code != 0


def test_scenario_insufficient_data(env : WaidBoot, scenario_generator: WAIDScenarioGenerator) -> None:
    """
    @brief Tests 'insufficient_data' scenario with truncated history below guardrail.
    @param env WaidBoot configuration instance.
    @param scenario_generator Scenario generator fixture.
    @return None
    """
    data_path = scenario_generator.build_scenario(
        env,
        scenario_name="test_insufficient_data_scenario",
        scenario_mode="insufficient_data"
    )
    
    csv_files = list(data_path.glob("ecowitt/*.csv"))
    assert len(csv_files) == 1
    df = pd.read_csv(csv_files[0])
    assert len(df) == 144


def test_scenario_training_required(env : WaidBoot, scenario_generator: WAIDScenarioGenerator) -> None:
    """
    @brief Tests 'training_required' scenario ensuring full history without pre-trained model.
    @param env WaidBoot configuration instance.
    @param scenario_generator Scenario generator fixture.
    @return None
    """
    data_path = scenario_generator.build_scenario(
        env,
        scenario_name="test_training_required_scenario",
        scenario_mode="training_required"
    )
    
    assert (data_path / "ecowitt").exists()
    assert not (data_path / "models" / "lstm_nowcast_v1.h5").exists()


def test_scenario_inference_ready(env : WaidBoot, scenario_generator: WAIDScenarioGenerator) -> None:
    """
    @brief Tests 'inference_ready' scenario ensuring mock model checkpoint and full data.
    @param env WaidBoot configuration instance.
    @param scenario_generator Scenario generator fixture.
    @return None
    """
    data_path = scenario_generator.build_scenario(
        env,
        scenario_name="test_inference_ready_scenario",
        scenario_mode="inference_ready"
    )
    
    assert (data_path / "ecowitt").exists()
    assert (data_path / "era5").exists()
    assert (data_path / "models" / "lstm_nowcast_v1.h5").exists()


def test_scenario_anomaly_block(env : WaidBoot, scenario_generator: WAIDScenarioGenerator) -> None:
    """
    @brief Tests 'anomaly_block' scenario with injected physical violations.
    @param env WaidBoot configuration instance.
    @param scenario_generator Scenario generator fixture.
    @return None
    """
    data_path = scenario_generator.build_scenario(
        env,
        scenario_name="test_anomaly_block_scenario",
        scenario_mode="anomaly_block",
        target="ecowitt",
        anomaly_type="physics_anomaly"
    )
    
    csv_files = list(data_path.glob("ecowitt/*.csv"))
    df = pd.read_csv(csv_files[0])
    assert df.loc[0, "solar_radiation"] == 450.0


def run_scenario_cli(env: WaidBoot, scenario_mode: str) -> None:
    """
    @brief Helper to execute individual scenario generation and full pipeline execution via native CLI with live logs.
    @param env WaidBoot instance containing configuration.
    @param scenario_mode Target scenario mode string.
    @return None
    """
    generator = WAIDScenarioGenerator(env)
    scenario_name = f"test_{scenario_mode}_scenario"
    
    print(f"\n--- [CLI RUNNER] Setting up scenario: {scenario_name} (Mode: {scenario_mode}) ---")
    data_path = generator.build_scenario(
        scenario_name=scenario_name,
        scenario_mode=scenario_mode,
        anomaly_type="physics_anomaly" if scenario_mode == "anomaly_block" else None,
        target="ecowitt" if scenario_mode == "anomaly_block" else "none"
    )
    
    print(f"--- [CLI RUNNER] Executing full pipeline orchestration for mode [{scenario_mode}] at {data_path} ---")
    
    env_vars = os.environ.copy()
    env_vars["WAID_DATA_DIR"] = str(data_path)
    env_vars["WAID_RETRO_NOW"] = "2026-09-15 12:00:00"
    env_vars["WAID_SIM_MODE"] = "True"
    env_vars["WAID_ALLOW_ENV_OVERRIDE"] = "False"
    
    exit_code = execute_pipeline_with_streaming(env, env_vars)
    print(f"[CLI RESULT] Pipeline orchestration finished with exit code: {exit_code}")

    # Catch and check logs if needed
    log_files = list(data_path.glob("**/waid_pipeline.log")) + list(data_path.glob("logs/*.log"))
    if log_files:
        log_content = log_files[0].read_text(encoding="utf-8")
        if scenario_mode in ("no_data", "insufficient_data"):
            assert any(term in log_content.lower() for term in ["guardrail", "missing", "insufficient", "error", "critical"])
            print(f"[CLI PASSED] Successfully validated guardrail log messages for '{scenario_mode}'.")


if __name__ == "__main__":
    env = WaidBoot()
    parser = argparse.ArgumentParser(description="WAID Scenario Integration Test CLI")
    parser.add_argument("--set-scenario", required=True, choices=["no_data", "insufficient_data", "training_required", "inference_ready", "anomaly_block"])
    args = parser.parse_args()

    run_scenario_cli(env, args.set_scenario)