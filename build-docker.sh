#!/bin/bash
set -e

##
# @file build-docker.sh
# @brief WAID Docker environment build and initialization script for Linux/WSL.
# @details Ensures required local data, logs, and dbt directories exist before building Docker containers.
# @author AF
# @date 2026

echo "Building and starting WAID Docker environment (Linux/WSL)..."

# Ensure target volume directories exist locally
mkdir -p data logs dbt/target dbt/logs

# Build and run the container
docker-compose build