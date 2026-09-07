#!/bin/bash
set -e

##
# @file build-docker.sh
# @brief WAID Docker environment build and initialization script for Linux/WSL.
# @details Ensures required local data, logs, and dbt directories exist before building Docker containers.
# @author AF
# @date 2026

# 1. Automatically switch to repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# Load environment variables from boot.env if available
if [ -f "config/boot.env" ]; then
    set -a
    source config/boot.env
    set +a
fi

# 2. Environment selection (default: prod)
ENV="${1:-prod}"
COMPOSE_FILE="docker/${ENV}/docker-compose.yml"
OVERRIDE_FILE="docker/${ENV}/docker-compose.override.yml"

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "Error: File $COMPOSE_FILE not found!"
    echo "Usage: ./docker/build-docker.sh [prod|lab|arm]"
    exit 1
fi

# Set target platform for cross-compilation when targeting arm
if [ "$ENV" = "arm" ]; then
    export DOCKER_DEFAULT_PLATFORM=linux/arm64
    echo "Target architecture set to: linux/arm64"
fi

# Build compose file arguments
COMPOSE_ARGS=("-f" "$COMPOSE_FILE")
if [ -f "$OVERRIDE_FILE" ]; then
    COMPOSE_ARGS+=("-f" "$OVERRIDE_FILE")
    echo "Detected override file: $OVERRIDE_FILE"
fi

echo "Building WAID Docker environment ($ENV) (Linux/WSL)..."

# Ensure target volume directories exist locally at repository root
mkdir -p data logs dbt/target dbt/logs

# Extended timeouts for BuildKit
export DOCKER_CLIENT_TIMEOUT=7200
export COMPOSE_HTTP_TIMEOUT=7200
export BUILDKIT_STEP_TIMEOUT=7200

# Build container leveraging local cache
docker compose "${COMPOSE_ARGS[@]}" build