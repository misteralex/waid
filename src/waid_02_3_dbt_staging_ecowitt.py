#!/usr/bin/env python3

"""
@file waid_02_3_dbt_staging_ecowitt.py
@brief Runs and tests matched datasets in dbt using a local helper function.
@details Uses WaidBoot internal methods and a local subprocess helper to run and test matched records in dbt.
@author AF
@date 2026
"""

from config.boot import (
    WaidBoot,
    WError,
    WaidExit,
    validate_period,
)
from waid_shared import (
    run_dbt_command,
)
import sys
import argparse
import json
from loguru import logger


def main() -> int:
    """
    @brief Executes and tests dbt staging models for Ecowitt.
    @return Process exit code integer.
    """
    try:
        env = WaidBoot()
        
        parser = argparse.ArgumentParser(
            description="WAID: running and testing matched dataset in dbt.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
                
        parser.add_argument(
            "--period",
            type=validate_period,
            help="Target month in YYYY-MM format",
        )
        
        parsed_args = parser.parse_args()
        period_val = parsed_args.period

        logger.info(f"Processing database table: {env.db.stg_ecowitt}")
        
        # int_matches_bias is a raw source [DB-Raw]
        code = run_dbt_command(
            [
                "dbt", "run", "--select", 
                env.db.stg_ecowitt
            ],
            env,
            period=period_val,
        )
        if code != env.waid_exit.SUCCESS:
            return code

        code = run_dbt_command(
            [
                "dbt", "test", "--select", 
                env.db.stg_ecowitt
            ],
            env,
            period=period_val,
        )
        if code != env.waid_exit.SUCCESS:
            return code
        
        logger.success("=== dbt Environment Synchronization Completed Successfully ===")

    except WError as e:
        logger.error(e)
        return e.code
        
    except Exception:
        logger.exception("Unexpected error while validating environments")
        return WaidExit.INTERNAL_ERROR

    return env.waid_exit.SUCCESS


if __name__ == "__main__":
    sys.exit(main())