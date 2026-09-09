## WAID (Weather AI Direct Nowcasting) Pipeline Architecture & Execution Flow

The orchestration chain, managed by **Prefect**, follows a modular, end-to-end data engineering and machine learning lifecycle. It moves sequentially through ingestion, transformation, bias analysis, model training, inference, and visualization.


### Pipeline Execution Summary Table

| Phase | Main Modules | Key Responsibility |
| --- | --- | --- |
| **Ingest & Profile** | `waid_01_*` | Raw data extraction (**Ecowitt** & **ERA5**) and data catalog profiling. |
| **Transform & Align** | `waid_02_*`, `waid_03_*`, `waid_04_*` | Timestamp sync, dbt cleaning, dataset matching, and bias metric evaluation. |
| **ML & Inference** | `waid_05_*`, `waid_06_*` | Tensor creation, model training, inference evaluation, and forecasting. |
| **Deploy & Viz** | `waid_07_*`, `waid_08_*` | Local and **Supabase** DB export, **Streamlit** cache updates, and UI dashboard delivery. |

---

### Pipeline Execution Paradigms: Lab CLI vs. Prefect Orchestrator
The WAID pipeline supports two distinct execution modes depending on the operational environment:
* **Lab Mode (Script Sequence)**: Direct, sequential execution of standalone Python scripts and dbt models via CLI commands. This mode is ideal for local debugging, rapid prototyping, and granular step-by-step verification. Refer to `waid_orchestrate_lab.py` for full implementation details.

* **Orchestrated Mode (Prefect)**: Managed end-to-end via a unified Prefect Flow, where each pipeline step is encapsulated into modular `@task` functions. Prefect handles DAG dependency management, concurrency, state tracking, automatic retries, and UI logging. Refer to `waid_orchestrate.py` for full implementation details.

#### **1. Data Ingestion & Profiling (Extraction & Catalog)**

* **Lab / Script Execution Mode:** <div style="margin-left: 40px;">  `waid_01_1_ingest_ecowitt`
`waid_01_2_ingest_era5`
`waid_01_3_profile_era5`
* **Purpose:** Ingests raw observational feeds from local station data (Ecowitt) and reanalysis weather sources (ERA5). Generates initial data profiling and schema validation before downstream processing.
* **Files**: CSV / NetCDF-formatted data
* **Tables**: None

#### **2. Data Transformation, Alignment & Bias Analysis**

* **Lab / Script Execution Mode:** <div style="margin-left: 40px;"> 
`waid_02_1_sync_ecowitt`
`waid_02_2_dbt_staging_ecowitt`
`waid_03_1_match_datasets`
`waid_03_2_dbt_matches`
`waid_03_3_dbt_matches_bias`
`waid_04_1_setup_metadata`
</div>

* **Purpose:** Synchronizes timestamps and handles data cleaning using dbt transformations. Spatially/temporally matches ERA5 and Ecowitt datasets, executes dbt models to derive statistical bias metrics between predicted/reanalysis data and ground truth, runs diagnostic utility checks (`waid_analyze_bias`), and registers dataset metadata specs.

* **Tables**: <div style="margin-left: 40px;"> 
Step 02.1 `ecowitt_records`
Step 02.2 `stg_ecowitt (stg_ecowitt.sql, stg_ecowitt.yml)`
Step 03.1 `match_records`
Step 03.2 `match_records`
Step 03.3 `int_matches_bias (int_matches_bias.sql, int_matches_bias.yml)`
Step 04.1 `station_metadata`
</div>


#### **3. Machine Learning Pipeline & Inference Engine**

* **Lab / Script Execution Mode:** <div style="margin-left: 40px;"> 
`waid_05_1_ml_tensors`
`waid_05_2_ml_train`
`waid_06_1_inference_forecast`
`waid_06_2_inference_stats`
`waid_06_3_dbt_inference_quality`
`waid_06_4_inference_quality`

* **Purpose:** Formats cleaned feature tables into multi-dimensional tensors for PyTorch/ML frameworks. Trains the baseline ML model (`05_2`), executes batch inference (`06_1`), and evaluates prediction quality using both dbt models and Python scoring scripts (`06_3`, `06_4`) before generating final forecast outputs (`07_1`).
* **Files**: <div style="margin-left: 40px;">
    - Step 05.1 (Refer to `waid.env`)
        - `WAID_ML_MODEL_H5_FILE`
        - `WAID_ML_INPUT_SCALER_PKL_FILE`
        - `WAID_ML_OUTPUT_SCALER_PKL_FILE`
    - Step 05.2 PKL formatted data

* **Tables**: <div style="margin-left: 40px;">Step 05.1 `stg_ecowitt`
Step 05.2 `ml_model_registry`
Step 06.1 `inference_records`
Step 06.2 `inference_stats (inference_stats.sql)`
Step 06.3 `inference_quality (inference_quality.sql)`
Step 06.4 `inference_quality`

#### **4. Deployment & Visualization**

* **Lab / Script Execution Mode:** <div style="margin-left: 40px;"> 
`waid_07_1_export_deploy_db`
`waid_08_1_viz_streamlit_app.py`
`waid_08_2_doc_dbt_deploy.py`

* **Purpose:** Exports the processed metrics, forecasts, and predictions into a lightweight deployment database. Triggers an update to the visualization state and launches the Streamlit dashboard UI for user interaction. Generates and synchronizes dbt-compatible schema documentation and data lineage artifacts for the persistent deployment database.
* **Files**: <div style="margin-left: 40px;">
Step 07.1 `WAID_DEPLOY_FILE`
Step 08.1 `WAID_DEPLOY_DIR/app.py`
Step 08.2 `WAID_DOCS_DIR/waid_dbt_models.md`

