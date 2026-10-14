#!/usr/bin/env python3

"""
@file test_waid_06_1_inference_forecast.py
@brief Unit tests for the 6-hour meteorological inference engine and schema verification.
@details Uses pytest, sqlite3, numpy, and mocks to validate cyclic time feature encoding,
         inference tensor creation, and inference_forecast table initialization.
@author AF
@date 2026
"""

import pytest
import numpy as np
import pandas as pd
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

from waid_06_1_inference_forecast import (
    add_cyclic_time_features,
    build_inference_tensor,
    ensure_inference_forecast_table,
)


def test_add_cyclic_time_features() -> None:
    """
    @brief Tests the correct encoding of diurnal and seasonal cyclic features from timestamps.
    """
    df = pd.DataFrame({
        "timestamp": ["2026-06-01 12:00:00", "2026-01-01 00:00:00"]
    })
    
    df_cyclic = add_cyclic_time_features(df)
    
    assert "hour_sin" in df_cyclic.columns
    assert "hour_cos" in df_cyclic.columns
    assert "doy_sin" in df_cyclic.columns
    assert "doy_cos" in df_cyclic.columns
    
    # At 12:00 UTC, hour_sin should be very close to 0.0 and hour_cos close to -1.0
    assert pytest.approx(df_cyclic.loc[0, "hour_sin"], abs=1e-5) == 0.0
    assert pytest.approx(df_cyclic.loc[0, "hour_cos"], abs=1e-5) == -1.0


def test_ensure_inference_forecast_table(tmp_path: Path) -> None:
    """
    @brief Tests that ensure_inference_forecast_table creates and updates the inference table schema.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    db_file = tmp_path / "test_waid_inference.db"
    db_table = "inference_forecast"
    
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        ensure_inference_forecast_table(db_table, cursor)
        conn.commit()

    # Verify table schema columns in SQLite
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(inference_forecast);")
        columns = [row[1] for row in cursor.fetchall()]
        
        assert "timestamp" in columns
        assert "model_version" in columns
        assert "pred_temp" in columns
        assert "diff_temp" in columns
        assert "actual_temp" in columns
        assert "historical_bias_temp" in columns
        assert "drift_vs_bias" in columns


def test_build_inference_tensor() -> None:
    """
    @brief Tests construction of the 3D multi-feature tensor for model inference.
    """
    # Create 24 rows of dummy raw telemetry matching expected features
    features = [
        "ecowitt_temp", "ecowitt_pres", "ecowitt_rh", 
        "ecowitt_wind", "ecowitt_solar", "ecowitt_rain"
    ]
    data = np.random.rand(24, len(features))
    df_raw = pd.DataFrame(data, columns=features)
    df_raw["timestamp"] = pd.date_range(start="2026-06-01", periods=24, freq="h").strftime("%Y-%m-%d %H:%M:%S")

    mock_env = MagicMock()
    mock_env.ecowitt_latitude = 45.0
    mock_env.ecowitt_longitude = 9.0
    mock_env.n_input_features = 11
    
    # 6 raw + 4 cyclic + 1 theo_solar = 11 features
    mock_env.input_features_match = [
        "ecowitt_temp", "ecowitt_pres", "ecowitt_rh", 
        "ecowitt_wind", "ecowitt_solar", "ecowitt_rain",
        "hour_sin", "hour_cos", "doy_sin", "doy_cos", "theo_solar"
    ]

    tensor = build_inference_tensor(mock_env, df_raw)
    
    # Check shape: (batch=1, timesteps=24, features=11)
    assert tensor.shape == (1, 24, 11)
    assert not np.isnan(tensor).any()