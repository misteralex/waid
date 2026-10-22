# WAID: Functional Requirements & Integration Test Architecture

This document outlines the core functional requirements, the comprehensive integration test suite, security protocols, and CI/CD validation pipelines for the WAID edge microclimate forecasting framework. It maps high-level project goals directly to the modular script architecture implemented in the repository.

---

## 1. Executive Summary & Testing Manifesto

The WAID Quality Assurance framework adheres to enterprise-grade software engineering standards, ensuring absolute transparency, maintainability, and open-source contribution readiness. The core tenets of our testing infrastructure include:
* **Automated Execution:** All test suites are structured as modular, executable scripts runnable via pytest and local orchestrators.
* **Public CI/CD Integration:** Automated validation pipelines running on GitHub Actions for pull requests, commits, and branch merges.
* **Local Developer Experience:** Clear instructions and script isolation allowing developers to execute targeted subsets or the full suite locally.
* **Code Coverage Reporting:** Integration with coverage tools (`pytest-cov`) to continuously measure test metrics across pipelines.
* **Requirement Traceability:** Strict mapping between core functional specifications and individual test tags (`T...` / `M...`).
* **Defect & Feature Policy:** Mandatory test-driven bug fixing and feature implementation protocols to prevent regressions.

---

## 2. Functional Requirements (FR)

Derived from end-to-end system specifications and domain-specific meteorological constraints, the core functional requirements of the pipeline are structured as follows:

### FR-01: Asynchronous Ingestion & Multi-Source Synchronization
* **Description:** The system must asynchronously ingest high-frequency local meteorological telemetry (edge sensors via HTTP/mock) and global reanalysis data (Copernicus ERA5 NetCDF), natively handling temporal latency offsets (e.g., a 5-day ERA5 delay) and fusing them into a unified, continuous UTC time-series dataset without gaps.
* **Mapped Implementation Scripts:**
`test_waid_01_1_ingest_ecowitt.py`, `test_waid_01_2_ingest_era5.py`,
`test_waid_01_3_profile_era5.py`, `test_waid_02_1_dbt_sync.py`,
`test_waid_02_2_sync_ecowitt.py`, `test_waid_03_1_match_datasets.py`

### FR-02: Physics-Informed Data Contracts & Guardrails
* **Description:** Data ingestion and transformation layers must enforce domain-specific physical laws rather than syntax-only checks. Any physical violation (e.g., negative solar radiation during nighttime, negative precipitation rates, relative humidity outside the $0-100\%$ range) must be intercepted, corrected, or filtered prior to downstream processing.
* **Mapped Implementation Scripts:** `test_waid_04_1_dbt_setup_metadata.py`, `test_waid_04_2_setup_specs.py`, `test_waid_shared.py`

### FR-03: Deterministic Thermodynamic Modeling via dbt
* **Description:** Validated raw data must be processed through an analytical transformation chain managed by dbt, calculating deterministic, traceable, and reproducible key microclimatic derived parameters (**Vapor Pressure Deficit - VPD**, **Dew Point**, **Enthalpy**, and **Temperature-Humidity Index - THI**).
* **Mapped Implementation Scripts:** `waid_03_2_dbt_matches_datasets.py`, `waid_03_3_dbt_matches_bias.py`, `test_waid_08_2_doc_dbt_deploy.py`

### FR-04: Incremental Persistence, Cloud Sync & Predictive Inference
* **Description:** The system must periodically execute predictive machine learning models (6-hour LSTM nowcasting) and perform incremental database writes to local storage (SQLite) and cloud infrastructure (Supabase), safely handling cloud disconnections and comparing inferences against subsequent real observations.
* **Mapped Implementation Scripts:**
`test_waid_05_1_ml_tensors.py`, `test_waid_05_2_ml_train.py`, `test_waid_05_3_ml_sanity_check.py`, `test_waid_06_1_inference_forecast.py`, `test_waid_06_2_dbt_inference_stats.py`, `test_waid_06_3_dbt_inference_quality.py`, `test_waid_06_4_inference_quality.py`, `test_waid_07_1_export_deploy_db.py`, `test_waid_08_1_viz_streamlit_app.py`