* **Tables**: <div style="margin-left: 40px;"> 
Step 07.1 `public_forecasts` (and remote `Supabase datasets`)
---

## About main scripts

### `boot.py`

Central bootstrap and runtime initialization module for the WAID pipeline. It manages:

- Global configuration and environment variables, including nested expansion and .env fallback generation.
- Early-stage logging configuration using Loguru.
- System execution exit codes through WaidExit.
- Database credentials through the DBCredentials dataclass.
- Configuration validation through BaseConfig, BootSettings, WaidSettings, and WaidBoot.
- Provisioning of connection parameters, directory paths, feature mappings, and operational thresholds for external analytical and storage targets, such as Supabase PostgreSQL and Ecowitt station feeds.

The module does not directly interact with physical database tables; instead, it acts as a configuration broker for the WAID pipeline.

### `waid_01_1_ingest_ecowitt.py`

Automated Python ingestion script that downloads raw weather observations directly from an Ecowitt station gateway web server via HTTP. It manages:

- Preliminary gateway availability checks through check_url_exists(url, timeout) before downloading data.
- Target timeframe evaluation through the --period CLI parameter, distinguishing historical closed months from the active current month.
- Idempotent processing by skipping completed historical files (.full) to avoid redundant downloads and unnecessary network traffic.
- Monthly raw data downloads using urllib, with explicit network timeout handling.
- Download validation through a minimum file size threshold (MIN_SIZE_BYTES = 100) before replacing existing target files.
- Atomic file updates by downloading data to temporary .download files and renaming them only after successful validation.
- Network fault tolerance through explicit timeout handling and URLError / TimeoutError exception management, including cleanup of temporary files after failures.
- Runtime initialization through WaidBoot, CLI argument parsing, custom - WError exception handling, and standardized process exit status codes.

The script is designed to be idempotent, fault-tolerant, and safe for downstream ETL processing, preventing incomplete or corrupted downloads from being consumed as valid input.

### `waid_01_2_ingest_era5.py`
Python script designed to download and consolidate atmospheric reanalysis data from the Copernicus Climate Data Store (CDS). It extracts NetCDF matrices aligned with UTC timestamp standards and targeted geographic coordinates for integration into the WAID pipeline. It manages:

- **Configuration & Environment Setup:**
    - Injects custom configuration paths into the Python execution environment using `WAID_SOURCE`.
    - Instantiates system context and validates credentials via `WaidBoot`.
    - Validates command-line arguments including target month (--period), coordinates (--lat, --lon), and elevation (--elevation).
- **CDS API Operations:**
    - Connects to Copernicus CDS using cdsapi.Client with dynamic API URL and key configuration.
    - Generates a 0.5° Bounding Box centered around target coordinates.
    - Retrieves hourly single-level reanalysis parameters (*2m_temperature, 2m_dewpoint_temperature, surface_pressure, 10m_u_component_of_wind, 10m_v_component_of_wind, surface_solar_radiation_downwards, total_precipitation, geopotential*).
- **Data Stream Processing & Merging:**
    - Detects and handles server-side multi-file ZIP encapsulation.
    - Merges disparate NetCDF file streams using xarray.merge into a single consolidated NetCDF file.
    - Evaluates dataset completeness against total calendar days in the month to finalize full month archives (.full).
- **Caching & Resilience:**
    - Skips execution if a verified full-month file is already present.
    - Cleans up temporary extraction directories and partial files on error.
    - Gracefully handles server-side data unavailability without breaking downstream execution pipelines.

This script serves as the primary atmospheric data ingestion component, ensuring synchronized meteorological reanalysis matrices are available for downstream telemetry matching and processing.

### `waid_01_3_profile_era5.py`  
Python profiling and validation script for ERA5 NetCDF reanalysis files within the WAID pipeline. It inspects dataset structures, validates coordinate boundaries, performs data quality checks on extracted localized time series, and logs statistical summaries. It manages:

* **Environment & Argument Parsing**:
    * Injects configuration dependencies via `WAID_SOURCE` and validates target periods using `validate_period`.
    * Configures command-line argument parsing for `--period` in `YYYY-MM` format.
* **Dataset Inspection & Metadata Extraction**:
    * Evaluates file availability across standard `.nc` or finalized `.full` NetCDF dataset paths.
    * Extracts dimensions and inspects variable attributes including variable names, measurement units, and long names.
    * Validates latitude and longitude ranges against target coordinates defined in `.env` (`env.ecowitt_latitude`, `env.ecowitt_longitude`).
* **Data Quality & Point Extraction**:
    * Selects nearest spatial grid points based on station coordinates using `xarray.Dataset.sel`.
    * Converts multi-variable dataset slices into a Pandas `DataFrame`.
    * Performs NaN count checks to detect missing data or potential corruption.
* **Statistical Profiling & Latency Tracking**:
    * Generates basic summary statistics (`min`, `max`, `mean`) and prints sample data previews.
    * Calculates time lag in days between current time and the most recent valid observation for partial month files.

This script acts as a data quality assurance component, verifying structural integrity and detecting completeness or corruption in ERA5 NetCDF files before downstream ingestion.

