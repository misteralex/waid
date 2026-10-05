#!/usr/bin/env python3

"""
@file app.py
@brief Streamlit public analytics dashboard featuring dedicated tabs for weather features and 3-way comparisons.
@details Integrates automated deployment packaging, dynamic database query resolution (SQLite/Supabase),
         and standard operational error handling for the WAID framework.
@author AF
@date 2026
"""

import os
import sys
import sqlite3
import shutil
import argparse
import pandas as pd
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx
import plotly.graph_objects as go
import numpy as np
from pathlib import Path
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from dotenv import load_dotenv

# Calculate absolute project root path and load configuration env file
PROJECT_ROOT = Path(__file__).resolve().parents[1]
dotenv_path = PROJECT_ROOT / "config" / "waid.env"

if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)
else:
    load_dotenv()  # Fallback to default .env file in project root

# Resolve WAID root path via WAID_SOURCE environment variable
waid_root = Path(
    os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])
).resolve()

# Append src directory to sys.path (enables imports like: from waid_shared import ...)
src_dir = waid_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Append root directory to sys.path as fallback
if str(waid_root) not in sys.path:
    sys.path.insert(0, str(waid_root))

# Append config directory to sys.path (enables imports like: from boot import ...)
config_dir = waid_root / "config"
if str(config_dir) not in sys.path:
    sys.path.insert(0, str(config_dir))

from boot import WaidBoot, WError, WaidExit

# Import shared utilities from Single Source of Truth inside src/
from waid_shared import get_last_inference_datetime


def get_deployment_status() -> str:
    """Evaluates the deployment package sync status relative to the source script.

    @details Checks whether the deployment directory exists and if the source script mtime is newer.
    @return Deployment status identifier string: "MISSING", "OUTDATED", "SYNCED", or "UNKNOWN".
    """
    try:
        env = WaidBoot()
        deploy_app = Path(env.deploy_dir) / "app.py"
        src_script = Path(__file__).resolve()
        
        if not deploy_app.exists():
            return "MISSING"
        
        if src_script.stat().st_mtime > deploy_app.stat().st_mtime:
            return "OUTDATED"
        
        return "SYNCED"
    except Exception:
        return "UNKNOWN"


def run_deployment_setup(env: WaidBoot) -> None:
    """Generates or updates the standalone target deployment package.

    @details Copies database dependencies, updates source script headers, and writes requirements.txt.
    @param env WaidBoot configuration instance containing system environment settings.
    @return None
    """
    deploy_dir = Path(env.deploy_dir)
    src_script = Path(__file__).resolve()
    db_source = Path(env.deploy_db_file)
    db_dest = Path(deploy_dir / "data" / os.path.basename(env.deploy_db_file))

    logger.info(f"🔶 Deploy Mode : {env.deploy_mode}")
    logger.info(f"🔶 DB Target   : {getattr(env, 'target_env', os.getenv('WAID_TARGET_ENV', 'draft'))}")    
    logger.info(f"Initializing deployment package at: {deploy_dir}")
    
    deploy_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write requirements.txt
    req_content = (
        "streamlit>=1.30.0\n"
        "plotly>=5.0.0\n"
        "python-dotenv>=1.0.0\n"
        "loguru>=0.7.0\n"
        "pandas>=2.0.0\n"
        "numpy>=1.24.0\n"
        "sqlalchemy>=2.0.0\n"
        "psycopg2-binary>=2.9.0\n"
    )
    with open(deploy_dir / "requirements.txt", "w", encoding="utf-8") as f:
        f.write(req_content)

    # 2. Generate app.py by updating the @file header
    content = src_script.read_text(encoding="utf-8")
    updated_content = content.replace(
        "@file app.py", 
        "@file app.py"
    )
    (deploy_dir / "app.py").write_text(updated_content, encoding="utf-8")

    # 3. Copy database file to deployment root directory
    if db_source.exists():
        (deploy_dir / "data").mkdir(parents=True, exist_ok=True)
        logger.info(f"Data deployment from {db_source} to {db_dest}")
        shutil.copy(db_source, db_dest)
        logger.success(f"Database successfully copied to: {db_dest}")
    else:
        logger.warning(f"Source database not found at {db_source}")

    logger.success("Deployment package successfully created!")


