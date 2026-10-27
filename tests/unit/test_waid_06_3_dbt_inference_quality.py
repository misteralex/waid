"""
@file test_waid_06_3_dbt_inference_quality.py
@brief Unit tests for waid_06_3_dbt_inference_quality table checks and dbt execution workflows.
@author AF
@date 2026
"""

import pytest
from unittest.mock import MagicMock, patch, call
from config.boot import WaidBoot, WaidExit
from src.waid_06_3_dbt_inference_quality import main


@patch("src.waid_06_3_dbt_inference_quality.check_db_table_exists")
@patch("src.waid_06_3_dbt_inference_quality.argparse.ArgumentParser.parse_args")
@patch("src.waid_06_3_dbt_inference_quality.run_dbt_command")
@patch("src.waid_06_3_dbt_inference_quality.WaidBoot")
def test_inference_quality_success(mock_waid_boot_cls, mock_run_dbt, mock_parse_args, mock_check_table):
    """
    @brief Test successful table check and dbt run execution with full-refresh for inference quality.
    @param mock_waid_boot_cls Mocked WaidBoot class.
    @param mock_run_dbt Mocked run_dbt_command function.
    @param mock_parse_args Mocked parse_args function.
    @param mock_check_table Mocked check_db_table_exists function.
    """
    env = MagicMock()
    env.db.inference_quality = "inference_quality_model"
    env.waid_exit.SUCCESS = 0
    mock_waid_boot_cls.return_value = env

    mock_check_table.return_value = True
    mock_parse_args.return_value = MagicMock(period=None)
    mock_run_dbt.return_value = 0

    exit_code = main()
    assert exit_code == 0
    mock_check_table.assert_called_once_with(env, "inference_quality_model")
    
    assert mock_run_dbt.call_count == 2
    expected_calls = [
        call(["dbt", "run", "--select", "inference_quality_model", "--full-refresh"], env, period=None),
        call(["dbt", "test", "--select", "inference_quality_model"], env, period=None)
    ]
    mock_run_dbt.assert_has_calls(expected_calls)


@patch("src.waid_06_3_dbt_inference_quality.check_db_table_exists")
@patch("src.waid_06_3_dbt_inference_quality.argparse.ArgumentParser.parse_args")
@patch("src.waid_06_3_dbt_inference_quality.run_dbt_command")
@patch("src.waid_06_3_dbt_inference_quality.WaidBoot")
def test_inference_quality_table_missing_warning(mock_waid_boot_cls, mock_run_dbt, mock_parse_args, mock_check_table):
    """
    @brief Test non-blocking warning logging when inference quality table is missing before running dbt.
    @param mock_waid_boot_cls Mocked WaidBoot class.
    @param mock_run_dbt Mocked run_dbt_command function.
    @param mock_parse_args Mocked parse_args function.
    @param mock_check_table Mocked check_db_table_exists function.
    """
    env = MagicMock()
    env.db.inference_quality = "inference_quality_model"
    env.waid_exit.SUCCESS = 0
    mock_waid_boot_cls.return_value = env

    mock_check_table.return_value = False
    mock_parse_args.return_value = MagicMock(period="2026-09")
    mock_run_dbt.return_value = 0

    exit_code = main()
    assert exit_code == 0
    mock_check_table.assert_called_once_with(env, "inference_quality_model")
    
    assert mock_run_dbt.call_count == 2
    expected_calls = [
        call(["dbt", "run", "--select", "inference_quality_model", "--full-refresh"], env, period="2026-09"),
        call(["dbt", "test", "--select", "inference_quality_model"], env, period="2026-09")
    ]
    mock_run_dbt.assert_has_calls(expected_calls)