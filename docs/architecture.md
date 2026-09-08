## Global Architecture

**WAID (Weather AI Direct Nowcasting)** is an end-to-end, edge-native data engineering framework designed to process local telemetry (Ecowitt) alongside satellite/reanalysis data, delivering physics-constrained 6-hour nowcasting via LSTM models.

**WAID** is designed as a **portable, multi-environment weather forecasting platform**. The same core pipeline can run on a conventional PC/server or on a resource-constrained ARM Edge device, while the resulting data can be consumed either locally or through a remote cloud deployment.

The architecture separates **data processing, machine learning, orchestration, storage, and visualization**, allowing the platform to adapt to different operational environments without changing the underlying forecasting pipeline.

```text
              ┌────────────────────────────────────────────────────────────────────────┐
              │                        WAID ARCHITECTURE FLOW                          │
              └────────────────────────────────────────────────────────────────────────┘

              [ INPUT DATA ]
              ├── Ecowitt Station Telemetry (Real-Time)
              ├── ERA5 Reanalysis / Satellite Data
              └── Deterministic Solar Physics Signal ───┐
              (Timestamp + Lat/Lon + Day of Year)       │
                                                        ▼
                                          ┌────────────────────────────┐
                                          │    TENSOR CONSTRUCT        │
                                          └──────────────┬─────────────┘
                                                         │
                                                         ▼
                                          ┌────────────────────────────┐
                                          │    6-HOUR LSTM MODEL       │
                                          └──────────────┬─────────────┘
                                                         │
                                                         ▼
              [ EDGE EXECUTION ] ◄───────────────────────┘
              ├── ARM64 Board (Lightweight Daemon: waid_scheduler_lab)
              └── Local SQLite Buffer (Fault-Tolerant)
                                                        │
                                                        ▼ (ETL Sync)
              [ CLOUD STORAGE ]
              └── Supabase PostgreSQL Warehouse (prod schema)
                                                        │
                                                        ▼
              [ ANALYTICS & RECONCILIATION ]
              ├── Streamlit Live Dashboard (waid-analytics.streamlit.app)
              └── Error Analysis Loop (MAE, Bias, Sensor Drift vs ERA5)
```

## Why the Future of Weather Forecasting Isn't in the Cloud: Lessons from the WAID Project

**Introduction: The Microclimate Gap**

Global weather models, such as the **ERA5** reanalysis dataset, provide an indispensable foundation for modern atmospheric science. However, from an engineering perspective, these high-level models frequently struggle with the "microclimate gap." They operate at spatial resolutions that inherently fail to capture the hyper-local environmental nuances of a specific backyard or a complex urban canyon. When the objective is precise, immediate forecasting, relying solely on massive, centralized global datasets results in a disconnect between macroscopic atmospheric trends and the ground truth of localized telemetry.

**WAID** project was architected as a solution to bridge this gap. Functioning as an edge-native data engineering framework, WAID reconciles high-level satellite and reanalysis data with real-time telemetry from local weather stations (**Ecowitt**). This approach shifts the focus from broad simulations to high-fidelity, localized "nowcasting."

**As a Cloud-Native Architect and Applied AI researcher, I view **WAID** as a specialized intersection of data engineering and physics. Rather than treating weather as a purely statistical problem for machine learning to solve, the system integrates deterministic physical laws with Long Short-Term Memory (LSTM) networks. This hybrid approach grounds the AI in the immediate reality of local telemetry while respecting the immutable laws of the physical world.**

## Stop Teaching AI Things We Already Know (Deterministic Physics)

A common inefficiency in machine learning is forcing a model to "learn" patterns from historical data that are already mathematically certain. In atmospheric modeling, the astronomical day/night cycle is a predictable physical constant. **WAID optimizes the inference process by injecting "Deterministic Solar Physics" directly into the pipeline.**

Instead of requiring the LSTM to deduce solar radiation patterns from noisy historical observations—a process that increases variance and requires significant computational overhead—the system dynamically calculates a theoretical solar-radiation signal at the moment of inference. This signal is injected directly into the inference tensor alongside meteorological and temporal features. The calculation is derived from four deterministic constants: timestamp, day of the year, station latitude, and station longitude.

**"The objective is to inject a known physical structure into a data-driven forecasting system while keeping the edge implementation lightweight and deterministic."**

By providing this deterministic representation of the solar cycle across the forecast horizon, we reduce the burden on the model. It no longer needs to "learn" that there is no solar radiation at midnight; instead, its computational resources are reserved for modeling the non-linear, stochastic atmospheric variables that truly require deep learning.