@st.cache_data(ttl=300)
def get_available_dates() -> list:
    """Queries distinct dates available in the forecasts database for selector UI elements.

    @details Selects distinct timestamps from public_forecasts using Supabase or SQLite based on deployment mode.
    @return Sorted list of date strings (YYYY-MM-DD) in descending order.
    """
    try:
        env = WaidBoot()
        deploy_mode = getattr(env, "deploy_mode", os.getenv("WAID_DEPLOY_MODE", "local")).lower()
    except Exception:
        deploy_mode = os.getenv("WAID_DEPLOY_MODE", "local").lower()

    if deploy_mode == "cloud":
        try:
            db_config = getattr(env, "active_db_config", None)
            user = getattr(db_config, "user", None) or getattr(db_config, "db_user", None) or os.getenv("WAID_DB_USER")
            password = getattr(db_config, "password", None) or getattr(db_config, "db_password", None) or os.getenv("WAID_DB_PASSWORD")
            host = getattr(db_config, "host", None) or getattr(db_config, "db_host", None) or os.getenv("WAID_DB_HOST")
            port = getattr(db_config, "port", None) or getattr(db_config, "db_port", "6543") or os.getenv("WAID_DB_PORT", "6543")
            dbname = getattr(db_config, "dbname", None) or getattr(db_config, "db_name", "postgres") or os.getenv("WAID_DB_NAME", "postgres")

            if not all([user, password, host]):
                return []

            supabase_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require"
            engine = create_engine(supabase_url, poolclass=NullPool)

            schema_prefix = f"{env.db_schema_target}." if hasattr(env, "db_schema_target") and env.db_schema_target else ""
            query = text(f"SELECT DISTINCT DATE(timestamp) AS target_date FROM {schema_prefix}public_forecasts ORDER BY target_date DESC;")
            with engine.connect() as conn:
                df_dates = pd.read_sql_query(query, conn)

            if not df_dates.empty:
                return df_dates['target_date'].astype(str).tolist()
        except Exception as e:
            st.error(f"Error fetching dates from Supabase: {e}")
            return []
    else:
        base_dir = Path(__file__).resolve().parent
        current_deploy_db = os.path.basename(env.deploy_db_file)
        deploy_dir = base_dir if base_dir.name == "deploy" else base_dir / "deploy"
        cloud_deploy_db = deploy_dir / "data" / current_deploy_db
        local_deploy_db = Path(env.deploy_dir) / "data" / current_deploy_db
        db_path = cloud_deploy_db if cloud_deploy_db.exists() else (local_deploy_db if local_deploy_db.exists() else None)

        if not db_path or not db_path.exists():
            return []

        try:
            with sqlite3.connect(db_path) as conn:
                query = "SELECT DISTINCT DATE(timestamp) AS target_date FROM public_forecasts ORDER BY target_date DESC"
                df_dates = pd.read_sql_query(query, conn)
                if not df_dates.empty:
                    return df_dates['target_date'].astype(str).tolist()
        except Exception as e:
            st.error(f"Error fetching dates from SQLite: {e}")
            return []

    return []


