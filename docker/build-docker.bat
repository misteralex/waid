@echo off

##
# @file build-docker.bat
# @brief WAID Docker environment build and initialization script for Windows.
# @details Ensures required local data, logs, and dbt directories exist before building Docker containers.
# @author AF
# @date 2026

echo Building and starting WAID Docker environment (Windows)...

if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "dbt\target" mkdir dbt\target
if not exist "dbt\logs" mkdir dbt\logs

docker-compose build
pause