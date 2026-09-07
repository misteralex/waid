#!/bin/bash
set -e

##
# @file start-lab.sh
# @brief WAID Lab Launcher Script for Linux/WSL.
# @details Manages local and containerized execution of lab pipelines, schedulers, and dashboards.
# @author AF
# @date 2026

COMPOSE_FILES="-f docker/lab/docker-compose.yml -f docker/lab/docker-compose.override.yml"

show_usage() {
    echo "=== WAID Lab Launcher (Linux/WSL) ==="
    echo "Usage: ./start-lab.sh [option]"
    echo ""
    echo "Local execution options:"
    echo "  pipeline            - Runs single pipeline pass locally (waid_orchestrate_lab.py)"
    echo "  scheduler           - Starts continuous scheduler locally (waid_scheduler_lab.py)"
    echo "  dashboard           - Starts Streamlit dashboard locally"
    echo ""
    echo "Docker Lab options:"
    echo "  docker-edge         - Starts Edge runner/orchestrator in Docker (profile: edge)"
    echo "  docker-arm          - Starts ARM runner/orchestrator in Docker (profile: arm)"
    echo "  docker-prefect      - Starts Prefect server & worker stack with pre-clean (profile: prefect)"
    echo "  clean-prefect       - Cleans Prefect database locks and temporary WAL files"
    echo "  down                - Stops and removes all running Docker Lab containers (edge, arm & prefect)"
    echo ""
    echo "Utility options:"
    echo "  --help, -h          - Shows this help menu"
    echo "======================================="
}

COMMAND="${1:-docker-edge}"

clean_prefect_locks() {
    echo "Cleaning Prefect temporary locks and SQLite state..."
    docker compose --profile prefect $COMPOSE_FILES run --rm waid-lab-prefect sh -c "rm -rf /root/.prefect/*.db-wal /root/.prefect/*.db-shm /tmp/prefect/*" || true
}

case "$COMMAND" in
    pipeline|local-pipeline)
        echo "Starting single lab pipeline pass locally..."
        python waid_orchestrate_lab.py
        ;;
    scheduler|local-scheduler)
        echo "Starting continuous scheduler locally..."
        python waid_scheduler_lab.py
        ;;
    dashboard|local-dashboard)
        echo "Starting dashboard locally..."
        streamlit run src/waid_08_1_viz_streamlit_app.py
        ;;
    docker-edge|edge)
        echo "Starting Edge orchestrator in Docker (profile: edge)..."
        docker compose --profile edge $COMPOSE_FILES up -d waid-lab-orchestrator
        docker compose --profile edge $COMPOSE_FILES logs -f waid-lab-orchestrator
        ;;
    docker-prefect|prefect)
        clean_prefect_locks
        echo "Starting Prefect orchestrator stack in Docker (profile: prefect)..."
        docker compose --profile prefect $COMPOSE_FILES up -d waid-lab-prefect
        docker compose --profile prefect $COMPOSE_FILES logs -f waid-lab-prefect
        ;;
    clean-prefect|clean)
        clean_prefect_locks
        ;;
    down|stop|docker-down)
        echo "Stopping and removing all Docker Lab containers (edge, prefect)..."
        docker compose --profile edge --profile arm --profile prefect $COMPOSE_FILES down --remove-orphans
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