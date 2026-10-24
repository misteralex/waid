#!/usr/bin/env python3

"""
@file waid_validate_env.py
@brief Modular validation and environment synchronization tool for the WAID repository.
@details Manage global system packages and both ".env" and ".env-dbt" python environments using pip-tools.
@author AF
@date 2026
"""

import os
import sys
from pathlib import Path
os.environ["WAID_LOG_PREFIX"] = "ops_validation"
from config.boot import (
    WaidBoot,
    WError,
    WaidExit,
)
import ast
import subprocess
import argparse
import shlex
import shutil
from loguru import logger

# ---------------------------------------------------------------------------
# Individual Step Definitions
# ---------------------------------------------------------------------------

def setup_global_env(env: WaidBoot) -> None:
    """Step: env-global - Install global system packages using apt with privilege verification.

    @param env: The boot configuration and runtime environment context.
    @return: None
    """
    logger.info("=== 🔶 [Step: env-global] Starting global system environment setup ===")

    # Check if apt is available (Debian/Ubuntu-based systems)
    if not shutil.which("apt"):
        logger.warning("System command 'apt' not found. Skipping global environment setup.")
        return

    logger.warning(
        "[SECURITY NOTICE] This step requires administrative (sudo) privileges "
        "to install global system packages (e.g., sqlite3) via apt."
    )

    # Verify if running as root or if sudo is available
    is_root = os.geteuid() == 0
    sudo_available = shutil.which("sudo") is not None

    if not is_root and not sudo_available:
        logger.error("Administrative privileges are required, but neither root access nor 'sudo' is available.")
        sys.exit(1)

    packages_to_install = [
        "sqlite3",
    ]
    cmd = []

    if is_root:
        cmd = ["apt", "update"]
    else:
        cmd = ["sudo", "apt", "update"]

    logger.info(f"Executing command: {shlex.join(cmd)}")
    update_result = subprocess.run(cmd, capture_output=False, text=True)
    if update_result.returncode != 0:
        logger.error("Failed to update apt repositories!")
        sys.exit(1)

    if is_root:
        cmd = ["apt", "install", "-y"] + packages_to_install
    else:
        cmd = ["sudo", "apt", "install", "-y"] + packages_to_install

    logger.info(f"Executing command: {shlex.join(cmd)}")
    install_result = subprocess.run(cmd, capture_output=False, text=True)
    if install_result.returncode != 0:
        logger.error("Failed to install global system packages via apt!")
        sys.exit(1)

    logger.info("Global system environment configured successfully.")


def setup_main_venv(env : WaidBoot) -> None:
    """Step: venv - Scan imports, generate requirements.in, compile, and sync .venv.

    @param env: The boot configuration and runtime environment context.
    @return: None
    """
    logger.info("=== 🔶 [Step: venv] Starting .venv dependency analysis and synchronization ===")
    
    venv_dir = env.waid_source_dir / ".venv"
    if not venv_dir.is_dir():
        logger.warning(".venv directory not found. Skipping .venv synchronization.")
        return

    os.chdir(env.waid_source_dir)
    stdlib = sys.stdlib_module_names
    packages = set()

    def parse_file(filepath: str) -> None:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=filepath)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        packages.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        packages.add(node.module.split(".")[0])
        except Exception:
            pass

    for item in os.listdir("."):
        if item.endswith(".py") and os.path.isfile(item):
            parse_file(item)

    recursive_paths = [
        "src", 
        "config",
    ]
    for path in recursive_paths:
        p_full = env.waid_source_dir / path
        if not p_full.exists():
            continue
        for root, dirs, files in os.walk(p_full):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            for file in files:
                if file.endswith(".py"):
                    parse_file(os.path.join(root, file))

    package_mapping = {
        "sklearn": "scikit-learn",
        "yaml": "PyYAML",
        "websocket": "websocket-client",
    }

    local_ignores = {
        "src",
        "config",
        "mock",
        "waid", 
        "waid_shared", 
        "bootstrap", 
        "boot",
        "waid_validate_env",
    }
    
    external = {
        package_mapping.get(p, p) 
        for p in packages 
        if p not in stdlib and p not in local_ignores and not p.startswith("_")
    }

    # Tools or libraries not available directly from source (i.e., not detectable via static AST import scanning)
    manual_dependencies = {
        "pytest",
        "pip-tools",
        "xarray",
        "netcdf4",
        "h5netcdf",
        "psycopg2-binary",
        "prefect==3.8.8",
        "fastapi>=0.139.0,<0.155.0",
        "griffe<1.0.0",
    }
    external.update(manual_dependencies)

    req_in_path = env.waid_source_dir / "requirements.in"
    with open(req_in_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(external)) + "\n")
    logger.info("requirements.in generated successfully.")

    venv_python = str(venv_dir / "bin" / "python")
    
    cmd_compile = [venv_python, "-m", "piptools", "compile", "--upgrade", "requirements.in"]
    if env.debug_mode: cmd_compile.insert(4, "--verbose")
    
    logger.info(f"Executing command: {shlex.join(cmd_compile)}")
    compile_result = subprocess.run(cmd_compile, capture_output=False, text=True)
    if compile_result.returncode != 0:
        logger.error("pip-compile failed for .venv!")
        sys.exit(1)

    cmd_sync = [venv_python, "-m", "piptools", "sync", "requirements.txt"]
    if env.debug_mode: cmd_sync.insert(4, "--verbose")
    
    logger.info(f"Executing command: {shlex.join(cmd_sync)}")
    sync_result = subprocess.run(cmd_sync, capture_output=False, text=True)
    if sync_result.returncode != 0:
        logger.error("pip-sync failed for .venv!")
        sys.exit(1)
        
    logger.info(".venv synchronized successfully.")


