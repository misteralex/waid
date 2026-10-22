#!/usr/bin/env python3

"""
@file test_waid_02_2_sync_ecowitt.py
@brief Unit tests for the Ecowitt batch aggregator and SQLite synchronizer.
@details Uses pytest, tmp_path, and pandas to validate table schema generation,
         timestamp UTC conversion, and database synchronization logic without external I/O blocks.
@author AF
@date 2026
"""

import pytest
import argparse
from unittest.mock import MagicMock, patch
from pathlib import Path
from datetime import datetime
import pandas as pd
import sqlite3

from waid_02_2_sync_ecowitt import (
    ensure_table_exists,
    process_timestamps_to_utc,
    report_gaps,
    sync_ecowitt_with_db,
)

class TestEcowittSync:
    """
    @brief Test suite for Ecowitt telemetry synchronization and database mapping.
    """

    def test_ensure_table_exists(self, tmp_path: Path) -> None:
        """
        @brief Tests that ensure_table_exists creates the SQLite table and returns the correct column map.
        @param tmp_path Pytest fixture providing a temporary directory.
        """
        db_file = tmp_path / "test_waid.db"
        mock_env = MagicMock()
        mock_env.waid_db_file = db_file
        mock_env.db.ecowitt_records = "ecowitt_data"
        
        column_map = ensure_table_exists(mock_env)
        
        assert "Time" in column_map
        assert column_map["Time"] == "timestamp"
        
        # Verify table exists in SQLite
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ecowitt_data';")
            table_found = cursor.fetchone()
            assert table_found is not None

    def test_process_timestamps_to_utc(self) -> None:
        """
        @brief Tests conversion of local epoch timestamps to standardized UTC strings.
        """
        df = pd.DataFrame({
            "epoch_timestamp": [1785542400],  # Correct epoch for 2026-08-01 00:00:00 UTC
            "timestamp": ["2026-08-01 02:00:00"]
        })
        
        processed_df = process_timestamps_to_utc(df, "Europe/Paris")
        assert processed_df["timestamp"].iloc[0] == "2026-08-01 00:00:00"
        assert processed_df["epoch_timestamp"].iloc[0] == 1785542400

    def test_report_gaps(self) -> None:
        """
        @brief Tests gap detection logic on minute-level timestamps.
        """
        df = pd.DataFrame({
            "timestamp": [
                "2026-08-01 00:00:00",
                "2026-08-01 00:01:00",
                "2026-08-01 00:05:00"  # 3 minutes gap here
            ]
        })
        
        gaps = report_gaps(df, min_gap_min=2)
        assert len(gaps) == 1
        assert gaps["missing_min"].iloc[0] == 3

    @patch("waid_02_2_sync_ecowitt.ensure_table_exists")
    def test_sync_ecowitt_with_db_file_missing(self, mock_ensure: MagicMock, tmp_path: Path) -> None:
        """
        @brief Tests that WError is raised if the target CSV file does not exist.
        @param mock_ensure Mocked schema initialization function.
        @param tmp_path Pytest fixture providing a temporary directory.
        """
        mock_env = MagicMock()
        mock_env.ecowitt_dir = tmp_path
        
        mock_args = argparse.Namespace(
            period=datetime(2026, 8, 1)
        )
        
        with pytest.raises(Exception) as exc_info:
            sync_ecowitt_with_db(mock_env, mock_args, {})
        assert "Source dataset file missing" in str(exc_info.value)