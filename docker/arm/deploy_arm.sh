#!/bin/bash

##
# @file deploy_arm.sh
# @brief Deployment script for WAID pipeline on ARM architecture.
# @details Handles the entire deployment process for ARM-based targets.
# @author AF
# @date 2026

set -e

# === Load environment configuration ===
set -a
[ -f "${WAID_SOURCE}/config/boot.env" ] && source "${WAID_SOURCE}/config/boot.env"
[ -f "${WAID_SOURCE}/config/waid.env" ] && source "${WAID_SOURCE}/config/waid.env"
set +a

if [ -z "${WAID_SOURCE}" ]; then
    echo "CRITICAL ERROR: WAID_SOURCE environment variable is not set!"
    exit 1
fi
 
# Fallback or validation of ARM target variables
ARM_USER="${WAID_BOARD_ARM_USER:-waid}"
ARM_IP="${WAID_BOARD_ARM_IP:?CRITICAL ERROR: WAID_BOARD_ARM_IP is not set in config/waid.env!}"
BOARD_ARM_DIR="${WAID_BOARD_ARM_DIR:?CRITICAL ERROR: WAID_BOARD_ARM_DIR is not set in config/waid.env!}"
BOARD_ARM_IMAGE=$DOCKER_DEPLOY_BOARD_ARM_DIR/$DOCKER_BOARD_ARM_IMAGE_FILE
BOARD_ARM_BUNDLE=$DOCKER_DEPLOY_BOARD_ARM_DIR/$DOCKER_BOARD_ARM_BUNDLE_FILE
echo "Deployment target: ${ARM_USER}@${ARM_IP}:${BOARD_ARM_DIR}"

# Sanity check for current docker deployment if already exist
mkdir -p ${DOCKER_DEPLOY_BOARD_ARM_DIR}
echo "Deployment source: ${DOCKER_DEPLOY_BOARD_ARM_DIR}"
echo "Checking existing packages..."

if gzip -t "$BOARD_ARM_IMAGE" "$BOARD_ARM_BUNDLE" 2>/dev/null; then
    echo "All checks passed successfully. Proceeding with deployment..."
    CHECK_PKGS=1
else
    echo "Missing packages. Process new ARM docker build"
    CHECK_PKGS=0
fi

if (( CHECK_PKGS == 0 )); then
    echo "=== Checking active DB locks and performing SQLite VACUUM ==="

    # Check if the main database (WAID_DB_FILE) is locked by any active process
    if fuser $WAID_DB_FILE >/dev/null 2>&1; then
        echo "CRITICAL ERROR: <$WAID_DB_FILE> is currently locked by active processes!"
        echo "The following processes are using the database:"
        fuser -v $WAID_DB_FILE
        echo "Deployment aborted. Please stop active processes and retry."
        exit 1
    else
        echo "No active locks detected on <$WAID_DB_FILE>. Proceeding with VACUUM..."
    fi

    sqlite3 $WAID_DB_FILE "VACUUM;"
    sqlite3 $WAID_DB_FILE "PRAGMA integrity_check;"

    echo "=== Building Docker ARM64 image ==="

    # Check if Docker daemon / socket is accessible (works with Docker Desktop WSL integration)
    if ! docker info >/dev/null 2>&1; then
        echo "CRITICAL ERROR: Docker daemon is not accessible."
        echo "Please ensure Docker Desktop is running on Windows and WSL integration is enabled for this distro."
        exit 1
    fi
    echo "Docker daemon is running and accessible."

    # Resource guard for WSL emulation: restrict parallel threads to protect host stability
    TOTAL_CORES=$(nproc)
    BUILD_CORES=$(( TOTAL_CORES > 2 ? TOTAL_CORES - 1 : 1 ))
    echo "Host resource check: ${TOTAL_CORES} core(s) detected."
    echo "Restricting ARM emulation build to ${BUILD_CORES} parallel thread(s) to prevent WSL CPU saturation."

    # Export DOCKER_BUILDKIT settings and pass parallel limits if applicable
    export DOCKER_BUILDKIT=1

    # Run build leveraging the calculated core throttling
    ./docker/build_docker.sh arm

    echo "Exporting Docker image..."
    docker save waid_arm:latest | gzip > $BOARD_ARM_IMAGE

    echo "Packaging source and explicit configuration artifacts"
    touch data/waid_deploy.db 2>/dev/null || true

    # Sanitize line endings for shell scripts and env files
    find config/ docker/ -type f \( -name "*.sh" -o -name "*.env" \) -exec sed -i 's/\r$//' {} +

    echo "=== Preparing configuration for ARM production release ==="
    sed -i 's/^WAID_DEPLOY_MODE=.*/WAID_DEPLOY_MODE=cloud/' config/waid.env
    sed -i 's/^#WAID_DEPLOY_MODE=cloud/WAID_DEPLOY_MODE=cloud/' config/waid.env
    
    sed -i 's/^WAID_DB_SCHEMA_TARGET=.*/WAID_DB_SCHEMA_TARGET=prod/' config/waid.env
    sed -i 's/^#WAID_DB_SCHEMA_TARGET=prod/WAID_DB_SCHEMA_TARGET=prod/' config/waid.env

    # Package explicit artifacts (including entire docker/arm folder)
    tar -czf ${BOARD_ARM_BUNDLE} \
        config/boot.env \
        config/waid.env \
        config/boot.py \
        config/profiles.yml \
        src/ \
        dbt/ \
        docker/arm/ \
        data/waid.db \
        data/waid_deploy.db \
        data/models/ \
        data/ecowitt/ \
        data/era5/ \
        data/matches/ \
        data/tensors/ \
        waid_scheduler_lab.py \
        waid_orchestrate_lab.py
fi

# Make remote release entry
TODAY=$(date +%Y%m%d)
REMOTE_RELEASE_DIR="${HOME}/waid_release_${TODAY}"
echo "Copying files to ARM-based target device via SCP"
ssh ${ARM_USER}@${ARM_IP} "mkdir -p ${REMOTE_RELEASE_DIR}"
scp $BOARD_ARM_IMAGE $BOARD_ARM_BUNDLE \
    $DOCKER_BOARD_ARM_DIR/$DOCKER_BOARD_ARM_UPDATE_FILE ${ARM_USER}@${ARM_IP}:${REMOTE_RELEASE_DIR}/

# Running remote deployment sequence
echo "Running remote deployment sequence"
ssh -tt ${ARM_USER}@${ARM_IP} "bash ${REMOTE_RELEASE_DIR}/${DOCKER_BOARD_ARM_UPDATE_FILE} \
    '${BOARD_ARM_DIR}' '${DOCKER_BOARD_ARM_BUNDLE_FILE}' '${DOCKER_BOARD_ARM_IMAGE_FILE}' '${REMOTE_RELEASE_DIR}'"

echo "ARM Board Deployment Completed Successfully"