---

## 3. Master Test Matrix & Traceability Tags

| Test ID | Module / Component Name | Status | Implementation Script / Path |
| :--- | :--- | :--- | :--- |
| **T011** | Ecowitt Ingestion & Download | Implemented | `test_waid_01_1_download_ecowitt.py` |
| **T012** | ERA5 NetCDF Download | Implemented | `test_waid_01_2_download_era5.py` |
| **T013** | ERA5 NetCDF Profiling | Implemented | `test_waid_01_3_profile_era5.py` |
| **T021** | Database initialization and full dbt setup | Implemented | `test_waid_02_1_sync_dbt.py` |
| **T022** | Ecowitt Temporal Synchronization | Implemented | `test_waid_02_2_sync_ecowitt.py` |
| **T023** | Executes and tests dbt staging models for Ecowitt | Implemented | `test_waid_02_3_dbt_staging_ecowitt.py` |
| **T024** | Ecowitt Statistics Synchronization | Planned | `test_waid_02_4_sync_ecowitt_statitics.py` |
| **T025** | ERA5 Statistics Synchronization | Planned | `test_waid_02_5_sync_era5_statitics.py` |
| **T031** | Multi-Source Dataset Matching | Implemented | `test_waid_03_1_match_datasets.py` |
| **T032** | Runs and tests matched datasets in dbt | Implemented | `test_waid_03_2_dbt_matches_datasets.py` |
| **T033** | Computes observation vs model bias metrics via dbt | Implemented | `est_waid_03_3_dbt_matches_bias.py` |
| **T041** | Builds station metadata tables and generates feature specs | Implemented | `test_waid_04_1_dbt_setup_metadata.py` |
| **T042** | Setup Specs & Physics Guardrails (`apply_physics_guardrails`) | Implemented | `test_waid_04_2_setup_specs.py` |
| **T051** | ML Historical Tensor Shaping & Scaling | Implemented | `test_waid_05_1_ml_tensors.py` |
| **T052** | LSTM Baseline Model Training | Implemented | `test_waid_05_2_ml_train.py` |
| **T053** | ML Sanity Check & Loss Stability | Implemented | `test_waid_05_3_ml_sanity_check.py` |
| **T061** | Nowcasting Inference Execution | Implemented | `test_waid_06_1_inference_forecast.py` |
| **T062** | Inference dbt Feature Preparation | Implemented | `test_waid_06_2_dbt_inference_stats.py` |
| **T063** | Inference dbt Statistical Metrics (`inference_stats`) | Implemented | `test_waid_06_3_dbt_inference_quality.py` |
| **T064** | Inference Quality & Delta vs Actuals | Implemented | `test_waid_06_4_inference_quality.py` |
| **T071** | Incremental Database Persistence (SQLite) | Implemented | `test_waid_07_1_export_deploy_db.py` |
| **T072** | Supabase Cloud Connectivity & Fallback Test | Planned / Sandbox | `test_waid_07_2_supabase_resilience.py` |
| **T073** | Secrets Scanning & Dependency Vulnerability Check | Planned / Security | `test_waid_07_3_security_audit.py` |
| **T081** | Streamlit Dashboard Integration & Viz | Implemented | `test_waid_08_1_viz_streamlit_app.py` |
| **T082** | dbt Deployment & Compilation Check | Implemented | `test_waid_08_2_doc_dbt_deploy.py` |
| **T091** | System Orchestrator | Implemented | `test_waid_orchestrate.py`, `test_waid_orchestrate_lab.py` |
| **T092** | Scheduler | Implemented | `test_waid_scheduler_lab.py` |
| **T093** | Bias Analysis & Timestamp Debug Utilities | Implemented | `test_waid_debug_analyze_bias.py`, `test_waid_debug_timestamps.py` |
| **T094** | Shared functions | Implemented | `test_waid_shared.py` |
| **M010** | Dedicated Ecowitt Station Mock Server | Pending / Roadmap | `waid/mock/waid_ecowitt_server.py` |
| **M020** | ERA5 NetCDF Streamer Provider | Pending / Roadmap | `waid/mock/waid_era5_provider.py` |
| **M030** | Scenario & Anomaly Generator | Pending / Roadmap | `waid/mock/waid_scenario_generator.py` |