def setup_dbt_venv(env: WaidBoot) -> None:
    """Step: venv-dbt - Synchronize .venv-dbt environment using pip-sync with embedded dependencies.

    @param env: The boot configuration and runtime environment context.
    @return: None
    """
    logger.info("=== 🔶 [Step: venv-dbt] Starting .venv-dbt environment synchronization ===")

    venv_dbt_dir = env.waid_source_dir / ".venv-dbt"

    if not venv_dbt_dir.is_dir():
        logger.info(".venv-dbt directory not found. Creating virtual environment.")
        try:
            venv_dbt_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dbt_dir)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create .venv-dbt environment: {e.stderr}")
            sys.exit(1)

    venv_dbt_python = str(venv_dbt_dir / "bin" / "python")

    # Ensure pip-tools is installed inside .venv-dbt to support compile/sync
    try:
        subprocess.run(
            [venv_dbt_python, "-m", "pip", "install", "--upgrade", "pip", "pip-tools"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install pip-tools in .venv-dbt: {e.stderr}")
        sys.exit(1)

    # Define the default requirements list internally and write requirements-dbt.in
    dbt_dependencies = [
        "dbt-core<1.11",
        "dbt-sqlite",
        "dbt-adapters",
        "prefect-dbt",
        "prefect-shell",
        "sqlparse",
        "agate",
    ]

    req_dbt_in = env.waid_source_dir / "requirements-dbt.in"
    req_dbt_txt = env.waid_source_dir / "requirements-dbt.txt"

    try:
        req_dbt_in.write_text("\n".join(dbt_dependencies) + "\n", encoding="utf-8")
        logger.info(f"Successfully generated {req_dbt_in.name} with default dependencies.")
    except Exception as e:
        logger.error(f"Failed to write {req_dbt_in.name}: {e}")
        sys.exit(1)

    # Compile requirements-dbt.in to requirements-dbt.txt
    cmd_compile = [
        venv_dbt_python,
        "-m",
        "piptools",
        "compile",
        "--upgrade",
        str(req_dbt_in),
        "-o",
        str(req_dbt_txt),
    ]
    if env.debug_mode:
        cmd_compile.insert(4, "--verbose")

    logger.info(f"Executing command: {shlex.join(cmd_compile)}")
    compile_result = subprocess.run(cmd_compile, capture_output=False, text=True)
    if compile_result.returncode != 0:
        logger.error("pip-compile failed for .venv-dbt!")
        sys.exit(1)

    # Synchronize environment using pip-sync
    cmd_sync = [venv_dbt_python, "-m", "piptools", "sync", str(req_dbt_txt)]
    if env.debug_mode:
        cmd_sync.insert(4, "--verbose")

    logger.info(f"Executing command: {shlex.join(cmd_sync)}")
    sync_result = subprocess.run(cmd_sync, capture_output=False, text=True)
    if sync_result.returncode != 0:
        logger.error("pip-sync failed for .venv-dbt!")
        sys.exit(1)

    logger.info(".venv-dbt synchronized successfully.")


def setup_prefect(env: WaidBoot) -> None:
    """Validate Prefect in the main application venv."""
    logger.info("=== [Step: prefect] Validating Prefect ===")

    venv_dir = env.waid_source_dir / ".venv"
    venv_python = str(venv_dir / "bin" / "python")

    if not os.path.isfile(venv_python):
        logger.warning(
            "[PREFECT] Main venv not found; skipping Prefect validation."
        )
        return

    checks = [
        (
            "Dependency consistency",
            [
                venv_python, "-m", "pip", "check",
            ],
        ),
        (
            "Prefect server compatibility",
            [
                venv_python, "-c",
                (
                    "import prefect; "
                    "import prefect.server.api.concurrency_limits_v2; "
                    "print('Prefect server import OK')"
                ),
            ],
        ),
    ]

    failed = False

    for label, command in checks:
        logger.info(f"[PREFECT] Running: {label}")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.stdout.strip():
            logger.info(result.stdout.strip())

        if result.returncode != 0:
            failed = True
            logger.error(
                f"[PREFECT] FAILED: {label}\n"
                f"{result.stderr.strip()}"
            )

    if failed:
        raise RuntimeError(
            "Prefect validation failed. "
            "Check the dependency constraints in requirements.in."
        )

    logger.info("[PREFECT] All checks passed.")
    
    
def main() -> None:
    """
    @brief Main execution entry point for environment management.
    @return Process exit code integer.
    """
    try:
        env = WaidBoot()
        setup_global_env(env)
        setup_main_venv(env)
        setup_dbt_venv(env)
        setup_prefect(env)
        logger.info("=== Env Validation Completed Successfully ===")

    except WError as e:
        logger.error(e)
        return e.code

    except Exception:
        logger.exception("Unexpected error while validating environments")
        return env.waid_exit.INTERNAL_ERROR

    return env.waid_exit.SUCCESS


if __name__ == "__main__":
    sys.exit(main())