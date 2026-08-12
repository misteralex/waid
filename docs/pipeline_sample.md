## Weather AI Data (WAID) Pipeline Architecture

* **Boot & Environment Initialization**: The orchestrator boots up, validates configuration variables, activates debugging mode, and retrieves local station metadata (such as elevation and guardrail parameters).
* **dbt Preparation**: The workflow cleans the dbt environment, resolves dependencies, compiles project models, and dumps shared environment variables.
* **Data Ingestion (Extraction)**: Raw telemetry is extracted from the local Ecowitt weather station via IP, while historical reanalysis fields (temperature, pressure, wind, solar radiation, precipitation) are downloaded asynchronously via Copernicus CDS (ERA5 NetCDF streams).
* **Data Discovery & Profiling (Catalog)**: Raw records are synchronized and converted to UTC in a SQLite database, and ERA5 datasets undergo rigorous profiling to validate structure, dimensions, coordinate ranges, and data quality (including latency checks).
* **Synchronization & Data Alignment (Transform)**: Staging dbt models clean and cast telemetry data, running automated data tests before performing a left-join time-series alignment between the local station measurements and the ERA5 grid variables.
* **Performance Metrics & Bias Study (Analyze/Benchmark)**: Discrepancy analysis computes real-time biases across multiple meteorological dimensions (temperature, pressure, humidity, wind, solar radiation, rain), storing outputs in intermediate feature tables validated by dbt tests.
* **Inference & Physics Guardrails**: Active models load successfully to generate short-term weather forecasts protected by strict, physics-safe guardrails that verify theoretical solar limits and persistent historical tracking.

---

## Pipeline Execution Log

