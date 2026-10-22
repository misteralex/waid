#!/usr/bin/env python3

"""
@file test_waid_shared.py
@brief Unit tests for WAID shared core utility and data processing functions.
@details Validates theoretical solar radiation calculations, physics guardrails,
         sensor resolution quantization, period range generation, and Docker environment detection.
@author AF
@date 2026
"""

import os
import sys
from pathlib import Path
from src.waid_shared import (
    calculate_theoretical_solar_radiation,
    apply_physics_guardrails,
    generate_period_range,
    is_in_docker
)
import numpy as np
import pandas as pd
from unittest.mock import patch, mock_open


def test_calculate_theoretical_solar_radiation() -> None:
    """
    @brief Tests theoretical solar radiation calculation with latitude, longitude, and humidity.
    """
    timestamps = pd.date_range("2026-06-01 10:00:00", periods=3, freq="h")
    humidity = np.array([50.0, 60.0, 70.0])
    
    solar_rad = calculate_theoretical_solar_radiation(
        timestamps=timestamps.values,
        humidity=humidity,
        input_tz="UTC",
        lat=45.0,
        lon=9.0
    )

    assert isinstance(solar_rad, np.ndarray)
    assert len(solar_rad) == 3
    assert np.all(solar_rad >= 0.0)


def test_apply_physics_guardrails_scalar() -> None:
    """
    @brief Tests physics guardrails and sensor quantization on scalar values.
    """
    # Test temperature quantization (resolution 0.1)
    res_temp = apply_physics_guardrails(22.345, feature="temp")
    assert res_temp == 22.3

    # Test rain zero-threshold suppression (resolution 0.1, threshold 0.05)
    res_rain = apply_physics_guardrails(0.02, feature="rain")
    assert res_rain == 0.0


def test_apply_physics_guardrails_array() -> None:
    """
    @brief Tests physics guardrails on NumPy array data for specific features.
    """
    wind_data = np.array([0.01, 0.15, 2.45])
    res_wind = apply_physics_guardrails(wind_data, feature="wind")
    
    assert isinstance(res_wind, np.ndarray)
    assert res_wind[0] == 0.0  # Below deadband threshold (0.2 / 2 = 0.1)


def test_generate_period_range() -> None:
    """
    @brief Tests contiguous YYYY-MM period generation.
    """
    periods = generate_period_range("2026-01", "2026-04")
    assert periods == ["2026-01", "2026-02", "2026-03", "2026-04"]


def test_is_in_docker_true() -> None:
    """
    @brief Tests Docker environment detection when /.dockerenv exists.
    """
    with patch("pathlib.Path.exists", return_value=True):
        assert is_in_docker() is True


def test_is_in_docker_false() -> None:
    """
    @brief Tests Docker environment detection when not running inside container.
    """
    with patch("pathlib.Path.exists", return_value=False), \
         patch("builtins.open", side_effect=FileNotFoundError):
        assert is_in_docker() is False