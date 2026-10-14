#!/usr/bin/env python3

"""
@file test_waid_01_3_profile_era5.py
@brief Unit tests for the ERA5 NetCDF data profiling and catalog helper.
@details Uses pytest, tmp_path, and xarray to validate dataset profiling,
         missing file handling, and data quality checks without external file dependencies.
@author AF
@date 2026
"""

import pytest
import argparse
from unittest.mock import MagicMock
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import xarray as xr

from waid_01_3_profile_era5 import check_era5_data

class TestEra5Profiler:
    """
    @brief Test suite for ERA5 dataset metadata extraction and data profiling.
    """

    def test_check_era5_data_file_not_found(self, tmp_path: Path) -> None:
        """
        @brief Tests that check_era5_data gracefully skips profiling and returns SUCCESS if no file is found.
        @param tmp_path Pytest fixture providing a temporary directory.
        """
        mock_env = MagicMock()
        mock_env.era5_data_dir = tmp_path
        mock_env.waid_exit.SUCCESS = 0
        
        mock_args = argparse.Namespace(
            period=datetime(2026, 8, 1)
        )
        
        result = check_era5_data(mock_env, mock_args)
        assert result == 0

    def test_check_era5_data_success_profiling(self, tmp_path: Path) -> None:
        """
        @brief Tests successful dataset profiling using a temporary NetCDF file.
        @param tmp_path Pytest fixture providing a temporary directory.
        """
        mock_env = MagicMock()
        mock_env.era5_data_dir = tmp_path
        mock_env.ecowitt_latitude = 45.0
        mock_env.ecowitt_longitude = 9.0
        mock_env.waid_exit.SUCCESS = 0
        
        period = datetime(2026, 8, 1)
        filename_base = f"era5_{period.year}_{period.month:02d}"
        nc_file = tmp_path / f"{filename_base}.nc"
        
        # Create a dummy xarray dataset and save it as NetCDF (using lowercase 'h' for frequency)
        times = pd.date_range("2026-08-01", periods=5, freq="h")
        ds = xr.Dataset(
            {
                "2m_temperature": (("valid_time", "latitude", "longitude"), np.random.rand(5, 1, 1) + 273.15),
            },
            coords={
                "valid_time": times,
                "latitude": [45.0],
                "longitude": [9.0],
            }
        )
        ds["2m_temperature"].attrs = {"units": "K", "long_name": "2 metre temperature"}
        ds.to_netcdf(nc_file)
        ds.close()

        mock_args = argparse.Namespace(
            period=period
        )
        
        result = check_era5_data(mock_env, mock_args)
        assert result == 0