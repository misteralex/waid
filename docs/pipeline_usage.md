# WAID (Weather AI Direct Nowcasting) Pipeline Usage

## Stage 01 — Ingestion & Profiling

### `waid_01_1_ingest_ecowitt.py`

Ingests hourly Ecowitt weather-station observations. To execute the Ecowitt telemetry ingestion script manually with your local station parameters, run the following command  from the repository root:

```bash
python src/waid_01_1_ingest_ecowitt.py --ip 192.168.1.100 --period 2026-08
```

### `waid_01_2_ingest_era5.py`

To execute the ERA5 atmospheric reanalysis download script manually with custom coordinates (e.g., Rome) and a specific target period, run the following command from the repository root:

```bash
python src/waid_01_2_ingest_era5.py --period 2026-08 --lat 41.9028 --lon 12.4964 --elevation 6
```

### `waid_01_3_profile_era5.py`

To execute the ERA5 data profiling and catalog validation script for a specific target period, run the following command from the repository root:

```bash
python src/waid_01_3_profile_era5.py --period 2026-08
```

## Stage 02: Synchronization & Staging

### `waid_02_1_sync_ecowitt.py`

To execute the Ecowitt synchronization script and import local station CSV data into the SQLite database with automatic UTC conversion, run the following command from the repository root:

```bash
python src/waid_02_1_sync_ecowitt.py --period 2026-08
```

## Stage 03: Matching & Bias Analysis

### `waid_03_1_match_datasets.py`

To execute the dataset matching and feature store alignment script for a specific target period, run the following command from the repository root:

```bash
python src/waid_03_1_match_datasets.py --period 2026-08
```

## Stage 04: Station Specs & Setup

### `waid_04_1_setup_specs.py`

To execute the hardware sensor specifications setup and profiling script, run the following command from the repository root:

```bash
python src/waid_04_1_setup_specs.py
```

## Stage 05: Machine Learning Tensors & Training

### `waid_05_1_ml_tensors.py`

To execute the 3D training tensor generation script (extracting features and temporal embeddings from local telemetry) for a specific target period, run the following command from the repository root:

```bash
python src/waid_05_1_ml_tensors.py --period 2026-08
```

### `waid_05_2_ml_train.py`

To execute the machine learning model training pipeline (including incremental scaling, tensor enrichment, and model registry synchronization), run the following command from the repository root:

```bash
python src/waid_05_2_ml_train.py
```

## Stage 06: Inference & Quality Assessment

### `waid_06_1_inference_engine.py`

To execute the WAID inference engine, which loads the trained LSTM model to perform multi-step forecasting and stores the results in the database, run the following command from the repository root:

```bash
python src/waid_06_1_inference_engine.py
```

### `waid_06_5_inference_quality.py`

To execute the quality assurance script and validate the presence and integrity of inference records within the SQLite database, run the following command from the repository root:

```bash
python src/waid_06_5_inference_quality.py
```

## Stage 07: Forecasting

### `waid_07_1_inference_forecast.py`

To execute the 6-hour weather inference pipeline (which reconstructs absolute meteorological values, enforces strict physics-safe guardrails, and updates the `inference_forecast` table with incremental consuntivo data), run the following command from the repository root:

```bash
python src/waid_07_1_inference_forecast.py
```

### `waid_07_2_export_deploy_db.py`

To execute the ETL script that extracts operational forecasts and quality metrics from the internal lab database and deploys them to the public SQLite database (`WAID_DB_DEPLOY_FILE`), run the following command from the repository root:

```bash
python src/waid_07_2_export_deploy_db.py
```
<br>

## Stage 08: Data Product & Visualization

<br>

### `waid_08_1_viz_streamlit_update.py`

To execute the final synchronization and deployment script (with safety controls via WAID_ENV to handle git push only in production),  run the following command from the repository root:

```bash
python src/waid_08_1_viz_streamlit_update.py
```

<br>

### `waid_08_2_viz_streamlit_app.py`

