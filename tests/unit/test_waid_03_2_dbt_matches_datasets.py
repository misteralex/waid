"""
@file test_waid_03_2_dbt_matches_datasets.py
@brief Unit tests for waid_03_2_dbt_matches_datasets dbt execution and testing workflows.
@author AF
@date 2026
"""

import pytest
from unittest.mock import MagicMock, patch
from config.boot import WaidBoot, WaidExit
from src.waid_03_2_dbt_matches_datasets import main


@patch("src.waid_03_2_dbt_matches_datasets.argparse.ArgumentParser.parse_args")
@patch("src.waid_03_2_dbt_matches_datasets.run_dbt_command")
@patch("src.waid_03_2_dbt_matches_datasets.WaidBoot")
def test_matches_datasets_success(mock_waid_boot_cls, mock_run_dbt, mock_parse_args):
    """Test successful run and test of matched datasets dbt source models without period."""
    env = MagicMock()
    env.db.match_records = "match_records_table"
    env.waid_exit.SUCCESS = 0
    mock_waid_boot_cls.return_value = env

    mock_parse_args.return_value = MagicMock(period=None)
    mock_run_dbt.return_value = 0

    exit_code = main()
    assert exit_code == 0
    assert mock_run_dbt.call_count == 2
    mock_run_dbt.assert_any_call(["dbt", "run", "--select", "source:external_raw.match_records_table"], env, period=None)
    mock_run_dbt.assert_any_call(["dbt", "test", "--select", "source:external_raw.match_records_table"], env, period=None)


@patch("src.waid_03_2_dbt_matches_datasets.argparse.ArgumentParser.parse_args")
@patch("src.waid_03_2_dbt_matches_datasets.run_dbt_command")
@patch("src.waid_03_2_dbt_matches_datasets.WaidBoot")
def test_matches_datasets_test_failure(mock_waid_boot_cls, mock_run_dbt, mock_parse_args):
    """Test non-blocking return code when dbt test fails for matched datasets."""
    env = MagicMock()
    env.db.match_records = "match_records_table"
    env.waid_exit.SUCCESS = 0
    mock_waid_boot_cls.return_value = env

    mock_parse_args.return_value = MagicMock(period="2026-09")
    # First call (run) succeeds (0), second call (test) fails with error code 1
    mock_run_dbt.side_effect = [0, 1]

    exit_code = main()
    assert exit_code == 1
    assert mock_run_dbt.call_count == 2
    mock_run_dbt.assert_any_call(["dbt", "run", "--select", "source:external_raw.match_records_table"], env, period="2026-09")
    mock_run_dbt.assert_any_call(["dbt", "test", "--select", "source:external_raw.match_records_table"], env, period="2026-09")