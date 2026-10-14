#!/usr/bin/env python3

"""
@file test_waid_06_4_inference_quality.py
@brief Unit tests for the WAID inference quality check script.
@details Uses pytest, sqlite3, and mock objects to validate database connectivity,
         inference_quality table/view verification, and count checks.
@author AF
@date 2026
"""

import pytest
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

from waid_06_4_inference_quality import main


def test_inference_quality_success(tmp_path: Path) -> None:
    """
    @brief Tests successful execution of quality check when inference_quality table exists.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    db_file = tmp_path / "test_waid_quality.db"
    
    with sqlite3.connect(db_file) as conn:
        conn.execute("""
            CREATE TABLE inference_quality (
                id INTEGER PRIMARY KEY,
                metric_name TEXT,
                value REAL
            );
        """)
        conn.execute("INSERT INTO inference_quality (metric_name, value) VALUES ('mse', 0.123);")
        conn.commit()

    mock_exit = MagicMock()
    mock_exit.SUCCESS = 0
    mock_exit.INTERNAL_ERROR = 1

    mock_env = MagicMock()
    mock_env.waid_db_file = db_file
    mock_env.waid_exit = mock_exit
    mock_env.retro_now = None
    mock_env.db.inference_quality = "inference_quality"
    
    with patch("waid_06_4_inference_quality.WaidBoot", return_value=mock_env):
        with patch("sys.argv", ["waid_06_4_inference_quality.py"]):
            exit_code = main()
            assert exit_code == 0


def test_inference_quality_missing_table(tmp_path: Path) -> None:
    """
    @brief Tests execution when inference_quality table/view is missing.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    db_file = tmp_path / "test_waid_quality.db"
    
    # Create empty database without inference_quality table
    with sqlite3.connect(db_file) as conn:
        conn.commit()

    mock_exit = MagicMock()
    mock_exit.SUCCESS = 0
    mock_exit.INTERNAL_ERROR = 1

    mock_env = MagicMock()
    mock_env.waid_db_file = db_file
    mock_env.waid_exit = mock_exit
    mock_env.retro_now = None

    with patch("waid_06_4_inference_quality.WaidBoot", return_value=mock_env):
        with patch("sys.argv", ["waid_06_4_inference_quality.py"]):
            exit_code = main()
            assert exit_code == 0