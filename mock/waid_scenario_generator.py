#!/usr/bin/env python3

"""
@file waid_scenario_generator.py
@brief Scenario and anomaly generator for WAID mock testing (M030) with CLI support.
@details Generates isolated scenario test directories utilizing env.waid_mock_dir 
         and env.waid_mock_data_dir as baseline references.
"""

import shutil
import argparse
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from typing import Optional, Literal
from config.boot import (
    WaidBoot,
    WError,
    WaidExit,
)

class WAIDScenarioGenerator:
    """
    @brief Generates isolated test scenario directories tailored to specific ML 
           and pipeline integration testing states under WAID_MOCK_DATA_DIR.
    """

    def __init__(self, env: WaidBoot) -> None:
        """
        @brief Initializes the scenario generator using reference mock directories.
        @param env referencing global parameters.
        """
        self.env = env
        self.ecowitt_src = env.waid_mock_data_dir / "ecowitt"
        self.era5_src = env.waid_mock_data_dir / "era5"

    def build_scenario(
        self,
        env: WaidBoot,
        scenario_name: str, 
        scenario_mode: Literal["no_data", "insufficient_data", "training_required", "inference_ready", "anomaly_block"] = "inference_ready",
        year_tag: str = "2026", 
        month: str = "09", 
        target: Literal["none", "ecowitt", "era5", "both"] = "none",
        anomaly_type: Optional[str] = None,
        force_recreate: bool = False
    ) -> Path:
        """
        @brief Generates an isolated scenario directory structure based on operational mode.
               If the folder exists and force_recreate is False, it skips creation.
        @param self Instance of WAIDScenarioGenerator.
        @param scenario_name Name of the scenario folder.
        @param scenario_mode Operational state.
        @param year_tag Reference year tag.
        @param month Target month string.
        @param target Target source for anomalies.
        @param anomaly_type Type of transformation.
        @param force_recreate Whether to overwrite existing scenario directory.
        @return Path Path to the created scenario 'data' directory.
        """
        scenario_dir = Path(self.env.waid_mock_data_dir) / "scenarios" / scenario_name
        data_out = scenario_dir / "data"

        # Check existence rule: if folder exists and not forcing recreate, do nothing
        if scenario_dir.exists() and not force_recreate:
            print(f"[SCENARIO] Scenario '{scenario_name}' already exists. Skipping creation.")
            return data_out

        eco_out = data_out / "ecowitt"
        era5_out = data_out / "era5"
        
        if scenario_dir.exists():
            shutil.rmtree(scenario_dir)
        eco_out.mkdir(parents=True, exist_ok=True)
        era5_out.mkdir(parents=True, exist_ok=True)

        src_eco_file = self.ecowitt_src / f"{year_tag}{month}.csv"
        src_era5_file = self.era5_src / f"era5_{year_tag}_{month}.nc"

        if scenario_mode == "no_data":
            print(f"[{scenario_name}] Mode 'no_data': Created empty telemetry structure.")
            return data_out

        if src_eco_file.exists():
            df_eco = pd.read_csv(src_eco_file)
        else:
            df_eco = self._create_fallback_telemetry()

        if scenario_mode == "insufficient_data":
            df_eco = df_eco.head(144)  # < 14 days guardrail

        if target in ["ecowitt", "both"] and anomaly_type:
            df_eco = self._apply_transformation(df_eco, anomaly_type)

        dst_eco_file = eco_out / f"{year_tag}{month}.csv"
        df_eco.to_csv(dst_eco_file, index=False)

        dst_era5_file = era5_out / f"era5_{year_tag}_{month}.nc"
        if src_era5_file.exists():
            shutil.copy(src_era5_file, dst_era5_file)
        else:
            dst_era5_file.touch()

        models_out = data_out / "models"
        models_out.mkdir(exist_ok=True)
        if scenario_mode == "inference_ready":
            (models_out / "lstm_nowcast_v1.h5").touch()

        print(f"[SCENARIO] Successfully built scenario '{scenario_name}' in mode '{scenario_mode}'.")
        return data_out

    def _apply_transformation(self, df: pd.DataFrame, anomaly_type: str) -> pd.DataFrame:
        """
        @brief Applies synthetic anomalies or data transformations to the telemetry dataframe.
        @param df Input telemetry DataFrame.
        @param anomaly_type Type of anomaly to inject.
        @return DataFrame Modified telemetry DataFrame.
        """
        df_mod = df.copy()
        if anomaly_type == "heatwave" and "temp" in df_mod.columns:
            df_mod.loc[10:50, "temp"] += 7.5
        elif anomaly_type == "physics_anomaly" and "solar_radiation" in df_mod.columns:
            df_mod.loc[0:5, "solar_radiation"] = 450.0
        return df_mod

    def _create_fallback_telemetry(self) -> pd.DataFrame:
        """
        @brief Generates default fallback telemetry data when source CSV is missing.
        @return DataFrame Default mock telemetry DataFrame.
        """
        timestamps = pd.date_range(start="2026-09-01 00:00:00", periods=1440, freq="10min")
        return pd.DataFrame({
            "timestamp": timestamps,
            "temp": 18.5,
            "humidity": 60.0,
            "barom_rel": 1013.2,
            "solar_radiation": 0.0,
            "wind_speed": 1.2
        })

if __name__ == "__main__":
    env = WaidBoot()
    parser = argparse.ArgumentParser(description="WAID Scenario Generator CLI")
    parser.add_argument("--set-scenario", required=True, choices=["no_data", "insufficient_data", "training_required", "inference_ready", "anomaly_block"])
    parser.add_argument("--name", default=None, help="Custom scenario folder name")
    args = parser.parse_args()

    generator = WAIDScenarioGenerator(env)
    scenario_name = args.name or f"scenario_{args.set_scenario}"
    generator.build_scenario(env, scenario_name=scenario_name, scenario_mode=args.set_scenario)