### `waid_02_1_sync_ecowitt.py`
Python batch aggregation script designed to parse, normalize, and sync local Ecowitt weather station CSV data into a central SQLite database. It handles local timezone conversion to UTC, guarantees database schema integrity, and performs idempotent batch upserts. It manages:
* **Schema Validation & Database Setup**:
    * Initializes the destination SQLite table dynamically based on configuration variables (`env.ecowitt_table` and `env.waid_db`).
    * Maps raw CSV header names to standardized SQLite database column names.
    * Enforces primary key constraints on standard ISO timestamp strings and Unix epoch numerical values.
* **Timezone Normalization & Parsing**:
    * Parses naive local timestamp strings and localizes them using the configured system timezone (`env.tz_timezone`).
    * Converts localized local time series directly to standardized UTC datetime representations (`YYYY-MM-DD HH:MM:SS`) and Unix epoch timestamps.
    * Handles time transitions and invalid local date strings by dropping `NaT` instances.
* **File System Ingestion & Staging**:
    * Selects between standard `.csv` files for active current-month syncs and finalized `.full` files for historical periods.
    * Stages parsed telemetry records temporarily in a dedicated SQLite staging table (`staging_ecowitt`).
* **Data Synchronization & Upserts**:
    * Filters and matches DataFrame column structures against active database target schemas.
    * Performs idempotent batch upserts using `INSERT OR IGNORE` queries to prevent duplicate records.
    * Cleans up temporary staging tables upon completion or execution failure.

This script serves as the primary weather station telemetry ingestion component, standardizing disparate raw local telemetry into a persistent relational SQLite store for pipeline integration.

### `waid_03_1_match_datasets.py`
Python synchronization and alignment script that merges station telemetry with ERA5 atmospheric reanalysis data into a central Feature Store. It resamples local station measurements to hourly intervals, extracts grid data from NetCDF files, and performs a left-join to decouple station telemetry freshness from ERA5 latency. It manages:

* **Feature Store Table Initialization**:
    * Verifies and creates the target match table (`env.ml_matches_table`) in the SQLite database (`env.waid_db`) with defined schemas for station and ERA5 parameters.
* **ERA5 Data Extraction & Parameter Calculation**:
    * Extracts target coordinate grid time series from ERA5 NetCDF files (`.nc` or `.full`) using `xarray.Dataset.sel`.
    * Converts physical units including temperature from Kelvin to Celsius (`t2m`, `d2m`), pressure to hPa (`sp`), solar radiation to W/m² (`ssrd`), and total precipitation to mm (`tp`).
    * Derives relative humidity (`rh_era5`) using the Magnus-Tetens formula via `calculate_rh`.
    * Computes wind speed magnitude from vector components (`u10`, `v10`).
* **Telemetry Resampling & Left-Join Alignment**:
    * Queries station telemetry using `fetch_and_resample_ecowitt` for specified monthly time ranges.
    * Aligns timestamps to standardized hourly intervals and performs a left-join (`df_match`) between station telemetry and ERA5 reanalysis data.
    * Populates ERA5 benchmark fields with `NaN` when ERA5 files are unavailable.
* **Bias Calculation & Checkpoint Persistence**:
    * Computes mean measurement biases (`bias_temp`, `bias_pres`, `bias_rh`, `bias_wind`, `bias_solar`, `bias_rain`) when running in debug mode.
    * Exports aligned monthly datasets as CSV checkpoints to `env.ml_matches_dir`.
    * Clears overlapping historical date ranges and performs batch inserts (`INSERT OR REPLACE`) into the SQLite Feature Store.

This script serves as the primary data transformation and alignment engine, unifying raw station telemetry and reanalysis data into a feature table for downstream machine learning and analytics.

### `waid_04_1_setup_specs.py`
Python setup script designed to initialize, profile, and persist empirical sensor specifications into the station metadata storage. It analyzes recent station telemetry to derive physical resolution and deadband thresholds for primary features, falling back to predefined hardware specifications when data is insufficient. It manages:

* **Database Schema Maintenance**:
    * Inspects `station_metadata` table columns via `PRAGMA table_info`.
    * Executes an `ALTER TABLE` query to add the `sensor_specs` column when missing.
* **Empirical Sensor Profiling**:
    * Queries raw telemetry records from `ecowitt_records` for a 14-day trailing window.
    * Calculates physical resolution metrics based on non-zero delta percentiles (`np.percentile`) across target feature fields.
    * Estimates custom operational deadbands for specific sensor types, such as minimum thresholds for wind speed and tip sensitivity for rainfall.
* **Default Specifications & Persistence**:
    * Provides default hardware specification structures (`resolution`, `deadband`) for core features (`ecowitt_temp`, `ecowitt_rh`, `ecowitt_pres`, `ecowitt_wind`, `ecowitt_solar`, `ecowitt_rain`).
    * Serializes calculated or default sensor specification mappings into JSON format.
    * Updates the `station_metadata` table for the active station ID (`env.ecowitt_station_id`) with serialized specifications.

This script acts as a hardware profiling component, supplying empirical sensor resolution limits and operational noise thresholds required by downstream data processing and modeling tasks.


### `waid_05_1_ml_tensors.py`

Python pre-processing module responsible for extracting local weather telemetry from SQLite and assembling 3D feature tensors (X) and target delta tensors (Y) for training multi-step weather nowcasting machine learning models. It manages:

