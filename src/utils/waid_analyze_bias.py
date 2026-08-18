#!/usr/bin/env python3

import pandas as pd
import sqlite3
import argparse
import os
import sys
from pathlib import Path
from loguru import logger

##
# @file waid_analyze_bias.py
# @brief Bias Analysis: sanity check to validate data ready for ML training
# @details Performs Phase 3 (Transform/Alignment) of the data pipeline
# @author AF
# @date 2026

# Import WaidBoot configuration and utility classess
sys.path.append(str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config"))
from boot import (
    WaidBoot,
    validate_period,
    WError,
)

def report_bias_metrics(
    env : WaidBoot,
    period : str,
) -> None:
    """
    @brief Queries and logs statistical bias metrics for a specific target month.
    @param env WaidBoot configuration and environment context instance.
    @param period Target period datetime object.
    @return None or exit code integer if skipped.
    """

    requested_period = period.strftime("%Y-%m")
   
    conn = sqlite3.connect(env.waid_db)
    df = pd.read_sql_query(
        """
        SELECT *
        FROM int_matches_bias
        WHERE strftime('%Y-%m', timestamp) = ?
        ORDER BY timestamp
        """,
        conn,
        params=(requested_period,),
    )
    
    # Validate data ready for required period
    if df.empty:
        logger.warning(f"[WAID SKIPPED/WARNING] No data found for period '{requested_period}'. Skipping bias report.")
        return env.waid_exit.SUCCESS

    logger.debug("=" * 62)
    logger.debug("BIAS REPORT")
    logger.debug("=" * 62)
    logger.debug(f"Period : {requested_period}")
    logger.debug(f"Samples: {len(df):,}")
    logger.debug("")

    logger.debug(
        f"{'Feature':<18}"
        f"{'Unit':<8}"
        f"{'Mean':>12}"
        f"{'Std Dev':>12}"
        f"{'Min':>10}"
        f"{'Max':>10}"
    )
    logger.debug("-" * 62)

    for feat in env.output_features:
        name = feat["name"]
        unit = feat["unit"]
        column = feat["bias_col"]
        
        logger.debug(
            f"{name:<18}"
            f"{unit:8}"
            f"{df[column].mean():>12.2f}"
            f"{df[column].std():>12.2f}"
            f"{df[column].min():>10.2f}"
            f"{df[column].max():>10.2f}"
        )
        

def main() -> int:
    """
    @brief Main entry point for the bias analysis execution script.
    @return Integer exit code status value.
    """
    
    try:
        env = WaidBoot()
    
        parser = argparse.ArgumentParser(
            description="WAID: bias report of the features",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "--period",
            type=validate_period,
            help="Target month in YYYY-MM format",
        )

        if len(sys.argv) == 1:
            parser.print_help()
            logger.error("You must specify a valid input")
            return env.waid_exit.INPUT_FAIL
        
        requested_period = parser.parse_args().period
        return report_bias_metrics(env, requested_period)

    except WError as e:
        logger.error(e)
        return e.code

    except Exception:
        logger.exception("Unexpected error while process bias report")
        return env.waid_exit.INTERNAL_ERROR

if __name__ == "__main__":
    sys.exit(main())