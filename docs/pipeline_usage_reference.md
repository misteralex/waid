# WAID (Weather AI Direct Nowcasting) - Pipeline Usage

* [Operational Execution Modes](#operational-execution-modes)
* [Lab Execution CLI (`waid_orchestrate_lab.py`)](#lab-execution-cli)
* [Scheduler & Simulation Engine (`waid_scheduler_lab.py`)](#scheduler--simulation-engine)
* [Prefect Workflow Management (`waid_prefect_manager.py`)](#prefect-workflow-management)
* [Environment Reset Regimes (`WAID_SETUP_MODE`)](#environment-reset-regimes)
* [dbt Transformation Commands](#dbt-transformation-commands)
* [Docker & ARM Edge Deployments](#docker--arm-edge-deployments)
* [Configuration & Fallback Reference](#configuration--fallback-reference)

---

## Operational Execution Modes <a id="operational-execution-modes"></a>

The WAID platform supports two core execution paradigms tailored for different operational contexts:

1. **Lab & Edge Mode (Lightweight CLI / Subprocess Execution):**
   Direct, sequential execution via Python CLI scripts. Optimized for local debugging, rapid prototyping, and resource-constrained edge hardware (e.g., Raspberry Pi 4 / ARM64).
   * Orchestrator: `waid_orchestrate_lab.py`
   * Scheduler Daemon: `waid_scheduler_lab.py`

2. **Orchestrated Mode (Prefect Managed):**
   Managed via Prefect flows and tasks, providing DAG dependency tracking, automatic retries, concurrency controls, and web UI monitoring.
   * Manager: `waid_prefect_manager.py`
   * Flow Orchestrator: `waid_orchestrate.py`

---

## Lab Execution CLI (`waid_orchestrate_lab.py`) <a id="lab-execution-cli"></a>

The central CLI runner executing end-to-end processing passes (dbt setup, ingestion, matching, tensor creation, ML training, inference, deployment export).

### Usage & CLI Options

```bash
python src/waid_orchestrate_lab.py [OPTIONS]
```

| Flag | Description | Default |
| :--- | :--- | :--- |
| `--run-mode` | Operational mode: `incremental` or `backfill`. | `incremental` |
| `--skip-ingestion` | Skips raw telemetry fetching and reanalysis downloads. | `False` |
| `--skip-ingestion-ml-deploy` | Skip ingestion, ML training, and deploy/viz steps (executes inference & quality sequence only) | `False` |
| `--start-from` | Fast-forwards execution directly to a specific step script name. | `None` |
| `--period` | Target period in `YYYY-MM` format. | Active month |
| `--begin-period` / `--end-period` | Start and end month range for backfill runs. | `None` |
| `--retro-now` | Injects simulated UTC timestamp (`YYYY-MM-DD HH:MM:SS`) for retroactive testing. | `None` |

### Practical CLI Examples

```bash
# 1. Standard incremental pipeline run
python src/waid_orchestrate_lab.py --run-mode incremental

# 3. Resume pipeline from inference forecast step
python src/waid_orchestrate_lab.py --start-from waid_06_1_inference_forecast

# 4. Multi-period historical backfill
python src/waid_orchestrate_lab.py --run-mode backfill --begin-period 2026-01 --end-period 2026-03

# 5. Simulated historical execution using retro timestamp
python src/waid_orchestrate_lab.py --retro-now "2026-02-15 12:00:00"
```

---

## Scheduler & Simulation Engine (`waid_scheduler_lab.py`) <a id="scheduler--simulation-engine"></a>

Long-running daemon managing continuous operational loops and retroactive simulation backpasses.

### Usage Commands

```bash
# Continuous background execution (auto-initializes backfill if SQLite DB is missing)
python src/waid_scheduler_lab.py

# Retroactive historical simulation loop over a specific timeframe
python src/waid_scheduler_lab.py --retroactive \
    --retro-begin "2026-01-01 00:00:00" \
    --retro-end "2026-01-31 23:59:59"
```

---

## Prefect Workflow Management (`waid_prefect_manager.py`) <a id="prefect-workflow-management"></a>

Manages Prefect infrastructure bootstrapping, local API server checks, deployment registration (`prefect.yaml`), and worker pool execution.

```bash
# Standard deployment launch for active period
python src/waid_prefect_manager.py

# Target specific historical month
python src/waid_prefect_manager.py --period 2026-01

# Execute automated Prefect backfill flow
python src/waid_prefect_manager.py --auto-backfill
```

---

## Environment Reset Regimes (`WAID_SETUP_MODE`) <a id="environment-reset-regimes"></a>

The orchestrator inspects `WAID_SETUP_MODE` at runtime to control state reset levels:

| Mode Value | Regime Name | Operational Action |
| :---: | :--- | :--- |
| `0` | **Regime 0 (Standard)** | Standard incremental execution; no state is purged. |
| `1` | **Regime 1 (Soft Reset)** | Backs up environment; resets databases and ML artifacts while keeping raw ingested data. |
| `2` | **Regime 2 (Hard Reset)** | Purges all data directories; creates compressed ZIP archive prior to clean execution. |
| `3` | **Regime 3 (Force ML Training)** | Forces immediate Machine Learning retraining, bypassing retraining window guardrails. |

```bash
# Example: Triggering a Soft Reset run
export WAID_SETUP_MODE=1 && python src/waid_orchestrate_lab.py

# Example: Forcing ML Model retraining
export WAID_SETUP_MODE=3 && python src/waid_orchestrate_lab.py
```

---

## dbt Transformation Commands <a id="dbt-transformation-commands"></a>

Manual dbt commands for running and testing staging, intermediate bias, and inference models.

### Target Bias Variables

```text
max_bias_temp=3.0, max_bias_pres=15.0, max_bias_rh=30.0, 
max_bias_wind=2.0, max_bias_solar=50.0, max_bias_rain=2.0
```

### Execution Snippets

```bash
# 1. Staging Ecowitt Model & Tests
dbt run --select stg_ecowitt --target dev --vars '{"max_bias_temp": 3.0, "max_bias_pres": 15.0}'
dbt test --select stg_ecowitt --store-failures --target dev

# 2. Intermediate Bias Analysis Model
dbt run --select int_matches_bias --target dev
dbt test --select int_matches_bias --target dev

# 3. Full Model Refresh & Inference Quality Pipeline
dbt run --select station_metadata --full-refresh --target dev
dbt run --select +inference_quality --target dev
```

---

## Docker & ARM Edge Deployments <a id="docker--arm-edge-deployments"></a>

Convenience launcher scripts for containerized and edge hardware targets.

```bash
# Production stack (start.sh)
./start.sh up        # Launch production container stack
./start.sh logs      # Tail live container logs
./start.sh down      # Stop production containers

# Development & Lab profiles (start-lab.sh)
./start_lab.sh pipeline       # Local single pipeline pass
./start_lab.sh scheduler      # Local continuous scheduler
./start_lab.sh docker-edge    # ARM/Edge orchestrator container
./start_lab.sh docker-prefect # Prefect container stack

# Cross-compilation & ARM target deployment
./docker/build-docker.sh arm  # Cross-compile for ARM64 architecture
./docker/arm/deploy-arm.sh    # Remote SSH deployment to target edge board
```

---

## Configuration & Fallback Reference <a id="configuration--fallback-reference"></a>

Central system parameters managed via `WaidBoot` configuration broker (`config/boot.env` or `waid.env`):

| Parameter Name | Description | Default Fallback |
| :--- | :--- | :--- |
| `WAID_ECOWITT_GW_IP` | Local IP address for Ecowitt station gateway | `192.168.1.100` |
| `WAID_ECOWITT_STATION_ID` | Station unique identifier string | `STATION_01` |
| `WAID_ECOWITT_LATITUDE` | Station latitude (decimal degrees) | `41.9028` |
| `WAID_ECOWITT_LONGITUDE` | Station longitude (decimal degrees) | `12.4964` |
| `WAID_ECOWITT_ELEVATION_M` | Station elevation (meters above sea level) | `20.0` |
| `WAID_TIMEZONE` | Standard IANA Timezone string | `Europe/Rome` |
| `WAID_ERA5_API_KEY` | Copernicus CDS API Key | `placeholder_era5_key` |
| `WAID_DEPLOY_MODE` | Deployment target (`local` SQLite / `cloud` Supabase) | `local` |