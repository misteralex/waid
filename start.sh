#!/bin/bash
set -e

##
# @file start.sh
# @brief WAID Local and Docker Launcher Script for Linux/WSL.
# @details Manages local and containerized execution of pipelines, background schedulers, and Streamlit dashboards.
# @author AF
# @date 2026

show_usage() {
    echo "=== WAID Launcher (Linux/WSL) ==="
    echo "Usage: ./start.sh [option]"
    echo ""
    echo "Available options:"
    echo "  (no option)         - Runs the pipeline locally (default)"
    echo "  pipeline            - Runs the pipeline locally"
    echo "  scheduler           - Starts the continuous scheduler locally"
    echo "  dashboard           - Starts the dashboard locally"
    echo "  docker-pipeline     - Runs the pipeline once in Docker"
    echo "  docker-scheduler    - Starts the continuous scheduler in Docker"
    echo "  docker-dashboard    - Starts the dashboard in Docker"
    echo "  --help, -h          - Shows this help menu"
    echo "======================================="
}

COMMAND="${1:-pipeline}"

case "$COMMAND" in
    pipeline|local-pipeline)
        echo "Starting pipeline locally..."
        python waid_orchestrate.py
        ;;
    scheduler)
        echo "Starting continuous scheduler locally..."
        python waid_scheduler.py
        ;;
    dashboard|local-dashboard)
        echo "Starting dashboard locally..."
        streamlit run src/waid_08_2_viz_streamlit.py
        ;;
    docker-pipeline)
        echo "Starting pipeline in Docker (batch)..."
        docker-compose run --rm pipeline
        ;;
    docker-scheduler)
        echo "Starting continuous scheduler in Docker (background)..."
        docker-compose up -d pipeline
        ;;
    docker-dashboard)
        echo "Starting dashboard in Docker (http://localhost:8501)..."
        docker-compose up dashboard
        ;;
    --help|-h|help|menu)
        show_usage
        ;;
    *)
        echo "Unrecognized command: $COMMAND"
        echo ""
        show_usage
        exit 1
        ;;
esac