---

## 4. Functional Traceability & Test Specifications

#### 1. Ingestion, Profiling & Synchronization (FR-01)

* T011 | test_waid_01_1_download_ecowitt.py
  - @param mock_http_client: Mocked HTTP session for local telemetry endpoints.
  - @return bool: Assertion status for raw Ecowitt payload extraction.
  - Description: Validates asynchronous fetching of high-frequency local sensor JSON payloads, handling network timeouts and verifying UTC timestamp formatting.

* T012 | test_waid_01_2_download_era5.py
  - @param mock_cds_client: Mocked Copernicus CDS client.
  - @return bool: Assertion status for NetCDF file download integrity.
  - Description: Tests global reanalysis data retrieval and NetCDF extraction while handling the ~5-day ERA5 publishing delay.

* T013 | test_waid_01_3_profile_era5.py
  - @param sample_netcdf_path: Path to sample ERA5 NetCDF test fixture.
  - @return bool: Assertion status for spatial and temporal profiling.
  - Description: Analyzes grid boundaries, spatial bounding boxes, and temporal resolution profiles of reanalysis datasets.

* T021 | test_waid_02_1_sync_dbt.py
  - @param dbt_project_config: Target database connection dictionary.
  - @return bool: Assertion status for database initialization and dbt seed execution.
  - Description: Verifies local SQLite/Postgres schema creation and executes initial dbt seeds for static lookup tables.

* T022 | test_waid_02_2_sync_ecowitt.py
  - @param raw_ecowitt_df: Raw station payload DataFrame.
  - @return bool: Assertion status for deduplication and UTC alignment.
  - Description: Validates deduplication, time series continuity, and column normalization for local station telemetry.

* T023 | test_waid_02_3_dbt_staging_ecowitt.py
  - @param staged_model_output: Compiled execution output for stg_ecowitt.
  - @return bool: Assertion status for schema compliance.
  - Description: Tests dbt model compilation and execution for Ecowitt staging views.

* T024 | test_waid_02_4_sync_ecowitt_statitics.py (Planned)
  - @param ecowitt_history_df: Historical station telemetry DataFrame.
  - @return bool: Assertion status for statistical boundary calculations.
  - Description: Tests periodic computation of empirical hardware resolution limits, deadbands, and moving statistical baselines for Ecowitt telemetry.

* T025 | test_waid_02_5_sync_era5_statitics.py (Planned)
  - @param era5_history_df: Historical ERA5 reanalysis DataFrame.
  - @return bool: Assertion status for reanalysis distributional stats.
  - Description: Computes long-term statistical metrics, percentile distributions, and climatological normals for ERA5 grid cells.

* T031 | test_waid_03_1_match_datasets.py
  - @param ecowitt_ts_df: High-frequency local time series.
  - @param era5_ts_df: Low-frequency reanalysis time series.
  - @return bool: Assertion status for seamless multi-source fusion.
  - Description: Fuses local telemetry with delayed reanalysis grids into a continuous UTC dataset without temporal gaps.

----------------------------------------------------------------------------------------------------

#### 2. Physics Guardrails, Metadata & dbt Modeling (FR-02 & FR-03)

* T032 | test_waid_03_2_dbt_matches_datasets.py
  - @param matched_model_results: Output from combined dataset dbt models.
  - @return bool: Assertion status for relational join integrity.
  - Description: Tests dbt models responsible for aligning station observations directly against spatially nearest ERA5 grid points.

* T033 | test_waid_03_3_dbt_matches_bias.py
  - @param bias_metrics_df: Calculated residual metrics DataFrame.
  - @return bool: Assertion status for statistical bias evaluation.
  - Description: Computes residual distributions and systematic offsets between local station readings and reanalysis benchmarks.

* T041 | test_waid_04_1_dbt_setup_metadata.py
  - @param metadata_catalog: Schema metadata dictionary.
  - @return bool: Assertion status for catalog integrity.
  - Description: Builds station metadata models and generates target feature specifications inside dbt.

