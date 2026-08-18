#!/usr/bin/env python3

"""
@file waid_08_1_viz_streamlit_update.py
@brief Update and push utility script for the Streamlit dashboard.
@author AF
@date 2026
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from loguru import logger

# Inject configuration path safely
sys.path.append(
    str(Path(os.environ.get("WAID_SOURCE", Path(__file__).resolve().parents[1])).resolve() / "config")
)
from boot import WaidBoot, WError, WaidExit


def run_git_sync(env: WaidBoot) -> None:
    """
    Executes Git synchronization for the deployment folder if production mode is active.
    
    @param env The bootstrap configuration environment instance.
    """
    # Check execution mode: skip automatic git push in development/local setups
    execution_mode = os.environ.get("WAID_ENV", "dev").lower()
    if execution_mode != "prod":
        logger.info(f"Skipping Git synchronization: Current WAID_ENV is '{execution_mode}' (PROD required for auto-push).")
        return

    deploy_dir = Path(env.deploy_dir)
    
    if not deploy_dir.exists():
        raise WError(f"Deployment directory not found at: {deploy_dir}", WaidExit.FILE_NOT_FOUND)

    try:
        # Ensure we are operating within the repository context
        os.chdir(Path(env.waid_source_root))
        
        logger.info("Starting Git synchronization for the deployment folder...")
        
        # 1. Add
        subprocess.run(["git", "add", str(deploy_dir)], check=True)
        
        # 2. Commit
        commit_msg = "chore: update public dashboard analytics data"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        
        # 3. Push
        subprocess.run(["git", "push"], check=True)
        
        logger.success("Git synchronization successfully completed on GitHub.")
        
    except subprocess.CalledProcessError as e:
        raise WError(f"Error during Git operation: {e}", WaidExit.INTERNAL_ERROR)
    

def main() -> int:
    """
    Main entry point for automatic dashboard updates.
    
    @return Execution exit status code.
    """
    try:
        parser = argparse.ArgumentParser(description="WAID Streamlit Dashboard Update Utility")
        args = parser.parse_args()

        env = WaidBoot()
        run_git_sync(env)

    except WError as e:
        logger.error(f"[WAID ERROR] {e.message}")
        return e.code
    except Exception as e:
        logger.exception("Unexpected error during Git update")
        return WaidExit.INTERNAL_ERROR

    return WaidExit.SUCCESS

if __name__ == "__main__":
    sys.exit(main())