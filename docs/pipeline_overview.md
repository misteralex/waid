# WAID (Weather AI Direct Nowcasting) Pipeline Architecture

The **WAID Platform** is an end-to-end data engineering and machine learning system for real-time microclimate nowcasting. It combines physical telemetry from local station hardware (Ecowitt) with regional reanalysis benchmarks (Copernicus ERA5) to train physics-informed LSTM models and deliver short-term forecasts.

## High-Level Execution Lifecycle

The data pipeline processes telemetry through five functional layers:

```
[ Ingest & Profile ] ---> [ Transform & Align ] ---> [ ML & Inference ] ---> [ Deploy & Viz ]
   (Ecowitt/ERA5)           (dbt / Feature Store)      (LSTM / Nowcast)       (SQLite/Supabase/Streamlit)

```

1. **Ingest & Profile**: Acquires raw high-frequency observations from local stations via HTTP and downloads NetCDF atmospheric reanalysis grids from Copernicus CDS. Evaluates initial schema integrity and temporal completeness.

2. **Transform & Align**: Converts local timestamps to continuous UTC sequences, cleans telemetry via **dbt**, matches station coordinates to ERA5 grids, enforces physical boundaries (physics guardrails), and calculates historical sensor biases.

3. **ML Feature Store & Tensor Processing**: Windowing and scaling of multi-dimensional feature tensors ($X$) and target deltas ($Y$), injecting theoretical clear-sky solar radiation and temporal cycle embeddings.

4. **Machine Learning & Nowcast Engine**: Retrains baseline Keras/PyTorch LSTM models when retraining thresholds are met, runs multi-step 6-hour nowcasts, applies physical safety constraints, and reconciles predictions with ground truth.

5. **Deployment & Analytics**: Exports metrics to local deployment SQLite or Supabase PostgreSQL, updates Streamlit visualization layers, and auto-compiles dbt lineage documentation.

## Pipeline Execution Paradigms

WAID supports two execution paradigms depending on hardware constraints and operational targets:

### 1. Lab CLI / Embedded Edge Mode (`waid_orchestrate_lab.py`)

* **Target Environment**: Standalone edge hardware (Raspberry Pi, ARM boards) or local debugging environments where heavy orchestration overhead must be avoided.

* **Mechanism**: Direct, sequential execution of scripts and dbt CLI steps via direct subprocess calls.

* **Scheduling**: Managed by `waid_scheduler_lab.py`, a lightweight operational daemon providing continuous execution loops, retroactive historical simulations (`WAID_RETRO_NOW`), and keep-alive ping management.

### 2. Orchestrated Cloud Mode (`waid_orchestrate.py`)

* **Target Environment**: Production cloud nodes, servers, or containerized environments.

* **Mechanism**: End-to-end Directed Acyclic Graph (DAG) managed by **Prefect**. Each stage is wrapped in a modular `@task` handling dependency resolution, automatic retries, concurrency, state management, and UI monitoring.

* **Infrastructure**: Managed via `waid_prefect_manager.py` for worker pool bootstrapping and automated deployment registration.

## Deployment Architectures

| Deployment Target | Storage / DB Layer | Orchestration Mode | Deployment Launcher | 
| ----- | ----- | ----- | ----- | 
| **Local / Edge Board** | SQLite (`waid_deploy.db`) | Lab CLI Scheduler (`waid_scheduler_lab`) | `start-lab.sh` / `start-arm.sh` | 
| **Cloud Production** | Supabase PostgreSQL | Prefect Engine (`waid_orchestrate`) | `start.sh` | 

### Environment Reset Regimes

During testing and backfill operations, the orchestration engines support four environment reset levels:

* **Regime 0 (Standard)**: Ingestion and processing run without clearing persistent stores.

* **Regime 1 (Soft Reset)**: Creates a lightweight state backup, purges compiled SQLite databases and ML model artifacts, but retains raw downloaded telemetry files.

* **Regime 2 (Hard Reset)**: Creates a compressed archive of the workspace and purges all raw data, SQLite databases, and build artifacts.

* **Regime 3 (Force ML model training)**: Bypasses minimum interval checks and forces Machine Learning retraining to update the active model artifact.

## Physics Guardrails & Data Quality

Physical bounds enforcement occurs before tensor formation and model inference:

* **Solar Radiation**: Nighttime solar radiation forced to zero ($G_{solar} = 0 \text{ W/m}^2$ when $h_{solar} \le 0$).

* **Precipitation**: Non-negative rainfall rates ($P \ge 0 \text{ mm/h}$).

* **Humidity**: Bound strictly within physical percentage limits ($RH \in [0, 100\%]$).

* **Thermodynamics**: Guarantees dew point constraints ($T_{dew} \le T_{ambient}$).

## Logging & Observability

* **Log Files**: Daily rolling log files stored at root under `logs/waid_pipeline_YYYYMMDD.log`.

* **Log Levels**: Configurable via `WAID_LOG_LEVEL` (`INFO` by default, `DEBUG` for verbose diagnostic tracing).

* **Retroactive Simulation Tracing**: When running historical playbacks (`--retroactive`), logs explicitly reflect `WAID_RETRO_NOW` context to track simulated execution timestamps.