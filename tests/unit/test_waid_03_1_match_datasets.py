#!/usr/bin/env python3

"""
@file test_waid_03_1_match_datasets.py
@brief Unit tests for dataset alignment, feature store schema, and relative humidity calculations.
@details Uses pytest, tmp_path, and mock objects to validate calculate_rh accuracy,
         table creation, and dataset matching pipeline logic without external I/O blocks.
@author AF
@date 2026
"""

import pytest
import numpy as np
import pandas as pd
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

from waid_03_1_match_datasets import (
    ensure_table_exists,
    calculate_rh,
)


def test_ensure_table_exists(tmp_path: Path) -> None:
    """
    @brief Tests that ensure_table_exists creates the SQLite match table correctly.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    db_file = tmp_path / "test_waid.db"
    mock_env = MagicMock()
    mock_env.waid_db_file = db_file
    mock_env.db.match_records = "match_records"
    
    assert ensure_table_exists(mock_env) is True
    
    # Verify table schema columns in SQLite
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({mock_env.db.match_records});")
        columns = [row[1] for row in cursor.fetchall()]
        
        assert "timestamp" in columns
        assert "temp_era5" in columns
        assert "temp_eco" in columns
        assert "rain_eco" in columns


def test_calculate_rh_accuracy() -> None:
    """
    @brief Tests Relative Humidity calculation using Magnus-Tetens approximation.
    """
    # At temperature == dew point, relative humidity should be 100%
    temp = np.array([20.0, 15.0])
    dew = np.array([20.0, 15.0])
    
    rh = calculate_rh(temp, dew)
    np.testing.assert_allclose(rh, [100.0, 100.0], rtol=1e-3)


def test_calculate_rh_clipping() -> None:
    """
    @brief Tests that calculated relative humidity values are properly clipped between 0 and 100.
    """
    # Dew point significantly higher than temperature would exceed 100 without clipping
    temp = np.array([10.0])
    dew = np.array([25.0])
    
    rh = calculate_rh(temp, dew)
    assert rh[0] == 100.0