To launch the Streamlit public analytics dashboard, which provides dedicated visualizations for all six weather features and allows for three-way comparisons between model predictions, local sensor data (Ecowitt), and ERA5 ground truth metrics, run the following command from the repository root to launch the interactive Streamlit analytics dashboard:

```bash
streamlit run src/waid_08_2_viz_streamlit_app.py
```

To package the application and database for external deployment:
```bash
streamlit run src/waid_08_2_viz_streamlit_app.py --deploy
```
<br>

### `waid_08_3_doc_dbt_deploy.py`

To generate and deploy the automated Markdown data dictionary for dbt models within the Stage 08 pipeline, run the following command from the repository root:

```bash
python src/waid_08_3_doc_dbt_deploy.py
```

<br>

### `waid_08_4_viz_cli.py`

To execute the CLI visualizer for operational forecasts (including ERA5 ground truth comparisons and drift metrics), run the following command from the repository root:

```bash
python src/waid_08_4_viz_cli.py
```

## dbt Commands

The following commands are used to run and validate the main dbt models of the WAID pipeline.

### Common Configuration

The dbt commands use the following maximum allowable bias thresholds:

```text
max_bias_temp  = 3.0
max_bias_pres  = 15.0
max_bias_rh    = 30.0
max_bias_wind  = 2.0
max_bias_solar = 50.0
max_bias_rain  = 2.0
```

### 1. Ecowitt Staging

Run the `stg_ecowitt` model:

```bash
dbt run --select stg_ecowitt --target dev \
  --vars '{"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}'
```

Run the associated data-quality tests and store failed records:

```bash
dbt test --select stg_ecowitt --store-failures --target dev \
  --vars '{"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}'
```

### 2. Match Records

Run the `external_raw.match_records` source:

```bash
dbt run --select source:external_raw.match_records --target dev \
  --vars '{"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}'
```

Run the associated source tests:

```bash
dbt test --select source:external_raw.match_records --target dev \
  --vars '{"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}'
```

### 3. Bias Analysis

Run the `int_matches_bias` model:

```bash
dbt run --select int_matches_bias --target dev \
  --vars '{"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}'
```

Run the associated data-quality tests:

```bash
dbt test --select int_matches_bias --target dev \
  --vars '{"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}'
```

### 4. Station Metadata

Rebuild the `station_metadata` model:

```bash
dbt run --select station_metadata --full-refresh --target dev \
  --vars '{"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}'
```

### 5. Inference Statistics

Run the `inference_stats` model:

```bash
dbt run --select inference_stats --target dev \
  --vars '{"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}'
```

### 6. Inference Prediction

Rebuild the `inference_prediction` model:

```bash
dbt run --select inference_prediction --full-refresh --target dev \
  --vars '{"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}'
```

### 7. Inference Quality

Run the `inference_quality` model together with its upstream dependencies:

```bash
dbt run --select +inference_quality --target dev \
  --vars '{"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}'
```
---

## Additional Tools

The following components provide supporting services for the WAID pipeline, including scheduling, orchestration, bootstrap configuration, and shared utility functions.

| Tool | Description |
|---|---|
| **`waid_scheduler.py`** | **Continuous operational scheduler.** Checks the environment at startup and automatically triggers a historical backfill when the WAID database (`waid.db`) is not yet available. Once initialized, it periodically launches the pipeline in incremental mode through `waid_orchestrate.py`, passing the current period in `YYYY-MM` format. |
| **`waid_orchestrate.py`** | **Core pipeline orchestrator.** Coordinates the end-to-end WAID workflow, from dbt initialization and data ingestion, profiling, and alignment through Machine Learning training and inference. Supports incremental and backfill modes, reset operations, and propagation of the `--period` parameter across pipeline stages. |
| **`boot.py`** | **Bootstrap and configuration manager.** Loads and validates application and environment settings, configures logging through `loguru`, and validates required storage paths, SQLite databases, Ecowitt/ERA5 data directories, dbt resources, and Machine Learning tensor directories through the `WaidBoot` interface. |
| **`waid_shared.py`** | **Shared utility library.** Provides common functions for astronomical clear-sky solar radiation calculations, extraction and cleaning of Ecowitt telemetry, resampling and bounded interpolation, and retrieval of station metadata and sensor specifications from the SQLite Feature Store. |
| **`waid_analyze_bias.py`** | **Debugging and diagnostic utility.** Provided as a debugging and diagnostic utility within the WAID pipeline. It can be used to inspect bias-related results and perform sanity checks for a specific target period