@st.cache_data(ttl=300)
def load_public_data_for_feature(target_date: str, feature: str = None) -> pd.DataFrame:
    """Loads analytics records filtered by target date and specific weather feature key.

    @details Fetches required columns for time series rendering to minimize payload and memory consumption.
    @param target_date Target date string formatted as YYYY-MM-DD.
    @param feature Optional weather feature key (e.g., 'temp', 'rh', 'pres', 'wind', 'solar', 'rain').
    @return Cleaned pandas DataFrame populated with metric and forecast columns.
    """
    try:
        env = WaidBoot()
        deploy_mode = getattr(env, "deploy_mode", os.getenv("WAID_DEPLOY_MODE", "local")).lower()
        target_tz = getattr(env, "tz_timezone", "UTC")
    except Exception:
        deploy_mode = os.getenv("WAID_DEPLOY_MODE", "local").lower()
        target_tz = "UTC"

    # Define interval for the full LOCAL day
    local_start = pd.Timestamp(f"{target_date} 00:00:00", tz=target_tz)
    local_end = pd.Timestamp(f"{target_date} 23:59:59", tz=target_tz)

    # Convert to UTC for SQL query filter
    start_ts = local_start.tz_convert("UTC").strftime("%Y-%m-%d %H:%M:%S")
    end_ts = local_end.tz_convert("UTC").strftime("%Y-%m-%d %H:%M:%S")

    # Standard columns always available in SQLite and Supabase schemas
    base_columns = [
        "timestamp",
        "created_at",
        f"pred_{feature}",
        f"diff_{feature}",
        f"historical_bias_{feature}",
        f"drift_vs_bias_{feature}",
        f"{feature}_era5",
        f"abs_error_{feature}"
    ] if feature else []

    if deploy_mode == "cloud":
        try:
            db_config = getattr(env, "active_db_config", None)
            user = getattr(db_config, "user", None) or getattr(db_config, "db_user", None) or os.getenv("WAID_DB_USER")
            password = getattr(db_config, "password", None) or getattr(db_config, "db_password", None) or os.getenv("WAID_DB_PASSWORD")
            host = getattr(db_config, "host", None) or getattr(db_config, "db_host", None) or os.getenv("WAID_DB_HOST")
            port = getattr(db_config, "port", None) or getattr(db_config, "db_port", "6543") or os.getenv("WAID_DB_PORT", "6543")
            dbname = getattr(db_config, "dbname", None) or getattr(db_config, "db_name", "postgres") or os.getenv("WAID_DB_NAME", "postgres")

            if not all([user, password, host]):
                return pd.DataFrame()

            supabase_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require"
            engine = create_engine(supabase_url, poolclass=NullPool)

            schema_prefix = f"{env.db_schema_target}." if hasattr(env, "db_schema_target") and env.db_schema_target else ""
            
            # On Supabase, include calculated actual_{feature} column if present in the view
            columns_to_select = base_columns + [f"actual_{feature}"] if feature else []
            select_clause = ", ".join(columns_to_select) if columns_to_select else "*"

            query = text(f"""
                SELECT {select_clause} FROM {schema_prefix}public_forecasts 
                WHERE timestamp >= :start_ts AND timestamp <= :end_ts 
                ORDER BY timestamp ASC;
            """)
            df = pd.read_sql_query(query, engine, params={"start_ts": start_ts, "end_ts": end_ts})

        except Exception as e:
            # Fallback for Supabase if the view lacks the actual_* column
            if feature and f"actual_{feature}" in str(e):
                select_clause = ", ".join(base_columns)
                query = text(f"""
                    SELECT {select_clause} FROM {schema_prefix}public_forecasts 
                    WHERE timestamp >= :start_ts AND timestamp <= :end_ts 
                    ORDER BY timestamp ASC;
                """)
                df = pd.read_sql_query(query, engine, params={"start_ts": start_ts, "end_ts": end_ts})
            else:
                st.error(f"Supabase connection error: {e}")
                return pd.DataFrame()
    else:
        base_dir = Path(__file__).resolve().parent
        current_deploy_db = os.path.basename(env.deploy_db_file)
        cloud_deploy_db = (
            base_dir / "data" / current_deploy_db
            if base_dir.name == "deploy"
            else base_dir / "deploy" / "data" / current_deploy_db
        )
        local_deploy_db = Path(env.deploy_dir) / "data" / current_deploy_db
        db_path = cloud_deploy_db if cloud_deploy_db.exists() else (local_deploy_db if local_deploy_db.exists() else None)
        
        if not db_path or not db_path.exists():
            return pd.DataFrame()

        try:
            with sqlite3.connect(db_path) as conn:
                # For SQLite, select exact columns matching real schema (without actual_*)
                select_clause = ", ".join(base_columns) if feature else "*"
                query = f"SELECT {select_clause} FROM public_forecasts WHERE timestamp >= ? AND timestamp <= ? ORDER BY timestamp ASC"
                df = pd.read_sql_query(query, conn, params=(start_ts, end_ts))
        except Exception as e:
            st.error(f"Local SQLite database error: {e}")
            return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    # Numeric conversion for selected feature columns
    target_keys = [feature] if feature else ['temp', 'rh', 'pres', 'wind', 'rain', 'solar']
    numeric_cols = []
    for k in target_keys:
        numeric_cols.extend([
            f'pred_{k}', f'diff_{k}', f'historical_bias_{k}', 
            f'drift_vs_bias_{k}', f'{k}_era5', f'abs_error_{k}', f'actual_{k}'
        ])

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


