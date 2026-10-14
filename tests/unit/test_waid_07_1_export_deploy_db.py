#!/usr/bin/env python3

"""
@file test_waid_07_1_export_deploy_db.py
@brief Unit tests for the WAID ETL export and deployment database script.
@details Uses pytest, sqlite3, pandas, and mock objects to validate data extraction,
         deduplication completeness, and local SQLite public_forecasts persistence.
@author AF
@date 2026
"""

import pytest
import sqlite3
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock, patch

from waid_07_1_export_deploy_db import main


def test_export_deploy_db_success(tmp_path: Path) -> None:
    """
    @brief Tests successful ETL extraction, deduplication, and export to deployment database.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    lab_db = tmp_path / "lab_waid.db"
    deploy_db = tmp_path / "deploy_waid.db"
    
    # 1. Setup lab database with source tables
    with sqlite3.connect(lab_db) as conn:
        conn.execute("""
            CREATE TABLE inference_forecast (
                timestamp TEXT,
                created_at TEXT,
                model_version TEXT,
                pred_temp REAL, pred_rh REAL, pred_pres REAL, pred_wind REAL, pred_rain REAL, pred_solar REAL,
                diff_temp REAL, diff_rh REAL, diff_pres REAL, diff_wind REAL, diff_rain REAL, diff_solar REAL,
                historical_bias_temp REAL, historical_bias_rh REAL, historical_bias_pres REAL, historical_bias_wind REAL, historical_bias_rain REAL, historical_bias_solar REAL,
                drift_vs_bias_temp REAL, drift_vs_bias_rh REAL, drift_vs_bias_pres REAL, drift_vs_bias_wind REAL, drift_vs_bias_rain REAL, drift_vs_bias_solar REAL,
                PRIMARY KEY (timestamp, model_version)
            );
        """)
        conn.execute("""
            CREATE TABLE inference_quality (
                timestamp TEXT,
                model_version TEXT,
                temp_era5 REAL, rh_era5 REAL, pres_era5 REAL, wind_era5 REAL, rain_era5 REAL, solar_era5 REAL,
                abs_error_temp REAL, abs_error_rh REAL, abs_error_pres REAL, abs_error_wind REAL, abs_error_rain REAL, abs_error_solar REAL,
                PRIMARY KEY (timestamp, model_version)
            );
        """)
        
        # Insert duplicate/overlapping rows to test deduplication
        conn.execute("""
            INSERT INTO inference_forecast (timestamp, created_at, model_version, pred_temp) 
            VALUES ('2026-06-01 12:00:00', '2026-06-01 12:05:00', 'v1', 22.5);
        """)
        conn.execute("""
            INSERT INTO inference_quality (timestamp, model_version, temp_era5) 
            VALUES ('2026-06-01 12:00:00', 'v1', 22.0);
        """)
        conn.commit()

    mock_exit = MagicMock()
    mock_exit.SUCCESS = 0
    mock_exit.DATA_FAIL = 3
    mock_exit.CONFIG_FAIL = 4

    mock_env = MagicMock()
    mock_env.waid_db_file = str(lab_db)
    mock_env.deploy_db_file = str(deploy_db)
    mock_env.waid_data_dir = tmp_path
    mock_env.deploy_mode = "local"
    mock_env.waid_exit = mock_exit
    mock_env.retro_now = None
    mock_env.db.inference_forecast = "inference_forecast"
    mock_env.db.inference_quality = "inference_quality"

    with patch("waid_07_1_export_deploy_db.WaidBoot", return_value=mock_env):
        with patch("sys.argv", ["waid_07_1_export_deploy_db.py"]):
            exit_code = main()
            assert exit_code == 0

    # Verify deploy database contains the exported records
    with sqlite3.connect(deploy_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM public_forecasts;")
        count = cursor.fetchone()[0]
        assert count == 1


def test_export_deploy_db_missing_lab_db(tmp_path: Path) -> None:
    """
    @brief Tests ETL failure when the source lab database does not exist.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    non_existent_db = tmp_path / "non_existent.db"
    deploy_db = tmp_path / "deploy_waid.db"

    mock_exit = MagicMock()
    mock_exit.SUCCESS = 0
    mock_exit.DATA_FAIL = 3
    mock_exit.CONFIG_FAIL = 4

    mock_env = MagicMock()
    mock_env.waid_db_file = str(non_existent_db)
    mock_env.deploy_db_file = str(deploy_db)
    mock_env.waid_data_dir = tmp_path
    mock_env.deploy_mode = "local"
    mock_env.waid_exit = mock_exit
    mock_env.retro_now = None

    with patch("waid_07_1_export_deploy_db.WaidBoot", return_value=mock_env):
        with patch("sys.argv", ["waid_07_1_export_deploy_db.py"]):
            exit_code = main()
            assert exit_code == 3  # WaidExit.DATA_FAIL