- Local weather observations from the stg_ecowitt SQLite table.
- Telemetry loading through load_ecowitt_telemetry(env, period), including monthly filtering, lookback_hours buffering across month boundaries, and explicit datetime typing.
- Cyclical temporal feature generation through compute_temporal_embeddings(df), using sine/cosine embeddings for hour of day and day of year.
- Sliding-window generation through generate_sliding_window_tensors(env, df, lookback, forecast).
- Input tensor (X) generation as a 3D matrix with shape (samples, lookback, 10), combining 6 weather metrics with 4 cyclical time embeddings.
- Target delta tensor (Y) generation as a 3D matrix with shape (samples, forecast, 6), representing feature changes over the forecast horizon.
- Serialization of generated arrays and timestamps to disk using joblib:
X_raw_YYYY_MM.pkl
Y_raw_YYYY_MM.pkl
timestamps_YYYY_MM.pkl
- Resource cleanup and exception handling through try...finally blocks for SQLite connections and clean handling of custom WError exceptions.

The module preserves training-window continuity at monthly boundaries through the lookback buffer and uses cyclical temporal encoding to avoid artificial discontinuities between consecutive time periods.

### `waid_05_2_ml_train.py`

Machine learning training pipeline designed for local weather nowcasting. It ingests multi-period 3D tensors, enriches the input features with solar-physics domain knowledge, trains a Keras LSTM model, and manages model artifact versioning through SQLite. It manages:

- Station telemetry from the stg_ecowitt SQLite table, used to align physical variables and calculate theoretical solar radiation.
- Model versioning and metadata through the ml_model_registry SQLite table, including training timestamps, MSE loss metrics, active status, and paths to saved Keras models and joblib scalers.
- Station-specific training configuration from the station_metadata SQLite table, including the min_training_days retraining interval.
- Physics-informed feature engineering in train_model(...), calculating theoretical clear-sky solar radiation from station latitude and longitude and adding it as an input feature.
- Incremental fitting of StandardScaler instances across all available training periods, with the resulting scaling artifacts persisted to disk.
- Memory-efficient tf.data.Dataset pipelines with batch size 32, shuffling, prefetching with AUTOTUNE, and an 80/20 training-validation split.
- LSTM model construction using an Input → LSTM(64) → Dropout(0.2) → Dense → Reshape architecture with EarlyStopping.
- Retraining eligibility checks through check_retrain_required(...), enforcing the configured minimum interval since the last active training session.
- Model registration through register_trained_model(...), deactivating the previous active model and storing the new version, metrics, and artifact paths in ml_model_registry.
- Safe model rollouts with fallback handling and atomic SQLite updates to ensure that previous model versions remain available until the new model is successfully registered.

The pipeline combines memory-efficient training, physics-informed feature engineering, automated MLOps tracking, and retraining guardrails to provide reproducible and controlled model updates.

### `waid_06_1_inference_forecast.py`

Live inference engine for the WAID machine learning system. It reads recent station observations, constructs normalized feature tensors, generates multi-step forecasts with the trained LSTM model, applies physical safety constraints, and persists predictions and reconciliation metrics to SQLite. It manages:

- Active model and scaler artifacts from the ml_model_registry SQLite table through load_active_model_artifacts(env).
- Ground-truth observations and historical bias parameters from match_records and int_matches_bias.
- Forecast persistence through the inference_forecast SQLite table, including predicted meteorological values, input window lineage, observation deltas, and bias drift metrics.
- Recent telemetry retrieval through fetch_recent_telemetry(env), using fetch_and_resample_ecowitt to map raw sensor measurements to internal model features.
- Inference tensor construction through build_inference_tensor(env, df_raw), including cyclical time embeddings and theoretical clear-sky solar radiation features.
- Multi-step forecast generation using the active trained LSTM model and previously fitted StandardScaler artifacts.
- Prediction persistence and reconciliation through persist_and_update_inference_forecast(...), including retroactive updates when corresponding ground-truth observations become available.
- Physical safety constraints through the shared apply_physics_guardrails(...) function, preventing non-physical outputs such as negative rainfall or solar radiation exceeding astronomical limits.
- Dynamic delta-to-absolute reconstruction, adding predicted target deltas to the latest observed station state to maintain continuous forecast trajectories.
- Timezone-aware forecast horizon generation, with datetime values aligned to the appropriate boundaries and serialized as standard UTC timestamps.
- Automated reconciliation of historical forecasts with missing observation differences, updating bias and drift metrics as new station observations become available.

The inference pipeline combines physics-aware prediction constraints, continuous forecast reconstruction, model artifact management, and automated post-hoc reconciliation to maintain reliable and traceable live forecasts.

### `waid_06_4_inference_quality.py`

Lightweight validation and quality verification script within the WAID inference pipeline. It validates the structural availability and population of the inference quality benchmark generated by upstream dbt models. It manages:

- Read-only connection to the active SQLite database defined by env.waid_db.
- Simulated execution timestamps through the --mock-now CLI argument.
- Structural validation of the inference_quality table or view by querying SQLite's sqlite_master metadata.
- Verification that the inference_quality entity has been successfully created by the upstream dbt transformation pipeline.
- Retrieval and validation of the total number of benchmark records available for forecast quality analysis.

The script provides a lightweight post-inference validation layer, ensuring that the forecast quality benchmark is structurally available and populated before subsequent pipeline stages consume it.

### `waid_07_1_export_deploy_db.py`

ETL (Extract, Transform, Load) exporter responsible for extracting weather forecast predictions, historical bias indicators, and quality metrics from the internal lab database and publishing them to external deployment environments. It manages:

- Data extraction and reconciliation by joining inference_forecast with inference_quality on the composite key (timestamp, model_version).
- Export of meteorological predictions, feature differentials, historical bias baselines, drift measurements, ERA5 reanalysis references, and absolute errors for temperature, humidity, pressure, wind, rainfall, and solar radiation.
- Local SQLite deployment by populating the public deployment database (deploy_db_file) and the public_forecasts table.
- Automatic creation of the idx_public_forecasts_ts_model composite index on (timestamp, model_version) to optimize public queries and dashboard response times.
- Cloud deployment synchronization through export_to_supabase when env.deploy_mode == "cloud".
- Dynamic PostgreSQL schema validation and creation through SQLAlchemy and the postgresql+psycopg2 connection driver.
- Replacement and indexing of the public_forecasts PostgreSQL table in the target Supabase deployment environment.

The script provides the data publication layer between the internal WAID lab environment and the public deployment infrastructure, supporting both lightweight local SQLite deployments and cloud-based Supabase PostgreSQL deployments.

### `waid_08_1_viz_streamlit_app.py`

Interactive visualization application and automated deployment packager built with Streamlit and Plotly. It serves as the primary analytics dashboard for the WAID platform, enabling operators and users to evaluate model forecasts against local Ecowitt observations and ECMWF ERA5 reanalysis data. It manages:

- Analytics data from the public_forecasts database view/table, including model predictions, ground-truth observations, historical bias metrics, and absolute errors.
- Deployment status detection through get_deployment_status(), checking whether the localized deploy/ package exists and whether its assets are up to date.
- Automated deployment packaging through run_deployment_setup(env), generating the required deployment structure, standalone requirements.txt, execution wrapper app.py, and bundled SQLite databases.
- Dynamic data access through load_public_data(), supporting both deployment modes:
    - Cloud mode: connects to Supabase PostgreSQL through SQLAlchemy using non-pooling connections.
    - Local mode: queries the local SQLite database from cached paths.
- Interactive dashboard construction through run_dashboard(env), including multiple tabs, timezone-normalized timestamps, daily selectors, metric cards for MAE, Bias, and Drift, and Plotly time-series comparisons across all six weather features.
- Timezone-safe data processing, converting UTC timestamps to the appropriate local timezone for visualization and analysis.
- Physical data validation and bounding, including non-negative wind, rainfall, and solar radiation values and relative

### `waid_08_2_doc_dbt_deploy.py`

Automated documentation pipeline and Markdown report generator for the WAID dbt project. It detects changes in dbt model definitions, generates updated dbt documentation artifacts, and converts the resulting metadata into a structured Markdown document. It manages:

- Incremental change detection through calculate_models_hash(dbt_dir), computing a cumulative MD5 hash across all .sql and .yml files in the dbt models directory.
- Cached documentation generation by skipping dbt docs generate when no model definition changes are detected.
- dbt documentation compilation through the dbt CLI, producing the project manifest.json.
- Automated metadata extraction through extract_and_generate_markdown(manifest_path, output_file), parsing model schemas, descriptions, and column data types from manifest.json.
- Generation of the human-readable waid_dbt_models.md documentation file.
- Documentation validation through check_and_complete(), ensuring that the generated Markdown artifact exists and providing commands for launching a local HTTP server for browser-based previews.
- Environment initialization through WaidBoot, dynamically resolving project paths and executable locations.
- End-to-end orchestration through main(), coordinating change detection, dbt documentation generation, metadata extraction, and artifact creation.

The pipeline provides incremental documentation builds and automated metadata extraction, avoiding unnecessary dbt documentation generation while keeping the Markdown documentation synchronized with the current dbt model definitions.

### `waid_shared.py`

Core utility and data-processing module for the WAID platform. It centralizes shared functionality for physical constraints, sensor calibration, solar radiation modelling, telemetry processing, and station metadata management across the machine learning lifecycle. It manages:

- Theoretical solar radiation calculations through calculate_theoretical_solar_radiation(...), computing clear-sky solar radiation in W/m² from solar declination, hour angles, and station coordinates.
- Timezone-safe solar calculations by normalizing input timestamps to UTC and preventing Daylight Saving Time (DST) distortions.
- Ecowitt telemetry retrieval and resampling through fetch_and_resample_ecowitt(...), querying raw station observations from SQLite and converting them into synchronized time intervals.
- Time-series aggregation using hourly averages for temperature, pressure, humidity, solar radiation, and wind, and maximum hourly totals for rainfall.
- Bounded time-based interpolation, limited by the configured max_interpolate_hours threshold.
- Station metadata retrieval through get_station_metadata(...), including elevation, minimum training constraints, retraining windows, and sensor hardware specifications from the station_metadata SQLite table.
- Physical safety enforcement through apply_physics_guardrails(...), including theoretical clear-sky limits for solar radiation and non-negative constraints for applicable weather parameters.
- Sensor-specific calibration through hardware sensitivity thresholds, deadbands, and measurement resolution specifications.
- Period range generation through generate_period_range(begin_period, end_period), producing sequential YYYY-MM ranges for time-series iteration and historical backfilling.

The module acts as the shared processing and domain-logic layer for the WAID platform, ensuring consistent telemetry handling, physical validation, sensor calibration, and metadata access across ingestion, training, inference, and visualization workflows.

