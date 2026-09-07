@echo off
setlocal enabledelayedexpansion

##
# @file start.bat
# @brief WAID Local and Docker Launcher Script for Windows.
# @details Manages local and containerized execution of pipelines, background schedulers, and Streamlit dashboards.
# @author AF
# @date 2026

set COMMAND=%1

if "%COMMAND%"=="" set COMMAND=pipeline

if /I "%COMMAND%"=="pipeline" (
    echo Starting pipeline locally...
    python waid_orchestrate_lab.py
    goto end
)
if /I "%COMMAND%"=="local-pipeline" (
    echo Starting pipeline locally...
    python waid_orchestrate_lab.py
    goto end
)
if /I "%COMMAND%"=="scheduler" (
    echo Starting continuous scheduler locally...
    python waid_scheduler_lab.py
    goto end
)
if /I "%COMMAND%"=="dashboard" (
    echo Starting dashboard locally...
    streamlit run src/waid_08_1_viz_streamlit_app.py
    goto end
)
if /I "%COMMAND%"=="local-dashboard" (
    echo Starting dashboard locally...
    streamlit run src/waid_08_1_viz_streamlit_app.py
    goto end
)
if /I "%COMMAND%"=="docker-pipeline" (
    echo Starting pipeline in Docker (batch)...
    docker-compose run --rm pipeline
    goto end
)
if /I "%COMMAND%"=="docker-scheduler" (
    echo Starting continuous scheduler in Docker (background)...
    docker-compose up -d pipeline
    goto end
)
if /I "%COMMAND%"=="docker-dashboard" (
    echo Starting dashboard in Docker (http://localhost:8501)...
    docker-compose up dashboard
    goto end
)

:help
echo =======================================
echo     WAID Launcher (Windows)
echo =======================================
echo Usage: start.bat [option]
echo.
echo Available options:
echo   (no option)         - Runs the pipeline locally (default)
echo   pipeline            - Runs the pipeline locally
echo   scheduler           - Starts the continuous scheduler locally
echo   dashboard           - Starts the dashboard locally
echo   docker-pipeline     - Runs the pipeline once in Docker
echo   docker-scheduler    - Starts the continuous scheduler in Docker
echo   docker-dashboard    - Starts the dashboard in Docker
echo   --help / help       - Shows this menu
echo =======================================
pause

:end