For a detailed technical breakdown of the mathematical background and physical tensor implementation, consult the case study: [**WAID Case Study: Integrating Solar-Radiation Physics into Edge Weather Nowcasting**](https://github.com/misteralex/waid/blob/main/docs/waid_case_study_integrating_solar_radiation.md)

## The "Edge-Native" Advantage

For short-term nowcasting, local observations serve as the ultimate ground truth. While global reanalysis data and satellite imagery provide critical context, real-time telemetry from local hardware (Ecowitt) captures immediate shifts—such as a sudden pressure drop or a micro-burst of wind—that global models simply cannot resolve in time.

The WAID architecture prioritizes this local data to refine forecasts within a tight 6-hour nowcasting window. To maintain high-fidelity responsiveness at the edge, the system processes inputs through a structured, synchronized pipeline:

By executing this sequence locally, the system ensures that the "ground truth" remains the primary driver of the prediction, allowing the model to adapt to the specific microclimate in real-time.

## Orchestration Without the Bloat

A significant challenge in edge-native engineering is the hardware constraint of ARM64 platforms. Traditional, heavyweight orchestration stacks often introduce unnecessary overhead, consuming the limited CPU and memory cycles required for inference.

To solve for this, WAID utilizes a "dual execution model" tailored to the specific environment:

* **Prefect**: Utilized for laboratory environments and cloud-based pipelines where high-level orchestration and visibility are beneficial.
* **waid_scheduler_lab**: A lightweight operational daemon designed specifically for low-power local execution on ARM64 edge nodes.

This flexibility is further supported by three distinct deployment modes: Local Bare-Metal PC for prototyping and model experimentation, Containerized x86_64 for scalable cloud pipelines, and the ARM64 Edge Board for production deployments. This "lean execution" principle proves that sophisticated AI does not require bloated infrastructure to deliver enterprise-grade reliability at the edge.

## The Continuous Feedback Loop as a Reality Check

To remain technically viable, an AI system must be held accountable to real-world outcomes. WAID is not a static ML experiment; it is a live, evolving system where every forecast is eventually reconciled against the actual incoming observations.

**"WAID is not a static ML experiment. The pipeline runs continuously, with live station telemetry feeding the system and predictions being reconciled against incoming observations in a continuous feedback loop."**

This loop follows a precise sequence: Observation ➔ Inference ➔ Forecast ➔ Real-World Observation ➔ Error Analysis. By maintaining this cycle, the system can dynamically monitor for:

* Mean Absolute Error (MAE): Quantifying prediction accuracy over time.
* Historical Bias: Detecting consistent over- or under-prediction of variables.
* Sensor Drift: Identifying potential hardware degradation at the station level.
* ERA5 Baselines: Benchmarking edge performance against global model standards to validate the "edge-native" value proposition.

## Decoupling for Reliability and Scale

Architecting for the edge requires a strategy for network volatility. WAID employs a decoupled architecture that separates local operational execution from long-term analytics using a mechanism of Hybrid Synchronization.

Operational execution remains local to the edge, utilizing SQLite for local buffering. This ensures that the core forecasting function remains operational even during network interruptions. Verified production datasets are then synchronized via ETL into a remote PostgreSQL warehouse (Supabase). This separation of concerns is illustrated by the following data flow:

This decoupling ensures that the public-facing Streamlit dashboard remains high-performing and scalable, powered by the warehouse rather than taxing the limited resources of the ARM64 edge nodes.

---

### Key Data Engineering & Architectural insights behind the platform:

- **Flexible Deployment Targets** (Multi-Environment Data Routing):
WAID supports 3 distinct deployment modes.
- **Hybrid Ingestion & Synchronization Pipeline**:
Dealing with heterogeneous temporal resolutions and sensor latency required a robust staging strategy — integrating automated NetCDF ingest (Copernicus CDS API) with local station CSV telemetry using UTC normalization and bounded interpolation.
- **Edge-Optimized Orchestration**:
Running heavy orchestration stacks on ARM hardware introduces unnecessary overhead. WAID solves this by implementing a dual execution model: Prefect for lab/cloud pipelines, and a custom, lightweight operational daemon (waid_scheduler_lab) for ARM edge nodes.
- **Live Reconciled Inference & Metrics**:
Inference isn't just about outputting predictions; it's about tracking drift. The pipeline dynamically updates past forecasts with live incoming telemetry to continually benchmark MAE, historical bias, and sensor drift against ERA5 baselines.
- **Isolated Data Products for Dissemination**:
To ensure high availability and mobile stability, operational outputs are extracted via an ETL pipeline to an isolated production database, serving a Streamlit dashboard with full responsive rendering.
---

### Deployment Modes

 WAID supports 3 distinct deployment modes:

 - **Host / Local mode (`WAID_DEPLOY_MODE=local`)**\
   The complete pipeline runs directly on a PC or server host and stores its generated data in a local SQLite database. The local Streamlit application reads this database directly, providing a self-contained deployment suitable for development, testing, standalone installations, or environments without cloud connectivity.
- **Host / Cloud mode (`WAID_DEPLOY_MODE=cloud`)**\
   The pipeline still runs on a PC or server host, but the resulting public forecast data is exported to a remote PostgreSQL/Supabase database. The Streamlit Community Cloud application accesses the remotely published dataset, allowing forecasts to be exposed through a public web dashboard without requiring the processing host itself to be publicly accessible.
- **ARM Edge mode**\
   The complete pipeline can run on an ARM-based Edge device with limited CPU and memory resources. The Edge deployment can produce both **local data for on-device visualization** and **remote data for cloud-based dashboards**, allowing the system to operate autonomously while optionally publishing selected results to a remote environment.

### Orchestration Architecture

 WAID provides two orchestration strategies depending on the available computing resources:

 - **Prefect orchestration** is intended for production deployments running on conventional PC/server infrastructure. It provides workflow scheduling, deployment management, worker execution, monitoring, and operational control.
- **Lightweight Edge orchestration** is used on ARM and other resource-constrained devices. Instead of running Prefect, which introduces additional memory and runtime overhead, the Edge deployment uses `waid_scheduler_lab.py` and `waid_orchestrate_lab.py` to provide a lightweight scheduling and subprocess-based execution layer.

 This separation allows the same processing pipeline to operate across both powerful host environments and low-resource Edge hardware without imposing the memory requirements of the full Prefect stack on Edge devices.

### Continuous and Retroactive Execution

 The pipeline supports both **forward operational execution** and **retroactive historical execution**.

 - In normal operation, the scheduler periodically executes the pipeline and updates the latest forecast according to the configured scheduling interval. The system is designed to support frequent forecast updates, with **6-hour forecasting representing the intended operational horizon and update cadence**.
- The **retroactive mode** allows the complete pipeline to be executed against historical periods prior to the current date. Through simulated timestamps such as `WAID_MOCK_NOW`, the system can reproduce the state of the pipeline at previous points in time without modifying the host operating system clock.

 Retroactive execution is particularly useful for **historical validation, model evaluation, backtesting, debugging, and reproducibility**.

### Externalized Configuration

 All relevant operational parameters are designed to be configurable independently from the Docker image. Configuration files and environment variables are provided through an **external volume mounted into the container**, allowing operators to change deployment parameters without rebuilding the Docker image.

 This approach separates:

 - **Application code and runtime dependencies**, packaged inside the Docker image.
- **Operational configuration**, maintained outside the image.
- **Persistent data and databases**, stored outside the ephemeral container filesystem.
- **Generated model and pipeline artifacts**, which can be persisted independently of container lifecycle.

 As a result, the same Docker image can be reused across different stations, environments, and deployment modes simply by changing the externally mounted configuration.

### End-to-End Data Flow

 At a high level, the architecture follows this processing chain:

```text
                            Weather Station / External Data
                                          │
                                          ▼
                                   Data Ingestion
                                          │
                                          ▼
                                   SQLite / Raw Data
                                          │
                                          ▼
                                 dbt Transformations
                                          │
                                          ▼
                               Matching & Bias Analysis
                                          │
                                          ▼
                                ML Feature Engineering
                                          │
                                          ▼
                                    Model Training
                                          │
                                          ▼
                                ML Inference / Forecast
                                          │
                                          ▼
                                  Forecast Evaluation
                                          │
                                          ▼
                                   Public Data Export
                                      ┌───┴────┐
                                      │        │
                                      ▼        ▼
                                   SQLite   PostgreSQL
                                   (Local)   (Cloud)
                                      │        │
                                      ▼        ▼
                            Local Streamlit   Streamlit Cloud
```

### Host vs. Edge Architecture

 The main architectural distinction is therefore the **execution environment rather than the forecasting logic**:

```text
                                    WAID Pipeline
                                           │
                            ┌──────────────┴──────────────┐
                            │                             │
                        Host / PC                     ARM Edge
                            │                             │
                      Prefect Stack              Lightweight Scheduler
                            │                             │
                            └──────────────┬──────────────┘
                                           │
                                   Same Core Pipeline
                                           │
                                  ┌────────┴────────┐
                                  │                 │
                                Local             Cloud
                                SQLite          PostgreSQL
                                  │                 │
                                  ▼                 ▼
                            Local Streamlit    Streamlit Cloud
```

 The architecture therefore supports a **single forecasting pipeline with multiple execution and publication strategies**, rather than maintaining separate application implementations for host and Edge environments.

### Operational Characteristics

 The overall design provides:

 - **Portability:** the same pipeline can run on PC/server and ARM Edge hardware.
- **Resource awareness:** Prefect is used where sufficient resources are available, while Edge deployments use a lightweight local orchestrator.
- **Local autonomy:** Edge devices can process and store forecasts locally without depending on continuous cloud connectivity.
- **Cloud publication:** forecast results can optionally be synchronized to a remote PostgreSQL/Supabase environment.
- **Flexible visualization:** the same forecast data can be consumed by a local Streamlit instance or a remote Streamlit Community Cloud dashboard.
- **Historical reproducibility:** retroactive execution enables deterministic replay of previous periods.
- **Externalized configuration:** operational parameters remain outside the Docker image and can be changed without rebuilding the application.
- **Persistent storage:** databases, model artifacts, logs, and generated data can survive container restarts and image updates.
- **Automated forecasting:** the scheduler continuously updates forecasts according to the configured execution interval, with a target **6-hour forecasting cycle**.
- **Modular processing:** ingestion, transformation, matching, ML, evaluation, export, visualization, and documentation remain independently executable pipeline stages.
- **Container portability:** Docker provides a consistent runtime environment across conventional hosts and ARM-based Edge systems.
- **Separation of concerns:** orchestration, computation, persistence, and visualization are decoupled, making the system easier to deploy and maintain.

 Overall, WAID is designed as a **hybrid Edge-to-Cloud forecasting architecture**: computation can remain close to the weather station when required, while forecast products can simultaneously remain available locally and be published remotely when connectivity and cloud services are available.

---

### Database Target & Execution Mode Architecture

The WAID platform uses a dual-tier configuration model to manage data persistence and dashboard rendering across development, staging, and production environments. This decoupling is governed by two key environment variables: `WAID_DB_SCHEMA_TARGET` and `WAID_DEPLOY_MODE`.
```text
                            ┌─────────────────────────────────────────┐
                            │          Streamlit Dashboard            │
                            └────────────────────┬────────────────────┘
                                                 │
                                   Is WAID_DEPLOY_MODE = cloud?
                                                 / \
                                          Yes /     \ No
                                          /         \
                                          ▼           ▼
                            ┌───────────────────┐       ┌───────────────────┐
                            │ Supabase Postgres │       │   SQLite Local    │
                            │   (Cloud Mode)    │       │   (Local Mode)    │
                            └─────────┬─────────┘       └───────────────────┘
                                   │
                     Target Schema (WAID_DB_SCHEMA_TARGET)
                     ┌───────────────┼───────────────┐
                     ▼               ▼               ▼
              ┌─────────┐     ┌─────────┐     ┌─────────┐
              │  draft  │     │  prod   │     │  retro  │
              └─────────┘     └─────────┘     └─────────┘
```
**1. Target Schema Selection (`WAID_DB_SCHEMA_TARGET`)**
The `WAID_DB_SCHEMA_TARGET` variable dictates the logical PostgreSQL schema target within Supabase where the ingestion, dbt models, and inference pipelines read and write data.

- **draft**: Used during local experiments, active development, and pipeline testing. Isolates unverified model outputs and data transformations from production tables.

- **prod**: The operational production schema. Houses production model inferences, verified station readings (ecowitt), and computed drift metrics. Used by live dashboards to serve public weather AI forecasts.

- **retro**: Dedicated to historical re-analysis, model backtesting, and retro-fitting algorithms against historical weather datasets (ERA5 / reanalysis data) without mutating live operational logs.

**2. Deployment Execution Mode (`WAID_DEPLOY_MODE`)**
The `WAID_DEPLOY_MODE` variable determines the backend data source queried by the Streamlit application (`waid_08_1_viz_streamlit_app.py`).

- **cloud** (Default for Cloud & Remote Deployments):
       - Streamlit connects directly to Supabase PostgreSQL via Streamlit Secrets / SQLAlchemy using the schema specified in `WAID_DB_SCHEMA_TARGET`.
       - Eliminates the need to maintain or transfer local SQLite binaries to cloud hosting services (e.g., Streamlit Community Cloud).
       - Provides real-time synchronization between the ARM edge pipeline and public dashboard viewers.

- **local** (Used for Offline / On-Premises Execution):
       - Streamlit queries the local SQLite database (data/waid_deploy.db or data/waid.db).
       - Enables zero-network, fully offline execution and rapid local prototyping without incurring cloud database overhead or requiring external network connectivity.

---

## 🚀 Live Operational Dashboard

The live demonstration and operational dashboard of the WAID framework is hosted on Streamlit Cloud:

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://waid-analytics.streamlit.app/)

> **Live Web App**: <https://waid-analytics.streamlit.app/>

---
## Conclusion: The Convergence of Learning and Laws

The core philosophy of the WAID project is that the future of forecasting lies in the convergence of learned patterns and deterministic physical laws. By combining the predictive flexibility of LSTMs with the mathematical certainty of solar physics and continuous reconciliation with reality, we can bypass the limitations of global-only models.

As we continue to push intelligence further toward the edge where data is born, we must ask ourselves: What strategies are you using to integrate deterministic physical constraints into ML inference at the edge?