```python
import numpy as np
from boot import WaidBoot
from waid_shared import (
    fetch_and_resample_ecowitt,
    get_station_metadata,
    apply_physics_guardrails,
    calculate_theoretical_solar_radiation
)

# 1. Initialize environment configuration
env = WaidBoot()

# 2. Retrieve station metadata and sensor specs from SQLite DB
station_id, name, elevation, min_days, retrain_days, sensor_specs = get_station_metadata(env)

# 3. Fetch and resample raw sensor data for a specific time window
df_clean = fetch_and_resample_ecowitt(
    env=env,
    start_date="2026-01-01 00:00:00",
    end_date="2026-01-07 23:59:59"
)

# 4. Compute theoretical solar radiation for physics validation
timestamps = df_clean["timestamp"].values
solar_theoretical = calculate_theoretical_solar_radiation(
    timestamps=timestamps,
    lat=env.ecowitt_latitude,
    lon=env.ecowitt_longitude,
    local_tz=env.tz_timezone
)

# 5. Apply physical guardrails and sensor deadbands to single features
raw_wind_data = df_clean["wind_m_s"].to_numpy()
cleaned_wind_data = apply_physics_guardrails(
    data=raw_wind_data,
    feature="wind",
    sensor_specs=sensor_specs
)
```

### `waid_prefect_manager.py`

Operational lifecycle manager for Prefect execution in production environments. It automates Prefect infrastructure bootstrapping, deployment registration, initial flow execution, and worker process monitoring. It manages:

- Prefect server health checks through ensure_prefect_server, querying the local Prefect API health endpoint and automatically starting an unbuffered background server process when the server is inactive.
- Work pool initialization through ensure_work_pool, ensuring that the required Prefect process work pool exists and is available for execution, with default-agent-pool as the default pool.
- Dynamic deployment manifest generation through generate_prefect_yaml, creating a runtime-specific prefect.yaml based on parameters such as the target YYYY-MM period, --skip-ingestion, and --auto-backfill.
- Deployment registration through run_deployment, invoking prefect deploy --all to register scheduled flows with the Prefect server.
- Immediate initial execution through trigger_initial_run, launching a flow run after deployment registration to avoid waiting for the first scheduled execution.
- Worker process management through start_worker, launching a Prefect worker with the configured work pool to poll and execute queued flow runs.
- Resilient process and subprocess management while preserving the existing CLI arguments, control structures, and execution logic.
- Standardized English-language logging and comments across the Prefect lifecycle operations.
- Complete English Doxygen/PEP-257-style docstrings for the module's management functions.

The module provides the **Prefect infrastructure management layer** for the WAID platform and works in synergy with **waid_orchestrate.py**: **waid_prefect_manager.py** manages the Prefect runtime infrastructure and deployments, while **waid_orchestrate.py** coordinates the execution of the underlying WAID pipeline tasks and sub-flows.

### `waid_orchestrate.py`

**Prefect-based orchestration module** responsible for coordinating the WAID pipeline through modular tasks and sub-flows. It manages:

- Modular execution of pipeline tasks and sub-flows through Prefect.
- Invocation of Python scripts through subprocess calls while preserving the existing execution flow, CLI arguments, and control structures.
- Validation and resolution of Python script paths before execution.
- Execution logging and error reporting across the different pipeline stages.
- Historical data processing through the automated backfill workflow, including the AUTO-BACKFILL execution path.
- Standardized task and sub-flow documentation through English Doxygen/PEP-257-style docstrings.
- Consistent English-language logging and error messages across orchestration tasks.

The module acts as the central workflow orchestration layer for the WAID platform, coordinating the execution of individual processing scripts while keeping the underlying pipeline logic modular and unchanged.

### `waid_scheduler_lab.py`

Long-running operational daemon and retroactive simulation driver for the WAID pipeline. It coordinates scheduled execution loops and multi-period historical simulations by managing environment contexts and invoking waid_orchestrate_lab.py. It manages:

- Initial environment validation through check_initial_setup_needed, verifying the presence of the waid_db SQLite database.
- Automated historical backfill during first-time initialization when no existing database environment is detected.
- Pipeline subprocess execution through run_pipeline, launching waid_orchestrate_lab.py in the appropriate backfill or incremental execution mode.
- Historical time simulation through the WAID_MOCK_NOW environment variable, allowing retrospective and step-by-step execution without modifying the host operating system clock.
- Retroactive simulation mode through --retroactive, iterating through historical timestamp intervals defined by --mock-begin and --mock-end.
- Incremental simulation execution at each historical step using --skip-ingestion-deploy.
- Final publication after retroactive simulation through waid_08_1_viz_streamlit_app.
- Continuous operational execution through a recurring loop based on env.scheduled_interval_sec, running incremental updates and ML forecasts and sleeping between scheduled executions.

The module provides the central execution layer of the **WAID platform**, coordinating all pipeline stages from raw data ingestion through machine learning, forecast evaluation, visualization, and documentation. It is designed to work in conjunction with `waid_scheduler_lab.py`, which controls scheduled and retroactive execution cycles.

This lightweight orchestration stack is specifically intended for edge deployments on resource-constrained devices, where the Prefect-based orchestration layer may introduce excessive memory overhead. **By relying on direct subprocess execution and a lightweight scheduling loop, it provides a more resource-efficient alternative for running the complete WAID pipeline on embedded or low-resource hardware**. For more information about the ARM-compatible Docker version and its deployment on resource-constrained edge devices, see the **ARM Docker Deployment section**.

### `waid_orchestrate_lab.py`

Central pipeline execution engine and orchestrator for the WAID system. It coordinates end-to-end data processing, dbt transformations, feature engineering, machine learning training and inference, and dashboard data deployment. It manages:

