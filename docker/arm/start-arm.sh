#!/bin/bash
/**
 * @file start-arm.sh
 * @brief Bootstrapping and volume permission initialization script for WAID pipeline on ARM architecture.
 * @details Resolves runtime UID/GID variables, verifies host directory structure for Docker bind mounts, 
 *          launches Docker Compose services, and aligns dbt workspace execution permissions.
 * @author AF
 * @date 2026
 */
set -e

export WAID_UID=$(id -u)
export WAID_GID=$(id -g)

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

VOLUMES_DIRS=(
  "data"
  "logs"
  "config"
  "deploy"
  "dbt/target"
  "dbt/logs"
)

echo "[WAID-BOOT] Checking host volume permissions..."
for dir in "${VOLUMES_DIRS[@]}"; do
  if [ ! -d "$dir" ]; then
    mkdir -p "$dir"
  fi
done

# Launching container services
docker compose -f docker/arm/docker-compose.yml up -d

# Idempotent permission fix inside container context
echo "[WAID-BOOT] Aligning container dbt directory permissions..."
docker compose -f docker/arm/docker-compose.yml exec -u root waid-arm bash -c "chown -R ${WAID_UID}:${WAID_GID} /app/dbt && chmod -R 775 /app/dbt"

echo "[WAID-BOOT] Environment ready."