@st.cache_data(ttl=300)
def check_era5_availability(target_date: str) -> bool:
    """Evaluates if ERA5 reanalysis ground truth data is populated for a target date.

    @param target_date Target date string formatted as YYYY-MM-DD.
    @return True if non-null ERA5 temperature values exist; False otherwise.
    """
    df = load_public_data_for_feature(target_date, feature='temp')
    if not df.empty and 'temp_era5' in df.columns:
        return df['temp_era5'].notnull().any()
    return False


@st.cache_data(ttl=300)
def fetch_last_inference_timestamp() -> str:
    """Retrieves the timestamp corresponding to the latest machine learning inference execution.

    @details Queries created_at or timestamp in public_forecasts using local time comparison.
    @return Formatted timestamp string (YYYY-MM-DD HH:MM:SS) or "N/A" if unavailable.
    """
    try:
        env = WaidBoot()
        deploy_mode = getattr(env, "deploy_mode", os.getenv("WAID_DEPLOY_MODE", "local")).lower()
    except Exception:
        deploy_mode = os.getenv("WAID_DEPLOY_MODE", "local").lower()

    raw_ts = None

    if deploy_mode == "cloud":
        try:
            db_config = getattr(env, "active_db_config", None)
            user = getattr(db_config, "user", None) or getattr(db_config, "db_user", None) or os.getenv("WAID_DB_USER")
            password = getattr(db_config, "password", None) or getattr(db_config, "db_password", None) or os.getenv("WAID_DB_PASSWORD")
            host = getattr(db_config, "host", None) or getattr(db_config, "db_host", None) or os.getenv("WAID_DB_HOST")
            port = getattr(db_config, "port", None) or getattr(db_config, "db_port", "6543") or os.getenv("WAID_DB_PORT", "6543")
            dbname = getattr(db_config, "dbname", None) or getattr(db_config, "db_name", "postgres") or os.getenv("WAID_DB_NAME", "postgres")

            if not all([user, password, host]):
                return "N/A"

            supabase_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require"
            engine = create_engine(supabase_url, poolclass=NullPool)
            schema_prefix = f"{env.db_schema_target}." if hasattr(env, "db_schema_target") and env.db_schema_target else ""
            
            # On PostgreSQL (Supabase), retrieve MAX(created_at)
            query = text(f"""
                SELECT MAX(created_at) AS last_ts 
                FROM {schema_prefix}public_forecasts;
            """)
            with engine.connect() as conn:
                raw_ts = conn.execute(query).scalar()

        except Exception as e:
            st.error(f"Error fetching last inference from Supabase: {e}")
            return "N/A"
    else:
        base_dir = Path(__file__).resolve().parent
        current_deploy_db = os.path.basename(env.deploy_db_file)
        cloud_deploy_db = (
            base_dir / "data" / current_deploy_db
            if base_dir.name == "deploy"
            else base_dir / "deploy" / "data" / current_deploy_db
        )
        local_deploy_db = Path(env.deploy_dir) / "data" / current_deploy_db
        data_dir_db = Path(env.waid_data_dir) / current_deploy_db

        db_path = None
        for candidate in [cloud_deploy_db, local_deploy_db, data_dir_db]:
            if candidate and candidate.exists():
                db_path = candidate
                break

        if not db_path:
            return "N/A"

        # In local SQLite, compare created_at with system local time
        try:
            with sqlite3.connect(db_path) as conn:
                query = """
                    SELECT MAX(created_at) AS last_ts 
                    FROM public_forecasts
                    WHERE created_at <= datetime('now', 'localtime');
                """
                df_res = pd.read_sql_query(query, conn)
                if not df_res.empty and pd.notnull(df_res["last_ts"].iloc[0]):
                    raw_ts = df_res["last_ts"].iloc[0]
        except Exception as e:
            logger.debug(f"Error querying SQLite: {e}")
            return "N/A"

    if raw_ts:
        # Since created_at is ALREADY in local time, return directly as string
        return str(raw_ts)

    return "N/A"


