"""
@file test_waid_06_3_dbt_inference_quality.py
@brief Unit tests for waid_06_3_dbt_inference_quality table checks and dbt execution workflows.
@author AF
@date 2026
"""

import pytest
from unittest.mock import MagicMock, patch
from config.boot import WaidBoot, WaidExit
from src.waid_06_3_dbt_inference_quality import main


@patch("src.waid_06_3_dbt_inference_quality.check_db_table_exists")
@patch("src.waid_06_3_dbt_inference_quality.argparse.ArgumentParser.parse_args")
@patch("src.waid_06_3_dbt_inference_quality.run_dbt_command")
@patch("src.waid_06_3_dbt_inference_quality.WaidBoot")
def test_inference_quality_success(mock_waid_boot_cls, mock_run_dbt, mock_parse_args, mock_check_table):
    """Test successful table check and dbt run execution with full-refresh for inference quality."""
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
    mock_run_dbt.assert_called_once_with(
        ["dbt", "run", "--select", "inference_quality_model", "--full-refresh"],
        env,
        period=None
    )


@patch("src.waid_06_3_dbt_inference_quality.check_db_table_exists")
@patch("src.waid_06_3_dbt_inference_quality.argparse.ArgumentParser.parse_args")
@patch("src.waid_06_3_dbt_inference_quality.run_dbt_command")
@patch("src.waid_06_3_dbt_inference_quality.WaidBoot")
def test_inference_quality_table_missing_warning(mock_waid_boot_cls, mock_run_dbt, mock_parse_args, mock_check_table):
    """Test non-blocking warning logging when inference quality table is missing before running dbt."""
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
    mock_run_dbt.assert_called_once_with(
        ["dbt", "run", "--select", "inference_quality_model", "--full-refresh"],
        env,
        period="2026-09"
    )