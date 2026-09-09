#!/usr/bin/env python3

"""
@file waid_08_1_viz_streamlit_app.py
@brief Streamlit public analytics dashboard featuring dedicated tabs for all 6 weather features and 3-way comparisons,
       integrated with automated deployment packaging, dynamic DB loading (SQLite/Supabase), and standard error handling.
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

# Inject configuration path safely
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import WaidBoot, WError, WaidExit


def get_deployment_status() -> str:
    """
    @brief Checks whether the deployment directory exists and is up to date relative to the source script.
    
    @return Deployment status identifier ("MISSING", "OUTDATED", "SYNCED", or "UNKNOWN").
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
    """
    @brief Generates or updates the target deployment directory and assets.
    
    @param env WaidBoot configuration instance.
    """
    deploy_dir = Path(env.deploy_dir)
    src_script = Path(__file__).resolve()
    db_source = Path(env.waid_data_dir / env.deploy_db_file)
    db_dest = Path(deploy_dir / "data" / env.deploy_db_file)

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
        "@file waid_08_1_viz_streamlit_app.py", 
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
    """
    @brief Fetches only the distinct list of available dates from the database for fast dropdown rendering.
    
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

            query = text(f"SELECT DISTINCT DATE(timestamp) AS target_date FROM {env.db_schema_target}.public_forecasts ORDER BY target_date DESC;")
            with engine.connect() as conn:
                df_dates = pd.read_sql_query(query, conn)

            if not df_dates.empty:
                return df_dates['target_date'].astype(str).tolist()
        except Exception as e:
            st.error(f"Error fetching dates from Supabase: {e}")
            return []
    else:
        base_dir = Path(__file__).resolve().parent
        cloud_deploy_db = base_dir / "data" / env.deploy_db_file if base_dir.name == "deploy" else base_dir / "deploy" / "data" / env.deploy_db_file
        local_deploy_db = Path(env.deploy_dir) / "data" / env.deploy_db_file
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
def load_public_data_for_day(target_date: str) -> pd.DataFrame:
    """
    @brief Loads analytics data exclusively for the specified target date.
    
    @param target_date Target date string in YYYY-MM-DD format.
    @return Cleaned pandas DataFrame containing day specific metrics and forecasts.
    """
    try:
        env = WaidBoot()
        deploy_mode = getattr(env, "deploy_mode", os.getenv("WAID_DEPLOY_MODE", "local")).lower()
    except Exception:
        deploy_mode = os.getenv("WAID_DEPLOY_MODE", "local").lower()

    start_ts = f"{target_date} 00:00:00"
    end_ts = f"{target_date} 23:59:59"

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

            query = text(f"""
                SELECT * FROM {env.db_schema_target}.public_forecasts 
                WHERE timestamp >= :start_ts AND timestamp <= :end_ts 
                ORDER BY timestamp ASC;
            """)
            df = pd.read_sql_query(query, engine, params={"start_ts": start_ts, "end_ts": end_ts})

        except Exception as e:
            st.error(f"Supabase connection error: {e}")
            return pd.DataFrame()

    else:
        base_dir = Path(__file__).resolve().parent
        cloud_deploy_db = base_dir / "data" / env.deploy_db_file if base_dir.name == "deploy" else base_dir / "deploy" / "data" / env.deploy_db_file
        local_deploy_db = Path(env.deploy_dir) / "data" / env.deploy_db_file
        db_path = cloud_deploy_db if cloud_deploy_db.exists() else (local_deploy_db if local_deploy_db.exists() else None)
        
        if not db_path or not db_path.exists():
            return pd.DataFrame()

        try:
            with sqlite3.connect(db_path) as conn:
                query = "SELECT * FROM public_forecasts WHERE timestamp >= ? AND timestamp <= ? ORDER BY timestamp ASC"
                df = pd.read_sql_query(query, conn, params=(start_ts, end_ts))
        except Exception as e:
            st.error(f"Local SQLite database error: {e}")
            return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    numeric_cols = [
        'pred_temp', 'pred_rh', 'pred_pres', 'pred_wind', 'pred_rain', 'pred_solar',
        'diff_temp', 'diff_rh', 'diff_pres', 'diff_wind', 'diff_rain', 'diff_solar',
        'historical_bias_temp', 'historical_bias_rh', 'historical_bias_pres', 
        'historical_bias_wind', 'historical_bias_rain', 'historical_bias_solar',
        'drift_vs_bias_temp', 'drift_vs_bias_rh', 'drift_vs_bias_pres', 
        'drift_vs_bias_wind', 'drift_vs_bias_rain', 'drift_vs_bias_solar',
        'temp_era5', 'rh_era5', 'pres_era5', 'wind_era5', 'rain_era5', 'solar_era5',
        'abs_error_temp', 'abs_error_rh', 'abs_error_pres', 'abs_error_wind', 'abs_error_rain', 'abs_error_solar'
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

def run_dashboard(env: WaidBoot) -> None:
    """
    @brief Executes the Streamlit interactive visualization dashboard logic.
    """

    st.set_page_config(page_title="WAID Public Analytics", layout="wide")

    # CSS responsive per ottimizzare i margini e i font sui dispositivi mobili (< 768px)
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

    st.sidebar.header("Configuration")
    selected_date = st.sidebar.sidebar if False else st.sidebar.selectbox("Select Target Day:", available_dates, index=default_index)

    df_day = load_public_data_for_day(selected_date)
    if df_day.empty:
        st.warning(f"No data available for {selected_date}.")
        return

    # Robust timestamp parsing with explicit UTC localization and conversion to local timezone
    df_day['ts_target'] = pd.to_datetime(df_day['timestamp'], errors='coerce')
    if df_day['ts_target'].dt.tz is None:
        df_day['ts_target'] = df_day['ts_target'].dt.tz_localize('UTC')
    
    target_tz = env.tz_timezone
    df_day['ts_target'] = df_day['ts_target'].dt.tz_convert(target_tz).dt.tz_convert(None)  

    for k in ['temp', 'rh', 'pres', 'wind', 'rain', 'solar']:  
        if f'pred_{k}' in df_day.columns and f'diff_{k}' in df_day.columns:
            # Reconstruct Actual = Pred - Diff
            raw_actual = df_day[f'pred_{k}'] - df_day[f'diff_{k}']
            
            if k in ['wind', 'rain', 'solar']:
                # Zero-bounded features (>= 0.0)
                df_day[f'ecowitt_{k}'] = raw_actual.clip(lower=0.0)
            elif k == 'rh':
                # Relative Humidity bounded strictly between 0% and 100%
                df_day[f'ecowitt_{k}'] = raw_actual.clip(lower=0.0, upper=100.0)
            else:
                # Temperature and Pressure (no hard zero boundary)
                df_day[f'ecowitt_{k}'] = raw_actual

    # Estraggo la presenza di ERA5 sui dati caricati del giorno
    era5_available = df_day[df_day['temp_era5'].notnull()]['ts_target'] if 'temp_era5' in df_day.columns else pd.Series()

    if not era5_available.empty:
        st.sidebar.info(
            f"**ERA5 Status:** Ground truth ERA5 data available for selected day `{selected_date}`."
        )
    else:
        st.sidebar.warning("⚠️ No ERA5 ground truth data currently available for this day.")

    st.markdown(f"### Operational Analysis for Target Date: **{selected_date}**")

    features = {
        "temp": ("Temperature", "°C"),
        "rh": ("Relative Humidity", "%"),
        "pres": ("Pressure", "hPa"),
        "wind": ("Wind Speed", "m/s"),
        "solar": ("Solar Radiation", "W/m²"),
        "rain": ("Hourly Rain", "mm")
    }

    # Configurazione Plotly universale e mobile-friendly
    plotly_config = {
        'responsive': True,
        'displayModeBar': False,
        'scrollZoom': False
    }

    feature_tabs = st.tabs([label for label, unit in features.values()])
    
    for idx, (key, (label, unit)) in enumerate(features.items()):
        with feature_tabs[idx]:
            st.subheader(f"Feature: {label} ({unit})")
            
            col1, col2, col3 = st.columns(3)
            mae_era5 = df_day[f'abs_error_{key}'].mean() if f'abs_error_{key}' in df_day.columns else None
            bias = df_day[f'historical_bias_{key}'].mean() if f'historical_bias_{key}' in df_day.columns else 0.0
            drift = df_day[f'drift_vs_bias_{key}'].mean() if f'drift_vs_bias_{key}' in df_day.columns else 0.0

            with col1:
                st.metric("MAE (Pred vs ERA5)", f"{mae_era5:.2f} {unit}" if pd.notnull(mae_era5) else "N/A (Pending ERA5)")
            with col2:
                st.metric("Historical Bias", f"{bias:+.2f} {unit}")
            with col3:
                st.metric("Drift vs Bias", f"{drift:+.2f} {unit}")

            st.markdown("---")

            st.markdown(f"#### 1. Model Prediction vs Local Sensor (Ecowitt)")
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=df_day['ts_target'], y=df_day[f'pred_{key}'], name='Prediction', mode='lines+markers', line=dict(color='#1f77b4', width=2)))
            if f'ecowitt_{key}' in df_day.columns:
                fig1.add_trace(go.Scatter(x=df_day['ts_target'], y=df_day[f'ecowitt_{key}'], name='Actual (Ecowitt)', mode='lines+markers', line=dict(color='#2ca02c', width=2, dash='dot')))
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

            st.markdown(f"#### 2. Local Sensor (Ecowitt) vs ERA5 Reanalysis Truth")
            fig2 = go.Figure()
            if f'ecowitt_{key}' in df_day.columns:
                fig2.add_trace(go.Scatter(x=df_day['ts_target'], y=df_day[f'ecowitt_{key}'], name='Actual (Ecowitt)', mode='lines+markers', line=dict(color='#2ca02c', width=2)))
            if f'{key}_era5' in df_day.columns:
                fig2.add_trace(go.Scatter(x=df_day['ts_target'], y=df_day[f'{key}_era5'], name='ERA5 Truth', mode='lines+markers', line=dict(color='#d62728', width=2, dash='dash')))
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

            st.markdown(f"#### 3. Model Prediction vs ERA5 Reanalysis Truth")
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=df_day['ts_target'], y=df_day[f'pred_{key}'], name='Prediction', mode='lines+markers', line=dict(color='#1f77b4', width=2)))
            if f'{key}_era5' in df_day.columns:
                fig3.add_trace(go.Scatter(x=df_day['ts_target'], y=df_day[f'{key}_era5'], name='ERA5 Truth', mode='lines+markers', line=dict(color='#d62728', width=2, dash='dash')))
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

    st.markdown("---")
    with st.expander("View Raw Database Records & Metrics"):
        st.dataframe(df_day, width="stretch")

def main() -> int:
    """
    @brief Main execution entry point for Streamlit dashboard and deploy packaging.

    @return Process exit status code.
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