* T042 | test_waid_04_2_setup_specs.py
  - @param telemetry_record: Input sensor telemetry dictionary.
  - @return bool: Assertion status for physical contract enforcement.
  - Description: Enforces domain-specific physical laws, filtering/correcting negative nighttime solar radiation, negative rainfall, and invalid relative humidity (RH outside [0, 100%]).

----------------------------------------------------------------------------------------------------

#### 3. Machine Learning & Predictive Inference (FR-04)

* T051 | test_waid_05_1_ml_tensors.py
  - @param processed_features_df: Cleaned thermodynamic feature set.
  - @return bool: Assertion status for sliding-window tensor shapes.
  - Description: Validates sequence windowing, scaling routines (StandardScaler), and 3D tensor formatting for 6-hour LSTM inference.

* T052 | test_waid_05_2_ml_train.py
  - @param model_inputs: Tuple of training features (X) and targets (y).
  - @return bool: Assertion status for model convergence and artifact saving.
  - Description: Tests training loops for LSTM microclimate models, verifying loss reduction and weight persistence.

* T053 | test_waid_05_3_ml_sanity_check.py
  - @param trained_lstm_model: Instantiated Keras model artifact.
  - @return bool: Assertion status for physical prediction bounds.
  - Description: Runs sanity checks on model predictions to prevent non-physical outputs (e.g., extreme temperature spikes).

* T061 | test_waid_06_1_inference_forecast.py
  - @param latest_tensor_batch: Recent telemetry tensor batch.
  - @return bool: Assertion status for 6-hour nowcast execution.
  - Description: Executes batch prediction pipelines and formats raw model outputs into structured time-series predictions.

* T062 | test_waid_06_2_dbt_inference_stats.py
  - @param raw_predictions_df: Raw prediction log.
  - @return bool: Assertion status for dbt feature preparation.
  - Description: Prepares inference outputs for downstream dbt feature modeling and derived parameter calculations.

* T063 | test_waid_06_3_dbt_inference_quality.py
  - @param quality_metrics_table: Evaluation metrics result set.
  - @return bool: Assertion status for dbt quality test passes.
  - Description: Executes dbt data tests evaluating forecast error distributions (RMSE, MAE, bias bounds).

* T064 | test_waid_06_4_inference_quality.py
  - @param prediction_log_df: Historical forecast log DataFrame.
  - @param actual_observation_df: Subsequent real Ecowitt observation DataFrame.
  - @return bool: Assertion status for delta residual calculations.
  - Description: Evaluates prediction accuracy by calculating deltas between 6-hour predictions and real subsequent station observations.

----------------------------------------------------------------------------------------------------

#### 4. Persistence, Cloud Resilience & Security (FR-04)

* T071 | test_waid_07_1_export_deploy_db.py
  - @param sqlite_connection: Active SQLite database handle.
  - @return bool: Assertion status for incremental persistence.
  - Description: Executes incremental updates to SQLite databases, updating prediction records with real observations without overwriting prediction history.

* T072 | test_waid_07_2_supabase_resilience.py (Planned / Sandbox)
  - @param mock_supabase_client: Mocked Supabase connection with injected network drops.
  - @return bool: Assertion status for offline queuing and retry success.
  - Description: Tests Cloud sync resilience, validating offline local buffering and automatic replay upon network recovery.

* T073 | test_waid_07_3_security_audit.py (Planned / Security)
  - @param codebase_path: Root repository directory path.
  - @return bool: Assertion status for zero hardcoded credentials and vulnerability pass.
  - Description: Scans scripts, configs, and dbt profiles for hardcoded tokens, API keys, or vulnerable dependencies.

----------------------------------------------------------------------------------------------------

#### 5. Visualization, Orchestration, Scheduling & Debug Utilities

* T081 | test_waid_08_1_viz_streamlit_app.py
  - @param streamlit_session_state: Mocked Streamlit session state.
  - @return bool: Assertion status for visual element rendering.
  - Description: Validates Streamlit dashboard component rendering, interactive filters, and chart formatting.

