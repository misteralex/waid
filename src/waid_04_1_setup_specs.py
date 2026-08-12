#!/usr/bin/env python3

"""
@file waid_04_3_setup_specs.py
@brief Hardware Sensor Specifications Setup and Profiling.
@details Initializes and updates empirical sensor characteristics (resolution and deadbands) 
         for the 6 core features within the station_metadata table.
@author AF
@date 2026
"""

import os
import sys
import json
import sqlite3
import numpy as np
import pandas as pd
from pathlib import Path
from loguru import logger

# Inject configuration path into python execution environment
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import WaidBoot, WError, WaidExit

def ensure_sensor_specs_column(env: WaidBoot) -> None:
    """Ensures the sensor_specs column exists in the station_metadata table."""
    try:
        with sqlite3.connect(env.waid_db) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(station_metadata);")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "sensor_specs" not in columns:
                logger.info("Adding 'sensor_specs' column to 'station_metadata' table...")
                cursor.execute("ALTER TABLE station_metadata ADD COLUMN sensor_specs TEXT;")
                conn.commit()
                logger.success("Column 'sensor_specs' added successfully.")
            else:
                logger.info("Column 'sensor_specs' already exists in 'station_metadata'.")
    except sqlite3.Error as e:
        raise WError(f"Failed to ensure sensor_specs column: {e}", code=WaidExit.DATA_FAIL)

def profile_or_default_specs(env: WaidBoot) -> dict:
    """Profiles raw data or falls back to robust default hardware specs for the 6 features."""
    default_specs = {
        'ecowitt_temp': {'resolution': 0.1, 'deadband': 0.0},
        'ecowitt_rh': {'resolution': 1.0, 'deadband': 0.0},
        'ecowitt_pres': {'resolution': 0.1, 'deadband': 0.0},
        'ecowitt_wind': {'resolution': 0.1, 'deadband': 0.2},
        'ecowitt_solar': {'resolution': 1.0, 'deadband': 0.0},
        'ecowitt_rain': {'resolution': 0.1, 'deadband': 0.1}
    }
    
    try:
        with sqlite3.connect(env.waid_db) as conn:
            query = """
                SELECT outdoor_temperature_c, abs_pressure_hpa, outdoor_humidity, 
                       wind_m_s, solar_rad_w_m2, hourly_rain_mm 
                FROM ecowitt_records 
                WHERE timestamp >= datetime('now', '-14 days')
            """
            df = pd.read_sql(query, conn)
            
        if df.empty or len(df) < 50:
            logger.warning("Insufficient raw data for profiling. Using professional default specs.")
            return default_specs

        specs = default_specs.copy()

        feature_map = {
            feature["ecowitt_match"]: feature["ecowitt_field"]
            for feature in env.output_features
        }
        logger.debug(f"Profiling sensor specs for features: {list(feature_map.keys())}: {list(feature_map.values())}")
        
        for target, col in feature_map.items():
            series = df[col].dropna()
            if len(series) < 10:
                continue
            
            diffs = np.abs(np.diff(series.values))
            non_zero_diffs = diffs[diffs > 1e-4]
            if len(non_zero_diffs) > 0:
                estimated_res = float(np.percentile(non_zero_diffs, 25))
                specs[target]['resolution'] = max(0.01, round(estimated_res, 2))

            if target == 'ecowitt_wind':
                non_zero = series[series > 0]
                if not non_zero.empty:
                    specs[target]['deadband'] = float(np.percentile(non_zero, 10))
            elif target == 'ecowitt_rain':
                non_zero = series[series > 0]
                if not non_zero.empty:
                    specs[target]['deadband'] = float(non_zero.min())

        logger.success(f"Empirically profiled sensor specs: {specs}")
        return specs

    except Exception as e:
        logger.warning(f"Profiling failed ({e}). Falling back to default hardware specs.")
        return default_specs

def update_station_specs(env: WaidBoot, specs: dict) -> None:
    """Persists the sensor specs JSON into the station_metadata table."""
    specs_json = json.dumps(specs)
    station_id = env.ecowitt_station_id
    
    try:
        with sqlite3.connect(env.waid_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE station_metadata SET sensor_specs = ? WHERE station_id = ?",
                (specs_json, station_id)
            )
            conn.commit()
            logger.success(f"Station metadata successfully updated with sensor specs for station '{station_id}'.")
    except sqlite3.Error as e:
        raise WError(f"Failed to update station metadata with sensor specs: {e}", code=WaidExit.DATA_FAIL)

def main() -> int:
    try:
        env = WaidBoot()
        logger.info("Initializing station sensor specifications setup...")
        
        ensure_sensor_specs_column(env)
        specs = profile_or_default_specs(env)
        update_station_specs(env, specs)
        
        return WaidExit.SUCCESS
    
    except WError as e:
        logger.error(f"[WAID ERROR] {e.message}")
        return e.code
    except Exception:
        logger.exception("Unexpected failure during sensor specs setup")
        return WaidExit.INTERNAL_ERROR

if __name__ == "__main__":
    sys.exit(main())