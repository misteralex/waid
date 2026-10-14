"""
@file test_waid_orchestrate.py
@brief Unit tests for waid_orchestrate.py Prefect orchestrator module.
@author AF
@date 2026
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from waid_orchestrate import (
    run_python_step,
    run_dbt_step,
    ensure_dbt_setup,
)


@pytest.fixture
def mock_waid_env(tmp_path) -> MagicMock:
    """
    @brief Fixture providing a mock WaidBoot configuration environment for Prefect tests.
    @param tmp_path Pytest fixture for temporary directory.
    @return MagicMock configured environment instance.
    """
    tools_dir = tmp_path / "tools"
    dbt_dir = tmp_path / "dbt"
    profiles_dir = tmp_path / "config"
    db_path = tmp_path / "waid.db"
    
    tools_dir.mkdir(parents=True, exist_ok=True)
    dbt_dir.mkdir(parents=True, exist_ok=True)
    profiles_dir.mkdir(parents=True, exist_ok=True)

    env = MagicMock()
    env.tools_dir = tools_dir
    env.waid_source_dir = tmp_path
    env.dbt_dir = dbt_dir
    env.dbt_profiles_dir = profiles_dir
    env.dbt_bin_file = "dbt"
    env.waid_db_file = str(db_path)
    env.env_dict = {"WAID_SIM_MODE": "1"}
    return env


@patch("waid_orchestrate.get_run_logger")
@patch("waid_orchestrate.subprocess.run")
def test_run_python_step_success(mock_subprocess_run, mock_get_logger, mock_waid_env) -> None:
    """
    @brief Tests successful execution of a python script step via Prefect task.
    @param mock_subprocess_run Mocked subprocess.run call.
    @param mock_get_logger Mocked Prefect run logger.
    @param mock_waid_env Mocked environment fixture.
    @return None
    """
    mock_subprocess_run.return_value = MagicMock(returncode=0)
    mock_get_logger.return_value = MagicMock()
    
    script_file = mock_waid_env.tools_dir / "waid_01_1_ingest_ecowitt.py"
    script_file.touch()

    code = run_python_step.fn(
        env = mock_waid_env,
        script_name="waid_01_1_ingest_ecowitt.py",
        extra_args=["--period", "2026-06"],
    )

    assert code == 0
    mock_subprocess_run.assert_called_once()


@patch("waid_orchestrate.get_run_logger")
def test_run_python_step_not_found(mock_get_logger, mock_waid_env) -> None:
    """
    @brief Tests that FileNotFoundError is raised when python script does not exist.
    @param mock_get_logger Mocked Prefect run logger.
    @param mock_waid_env Mocked environment fixture.
    @return None
    """
    mock_get_logger.return_value = MagicMock()

    with pytest.raises(FileNotFoundError):
        run_python_step.fn(
            env = mock_waid_env,
            script_name="non_existent_script.py",
            
        )


@patch("waid_orchestrate.get_run_logger")
@patch("waid_orchestrate.subprocess.run")
def test_run_dbt_step_success(mock_subprocess_run, mock_get_logger, mock_waid_env) -> None:
    """
    @brief Tests successful execution of a dbt command via Prefect task.
    @param mock_subprocess_run Mocked subprocess.run call.
    @param mock_get_logger Mocked Prefect run logger.
    @param mock_waid_env Mocked environment fixture.
    @return None
    """
    mock_subprocess_run.return_value = MagicMock(returncode=0)
    mock_get_logger.return_value = MagicMock()

    code = run_dbt_step.fn(
        env = mock_waid_env,
        command="run",
        select="stg_ecowitt",
        full_refresh=True,
    )

    assert code == 0
    mock_subprocess_run.assert_called_once()
    args_called = mock_subprocess_run.call_args[0][0]
    assert "run" in args_called
    assert "--full-refresh" in args_called
    assert "stg_ecowitt" in args_called


def test_ensure_dbt_setup_manifest_exists(mock_waid_env) -> None:
    """
    @brief Tests ensure_dbt_setup skips initialization if manifest.json exists.
    @param mock_waid_env Mocked environment fixture.
    @return None
    """
    target_dir = mock_waid_env.dbt_dir / "target"
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "manifest.json").touch()

    code = ensure_dbt_setup.fn(mock_waid_env)
    assert code == 0


@patch("waid_orchestrate.get_run_logger")
@patch("waid_orchestrate.run_dbt_step")
def test_ensure_dbt_setup_missing_manifest(mock_run_dbt, mock_get_logger, mock_waid_env) -> None:
    """
    @brief Tests ensure_dbt_setup executes deps and compile when manifest is missing.
    @param mock_run_dbt Mocked run_dbt_step task function.
    @param mock_get_logger Mocked Prefect run logger.
    @param mock_waid_env Mocked environment fixture.
    @return None
    """
    mock_run_dbt.return_value = 0
    mock_get_logger.return_value = MagicMock()

    code = ensure_dbt_setup.fn(mock_waid_env)
    assert code == 0
    assert mock_run_dbt.call_count == 2