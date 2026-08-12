##
# @file test_waid_01_1_ingest_ecowitt.py
# @brief Unit tests for the Ecowitt automated data ingestor.
# @details Uses pytest and unittest.mock to validate URL checks and file download logic
#          without requiring an active network connection or actual file system operations.
# @author AF
# @date 2026

import pytest
import argparse
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
from datetime import datetime

# Assume the script is named waid_01_1_ingest_ecowitt.py
from waid_01_1_ingest_ecowitt import check_url_exists, download_ecowitt_data

class TestEcowittDownloader:
    
    ##
    # @brief Tests that check_url_exists returns True when server responds with 200.
    @patch("urllib.request.urlopen")
    def test_check_url_exists_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        assert check_url_exists("http://192.168.1.1") is True

    ##
    # @brief Tests that check_url_exists returns False when an exception (e.g. timeout) occurs.
    @patch("urllib.request.urlopen")
    def test_check_url_exists_failure(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Connection error")
        
        assert check_url_exists("http://192.168.1.1") is False

    ##
    # @brief Tests the full download workflow, ensuring the file is accepted if size > 100 bytes.
    @patch("waid_01_1_ingest_ecowitt.check_url_exists")
    @patch("subprocess.run")
    def test_download_ecowitt_data_success(self, mock_subprocess, mock_check_url):
        # Setup mocks
        mock_check_url.return_value = True
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        # Mock env and args
        mock_env = MagicMock()
        mock_env.ecowitt_dir = Path("/tmp")
        mock_env.waid_exit.SUCCESS = 0
        
        mock_args = argparse.Namespace(
            period=MagicMock(year=2026, month=8),
            ip="192.168.1.1",
            port=80,
            timeout=30
        )
        
        # Mock Path.exists and stat
        with patch.object(Path, 'exists', return_value=True), patch.object(Path, 'stat') as mock_stat:
            mock_stat.return_value.st_size = 200
            with patch.object(Path, 'rename') as mock_rename, patch.object(Path, 'unlink'):
                
                result = download_ecowitt_data(mock_env, mock_args)
                assert result == 0

    ##
    # @brief Tests that the function returns a failure code when no data is available at the source.
    @patch("waid_01_1_ingest_ecowitt.check_url_exists")
    def test_download_ecowitt_data_no_data(self, mock_check_url):
        mock_check_url.return_value = False
        
        mock_env = MagicMock()
        mock_env.waid_exit.SUCCESS = 0
        mock_env.waid_exit.DATA_FAIL = 1
        
        # Facciamo in modo che il periodo corrisponda al mese corrente (agosto 2026)
        # In questo modo evita il controllo "if not is_current_month and data_file.exists()"
        current_time = datetime.now()
        mock_args = argparse.Namespace(
            period=MagicMock(year=current_time.year, month=current_time.month),
            ip="192.168.1.1",
            port=80,
            timeout=30
        )
        
        result = download_ecowitt_data(mock_env, mock_args)
        assert result == 1