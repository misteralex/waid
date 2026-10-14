#!/usr/bin/env python3

"""
@file test_waid_scheduler_lab.py
@brief Unit tests for waid_scheduler_lab.py continuous scheduler and retroactive simulator.
@author AF
@date 2026
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from waid_scheduler_lab import (
    check_initial_setup_needed,
    run_pipeline,
    ping_streamlit,
    clean_target_range,
)


@pytest.fixture
def mock_scheduler_env(tmp_path) -> MagicMock:
    """
    @brief Fixture providing a mock WaidBoot configuration environment for scheduler tests.
    @param tmp_path Pytest fixture for temporary directory.
    @return MagicMock configured environment instance.
    """
    db_path = tmp_path / "waid.db"
    deploy_db_path = tmp_path / "deploy.db"

    env = MagicMock()
    env.waid_db_file = str(db_path)
    env.deploy_db_file = str(deploy_db_path)
    env.streamlit_url = "https://waid-analytics.streamlit.app"
    env.tz_timezone = "UTC"
    env.retro_cleanup = True
    env.mock_interval_hours = 1
    env.scheduled_interval_hours = 1
    env.backfill_begin_period = datetime(2026, 1, 1)
    env.backfill_end_period = datetime(2026, 6, 1)
    return env


def test_check_initial_setup_needed_missing(mock_scheduler_env) -> None:
    """
    @brief Tests check_initial_setup_needed returns True when database does not exist.
    @param mock_scheduler_env Mocked environment fixture.
    @return None
    """
    assert check_initial_setup_needed(mock_scheduler_env) is True


def test_check_initial_setup_needed_exists(mock_scheduler_env) -> None:
    """
    @brief Tests check_initial_setup_needed returns False when database exists.
    @param mock_scheduler_env Mocked environment fixture.
    @return None
    """
    db_path = Path(mock_scheduler_env.waid_db_file)
    db_path.touch()
    assert check_initial_setup_needed(mock_scheduler_env) is False


@patch("waid_scheduler_lab.subprocess.run")
def test_run_pipeline_incremental(mock_subprocess_run, monkeypatch) -> None:
    """
    @brief Tests run_pipeline executes incremental mode correctly with default or mock period.
    @param mock_subprocess_run Mocked subprocess.run call.
    @param monkeypatch Pytest monkeypatch fixture.
    @return None
    """
    monkeypatch.delenv("WAID_RETRO_NOW", raising=False)
    mock_subprocess_run.return_value = MagicMock(returncode=0)

    code = run_pipeline("incremental")
    assert code == 0
    mock_subprocess_run.assert_called_once()
    args_called = mock_subprocess_run.call_args[0][0]
    assert "waid_orchestrate_lab.py" in args_called
    assert "--run-mode" in args_called
    assert "incremental" in args_called
    assert "--period" in args_called


@patch("waid_scheduler_lab.websocket.create_connection")
@patch("waid_scheduler_lab.requests.get")
def test_ping_streamlit_success(mock_requests_get, mock_ws_create, mock_scheduler_env) -> None:
    """
    @brief Tests ping_streamlit successfully performs HTTP request and WebSocket connection.
    @param mock_requests_get Mocked requests.get function.
    @param mock_ws_create Mocked websocket.create_connection function.
    @param mock_scheduler_env Mocked environment fixture.
    @return None
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "OK"
    mock_requests_get.return_value = mock_response

    ping_streamlit(mock_scheduler_env, timeout=5)

    mock_requests_get.assert_called_once()
    mock_ws_create.assert_called_once()


def test_clean_target_range(mock_scheduler_env) -> None:
    """
    @brief Tests clean_target_range correctly deletes records from local lab and deploy databases.
    @param mock_scheduler_env Mocked environment fixture.
    @return None
    """
    # Setup mock database attributes
    mock_scheduler_env.db = MagicMock()
    mock_scheduler_env.db.inference_forecast = "inference_forecast"
    mock_scheduler_env.db.inference_stats = "inference_stats"
    mock_scheduler_env.db.inference_quality = "inference_quality"

    # Create lab database with table and test row
    lab_db = Path(mock_scheduler_env.waid_db_file)
    with sqlite3.connect(lab_db) as conn:
        conn.execute("CREATE TABLE inference_forecast (timestamp TEXT)")
        conn.execute("INSERT INTO inference_forecast VALUES ('2026-06-01 12:00:00')")
        conn.commit()

    # Create deploy database with table and test row
    deploy_db = Path(mock_scheduler_env.deploy_db_file)
    with sqlite3.connect(deploy_db) as conn:
        conn.execute("CREATE TABLE public_forecasts (timestamp TEXT, created_at TEXT)")
        conn.execute("INSERT INTO public_forecasts VALUES ('2026-06-01 12:00:00', '2026-06-01 12:00:00')")
        conn.commit()

    start_dt = datetime(2026, 6, 1, 10, 0, 0)
    end_dt = datetime(2026, 6, 1, 14, 0, 0)

    clean_target_range(mock_scheduler_env, start_dt, end_dt)

    # Verify records were cleaned
    with sqlite3.connect(lab_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM inference_forecast")
        assert cursor.fetchone()[0] == 0

    with sqlite3.connect(deploy_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM public_forecasts")
        assert cursor.fetchone()[0] == 0