```log

2026-08-10 21:57:08.601 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:381 - Boot WAID pipeline...
2026-08-10 21:57:08.801 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:407 - WAID_VERSION = '1.0.0' (configuration source: waid.env)
2026-08-10 21:57:08.817 | DEBUG    | boot.py:<module>:427 | Debugging successfully activated
2026-08-10 21:57:08.817 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Debugging successfully activated
2026-08-10 21:57:08.818 | INFO     | waid_07_1_inference_forecast.py:main:360 | Initializing 6-hour weather inference and strict physics-safe guardrail pipeline...
2026-08-10 21:57:08.818 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Initializing 6-hour weather inference and strict physics-safe guardrail pipeline...
2026-08-10 21:57:08.898 | INFO     | waid_utils.py:get_station_metadata:176 | Loaded Station Metadata from DB: 'Local Home Weather Station' (STATION_01) | Elevation: 6m | Guardrails: Min Days=14, Retrain Window=30
2026-08-10 21:57:08.899 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Guardrails: Min Days=14, Retrain Window=30
2026-08-10 21:57:08.965 | INFO     | waid_orchestrate.py:run_command:125 | [Profiling] E0000 00:00:1786391828.965317   32335 cuda_platform.cc:52] failed call to cuInit: INTERNAL: CUDA error: Failed call to cuInit: UNKNOWN ERROR (303)
2026-08-10 21:57:09.115 | SUCCESS  | waid_07_1_inference_forecast.py:load_active_model_artifacts:66 | Active model and scalers loaded successfully.
2026-08-10 21:57:09.115 | INFO     | waid_utils.py:fetch_and_resample_ecowitt:66 | Connecting to Ecowitt Database: /home/alex/waid/data/waid.db
2026-08-10 21:57:09.115 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Active model and scalers loaded successfully.
2026-08-10 21:57:09.116 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Connecting to Ecowitt Database: /home/alex/waid/data/waid.db
2026-08-10 21:57:09.121 | INFO     | waid_utils.py:fetch_and_resample_ecowitt:71 | Querying Ecowitt DB for window: [2026-08-07 21:57:09] to [2026-08-10 21:57:09]
2026-08-10 21:57:09.121 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Querying Ecowitt DB for window: [2026-08-07 21:57:09] to [2026-08-10 21:57:09]
2026-08-10 21:57:09.208 | INFO     | waid_utils.py:fetch_and_resample_ecowitt:111 | Resampling local telemetry into 60min synchronized slots...
2026-08-10 21:57:09.209 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Resampling local telemetry into 60min synchronized slots...
2026-08-10 21:57:09.216 | INFO     | waid_utils.py:fetch_and_resample_ecowitt:130 | Applying bounded time interpolation (max threshold: 2h / 2 steps)...
2026-08-10 21:57:09.216 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Applying bounded time interpolation (max threshold: 2h / 2 steps)...
2026-08-10 21:57:09.231 | DEBUG    | waid_07_1_inference_forecast.py:build_inference_tensor:131 | Physics Guardrail - Forecast Input Tensor - Theoretical Solar Range: Min=0.00 W/m², Max=833.42 W/m²
2026-08-10 21:57:09.232 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Physics Guardrail - Forecast Input Tensor - Theoretical Solar Range: Min=0.00 W/m², Max=833.42 W/m²
2026-08-10 21:57:09.558 | INFO     | waid_07_1_inference_forecast.py:main:398 | Using strict target order for reconstruction: ['ecowitt_temp', 'ecowitt_rh', 'ecowitt_pres', 'ecowitt_wind', 'ecowitt_solar', 'ecowitt_rain']
2026-08-10 21:57:09.559 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Using strict target order for reconstruction: ['ecowitt_temp', 'ecowitt_rh', 'ecowitt_pres', 'ecowitt_wind', 'ecowitt_solar', 'ecowitt_rain']
2026-08-10 21:57:09.559 | INFO     | waid_07_1_inference_forecast.py:main:399 | Last Actual Telemetry Baseline:
{'ecowitt_temp': 28.862264150943396, 'ecowitt_rh': 29.69811320754717, 'ecowitt_pres': 1013.8358490566038, 'ecowitt_wind': 0.22075471698113205, 'ecowitt_solar': 1.6260377358490568, 'ecowitt_rain': 0.0}
2026-08-10 21:57:09.559 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Last Actual Telemetry Baseline:
2026-08-10 21:57:09.560 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] {'ecowitt_temp': 28.862264150943396, 'ecowitt_rh': 29.69811320754717, 'ecowitt_pres': 1013.8358490566038, 'ecowitt_wind': 0.22075471698113205, 'ecowitt_solar': 1.6260377358490568, 'ecowitt_rain': 0.0}
2026-08-10 21:57:09.561 | DEBUG    | waid_07_1_inference_forecast.py:apply_physics_guardrails:150 | Physics Guardrail - Forecast Guardrails - Future Theoretical Solar Range: Min=0.00 W/m², Max=0.00 W/m²
2026-08-10 21:57:09.562 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Physics Guardrail - Forecast Guardrails - Future Theoretical Solar Range: Min=0.00 W/m², Max=0.00 W/m²
2026-08-10 21:57:09.668 | SUCCESS  | waid_07_1_inference_forecast.py:persist_and_update_inference_forecast:352 | Permanent inference_forecast table successfully updated for all 6 features with incremental predictions and consuntivo actuals.
2026-08-10 21:57:09.669 | SUCCESS  | waid_07_1_inference_forecast.py:main:418 | 6-hour absolute forecast outputs successfully generated, guarded, and stored.
2026-08-10 21:57:09.669 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Permanent inference_forecast table successfully updated for all 6 features with incremental predictions and consuntivo actuals.
2026-08-10 21:57:09.669 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] 6-hour absolute forecast outputs successfully generated, guarded, and stored.
2026-08-10 21:57:10.662 | SUCCESS  | waid_orchestrate.py:main:639 | --- Pipeline successfully terminated ---
2026-08-10 21:57:10.700 | SUCCESS  | waid_scheduler.py:main:106 | Scheduled incremental run completed successfully.
2026-08-10 21:57:10.700 | INFO     | waid_scheduler.py:main:114 | Sleeping for 60 minutes until next execution...
2026-08-10 22:57:10.702 | INFO     | waid_scheduler.py:main:102 | Triggering scheduled incremental WAID pipeline run...
2026-08-10 22:57:11.653 | DEBUG    | boot.py:<module>:427 | Debugging successfully activated
2026-08-10 22:57:11.654 | INFO     | waid_orchestrate.py:main:550 | --- REGIME MODE (Mode 0): Incremental execution ---
2026-08-10 22:57:11.655 | DEBUG    | waid_orchestrate.py:run_step_sequence:433 | NO extra arguments passed to step 'waid_00_1_dbt_clean' (expects only runner)
2026-08-10 22:57:11.655 | INFO     | waid_orchestrate.py:waid_00_1_dbt_clean:145 | Cleaning dbt environment
2026-08-10 22:57:11.656 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [0, 1]
2026-08-10 22:57:11.656 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_00_1_dbt_clean
2026-08-10 22:57:11.656 | DEBUG    | waid_orchestrate.py:run_command:89 | dbt clean --target dev --vars {"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}
2026-08-10 22:57:11.656 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: dbt-run ---
2026-08-10 22:57:17.119 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:17  Running with dbt=1.11.12
2026-08-10 22:57:17.806 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:17  Checking /home/alex/waid/dbt/target/*
2026-08-10 22:57:17.872 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:17  Cleaned /home/alex/waid/dbt/target/*
2026-08-10 22:57:17.872 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:17  Checking /home/alex/waid/dbt/logs/*
2026-08-10 22:57:17.874 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:17  Cleaned /home/alex/waid/dbt/logs/*
2026-08-10 22:57:17.874 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:17  Checking /home/alex/waid/dbt/dbt_packages/*
2026-08-10 22:57:17.939 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:17  Cleaned /home/alex/waid/dbt/dbt_packages/*
2026-08-10 22:57:17.939 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:17  Finished cleaning all paths.
2026-08-10 22:57:18.944 | DEBUG    | waid_orchestrate.py:run_step_sequence:433 | NO extra arguments passed to step 'waid_00_2_dbt_deps' (expects only runner)
2026-08-10 22:57:18.945 | INFO     | waid_orchestrate.py:waid_00_2_dbt_deps:151 | Installing missing package dependencies
2026-08-10 22:57:18.945 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [0, 2]
2026-08-10 22:57:18.945 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_00_2_dbt_deps
2026-08-10 22:57:18.946 | DEBUG    | waid_orchestrate.py:run_command:89 | dbt deps --target dev --vars {"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}
2026-08-10 22:57:18.946 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: dbt-run ---
2026-08-10 22:57:21.587 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:21  Running with dbt=1.11.12
2026-08-10 22:57:22.385 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:22  Installing dbt-labs/dbt_utils
2026-08-10 22:57:22.937 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:22  Installed from version 1.3.0
2026-08-10 22:57:22.938 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:22  Updated version available: 1.4.1
2026-08-10 22:57:22.940 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:22
2026-08-10 22:57:22.941 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:22  Updates available for packages: ['dbt-labs/dbt_utils']
2026-08-10 22:57:22.941 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] Update your versions in packages.yml, then run dbt deps
2026-08-10 22:57:23.936 | DEBUG    | waid_orchestrate.py:run_step_sequence:433 | NO extra arguments passed to step 'waid_00_3_dbt_compile' (expects only runner)
2026-08-10 22:57:23.937 | INFO     | waid_orchestrate.py:waid_00_3_dbt_compile:157 | Compiling dbt project
2026-08-10 22:57:23.937 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [0, 3]
2026-08-10 22:57:23.938 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_00_3_dbt_compile
2026-08-10 22:57:23.938 | DEBUG    | waid_orchestrate.py:run_command:89 | dbt compile --target dev --vars {"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}
2026-08-10 22:57:23.939 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: dbt-run ---
2026-08-10 22:57:26.603 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:26  Running with dbt=1.11.12
2026-08-10 22:57:27.366 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:27  Registered adapter: sqlite=1.10.0
2026-08-10 22:57:27.641 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:27  Unable to do partial parsing because saved manifest not found. Starting full parse.
2026-08-10 22:57:30.796 | WARNING  | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:30  [WARNING][MissingArgumentsPropertyInGenericTestDeprecation]: Deprecated
2026-08-10 22:57:30.797 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] functionality
2026-08-10 22:57:30.797 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] Found top-level arguments to test `dbt_utils.accepted_range` defined on
2026-08-10 22:57:30.798 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 'stg_matches' in package 'waid' (models/staging/stg_matches.yml). Arguments to
2026-08-10 22:57:30.798 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] generic tests should be nested under the `arguments` property.
2026-08-10 22:57:31.322 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:31  Found 9 models, 19 data tests, 4 sources, 533 macros
2026-08-10 22:57:31.328 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:31
2026-08-10 22:57:31.328 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:31  Concurrency: 1 threads (target='dev')
2026-08-10 22:57:31.330 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:31
2026-08-10 22:57:32.004 | WARNING  | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:32  [WARNING][DeprecationsSummary]: Deprecated functionality
2026-08-10 22:57:32.004 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] Summary of encountered deprecations:
2026-08-10 22:57:32.005 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] - MissingArgumentsPropertyInGenericTestDeprecation: 3 occurrences
2026-08-10 22:57:32.005 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] To see all deprecation instances instead of just the first occurrence of each,
2026-08-10 22:57:32.006 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] run command again with the `--show-all-deprecations` flag. You may also need to
2026-08-10 22:57:32.006 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] run with `--no-partial-parse` as some deprecations are only encountered during
2026-08-10 22:57:32.007 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] parsing.
2026-08-10 22:57:33.105 | DEBUG    | waid_orchestrate.py:run_step_sequence:433 | NO extra arguments passed to step 'waid_00_4_dbt_dump_vars' (expects only runner)
2026-08-10 22:57:33.105 | INFO     | waid_orchestrate.py:waid_00_4_dbt_dump_vars:163 | DBT check up shared variables
2026-08-10 22:57:33.105 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [0, 4]
2026-08-10 22:57:33.105 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_00_4_dbt_dump_vars
2026-08-10 22:57:33.106 | DEBUG    | waid_orchestrate.py:run_command:89 | dbt run-operation dump_vars --target dev --vars {"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}
2026-08-10 22:57:33.106 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: dbt-run ---
2026-08-10 22:57:35.930 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:35  Running with dbt=1.11.12
2026-08-10 22:57:36.444 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:36  Registered adapter: sqlite=1.10.0
2026-08-10 22:57:37.393 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:37  Found 9 models, 19 data tests, 4 sources, 533 macros
2026-08-10 22:57:37.412 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:57:37  {"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}
2026-08-10 22:57:38.434 | INFO     | waid_orchestrate.py:main:630 | Starting INCREMENTAL execution
2026-08-10 22:57:38.434 | INFO     | waid_orchestrate.py:waid_01_1_ingest_ecowitt:182 | Downloading Ecowitt data
2026-08-10 22:57:38.435 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [1, 1] - Period: 2026-08
2026-08-10 22:57:38.435 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_01_1_ingest_ecowitt
2026-08-10 22:57:38.436 | DEBUG    | waid_orchestrate.py:run_command:89 | python /home/alex/waid/src/waid_01_1_ingest_ecowitt.py --period 2026-08
2026-08-10 22:57:38.436 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: Download ---
2026-08-10 22:57:38.963 | INFO     | waid_orchestrate.py:run_command:129 | [Download] boot:<module>:381 - Boot WAID pipeline...
2026-08-10 22:57:39.168 | DEBUG    | waid_orchestrate.py:run_command:129 | [Download] boot:<module>:407 - WAID_VERSION = '1.0.0' (configuration source: waid.env)
2026-08-10 22:57:39.182 | DEBUG    | boot.py:<module>:427 | Debugging successfully activated
2026-08-10 22:57:39.182 | DEBUG    | waid_orchestrate.py:run_command:129 | [Download] Debugging successfully activated
2026-08-10 22:57:39.183 | INFO     | waid_01_1_ingest_ecowitt.py:main:157 | Default station IP: 192.168.1.100
2026-08-10 22:57:39.184 | INFO     | waid_orchestrate.py:run_command:129 | [Download] Default station IP: 192.168.1.100
2026-08-10 22:57:39.184 | INFO     | waid_01_1_ingest_ecowitt.py:download_ecowitt_data:63 | Starting Ecowitt Download
2026-08-10 22:57:39.185 | INFO     | waid_01_1_ingest_ecowitt.py:download_ecowitt_data:64 | Period: 2026-08 | Station: 192.168.1.100:81
2026-08-10 22:57:39.185 | INFO     | waid_orchestrate.py:run_command:129 | [Download] Starting Ecowitt Download
2026-08-10 22:57:39.185 | INFO     | waid_01_1_ingest_ecowitt.py:download_ecowitt_data:81 | Target file: 202608.csv
2026-08-10 22:57:39.185 | INFO     | waid_orchestrate.py:run_command:129 | [Download] Station: 192.168.1.100:81
2026-08-10 22:57:39.185 | INFO     | waid_orchestrate.py:run_command:129 | [Download] Target file: 202608.csv
2026-08-10 22:57:39.334 | INFO     | waid_01_1_ingest_ecowitt.py:download_ecowitt_data:95 | Downloading 202608A.csv
2026-08-10 22:57:39.334 | INFO     | waid_orchestrate.py:run_command:129 | [Download] Downloading 202608A.csv
2026-08-10 22:57:51.198 | INFO     | waid_01_1_ingest_ecowitt.py:download_ecowitt_data:134 | Successfully created: 202608.csv
2026-08-10 22:57:51.199 | INFO     | waid_orchestrate.py:run_command:129 | [Download] Successfully created: 202608.csv
2026-08-10 22:57:51.240 | INFO     | waid_orchestrate.py:waid_01_2_ingest_era5:191 | Downloading ERA5 data
2026-08-10 22:57:51.241 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [1, 2] - Period: 2026-08
2026-08-10 22:57:51.241 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_01_2_ingest_era5
2026-08-10 22:57:51.242 | DEBUG    | waid_orchestrate.py:run_command:89 | python /home/alex/waid/src/waid_01_2_ingest_era5.py --period 2026-08
2026-08-10 22:57:51.242 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: Download ---
2026-08-10 22:57:53.341 | INFO     | waid_orchestrate.py:run_command:129 | [Download] boot:<module>:381 - Boot WAID pipeline...
2026-08-10 22:57:53.539 | DEBUG    | waid_orchestrate.py:run_command:129 | [Download] boot:<module>:407 - WAID_VERSION = '1.0.0' (configuration source: waid.env)
2026-08-10 22:57:53.554 | DEBUG    | boot.py:<module>:427 | Debugging successfully activated
2026-08-10 22:57:53.555 | DEBUG    | waid_orchestrate.py:run_command:129 | [Download] Debugging successfully activated
2026-08-10 22:57:53.556 | INFO     | waid_01_2_ingest_era5.py:download_era5:50 | Starting ERA5 Download (Month: 2026-08)
2026-08-10 22:57:53.557 | INFO     | waid_01_2_ingest_era5.py:download_era5:51 | Target UTC Coordinates: (41.9028, 12.4964) | Elevation: 6.0m
2026-08-10 22:57:53.557 | INFO     | waid_orchestrate.py:run_command:129 | [Download] Starting ERA5 Download (Month: 2026-08)
2026-08-10 22:57:53.557 | INFO     | waid_orchestrate.py:run_command:129 | [Download] Elevation: 6.0m
2026-08-10 22:57:53.970 | INFO     | waid_01_2_ingest_era5.py:download_era5:83 | Requesting ERA5 variables for 2026-08 in UTC...
2026-08-10 22:57:53.971 | INFO     | waid_orchestrate.py:run_command:129 | [Download] Requesting ERA5 variables for 2026-08 in UTC...
2026-08-10 22:57:54.349 | INFO     | waid_orchestrate.py:run_command:129 | [Download] 2026-08-10 22:57:54,349 INFO Request ID is a564a8d1-c242-4f63-bf0e-f658e460860d
2026-08-10 22:57:54.446 | INFO     | waid_orchestrate.py:run_command:129 | [Download] 2026-08-10 22:57:54,446 INFO status has been updated to accepted
2026-08-10 22:58:09.145 | INFO     | waid_orchestrate.py:run_command:129 | [Download] 2026-08-10 22:58:09,145 INFO status has been updated to running
2026-08-10 22:59:11.477 | INFO     | waid_orchestrate.py:run_command:129 | [Download] 2026-08-10 22:59:11,476 INFO status has been updated to successful
2026-08-10 22:59:12.248 | INFO     | waid_orchestrate.py:run_command:129 | [Download] 
2026-08-10 22:59:12.600 | INFO     | waid_orchestrate.py:run_command:129 | [Download] 0.00/120k [00:00<?, ?B/s]
2026-08-10 22:59:12.602 | INFO     | waid_orchestrate.py:run_command:129 | [Download] 8a3ffd2d52227d892bf841bcd5f10462.zip: 100%|██████████| 120k/120k [00:00<00:00, 350kB/s]
2026-08-10 22:59:12.602 | INFO     | waid_01_2_ingest_era5.py:download_era5:114 | Server-side multi-file ZIP encapsulation detected. Consolidating parameter streams...
2026-08-10 22:59:12.602 | INFO     | waid_orchestrate.py:run_command:129 | [Download] 
2026-08-10 22:59:12.603 | INFO     | waid_orchestrate.py:run_command:129 | [Download] Server-side multi-file ZIP encapsulation detected. Consolidating parameter streams...
2026-08-10 22:59:12.728 | INFO     | waid_01_2_ingest_era5.py:download_era5:123 | Combining 2 NetCDF stream components...
2026-08-10 22:59:12.728 | INFO     | waid_orchestrate.py:run_command:129 | [Download] Combining 2 NetCDF stream components...
2026-08-10 22:59:14.012 | INFO     | waid_01_2_ingest_era5.py:download_era5:128 | Latest record timestamp (UTC): 2026-08-05 20:00:00
2026-08-10 22:59:14.013 | INFO     | waid_orchestrate.py:run_command:129 | [Download] Latest record timestamp (UTC): 2026-08-05 20:00:00
2026-08-10 22:59:14.361 | INFO     | waid_01_2_ingest_era5.py:download_era5:137 | Parameter streams merged successfully into single NetCDF dataset.
2026-08-10 22:59:14.361 | INFO     | waid_orchestrate.py:run_command:129 | [Download] Parameter streams merged successfully into single NetCDF dataset.
2026-08-10 22:59:14.362 | INFO     | waid_01_2_ingest_era5.py:download_era5:152 | Success! Ready data file: /home/alex/waid/data/era5/era5_2026_08.nc
2026-08-10 22:59:14.362 | INFO     | waid_01_2_ingest_era5.py:download_era5:174 | --- ERA5 Download process completed ---
2026-08-10 22:59:14.362 | INFO     | waid_orchestrate.py:run_command:129 | [Download] Success! Ready data file: /home/alex/waid/data/era5/era5_2026_08.nc
2026-08-10 22:59:14.362 | INFO     | waid_orchestrate.py:run_command:129 | [Download] --- ERA5 Download process completed ---
2026-08-10 22:59:14.748 | INFO     | waid_orchestrate.py:waid_02_1_sync_ecowitt:200 | Synchronizing Ecowitt with SQLite database
2026-08-10 22:59:14.748 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [2, 1] - Period: 2026-08
2026-08-10 22:59:14.748 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_02_1_sync_ecowitt
2026-08-10 22:59:14.749 | DEBUG    | waid_orchestrate.py:run_command:89 | python /home/alex/waid/src/waid_02_1_sync_ecowitt.py --period 2026-08
2026-08-10 22:59:14.749 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: Ingestion ---
2026-08-10 22:59:15.996 | INFO     | waid_orchestrate.py:run_command:129 | [Ingestion] boot:<module>:381 - Boot WAID pipeline...
2026-08-10 22:59:16.352 | DEBUG    | waid_orchestrate.py:run_command:129 | [Ingestion] boot:<module>:407 - WAID_VERSION = '1.0.0' (configuration source: waid.env)
2026-08-10 22:59:16.370 | DEBUG    | boot.py:<module>:427 | Debugging successfully activated
2026-08-10 22:59:16.371 | DEBUG    | waid_orchestrate.py:run_command:129 | [Ingestion] Debugging successfully activated
2026-08-10 22:59:16.373 | INFO     | waid_02_1_sync_ecowitt.py:ensure_table_exists:73 | Checking current Ecowitt table schema (ecowitt_records)...
2026-08-10 22:59:16.373 | INFO     | waid_orchestrate.py:run_command:129 | [Ingestion] Checking current Ecowitt table schema (ecowitt_records)...
2026-08-10 22:59:16.411 | INFO     | waid_02_1_sync_ecowitt.py:ensure_table_exists:91 | Table sanity check successfully completed (ecowitt_records).
2026-08-10 22:59:16.412 | INFO     | waid_orchestrate.py:run_command:129 | [Ingestion] Table sanity check successfully completed (ecowitt_records).
2026-08-10 22:59:16.412 | INFO     | waid_02_1_sync_ecowitt.py:sync_ecowitt_with_db:158 | Looking for Ecowitt data file: /home/alex/waid/data/ecowitt/202608.csv
2026-08-10 22:59:16.412 | INFO     | waid_orchestrate.py:run_command:129 | [Ingestion] Looking for Ecowitt data file: /home/alex/waid/data/ecowitt/202608.csv
2026-08-10 22:59:16.712 | INFO     | waid_02_1_sync_ecowitt.py:process_timestamps_to_utc:109 | Converting raw timestamps from local timezone ('Europe/Paris') to UTC...
2026-08-10 22:59:16.712 | INFO     | waid_orchestrate.py:run_command:129 | [Ingestion] Converting raw timestamps from local timezone ('Europe/Paris') to UTC...
2026-08-10 22:59:19.312 | INFO     | waid_02_1_sync_ecowitt.py:sync_ecowitt_with_db:210 | Aggregation complete. Total new UTC records inserted: 65
2026-08-10 22:59:19.312 | INFO     | waid_orchestrate.py:run_command:129 | [Ingestion] Aggregation complete. Total new UTC records inserted: 65
2026-08-10 22:59:19.588 | INFO     | waid_orchestrate.py:waid_02_2_profile_era5:209 | Profiling ERA5 data
2026-08-10 22:59:19.588 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [2, 2] - Period: 2026-08
2026-08-10 22:59:19.589 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_02_2_profile_era5
2026-08-10 22:59:19.589 | DEBUG    | waid_orchestrate.py:run_command:89 | python /home/alex/waid/src/waid_02_2_profile_era5.py --period 2026-08
2026-08-10 22:59:19.590 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: Profiling ---
2026-08-10 22:59:20.942 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:381 - Boot WAID pipeline...
2026-08-10 22:59:21.234 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:407 - WAID_VERSION = '1.0.0' (configuration source: waid.env)
2026-08-10 22:59:21.257 | DEBUG    | boot.py:<module>:427 | Debugging successfully activated
2026-08-10 22:59:21.258 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Debugging successfully activated
2026-08-10 22:59:21.260 | INFO     | waid_02_2_profile_era5.py:check_era5_data:40 | --- Starting profiling (Month: 2026-08) ---
2026-08-10 22:59:21.261 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] --- Starting profiling (Month: 2026-08) ---
2026-08-10 22:59:21.261 | INFO     | waid_02_2_profile_era5.py:check_era5_data:53 | Analyzing ERA5 file: /home/alex/waid/data/era5/era5_2026_08.nc
2026-08-10 22:59:21.262 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Analyzing ERA5 file: /home/alex/waid/data/era5/era5_2026_08.nc
2026-08-10 22:59:21.414 | INFO     | waid_02_2_profile_era5.py:check_era5_data:59 |  [HEADER & PARAMETERS]
2026-08-10 22:59:21.415 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] [HEADER & PARAMETERS]
2026-08-10 22:59:21.415 | INFO     | waid_02_2_profile_era5.py:check_era5_data:60 | Dimensions: {'valid_time': 117, 'latitude': 2, 'longitude': 2}
2026-08-10 22:59:21.415 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Dimensions: {'valid_time': 117, 'latitude': 2, 'longitude': 2}
2026-08-10 22:59:21.416 | INFO     | waid_02_2_profile_era5.py:check_era5_data:63 | Data Variables (Catalog mapping ready):
2026-08-10 22:59:21.416 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Data Variables (Catalog mapping ready):
2026-08-10 22:59:21.417 | INFO     | waid_02_2_profile_era5.py:check_era5_data:67 |   - t2m        | K          | 2 metre temperature
2026-08-10 22:59:21.417 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] 2 metre temperature
2026-08-10 22:59:21.418 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] 2 metre dewpoint temperature
2026-08-10 22:59:21.418 | INFO     | waid_02_2_profile_era5.py:check_era5_data:67 |   - d2m        | K          | 2 metre dewpoint temperature
2026-08-10 22:59:21.419 | INFO     | waid_02_2_profile_era5.py:check_era5_data:67 |   - sp         | Pa         | Surface pressure
2026-08-10 22:59:21.419 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Surface pressure
2026-08-10 22:59:21.420 | INFO     | waid_02_2_profile_era5.py:check_era5_data:67 |   - u10        | m s**-1    | 10 metre U wind component
2026-08-10 22:59:21.420 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] 10 metre U wind component
2026-08-10 22:59:21.420 | INFO     | waid_02_2_profile_era5.py:check_era5_data:67 |   - v10        | m s**-1    | 10 metre V wind component
2026-08-10 22:59:21.421 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] 10 metre V wind component
2026-08-10 22:59:21.421 | INFO     | waid_02_2_profile_era5.py:check_era5_data:67 |   - z          | m**2 s**-2 | Geopotential
2026-08-10 22:59:21.421 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Geopotential
2026-08-10 22:59:21.421 | INFO     | waid_02_2_profile_era5.py:check_era5_data:67 |   - ssrd       | J m**-2    | Surface short-wave (solar) radiation downwards
2026-08-10 22:59:21.422 | INFO     | waid_02_2_profile_era5.py:check_era5_data:67 |   - tp         | m          | Total precipitation
2026-08-10 22:59:21.422 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Surface short-wave (solar) radiation downwards
2026-08-10 22:59:21.422 | INFO     | waid_02_2_profile_era5.py:check_era5_data:70 |  [COORDINATE CHECK]
2026-08-10 22:59:21.422 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Total precipitation
2026-08-10 22:59:21.422 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] [COORDINATE CHECK]
2026-08-10 22:59:21.424 | INFO     | waid_02_2_profile_era5.py:check_era5_data:71 | Lat Range: 41.90 to 42.0
2026-08-10 22:59:21.424 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Lat Range: 41.90 to 42.0
2026-08-10 22:59:21.425 | INFO     | waid_02_2_profile_era5.py:check_era5_data:72 | Lon Range: 12.50 to 2.5
2026-08-10 22:59:21.425 | INFO     | waid_02_2_profile_era5.py:check_era5_data:73 | Target from .env: 41.9028, 12.4964
2026-08-10 22:59:21.425 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Lon Range: 12.50 to 2.5
2026-08-10 22:59:21.425 | INFO     | waid_02_2_profile_era5.py:check_era5_data:76 |  [DATA PREVIEW & VALIDATION]
2026-08-10 22:59:21.425 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Target from .env: 41.9028, 12.4964
2026-08-10 22:59:21.426 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] [DATA PREVIEW & VALIDATION]
2026-08-10 22:59:21.756 | INFO     | waid_02_2_profile_era5.py:check_era5_data:89 | Data Quality: No missing values found in the selected point.
2026-08-10 22:59:21.757 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Data Quality: No missing values found in the selected point.
2026-08-10 22:59:21.943 | INFO     | waid_02_2_profile_era5.py:check_era5_data:92 | Sample Data (First 5 rows):
           valid_time         t2m         d2m  ...  latitude  longitude  expver
0 2026-08-01 00:00:00  291.910522  287.920349  ...     41.90       12.50    0005
1 2026-08-01 01:00:00  291.136261  287.892761  ...     41.90       12.50    0005
2 2026-08-01 02:00:00  290.382172  287.437927  ...     41.90       12.50    0005
3 2026-08-01 03:00:00  289.666382  286.907501  ...     41.90       12.50    0005
4 2026-08-01 04:00:00  289.121277  286.594543  ...     41.90       12.50    0005

[5 rows x 13 columns]
2026-08-10 22:59:21.943 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Sample Data (First 5 rows):
2026-08-10 22:59:21.944 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] valid_time         t2m         d2m  ...  latitude  longitude  expver
2026-08-10 22:59:21.944 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] 0 2026-08-01 00:00:00  291.910522  287.920349  ...     41.90       12.50    0005
2026-08-10 22:59:21.945 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] 1 2026-08-01 01:00:00  291.136261  287.892761  ...     41.90       12.50    0005
2026-08-10 22:59:21.945 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] 2 2026-08-01 02:00:00  290.382172  287.437927  ...     41.90       12.50    0005
2026-08-10 22:59:21.946 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] 3 2026-08-01 03:00:00  289.666382  286.907501  ...     41.90       12.50    0005
2026-08-10 22:59:21.946 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] 4 2026-08-01 04:00:00  289.121277  286.594543  ...     41.90       12.50    0005
2026-08-10 22:59:21.946 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] 
2026-08-10 22:59:21.947 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] [5 rows x 13 columns]
2026-08-10 22:59:22.330 | INFO     | waid_02_2_profile_era5.py:check_era5_data:93 | Basic Stats:
                         valid_time         t2m  ...  latitude  longitude
min             2026-08-01 00:00:00  287.064453  ...     41.90       12.50
max             2026-08-05 20:00:00  308.402710  ...     41.90       12.50
mean  2026-08-03 10:00:00.000000256  297.437561  ...     41.90       12.50

[3 rows x 12 columns]
2026-08-10 22:59:22.330 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Basic Stats:
2026-08-10 22:59:22.331 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] valid_time         t2m  ...  latitude  longitude
2026-08-10 22:59:22.331 | INFO     | waid_02_2_profile_era5.py:check_era5_data:97 | Most recent measurement: 2026-08-05 20:00:00
2026-08-10 22:59:22.331 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] min             2026-08-01 00:00:00  287.064453  ...     41.90       12.50
2026-08-10 22:59:22.332 | WARNING  | waid_02_2_profile_era5.py:check_era5_data:103 | Partial dataset. Latency lag: 5.1 days
2026-08-10 22:59:22.332 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] max             2026-08-05 20:00:00  308.402710  ...     41.90       12.50
2026-08-10 22:59:22.332 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] mean  2026-08-03 10:00:00.000000256  297.437561  ...     41.90       12.50
2026-08-10 22:59:22.333 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] 
2026-08-10 22:59:22.333 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] [3 rows x 12 columns]
2026-08-10 22:59:22.333 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Most recent measurement: 2026-08-05 20:00:00
2026-08-10 22:59:22.334 | WARNING  | waid_orchestrate.py:run_command:129 | [Profiling] Partial dataset. Latency lag: 5.1 days
2026-08-10 22:59:22.593 | INFO     | waid_orchestrate.py:waid_02_3_dbt_clean_ecowitt:218 | Staging table for cleaned and casted Ecowitt data
2026-08-10 22:59:22.594 | DEBUG    | waid_orchestrate.py:waid_02_3_dbt_clean_ecowitt:219 | Extra arguments: ['--period', '2026-08']
2026-08-10 22:59:22.594 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [2, 3] - Period: 2026-08
2026-08-10 22:59:22.595 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_02_3_dbt_clean_ecowitt
2026-08-10 22:59:22.595 | DEBUG    | waid_orchestrate.py:run_command:89 | dbt run --select stg_ecowitt --target dev --vars {"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}
2026-08-10 22:59:22.596 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: dbt-run ---
2026-08-10 22:59:26.172 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:26  Running with dbt=1.11.12
2026-08-10 22:59:26.712 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:26  Registered adapter: sqlite=1.10.0
2026-08-10 22:59:27.821 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:27  Found 9 models, 19 data tests, 4 sources, 533 macros
2026-08-10 22:59:27.826 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:27
2026-08-10 22:59:27.827 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:27  Concurrency: 1 threads (target='dev')
2026-08-10 22:59:27.829 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:27
2026-08-10 22:59:27.997 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:27  1 of 1 START sql table model main.stg_ecowitt .................................. [RUN]
2026-08-10 22:59:40.072 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:40  1 of 1 OK created sql table model main.stg_ecowitt ............................. [OK in 11.95s]
2026-08-10 22:59:40.091 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:40
2026-08-10 22:59:40.093 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:40  Finished running 1 table model in 0 hours 0 minutes and 12.26 seconds (12.26s).
2026-08-10 22:59:40.183 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:40
2026-08-10 22:59:40.184 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:40  Completed successfully
2026-08-10 22:59:40.185 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:40
2026-08-10 22:59:40.187 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:40  Done. PASS=1 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=1
2026-08-10 22:59:41.305 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [2, 3] - Period: 2026-08
2026-08-10 22:59:41.305 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_02_3_dbt_clean_ecowitt
2026-08-10 22:59:41.305 | DEBUG    | waid_orchestrate.py:run_command:89 | dbt test --select stg_ecowitt --store-failures --target dev --vars {"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}
2026-08-10 22:59:41.305 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: dbt-test ---
2026-08-10 22:59:44.040 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:44  Running with dbt=1.11.12
2026-08-10 22:59:44.627 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:44  Registered adapter: sqlite=1.10.0
2026-08-10 22:59:45.607 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:45  Found 9 models, 19 data tests, 4 sources, 533 macros
2026-08-10 22:59:45.611 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:45
2026-08-10 22:59:45.612 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:45  Concurrency: 1 threads (target='dev')
2026-08-10 22:59:45.613 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:45
2026-08-10 22:59:45.792 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:45  1 of 8 START test dbt_utils_accepted_range_stg_ecowitt_hourly_rain__300__0 ..... [RUN]
2026-08-10 22:59:46.097 | SUCCESS  | waid_orchestrate.py:run_command:123 | [dbt-test] 20:59:46  1 of 8 PASS dbt_utils_accepted_range_stg_ecowitt_hourly_rain__300__0 ........... [PASS in 0.30s]
2026-08-10 22:59:46.101 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:46  2 of 8 START test dbt_utils_accepted_range_stg_ecowitt_humidity__100__0 ........ [RUN]
2026-08-10 22:59:46.230 | SUCCESS  | waid_orchestrate.py:run_command:123 | [dbt-test] 20:59:46  2 of 8 PASS dbt_utils_accepted_range_stg_ecowitt_humidity__100__0 .............. [PASS in 0.13s]
2026-08-10 22:59:46.234 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:46  3 of 8 START test dbt_utils_accepted_range_stg_ecowitt_pressure_hpa__1100__800 . [RUN]
2026-08-10 22:59:46.361 | SUCCESS  | waid_orchestrate.py:run_command:123 | [dbt-test] 20:59:46  3 of 8 PASS dbt_utils_accepted_range_stg_ecowitt_pressure_hpa__1100__800 ....... [PASS in 0.13s]
2026-08-10 22:59:46.364 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:46  4 of 8 START test dbt_utils_accepted_range_stg_ecowitt_solar_radiation__1500__0  [RUN]
2026-08-10 22:59:46.544 | SUCCESS  | waid_orchestrate.py:run_command:123 | [dbt-test] 20:59:46  4 of 8 PASS dbt_utils_accepted_range_stg_ecowitt_solar_radiation__1500__0 ...... [PASS in 0.18s]
2026-08-10 22:59:46.548 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:46  5 of 8 START test dbt_utils_accepted_range_stg_ecowitt_temperature__50___30 .... [RUN]
2026-08-10 22:59:46.757 | SUCCESS  | waid_orchestrate.py:run_command:123 | [dbt-test] 20:59:46  5 of 8 PASS dbt_utils_accepted_range_stg_ecowitt_temperature__50___30 .......... [PASS in 0.21s]
2026-08-10 22:59:46.761 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:46  6 of 8 START test dbt_utils_accepted_range_stg_ecowitt_wind_speed__80__0 ....... [RUN]
2026-08-10 22:59:46.885 | SUCCESS  | waid_orchestrate.py:run_command:123 | [dbt-test] 20:59:46  6 of 8 PASS dbt_utils_accepted_range_stg_ecowitt_wind_speed__80__0 ............. [PASS in 0.12s]
2026-08-10 22:59:46.888 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:46  7 of 8 START test not_null_stg_ecowitt_timestamp ............................... [RUN]
2026-08-10 22:59:46.997 | SUCCESS  | waid_orchestrate.py:run_command:123 | [dbt-test] 20:59:46  7 of 8 PASS not_null_stg_ecowitt_timestamp ..................................... [PASS in 0.11s]
2026-08-10 22:59:47.001 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:47  8 of 8 START test unique_stg_ecowitt_timestamp ................................. [RUN]
2026-08-10 22:59:47.466 | SUCCESS  | waid_orchestrate.py:run_command:123 | [dbt-test] 20:59:47  8 of 8 PASS unique_stg_ecowitt_timestamp ....................................... [PASS in 0.46s]
2026-08-10 22:59:47.483 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:47
2026-08-10 22:59:47.484 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:47  Finished running 8 data tests in 0 hours 0 minutes and 1.87 seconds (1.87s).
2026-08-10 22:59:47.574 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:47
2026-08-10 22:59:47.575 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:47  Completed successfully
2026-08-10 22:59:47.576 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:47
2026-08-10 22:59:47.577 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:47  Done. PASS=8 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=8
2026-08-10 22:59:48.606 | INFO     | waid_orchestrate.py:waid_03_1_match_datasets:235 | Data matching between ERA5 and Ecowitt
2026-08-10 22:59:48.607 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [3, 1] - Period: 2026-08
2026-08-10 22:59:48.607 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_03_1_match_datasets
2026-08-10 22:59:48.608 | DEBUG    | waid_orchestrate.py:run_command:89 | python /home/alex/waid/src/waid_03_1_match_datasets.py --period 2026-08
2026-08-10 22:59:48.608 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: Matching ---
2026-08-10 22:59:49.733 | INFO     | waid_orchestrate.py:run_command:129 | [Matching] boot:<module>:381 - Boot WAID pipeline...
2026-08-10 22:59:49.949 | DEBUG    | waid_orchestrate.py:run_command:129 | [Matching] boot:<module>:407 - WAID_VERSION = '1.0.0' (configuration source: waid.env)
2026-08-10 22:59:49.965 | DEBUG    | boot.py:<module>:427 | Debugging successfully activated
2026-08-10 22:59:49.965 | DEBUG    | waid_orchestrate.py:run_command:129 | [Matching] Debugging successfully activated
2026-08-10 22:59:50.019 | INFO     | waid_03_1_match_datasets.py:perform_matching_with_era5:218 | Using ERA5 Dataset: era5_2026_08.nc
2026-08-10 22:59:50.019 | INFO     | waid_orchestrate.py:run_command:129 | [Matching] Using ERA5 Dataset: era5_2026_08.nc
2026-08-10 22:59:50.116 | INFO     | waid_03_1_match_datasets.py:perform_matching_with_era5:221 | Extracting grid variables for Target Location (Lat: 41.9028, Lon: 12.4964)
2026-08-10 22:59:50.117 | INFO     | waid_orchestrate.py:run_command:129 | [Matching] Extracting grid variables for Target Location (Lat: 41.9028, Lon: 12.4964)
2026-08-10 22:59:50.148 | INFO     | waid_03_1_match_datasets.py:perform_matching_with_era5:271 | ERA5 extracted successfully. Records: 117
2026-08-10 22:59:50.149 | INFO     | waid_03_1_match_datasets.py:perform_matching_with_ecowitt:135 | Fetching Ecowitt hourly resampled data from 2026-08-01 00:00:00 to 2026-08-10 22:59:50
2026-08-10 22:59:50.149 | INFO     | waid_utils.py:fetch_and_resample_ecowitt:66 | Connecting to Ecowitt Database: /home/alex/waid/data/waid.db
2026-08-10 22:59:50.149 | INFO     | waid_orchestrate.py:run_command:129 | [Matching] ERA5 extracted successfully. Records: 117
2026-08-10 22:59:50.150 | INFO     | waid_orchestrate.py:run_command:129 | [Matching] Fetching Ecowitt hourly resampled data from 2026-08-01 00:00:00 to 2026-08-10 22:59:50
2026-08-10 22:59:50.150 | INFO     | waid_orchestrate.py:run_command:129 | [Matching] Connecting to Ecowitt Database: /home/alex/waid/data/waid.db
2026-08-10 22:59:50.156 | INFO     | waid_utils.py:fetch_and_resample_ecowitt:71 | Querying Ecowitt DB for window: [2026-08-01 00:00:00] to [2026-08-10 22:59:50]
2026-08-10 22:59:50.156 | INFO     | waid_orchestrate.py:run_command:129 | [Matching] Querying Ecowitt DB for window: [2026-08-01 00:00:00] to [2026-08-10 22:59:50]
2026-08-10 22:59:50.288 | INFO     | waid_utils.py:fetch_and_resample_ecowitt:111 | Resampling local telemetry into 60min synchronized slots...
2026-08-10 22:59:50.288 | INFO     | waid_orchestrate.py:run_command:129 | [Matching] Resampling local telemetry into 60min synchronized slots...
2026-08-10 22:59:50.451 | INFO     | waid_utils.py:fetch_and_resample_ecowitt:130 | Applying bounded time interpolation (max threshold: 2h / 2 steps)...
2026-08-10 22:59:50.452 | INFO     | waid_orchestrate.py:run_command:129 | [Matching] Applying bounded time interpolation (max threshold: 2h / 2 steps)...
2026-08-10 22:59:50.463 | INFO     | waid_03_1_match_datasets.py:perform_matching_with_ecowitt:164 | Merging Ecowitt station measurements with ERA5 model data (Left Join)...
2026-08-10 22:59:50.463 | INFO     | waid_orchestrate.py:run_command:129 | [Matching] Merging Ecowitt station measurements with ERA5 model data (Left Join)...
2026-08-10 22:59:50.480 | SUCCESS  | waid_03_1_match_datasets.py:perform_matching_with_ecowitt:172 | Synchronization complete! Total synchronized records: 237 rows.
2026-08-10 22:59:50.480 | INFO     | waid_orchestrate.py:run_command:129 | [Matching] Synchronization complete! Total synchronized records: 237 rows.
2026-08-10 22:59:50.493 | DEBUG    | waid_03_1_match_datasets.py:perform_matching_with_ecowitt:185 | --- BIAS REPORT FOR PERIOD: 2026-08 (Matched Subset: 115) ---
2026-08-10 22:59:50.493 | DEBUG    | waid_orchestrate.py:run_command:129 | [Matching] --- BIAS REPORT FOR PERIOD: 2026-08 (Matched Subset: 115) ---
2026-08-10 22:59:50.494 | DEBUG    | waid_03_1_match_datasets.py:perform_matching_with_ecowitt:186 | Mean Temp Bias       : +1.49 °C
2026-08-10 22:59:50.495 | DEBUG    | waid_orchestrate.py:run_command:129 | [Matching] Mean Temp Bias       : +1.49 °C
2026-08-10 22:59:50.495 | DEBUG    | waid_03_1_match_datasets.py:perform_matching_with_ecowitt:187 | Mean Pressure Bias   : +7.83 hPa
2026-08-10 22:59:50.496 | DEBUG    | waid_orchestrate.py:run_command:129 | [Matching] Mean Pressure Bias   : +7.83 hPa
2026-08-10 22:59:50.496 | DEBUG    | waid_03_1_match_datasets.py:perform_matching_with_ecowitt:188 | Mean Humidity Bias   : -7.34 %
2026-08-10 22:59:50.497 | DEBUG    | waid_orchestrate.py:run_command:129 | [Matching] Mean Humidity Bias   : -7.34 %
2026-08-10 22:59:50.497 | DEBUG    | waid_03_1_match_datasets.py:perform_matching_with_ecowitt:189 | Mean Wind Speed Bias : -2.91 m/s
2026-08-10 22:59:50.498 | DEBUG    | waid_orchestrate.py:run_command:129 | [Matching] Mean Wind Speed Bias : -2.91 m/s
2026-08-10 22:59:50.498 | DEBUG    | waid_03_1_match_datasets.py:perform_matching_with_ecowitt:190 | Mean Solar Rad Bias  : -212.46 W/m2
2026-08-10 22:59:50.498 | DEBUG    | waid_orchestrate.py:run_command:129 | [Matching] Mean Solar Rad Bias  : -212.46 W/m2
2026-08-10 22:59:50.499 | DEBUG    | waid_03_1_match_datasets.py:perform_matching_with_ecowitt:191 | Mean Hourly Rain Bias: -0.00 mm
2026-08-10 22:59:50.499 | DEBUG    | waid_orchestrate.py:run_command:129 | [Matching] Mean Hourly Rain Bias: -0.00 mm
2026-08-10 22:59:50.513 | SUCCESS  | waid_03_1_match_datasets.py:perform_matching_with_ecowitt:197 | Monthly checkpoint saved to CSV: matched_2026-08.csv
2026-08-10 22:59:50.513 | INFO     | waid_03_1_match_datasets.py:perform_matching_with_era5:283 | Synchronizing aligned dataset into Feature Store: match_records
2026-08-10 22:59:50.513 | INFO     | waid_orchestrate.py:run_command:129 | [Matching] Monthly checkpoint saved to CSV: matched_2026-08.csv
2026-08-10 22:59:50.514 | INFO     | waid_orchestrate.py:run_command:129 | [Matching] Synchronizing aligned dataset into Feature Store: match_records
2026-08-10 22:59:50.663 | WARNING  | waid_03_1_match_datasets.py:perform_matching_with_era5:303 | Cleared 236 overlapping historical rows from match_records.
2026-08-10 22:59:50.663 | WARNING  | waid_orchestrate.py:run_command:129 | [Matching] Cleared 236 overlapping historical rows from match_records.
2026-08-10 22:59:51.140 | SUCCESS  | waid_03_1_match_datasets.py:perform_matching_with_era5:337 | Feature Store table 'match_records' updated! Inserted 237 synchronized records.
2026-08-10 22:59:51.141 | INFO     | waid_orchestrate.py:run_command:129 | [Matching] Feature Store table 'match_records' updated! Inserted 237 synchronized records.
2026-08-10 22:59:51.425 | INFO     | waid_orchestrate.py:waid_03_2_dbt_matches:244 | Bias Calculation (Discrepancy Analysis)
2026-08-10 22:59:51.425 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [3, 2] - Period: 2026-08
2026-08-10 22:59:51.426 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_03_2_dbt_matches
2026-08-10 22:59:51.426 | DEBUG    | waid_orchestrate.py:run_command:89 | dbt run --select source:external_raw.match_records --target dev --vars {"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}
2026-08-10 22:59:51.426 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: dbt-run ---
2026-08-10 22:59:54.129 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:54  Running with dbt=1.11.12
2026-08-10 22:59:54.586 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:54  Registered adapter: sqlite=1.10.0
2026-08-10 22:59:55.428 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:55  Found 9 models, 19 data tests, 4 sources, 533 macros
2026-08-10 22:59:55.432 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 20:59:55  Nothing to do. Try checking your model configs and model specification args
2026-08-10 22:59:56.568 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [3, 2]
2026-08-10 22:59:56.568 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_03_2_dbt_matches
2026-08-10 22:59:56.569 | DEBUG    | waid_orchestrate.py:run_command:89 | dbt test --select source:external_raw.match_records --target dev --vars {"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}
2026-08-10 22:59:56.569 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: dbt-test ---
2026-08-10 22:59:59.270 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:59  Running with dbt=1.11.12
2026-08-10 22:59:59.764 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 20:59:59  Registered adapter: sqlite=1.10.0
2026-08-10 23:00:00.619 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:00  Found 9 models, 19 data tests, 4 sources, 533 macros
2026-08-10 23:00:00.623 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:00  Nothing to do. Try checking your model configs and model specification args
2026-08-10 23:00:01.677 | INFO     | waid_orchestrate.py:waid_03_3_dbt_matches_bias:260 | Bias Calculation (Discrepancy Analysis)
2026-08-10 23:00:01.677 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [3, 3] - Period: 2026-08
2026-08-10 23:00:01.678 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_03_3_dbt_matches_bias
2026-08-10 23:00:01.678 | DEBUG    | waid_orchestrate.py:run_command:89 | dbt run --select int_matches_bias --target dev --vars {"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}
2026-08-10 23:00:01.678 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: dbt-run ---
2026-08-10 23:00:04.405 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:04  Running with dbt=1.11.12
2026-08-10 23:00:04.856 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:04  Registered adapter: sqlite=1.10.0
2026-08-10 23:00:05.671 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:05  Found 9 models, 19 data tests, 4 sources, 533 macros
2026-08-10 23:00:05.675 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:05
2026-08-10 23:00:05.676 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:05  Concurrency: 1 threads (target='dev')
2026-08-10 23:00:05.677 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:05
2026-08-10 23:00:05.839 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:05  1 of 1 START sql table model main.int_matches_bias ............................. [RUN]
2026-08-10 23:00:07.769 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:07  1 of 1 OK created sql table model main.int_matches_bias ........................ [OK in 1.93s]
2026-08-10 23:00:07.790 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:07
2026-08-10 23:00:07.791 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:07  Finished running 1 table model in 0 hours 0 minutes and 2.11 seconds (2.11s).
2026-08-10 23:00:07.884 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:07
2026-08-10 23:00:07.885 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:07  Completed successfully
2026-08-10 23:00:07.886 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:07
2026-08-10 23:00:07.887 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:07  Done. PASS=1 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=1
2026-08-10 23:00:08.834 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [3, 3] - Period: 2026-08
2026-08-10 23:00:08.835 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_03_3_dbt_matches_bias
2026-08-10 23:00:08.835 | DEBUG    | waid_orchestrate.py:run_command:89 | dbt test --select int_matches_bias --target dev --vars {"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}
2026-08-10 23:00:08.835 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: dbt-test ---
2026-08-10 23:00:11.544 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:11  Running with dbt=1.11.12
2026-08-10 23:00:12.179 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:12  Registered adapter: sqlite=1.10.0
2026-08-10 23:00:13.062 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:13  Found 9 models, 19 data tests, 4 sources, 533 macros
2026-08-10 23:00:13.066 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:13
2026-08-10 23:00:13.067 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:13  Concurrency: 1 threads (target='dev')
2026-08-10 23:00:13.068 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:13
2026-08-10 23:00:13.216 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:13  1 of 5 START test dbt_utils_accepted_range_int_matches_bias_bias_pres__30_0___30_0  [RUN]
2026-08-10 23:00:13.312 | SUCCESS  | waid_orchestrate.py:run_command:123 | [dbt-test] 21:00:13  1 of 5 PASS dbt_utils_accepted_range_int_matches_bias_bias_pres__30_0___30_0 ... [PASS in 0.09s]
2026-08-10 23:00:13.316 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:13  2 of 5 START test dbt_utils_accepted_range_int_matches_bias_bias_temp__15_0___15_0  [RUN]
2026-08-10 23:00:13.352 | SUCCESS  | waid_orchestrate.py:run_command:123 | [dbt-test] 21:00:13  2 of 5 PASS dbt_utils_accepted_range_int_matches_bias_bias_temp__15_0___15_0 ... [PASS in 0.03s]
2026-08-10 23:00:13.355 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:13  3 of 5 START test int_matches_bias_min_rows .................................... [RUN]
2026-08-10 23:00:13.383 | SUCCESS  | waid_orchestrate.py:run_command:123 | [dbt-test] 21:00:13  3 of 5 PASS int_matches_bias_min_rows .......................................... [PASS in 0.03s]
2026-08-10 23:00:13.387 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:13  4 of 5 START test not_null_int_matches_bias_timestamp .......................... [RUN]
2026-08-10 23:00:13.424 | SUCCESS  | waid_orchestrate.py:run_command:123 | [dbt-test] 21:00:13  4 of 5 PASS not_null_int_matches_bias_timestamp ................................ [PASS in 0.04s]
2026-08-10 23:00:13.429 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:13  5 of 5 START test unique_int_matches_bias_timestamp ............................ [RUN]
2026-08-10 23:00:13.468 | SUCCESS  | waid_orchestrate.py:run_command:123 | [dbt-test] 21:00:13  5 of 5 PASS unique_int_matches_bias_timestamp .................................. [PASS in 0.04s]
2026-08-10 23:00:13.492 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:13
2026-08-10 23:00:13.493 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:13  Finished running 5 data tests in 0 hours 0 minutes and 0.42 seconds (0.42s).
2026-08-10 23:00:13.581 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:13
2026-08-10 23:00:13.582 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:13  Completed successfully
2026-08-10 23:00:13.583 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:13
2026-08-10 23:00:13.584 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-test] 21:00:13  Done. PASS=5 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=5
2026-08-10 23:00:14.550 | DEBUG    | waid_orchestrate.py:run_step_sequence:424 | Executing debug step: debug_waid_analyze_bias
2026-08-10 23:00:14.550 | INFO     | waid_orchestrate.py:debug_waid_analyze_bias:276 | Report matching between Ecowitt and ERA5 data
2026-08-10 23:00:14.551 | INFO     | waid_orchestrate.py:run_command:88 | Request from: debug_waid_analyze_bias
2026-08-10 23:00:14.552 | DEBUG    | waid_orchestrate.py:run_command:89 | python /home/alex/waid/src/utils/waid_analyze_bias.py --period 2026-08
2026-08-10 23:00:14.552 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: Profiling ---
2026-08-10 23:00:15.613 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:381 - Boot WAID pipeline...
2026-08-10 23:00:15.801 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:407 - WAID_VERSION = '1.0.0' (configuration source: waid.env)
2026-08-10 23:00:15.817 | DEBUG    | boot.py:<module>:427 | Debugging successfully activated
2026-08-10 23:00:15.817 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Debugging successfully activated
2026-08-10 23:00:15.875 | DEBUG    | waid_analyze_bias.py:report_bias_metrics:50 | ==============================================================
2026-08-10 23:00:15.876 | DEBUG    | waid_analyze_bias.py:report_bias_metrics:51 | BIAS REPORT
2026-08-10 23:00:15.876 | DEBUG    | waid_analyze_bias.py:report_bias_metrics:52 | ==============================================================
2026-08-10 23:00:15.876 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] ==============================================================
2026-08-10 23:00:15.876 | DEBUG    | waid_analyze_bias.py:report_bias_metrics:53 | Period : 2026-08
2026-08-10 23:00:15.876 | DEBUG    | waid_analyze_bias.py:report_bias_metrics:54 | Samples: 237
2026-08-10 23:00:15.876 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] BIAS REPORT
2026-08-10 23:00:15.877 | DEBUG    | waid_analyze_bias.py:report_bias_metrics:55 | 
2026-08-10 23:00:15.877 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] ==============================================================
2026-08-10 23:00:15.877 | DEBUG    | waid_analyze_bias.py:report_bias_metrics:57 | Feature           Unit            Mean     Std Dev       Min       Max
2026-08-10 23:00:15.877 | DEBUG    | waid_analyze_bias.py:report_bias_metrics:65 | --------------------------------------------------------------
2026-08-10 23:00:15.877 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Period : 2026-08
2026-08-10 23:00:15.877 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Samples: 237
2026-08-10 23:00:15.878 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] 
2026-08-10 23:00:15.878 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Feature           Unit            Mean     Std Dev       Min       Max
2026-08-10 23:00:15.879 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] --------------------------------------------------------------
2026-08-10 23:00:15.881 | DEBUG    | waid_analyze_bias.py:report_bias_metrics:72 | Temperature       °C              1.49        3.13     -5.30      6.11
2026-08-10 23:00:15.881 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Temperature       °C              1.49        3.13     -5.30      6.11
2026-08-10 23:00:15.882 | DEBUG    | waid_analyze_bias.py:report_bias_metrics:72 | Pressure          hPa             7.83        0.61      5.92      9.25
2026-08-10 23:00:15.882 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Pressure          hPa             7.83        0.61      5.92      9.25
2026-08-10 23:00:15.883 | DEBUG    | waid_analyze_bias.py:report_bias_metrics:72 | Humidity          %              -7.34       11.26    -30.31     10.15
2026-08-10 23:00:15.884 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Humidity          %              -7.34       11.26    -30.31     10.15
2026-08-10 23:00:15.884 | DEBUG    | waid_analyze_bias.py:report_bias_metrics:72 | Wind speed        m/s            -2.91        1.02     -4.64     -0.71
2026-08-10 23:00:15.885 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Wind speed        m/s            -2.91        1.02     -4.64     -0.71
2026-08-10 23:00:15.885 | DEBUG    | waid_analyze_bias.py:report_bias_metrics:72 | Solar radiation   W/m²         -212.46      268.35   -812.64    155.08
2026-08-10 23:00:15.886 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Solar radiation   W/m²         -212.46      268.35   -812.64    155.08
2026-08-10 23:00:15.887 | DEBUG    | waid_analyze_bias.py:report_bias_metrics:72 | Hourly rain       mm             -0.00        0.05     -0.20      0.50
2026-08-10 23:00:15.887 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Hourly rain       mm             -0.00        0.05     -0.20      0.50
2026-08-10 23:00:16.052 | INFO     | waid_orchestrate.py:waid_04_1_setup_metadata:285 | Setting up station metadata
2026-08-10 23:00:16.052 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [4, 1]
2026-08-10 23:00:16.052 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_04_1_setup_metadata
2026-08-10 23:00:16.053 | DEBUG    | waid_orchestrate.py:run_command:89 | dbt run --select station_metadata --full-refresh --target dev --vars {"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}
2026-08-10 23:00:16.053 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: dbt-run ---
2026-08-10 23:00:18.723 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:18  Running with dbt=1.11.12
2026-08-10 23:00:19.176 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:19  Registered adapter: sqlite=1.10.0
2026-08-10 23:00:20.020 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:20  Found 9 models, 19 data tests, 4 sources, 533 macros
2026-08-10 23:00:20.025 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:20
2026-08-10 23:00:20.025 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:20  Concurrency: 1 threads (target='dev')
2026-08-10 23:00:20.026 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:20
2026-08-10 23:00:20.193 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:20  1 of 1 START sql table model main.station_metadata ............................. [RUN]
2026-08-10 23:00:20.305 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:20  1 of 1 OK created sql table model main.station_metadata ........................ [OK in 0.11s]
2026-08-10 23:00:20.324 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:20
2026-08-10 23:00:20.326 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:20  Finished running 1 table model in 0 hours 0 minutes and 0.30 seconds (0.30s).
2026-08-10 23:00:20.407 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:20
2026-08-10 23:00:20.408 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:20  Completed successfully
2026-08-10 23:00:20.409 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:20
2026-08-10 23:00:20.410 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:00:20  Done. PASS=1 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=1
2026-08-10 23:00:21.370 | INFO     | waid_orchestrate.py:waid_04_1_setup_metadata:293 | Setting up sensor specifications
2026-08-10 23:00:21.371 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [4, 1] - Period: 2026-08
2026-08-10 23:00:21.372 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_04_1_setup_metadata
2026-08-10 23:00:21.372 | DEBUG    | waid_orchestrate.py:run_command:89 | python /home/alex/waid/src/waid_04_1_setup_specs.py --period 2026-08
2026-08-10 23:00:21.373 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: Profiling ---
2026-08-10 23:00:22.483 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:381 - Boot WAID pipeline...
2026-08-10 23:00:22.828 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:407 - WAID_VERSION = '1.0.0' (configuration source: waid.env)
2026-08-10 23:00:22.846 | DEBUG    | boot.py:<module>:427 | Debugging successfully activated
2026-08-10 23:00:22.846 | INFO     | waid_04_1_setup_specs.py:main:127 | Initializing station sensor specifications setup...
2026-08-10 23:00:22.846 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Debugging successfully activated
2026-08-10 23:00:22.847 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Initializing station sensor specifications setup...
2026-08-10 23:00:22.891 | INFO     | waid_04_1_setup_specs.py:ensure_sensor_specs_column:36 | Adding 'sensor_specs' column to 'station_metadata' table...
2026-08-10 23:00:22.891 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Adding 'sensor_specs' column to 'station_metadata' table...
2026-08-10 23:00:23.019 | SUCCESS  | waid_04_1_setup_specs.py:ensure_sensor_specs_column:39 | Column 'sensor_specs' added successfully.
2026-08-10 23:00:23.019 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Column 'sensor_specs' added successfully.
2026-08-10 23:00:23.285 | SUCCESS  | waid_04_1_setup_specs.py:profile_or_default_specs:100 | Empirically profiled sensor specs: {'ecowitt_temp': {'resolution': 0.1, 'deadband': 0.0}, 'ecowitt_rh': {'resolution': 1.0, 'deadband': 0.0}, 'ecowitt_pres': {'resolution': 0.1, 'deadband': 0.0}, 'ecowitt_wind': {'resolution': 0.1, 'deadband': 0.1}, 'ecowitt_solar': {'resolution': 0.11, 'deadband': 0.0}, 'ecowitt_rain': {'resolution': 0.2, 'deadband': 0.2}}
2026-08-10 23:00:23.285 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Empirically profiled sensor specs: {'ecowitt_temp': {'resolution': 0.1, 'deadband': 0.0}, 'ecowitt_rh': {'resolution': 1.0, 'deadband': 0.0}, 'ecowitt_pres': {'resolution': 0.1, 'deadband': 0.0}, 'ecowitt_wind': {'resolution': 0.1, 'deadband': 0.1}, 'ecowitt_solar': {'resolution': 0.11, 'deadband': 0.0}, 'ecowitt_rain': {'resolution': 0.2, 'deadband': 0.2}}
2026-08-10 23:00:23.368 | SUCCESS  | waid_04_1_setup_specs.py:update_station_specs:120 | Station metadata successfully updated with sensor specs for station 'STATION_01'.
2026-08-10 23:00:23.369 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Station metadata successfully updated with sensor specs for station 'STATION_01'.
2026-08-10 23:00:23.559 | INFO     | waid_orchestrate.py:waid_05_1_ml_tensors:302 | Generating ML Tensors
2026-08-10 23:00:23.559 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [5, 1] - Period: 2026-08
2026-08-10 23:00:23.559 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_05_1_ml_tensors
2026-08-10 23:00:23.560 | DEBUG    | waid_orchestrate.py:run_command:89 | python /home/alex/waid/src/waid_05_1_ml_tensors.py --period 2026-08
2026-08-10 23:00:23.560 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: Profiling ---
2026-08-10 23:00:24.670 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:381 - Boot WAID pipeline...
2026-08-10 23:00:24.869 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:407 - WAID_VERSION = '1.0.0' (configuration source: waid.env)
2026-08-10 23:00:24.884 | DEBUG    | boot.py:<module>:427 | Debugging successfully activated
2026-08-10 23:00:24.884 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Debugging successfully activated
2026-08-10 23:00:25.910 | DEBUG    | waid_orchestrate.py:run_step_sequence:433 | NO extra arguments passed to step 'waid_05_2_ml_train' (expects only runner)
2026-08-10 23:00:25.910 | INFO     | waid_orchestrate.py:waid_05_2_ml_train:315 | Training ML Model
2026-08-10 23:00:25.911 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [5, 2]
2026-08-10 23:00:25.911 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_05_2_ml_train
2026-08-10 23:00:25.911 | DEBUG    | waid_orchestrate.py:run_command:89 | python /home/alex/waid/src/waid_05_2_ml_train.py
2026-08-10 23:00:25.912 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: Profiling ---
2026-08-10 23:00:29.631 | WARNING  | waid_orchestrate.py:run_command:129 | [Profiling] WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
2026-08-10 23:00:29.631 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] I0000 00:00:1786395629.631060    4254 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
2026-08-10 23:00:31.453 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] I0000 00:00:1786395631.453347    4254 cpu_feature_guard.cc:227] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
2026-08-10 23:00:31.453 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] To enable the following instructions: AVX2 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
2026-08-10 23:00:36.794 | WARNING  | waid_orchestrate.py:run_command:129 | [Profiling] WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
2026-08-10 23:00:36.794 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] I0000 00:00:1786395636.794237    4254 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
2026-08-10 23:00:57.319 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:381 - Boot WAID pipeline...
2026-08-10 23:00:57.514 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:407 - WAID_VERSION = '1.0.0' (configuration source: waid.env)
2026-08-10 23:00:57.528 | DEBUG    | boot.py:<module>:427 | Debugging successfully activated
2026-08-10 23:00:57.528 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Debugging successfully activated
2026-08-10 23:00:57.530 | WARNING  | waid_05_2_ml_train.py:main:426 | No hardware GPU detected: Training will proceed on CPU.
2026-08-10 23:00:57.530 | INFO     | waid_orchestrate.py:run_command:125 | [Profiling] E0000 00:00:1786395657.530306    4254 cuda_platform.cc:52] failed call to cuInit: INTERNAL: CUDA error: Failed call to cuInit: UNKNOWN ERROR (303)
2026-08-10 23:00:57.530 | WARNING  | waid_orchestrate.py:run_command:129 | [Profiling] No hardware GPU detected: Training will proceed on CPU.
2026-08-10 23:00:57.567 | INFO     | waid_utils.py:get_station_metadata:176 | Loaded Station Metadata from DB: 'Local Home Weather Station' (STATION_01) | Elevation: 6m | Guardrails: Min Days=14, Retrain Window=30
2026-08-10 23:00:57.567 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Guardrails: Min Days=14, Retrain Window=30
2026-08-10 23:00:57.611 | INFO     | waid_05_2_ml_train.py:get_available_periods:412 | Detected period datasets: ['2025_11', '2025_12', '2026_01', '2026_02', '2026_03', '2026_04', '2026_05', '2026_06', '2026_07', '2026_08']
2026-08-10 23:00:57.611 | INFO     | waid_05_2_ml_train.py:check_retrain_required:107 | Checking ML model registry status for Station: 'Local Home Weather Station' (STATION_01)...
2026-08-10 23:00:57.611 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Detected period datasets: ['2025_11', '2025_12', '2026_01', '2026_02', '2026_03', '2026_04', '2026_05', '2026_06', '2026_07', '2026_08']
2026-08-10 23:00:57.612 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Checking ML model registry status for Station: 'Local Home Weather Station' (STATION_01)...
2026-08-10 23:00:57.663 | INFO     | waid_05_2_ml_train.py:check_retrain_required:129 | Last model trained at: [2026-08-09 12:38:22] (1 days ago)
2026-08-10 23:00:57.664 | INFO     | waid_05_2_ml_train.py:check_retrain_required:130 | Minimum training interval / days guardrail: [14] days
2026-08-10 23:00:57.663 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] /home/alex/waid/src/waid_05_2_ml_train.py:127: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
2026-08-10 23:00:57.664 | SUCCESS  | waid_05_2_ml_train.py:check_retrain_required:134 | Retraining skipped: Only 1 days passed since last training, which is less than the required minimum interval of 14 days.
2026-08-10 23:00:57.664 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] days_since_last_training = (datetime.utcnow() - last_trained_at).days
2026-08-10 23:00:57.664 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Last model trained at: [2026-08-09 12:38:22] (1 days ago)
2026-08-10 23:00:57.664 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Minimum training interval / days guardrail: [14] days
2026-08-10 23:00:57.665 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Retraining skipped: Only 1 days passed since last training, which is less than the required minimum interval of 14 days.
2026-08-10 23:00:58.677 | DEBUG    | waid_orchestrate.py:run_step_sequence:433 | NO extra arguments passed to step 'waid_06_1_inference_engine' (expects only runner)
2026-08-10 23:00:58.678 | INFO     | waid_orchestrate.py:waid_06_1_inference_engine:324 | Executing inference
2026-08-10 23:00:58.678 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [6, 1]
2026-08-10 23:00:58.679 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_06_1_inference_engine
2026-08-10 23:00:58.679 | DEBUG    | waid_orchestrate.py:run_command:89 | python /home/alex/waid/src/waid_06_1_inference_engine.py
2026-08-10 23:00:58.679 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: Profiling ---
2026-08-10 23:00:59.994 | WARNING  | waid_orchestrate.py:run_command:129 | [Profiling] WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
2026-08-10 23:00:59.995 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] I0000 00:00:1786395659.994709    4352 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
2026-08-10 23:01:00.098 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] I0000 00:00:1786395660.098046    4352 cpu_feature_guard.cc:227] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
2026-08-10 23:01:00.098 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] To enable the following instructions: AVX2 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
2026-08-10 23:01:02.298 | WARNING  | waid_orchestrate.py:run_command:129 | [Profiling] WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
2026-08-10 23:01:02.298 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] I0000 00:00:1786395662.298099    4352 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
2026-08-10 23:01:03.899 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:381 - Boot WAID pipeline...
2026-08-10 23:01:04.092 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:407 - WAID_VERSION = '1.0.0' (configuration source: waid.env)
2026-08-10 23:01:04.106 | DEBUG    | boot.py:<module>:427 | Debugging successfully activated
2026-08-10 23:01:04.107 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Debugging successfully activated
2026-08-10 23:01:04.107 | WARNING  | waid_06_1_inference_engine.py:main:308 | Inference script is running with GPU disabled. Ensure this is intended.
2026-08-10 23:01:04.108 | INFO     | waid_06_1_inference_engine.py:__init__:66 | Starting inference process...
2026-08-10 23:01:04.107 | WARNING  | waid_orchestrate.py:run_command:129 | [Profiling] Inference script is running with GPU disabled. Ensure this is intended.
2026-08-10 23:01:04.108 | INFO     | waid_06_1_inference_engine.py:__init__:67 | Using model: /home/alex/waid/data/models/weather_model_full.h5
2026-08-10 23:01:04.108 | INFO     | waid_06_1_inference_engine.py:__init__:68 | Using X scaler: /home/alex/waid/data/models/weather_x_scaler_full.pkl
2026-08-10 23:01:04.108 | INFO     | waid_06_1_inference_engine.py:__init__:69 | Using Y scaler: /home/alex/waid/data/models/weather_y_scaler_full.pkl
2026-08-10 23:01:04.108 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Starting inference process...
2026-08-10 23:01:04.109 | INFO     | waid_06_1_inference_engine.py:__init__:70 | Using DB: /home/alex/waid/data/waid.db
2026-08-10 23:01:04.109 | INFO     | waid_06_1_inference_engine.py:__init__:71 | Saving predictions to: /home/alex/waid/data/waid.db
2026-08-10 23:01:04.109 | INFO     | waid_06_1_inference_engine.py:__init__:72 | All configurations initialized.
2026-08-10 23:01:04.109 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Using model: /home/alex/waid/data/models/weather_model_full.h5
2026-08-10 23:01:04.109 | INFO     | waid_06_1_inference_engine.py:run_inference:272 | Starting pipeline execution: Validation and System Health Check...
2026-08-10 23:01:04.109 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Using X scaler: /home/alex/waid/data/models/weather_x_scaler_full.pkl
2026-08-10 23:01:04.110 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Using Y scaler: /home/alex/waid/data/models/weather_y_scaler_full.pkl
2026-08-10 23:01:04.110 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Using DB: /home/alex/waid/data/waid.db
2026-08-10 23:01:04.111 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Saving predictions to: /home/alex/waid/data/waid.db
2026-08-10 23:01:04.111 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] All configurations initialized.
2026-08-10 23:01:04.112 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Starting pipeline execution: Validation and System Health Check...
2026-08-10 23:01:04.164 | INFO     | waid_06_1_inference_engine.py:check_system_health:125 | System health check passed.
2026-08-10 23:01:04.164 | SUCCESS  | waid_06_1_inference_engine.py:run_inference:274 | System health check passed. Input data is fresh.
2026-08-10 23:01:04.164 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] System health check passed.
2026-08-10 23:01:04.164 | INFO     | waid_06_1_inference_engine.py:run_inference:276 | Executing model forecasting engine...
2026-08-10 23:01:04.164 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] System health check passed. Input data is fresh.
2026-08-10 23:01:04.165 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Executing model forecasting engine...
2026-08-10 23:01:04.232 | INFO     | waid_orchestrate.py:run_command:125 | [Profiling] E0000 00:00:1786395664.232057    4352 cuda_platform.cc:52] failed call to cuInit: INTERNAL: CUDA error: Failed call to cuInit: UNKNOWN ERROR (303)
2026-08-10 23:01:04.515 | DEBUG    | waid_06_1_inference_engine.py:prepare_and_predict:226 | Physics Guardrail - Inference - Theoretical Solar Radiation Stats for current window:
2026-08-10 23:01:04.515 | DEBUG    | waid_06_1_inference_engine.py:prepare_and_predict:227 |   - Window Timestamp Range: [2026-08-10 20:57:00 to 2026-08-10 20:34:00]
2026-08-10 23:01:04.515 | DEBUG    | waid_06_1_inference_engine.py:prepare_and_predict:228 |   - Solar Range: Min=18.24 W/m², Max=80.07 W/m²
2026-08-10 23:01:04.515 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Physics Guardrail - Inference - Theoretical Solar Radiation Stats for current window:
2026-08-10 23:01:04.515 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] - Window Timestamp Range: [2026-08-10 20:57:00 to 2026-08-10 20:34:00]
2026-08-10 23:01:04.516 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] - Solar Range: Min=18.24 W/m², Max=80.07 W/m²
2026-08-10 23:01:04.949 | INFO     | waid_06_1_inference_engine.py:prepare_and_predict:265 | Inference completed and reconstructed. Model: weather_model_full.h5
2026-08-10 23:01:04.949 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Inference completed and reconstructed. Model: weather_model_full.h5
2026-08-10 23:01:04.951 | INFO     | waid_06_1_inference_engine.py:run_inference:281 | Checking database structure and running schema evolution check...
2026-08-10 23:01:04.951 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Checking database structure and running schema evolution check...
2026-08-10 23:01:04.989 | WARNING  | waid_06_1_inference_engine.py:ensure_db_structure:157 | Schema mismatch detected. Rebuilding table...
2026-08-10 23:01:04.989 | WARNING  | waid_orchestrate.py:run_command:129 | [Profiling] Schema mismatch detected. Rebuilding table...
2026-08-10 23:01:05.066 | INFO     | waid_06_1_inference_engine.py:ensure_db_structure:161 | Table successfully reconstructed.
2026-08-10 23:01:05.067 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Table successfully reconstructed.
2026-08-10 23:01:05.077 | DEBUG    | waid_06_1_inference_engine.py:ensure_db_structure:167 | Database schema synchronization completed successfully.
2026-08-10 23:01:05.078 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Database schema synchronization completed successfully.
2026-08-10 23:01:05.081 | INFO     | waid_06_1_inference_engine.py:run_inference:288 | Saving predictions to database target table...
2026-08-10 23:01:05.081 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Saving predictions to database target table...
2026-08-10 23:01:05.199 | INFO     | waid_06_1_inference_engine.py:run_inference:300 | Inference records saved to /home/alex/waid/data/waid.db (Model Version: e4da724e)
2026-08-10 23:01:05.199 | SUCCESS  | waid_06_1_inference_engine.py:run_inference:301 | Inference process successfully completed and finalized.
2026-08-10 23:01:05.199 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Inference records saved to /home/alex/waid/data/waid.db (Model Version: e4da724e)
2026-08-10 23:01:05.200 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Inference process successfully completed and finalized.
2026-08-10 23:01:06.346 | DEBUG    | waid_orchestrate.py:run_step_sequence:433 | NO extra arguments passed to step 'waid_06_2_inference_stats' (expects only runner)
2026-08-10 23:01:06.347 | INFO     | waid_orchestrate.py:waid_06_2_inference_stats:333 | Updating inference statistics parameters
2026-08-10 23:01:06.347 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [6, 2]
2026-08-10 23:01:06.348 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_06_2_inference_stats
2026-08-10 23:01:06.348 | DEBUG    | waid_orchestrate.py:run_command:89 | dbt run --select inference_stats --target dev --vars {"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}
2026-08-10 23:01:06.348 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: dbt-run ---
2026-08-10 23:01:09.149 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:09  Running with dbt=1.11.12
2026-08-10 23:01:09.608 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:09  Registered adapter: sqlite=1.10.0
2026-08-10 23:01:10.408 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:10  Found 9 models, 19 data tests, 4 sources, 533 macros
2026-08-10 23:01:10.413 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:10
2026-08-10 23:01:10.414 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:10  Concurrency: 1 threads (target='dev')
2026-08-10 23:01:10.415 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:10
2026-08-10 23:01:10.574 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:10  1 of 1 START sql table model main.inference_stats .............................. [RUN]
2026-08-10 23:01:10.698 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:10  1 of 1 OK created sql table model main.inference_stats ......................... [OK in 0.12s]
2026-08-10 23:01:10.718 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:10
2026-08-10 23:01:10.720 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:10  Finished running 1 table model in 0 hours 0 minutes and 0.30 seconds (0.30s).
2026-08-10 23:01:10.800 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:10
2026-08-10 23:01:10.801 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:10  Completed successfully
2026-08-10 23:01:10.801 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:10
2026-08-10 23:01:10.802 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:10  Done. PASS=1 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=1
2026-08-10 23:01:11.818 | DEBUG    | waid_orchestrate.py:run_step_sequence:433 | NO extra arguments passed to step 'waid_06_3_inference_prediction' (expects only runner)
2026-08-10 23:01:11.819 | INFO     | waid_orchestrate.py:waid_06_3_inference_prediction:342 | Performing inference prediction
2026-08-10 23:01:11.819 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [6, 3]
2026-08-10 23:01:11.820 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_06_3_inference_prediction
2026-08-10 23:01:11.820 | DEBUG    | waid_orchestrate.py:run_command:89 | dbt run --select inference_prediction --full-refresh --target dev --vars {"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}
2026-08-10 23:01:11.820 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: dbt-run ---
2026-08-10 23:01:14.484 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:14  Running with dbt=1.11.12
2026-08-10 23:01:14.926 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:14  Registered adapter: sqlite=1.10.0
2026-08-10 23:01:15.780 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:15  Found 9 models, 19 data tests, 4 sources, 533 macros
2026-08-10 23:01:15.784 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:15
2026-08-10 23:01:15.785 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:15  Concurrency: 1 threads (target='dev')
2026-08-10 23:01:15.786 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:15
2026-08-10 23:01:15.957 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:15  1 of 1 START sql incremental model main.inference_prediction ................... [RUN]
2026-08-10 23:01:16.130 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:16  1 of 1 OK created sql incremental model main.inference_prediction .............. [OK in 0.17s]
2026-08-10 23:01:16.153 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:16
2026-08-10 23:01:16.155 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:16  Finished running 1 incremental model in 0 hours 0 minutes and 0.37 seconds (0.37s).
2026-08-10 23:01:16.249 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:16
2026-08-10 23:01:16.251 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:16  Completed successfully
2026-08-10 23:01:16.252 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:16
2026-08-10 23:01:16.253 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:16  Done. PASS=1 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=1
2026-08-10 23:01:17.201 | DEBUG    | waid_orchestrate.py:run_step_sequence:433 | NO extra arguments passed to step 'waid_06_4_dbt_inference_quality' (expects only runner)
2026-08-10 23:01:17.201 | INFO     | waid_orchestrate.py:waid_06_4_dbt_inference_quality:351 | Updating inference quality metrics by Ecowitt
2026-08-10 23:01:17.202 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [6, 4]
2026-08-10 23:01:17.202 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_06_4_dbt_inference_quality
2026-08-10 23:01:17.202 | DEBUG    | waid_orchestrate.py:run_command:89 | dbt run --select +inference_quality --target dev --vars {"max_bias_temp": 3.0, "max_bias_pres": 15.0, "max_bias_rh": 30.0, "max_bias_wind": 2.0, "max_bias_solar": 50.0, "max_bias_rain": 2.0}
2026-08-10 23:01:17.203 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: dbt-run ---
2026-08-10 23:01:19.880 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:19  Running with dbt=1.11.12
2026-08-10 23:01:20.377 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:20  Registered adapter: sqlite=1.10.0
2026-08-10 23:01:21.202 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:21  Found 9 models, 19 data tests, 4 sources, 533 macros
2026-08-10 23:01:21.207 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:21
2026-08-10 23:01:21.208 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:21  Concurrency: 1 threads (target='dev')
2026-08-10 23:01:21.209 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:21
2026-08-10 23:01:21.353 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:21  1 of 4 START sql incremental model main.inference_prediction ................... [RUN]
2026-08-10 23:01:21.518 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:21  1 of 4 OK created sql incremental model main.inference_prediction .............. [OK in 0.16s]
2026-08-10 23:01:21.522 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:21  2 of 4 START sql table model main.int_matches_bias ............................. [RUN]
2026-08-10 23:01:22.142 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:22  2 of 4 OK created sql table model main.int_matches_bias ........................ [OK in 0.62s]
2026-08-10 23:01:22.148 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:22  3 of 4 START sql table model main.stg_ecowitt .................................. [RUN]
2026-08-10 23:01:26.900 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:26  3 of 4 OK created sql table model main.stg_ecowitt ............................. [OK in 4.75s]
2026-08-10 23:01:26.906 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:26  4 of 4 START sql incremental model main.inference_quality ...................... [RUN]
2026-08-10 23:01:27.078 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:27  4 of 4 OK created sql incremental model main.inference_quality ................. [OK in 0.17s]
2026-08-10 23:01:27.095 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:27
2026-08-10 23:01:27.096 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:27  Finished running 2 incremental models, 2 table models in 0 hours 0 minutes and 5.89 seconds (5.89s).
2026-08-10 23:01:27.190 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:27
2026-08-10 23:01:27.191 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:27  Completed successfully
2026-08-10 23:01:27.192 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:27
2026-08-10 23:01:27.193 | INFO     | waid_orchestrate.py:run_command:129 | [dbt-run] 21:01:27  Done. PASS=4 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=4
2026-08-10 23:01:28.212 | DEBUG    | waid_orchestrate.py:run_step_sequence:433 | NO extra arguments passed to step 'waid_06_5_inference_quality' (expects only runner)
2026-08-10 23:01:28.212 | INFO     | waid_orchestrate.py:waid_06_5_inference_quality:360 | Checking inference quality
2026-08-10 23:01:28.213 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [6, 5]
2026-08-10 23:01:28.213 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_06_5_inference_quality
2026-08-10 23:01:28.213 | DEBUG    | waid_orchestrate.py:run_command:89 | python /home/alex/waid/src/waid_06_5_inference_quality.py
2026-08-10 23:01:28.214 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: Profiling ---
2026-08-10 23:01:28.698 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:381 - Boot WAID pipeline...
2026-08-10 23:01:28.914 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:407 - WAID_VERSION = '1.0.0' (configuration source: waid.env)
2026-08-10 23:01:28.930 | DEBUG    | boot.py:<module>:427 | Debugging successfully activated
2026-08-10 23:01:28.930 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Debugging successfully activated
2026-08-10 23:01:28.931 | INFO     | waid_06_5_inference_quality.py:main:27 | Starting quality check using DB: /home/alex/waid/data/waid.db
2026-08-10 23:01:28.931 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Starting quality check using DB: /home/alex/waid/data/waid.db
2026-08-10 23:01:28.996 | INFO     | waid_06_5_inference_quality.py:main:41 | Total inference records found: 6
2026-08-10 23:01:28.996 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Total inference records found: 6
2026-08-10 23:01:29.021 | INFO     | waid_06_5_inference_quality.py:main:51 | Total quality benchmark records found: 0
2026-08-10 23:01:29.021 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Total quality benchmark records found: 0
2026-08-10 23:01:29.034 | SUCCESS  | waid_06_5_inference_quality.py:main:54 | Quality check completed successfully.
2026-08-10 23:01:29.034 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Quality check completed successfully.
2026-08-10 23:01:29.089 | DEBUG    | waid_orchestrate.py:run_step_sequence:433 | NO extra arguments passed to step 'waid_07_1_inference_forecast' (expects only runner)
2026-08-10 23:01:29.089 | INFO     | waid_orchestrate.py:waid_07_1_inference_forecast:369 | Checking 6h forecast inference quality
2026-08-10 23:01:29.090 | INFO     | waid_orchestrate.py:run_command:86 | 🔶 Step [7, 1]
2026-08-10 23:01:29.090 | INFO     | waid_orchestrate.py:run_command:88 | Request from: waid_07_1_inference_forecast
2026-08-10 23:01:29.090 | DEBUG    | waid_orchestrate.py:run_command:89 | python /home/alex/waid/src/waid_07_1_inference_forecast.py
2026-08-10 23:01:29.091 | INFO     | waid_orchestrate.py:run_command:90 | --- Context: Profiling ---
2026-08-10 23:01:30.397 | WARNING  | waid_orchestrate.py:run_command:129 | [Profiling] WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
2026-08-10 23:01:30.397 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] I0000 00:00:1786395690.397059    4556 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
2026-08-10 23:01:30.484 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] I0000 00:00:1786395690.484070    4556 cpu_feature_guard.cc:227] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
2026-08-10 23:01:30.484 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] To enable the following instructions: AVX2 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
2026-08-10 23:01:32.791 | WARNING  | waid_orchestrate.py:run_command:129 | [Profiling] WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
2026-08-10 23:01:32.791 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] I0000 00:00:1786395692.791121    4556 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
2026-08-10 23:01:34.418 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:381 - Boot WAID pipeline...
2026-08-10 23:01:34.613 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] boot:<module>:407 - WAID_VERSION = '1.0.0' (configuration source: waid.env)
2026-08-10 23:01:34.628 | DEBUG    | boot.py:<module>:427 | Debugging successfully activated
2026-08-10 23:01:34.628 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Debugging successfully activated
2026-08-10 23:01:34.629 | INFO     | waid_07_1_inference_forecast.py:main:360 | Initializing 6-hour weather inference and strict physics-safe guardrail pipeline...
2026-08-10 23:01:34.629 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Initializing 6-hour weather inference and strict physics-safe guardrail pipeline...
2026-08-10 23:01:34.664 | INFO     | waid_utils.py:get_station_metadata:176 | Loaded Station Metadata from DB: 'Local Home Weather Station' (STATION_01) | Elevation: 6m | Guardrails: Min Days=14, Retrain Window=30
2026-08-10 23:01:34.664 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Guardrails: Min Days=14, Retrain Window=30
2026-08-10 23:01:34.729 | INFO     | waid_orchestrate.py:run_command:125 | [Profiling] E0000 00:00:1786395694.729026    4556 cuda_platform.cc:52] failed call to cuInit: INTERNAL: CUDA error: Failed call to cuInit: UNKNOWN ERROR (303)
2026-08-10 23:01:34.883 | SUCCESS  | waid_07_1_inference_forecast.py:load_active_model_artifacts:66 | Active model and scalers loaded successfully.
2026-08-10 23:01:34.884 | INFO     | waid_utils.py:fetch_and_resample_ecowitt:66 | Connecting to Ecowitt Database: /home/alex/waid/data/waid.db
2026-08-10 23:01:34.884 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Active model and scalers loaded successfully.
2026-08-10 23:01:34.884 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Connecting to Ecowitt Database: /home/alex/waid/data/waid.db
2026-08-10 23:01:34.890 | INFO     | waid_utils.py:fetch_and_resample_ecowitt:71 | Querying Ecowitt DB for window: [2026-08-07 23:01:34] to [2026-08-10 23:01:34]
2026-08-10 23:01:34.890 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Querying Ecowitt DB for window: [2026-08-07 23:01:34] to [2026-08-10 23:01:34]
2026-08-10 23:01:34.969 | INFO     | waid_utils.py:fetch_and_resample_ecowitt:111 | Resampling local telemetry into 60min synchronized slots...
2026-08-10 23:01:34.969 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Resampling local telemetry into 60min synchronized slots...
2026-08-10 23:01:34.978 | INFO     | waid_utils.py:fetch_and_resample_ecowitt:130 | Applying bounded time interpolation (max threshold: 2h / 2 steps)...
2026-08-10 23:01:34.978 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Applying bounded time interpolation (max threshold: 2h / 2 steps)...
2026-08-10 23:01:34.994 | DEBUG    | waid_07_1_inference_forecast.py:build_inference_tensor:131 | Physics Guardrail - Forecast Input Tensor - Theoretical Solar Range: Min=0.00 W/m², Max=833.42 W/m²
2026-08-10 23:01:34.995 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Physics Guardrail - Forecast Input Tensor - Theoretical Solar Range: Min=0.00 W/m², Max=833.42 W/m²
2026-08-10 23:01:35.300 | INFO     | waid_07_1_inference_forecast.py:main:398 | Using strict target order for reconstruction: ['ecowitt_temp', 'ecowitt_rh', 'ecowitt_pres', 'ecowitt_wind', 'ecowitt_solar', 'ecowitt_rain']
2026-08-10 23:01:35.300 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Using strict target order for reconstruction: ['ecowitt_temp', 'ecowitt_rh', 'ecowitt_pres', 'ecowitt_wind', 'ecowitt_solar', 'ecowitt_rain']
2026-08-10 23:01:35.301 | INFO     | waid_07_1_inference_forecast.py:main:399 | Last Actual Telemetry Baseline:
{'ecowitt_temp': 27.28620689655172, 'ecowitt_rh': 34.62068965517241, 'ecowitt_pres': 1014.8689655172413, 'ecowitt_wind': 0.303448275862069, 'ecowitt_solar': 0.0, 'ecowitt_rain': 0.0}
2026-08-10 23:01:35.301 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Last Actual Telemetry Baseline:
2026-08-10 23:01:35.301 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] {'ecowitt_temp': 27.28620689655172, 'ecowitt_rh': 34.62068965517241, 'ecowitt_pres': 1014.8689655172413, 'ecowitt_wind': 0.303448275862069, 'ecowitt_solar': 0.0, 'ecowitt_rain': 0.0}
2026-08-10 23:01:35.303 | DEBUG    | waid_07_1_inference_forecast.py:apply_physics_guardrails:150 | Physics Guardrail - Forecast Guardrails - Future Theoretical Solar Range: Min=0.00 W/m², Max=0.00 W/m²
2026-08-10 23:01:35.304 | DEBUG    | waid_orchestrate.py:run_command:129 | [Profiling] Physics Guardrail - Forecast Guardrails - Future Theoretical Solar Range: Min=0.00 W/m², Max=0.00 W/m²
2026-08-10 23:01:35.424 | SUCCESS  | waid_07_1_inference_forecast.py:persist_and_update_inference_forecast:352 | Permanent inference_forecast table successfully updated for all 6 features with incremental predictions and consuntivo actuals.
2026-08-10 23:01:35.425 | SUCCESS  | waid_07_1_inference_forecast.py:main:418 | 6-hour absolute forecast outputs successfully generated, guarded, and stored.
2026-08-10 23:01:35.425 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] Permanent inference_forecast table successfully updated for all 6 features with incremental predictions and consuntivo actuals.
2026-08-10 23:01:35.425 | INFO     | waid_orchestrate.py:run_command:129 | [Profiling] 6-hour absolute forecast outputs successfully generated, guarded, and stored.
2026-08-10 23:01:36.465 | SUCCESS  | waid_orchestrate.py:main:639 | --- Pipeline successfully terminated ---
```