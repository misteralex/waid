#!/usr/bin/env python3

"""
@file waid_ecowitt_diagnostics.py
@brief WAID Data Diagnostic for Feature Alignment.
@details Evaluates whether empirical hardware specifications from station metadata
         match real-world records in the database, providing a diagnostic report
         on the effective resolution of each environmental sensor.
@author AF
@date 2026
"""

from config.boot import (
    WaidBoot,
    WError,
    WaidExit,
)
from src.waid_shared import (
    get_station_metadata,
)
import sqlite3
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from loguru import logger


def estimate_resolution(series: pd.Series, name: str) -> float | None:
    """
    @brief Calculates the effective sensor resolution by analyzing the statistical mode
           of consecutive differences between sorted unique values.

    @param series Pandas Series containing raw sensor observations.
    @param name Identifier string for the feature being processed.
    @return Estimated resolution step float, or None if sample size is insufficient.
    """
    clean_data = series.dropna().to_numpy()
    if len(clean_data) < 50:  # Minimum sample size for statistical validity
        return None

    # Find unique values and sort them in ascending order
    uniques = np.sort(np.unique(clean_data))

    if len(uniques) < 2:
        return None

    # Compute step intervals between adjacent unique observations
    diffs = np.diff(uniques)
    diffs = np.round(diffs, 4)  # Suppress Python floating-point precision artifacts
    diffs = diffs[diffs > 0]  # Retain strictly positive step differences

    if len(diffs) == 0:
        return None

    # The estimated resolution corresponds to the most frequent step delta (Statistical Mode)
    return float(pd.Series(diffs).mode().iloc[0])


def run_sensor_diagnostics() -> None:
    """
    @brief Executes database queries against historical records and verifies sensor
           resolutions against the station metadata specifications loaded from DB.
    """
    env = WaidBoot()
    db_path = Path(env.waid_db_file)

    logger.info("=" * 65)
    logger.info("      ECOWITT SENSOR RESOLUTION DIAGNOSTIC TOOL")
    logger.info("=" * 65)
    logger.info(f"Connecting to database: {db_path} ...")

    # Fetch pre-computed station metadata and specs dynamically
    (
        station_id,
        station_name,
        elevation,
        min_days,
        retrain_window,
        sensor_specs,
    ) = get_station_metadata(env)

    logger.info(
        f"Loaded specifications for station '{station_name}' ({station_id})."
    )

    # Extract target DB columns directly from env.output_features
    feature_mapping = [
        {
            "db_column": feature["ecowitt_field"],
            "spec_key": feature["ecowitt_match"],
            "label": feature["name"],
            "unit": feature.get("unit", ""),
        }
        for feature in env.output_features
    ]

    columns_to_query = ", ".join([f'"{f["db_column"]}"' for f in feature_mapping])
    query = f"SELECT {columns_to_query} FROM {env.db.ecowitt_records}"

    logger.info("Extracting historical sensor telemetry...")
    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error(f" SQL Execution Error: {e}")
        return

    total_records = len(df)
    logger.info(
        f"Diagnostics started on {total_records:,} historical records.\n"
    )

    # Output Report Header
    logger.info(
        f"{'SENSOR (Column)':<28} | {'EXPECTED':<8} | {'ESTIMATED':<8} | {'STATUS':<8} | {'DIAGNOSIS'}"
    )
    logger.info("-" * 100)

    # Iterate diagnostic routine across dynamically resolved output features
    for item in feature_mapping:
        col = item["db_column"]
        spec_key = item["spec_key"]
        label = item["label"]
        unit = item["unit"]

        if col not in df.columns:
            continue

        # Fetch expected resolution directly from sensor_specs
        spec = sensor_specs.get(spec_key, {})
        expected = spec.get("resolution", 0.1)

        sensor_series = df[col]

        try:
            estimated = estimate_resolution(sensor_series, col)
        except Exception:
            estimated = None

        if estimated is None:
            status = "WARNING"
            diagnosis = "Insufficient data variation or sensor stuck at zero."
            est_str = "N/A"
        elif np.isclose(estimated, expected, atol=1e-4):
            status = "OK"
            diagnosis = "Sensor strictly adheres to nominal specifications."
            est_str = f"{estimated:.2f} {unit}"
        else:
            status = " ANOMALY"
            est_str = f"{estimated:.4f} {unit}"
            if estimated < expected:
                diagnosis = "Finer resolution than expected."
            else:
                diagnosis = (
                    "Coarser resolution. Possible mechanical wear, obstruction, "
                    "or compressed data."
                )

        logger.info(
            f"{label:<28} | {expected:<5} {unit:<2} | {est_str:<8} | {status:<8} | {diagnosis}"
        )

    logger.info("Diagnostics completed successfully.")
    logger.warning(
        "ANOMALY: possible firmware conversion or electrical float noise"
    )
    logger.info("=" * 100)


if __name__ == "__main__":
    run_sensor_diagnostics()