---

## WAID Pipeline Orchestrator

The `waid_orchestrate.py` script is the central execution engine of the WAID project. It coordinates the end-to-end execution lifecycle, including environment setup, dbt project building, data ingestion, backfilling, incremental updates, and machine learning training/inference workflows.  

### Usage & Command-Line Arguments

The script supports various flags to control the execution scope, allowing for granular debugging and rapid iteration.

```bash
python waid_orchestrate.py [OPTIONS]
```

### Options Summary

| Flag | Description |
| :--- | :--- |
| --run-mode | Set to 'incremental' (default) or 'backfill' (for multi-period historical processing). |
| --skip-setup | Skips dbt setup steps (00_1 to 00_4) to save time during iteration. |
| --skip-ingestion | Skips raw data ingestion and mock update steps. |
| --only-setup | Runs only the dbt setup steps (00_1 to 00_4) and exit. |
| --start-from | Fast-forwards execution directly to a specific step function name. |
| --period | Specifies the target period (YYYY-MM) for the run. |
| --begin-period / --end-period | Defines the start and end date range for backfill mode. |
| --mock-now | Injects a simulated timestamp (YYYY-MM-DD HH:MM:SS) for retroactive execution. |

---

### Practical Examples

#### 1. Rapid Iteration (Skip Setup and Ingestion)
If you are iterating on the ML model or inference scripts and the dbt/data environment is already prepared, you can bypass the overhead of setup and ingestion:

```bash
python waid_orchestrate.py --skip-setup --skip-ingestion
```

#### 2. Standard Incremental Run
Executes the full pipeline for the current default period:
```bash
python waid_orchestrate.py --run-mode incremental
```

#### 3. Historical Backfill
Processes data preparation for a specific date range, followed by a final global Machine Learning & Inference cycle:
```bash
python waid_orchestrate.py --run-mode backfill --begin-period 2026-01 --end-period 2026-03
```

#### 4. Targeted Debugging
If a specific step in the ML sequence fails, you can skip to that step without re-running the entire data preparation pipeline:
```bash
python waid_orchestrate.py --start-from waid_06_1_inference_engine
```

#### 5. Simulation with Mock Time
Useful for testing how the system performs using historical timestamps:
```bash
python waid_orchestrate.py --mock-now "2026-02-15 12:00:00"
```

---

## WAID Scheduler Usage

The `waid_scheduler.py` script manages both live continuous execution and historical backfill/simulation tasks.

### Usage Commands

#### 1. Continuous Operational Mode (Default)
Starts the background service. It checks if the database is initialized (running a backfill if needed) and then enters an infinite loop.
```bash
python waid_scheduler.py
```

#### 2. Retroactive Simulation Mode
Processes historical data for a specific time window. This bypasses the infinite loop and processes step-by-step using the provided timestamps.
```bash
python waid_scheduler.py --retroactive \
    --mock-begin "2026-01-01 00:00:00" \
    --mock-end "2026-01-31 23:59:59"
```

### Options Summary
| Flag | Description |
| :--- | :--- |
| `--retroactive` | Enables batch mode to iterate through a historical timeframe. |
| `--mock-begin` / `--begin-period` | Start timestamp for simulation (YYYY-MM-DD HH:MM:SS). |
| `--mock-end` / `--end-period` | End timestamp for simulation (YYYY-MM-DD HH:MM:SS). |

---

## Environment Configuration
The orchestrator reads the WAID_SETUP_MODE environment variable to manage data state resets:

