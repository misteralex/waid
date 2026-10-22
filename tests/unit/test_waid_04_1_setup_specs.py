#!/usr/bin/env python3

"""
@file test_waid_04_2_setup_specs.py
@brief Unit tests for hardware sensor resolution profiling and metadata updates.
@details Uses pytest, tmp_path, and mock objects to validate table schema extensions,
         resolution estimation logic, and database updates without external dependencies.
@author AF
@date 2026
"""

import pytest
import sqlite3
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock, patch

from waid_04_2_setup_specs import (
    ensure_sensor_specs_column,
    estimate_mode_resolution,
    update_station_specs,
)


def test_ensure_sensor_specs_column(tmp_path: Path) -> None:
    """
    @brief Tests that ensure_sensor_specs_column adds the column if missing.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    db_file = tmp_path / "test_waid.db"
    
    # Setup initial station_metadata table without sensor_specs column
    with sqlite3.connect(db_file) as conn:
        conn.execute("""
            CREATE TABLE station_metadata (
                station_id TEXT PRIMARY KEY,
                latitude REAL,
                longitude REAL
            );
        """)
        conn.commit()

    mock_env = MagicMock()
    mock_env.waid_db_file = db_file
    mock_env.db.station_metadata = "station_metadata"

    ensure_sensor_specs_column(mock_env)

    # Verify column exists
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(station_metadata);")
        columns = [row[1] for row in cursor.fetchall()]
        assert "sensor_specs" in columns


def test_estimate_mode_resolution() -> None:
    """
    @brief Tests the estimation of sensor resolution using statistical mode of unique differences.
    """
    # Create a series with a consistent step of 0.5
    data = np.arange(0, 50, 0.5)
    series = pd.Series(data)

    res = estimate_mode_resolution(series)
    assert res == 0.5


def test_estimate_mode_resolution_insufficient_data() -> None:
    """
    @brief Tests that resolution estimation returns None when data points are insufficient.
    """
    series = pd.Series([1.0, 1.5, 2.0])
    res = estimate_mode_resolution(series)
    assert res is None


def test_update_station_specs(tmp_path: Path) -> None:
    """
    @brief Tests persisting sensor specifications JSON into the station_metadata table.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    db_file = tmp_path / "test_waid.db"
    
    with sqlite3.connect(db_file) as conn:
        conn.execute("""
            CREATE TABLE station_metadata (
                station_id TEXT PRIMARY KEY,
                sensor_specs TEXT
            );
        """)
        conn.execute("INSERT INTO station_metadata (station_id, sensor_specs) VALUES ('STN_01', NULL);")
        conn.commit()

    mock_env = MagicMock()
    mock_env.waid_db_file = db_file
    mock_env.ecowitt_station_id = "STN_01"
    mock_env.db.station_metadata = "station_metadata"

    specs = {"ecowitt_temp": {"resolution": 0.1, "deadband": 0.0}}
    update_station_specs(mock_env, specs)

    # Verify JSON was correctly saved
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sensor_specs FROM station_metadata WHERE station_id = 'STN_01';")
        row = cursor.fetchone()
        assert row is not None
        assert "ecowitt_temp" in row[0]