#!/bin/bash
##
# @file deploy_arm_update.sh
# @brief Script eseguito sul nodo ARM (weatherhub) per avviare la release.
# @details Gestisce backup, estrazione, caricamento immagine Docker e startup dei container.
# @author AF
# @date 2026

set -e

# Parameters passed by the local orchestrator
DEPLOY_DIR="${1:?CRITICAL ERROR: Missing DEPLOY_DIR parameter!}"
BUNDLE_FILE="${2:?CRITICAL ERROR: Missing BUNDLE_FILE parameter!}"
IMAGE_FILE="${3:?CRITICAL ERROR: Missing IMAGE_FILE parameter!}"
RELEASE_DIR="${4:?CRITICAL ERROR: Missing RELEASE_DIR parameter!}"

export WAID_SOURCE="$DEPLOY_DIR"

echo ">>> [1/6] Navigating the home directory ($HOME)..."
cd "$HOME" || exit 1

TODAY=$(date +%Y%m%d)
BACKUP_NAME="${HOME}/waid-backup-${TODAY}"

if [ -L "$DEPLOY_DIR" ]; then
    echo ">>> [2/6] Remove current release symlink..."
    rm "$DEPLOY_DIR"
elif [ -d "$DEPLOY_DIR" ]; then
    echo ">>> [2/6] Back up current release to $BACKUP_NAME..."
    [ -e "$BACKUP_NAME" ] && rm -rf "$BACKUP_NAME"
    mv "$DEPLOY_DIR" "$BACKUP_NAME"
else
    echo ">>> [2/6] The deploy directory '$DEPLOY_DIR' does not yet exist."
fi

echo ">>> [3/6] Creation of deployment directory..."
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR" || exit 1

# Extracting files by pulling them directly from the dated release folder
if [ -f "$RELEASE_DIR/$BUNDLE_FILE" ]; then
    echo ">>> [4/6] Extracting source archive from ${RELEASE_DIR}..."
    tar -xzf "$RELEASE_DIR/$BUNDLE_FILE"
    mkdir -p dbt/logs dbt/target logs data
fi

if [ -f "$RELEASE_DIR/$IMAGE_FILE" ]; then
    echo ">>> [5/6] Loading ARM Docker image from ${RELEASE_DIR}..."
    docker load -i "$RELEASE_DIR/$IMAGE_FILE"
else
    echo ">>> [5/6] Warning: No new image archives found in ${RELEASE_DIR}. Using the existing image."
fi

echo ">>> [6/6] Starting services via Docker Compose..."
chmod +x docker/arm/start_arm.sh

docker compose -f docker/arm/docker-compose.yml down
./docker/arm/start_arm.sh

echo "=== Remote Deployment Completed Successfully ==="
echo "=== Historical release preserved in: ${RELEASE_DIR} ==="
docker ps --filter "name=waid"