"""
@file test_waid_06_2_dbt_inference_stats.py
@brief Unit tests for waid_06_2_dbt_inference_stats dbt execution and testing workflows.
@author AF
@date 2026
"""

import pytest
from unittest.mock import MagicMock, patch
from config.boot import WaidBoot, WaidExit
from src.waid_06_2_dbt_inference_stats import main


@patch("src.waid_06_2_dbt_inference_stats.argparse.ArgumentParser.parse_args")
@patch("src.waid_06_2_dbt_inference_stats.run_dbt_command")
@patch("src.waid_06_2_dbt_inference_stats.WaidBoot")
def test_inference_stats_success(mock_waid_boot_cls, mock_run_dbt, mock_parse_args):
    """Test successful run and test of dbt inference stats models without period."""
    env = MagicMock()
    env.db.inference_stats = "inference_stats_model"
    env.waid_exit.SUCCESS = 0
    mock_waid_boot_cls.return_value = env

    mock_parse_args.return_value = MagicMock(period=None)
    mock_run_dbt.return_value = 0

    exit_code = main()
    assert exit_code == 0
    assert mock_run_dbt.call_count == 2
    mock_run_dbt.assert_any_call(["dbt", "run", "--select", "inference_stats_model"], env, period=None)
    mock_run_dbt.assert_any_call(["dbt", "test", "--select", "inference_stats_model"], env, period=None)


@patch("src.waid_06_2_dbt_inference_stats.argparse.ArgumentParser.parse_args")
@patch("src.waid_06_2_dbt_inference_stats.run_dbt_command")
@patch("src.waid_06_2_dbt_inference_stats.WaidBoot")
def test_inference_stats_test_failure(mock_waid_boot_cls, mock_run_dbt, mock_parse_args):
    """Test non-blocking return code when dbt test fails for inference stats datasets."""
    env = MagicMock()
    env.db.inference_stats = "inference_stats_model"
    env.waid_exit.SUCCESS = 0
    mock_waid_boot_cls.return_value = env

    mock_parse_args.return_value = MagicMock(period="2026-09")
    mock_run_dbt.side_effect = [0, 1]

    exit_code = main()
    assert exit_code == 1
    assert mock_run_dbt.call_count == 2
    mock_run_dbt.assert_any_call(["dbt", "run", "--select", "inference_stats_model"], env, period="2026-09")
    mock_run_dbt.assert_any_call(["dbt", "test", "--select", "inference_stats_model"], env, period="2026-09")