- Pipeline execution through PipelineRunner, encapsulating subprocess execution for Python scripts and dbt commands.
- Automatic injection of dbt operational variables, including bias thresholds for temperature, pressure, relative humidity, wind, solar radiation, and rainfall, together with the appropriate dbt profile configuration.
- Centralized process logging through Loguru, including raw log filtering, ANSI color sequence removal, and formatted output streams.
- Simulated execution through the WAID_MOCK_NOW environment variable, enabling deterministic historical pipeline execution without modifying the host system clock.
- Environment reset and execution regimes:
    - Regime 0 — Standard: Executes the pipeline without purging the existing environment state.
    - Regime 1 — Soft Reset: Creates a lightweight backup and removes compiled SQLite databases and ML models while preserving raw ingested data.
    - Regime 2 — Hard Reset: Creates a compressed ZIP archive of the data directory and completely purges raw data, databases, and build artifacts.
- Step 00 — dbt Setup: Cleans the dbt environment, resolves dependencies, compiles the project, and exports shared dbt configuration variables through waid_00_1 to waid_00_4.
- Steps 01–04 — Data Ingestion & Matching: Ingests Ecowitt and ERA5 NetCDF telemetry, stages records through dbt, performs temporal matching, and calculates operational sensor biases through models such as stg_ecowitt and int_matches_bias.
- Steps 05–07 — Machine Learning & Inference: Generates ML feature tensors, trains model baselines, evaluates 6-hour forecast quality, and exports production database snapshots.
- Step 08 — Visualization & Documentation: Deploys Streamlit analytics data packages and generates automated Markdown data dictionaries.

The module provides the central execution layer of the WAID platform, coordinating all pipeline stages from raw data ingestion through machine learning, forecast evaluation, visualization, and documentation. It is designed to work in conjunction with waid_scheduler_lab.py, which controls scheduled and retroactive execution cycles.

### `sources.yml`

dbt source configuration file that registers and documents external raw database tables populated by upstream ingestion mechanisms, such as Python pipelines. It manages:

- Raw Ecowitt weather observations from external_raw.ecowitt_records, including temperature, humidity, pressure, wind, and rain sensor measurements.
- Synchronized Ecowitt and ERA5 observations from external_raw.match_records, providing paired hourly ground-truth and reanalysis metrics.
- Individual ML inference runs from external_raw.inference_records, including emission timestamps, active time windows, and model version metadata.
- Forecast outputs from external_raw.inference_forecast, including target forecast timestamps and associated model versions.
- Explicit column data types using standard types such as INTEGER, REAL, TEXT, and DATETIME.
- Data integrity checks through dbt not_null tests on critical fields such as timestamp and model_version.
- Source declarations using dbt schema version 2 and the external_raw source namespace.

### `inference_quality.sql`

Incremental dbt model designed to evaluate ML forecast accuracy by reconciling model predictions, ground-truth weather observations, and ERA5 reanalysis data. It manages:

- Raw ML predictions from external_raw.inference_forecast, including clipping of non-physical values such as negative solar radiation and rainfall.
- Incremental processing using a 3-day lookback buffer relative to the target table (this), while respecting mock timestamp constraints (waid_mock_now / WAID_MOCK_NOW).
- Ground-truth weather observations from ref('stg_ecowitt').
ERA5 reanalysis data from ref('int_matches_bias'), used as an external benchmark.
- Timestamp-based reconciliation across predictions, station observations, and ERA5 data.
- Prediction error calculation against ground-truth observations using deltas (prediction - actual).
- Absolute error calculation against the ERA5 benchmark using ABS(pred - era5).
- Percentage error calculation against ERA5, safely handling zero benchmark values with NULLIF.

### `inference_stats.sql`

Incremental dbt transformation model designed to compute consensus metrics and forecast uncertainty across machine learning weather predictions. It manages:

- Raw prediction runs from source('external_raw', 'inference_forecast').
- Grouping of inference runs by model_version and prediction timestamp.
- Calculation of n_votes, representing the number of inference runs contributing to each target timestamp.
- Calculation of consensus_* metrics using mean predictions for temperature, pressure, relative humidity, wind speed, solar radiation, and rainfall.
- Calculation of std_* metrics using population standard deviation to quantify forecast variance and uncertainty.
- Incremental processing using incremental_strategy='merge', with timestamp as the unique_key and an index on the destination table.
- Filtering of incremental runs to process only records with a timestamp greater than the current maximum timestamp in {{ this }}.
- Graceful handling of the first incremental execution using coalesce with a fallback timestamp of 1970-01-01 00:00:00.
- Portable standard deviation calculations using the algebraic formula SQRT(AVG(X²) - AVG(X)²), avoiding database-specific aggregate functions.

The model requires upstream raw forecasts to be available in external_raw.inference_forecast before execution.

### `start.sh`

Production launcher and container management interface for the WAID pipeline on Linux/WSL environments. It manages:

- Environment initialization by verifying and loading variables from config/boot.env into the execution context using source.
- Docker Compose orchestration through docker compose -f docker/prod/docker-compose.yml.
- Production container lifecycle operations, including starting services in the background, shutting down the stack, and streaming service logs in real time.
- Prefect flow execution by default, bringing up the production stack responsible for scheduled and triggered workflow pipelines.
- Strict execution safety through set -e, ensuring that the script terminates immediately when a command fails.
- Command-line argument handling through a case statement, supporting the available execution modes and options.
- User guidance through the show_usage help menu, displayed for --help requests or unrecognized arguments.

The script provides a single, safe command-line interface for initializing the environment and managing the production WAID container stack.

### `start-lab.sh`

