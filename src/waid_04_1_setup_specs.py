#!/usr/bin/env python3

"""
@file waid_04_1_setup_specs.py
@brief Hardware Sensor Specifications Setup and Profiling.
@details Initializes and updates empirical sensor characteristics (resolution and deadbands) 
         for the core features within the station_metadata table using shared utilities.
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

# Inject src path for shared module
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "src")
)
from waid_shared import NOMINAL_SENSOR_SPECS, get_station_metadata


def ensure_sensor_specs_column(env: WaidBoot) -> None:
    """
    @brief Ensures the sensor_specs column exists in the station_metadata table.

    @param env WaidBoot configuration instance.
    @raises WError If database modification fails.
    """
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


def estimate_mode_resolution(series: pd.Series) -> float | None:
    """
    @brief Estimates effective sensor resolution using statistical mode of unique differences.

    @param series Pandas Series containing raw sensor observations.
    @return Estimated resolution step float, or None if sample size is insufficient.
    """
    clean_data = series.dropna().to_numpy()
    if len(clean_data) < 50:
        return None

    uniques = np.sort(np.unique(clean_data))
    if len(uniques) < 2:
        return None

    diffs = np.diff(uniques)
    diffs = np.round(diffs, 4)
    diffs = diffs[diffs > 0]

    if len(diffs) == 0:
        return None

    return float(pd.Series(diffs).mode().iloc[0])


def profile_or_default_specs(env: WaidBoot) -> dict:
    """
    @brief Profiles raw telemetry data or falls back to shared default hardware specs for output features.

    @param env WaidBoot configuration instance.
    @return Dictionary containing resolution and deadband parameters per feature.
    """
    # Retrieve current specs stored in DB (or nominal defaults if DB is empty)
    try:
        _, _, _, _, _, db_specs = get_station_metadata(env)
    except Exception:
        db_specs = NOMINAL_SENSOR_SPECS.copy()

    try:
        with sqlite3.connect(env.waid_db) as conn:
            query = f"""
                SELECT outdoor_temperature_c, abs_pressure_hpa, outdoor_humidity, 
                       wind_m_s, solar_rad_w_m2, hourly_rain_mm 
                FROM {env.ecowitt_table} 
                WHERE timestamp >= datetime('now', '-14 days')
            """
            df = pd.read_sql(query, conn)

        if df.empty or len(df) < 50:
            logger.warning(
                "Insufficient raw data for profiling. Using nominal default specs."
            )
            return db_specs

        specs = db_specs.copy()

        feature_map = {
            feature["ecowitt_match"]: feature["ecowitt_field"]
            for feature in env.output_features
        }

        for target, col in feature_map.items():
            if col not in df.columns:
                continue

            series = df[col].dropna()

            # 1. Estimate resolution using statistical mode
            estimated_res = estimate_mode_resolution(series)
            if estimated_res is not None:
                new_res = round(estimated_res, 4)

                # Compare empirical resolution against NOMINAL default spec from waid_shared
                nominal_res = NOMINAL_SENSOR_SPECS.get(target, {}).get(
                    "resolution", 0.1
                )

                if not np.isclose(new_res, nominal_res, atol=1e-4):
                    logger.warning(
                        f"Sensor resolution deviation for '{target}' ({col}): "
                        f"Nominal={nominal_res}, Profiled Empirical={new_res}. "
                        f"Updating metadata to match effective data granularity."
                    )

                specs[target]["resolution"] = new_res

            # 2. Estimate deadband/threshold for activation features
            if target == "ecowitt_wind":
                non_zero = series[series > 0]
                if not non_zero.empty:
                    specs[target]["deadband"] = float(
                        np.percentile(non_zero, 10)
                    )
            elif target == "ecowitt_rain":
                non_zero = series[series > 0]
                if not non_zero.empty:
                    specs[target]["deadband"] = float(non_zero.min())

        logger.success(f"Empirically profiled sensor specs: {specs}")
        return specs

    except Exception as e:
        logger.warning(
            f"Profiling failed ({e}). Falling back to nominal default specs."
        )
        return NOMINAL_SENSOR_SPECS.copy()


def update_station_specs(env: WaidBoot, specs: dict) -> None:
    """
    @brief Persists the sensor specs JSON into the station_metadata table.

    @param env WaidBoot configuration instance.
    @param specs Dictionary of sensor specifications to serialize.
    @raises WError If metadata database update fails.
    """
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
    """
    @brief Main execution entry point for hardware sensor specification profiling and setup.

    @return Exit code integer indicating process status.
    """
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