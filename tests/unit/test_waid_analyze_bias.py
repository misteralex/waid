"""
@file test_waid_analyze_bias.py
@brief Unit tests for waid_analyze_bias script.
@author AF
@date 2026
"""

import sqlite3
from datetime import datetime
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from utils.waid_analyze_bias import report_bias_metrics, main


@pytest.fixture
def mock_env() -> MagicMock:
    """
    @brief Fixture providing a mock WaidBoot environment with temporary database and features.
    @return MagicMock configured environment instance.
    """
    env = MagicMock()
    env.waid_exit.SUCCESS = 0
    env.waid_exit.INPUT_FAIL = 1
    env.waid_exit.INTERNAL_ERROR = 2
    env.output_features = [
        {
            "name": "Temperature",
            "unit": "°C",
            "bias_col": "temp_diff",
        }
    ]
    return env


def test_report_bias_metrics_success(tmp_path, mock_env) -> None:
    """
    @brief Tests bias metrics reporting when data is present in the database.
    @param tmp_path Pytest fixture for temporary directory.
    @param mock_env Mock environment fixture.
    @return None
    """
    db_file = tmp_path / "test_waid.db"
    conn = sqlite3.connect(db_file)
    conn.execute(
        """
        CREATE TABLE int_matches_bias (
            timestamp TEXT,
            temp_diff REAL
        )
        """
    )
    conn.execute(
        "INSERT INTO int_matches_bias (timestamp, temp_diff) VALUES ('2026-06-01 12:00:00', 0.5)"
    )
    conn.execute(
        "INSERT INTO int_matches_bias (timestamp, temp_diff) VALUES ('2026-06-01 13:00:00', -0.2)"
    )
    conn.commit()
    conn.close()

    mock_env.waid_db_file = str(db_file)
    period = datetime(2026, 6, 1)

    result = report_bias_metrics(mock_env, period)
    assert result is None


def test_report_bias_metrics_empty(tmp_path, mock_env) -> None:
    """
    @brief Tests bias metrics reporting when no data exists for the requested period.
    @param tmp_path Pytest fixture for temporary directory.
    @param mock_env Mock environment fixture.
    @return None
    """
    db_file = tmp_path / "test_waid.db"
    conn = sqlite3.connect(db_file)
    conn.execute(
        """
        CREATE TABLE int_matches_bias (
            timestamp TEXT,
            temp_diff REAL
        )
        """
    )
    conn.commit()
    conn.close()

    mock_env.waid_db_file = str(db_file)
    period = datetime(2026, 6, 1)

    result = report_bias_metrics(mock_env, period)
    assert result == mock_env.waid_exit.SUCCESS


@patch("utils.waid_analyze_bias.WaidBoot")
@patch("argparse.ArgumentParser.parse_args")
def test_main_missing_arguments(mock_parse_args, mock_waid_boot) -> None:
    """
    @brief Tests main function execution path when arguments are missing or invalid.
    @param mock_parse_args Mocked argument parser.
    @param mock_waid_boot Mocked boot configuration.
    @return None
    """
    env_instance = mock_waid_boot.return_value
    env_instance.waid_exit.INPUT_FAIL = 1

    with patch("sys.argv", ["waid_analyze_bias.py"]):
        exit_code = main()
        assert exit_code == env_instance.waid_exit.INPUT_FAIL