"""
@file test_waid_03_3_dbt_matches_bias.py
@brief Unit tests for waid_03_3_dbt_matches_bias dbt execution and testing workflows.
@author AF
@date 2026
"""

import pytest
from unittest.mock import MagicMock, patch
from config.boot import WaidBoot, WaidExit
from src.waid_03_3_dbt_matches_bias import main


@patch("src.waid_03_3_dbt_matches_bias.argparse.ArgumentParser.parse_args")
@patch("src.waid_03_3_dbt_matches_bias.run_dbt_command")
@patch("src.waid_03_3_dbt_matches_bias.WaidBoot")
def test_matches_bias_success(mock_waid_boot_cls, mock_run_dbt, mock_parse_args):
    """Test successful run and test of matched bias dbt models without period."""
    env = MagicMock()
    env.db.int_matches_bias = "int_matches_bias_model"
    env.waid_exit.SUCCESS = 0
    mock_waid_boot_cls.return_value = env

    mock_parse_args.return_value = MagicMock(period=None)
    mock_run_dbt.return_value = 0

    exit_code = main()
    assert exit_code == 0
    assert mock_run_dbt.call_count == 2
    mock_run_dbt.assert_any_call(["dbt", "run", "--select", "int_matches_bias_model"], env, period=None)
    mock_run_dbt.assert_any_call(["dbt", "test", "--select", "int_matches_bias_model"], env, period=None)


@patch("src.waid_03_3_dbt_matches_bias.argparse.ArgumentParser.parse_args")
@patch("src.waid_03_3_dbt_matches_bias.run_dbt_command")
@patch("src.waid_03_3_dbt_matches_bias.WaidBoot")
def test_matches_bias_run_failure(mock_waid_boot_cls, mock_run_dbt, mock_parse_args):
    """Test non-blocking return code when dbt run fails for matched bias datasets."""
    env = MagicMock()
    env.db.int_matches_bias = "int_matches_bias_model"
    env.waid_exit.SUCCESS = 0
    mock_waid_boot_cls.return_value = env

    mock_parse_args.return_value = MagicMock(period="2026-09")
    mock_run_dbt.return_value = 1

    exit_code = main()
    assert exit_code == 1
    mock_run_dbt.assert_called_once_with(["dbt", "run", "--select", "int_matches_bias_model"], env, period="2026-09")