## Global Architecture

 WAID is designed as a **portable, multi-environment weather forecasting platform**. The same core pipeline can run on a conventional PC/server or on a resource-constrained ARM Edge device, while the resulting data can be consumed either locally or through a remote cloud deployment.

 The architecture separates **data processing, machine learning, orchestration, storage, and visualization**, allowing the platform to adapt to different operational environments without changing the underlying forecasting pipeline.

 ### Deployment Modes

 WAID supports several deployment scenarios:

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

```
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

```
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

## 🌐 Live Operational Dashboard

The live demonstration and operational dashboard of the WAID framework is hosted on Streamlit Cloud:

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://waid-analytics.streamlit.app/)

> **Live Web App**: <https://waid-analytics.streamlit.app/>

### 🚀 Public Access & Deployment Overview
```text
+-----------------------------------------------------------------------+
|                         WAID LIVE DEMO                                |
|             https://waid-analytics.streamlit.app/                    |
+-----------------------------------------------------------------------+
|  • Operational Nowcasting UI: Live predictions vs Ecowitt vs ERA5     |
|  • Isolated Deployment DB: Syncs via Stage 08 ETL export pipeline     |
|  • Continuous Integration: Automatically rebuilt upon git push        |
+-----------------------------------------------------------------------+

```