* Mode 0 (Regime): Standard incremental execution; no state is purged.
* Mode 1 (Soft Reset): Preserves raw data while resetting database and machine learning artifacts with an automatic backup.
* Mode 2 (Hard Reset): Purges all data in the directory and creates a full zip archive backup before execution.

Example:
```bash
export WAID_SETUP_MODE=1 && python waid_orchestrate.py --skip-setup
```


## dbt Models

The WAID dbt project is organized into source, staging, intermediate, and mart models.

| Model | Description |
|---|---|
| **`sources.yml`**<br>`dbt/models/sources.yml` | Defines the external data sources used by the WAID dbt project, including raw Ecowitt observations, Ecowitt–ERA5 matched records, Machine Learning inference data, and live forecast staging data. |
| **`stg_ecowitt.sql` / `stg_ecowitt.yml`**<br>`dbt/models/staging/` | Cleans and standardizes raw Ecowitt weather-station data from `ecowitt_records`. It removes invalid timestamps, casts measurements to numeric types, and applies data-quality tests for completeness, uniqueness, and physical ranges. |
| **`stg_matches.sql` / `stg_matches.yml`**<br>`dbt/models/staging/` | Standardizes the Ecowitt–ERA5 matching dataset and derives differences between local station observations and ERA5 reference values, providing the basis for bias analysis and downstream validation. |
| **`int_matches_bias.sql` / `int_matches_bias.yml`**<br>`dbt/models/intermediate/` | Computes operational biases between Ecowitt observations and ERA5 reference values for the main meteorological variables. It also applies configurable bias thresholds and generates quality/overflow indicators for downstream processing. |
| **`station_metadata.sql`**<br>`dbt/models/marts/` | Builds the `station_metadata` table from the station configuration, including location and elevation information, Machine Learning parameters, and database indexing. |
| **`inference_stats.sql`**<br>`dbt/models/marts/` | Aggregates Machine Learning inference records by model version and calculates statistical metrics, including means and standard deviations, to monitor model output behavior over time. |
| **`inference_prediction.sql`**<br>`dbt/models/marts/` | Incrementally processes and standardizes live Machine Learning inference records, filtering new predictions by timestamp for efficient downstream consumption. |
| **`inference_quality.sql`**<br>`dbt/models/marts/` | Evaluates Machine Learning predictions against actual station observations and ERA5 reference data, calculating deltas, absolute errors, and percentage errors for continuous model validation. |

## Docker

The WAID project provides cross-platform scripts and Docker configuration files to build, initialize, and run the application in a consistent containerized environment.

| Component | Description |
|---|---|
| **`build-docker.sh` / `build-docker.bat`** | Cross-platform build scripts for Linux/WSL and Windows. They initialize the required host-mounted directories for persistent data and dbt artifacts before triggering the Docker Compose build process. |
| **`docker-compose.yml`** | Defines the Docker services, volumes, environment configuration, and service orchestration required to run the WAID architecture. |
| **`Dockerfile`** | Defines the WAID application image, including the Python 3.12 runtime and required project dependencies. |
| **`entrypoint.sh`** | Container entrypoint responsible for runtime initialization and environment setup before starting the configured container service. |
| **`start.sh` / `start.bat`** | Cross-platform execution wrappers for Linux/WSL and Windows. They provide unified commands to launch the WAID pipeline, continuous scheduler, and Streamlit dashboards either locally or within Docker containers. |

## Testing

The WAID project uses **pytest** as its testing framework, with dedicated configuration and test discovery settings.

| Component | Description |
|---|---|
| **`tests/`** | Contains the automated test suite used to validate the main WAID components and pipeline functionality. |
| **`pyproject.toml`** | Defines project metadata, build configuration, runtime dependencies, and pytest-related settings. |
| **`conftest.py`** | Provides shared pytest configuration, fixtures, and test setup used across the test suite. |


## Python Virtual Environment

The WAID project uses standard Python dependency and environment management tools to ensure consistent development, testing, and deployment environments.

Create and activate a local Python virtual environment before installing the project dependencies.

### Linux / macOS / WSL

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```