* T082 | test_waid_08_2_doc_dbt_deploy.py
  - @param manifest_json: Compiled dbt manifest JSON artifact.
  - @return bool: Assertion status for documentation compile success.
  - Description: Verifies automated dbt documentation compilation and static deployment staging.

* T091 | test_waid_orchestrate.py / test_waid_orchestrate_lab.py
  - @param pipeline_config: Execution parameters dictionary.
  - @return bool: Assertion status for end-to-end execution.
  - Description: End-to-end integration test executing the complete pipeline lifecycle from ingestion through inference.

* T092 | test_waid_scheduler_lab.py
  - @param loop_controller: Synchronous loop controller context.
  - @return bool: Assertion status for synchronous iteration and keep-alive ping execution.
  - Description: Tests synchronous execution loop scheduling, ensuring keep-alive pings (ping_streamlit) run directly within the main loop without periodic timer threads.

* T093 | test_waid_debug_analyze_bias.py / test_waid_debug_timestamps.py
  - @param diagnostic_logs: Path to execution log files.
  - @return bool: Assertion status for diagnostic metric extraction.
  - Description: Utility diagnostic test suite for inspecting feature bias anomalies and verifying timestamp timezone alignments across UTC layers.

* T094 | test_waid_shared.py
  - @param shared_module: Imported waid_shared utility library.
  - @return bool: Assertion status for thermodynamic equations.
  - Description: Direct unit testing of shared thermodynamic calculations (VPD, Dew Point, Enthalpy, THI) and central system utility functions.

#### 6. Roadmap Mock Servers & Simulation Infrastructure (M010 - M030)

* M010 | waid/mock/waid_ecowitt_server.py (Pending / Roadmap)
  - @param mock_port: Local network port for server binding.
  - @return HTTPServer: Running local HTTP server instance.
  - Description: Dedicated local mock server simulating live Ecowitt station HTTP pushes for edge testing without external network dependencies.

* M020 | waid/mock/waid_era5_provider.py (Pending / Roadmap)
  - @param netcdf_template: Synthetic NetCDF template dataset.
  - @return Streamer: Mock NetCDF streamer interface.
  - Description: Simulates Copernicus CDS API behavior by streaming synthetic ERA5 NetCDF chunks with configurable latency.

* M030 | waid/mock/waid_scenario_generator.py (Pending / Roadmap)
  - @param scenario_type: String identifier for anomaly type (e.g., sensor_drift, spike, outage).
  - @return DataFrame: Injected anomaly telemetry dataset.
  - Description: Synthetic data generator that injects hardware faults, extreme weather events, or communication drops to stress-test physical guardrails and resilience.

----------------------------------------------------------------------------------------------------

## 5. Integration & Functional Test Suite

1. Ingestion & Temporal Alignment Test (Ecowitt + ERA5) [T011 - T031]
   - Description: Validates multi-source asynchronous data ingestion from high-frequency local telemetry 
     (Ecowitt) and global reanalysis grids (Copernicus ERA5 NetCDF). Verifies proper temporal alignment 
     and zero-gap continuous UTC time-series generation despite the inherent ~5-day ERA5 publishing delay.
   - Mapped Test IDs: T011, T012, T013, T021, T022, T023, T031

2. Scenario Override & Hierarchical Fallback Test [M010 - M030]
   - Description: Evaluates mock data provisioning and simulation providers. Ensures that active testing 
     environments prioritize specific scenario override folders, gracefully falling back to default 
     fixtures located in 'waid/mock/data' when specific edge cases are not specified.
   - Mapped Component IDs: M010, M020, M030

3. Deterministic dbt Transformation Test [T032, T033, T062, T063, T082]
   - Description: Ensures that validated raw telemetry records passing through dbt analytical models 
     deterministically compute traceable and reproducible microclimatic derived parameters (Vapor Pressure 
     Deficit - VPD, Dew Point, Enthalpy, and Temperature-Humidity Index - THI).
   - Mapped Test IDs: T032, T033, T062, T063, T082

4. LSTM Baseline Training Simulation Test [T051 - T053]
   - Description: Validates sliding-window sequence construction, feature scaling via StandardScaler, 
     and model convergence stability during training for 6-hour LSTM microclimate nowcasting.
   - Mapped Test IDs: T051, T052, T053

