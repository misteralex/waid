#!/usr/bin/env python3

"""
@file waid_prefect_manager.py
@brief WAID Prefect Workflow Lifecycle Manager.
@details Manages the Prefect server initialization, dynamic configuration generation, 
         deployment registration, initial triggering, and worker lifecycle for production execution.
@author AF
@date 2026
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import yaml
import time
import httpx
from loguru import logger
from datetime import datetime

# Import WaidBoot configuration and utility classes
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import (
    WaidBoot,
    WError,
    WaidExit,
)

def get_subprocess_env() -> dict:
    """
    @brief Helper function to ensure all Prefect subprocesses use consistent environment settings.
    @return Dictionary containing copied environment variables with Prefect overrides.
    """
    env_vars = os.environ.copy()
    env_vars["PREFECT_API_URL"] = os.getenv("PREFECT_API_URL", "http://127.0.0.1:4200/api")
    
    # Do not override PREFECT_HOME if provided by container environment
    if "PREFECT_HOME" not in env_vars:
        env_vars["PREFECT_HOME"] = "/tmp/prefect"
        
    return env_vars


def parse_arguments(
    env: WaidBoot
):
    """
    @brief Parses command line arguments for the Prefect manager.
    @param env WaidBoot configuration instance.
    @return Tuple containing parsed arguments and unrecognized arguments.
    """
    parser = argparse.ArgumentParser(description="WAID Prefect Manager")
    parser.add_argument(
        "--period",
        type=str,
        default=None,
        help="Target month in YYYY-MM format. Defaults to current month if omitted."
    )
    parser.add_argument(
        "--skip-ingestion",
        action="store_true",
        help="Skip data ingestion and profile steps"
    )
    parser.add_argument(
        "--auto-backfill",
        action="store_true",
        default=env.auto_backfill,
        help="Execute historical data backfill (Steps 01-03 only)"
    )
    return parser.parse_known_args()


def generate_prefect_yaml(
    env: WaidBoot, 
    cli_args
) -> Path:
    """
    @brief Dynamically generates the prefect.yaml file ensuring parameters are correctly bound.
    @param env WaidBoot configuration instance.
    @param cli_args Parsed command line arguments.
    @return Path object pointing to the generated prefect.yaml file.
    """
    yaml_path = Path("prefect.yaml")
    parameters = {}
    
    if cli_args.auto_backfill:
        logger.info("Configuring deployment for AUTO-BACKFILL mode...")
        parameters["auto_backfill"] = True
    else:
        # Default to current month dynamically if period is not explicitly provided
        target_period = cli_args.period or datetime.now().strftime("%Y-%m")
        logger.info(f"Generating dynamic {yaml_path.name} configuration for target period: {target_period}...")
        parameters["period"] = target_period

    # Pass the boolean CLI argument directly to override default flow parameters
    parameters["skip_ingestion"] = cli_args.skip_ingestion

    config = {
        "prefect-version": "2.x",
        "name": "waid-project",
        "deployments": [
            {
                "name": getattr(env, "deployment_name", "waid-incremental-production"),
                "entrypoint": getattr(env, "entrypoint", "waid_orchestrate.py:waid_main_flow"),
                "work_pool": {
                    "name": getattr(env, "work_pool", "default-agent-pool"),
                },
                "schedule": {
                    # Convert hours to seconds
                    "interval": int(os.getenv("SCHEDULER_INTERVAL_HOURS", 1)) * 3600,  
                },
                "parameters": parameters,
            }
        ]
    }
    
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, sort_keys=False, default_flow_style=False)
        
    logger.info(f"Successfully generated {yaml_path.name} with parameters: {parameters}")
    return yaml_path


def run_deployment():
    """
    @brief Executes Prefect deployment registration (`prefect deploy --all`).
    """
    logger.info("Registering Prefect deployment (`prefect deploy --all`)...")
    
    env_vars = get_subprocess_env()
    
    result = subprocess.run(
        ["prefect", "deploy", "--all"],
        env=env_vars,
        capture_output=True,
        text=True
    )
    
    print("--- STDOUT ---")
    print(result.stdout)
    print("--- STDERR ---")
    print(result.stderr)
    
    if result.returncode != 0:
        logger.error(f"Failed to register Prefect deployment with code {result.returncode}")
        sys.exit(1)
    
    logger.info("Prefect deployment successfully registered.")


def start_worker(env: WaidBoot):
    """
    @brief Starts the Prefect worker process listening on the configured work pool.
    @param env WaidBoot configuration instance.
    """
    work_pool = getattr(env, "work_pool", "default-agent-pool")
    logger.info(f"Starting Prefect worker for work pool: '{work_pool}'...")
    
    env_vars = get_subprocess_env()
    try:
        subprocess.run(
            ["prefect", "worker", "start", "--pool", work_pool],
            env=env_vars,
            check=True
        )
    except KeyboardInterrupt:
        logger.info("Prefect worker stopped gracefully by user.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Prefect worker crashed with error code {e.returncode}")
        sys.exit(e.returncode)


def ensure_prefect_server(port: int = 4200, timeout: int = 5) -> bool:
    """
    @brief Checks if the Prefect server is active; if not, starts it non-interactively in the background.
    @param port HTTP port for the Prefect server API.
    @param timeout Request timeout seconds for health check.
    @return True if server is ready, False otherwise.
    """
    api_url = f"http://127.0.0.1:{port}/api/health"
    
    try:
        response = httpx.get(api_url, timeout=timeout)
        if response.status_code == 200:
            logger.info("Prefect server is active and reachable.")
            return True
    except httpx.RequestError:
        pass

    logger.warning("Prefect server not detected. Starting automatically in background...")
    
    # Configure execution environment to disable prompts and telemetry
    env = get_subprocess_env()
    env["PYTHONUNBUFFERED"] = "1"
    env["PREFECT_SERVER_ANALYTICS_ENABLED"] = "false"
    env["PREFECT_CLI_PROMPT"] = "false"
    env["PREFECT_SERVER_ALLOW_UPGRADES"] = "true"

    # Pre-migrate DB silently to ensure schema is ready before Uvicorn starts
    subprocess.run(
        ["prefect", "server", "database", "upgrade", "-y"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False
    )
    
    server_process = subprocess.Popen(
        ["prefect", "server", "start", "--host", "0.0.0.0", "--port", str(port)],
        stdout=sys.stdout,
        stderr=sys.stderr,
        env=env
    )
    
    start_time = time.time()
    max_wait = 45
    
    while time.time() - start_time < max_wait:
        if server_process.poll() is not None:
            logger.error(f"❌ Prefect process terminated with code {server_process.returncode}.")
            return False
            
        try:
            response = httpx.get(api_url, timeout=2)
            if response.status_code == 200:
                logger.info("Prefect server successfully started in background!")
                return True
        except httpx.RequestError:
            time.sleep(1)
            
    logger.error(f"❌ Timeout ({max_wait}s) reached. Unable to connect to {api_url}.")
    return False


def ensure_work_pool(env: WaidBoot):
    """
    @brief Ensures the configured work pool exists on the Prefect server.
    @param env WaidBoot configuration instance.
    """
    work_pool = getattr(env, "work_pool", "default-agent-pool")
    logger.info(f"Checking existence of Prefect work pool: '{work_pool}'...")
    
    env_vars = get_subprocess_env()

    result = subprocess.run(
        ["prefect", "work-pool", "create", work_pool, "--type", "process"],
        env=env_vars,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logger.info(f"Work pool '{work_pool}' created successfully.")
    else:
        logger.info(f"Work pool '{work_pool}' already exists or is configured.")
        
        
def trigger_initial_run(env: WaidBoot):
    """
    @brief Immediately triggers the first run of the registered deployment.
    @param env WaidBoot configuration instance.
    """
    deployment_name = f"{getattr(env, 'flow_name', 'WAID Main Orchestrator Flow')}/{getattr(env, 'deployment_name', 'waid-incremental-production')}"
    logger.info(f"Immediately triggering deployment run for: '{deployment_name}'...")
    
    env_vars = get_subprocess_env()

    try:
        subprocess.run(
            ["prefect", "deployment", "run", deployment_name],
            env=env_vars,
            check=True
        )
        logger.info("Initial run triggered successfully!")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error while triggering initial deployment run: {e}")
        
        
def main():
    """
    @brief Main entry point for the Prefect workflow lifecycle manager.
    """
    logger.info("Initializing WAID Prefect Manager...")
 
    # Initialize environment configuration
    env = WaidBoot()
       
    # Parse CLI arguments
    parsed_args, extra_args = parse_arguments(env)
    
    # Step 1: Check Prefect server activation
    if not ensure_prefect_server():
        sys.exit(1)
    
    # Step 2: Generate dynamic prefect.yaml ensuring parameters are bound
    generate_prefect_yaml(env, parsed_args)
    
    # Step 3: Ensure work pool exists
    ensure_work_pool(env)
    
    # Step 4: Deploy flows to Prefect Server
    run_deployment()
    
    # Step 5: Trigger immediate flow run so we don't have to wait 1 hour
    trigger_initial_run(env)
    
    # Step 6: Start Worker
    start_worker(env)


if __name__ == "__main__":
    main()