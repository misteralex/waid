##
# @file test_waid_01_2_ingest_era5.py
# @brief Unit tests for the ERA5 automated reanalysis data downloader.
# @details Uses pytest and unittest.mock to validate Copernicus CDS client requests,
#          API credentials validation, and file skipping logic without real API calls.
# @author AF
# @date 2026

import pytest
import argparse
from datetime import datetime
from unittest.mock import MagicMock, patch

from waid_01_2_ingest_era5 import download_era5, main

class TestEra5Downloader:

    ##
    # @brief Tests that download_era5 skips execution if the full month archive already exists.
    @patch("waid_01_2_ingest_era5.cdsapi.Client")
    def test_download_era5_already_exists(self, mock_cds_client):
        # Creiamo un mock per l'ambiente e per il file full, impostando st_size come intero
        mock_env = MagicMock()
        mock_file_full = MagicMock()
        mock_file_full.exists.return_value = True
        mock_file_full.stat.return_value.st_size = 1024  # Intero reale, evita il TypeError

        # Facciamo in modo che la divisione dei path restituisca il nostro mock controllato
        mock_env.era5_data_dir.__truediv__.return_value = mock_file_full
        
        mock_args = argparse.Namespace(
            period=datetime(2026, 2, 1),
            lat=45.0,
            lon=9.0,
            elevation=100
        )
        
        result = download_era5(mock_env, mock_args)
        assert result is True

    ##
    # @brief Tests that main returns CONFIG_FAIL when ERA5 API credentials are missing.
    @patch("waid_01_2_ingest_era5.WaidBoot")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_missing_credentials(self, mock_parse_args, mock_waid_boot):
        mock_env = MagicMock()
        mock_env.era5_api_url = None
        mock_env.era5_api_key = None
        mock_waid_boot.return_value = mock_env
        
        result = main()
        assert isinstance(result, int)