5. Incremental Inference & Dashboard Update Test [T061, T064, T071, T081]
   - Description: Tests real-time 6-hour nowcast generation, execution of incremental database writes 
     (SQLite/Supabase), and Streamlit app rendering. Ensures that prediction tables incrementally update 
     records with real subsequent Ecowitt observations to calculate error deltas without overwriting 
     historical prediction outputs.
   - Mapped Test IDs: T061, T064, T071, T081

6. Fault Tolerance & Resilience Test [T072, T091, T092, T093]
   - Description: Assesses system performance and edge behavior under fault conditions (e.g., corrupted 
     NetCDF files, HTTP endpoint timeouts, cloud connection drops). Verifies offline buffering, 
     graceful exception handling, structured error logging, and synchronous retry loops.
   - Mapped Test IDs: T072, T091, T092, T093

7. Data Contracts & Physics Guardrails Test [T041, T042, T094]
   - Description: Enforces domain-specific physical laws and hardware guardrails prior to downstream processing. 
     Intercepts, corrects, or filters physical anomalies including:
     * Nighttime solar radiation zeroing ($G_{solar} = 0 \text{ W/m}^2$ when $h_{solar} \le 0$)
     * Non-negative precipitation rates ($P \ge 0 \text{ mm/h}$)
     * Relative humidity physical bounds ($RH \in [0, 100\%]$)
     * Thermodynamic consistency constraint ($T_{dew} \le T_{ambient}$)
   - Mapped Test IDs: T041, T042, T094

---

## 6. Security, Secrets Management & Supabase Integration (`T072`, `T073`)
* **Credential Isolation:** Strict enforcement of environment-based configuration (`.env`). Hardcoded secrets (`SUPABASE_URL`, `SUPABASE_KEY`) are prohibited and caught by automated audits.
* **Cloud Resiliency & Fallback (`T072`):** If Supabase experiences timeouts or connection drops during incremental persistence, the system catches exceptions and defaults to local SQLite buffering without service interruption.
* **Dependency Vulnerability Scanning (`T073`):** Automated checks on third-party packages to detect known CVEs prior to merging code changes.

---

## 7. Regression Testing & Defect Prevention Protocol
* **Zero Silent Fixes:** Every critical bug must first be reproduced via a targeted test case before patching production code.
* **Permanent Traceability:** Regression tests are permanently mapped to their respective Traceability Tags (`T...`) and run automatically in the test suite.

---

## 8. Continuous Integration (CI) & Automated Validation
* **PR / Commit Triggers:** Fast unit tests, physics guardrail checks (`T041`), and dbt compilation dry-runs.
* **Main Branch / Scheduled Triggers:** Full integration suite, LSTM training sanity checks (`T052`), and persistence validation.
* **Hardware Environment Mirroring:** Execution within Docker containers utilizing `/tmp` tmpfs configurations to mirror ARM/Raspberry Pi storage constraints.

---

## 9. Quality Assurance (QA) & Testing Taxonomy

To ensure open-source maintainability, contribution readiness, and production-grade reliability, the WAID testing framework is structured across seven core QA pillars:

1. **Unit Tests:** Granular validation of core individual functions (e.g., mathematical formulas, tensor shapes, and parsing routines).
2. **Integration Tests:** Verification of interactions between major components (e.g., Ecowitt/ERA5 ingestion matching, dbt analytical models, and SQLite/Supabase synchronization).
3. **End-to-End (E2E) Tests:** Simulation of critical user workflows from raw data ingestion and ML nowcasting down to the live Streamlit dashboard updates.
4. **Regression Tests:** Persistent test cases mapped to identified bugs and previously implemented features to prevent backsliding.
5. **Automated CI/CD Execution:** Continuous integration pipelines triggering fast unit/guardrail checks on pull requests and full integration suites on scheduled merges.
6. **Security & Vulnerability Testing:** Automated dependency scanning and strict environment-based secrets management (`.env`, Supabase credential isolation).
7. **Test Documentation & Guidelines:** Comprehensive traceability matrices (`docs/testing_and_requirements.md`) and contribution guidelines designed to empower the open-source community.