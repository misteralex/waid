#!/bin/bash
set -e

##
# @file start.sh
# @brief WAID Production Launcher Script for Linux/WSL.
# @details Manages production execution of pipelines via Prefect and Docker.
# @author AF
# @date 2026

show_usage() {
    echo "=== WAID Production Launcher ==="
    echo "Usage: ./start.sh [option]"
    echo ""
    echo "Available options:"
    echo "  (no option)         - Runs production pipeline with Prefect (default)"
    echo "  up                  - Starts production container in background"
    echo "  down                - Stops production container"
    echo "  logs                - Shows production logs"
    echo "  --help, -h          - Shows this help menu"
    echo "====================================="
}

# Load environment variables from boot.env if available
if [ -f "config/boot.env" ]; then
    set -a
    source config/boot.env
    set +a
fi

COMMAND="${1:-up}"

case "$COMMAND" in
    up|run)
        echo "Starting WAID Production (Prefect) in Docker..."
        docker compose -f docker/prod/docker-compose.yml up
        ;;
    down)
        echo "Stopping WAID Production..."
        docker compose -f docker/prod/docker-compose.yml down
        ;;
    logs)
        echo "Showing production logs..."
        docker compose -f docker/prod/docker-compose.yml logs -f
        ;;
    --help|-h|help|menu)
        show_usage
        ;;
    *)
        echo "Unrecognized command: $COMMAND"
        show_usage
        exit 1
        ;;
esac