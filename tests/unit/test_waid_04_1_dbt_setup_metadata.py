"""
@file test_waid_04_1_dbt_setup_metadata.py
@brief Unit tests for waid_04_1_dbt_setup_metadata dbt setup execution workflows.
@author AF
@date 2026
"""

import pytest
from unittest.mock import MagicMock, patch, call
from config.boot import WaidBoot, WaidExit
from src.waid_04_1_dbt_setup_metadata import main


@patch("src.waid_04_1_dbt_setup_metadata.argparse.ArgumentParser.parse_args")
@patch("src.waid_04_1_dbt_setup_metadata.run_dbt_command")
@patch("src.waid_04_1_dbt_setup_metadata.WaidBoot")
def test_setup_metadata_success(mock_waid_boot_cls, mock_run_dbt, mock_parse_args):
    """
    @brief Test successful run of dbt station metadata setup with full-refresh and without period.
    @param mock_waid_boot_cls Mocked WaidBoot class.
    @param mock_run_dbt Mocked run_dbt_command function.
    @param mock_parse_args Mocked parse_args function.
    """
    env = MagicMock()
    env.db.station_metadata = "station_metadata_model"
    env.waid_exit.SUCCESS = 0
    mock_waid_boot_cls.return_value = env

    mock_parse_args.return_value = MagicMock(period=None)
    mock_run_dbt.return_value = 0

    exit_code = main()
    assert exit_code == 0
    assert mock_run_dbt.call_count == 2
    
    expected_calls = [
        call(["dbt", "run", "--select", "station_metadata_model", "--full-refresh"], env, period=None),
        call(["dbt", "test", "--select", "station_metadata_model"], env, period=None)
    ]
    mock_run_dbt.assert_has_calls(expected_calls)


@patch("src.waid_04_1_dbt_setup_metadata.argparse.ArgumentParser.parse_args")
@patch("src.waid_04_1_dbt_setup_metadata.run_dbt_command")
@patch("src.waid_04_1_dbt_setup_metadata.WaidBoot")
def test_setup_metadata_failure(mock_waid_boot_cls, mock_run_dbt, mock_parse_args):
    """
    @brief Test non-blocking return code when dbt run fails for station metadata setup.
    @param mock_waid_boot_cls Mocked WaidBoot class.
    @param mock_run_dbt Mocked run_dbt_command function.
    @param mock_parse_args Mocked parse_args function.
    """
    env = MagicMock()
    env.db.station_metadata = "station_metadata_model"
    env.waid_exit.SUCCESS = 0
    mock_waid_boot_cls.return_value = env

    mock_parse_args.return_value = MagicMock(period="2026-09")
    mock_run_dbt.return_value = 1

    exit_code = main()
    assert exit_code == 1
    
    # When first call fails (dbt run)
    assert mock_run_dbt.call_count == 1
    mock_run_dbt.assert_called_once_with(
        ["dbt", "run", "--select", "station_metadata_model", "--full-refresh"],
        env,
        period="2026-09"
    )