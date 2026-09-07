#!/bin/bash
set -e

##
# @file entrypoint.sh
# @brief WAID Container Entrypoint Initialization Script.
# @details Exports environment paths, loads configuration files securely, and dispatches execution commands.
# @author AF
# @date 2026

echo "=== WAID Container Starting ==="

# Force container working directory
export WAID_SOURCE="/app"
export PYTHONPATH="/app:/app/config:/app/src:${PYTHONPATH}"

# Securely load environment variables without breaking lines containing spaces
set -a
[ -f "${WAID_SOURCE}/config/boot.env" ] && source "${WAID_SOURCE}/config/boot.env"
[ -f "${WAID_SOURCE}/config/waid.env" ] && source "${WAID_SOURCE}/config/waid.env"
set +a

# Ensure executable permissions for scripts when mounted from host
chmod +x /app/*.sh /app/docker/*.sh 2>/dev/null || true

# Populate masked /app/.venv-dbt volume with links to internal /opt/venv-dbt
mkdir -p /app/.venv-dbt
ln -snf /opt/venv-dbt/bin /app/.venv-dbt/bin 2>/dev/null || true
ln -snf /opt/venv-dbt/lib /app/.venv-dbt/lib 2>/dev/null || true

if [ -f /opt/venv-dbt/pyvenv.cfg ] && [ ! -f /app/.venv-dbt/pyvenv.cfg ]; then
    ln -snf /opt/venv-dbt/pyvenv.cfg /app/.venv-dbt/pyvenv.cfg 2>/dev/null || true
fi

# Always evaluate current period first
CURRENT_PERIOD=$(date +%Y-%m)

# Check if period parameter is present in arguments
has_period=0
for arg in "$@"; do
    if [ "$arg" = "--period" ]; then
        has_period=1
        break
    fi
done

# Fallback injection if running any python orchestrator without --period
if [ "$1" = "python" ] && [ "$has_period" -eq 0 ]; then
    set -- "$@" --period "$CURRENT_PERIOD"
    echo "WARNING: Missing --period flag. Automatically set to current period: $CURRENT_PERIOD"
fi

echo "Current period set to: $CURRENT_PERIOD"

# Dispatch execution to CMD or provided arguments
exec "$@"
