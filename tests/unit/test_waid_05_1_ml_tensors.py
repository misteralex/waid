#!/usr/bin/env python3

"""
@file test_waid_05_1_ml_tensors.py
@brief Unit tests for multi-feature 3D tensor generator and sliding window transformations.
@details Uses pytest, numpy, and pandas to validate temporal embedding calculations,
         sliding window shape consistency, and 3D tensor production without external I/O blocks.
@author AF
@date 2026
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock

from waid_05_1_ml_tensors import (
    compute_temporal_embeddings,
    generate_sliding_window_tensors,
)


def test_compute_temporal_embeddings() -> None:
    """
    @brief Tests that compute_temporal_embeddings appends cyclical and solar features correctly.
    """
    df = pd.DataFrame({
        'timestamp': pd.date_range("2026-06-01 00:00:00", periods=5, freq='1h'),
        'outdoor_temperature_c': [20.0, 20.5, 21.0, 21.5, 22.0],
        'outdoor_humidity': [50.0, 52.0, 48.0, 45.0, 44.0],
    })
    
    mock_env = MagicMock()
    mock_env.ecowitt_latitude = 48.8566
    mock_env.ecowitt_longitude = 2.3522
    
    enriched_df = compute_temporal_embeddings(mock_env, df)
    
    # Verify new features exist
    expected_cols = ['hour_sin', 'hour_cos', 'doy_sin', 'doy_cos', 'theo_solar']
    for col in expected_cols:
        assert col in enriched_df.columns
        
    assert len(enriched_df) == 5


def test_generate_sliding_window_tensors() -> None:
    """
    @brief Tests vectorized 3D tensor generation (X and Y) using sliding windows.
    """
    # Create mock environment matching 6 output features
    mock_env = MagicMock()
    mock_env.output_features = [
        {"standard": "outdoor_temperature_c"},
        {"standard": "abs_pressure_hpa"},
        {"standard": "outdoor_humidity"},
        {"standard": "wind_m_s"},
        {"standard": "solar_rad_w_m2"},
        {"standard": "hourly_rain_mm"},
    ]
    
    lookback = 3
    forecast = 2
    total_rows = 10
    
    df = pd.DataFrame({
        'timestamp': pd.date_range("2026-06-01 00:00:00", periods=total_rows, freq='1h'),
        'outdoor_temperature_c': np.arange(total_rows, dtype=float),
        'abs_pressure_hpa': np.linspace(1013, 1010, total_rows),
        'outdoor_humidity': np.linspace(50, 60, total_rows),
        'wind_m_s': np.zeros(total_rows),
        'solar_rad_w_m2': np.zeros(total_rows),
        'hourly_rain_mm': np.zeros(total_rows),
        'hour_sin': np.zeros(total_rows),
        'hour_cos': np.ones(total_rows),
        'doy_sin': np.zeros(total_rows),
        'doy_cos': np.ones(total_rows),
        'theo_solar': np.zeros(total_rows),
    })
    
    X, Y, timestamps = generate_sliding_window_tensors(mock_env, df, lookback, forecast)
    
    expected_samples = total_rows - lookback - forecast + 1
    
    assert X.shape == (expected_samples, lookback, 11)
    assert Y.shape == (expected_samples, forecast, 6)
    assert len(timestamps) == expected_samples