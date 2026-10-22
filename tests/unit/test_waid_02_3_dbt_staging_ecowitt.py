"""
@file test_waid_02_3_dbt_staging_ecowitt.py
@brief Unit tests for waid_02_3_dbt_staging_ecowitt dbt execution and testing workflows.
@author AF
@date 2026
"""

import pytest
from unittest.mock import MagicMock, patch
from config.boot import WaidBoot, WaidExit
from src.waid_02_3_dbt_staging_ecowitt import main


@patch("src.waid_02_3_dbt_staging_ecowitt.argparse.ArgumentParser.parse_args")
@patch("src.waid_02_3_dbt_staging_ecowitt.run_dbt_command")
@patch("src.waid_02_3_dbt_staging_ecowitt.WaidBoot")
def test_staging_ecowitt_success(mock_waid_boot_cls, mock_run_dbt, mock_parse_args):
    """Test successful run and test of dbt staging ecowitt models without period."""
    env = MagicMock()
    env.db.stg_ecowitt = "stg_ecowitt_model"
    env.waid_exit.SUCCESS = 0
    mock_waid_boot_cls.return_value = env

    mock_parse_args.return_value = MagicMock(period=None)
    mock_run_dbt.return_value = 0

    exit_code = main()
    assert exit_code == 0
    assert mock_run_dbt.call_count == 2
    mock_run_dbt.assert_any_call(["dbt", "run", "--select", "stg_ecowitt_model"], env, period=None)
    mock_run_dbt.assert_any_call(["dbt", "test", "--select", "stg_ecowitt_model"], env, period=None)


@patch("src.waid_02_3_dbt_staging_ecowitt.argparse.ArgumentParser.parse_args")
@patch("src.waid_02_3_dbt_staging_ecowitt.run_dbt_command")
@patch("src.waid_02_3_dbt_staging_ecowitt.WaidBoot")
def test_staging_ecowitt_run_failure(mock_waid_boot_cls, mock_run_dbt, mock_parse_args):
    """Test non-blocking return code when dbt run fails."""
    env = MagicMock()
    env.db.stg_ecowitt = "stg_ecowitt_model"
    env.waid_exit.SUCCESS = 0
    mock_waid_boot_cls.return_value = env

    mock_parse_args.return_value = MagicMock(period="2026-09")
    # First call (run) returns error code 1, second call shouldn't happen
    mock_run_dbt.return_value = 1

    exit_code = main()
    assert exit_code == 1
    mock_run_dbt.assert_called_once_with(["dbt", "run", "--select", "stg_ecowitt_model"], env, period="2026-09")