#!/usr/bin/env bash
set -e

# Verify WAID_SOURCE consistency against actual script location (2 levels up)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [ -z "${WAID_SOURCE}" ]; then
    echo "CRITICAL ERROR: WAID_SOURCE environment variable is not set!"
    exit 1
fi

ACTUAL_ROOT="$(cd "${WAID_SOURCE}" && pwd)"

if [ "${EXPECTED_ROOT}" != "${ACTUAL_ROOT}" ]; then
    echo "CRITICAL ERROR: WAID_SOURCE mismatch!"
    echo "  Expected: ${EXPECTED_ROOT}"
    echo "  Actual:   ${ACTUAL_ROOT}"
    exit 1
fi

cd "${WAID_SOURCE}"
echo "Working directory validated and set to: $(pwd)"

# === Load environment configuration ===
set -a
[ -f "${WAID_SOURCE}/config/waid.env" ] && source "${WAID_SOURCE}/config/waid.env"
set +a

# Fallback o validazione delle variabili di target ARM
ARM_USER="${WAID_ARM_USER:-waid}"
RASP_IP="${WAID_ARM_IP:?CRITICAL ERROR: WAID_ARM_IP is not set in config/waid.env!}"
RASP_DIR="${WAID_ARM_DIR:-/home/${ARM_USER}/waid}"
echo "Deployment target: ${ARM_USER}@${RASP_IP}:${RASP_DIR}"

echo "=== 1. Checking active DB locks and performing SQLite VACUUM ==="

# Check if waid.db is locked by any active process
if fuser data/waid.db >/dev/null 2>&1; then
    echo "CRITICAL ERROR: waid.db is currently locked by active processes!"
    echo "The following processes are using the database:"
    fuser -v data/waid.db
    echo "Deployment aborted. Please stop active processes and retry."
    exit 1
else
    echo "No active locks detected on data/waid.db. Proceeding with VACUUM..."
fi

sqlite3 data/waid.db "VACUUM;"
sqlite3 data/waid.db "PRAGMA integrity_check;"

echo "=== 2. Building Docker ARM64 image ==="
./docker/build-docker.sh arm

echo "=== 2.1 Exporting Docker image ==="
docker save waid_arm:latest | gzip > waid_pipeline_arm.tar.gz

echo "=== 3. Packaging source and explicit configuration artifacts ==="
touch data/waid_deploy.db 2>/dev/null || true

# Sanitize line endings for shell scripts and env files
find config/ docker/ -type f \( -name "*.sh" -o -name "*.env" \) -exec sed -i 's/\r$//' {} +

# Package explicit artifacts (including entire docker/arm folder)
tar -czf waid_bundle.tar.gz \
    config/boot.env \
    config/waid.env \
    config/boot.py \
    config/profiles.yml \
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

echo "=== 4. Syncing files to ARM-based target device via SCP ==="
ssh ${ARM_USER}@${RASP_IP} "mkdir -p ${RASP_DIR}"
scp waid_pipeline_arm.tar.gz waid_bundle.tar.gz ${ARM_USER}@${RASP_IP}:${RASP_DIR}/

# Cleanup local temporary transfer files
rm -f waid_pipeline_arm.tar.gz waid_bundle.tar.gz

echo "=== 5. Running remote deployment sequence ==="
ssh -tt ${ARM_USER}@${RASP_IP} << EOF
    cd ${RASP_DIR}
    
    # Extract bundle and prepare persistence directories
    tar -xzf waid_bundle.tar.gz
    mkdir -p dbt/logs dbt/target logs data
    rm -f waid_bundle.tar.gz
    
    # Load image and deploy using start-arm.sh wrapper
    docker load < waid_pipeline_arm.tar.gz
    rm -f waid_pipeline_arm.tar.gz
    
    chmod +x docker/arm/start-arm.sh
    docker compose -f docker/arm/docker-compose.yml down
    ./docker/arm/start-arm.sh
    
    # Display initial startup logs
    docker logs --tail=30 waid_arm
    exit
EOF

echo "=== ARM Deployment Completed Successfully ==="