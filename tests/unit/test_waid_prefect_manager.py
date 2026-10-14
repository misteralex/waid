"""
@file test_waid_prefect_manager.py
@brief Unit tests for waid_prefect_manager.py workflow lifecycle manager.
@author AF
@date 2026
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import httpx

from waid_prefect_manager import (
    get_subprocess_env,
    generate_prefect_yaml,
    ensure_prefect_server,
    ensure_work_pool,
    run_deployment,
)


@pytest.fixture
def mock_waid_boot() -> MagicMock:
    """
    @brief Fixture providing a mock WaidBoot instance for Prefect manager tests.
    @return MagicMock configured WaidBoot instance.
    """
    boot = MagicMock()
    boot.auto_backfill = False
    boot.deployment_name = "waid-incremental-production"
    boot.entrypoint = "waid_orchestrate.py:waid_main_flow"
    boot.work_pool = "default-agent-pool"
    boot.flow_name = "WAID Main Orchestrator Flow"
    return boot


def test_get_subprocess_env(monkeypatch) -> None:
    """
    @brief Tests that get_subprocess_env populates Prefect API and home environment variables correctly.
    @param monkeypatch Pytest monkeypatch fixture.
    @return None
    """
    monkeypatch.delenv("PREFECT_API_URL", raising=False)
    monkeypatch.delenv("PREFECT_HOME", raising=False)

    env_vars = get_subprocess_env()

    assert env_vars["PREFECT_API_URL"] == "http://127.0.0.1:4200/api"
    assert env_vars["PREFECT_HOME"] == "/tmp/prefect"


def test_generate_prefect_yaml(tmp_path, mock_waid_boot) -> None:
    """
    @brief Tests dynamic generation of prefect.yaml configuration file.
    @param tmp_path Pytest temporary directory fixture.
    @param mock_waid_boot Mock WaidBoot fixture.
    @return None
    """
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        cli_args = MagicMock()
        cli_args.auto_backfill = False
        cli_args.period = "2026-06"
        cli_args.skip_ingestion = True

        yaml_path = generate_prefect_yaml(mock_waid_boot, cli_args)

        assert yaml_path.exists()
        content = yaml_path.read_text(encoding="utf-8")
        assert "waid-project" in content
        assert "waid-incremental-production" in content
        assert "2026-06" in content
        assert "skip_ingestion: true" in content or "skip_ingestion: True" in content
    finally:
        os.chdir(original_cwd)


@patch("waid_prefect_manager.httpx.get")
def test_ensure_prefect_server_already_active(mock_httpx_get) -> None:
    """
    @brief Tests ensure_prefect_server returns True immediately if server health check passes.
    @param mock_httpx_get Mocked httpx.get call.
    @return None
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_get.return_value = mock_response

    is_active = ensure_prefect_server(port=4200, timeout=1)
    assert is_active is True
    mock_httpx_get.assert_called_once()


@patch("waid_prefect_manager.subprocess.run")
@patch("waid_prefect_manager.subprocess.Popen")
@patch("waid_prefect_manager.httpx.get")
def test_ensure_prefect_server_starts_background(mock_httpx_get, mock_popen, mock_subprocess_run) -> None:
    """
    @brief Tests ensure_prefect_server starts background server process when health check initially fails.
    @param mock_httpx_get Mocked httpx.get call.
    @param mock_popen Mocked subprocess.Popen call.
    @param mock_subprocess_run Mocked subprocess.run call (for database upgrade).
    @return None
    """
    mock_response_success = MagicMock()
    mock_response_success.status_code = 200

    mock_httpx_get.side_effect = [
        httpx.RequestError("Connection refused"),
        mock_response_success,
    ]

    mock_process_instance = MagicMock()
    mock_process_instance.poll.return_value = None
    mock_popen.return_value = mock_process_instance

    mock_subprocess_run.return_value = MagicMock(returncode=0)

    is_active = ensure_prefect_server(port=4200, timeout=1)
    assert is_active is True
    mock_popen.assert_called_once()


@patch("waid_prefect_manager.subprocess.run")
def test_ensure_work_pool_success(mock_subprocess_run, mock_waid_boot) -> None:
    """
    @brief Tests ensure_work_pool executes work-pool creation correctly.
    @param mock_subprocess_run Mocked subprocess.run call.
    @param mock_waid_boot Mock WaidBoot fixture.
    @return None
    """
    mock_subprocess_run.return_value = MagicMock(returncode=0)

    ensure_work_pool(mock_waid_boot)
    mock_subprocess_run.assert_called_once()
    args_called = mock_subprocess_run.call_args[0][0]
    assert "work-pool" in args_called
    assert "create" in args_called
    assert "default-agent-pool" in args_called


@patch("waid_prefect_manager.subprocess.run")
def test_run_deployment_success(mock_subprocess_run) -> None:
    """
    @brief Tests run_deployment invokes 'prefect deploy --all' successfully.
    @param mock_subprocess_run Mocked subprocess.run call.
    @return None
    """
    mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="Deployed successfully", stderr="")

    run_deployment()
    mock_subprocess_run.assert_called_once()
    assert "--all" in mock_subprocess_run.call_args[0][0]