def render_feature_tab(env: WaidBoot, selected_date: str, key: str, label: str, unit: str, plotly_config: dict) -> None:
    """Renders metrics cards and interactive Plotly visual comparisons for a weather feature tab.

    @param env WaidBoot system environment configuration instance.
    @param selected_date Target date string formatted as YYYY-MM-DD.
    @param key Weather feature attribute identifier (e.g., 'temp', 'rh').
    @param label Human-readable feature title for chart headers.
    @param unit Measurement unit representation string (e.g., '°C', 'hPa').
    @param plotly_config Dictionary containing standard Plotly figure display parameters.
    @return None
    """
    df_day = load_public_data_for_feature(selected_date, feature=key)

    if df_day.empty:
        st.warning(f"No data available for {label} on {selected_date}.")
        return

    # 1. Parsing and hourly normalization strictly in UTC
    df_day['ts_target'] = pd.to_datetime(df_day['timestamp'], errors='coerce')
    if df_day['ts_target'].dt.tz is None:
        df_day['ts_target'] = df_day['ts_target'].dt.tz_localize('UTC')

    df_day['ts_target'] = df_day['ts_target'].dt.floor('h')

    # 2. Define target day window in UTC (00:00:00 - 23:00:00)
    day_start = pd.Timestamp(f"{selected_date} 00:00:00", tz="UTC")
    day_end = pd.Timestamp(f"{selected_date} 23:00:00", tz="UTC")

    # 3. Filter target day window
    df_day = df_day[(df_day['ts_target'] >= day_start) & (df_day['ts_target'] <= day_end)].copy()

    if df_day.empty:
        st.warning(f"No data available for {label} on {selected_date}.")
        return

    # 4. Deduplication keeping intact UTC timeline
    if 'created_at' in df_day.columns:
        df_day = df_day.sort_values(by=['ts_target', 'created_at'], ascending=[True, True])
    
    df_day = df_day.drop_duplicates(subset=['ts_target'], keep='last').sort_values('ts_target')

    # 5. Generate X-axis in local time solely for visualization display
    target_tz = env.tz_timezone
    if not target_tz:
        raise WError(
            "Failed to identify attribute 'tz_timezone'", code=WaidExit.DATA_FAIL
        )

    df_day['ts_display'] = (
        df_day['ts_target']
        .dt.tz_convert(target_tz)
        .dt.tz_localize(None)
    )

    # -------------------------------------------------------------------------
    # Reconstruct/Extract local sensor reading (Ecowitt)
    # -------------------------------------------------------------------------
    if f'actual_{key}' in df_day.columns and df_day[f'actual_{key}'].notnull().any():
        df_day[f'ecowitt_{key}'] = pd.to_numeric(df_day[f'actual_{key}'], errors='coerce')
    elif f'pred_{key}' in df_day.columns and f'diff_{key}' in df_day.columns:
        # For all features (including solar): actual = pred - diff
        df_day[f'ecowitt_{key}'] = df_day[f'pred_{key}'] - df_day[f'diff_{key}']
    else:
        df_day[f'ecowitt_{key}'] = np.nan

    # Clean numeric types
    df_day[f'ecowitt_{key}'] = pd.to_numeric(df_day[f'ecowitt_{key}'], errors='coerce')

    # Physical clipping bounds (prevents negative values due to sensor/model noise)
    if key in ['wind', 'rain', 'solar'] and f'ecowitt_{key}' in df_day.columns:
        df_day[f'ecowitt_{key}'] = df_day[f'ecowitt_{key}'].clip(lower=0.0)
    elif key == 'rh' and f'ecowitt_{key}' in df_day.columns:
        df_day[f'ecowitt_{key}'] = df_day[f'ecowitt_{key}'].clip(lower=0.0, upper=100.0)

    st.subheader(f"Feature: {label} ({unit})")
    
    col1, col2, col3 = st.columns(3)

    mae_series = df_day[f'abs_error_{key}'].dropna() if f'abs_error_{key}' in df_day.columns else pd.Series()
    mae_era5 = mae_series.mean() if not mae_series.empty else None

    bias_series = df_day[f'historical_bias_{key}'].dropna() if f'historical_bias_{key}' in df_day.columns else pd.Series()
    bias = bias_series.mean() if not bias_series.empty else 0.0

    drift_series = df_day[f'drift_vs_bias_{key}'].dropna() if f'drift_vs_bias_{key}' in df_day.columns else pd.Series()
    drift = drift_series.mean() if not drift_series.empty else 0.0

    with col1:
        st.metric("MAE (Pred vs ERA5)", f"{mae_era5:.2f} {unit}" if mae_era5 is not None else "N/A (Pending ERA5)")
    with col2:
        st.metric("Historical Bias", f"{bias:+.2f} {unit}")
    with col3:
        st.metric("Drift vs Bias", f"{drift:+.2f} {unit}")

    st.markdown("---")

    # 1. Model Prediction vs Local Sensor (Ecowitt)
    st.markdown("#### 1. Model Prediction vs Local Sensor (Ecowitt)")
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df_day['ts_display'], y=df_day[f'pred_{key}'], name='Prediction', mode='lines+markers', line=dict(color='#1f77b4', width=2)))
    if f'ecowitt_{key}' in df_day.columns:
        fig1.add_trace(go.Scatter(x=df_day['ts_display'], y=df_day[f'ecowitt_{key}'], name='Actual (Ecowitt)', mode='lines+markers', line=dict(color='#2ca02c', width=2, dash='dot')))
    fig1.update_layout(
        height=320, 
        hovermode="x unified", 
        yaxis_title=unit, 
        margin=dict(l=10, r=10, t=25, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(
        fig1, 
        width="stretch", 
        config=plotly_config, 
        key=f"plotly_fig1_{key}_{selected_date}"
    )

    # 2. Local Sensor (Ecowitt) vs ERA5 Reanalysis Truth
    st.markdown("#### 2. Local Sensor (Ecowitt) vs ERA5 Reanalysis Truth")
    fig2 = go.Figure()
    if f'ecowitt_{key}' in df_day.columns:
        fig2.add_trace(go.Scatter(x=df_day['ts_display'], y=df_day[f'ecowitt_{key}'], name='Actual (Ecowitt)', mode='lines+markers', line=dict(color='#2ca02c', width=2)))
    if f'{key}_era5' in df_day.columns:
        fig2.add_trace(go.Scatter(x=df_day['ts_display'], y=df_day[f'{key}_era5'], name='ERA5 Truth', mode='lines+markers', line=dict(color='#d62728', width=2, dash='dash')))
    fig2.update_layout(
        height=320, 
        hovermode="x unified", 
        yaxis_title=unit, 
        margin=dict(l=10, r=10, t=25, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(
        fig2, 
        width="stretch", 
        config=plotly_config, 
        key=f"plotly_fig2_{key}_{selected_date}"
    )

    # 3. Model Prediction vs ERA5 Reanalysis Truth
    st.markdown("#### 3. Model Prediction vs ERA5 Reanalysis Truth")
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=df_day['ts_display'], y=df_day[f'pred_{key}'], name='Prediction', mode='lines+markers', line=dict(color='#1f77b4', width=2)))
    if f'{key}_era5' in df_day.columns:
        fig3.add_trace(go.Scatter(x=df_day['ts_display'], y=df_day[f'{key}_era5'], name='ERA5 Truth', mode='lines+markers', line=dict(color='#d62728', width=2, dash='dash')))
    fig3.update_layout(
        height=320, 
        hovermode="x unified", 
        yaxis_title=unit, 
        margin=dict(l=10, r=10, t=25, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(
        fig3, 
        width="stretch", 
        config=plotly_config, 
        key=f"plotly_fig3_{key}_{selected_date}"
    )
    

def run_dashboard(env: WaidBoot) -> None:
    """Assembles and executes main Streamlit web application components and layout.

    @param env WaidBoot system environment configuration instance.
    @return None
    """
    st.set_page_config(page_title="WAID Public Analytics", layout="wide")

    # Responsive CSS styling for mobile devices (< 768px)
    st.markdown("""
        <style>
        @media (max-width: 768px) {
            .main .block-container {
                padding-top: 1.5rem !important;
                padding-left: 0.8rem !important;
                padding-right: 0.8rem !important;
            }
            [data-testid="stMetricValue"] {
                font-size: 1.3rem !important;
            }
            h3 {
                font-size: 1.2rem !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("WAID — Public Operational & Quality Monitor")
    
    available_dates = get_available_dates()
    if not available_dates:
        st.warning("Public analytics database not found or empty.")
        return

    today_str = pd.Timestamp.now().strftime('%Y-%m-%d')
    default_index = available_dates.index(today_str) if today_str in available_dates else 0

    # --- SIDEBAR CONFIGURATION ---
    st.sidebar.header("Configuration")
    selected_date = st.sidebar.selectbox("Select Target Day:", available_dates, index=default_index)

    last_inf_ts = fetch_last_inference_timestamp()
    st.sidebar.markdown(f"**Last ML Inference**  \n<small>{last_inf_ts}</small>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    # Quick ERA5 status check
    is_era5_ready = check_era5_availability(selected_date)
    if is_era5_ready:
        st.sidebar.info(
            f"**ERA5 Status:** Ground truth ERA5 data available for selected day `{selected_date}`."
        )
    else:
        st.sidebar.warning("No ERA5 ground truth data currently available for this day.")

    st.markdown(f"### Operational Analysis for Target Date: **{selected_date}**")

    features = {
        "temp": ("Temperature", "°C"),
        "rh": ("Relative Humidity", "%"),
        "pres": ("Pressure", "hPa"),
        "wind": ("Wind Speed", "m/s"),
        "solar": ("Solar Radiation", "W/m²"),
        "rain": ("Hourly Rain", "mm")
    }

    plotly_config = {
        'responsive': True,
        'displayModeBar': False,
        'scrollZoom': False
    }

    feature_tabs = st.tabs([label for label, unit in features.values()])
    
    # Lazy loading: render content only when the user selects a specific tab
    for idx, (key, (label, unit)) in enumerate(features.items()):
        with feature_tabs[idx]:
            render_feature_tab(env, selected_date, key, label, unit, plotly_config)

    st.markdown("---")
    with st.expander("View Raw Database Records & Metrics"):
        # Load full daily table only if requested by user expanding the section
        df_full = load_public_data_for_feature(selected_date, feature=None)
        st.dataframe(df_full, width="stretch")


def main() -> int:
    """Main entry point parsing command-line parameters and initiating workflow execution.

    @return Process exit code (0 for success, non-zero for errors).
    """
    try:      
        parser = argparse.ArgumentParser(description="WAID Streamlit Dashboard & Deploy Packager")
        parser.add_argument("--deploy", action="store_true", help="Executes setup and update of the deployment folder")
        args = parser.parse_args()

        env = WaidBoot()
                
        if args.deploy:
            run_deployment_setup(env)
        else:
            if not args.deploy and get_script_run_ctx() is None:
                logger.error(
                    "\n"
                    "WARNING: this script is a Streamlit application.\n"
                    "Do not run it directly with:\n"
                    "    python src/waid_08_1_viz_streamlit_app.py\n"
                    "\n"
                    "Run it instead with:\n"
                    "    streamlit run waid_08_1_viz_streamlit_app.py\n"
                    "or\n"
                    "    ./src/waid_08_1_viz_streamlit_app.py --deploy\n"
                )
                return WaidExit.INTERNAL_ERROR
            
            run_dashboard(env)

    except WError as e:
        logger.error(f"[WAID ERROR] {e.message}")
        return e.code

    except Exception:
        logger.exception("Unexpected error while running Streamlit dashboard utility")
        return WaidExit.INTERNAL_ERROR

    return WaidExit.SUCCESS


if __name__ == "__main__":
    sys.exit(main())