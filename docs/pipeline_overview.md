## WAID (Weather AI Direct Nowcasting) Pipeline Architecture & Execution Flow

The orchestration chain follows a modular, end-to-end data engineering and machine learning lifecycle. It moves sequentially through ingestion, transformation, bias analysis, model training, inference, and visualization.

**1. Data Ingestion & Profiling (Extraction & Catalog)**

* **Execution:** `waid_01_1_ingest_ecowitt` $\rightarrow$ `waid_01_2_ingest_era5` $\rightarrow$ `waid_01_3_profile_era5`
* **Purpose:** Ingests raw observational feeds from local station data (Ecowitt) and reanalysis weather sources (ERA5). Generates initial data profiling and schema validation before downstream processing.

**2. Data Transformation, Alignment & Bias Analysis**

* **Execution:** `waid_02_1_sync_ecowitt` $\rightarrow$ `waid_02_2_dbt_clean_ecowitt` $\rightarrow$ `waid_03_1_match_datasets` $\rightarrow$ `waid_03_2_dbt_matches` $\rightarrow$ `waid_03_3_dbt_matches_bias`  $\rightarrow$ `waid_04_1_setup_metadata`
* **Purpose:** Synchronizes timestamps and handles data cleaning using dbt transformations. Spatially/temporally matches ERA5 and Ecowitt datasets, executes dbt models to derive statistical bias metrics between predicted/reanalysis data and ground truth, runs diagnostic utility checks (`waid_analyze_bias`), and registers dataset metadata specs.

**3. Machine Learning Pipeline & Inference Engine**

* **Execution:** `waid_05_1_ml_tensors` $\rightarrow$ `waid_05_2_ml_train` $\rightarrow$ `waid_06_1_inference_engine` $\rightarrow$ `waid_06_2_inference_stats` $\rightarrow$ `waid_06_3_inference_prediction` $\rightarrow$ `waid_06_4_dbt_inference_quality` $\rightarrow$ `waid_06_5_inference_quality` $\rightarrow$ `waid_07_1_inference_forecast`
* **Purpose:** Formats cleaned feature tables into multi-dimensional tensors for PyTorch/ML frameworks. Trains the baseline ML model (`05_2`), executes batch inference (`06_1`), and evaluates prediction quality using both dbt models and Python scoring scripts (`06_4`, `06_5`) before generating final forecast outputs (`07_1`).

**4. Deployment & Visualization**

* **Execution:** `waid_07_2_export_deploy_db` $\rightarrow$ `waid_08_1_viz_streamlit_update` $\rightarrow$ `waid_08_2_viz_streamlit_app`
* **Purpose:** Exports the processed metrics, forecasts, and predictions into a lightweight deployment database. Triggers an update to the visualization state and launches the Streamlit dashboard UI for user interaction.

---

### Pipeline Execution Summary Table

| Phase | Main Modules | Key Responsibility |
| --- | --- | --- |
| **Ingest & Profile** | `waid_01_*` | Raw data extraction (Ecowitt & ERA5) and data catalog profiling. |
| **Transform & Align** | `waid_02_*`, `waid_03_*`, `waid_04_*` | Timestamp sync, dbt cleaning, dataset matching, and bias metric evaluation. |
| **ML & Inference** | `waid_05_*`, `waid_06_*`, `waid_07_1` | Tensor creation, model training, inference evaluation, and forecasting. |
| **Deploy & Viz** | `waid_07_2`, `waid_08_*` | DB export, Streamlit cache updates, and UI dashboard delivery. |
---

## Pipeline Execution Log

```log
[2026-08-18 12:00:10] [INFO] Initializing pipeline context... platform set to 'board'.
[2026-08-18 12:00:11] [INFO] Step 1: Data Ingestion (Extraction) started. Source: raw_weather_feed.
[2026-08-18 12:00:15] [INFO] Step 2: Data Discovery & Profiling (Catalog) executed successfully.
[2026-08-18 12:00:20] [INFO] Step 3: Synchronization & Data Alignment (Transform) - dbt run completed.
[2026-08-18 12:00:25] [INFO] Step 4: Performance Metrics & Bias Study (Analyze/Benchmark) initiated.
[2026-08-18 12:00:28] [WARN] Guardrail check: Bias metric deviation within acceptable threshold (Delta < 0.05).
[2026-08-18 12:00:30] [INFO] Step 5: Baseline Model Training (Machine Learning) started on board target.
[2026-08-18 12:00:45] [INFO] Step 6: Reporting & Visualization (Load/Viz) completed. Pipeline status: SUCCESS.
```
---

# WAID Architecture Notes: Edge Deployment & Target State

As the project evolves toward edge-native execution on standalone boards, the underlying target management and deployment strategy must remain flexible.
# WAID Docker Build Usage

The Docker build script supports target-specific configuration, allowing the build process to switch between development (host) and production (board) environments seamlessly.

## Usage Commands

### 1. Build for Host (Default)
Standard build for local development on Linux/WSL environments.
```bash
./build-docker.sh --target host
```

### 2. Build for Edge Board
Targeted build optimized for deployment on edge hardware.
```bash
./build-docker.sh --target board
```

## Options Summary
| Flag | Description |
| :--- | :--- |
| `--target` | Specifies the build platform (`host` or `board`). |

## Edge Deployment Readiness

1. **Resource Efficiency:** By maintaining lightweight dbt execution profiles (`threads: 1`) and SQLite-backed local persistence, the system minimizes resource overhead required for edge nodes.
2. **Deterministic State Playback:** Utilizing `--mock-now` and retroactive simulation features allows developers to validate edge performance against historical datasets locally before deploying binaries or scripts to physical hardware targets.