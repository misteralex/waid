"""
@file test_waid_02_1_dbt_sync.py
@brief Unit tests for waid_02_1_dbt_sync database initialization and dbt sequence workflows.
@author AF
@date 2026
"""

import pytest
from unittest.mock import MagicMock, patch
from config.boot import WaidBoot, WaidExit
from src.waid_02_1_dbt_sync import _check_main_database, waid_sync_dbt_clean


def test_check_main_database_success():
    """Test successful database initialization."""
    env = MagicMock()
    env.waid_db_file = ":memory:"
    env.db.init_main_database.return_value = 0
    env.waid_exit.SUCCESS = 0

    exit_code = _check_main_database(env)
    assert exit_code == 0
    env.db.init_main_database.assert_called_once_with(":memory:")


def test_check_main_database_already_exists():
    """Test database initialization when database already exists."""
    env = MagicMock()
    env.waid_db_file = ":memory:"
    env.db.init_main_database.return_value = 8  # DB_ALREADY_EXISTS code
    env.waid_exit.DB_ALREADY_EXISTS = 8
    env.waid_exit.SUCCESS = 0

    exit_code = _check_main_database(env)
    assert exit_code == 0


@patch("src.waid_02_1_dbt_sync.run_dbt_command")
def test_waid_sync_dbt_clean(mock_run_dbt):
    """Test dbt clean execution wrapper."""
    env = MagicMock()
    mock_run_dbt.return_value = 0

    exit_code = waid_sync_dbt_clean(env)
    assert exit_code == 0
    mock_run_dbt.assert_called_once_with(["dbt", "clean"], env)