Centralized orchestration launcher and command-line entry point for running WAID pipeline components in Linux and WSL environments. It supports both direct local execution and containerized Docker Compose deployments. It manages:

- Local pipeline execution through the pipeline command, triggering a single execution pass of waid_orchestrate_lab.py.
- Continuous scheduling and simulation through the scheduler command, launching waid_scheduler_lab.py.
- Local dashboard execution through the dashboard command, starting the Streamlit application from src/waid_08_1_viz_streamlit_app.py.
- Docker-based execution through the docker/lab/docker-compose.yml and override.yml configurations.
- Edge container profile through docker-edge, starting and streaming logs from the waid-lab-orchestrator container.
- Prefect container profile through docker-prefect, cleaning temporary locks and starting the waid-lab-prefect workflow orchestration container.
- Prefect environment cleanup through clean-prefect, removing SQLite lock/WAL state files and temporary Prefect files from the container workspace.
- Complete Docker environment shutdown through down, stopping and removing running containers across the Edge, ARM, and Prefect profiles and cleaning up orphaned containers.

The script provides a unified command-line interface for local, Edge/ARM, and Prefect-based WAID execution, allowing operators to switch between lightweight resource-constrained deployments and the full Prefect orchestration environment.


### `start-arm.sh`
This is a shell script designed for bootstrapping and initializing host volume permissions for the WAID pipeline running on ARM architecture. It prepares the local environment, starts the required Docker Compose services, and manages container-level file permissions. It manages:

- Environment Initialization:
    - Resolves current host runtime identity by exporting `WAID_UID` and `WAID_GID` variables.
    - Navigates automatically to the project root directory.
- Host Volume Setup:
    - Verifies and creates necessary host directory structures for Docker bind mounts (data, logs, config, deploy, dbt/target, dbt/logs).
- Container Service Orchestration:
    - Launches containerized services in detached mode using 
    `docker compose -f docker/arm/docker-compose.yml up -d.`
- Permissions Alignment:
    - Executes an idempotent permission alignment command as root inside the waid-arm container to set `chown -R and chmod -R 775` on /app/dbt, ensuring proper workspace execution rights for host user mapping.

**This script acts as the entrypoint bootstrap utility for launching and synchronizing the environment permissions of the ARM-based Docker deployment.**

---

## Pipeline Execution Log

All WAID logs are available in the logs directory at the root of the project.

Logs are generated on a daily basis and follow the naming convention waid_pipeline_YYYYMMDD.log (e.g. waid_pipeline_20260827.log).

To enable debug mode, set the WAID_LOG_LEVEL environment variable to DEBUG. Otherwise, the default log level is INFO.

```log
2026-09-07 12:50:59.190 | INFO     | waid_orchestrate_lab.py:run_command:109 | 🔶 Step [5, 2]
2026-09-07 12:50:59.190 | INFO     | waid_orchestrate_lab.py:run_command:111 | Request from: waid_05_2_ml_train
2026-09-07 12:50:59.190 | DEBUG    | waid_orchestrate_lab.py:run_command:112 | python /home/alex/af/github_projects/lab/waid-draft/src/waid_05_2_ml_train.py
2026-09-07 12:50:59.190 | INFO     | waid_orchestrate_lab.py:run_command:115 | [MOCK MODE] Running with WAID_MOCK_NOW=2026-09-07 06:00:00
2026-09-07 12:50:59.898 | WARNING  | waid_orchestrate_lab.py:run_command:175 | WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
2026-09-07 12:51:03.428 | WARNING  | waid_orchestrate_lab.py:run_command:175 | WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
2026-09-07 12:51:06.641 | INFO     | waid_orchestrate_lab.py:run_command:175 | --- Booting module context: waid_05_2_ml_train.py ---
2026-09-07 12:51:06.695 | DEBUG    | waid_orchestrate_lab.py:run_command:175 | Try to process Streamlit secrets...
2026-09-07 12:51:06.709 | DEBUG    | waid_orchestrate_lab.py:run_command:175 | Not running under Streamlit or no secrets found...
2026-09-07 12:51:06.767 | DEBUG    | waid_orchestrate_lab.py:run_command:175 | [CONFIG_FALLBACK] WAID_SETUP_MODE is missing or empty. Using default fallback: 0
2026-09-07 12:51:06.985 | DEBUG    | waid_orchestrate_lab.py:run_command:175 | WAID_VERSION = '1.0.0' (configuration source: waid.env)
```
---

# WAID Architecture Notes: Edge Deployment & Target State

As the project evolves toward edge-native execution on standalone boards, the underlying target management and deployment strategy must remain flexible.
# WAID Docker Build Usage

The Docker build script supports target-specific configuration, allowing the build process to switch between development (host) and production (board) environments seamlessly.

## Usage Commands

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

It automates the end-to-end packaging, cross-compilation, network transfer, and remote deployment of the WAID platform to an ARM-based target device. It handles local environment validation, database optimization, Docker ARM64 image building, artifact bundling, SCP transfer, and remote container orchestration via SSH.

**Usage:**
```
./docker/arm/deploy-arm.sh
```
---

## Edge Deployment Readiness

1. **Resource Efficiency:** By maintaining lightweight dbt execution profiles (`threads: 1`) and SQLite-backed local persistence, the system minimizes resource overhead required for edge nodes.
2. **Deterministic State Playback:** Utilizing `--mock-now` and retroactive simulation features allows developers to validate edge performance against historical datasets locally before deploying binaries or scripts to physical hardware targets.