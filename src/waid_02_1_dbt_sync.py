#!/usr/bin/env python3

"""
@file waid_02_1_dbt_sync.py
@brief Setup main SQLite database and dbt environment
@details Uses WaidBoot/WaidDB internal methods to ensure the main database exists and to setup dbt
@author AF
@date 2026
"""

from config.boot import (
    WaidBoot,
    WError,
    WaidExit,
)
from src.waid_shared import (
    run_dbt_command,
)
import sys
from loguru import logger
import subprocess
import json


def _check_main_database(env: WaidBoot) -> int:
    """
    @brief Setup main SQLite database (i.e. waid.db) using WaidDB internal methods from config.boot.py.
    @param env: WaidBoot configuration instance.
    @return Process exit code integer.
    """
    logger.info(f"Checking main SQLite database at: {env.waid_db_file}")

    # Invokes database initialization directly via the unified database manager inside boot.py
    exit_code = env.db.init_main_database(env.waid_db_file)
    
    if exit_code == getattr(env.waid_exit, "DB_ALREADY_EXISTS", 8):
        logger.warning("Database already exists. Proceeding with existing database.")
        return env.waid_exit.SUCCESS
    elif exit_code != 0:
        logger.error(f"Database initialization failed with exit code {exit_code}")
        return exit_code
        
    logger.success("New DB Setup completed successfully.")
    return env.waid_exit.SUCCESS


def waid_sync_dbt_clean(env) -> int:
    """
    @brief Cleans dbt target directory and dependencies.
    @param env: Configuration object containing source directory paths.
    @return Process return code integer.
    """
    return run_dbt_command(["dbt", "clean"], env)


def waid_sync_dbt_deps(env) -> int:
    """
    @brief Installs dbt project dependencies.
    @param env: Configuration object containing source directory paths.
    @return Process return code integer.
    """
    return run_dbt_command(["dbt", "deps"], env)


def waid_sync_dbt_compile(env) -> int:
    """
    @brief Compiles the dbt project models.
    @param env: Configuration object containing source directory paths.
    @return Process return code integer.
    """
    return run_dbt_command(["dbt", "compile"], env)


def waid_sync_dbt_dump_vars(env) -> int:
    """
    @brief Executes dbt dump_vars operation.
    @param env: Configuration object containing source directory paths.
    @return Process return code integer.
    """
    return run_dbt_command(["dbt", "run-operation", "dump_vars"], env)


def run_dbt_sequence(env: WaidBoot) -> int:
    """
    Executes the sequence of dbt maintenance and preparation commands:
    clean, deps, compile, and dump_vars using run_dbt_command.
    
    @param env: WaidBoot instance containing configuration paths and parameters.
    @return: Exit code integer (0 on success, or non-zero on failure).
    """
    steps = [
        ("waid_sync_dbt_clean", ["dbt", "clean"]),
        ("waid_sync_dbt_deps", ["dbt", "deps"]),
        ("waid_sync_dbt_compile", ["dbt", "compile"]),
        ("waid_sync_dbt_dump_vars", ["dbt", "run-operation", "dump_vars"])
    ]
    
    for step_name, base_cmd in steps:
        logger.info(f"Executing: {step_name}")
        
        exit_code = run_dbt_command(base_cmd, env)
        if exit_code != 0:
            logger.error(f"Error: Step '{step_name}' failed with exit code {exit_code}")
            return exit_code
            
    logger.info("=== All dbt sequence steps completed successfully ===")
    return 0

    
def main() -> int:
    """
    @brief Main execution entry point for SQLite database setup and dbt environment synchronization.
    @return Process exit code integer.
    """
    try:
        env = WaidBoot()
        
        db_setup_result = _check_main_database(env)
        if db_setup_result != env.waid_exit.SUCCESS:
            raise WError("Cannot validate main database.", db_setup_result)
        
        run_dbt_sequence(env)
        
        logger.success("=== SQLite Database Setup and dbt Environment Synchronization Completed Successfully ===")

    except WError as e:
        logger.error(e)
        return e.code
        
    except Exception:
        logger.exception("Unexpected error while validating environments")
        return env.waid_exit.INTERNAL_ERROR

    return env.waid_exit.SUCCESS


if __name__ == "__main__":
    sys.exit(main())