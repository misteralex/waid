#!/bin/bash
set -e

##
# @file entrypoint.sh
# @brief WAID Container Entrypoint Initialization Script.
# @details Exports environment paths, loads configuration files securely, and dispatches execution commands.
# @author AF
# @date 2026

echo "=== WAID Container Starting ==="

# Export PYTHONPATH to allow correct import of internal modules (e.g., 'boot')
export PYTHONPATH="/app:${PYTHONPATH}"

# Securely load environment variables without breaking lines containing spaces
set -a
[ -f "config/boot.env" ] && source config/boot.env
[ -f "config/waid.env" ] && source config/waid.env
set +a

# If arguments are passed from docker-compose (e.g., python waid_scheduler.py), execute them.
# Otherwise, execute default orchestration.
if [ "$#" -gt 0 ]; then
    exec "$@"
else
    exec python waid_orchestrate.py
fi