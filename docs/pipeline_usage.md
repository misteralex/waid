# WAID (Weather AI Direct Nowcasting) - Pipeline Usage

* [Pipeline Stages](#pipelinestages)
* [Additional Tools](#addtools)
* [WAID Pipeline Orchestrator](#pipelineorch)
* [WAID Pipeline Scheduler](#pipelinesched)
* [External Environment Configuration](#envconf)
* [dbt Commands](#dbtcomm)
* [dbt Models](#dbtmod)
* [Docker](#docker)
* [Testing](#testing)
* [Python Virtual Environment](#envirt)
* [Configuration Parameters & Fallback Reference](#reqconf)

# Pipeline Stages <a id="pipelinestages"></a> 

## Stage 01 — Ingestion & Profiling

### `waid_01_1_ingest_ecowitt.py`

Ingests hourly Ecowitt weather-station observations. To execute the Ecowitt telemetry ingestion script manually with your local station parameters, run the following command  from the repository root:

```bash
python src/waid_01_1_ingest_ecowitt.py --ip 192.168.1.100 --period 2026-08
```

### `waid_01_2_ingest_era5.py`

To execute the ERA5 atmospheric reanalysis download script manually with custom coordinates (e.g., Rome) and a specific target period, run the following command from the repository root:

```bash
python src/waid_01_2_ingest_era5.py --period 2026-08 --lat 41.9028 --lon 12.4964
 --elevation 6
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

### `waid_06_1_inference_forecast.py`

To execute the 6-hour weather inference pipeline (which reconstructs absolute meteorological values, enforces strict physics-safe guardrails, and updates the `inference_forecast` table with incremental consuntivo data), run the following command from the repository root:

```bash
python src/waid_06_1_inference_forecast.py
```

### `waid_06_4_inference_quality.py`

To execute the quality assurance script and validate the presence and integrity of inference records within the SQLite database, run the following command from the repository root:

```bash
python src/waid_06_4_inference_quality.py
```

## Stage 07: Forecasting


### `waid_07_1_export_deploy_db.py`

To execute the ETL script that extracts operational forecasts and quality metrics from the internal lab database and deploys them to the public SQLite database (`WAID_DEPLOY_FILE`), run the following command from the repository root:

```bash
python src/waid_07_1_export_deploy_db.py
```
<br>

## Stage 08: Data Product & Visualization

<br>

### `waid_08_1_viz_streamlit_app.py`

To launch the Streamlit public analytics dashboard, which provides dedicated visualizations for all six weather features and allows for three-way comparisons between model predictions, local sensor data (Ecowitt), and ERA5 ground truth metrics, run the following command from the repository root to launch the interactive Streamlit analytics dashboard:

```bash
streamlit run src/waid_08_1_viz_streamlit_app.py
```

To package the application and database for external deployment:
```bash
streamlit run src/waid_08_1_viz_streamlit_app.py --deploy
```
<br>

### `waid_08_2_doc_dbt_deploy.py`

To generate and deploy the automated Markdown data dictionary for dbt models within the Stage 08 pipeline, run the following command from the repository root:

```bash
python src/waid_08_2_doc_dbt_deploy.py
```
--- 

## Additional Tools <a id="addtools"></a>

The following components provide supporting services for the WAID pipeline, including scheduling, orchestration, bootstrap configuration, and shared utility functions.

| Tool | Description |
|---|---|
| **`waid_scheduler_lab.py`** | **Continuous operational scheduler.** Checks the environment at startup and automatically triggers a historical backfill when the WAID database (`waid.db`) is not yet available. Once initialized, it periodically launches the pipeline in incremental mode through `waid_orchestrate_lab.py`, passing the current period in `YYYY-MM` format. |
| **`waid_orchestrate_lab.py`** | **Core pipeline orchestrator.** Coordinates the end-to-end WAID workflow, from dbt initialization and data ingestion, profiling, and alignment through Machine Learning training and inference. Supports incremental and backfill modes, reset operations, and propagation of the `--period` parameter across pipeline stages. |
| **`boot.py`** | **Bootstrap and configuration manager.** Loads and validates application and environment settings, configures logging through `loguru`, and validates required storage paths, SQLite databases, Ecowitt/ERA5 data directories, dbt resources, and Machine Learning tensor directories through the `WaidBoot` interface. |
| **`waid_shared.py`** | **Shared utility library.** Provides common functions for astronomical clear-sky solar radiation calculations, extraction and cleaning of Ecowitt telemetry, resampling and bounded interpolation, and retrieval of station metadata and sensor specifications from the SQLite Feature Store. |
| **`waid_analyze_bias.py`** | **Debugging and diagnostic utility.** Provided as a debugging and diagnostic utility within the WAID pipeline. It can be used to inspect bias-related results and perform sanity checks for a specific target period. |
| **`waid_inspect_forecast.py`** | **Debugging and diagnostic utility.** CLI visualizer for operational forecasts (including ERA5 ground truth comparisons and drift metrics). |

---

## WAID Pipeline Orchestrator <a id="pipelineorch"></a>

The `waid_orchestrate_lab.py` script is the central execution engine of the WAID project. It coordinates the end-to-end execution lifecycle, including environment setup, dbt project building, data ingestion, backfilling, incremental updates, and machine learning training/inference workflows.  

### Usage & Command-Line Arguments

The script supports various flags to control the execution scope, allowing for granular debugging and rapid iteration.

```bash
python waid_orchestrate_lab.py [OPTIONS]
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
python waid_orchestrate_lab.py --skip-setup --skip-ingestion
```

#### 2. Standard Incremental Run
Executes the full pipeline for the current default period:
```bash
python waid_orchestrate_lab.py --run-mode incremental
```

#### 3. Historical Backfill
Processes data preparation for a specific date range, followed by a final global Machine Learning & Inference cycle:
```bash
python waid_orchestrate_lab.py --run-mode backfill --begin-period 2026-01 --end-period 2026-03
```

#### 4. Targeted Debugging
If a specific step in the ML sequence fails, you can skip to that step without re-running the entire data preparation pipeline:
```bash
python waid_orchestrate_lab.py --start-from waid_06_1_inference_forecast
```

#### 5. Simulation with Mock Time
Useful for testing how the system performs using historical timestamps:
```bash
python waid_orchestrate_lab.py --mock-now "2026-02-15 12:00:00"
```

---

### WAID Prefect Scheduler

Weather-AI (WAID) integrates Prefect for robust workflow orchestration using a two-tier execution pattern:
- `waid_prefect_manager.py`: Handles server lifecycle management, dynamic deployment generation (prefect.yaml), work pool configuration, and worker execution.
- `waid_orchestrate.py`: Serves as the core orchestrator script, structuring ingestion, dbt transformations, ML training, inference, and visualization into modular Prefect tasks and flows.

#### `waid_prefect_manager.py`
Usage & Usage Example - Prerequisites
- Python Version: Python 3.9
- Dependencies: prefect (2.x), httpx, pyyaml, loguru, boot
- Environment Variables: PREFECT_API_URL (default: [http://127.0.0.1:4200/api](http://127.0.0.1:4200/api)), SCHEDULER_INTERVAL_SEC (default: 3600).

**Usage: python waid_prefect_manager.py [options]**

Options:
-  --period PERIOD        Target month in YYYY-MM format (e.g. 2026-02)
-  --skip-ingestion       Skip data ingestion and profiling sub-flows
-  --auto-backfill        Execute historical data backfill mode

#### Execution Example

Start Prefect server, register deployment for current month, and run worker
**python waid_prefect_manager.py**

Deploy Prefect orchestrator for a specific historical month
**python waid_prefect_manager.py --period 2026-01**

Run Prefect orchestrator in backfill mode
**python waid_prefect_manager.py --auto-backfill**

#### `waid_orchestrate.py`
Options:
-  --period PERIOD        Target month in YYYY-MM format (e.g. 2026-02)
-  --skip-ingestion       Skip data ingestion and dbt preparation sub-flows
-  --auto-backfill        Execute historical data backfill across specified month range

#### Execution Example

Execute standard pipeline for the current month
**python waid_orchestrate.py**

Execute standard pipeline for a specific month
**python waid_orchestrate.py --period 2026-01**

Execute ML training and inference skipping ingestion/preparation
**python waid_orchestrate.py --skip-ingestion**

Run historical backfill across configured month ranges
**python waid_orchestrate.py --auto-backfill**

---

## WAID Pipeline Scheduler <a id="pipelinesched"></a>

The `waid_scheduler_lab.py` script manages both live continuous execution and historical backfill/simulation tasks.

### Usage Commands

#### 1. Continuous Operational Mode (Default)
Starts the background service. It checks if the database is initialized (running a backfill if needed) and then enters an infinite loop.
```bash
python waid_scheduler_lab.py
```

#### 2. Retroactive Simulation Mode
Processes historical data for a specific time window. This bypasses the infinite loop and processes step-by-step using the provided timestamps.
```bash
python waid_scheduler_lab.py --retroactive \
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

## External Environment Configuration <a id="envconf"></a>
The orchestrator reads the WAID_SETUP_MODE environment variable to manage data state resets:

* Mode 0 (Regime): Standard incremental execution; no state is purged.
* Mode 1 (Soft Reset): Preserves raw data while resetting database and machine learning artifacts with an automatic backup.
* Mode 2 (Hard Reset): Purges all data in the directory and creates a full zip archive backup before execution.
* Mode 3 (ML Retraining): Forcing ML model retraining, bypassing minimum training interval guardrails.

Example:
```bash
export WAID_SETUP_MODE=1 && python waid_orchestrate_lab.py --skip-setup
```
---

## dbt Commands <a id="dbtcomm"></a>

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

## dbt Models <a id="dbtmod"></a>

The WAID dbt project is organized into source, staging, intermediate, and mart models.

| Model | Description |
|---|---|
| `dbt/models/sources.yml` | Defines the external data sources used by the WAID dbt project, including raw Ecowitt observations, Ecowitt–ERA5 matched records, Machine Learning inference data, and live forecast staging data. |
| `ecowitt_records` | Raw telemetry staging store for direct high-frequency weather station readings
|  `stg_ecowitt` (stg_ecowitt.sql, stg_ecowitt.yml) | It acts as the dbt staging layer that cleans, standardizes, and type-casts raw Ecowitt station telemetry into unified meteorological variables.
| `match_records` (stg_matches.sql, stg_matches.yml) | It establishes an exact timestamp-by-timestamp join between physical station measurements (*_eco) and global reanalysis reference values (*_era5).
| `int_matches_bias` (int_matches_bias.sql, int_matches_bias.yml) | Intermediate transformation layer calculating operational sensor biases and anomalies between ground telemetry and reanalysis data
| `station_metadata` (station_metadata.sql) | Central configuration and metadata repository storing spatial coordinates, hardware specifications, and machine learning retraining hyper-parameters for weather stations
| `ml_model_registry` | Central operational catalog tracking trained machine learning model artifacts, dataset lineage, scalers, and deployment states
| `inference_records` | Store for predictions, model outputs, and calculated feature snapshots generated during real-time or batch inference runs
| `inference_stats` (inference_stats.sql) | Aggregated statistical store recording ensemble voting consensus and variance across model inference predictions
| `inference_quality` (inference_quality.sql) | Comprehensive benchmark evaluation store comparing model predictions against both actual station ground truth and ERA5 reanalysis data

### `ecowitt_records`
This table serves as the primary ingestion store for raw telemetry collected from local Ecowitt weather stations.
- Primary Function: It captures high-frequency, multi-sensor meteorological observations directly from Ecowitt devices at defined continuous intervals.
- Key Columns & Measurement Metrics:
  - timestamp (ISO 8601 text string used as the Primary Key) and epoch_timestamp (Unix epoch integer) for reliable time-series indexing.
  - Thermal & Moisture Metrics: Indoor/outdoor temperatures (indoor_temperature_c, outdoor_temperature_c), relative humidity (indoor_humidity, outdoor_humidity), calculated metrics (dew_point_c, feels_like_c), and Vapor Pressure Deficit (vpd_kpa).
  - Wind Telemetry: Sustained wind speed (wind_m_s), gust speed (gust_m_s), and wind direction (wind_direction_deg).
  - Barometric Pressure: Absolute (abs_pressure_hpa) and sea-level relative pressure (rel_pressure_hpa).
  - Solar Data: Solar radiation (solar_rad_w_m2) and UV index (uv_index).

Precipitation Measurements: Traditional tipping-bucket and modern haptic piezo rain measurements aggregated across various temporal windows (rate, hourly, event, daily, weekly, monthly, yearly).

Role in Pipeline: It acts as the raw operational source table in SQLite before data staging, validation, and alignment with ERA5 reanalysis datasets via dbt models.

### `stg_ecowitt`
This table serves as the cleaned staging layer within the dbt data transformation pipeline, casting raw station measurements into normalized, consistent weather metrics ready for analytical downstream processing.

- Primary Function: It standardizes, renames, and type-casts raw sensor fields from ecowitt_records into a unified schema for core meteorological variables.
- Key Columns & Measurement Metrics:
  - timestamp: ISO-formatted text identifier representing the exact measurement time.
  - temperature: Outdoor temperature value cast to floating-point number.
  - humidity: Relative humidity percentage.
  - pressure_hpa: Barometric pressure normalized in hectopascals (hPa).
  - wind_speed: Wind speed in meters per second (m/s).
  - solar_radiation: Solar irradiance in watts per square meter (W/m²).
  - hourly_rain: Accumulated liquid precipitation over the preceding hour in millimeters (mm).

It acts as the intermediate staging dataset (stg_ecowitt) created by dbt transformations, removing raw telemetry clutter and providing a clean input layer for feature extraction, bias calculation, and alignment with ERA5 reanalysis grids.

### `match_records`
This table serves as the core temporal alignment dataset that pairs local ground-truth station telemetry directly with localized ERA5 atmospheric reanalysis grid data.
- Primary Function: It establishes an exact timestamp-by-timestamp join between physical station measurements (*_eco) and global reanalysis reference values (*_era5).
- Key Columns & Measurement Metrics:
  - timestamp: ISO-formatted text primary key used for temporal synchronization.
  - ERA5 Reanalysis Metrics (*_era5): Reanalysis baseline values for temperature, barometric pressure, relative humidity, wind speed, solar radiation, and rainfall (temp_era5, pres_era5, rh_era5, wind_era5, solar_era5, rain_era5).
  - cowitt Station Telemetry (*_eco): Corresponding observed ground-truth values recorded by the local station (temp_eco, pres_eco, rh_eco, wind_eco, solar_eco, rain_eco).

It serves as the primary dataset for sensor bias quantification, drift analysis, dbt model transformations (int_matches_bias), and machine learning model feature matrix generation.

### `int_matches_bias`
This table serves as the intermediate dbt transformation model designed to compute operational sensor biases and detect systemic measurement anomalies between physical station readings and ERA5 reanalysis baselines.

- Primary Function: It calculates parameter-level error differentials (bias_* = ecowitt_* - era5_*) across all core weather variables to quantify local microclimate deviations and hardware drift.
- Key Columns & Measurement Metrics:
  - timestamp: ISO-formatted text identifier representing the aligned time window.
  - Observed & Reanalysis Metric Triplets: Structured trios for temperature (temp), barometric pressure (pres), relative humidity (rh), wind speed (wind), solar radiation (solar), and rainfall (rain):
    - ecowitt_*: Ground-truth telemetry measured by the local weather station.
    - era5_*: Localized ERA5 reanalysis reference grid value.
    - bias_*: Derived absolute error value indicating sensor deviation or localized microclimate effects.
  - bias_overflow_flag: Boolean/integer indicator flagging records where calculated sensor biases exceed configurable operational thresholds.

It acts as the primary feature engineering input layer for machine learning model training, error benchmarking, and drift monitoring in downstream pipeline steps.

### `station_metadata`
This table serves as the central metadata registry and configuration store for all operational weather stations within the WAID ecosystem.
- station_id & station_name: Unique identifier and descriptive label for the reporting station (enforced by idx_station_metadata_station_id).
- Spatial Attributes (latitude, longitude, elevation_m, height_above_ground_m): Geographic coordinates and physical placement heights used for spatial interpolation, lapse rate adjustments, and matching station data with ERA5 reanalysis grid cells.
- ML Lifecycle Rules (min_training_days, retrain_window_days): Configurable thresholds governing pipeline orchestration, determining the minimum historical data volume required before model training and the sliding window frequency for model retraining.
- sensor_specs & updated_at: JSON/text-encoded hardware specification metadata and record update timestamps.

It acts as the foundational reference table queried by ingestion engines, dbt spatial transformations, and Prefect orchestrators to parameterize model training windows and spatial reanalysis matching.

### `ml_model_registry`
This table serves as the machine learning model registry and tracking catalog for all trained models across weather stations within the WAID pipeline.
- Primary Function: It maintains full lineage and lifecycle state for machine learning models, recording trained artifact locations, input/output data scalers, training sample sizes, performance metrics, and active deployment flags.
- Key Columns & Metadata Attributes:
  - model_version: Unique version string identifier serving as the Primary Key.
  - station_id: Foreign Key referencing station_metadata(station_id) to tie each model version to a specific physical station.*
  - Temporal & Lineage Identifiers (trained_at, last_ecowitt_timestamp, train_samples_count): Timestamps recording when training occurred, the latest raw observation timestamp included in the training set, and total training sample count for auditability.
  - Artifact File Paths (model_path, x_scaler_path, y_scaler_path): Absolute or relative disk paths to serialized model binaries (e.g., ONNX, PyTorch, or Scikit-learn) and feature/target normalization scalers.
  - Performance & State Indicators (metrics_mse, is_active): Mean Squared Error evaluation metric and an integer flag (1 or 0) marking the currently active model for inference execution.

It acts as the single source of truth for the inference engine (waid_06_4_inference_quality.py or export modules), ensuring that only validated, active model artifacts and matching scalers are loaded during real-time bias correction and prediction runs.

### `inference_records`
This table serves as the primary operational logging store for all machine learning model predictions generated by the WAID inference engine (waid_06_1_inference_forecast.py).
- Primary Function: It stores time-stamped inference outputs, tracking both the temporal scope of the prediction windows and the exact meteorological feature predictions produced by active model versions.
- Key Columns & Operational Attributes:
  - Primary Key & Execution Timestamps (id, ts_emission): Auto-incrementing identifier and automatic timestamp (CURRENT_TIMESTAMP) recording when the inference job was executed.
  - Window & Observation Timestamps (ts_window_start, ts_window_end, timestamp): Datetime markers defining the input data window bounds and the target prediction observation timestamp.
  - Model Lineage Metadata (model_version, model_version_tag, n_features_used): Tracks the exact model version used from ml_model_registry, optional tag/alias strings, and total count of feature variables fed into the model.
  - Inference Output Variables: Model predictions or bias-corrected values for core weather parameters including outdoor temperature (outdoor_temperature_c), relative humidity (outdoor_humidity), barometric pressure (abs_pressure_hpa), wind speed (wind_m_s), solar radiation (solar_rad_w_m2), and hourly precipitation (hourly_rain_mm).

It serves as the final downstream target for ML predictions, enabling performance monitoring, prediction quality evaluation, historical accuracy tracking, and data visualization across reporting dashboards.

### `inference_stats`
This table serves as the statistical quality assurance store within the WAID inference pipeline, recording ensemble consensus values and variance metrics across model prediction runs.
- Primary Function: It computes and logs aggregated statistical metrics (mean consensus and standard deviation) generated by ensemble models or multi-vote inference processes for each prediction window.
- Key Columns & Operational Attributes:
  - Model & Time Lineage (model_version, timestamp): Identifies the specific model or ensemble version and the target observation datetime.
  - Ensemble Metrics (n_votes): Integer count of model votes or sub-model iterations contributing to the consensus calculation.
  - Consensus & Variance Metric Pairs: Mean predictions (consensus_*) alongside their corresponding standard deviations (std_*) measuring prediction uncertainty across key parameters:
    - Temperature: consensus_temp, std_temp
    - Pressure: consensus_pres, std_pres
    - Relative Humidity: consensus_rh, std_rh
    - Wind Speed: consensus_wind, std_wind
    - Solar Radiation: consensus_solar, std_solar
    - Rainfall: consensus_rain, std_rain

It acts as the primary analytical reference for measuring prediction dispersion and model confidence, allowing downstream monitoring dashboards to flag high-variance predictions and track ensemble agreement over time.

### `inference_quality`
This table serves as the primary post-inference benchmarking and quality assurance dataset, enabling direct accuracy evaluation of model predictions against ground-truth station observations and ERA5 reanalysis baselines.
- Primary Function: It consolidating model predictions, ground telemetry, and reanalysis data side-by-side to compute operational error metrics (signed deltas, absolute errors, and percentage errors) for each forecast window.
- Key Columns & Operational Attributes:
  - Temporal & Model Identifiers (timestamp, model_version): Target observation timestamp and the specific active ML model version evaluated.
  - Triple-Source Parameter Sets: Stores values across three sources for temperature, pressure, relative humidity, wind speed, solar radiation, and rainfall:
    - pred_*: Model-predicted or bias-corrected values generated by the inference engine.
    - actual_*: Real-time ground-truth telemetry measured by the local station.
    - *_era5: Corresponding ERA5 reanalysis reference grid values.
  - Derived Error Metrics:
    - delta_*: Signed prediction residuals ($actual - pred$) indicating direction of bias (overestimation vs. underestimation).
    - abs_error_*: Absolute error values $\vert{}actual - pred\vert{}$ used for MAE calculation.
    - perc_error_*: Relative percentage error metrics used to assess relative accuracy across varying scale magnitudes.

It acts as the core analytical data source for monitoring model degradation over time, triggering automatic model retraining workflows, and feeding reporting dashboards for performance visualization.

--- 

## Docker <a id="docker"></a>

The WAID project provides cross-platform scripts and Docker configuration files to build, initialize, and run the application in a consistent containerized environment.

| Component | Description |
|---|---|
| **`build-docker.sh` / `build-docker.bat`** | Cross-platform build scripts for Linux/WSL and Windows. They initialize the required host-mounted directories for persistent data and dbt artifacts before triggering the Docker Compose build process. |
| **`docker-compose.yml`** | Defines the Docker services, volumes, environment configuration, and service orchestration required to run the WAID architecture. |
| **`Dockerfile`** | Defines the WAID application image, including the Python 3.12 runtime and required project dependencies. |
| **`entrypoint.sh`** | Container entrypoint responsible for runtime initialization and environment setup before starting the configured container service. |
| **`start.sh` / `start.bat`** | Cross-platform execution wrappers for Linux/WSL and Windows. They provide unified commands to launch the WAID pipeline, continuous scheduler, and Streamlit dashboards either locally or within Docker containers. |
| **`deploy-arm.sh`** | Automates the end-to-end packaging, cross-compilation, network transfer, and remote deployment of the WAID platform to an ARM-based target device |

## Script - Prerequisites
- Operating System: Linux / WSL2
- Permissions: Executable rights (chmod +x start.sh)
- Dependencies: Docker with docker compose plugin installed, valid config/boot.env configuration file.

### start.sh

**Usage: ./start.sh [option]**

Available options:
  up, run             - Starts production container stack in Docker (default)
  down                - Stops and removes production containers
  logs                - Tail live production logs
  --help, -h          - Shows help menu

**CLI Execution Example**
```
# Grant execution permissions
chmod +x start.sh

# Start production orchestration stack in background/foreground
./start.sh up

# Display live container execution logs
./start.sh logs

# Stop production containers
./start.sh down
```

### start-lab.sh

**Usage: ./start_lab.sh [option]**

Options:
  - pipeline | local-pipeline      Runs single pipeline pass locally
  - scheduler | local-scheduler    Starts continuous scheduler daemon locally
  - dashboard | local-dashboard    Starts Streamlit dashboard locally
  - docker-edge | edge             Starts Edge orchestrator in Docker container
  - docker-prefect | prefect       Starts Prefect workflow stack with state pre-clean
  - clean-prefect | clean          Cleans Prefect temporary lock/WAL files
  - down | stop | docker-down      Stops and removes all Docker Lab containers
  - --help | -h                    Shows usage help menu

**CLI Execution Example**
```
# 1. Grant execution permissions
chmod +x start_lab.sh

# 2. Launch single pipeline pass locally
./start_lab.sh pipeline

# 3. Start Prefect orchestrator stack in Docker
./start_lab.sh docker-prefect

# 4. Stop and remove all running Docker Lab containers
./start_lab.sh down
```

### build-docker.sh

It automates the preparation and container build process for the WAID platform across Linux and WSL environments. It automatically navigates to the repository root, loads default runtime environment variables from `config/boot.env`, creates required local storage directories, and delegates the build execution to docker compose.

**Usage: ./docker/build-docker.sh [ENVIRONMENT]**

- ENVIRONMENT (Optional): Specifies the target execution profile:
  - `prod` (Default): Builds the production container environment.  
  - `lab`: Builds the development/laboratory environment.  
  - `arm`: Cross-compiles the Docker image for 64-bit ARM architectures (linux/arm64).  

**CLI Execution Example**
```
./docker/build-docker.sh
# Equivalent to: ./docker/build-docker.sh prod
```

### deploy-arm.sh

It automates the end-to-end packaging, cross-compilation, network transfer, and remote deployment of the WAID platform to an ARM-based target device (e.g., Raspberry Pi). It handles local environment validation, database optimization, Docker ARM64 image building, artifact bundling, SCP transfer, and remote container orchestration via SSH.

**Usage:**
```
./docker/arm/deploy-arm.sh
```

---

## Testing <a id="testing"></a>

The WAID project uses **pytest** as its testing framework, with dedicated configuration and test discovery settings.

| Component | Description |
|---|---|
| **`tests/`** | Contains the automated test suite used to validate the main WAID components and pipeline functionality. |
| **`pyproject.toml`** | Defines project metadata, build configuration, runtime dependencies, and pytest-related settings. |
| **`conftest.py`** | Provides shared pytest configuration, fixtures, and test setup used across the test suite. |


## Python Virtual Environment <a id="envirt"></a>

The WAID project uses standard Python dependency and environment management tools to ensure consistent development, testing, and deployment environments.

Create and activate a local Python virtual environment before installing the project dependencies.

### Linux / macOS / WSL

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration Parameters & Fallback Reference <a id="reqconf"></a>

This document provides a comprehensive reference for the WAID pipeline's environment configuration parameters. The pipeline utilizes an automated **fallback mechanism** to ensure operational continuity, which triggers warning logs when specific environment variables are missing, empty, or incorrectly formatted.

---

## 1. Gateway & Station Metadata
These parameters define the physical and network identity of your weather station.

| Parameter | Description | Default Fallback |
| :--- | :--- | :--- |
| `WAID_ECOWITT_GW_IP` | Local IP address for Ecowitt gateway | `192.168.1.100` |
| `WAID_ECOWITT_STATION_ID` | Unique identifier (must exist in `station_metadata`) | `STATION_01` |
| `WAID_ECOWITT_STATION_NAME` | Descriptive name for the weather station | `Local Home Weather Station` |
| `WAID_ECOWITT_LATITUDE` | Station latitude (decimal degrees) | `41.9028` |
| `WAID_ECOWITT_LONGITUDE` | Station longitude (decimal degrees) | `12.4964` |
| `WAID_ECOWITT_ELEVATION_M`| Station elevation (meters above sea level) | `20.0` |
| `WAID_ECOWITT_FLOOR` | Building floor level | `2` |
| `WAID_TIMEZONE` | IANA Timezone identifier | `Europe/Rome` |

---

## 2. External Services & APIs
Required for data synchronization and external API integration.

| Parameter | Description | Default Fallback |
| :--- | :--- | :--- |
| `WAID_ERA5_API_KEY` | Copernicus CDS API Authentication Key | `placeholder_era5_key` |

---

## 3. Database Connection Parameters (BaaS)
The pipeline supports multi-target environments. If credentials are missing for a specific target, the system defaults to safe placeholders to prevent runtime exceptions during the boot process.

| Environment | Host | User | Password |
| :--- | :--- | :--- | :--- |
| **DRAFT** | `host_placeholder` | `user_placeholder` | `password_placeholder` |
| **PROD** | `host_placeholder` | `user_placeholder` | `password_placeholder` |
| **RETRO** | `host_placeholder` | `user_placeholder` | `password_placeholder` |

> **⚠️ Security Warning**: Fallback values are strictly for local development and debugging. **Never** use these placeholders in production environments. Always configure your actual database credentials via secure environment variables or secret management systems.

---

## How it works
The `boot` module evaluates your configuration in three layers:
1. **Direct Injection**: Reads values from active environment variables.
2. **File Load**: Loads local `waid.env` if present.
3. **Fallback Logic**: If a variable remains `None` or whitespace, the `get_env_with_fallback` function logs a `[CONFIG_FALLBACK]` warning and injects the specified default value.

For any deployment, ensure your `.env` file reflects the specific requirements for your target environment to maintain data integrity and security.