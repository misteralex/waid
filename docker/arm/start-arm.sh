#!/bin/bash

##
# @file start-arm.sh
# @brief Bootstrapping and volume permission initialization script for WAID pipeline on ARM architecture.
# @details Resolves runtime UID/GID variables, verifies host directory structure for Docker bind mounts, 
#          launches Docker Compose services, and aligns dbt workspace execution permissions.
# @author AF
# @date 2026

set -e

# Export host user UID and GID for container user matching
export WAID_UID=$(id -u)
export WAID_GID=$(id -g)

# Resolve project root directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

# Define required host volumes directories
VOLUMES_DIRS=(
  "data"
  "logs"
  "config"
  "src"
  "deploy"
)

# Ensure host directories exist and verify write permissions silently
for dir in "${VOLUMES_DIRS[@]}"; do
  mkdir -p "$dir"
  if [ ! -w "$dir" ]; then
    echo "ERROR: Directory '$dir' is not writable by current user ($(whoami))." >&2
    exit 1
  fi
done

# Handle script arguments (e.g., ./start-arm.sh down)
ACTION="${1:-up}"

if [ "$ACTION" = "down" ]; then
  docker compose -f docker/arm/docker-compose.yml down
else
  # 1. Stop containers and purge old volumes
  docker compose -f docker/arm/docker-compose.yml down -v

  # 2. Force remove runtime/output folders from host filesystem
  sudo rm -rf dbt/logs dbt/target dbt/dbt_packages

  docker compose -f docker/arm/docker-compose.yml up -d
fi