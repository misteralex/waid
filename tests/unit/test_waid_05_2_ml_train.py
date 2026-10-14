#!/usr/bin/env python3

"""
@file test_waid_05_2_ml_train.py
@brief Unit tests for machine learning model training, registry schema, and denormalization.
@details Uses pytest, sqlite3, and scikit-learn to validate denormalize_predictions accuracy,
         model registry initialization, and available period detection without external hardware.
@author AF
@date 2026
"""

import pytest
import numpy as np
import pandas as pd
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch
from sklearn.preprocessing import StandardScaler

from waid_05_2_ml_train import (
    denormalize_predictions,
    ensure_model_registry_schema,
    get_available_periods,
)


def test_denormalize_predictions_2d() -> None:
    """
    @brief Tests 2D predictions denormalization using a fitted StandardScaler.
    """
    scaler = StandardScaler()
    original_data = np.array([[10.0, 20.0], [30.0, 40.0], [50.0, 60.0]])
    scaler.fit(original_data)
    
    scaled_data = scaler.transform(original_data)
    denorm_data = denormalize_predictions(scaler, scaled_data)
    
    np.testing.assert_allclose(denorm_data, original_data, rtol=1e-5)


def test_denormalize_predictions_3d() -> None:
    """
    @brief Tests 3D batch predictions denormalization using a fitted StandardScaler.
    """
    scaler = StandardScaler()
    original_2d = np.array([[10.0, 20.0], [30.0, 40.0], [50.0, 60.0], [70.0, 80.0]])
    scaler.fit(original_2d)
    
    # Shape: (batch=2, horizon=2, features=2)
    original_3d = original_2d.reshape(2, 2, 2)
    scaled_3d = scaler.transform(original_3d.reshape(-1, 2)).reshape(2, 2, 2)
    
    denorm_3d = denormalize_predictions(scaler, scaled_3d)
    np.testing.assert_allclose(denorm_3d, original_3d, rtol=1e-5)


def test_ensure_model_registry_schema(tmp_path: Path) -> None:
    """
    @brief Tests that ensure_model_registry_schema creates the ml_model_registry table correctly.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    db_file = tmp_path / "test_waid.db"
    
    # Create required station_metadata parent table for foreign key constraint
    with sqlite3.connect(db_file) as conn:
        conn.execute("""
            CREATE TABLE station_metadata (
                station_id TEXT PRIMARY KEY
            );
        """)
        conn.execute("INSERT INTO station_metadata (station_id) VALUES ('STN_01');")
        conn.commit()

    mock_env = MagicMock()
    mock_env.waid_db_file = db_file
    mock_env.ecowitt_station_id = "STN_01"
    mock_env.db.ml_model_registry = "ml_model_registry"
    mock_env.db.station_metadata = "station_metadata"
    
    ensure_model_registry_schema(mock_env)

    # Verify table schema columns in SQLite
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(ml_model_registry);")
        columns = [row[1] for row in cursor.fetchall()]
        
        assert "model_version" in columns
        assert "station_id" in columns
        assert "metrics_mse" in columns
        assert "is_active" in columns


def test_get_available_periods(tmp_path: Path) -> None:
    """
    @brief Tests detection and sorting of available training tensor files.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    tensors_dir = tmp_path / "tensors"
    tensors_dir.mkdir()
    
    # Create dummy tensor pkl files
    (tensors_dir / "X_raw_2026_07.pkl").touch()
    (tensors_dir / "X_raw_2026_06.pkl").touch()
    (tensors_dir / "X_raw_2026_08.pkl").touch()

    mock_env = MagicMock()
    mock_env.ml_tensors_dir = tensors_dir

    periods = get_available_periods(mock_env)
    assert periods == ["2026_06", "2026_07", "2026_08"]