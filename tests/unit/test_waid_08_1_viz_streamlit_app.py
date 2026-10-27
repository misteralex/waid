"""
@file test_waid_08_1_viz_streamlit_app.py
@brief Unit tests for the WAID Streamlit analytics dashboard and deployment script.
@details Validates deployment status checking, package setup generation, available dates querying,
         and public feature data loading using SQLite and pytest fixtures.
@author AF
@date 2026
"""

import os
import sqlite3
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock, patch

from waid_08_1_viz_streamlit_app import (
    get_deployment_status,
    run_deployment_setup,
    get_available_dates,
    load_public_data_for_feature,
    check_era5_availability,
    main
)


def test_get_deployment_status_missing(tmp_path: Path) -> None:
    """
    @brief Tests deployment status detection when the deployment app.py file is missing.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    mock_env = MagicMock()
    mock_env.streamlit_dir = tmp_path / "deploy"

    with patch("waid_08_1_viz_streamlit_app.WaidBoot", return_value=mock_env):
        status = get_deployment_status()
        assert status == "MISSING"


def test_run_deployment_setup(tmp_path: Path) -> None:
    """
    @brief Tests the deployment package generation including requirements.txt and app.py creation.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    deploy_dir = tmp_path / "deploy"
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "requirements.txt").touch()

    db_file = tmp_path / "deploy_waid.db"
    db_file.touch()

    mock_env = MagicMock()
    mock_env.streamlit_dir = deploy_dir
    mock_env.waid_source_dir = source_dir
    mock_env.deploy_db_file = str(db_file)
    mock_env.deploy_mode = "local"
    mock_env.target_env = "draft"

    run_deployment_setup(mock_env)

    assert (deploy_dir / "requirements.txt").exists()
    assert (deploy_dir / "app.py").exists()
    assert (deploy_dir / "data" / "deploy_waid.db").exists()


def test_get_available_dates_sqlite(tmp_path: Path) -> None:
    """
    @brief Tests querying distinct available dates from the local SQLite deployment database.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    deploy_dir = tmp_path / "deploy"
    data_dir = deploy_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "deploy_waid.db"

    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE public_forecasts (
                timestamp TEXT,
                created_at TEXT,
                pred_temp REAL
            );
        """)
        conn.execute("INSERT INTO public_forecasts VALUES ('2026-06-01 12:00:00', '2026-06-01 12:05:00', 22.5);")
        conn.execute("INSERT INTO public_forecasts VALUES ('2026-06-02 12:00:00', '2026-06-02 12:05:00', 23.0);")
        conn.commit()

    mock_env = MagicMock()
    mock_env.deploy_mode = "local"
    mock_env.streamlit_dir = deploy_dir
    mock_env.deploy_db_file = str(db_path)

    with patch("waid_08_1_viz_streamlit_app.WaidBoot", return_value=mock_env):
        dates = get_available_dates()
        assert "2026-06-01" in dates
        assert "2026-06-02" in dates


def test_load_public_data_for_feature_sqlite(tmp_path: Path) -> None:
    """
    @brief Tests loading and filtering public feature data from SQLite database.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    deploy_dir = tmp_path / "deploy"
    data_dir = deploy_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "deploy_waid.db"

    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE public_forecasts (
                timestamp TEXT,
                created_at TEXT,
                pred_temp REAL,
                diff_temp REAL,
                historical_bias_temp REAL,
                drift_vs_bias_temp REAL,
                temp_era5 REAL,
                abs_error_temp REAL
            );
        """)
        conn.execute("""
            INSERT INTO public_forecasts VALUES (
                '2026-06-01 12:00:00', '2026-06-01 12:05:00', 
                25.0, 1.0, 0.5, 0.1, 24.5, 0.5
            );
        """)
        conn.commit()

    mock_env = MagicMock()
    mock_env.deploy_mode = "local"
    mock_env.streamlit_dir = deploy_dir
    mock_env.deploy_db_file = str(db_path)
    mock_env.tz_timezone = "UTC"

    with patch("waid_08_1_viz_streamlit_app.WaidBoot", return_value=mock_env):
        df = load_public_data_for_feature("2026-06-01", feature="temp")
        assert not df.empty
        assert "pred_temp" in df.columns
        assert df["pred_temp"].iloc[0] == 25.0


def test_main_cli_deploy_flag(tmp_path: Path) -> None:
    """
    @brief Tests main function execution when invoked with the --deploy CLI flag.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    deploy_dir = tmp_path / "deploy"
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "requirements.txt").touch()

    db_file = tmp_path / "deploy_waid.db"
    db_file.touch()

    mock_env = MagicMock()
    mock_env.streamlit_dir = deploy_dir
    mock_env.waid_source_dir = source_dir
    mock_env.deploy_db_file = str(db_file)
    mock_env.deploy_mode = "local"
    mock_env.target_env = "draft"

    with patch("waid_08_1_viz_streamlit_app.WaidBoot", return_value=mock_env):
        with patch("sys.argv", ["waid_08_1_viz_streamlit_app.py", "--deploy"]):
            exit_code = main()
            assert exit_code == 0