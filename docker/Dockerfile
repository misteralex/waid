# ==============================================================================
# Stage 1: Builder (Compilation and venv setup)
# ==============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Primary virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Isolated dbt virtual environment
COPY requirements-dbt.txt .
RUN python -m venv /opt/venv-dbt && \
    /opt/venv-dbt/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv-dbt/bin/pip install --no-cache-dir --prefer-binary -r requirements-dbt.txt

# Remove Python bytecode to save space
RUN find /opt/venv /opt/venv-dbt -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# ==============================================================================
# Stage 2: Base Runtime (Reusable base image)
# ==============================================================================
FROM python:3.12-slim AS base

WORKDIR /app

# System runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Pre-create volume mountpoints with open permissions
RUN mkdir -p /app/data /app/logs /app/dbt/target /app/dbt/logs /app/docker /app/config

# Copy pre-compiled virtual environments
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/venv-dbt /opt/venv-dbt

# Permanent symlink creation
RUN ln -sf /opt/venv-dbt /app/.venv-dbt

ENV PATH="/opt/venv/bin:$PATH"

# ==============================================================================
# Stage 3: Production (Derived from base)
# ==============================================================================
FROM base AS prod

COPY . /app

CMD ["python", "waid_prefect_manager.py"]

# ==============================================================================
# Stage 4: Laboratory (Derived from base for experiments)
# ==============================================================================
FROM base AS lab

COPY . /app

CMD ["python", "waid_orchestrate_lab.py"]
