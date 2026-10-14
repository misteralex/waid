#!/usr/init/env python3  # type: ignore

"""
@file test_waid_05_3_ml_sanity_check.py
@brief Unit tests for the automated ML validation gate and pipeline alignment checks.
@details Uses pytest, numpy, joblib, and mock objects to validate tensor integrity inspection,
         feature schema alignment, and validation pass/fail logic without external dependencies.
@author AF
@date 2026
"""

import pytest
import numpy as np
import joblib
from pathlib import Path
from unittest.mock import MagicMock, patch
from sklearn.preprocessing import StandardScaler

from waid_05_3_ml_sanity_check import (
    validate_pipeline_alignment,
    SEMANTIC_EQUIVALENCES,
)


def test_semantic_equivalences_mapping() -> None:
    """
    @brief Tests that training and inference semantic equivalences are correctly mapped.
    """
    assert SEMANTIC_EQUIVALENCES.get("temperature") == "ecowitt_temp"
    assert SEMANTIC_EQUIVALENCES.get("humidity") == "ecowitt_rh"
    assert SEMANTIC_EQUIVALENCES.get("hour_sin") == "hour_sin"


def test_validate_pipeline_alignment_success(tmp_path: Path) -> None:
    """
    @brief Tests successful pipeline validation when tensors, scalers, and models are fully aligned.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    tensors_dir = tmp_path / "tensors"
    models_dir = tmp_path / "models"
    tensors_dir.mkdir()
    models_dir.mkdir()
    
    # 1. Create mock X, Y, timestamps tensors for a sample period
    period = "2026_06"
    num_samples, num_timesteps, num_features = 10, 5, 11
    
    X = np.zeros((num_samples, num_timesteps, num_features), dtype=np.float32)
    Y = np.zeros((num_samples, 2, 6), dtype=np.float32)
    timestamps = np.array([f"2026-06-01 {i:02d}:00:00" for i in range(num_samples)])
    
    joblib.dump(X, tensors_dir / f"X_raw_{period}.pkl")
    joblib.dump(Y, tensors_dir / f"Y_raw_{period}.pkl")
    joblib.dump(timestamps, tensors_dir / f"timestamps_{period}.pkl")
    
    # 2. Create a real StandardScaler and fit it with 11 features so joblib can pickle it properly
    scaler = StandardScaler()
    scaler.fit(np.zeros((5, 11)))
    joblib.dump(scaler, models_dir / "scaler_input.pkl")
    
    # 3. Create mock Keras model file
    model_file = models_dir / "waid_lstm.h5"
    model_file.touch()
    
    mock_env = MagicMock()
    mock_env.ml_tensors_dir = tensors_dir
    mock_env.ml_models_dir = models_dir
    mock_env.ml_input_scaler_pkl_file = "scaler_input.pkl"
    mock_env.ml_model_h5_file = "waid_lstm.h5"
    
    # Config output features matching 6 standard vars
    mock_env.output_features = [
        {"standard": "outdoor_temperature_c"},
        {"standard": "abs_pressure_hpa"},
        {"standard": "outdoor_humidity"},
        {"standard": "wind_m_s"},
        {"standard": "solar_rad_w_m2"},
        {"standard": "hourly_rain_mm"},
    ]
    
    # Inference order matching training order
    mock_env.input_features_match = [
        "outdoor_temperature_c", "abs_pressure_hpa", "outdoor_humidity",
        "wind_m_s", "solar_rad_w_m2", "hourly_rain_mm",
        "hour_sin", "hour_cos", "doy_sin", "doy_cos", "theo_solar"
    ]
    
    # Mock load_model to avoid real keras dependency issues during unit test
    with patch("waid_05_3_ml_sanity_check.load_model") as mock_load_model:
        mock_model_instance = MagicMock()
        mock_model_instance.input_shape = (None, 5, 11)
        mock_load_model.return_value = mock_model_instance
        
        from waid_05_3_ml_sanity_check import validate_pipeline_alignment
        result = validate_pipeline_alignment(mock_env)
        
        assert result == 0  # WaidExit.SUCCESS