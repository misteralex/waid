# Use an official Python runtime as a parent image
FROM python:3.12-slim

##
# @file Dockerfile
# @brief WAID Application Container Image Definition.
# @details Installs system and python packages, configures paths, and sets default container entrypoints.
# @author AF
# @date 2026

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/usr/local/bin:${PATH}"

# Install system dependencies (including git/bash if needed for dbt or scripts)
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    git \
    bash curl git wget && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy dependency specifications first to leverage Docker cache
COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of the project source code into the container
COPY . .

# Grant execution permissions to shell scripts
RUN chmod +x /app/entrypoint.sh /app/start.sh /app/src/*.sh 2>/dev/null || true

# Set the default container entrypoint
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]