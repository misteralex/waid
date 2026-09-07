#!/usr/bin/env bash
set -e

# Resolve script directory and determine project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Ensure WAID_SOURCE is defined
if [ -z "${WAID_SOURCE}" ]; then
    export WAID_SOURCE="${PROJECT_ROOT}"
    echo "WAID_SOURCE not set. Defaulting to: ${WAID_SOURCE}"
fi

# Load environment configuration if available
if [ -f "${WAID_SOURCE}/config/waid.env" ]; then
    set -a
    source "${WAID_SOURCE}/config/waid.env"
    set +a
fi

cd "${WAID_SOURCE}"

COMPOSE_FILE="docker/arm/docker-compose.yml"

# Se viene passato "down" come primo argomento, esegui il tear down
if [ "$1" = "down" ]; then
    shift
    echo "Stopping WAID container on ARM using WAID_SOURCE=${WAID_SOURCE}..."
    docker compose -f "${COMPOSE_FILE}" down "$@"
else
    echo "Starting WAID container on ARM using WAID_SOURCE=${WAID_SOURCE}..."
    # Se nessun argomento è passato, di default fa "up -d"
    if [ $# -eq 0 ]; then
        docker compose -f "${COMPOSE_FILE}" up -d
    else
        docker compose -f "${COMPOSE_FILE}" up "$@"
    fi
fi