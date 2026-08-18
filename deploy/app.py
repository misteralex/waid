#!/usr/bin/env python3

"""
@file app.py
@brief Streamlit public analytics dashboard featuring dedicated tabs for all 6 weather features and 3-way comparisons,
       integrated with automated deployment packaging and standard error handling.
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
import plotly.graph_objects as go
from pathlib import Path
from loguru import logger

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
    db_source = Path(env.waid_data_dir) / env.waid_db_deploy_file
    
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
        shutil.copy(db_source, deploy_dir / "data" / "waid_deploy.db")
        logger.success(f"Database successfully copied to: {deploy_dir / 'data' / 'waid_deploy.db'}")
    else:
        logger.warning(f"Source database not found at {db_source}")

    logger.success("Deployment package successfully created!")

@st.cache_data(ttl=300)
def load_public_data() -> pd.DataFrame:
    """
    @brief Loads public analytics data with fallback strategy for Streamlit Cloud.
    """
    # 1. Path per Streamlit Cloud / ambiente di deploy
    base_dir = Path(__file__).resolve().parent
    cloud_deploy_db = base_dir / "data" / "waid_deploy.db" if base_dir.name == "deploy" else base_dir / "deploy" / "data" / "waid_deploy.db"
    
    # 2. Path relativo locale
    local_deploy_db = Path("deploy/data/waid_deploy.db")
    
    if cloud_deploy_db.exists():
        db_path = cloud_deploy_db
    elif local_deploy_db.exists():
        db_path = local_deploy_db
    else:
        try:
            env = WaidBoot()
            db_path = Path(env.deploy_dir) / "data" / env.waid_db_deploy_file
        except Exception:
            return pd.DataFrame()
    
    if not db_path.exists():
        return pd.DataFrame()

    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query("SELECT * FROM public_forecasts ORDER BY timestamp ASC", conn)
        
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
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def run_dashboard() -> None:
    """
    @brief Executes the Streamlit interactive visualization dashboard logic.
    """
    st.set_page_config(page_title="WAID Public Analytics", layout="wide")
    
    if not Path("/mount").exists() and os.environ.get("STREAMLIT_SERVER_PORT") is None:
        status = get_deployment_status()
        if status == "OUTDATED":
            st.warning("**Deploy Outdated**: Run `python waid_08_2_viz_streamlit_app.py --deploy`")
        elif status == "MISSING":
            st.info("**Deploy**: Deployment folder not initialized.")

    st.title("WAID — Public Operational & Quality Monitor")
    
    df = load_public_data()
    if df.empty:
        st.warning("Public analytics database (`waid_deploy.db`) not found or empty.")
        return
    
    # Robust timestamp parsing with explicit UTC conversion and naive stripping for correct chart alignment
    df['ts_target'] = pd.to_datetime(df['timestamp'], errors='coerce')
    if df['ts_target'].dt.tz is not None:
        df['ts_target'] = df['ts_target'].dt.tz_convert(None)
    
    # Time shift to align database UTC timestamps with local sensor time
    df['ts_target'] = df['ts_target'] + pd.Timedelta(hours=2)

    for k in ['temp', 'rh', 'pres', 'wind', 'rain', 'solar']:  
        if f'pred_{k}' in df.columns and f'diff_{k}' in df.columns:
            # Reconstruct Actual = Pred - Diff
            raw_actual = df[f'pred_{k}'] - df[f'diff_{k}']
            
            if k in ['wind', 'rain', 'solar']:
                # Zero-bounded features (>= 0.0)
                df[f'ecowitt_{k}'] = raw_actual.clip(lower=0.0)
            elif k == 'rh':
                # Relative Humidity bounded strictly between 0% and 100%
                df[f'ecowitt_{k}'] = raw_actual.clip(lower=0.0, upper=100.0)
            else:
                # Temperature and Pressure (no hard zero boundary)
                df[f'ecowitt_{k}'] = raw_actual

    # UI Filtering
    df['date_str'] = df['ts_target'].dt.strftime('%Y-%m-%d')
    available_dates = sorted(df['date_str'].dropna().unique().tolist(), reverse=True)
    
    if not available_dates:
        st.warning("No valid dates found in the dataset.")
        return

    today_str = pd.Timestamp.now().strftime('%Y-%m-%d')
    default_index = available_dates.index(today_str) if today_str in available_dates else 0

    st.sidebar.header("Configuration")
    selected_date = st.sidebar.selectbox("Select Target Day:", available_dates, index=default_index)
    
    st.sidebar.info("**ERA5 Latency Note**: ERA5 reanalysis data typically has a ~7 day publication delay. Select older past dates to inspect ERA5 ground truth metrics.")

    df_day = df[df['date_str'] == selected_date].copy()
    if df_day.empty:
        st.warning(f"No data available for {selected_date}.")
        return

    st.markdown(f"### Operational Analysis for Target Date: **{selected_date}**")

    features = {
        "temp": ("Temperature", "°C"),
        "rh": ("Relative Humidity", "%"),
        "pres": ("Pressure", "hPa"),
        "wind": ("Wind Speed", "m/s"),
        "solar": ("Solar Radiation", "W/m²"),
        "rain": ("Hourly Rain", "mm")
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
            fig1.update_layout(height=350, hovermode="x unified", yaxis_title=unit, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig1, use_container_width=True)

            st.markdown(f"#### 2. Local Sensor (Ecowitt) vs ERA5 Reanalysis Truth")
            fig2 = go.Figure()
            if f'ecowitt_{key}' in df_day.columns:
                fig2.add_trace(go.Scatter(x=df_day['ts_target'], y=df_day[f'ecowitt_{key}'], name='Actual (Ecowitt)', mode='lines+markers', line=dict(color='#2ca02c', width=2)))
            if f'{key}_era5' in df_day.columns:
                fig2.add_trace(go.Scatter(x=df_day['ts_target'], y=df_day[f'{key}_era5'], name='ERA5 Truth', mode='lines+markers', line=dict(color='#d62728', width=2, dash='dash')))
            fig2.update_layout(height=350, hovermode="x unified", yaxis_title=unit, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig2, use_container_width=True)

            st.markdown(f"#### 3. Model Prediction vs ERA5 Reanalysis Truth")
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=df_day['ts_target'], y=df_day[f'pred_{key}'], name='Prediction', mode='lines+markers', line=dict(color='#1f77b4', width=2)))
            if f'{key}_era5' in df_day.columns:
                fig3.add_trace(go.Scatter(x=df_day['ts_target'], y=df_day[f'{key}_era5'], name='ERA5 Truth', mode='lines+markers', line=dict(color='#d62728', width=2, dash='dash')))
            fig3.update_layout(height=350, hovermode="x unified", yaxis_title=unit, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    with st.expander("View Raw Database Records & Metrics"):
        st.dataframe(df_day, use_container_width=True)

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
            run_dashboard()

    except WError as e:
        logger.error(f"[WAID ERROR] {e.message}")
        return e.code

    except Exception:
        logger.exception("Unexpected error while running Streamlit dashboard utility")
        return WaidExit.INTERNAL_ERROR

    return WaidExit.SUCCESS

if __name__ == "__main__":
    sys.exit(main())