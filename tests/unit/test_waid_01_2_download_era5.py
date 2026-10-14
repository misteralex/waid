#!/usr/bin/env python3

"""
@file test_waid_01_2_download_era5.py
@brief Unit tests for the ERA5 atmospheric reanalysis data downloader.
@details Uses pytest and unittest.mock to validate CDS client initialization,
         file skipping logic, and error handling without contacting external APIs.
@author AF
@date 2026
"""

import pytest
import argparse
from unittest.mock import MagicMock, patch
from pathlib import Path
from datetime import datetime

from waid_01_2_ingest_era5 import download_era5

class TestEra5Downloader:
    """
    @brief Test suite for ERA5 data retrieval and consolidation logic.
    """

    @patch("waid_01_2_ingest_era5.cdsapi.Client")
    def test_download_era5_already_exists(self, mock_cds_client: MagicMock, tmp_path: Path) -> None:
        """
        @brief Tests that download_era5 skips downloading if the full month archive already exists.
        @param mock_cds_client Mocked Copernicus CDS API client.
        @param tmp_path Pytest fixture providing a temporary directory.
        """
        mock_env = MagicMock()
        mock_env.era5_api_url = "https://cds.climate.copernicus.eu/api"
        mock_env.era5_api_key = "test-key"
        mock_env.era5_data_dir = tmp_path
        
        period = datetime(2026, 8, 1)
        filename_base = f"era5_{period.year}_{period.month:02d}"
        
        # Create a real temporary full file so stat().st_size returns a valid integer (> 0)
        full_file = tmp_path / f"{filename_base}.full"
        full_file.write_text("dummy netcdf content for testing")

        mock_args = argparse.Namespace(
            period=period,
            lat=45.0,
            lon=9.0,
            elevation=100
        )
        
        result = download_era5(mock_env, mock_args)
        assert result is True
        # Verify that client was initialized, but retrieve method was never called
        mock_cds_client.assert_called_once()
        mock_cds_client.return_value.retrieve.assert_not_called()

    @patch("waid_01_2_ingest_era5.cdsapi.Client")
    def test_download_era5_client_initialization_failure(self, mock_cds_client: MagicMock, tmp_path: Path) -> None:
        """
        @brief Tests that a WError is raised when the CDS API client fails to initialize.
        @param mock_cds_client Mocked Copernicus CDS API client raising an exception.
        @param tmp_path Pytest fixture providing a temporary directory.
        """
        mock_cds_client.side_effect = Exception("API connection failure")
        
        mock_env = MagicMock()
        mock_env.era5_api_url = "invalid-url"
        mock_env.era5_api_key = "invalid-key"
        mock_env.era5_data_dir = tmp_path
        
        mock_args = argparse.Namespace(
            period=datetime(2026, 8, 1),
            lat=45.0,
            lon=9.0,
            elevation=100
        )
        
        with pytest.raises(Exception) as exc_info:
            download_era5(mock_env, mock_args)
        assert "CDS API Client Initialization Failed" in str(exc_info.value)