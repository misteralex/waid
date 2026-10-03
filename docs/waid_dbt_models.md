# 📊 WAID Data Architecture & Models Documentation

> Automatically generated report from dbt `manifest.json` and physical SQLite inspection.

---

## 🏗️ dbt Transform Models

### Model: `int_matches_bias`

**Schema:** `main`  
**Description:** Calculated operational bias between Ecowitt telemetry and ERA5 baseline.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| **timestamp** | `TEXT` | Hourly ISO timestamp (UTC) |
| **ecowitt_temp** | `UNKNOWN` |  |
| **era5_temp** | `UNKNOWN` |  |
| **bias_temp** | `UNKNOWN` | Temperature bias (Ecowitt - ERA5) in °C |
| **ecowitt_pres** | `UNKNOWN` |  |
| **era5_pres** | `UNKNOWN` |  |
| **bias_pres** | `UNKNOWN` | Pressure bias (Ecowitt - ERA5) in hPa |
| **ecowitt_rh** | `UNKNOWN` |  |
| **era5_rh** | `UNKNOWN` |  |
| **bias_rh** | `UNKNOWN` |  |
| **ecowitt_wind** | `UNKNOWN` |  |
| **era5_wind** | `UNKNOWN` |  |
| **bias_wind** | `UNKNOWN` |  |
| **ecowitt_solar** | `UNKNOWN` |  |
| **era5_solar** | `UNKNOWN` |  |
| **bias_solar** | `UNKNOWN` |  |
| **ecowitt_rain** | `UNKNOWN` |  |
| **era5_rain** | `UNKNOWN` |  |
| **bias_rain** | `UNKNOWN` |  |
| **bias_overflow_flag** | `UNKNOWN` |  |

---

### Model: `inference_stats`

**Schema:** `main`  
**Description:** Consensus statistics and uncertainty standard deviations per model version.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| **model_version** | `TEXT` |  |
| **model_version_tag** | `TEXT` |  |
| **avg_temp** | `REAL` |  |
| **std_temp** | `REAL` |  |
| **avg_pres** | `REAL` |  |
| **std_pres** | `REAL` |  |
| **avg_rh** | `REAL` |  |
| **std_rh** | `REAL` |  |
| **avg_wind** | `REAL` |  |
| **std_wind** | `REAL` |  |
| **avg_solar** | `REAL` |  |
| **std_solar** | `REAL` |  |
| **avg_rain** | `REAL` |  |
| **std_rain** | `REAL` |  |

---

### Model: `inference_quality`

**Schema:** `main`  
**Description:** Reconciliation model comparing predictions against actuals and ERA5 reanalysis.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| **timestamp** | `TIMESTAMP` |  |
| **model_version** | `TEXT` |  |
| **pred_temp** | `REAL` |  |
| **pred_pres** | `REAL` |  |
| **pred_rh** | `REAL` |  |
| **pred_wind** | `REAL` |  |
| **pred_solar** | `REAL` |  |
| **pred_rain** | `REAL` |  |
| **actual_temp** | `REAL` |  |
| **actual_pres** | `REAL` |  |
| **actual_rh** | `REAL` |  |
| **actual_wind** | `REAL` |  |
| **actual_solar** | `REAL` |  |
| **actual_rain** | `REAL` |  |
| **temp_era5** | `REAL` |  |
| **pres_era5** | `REAL` |  |
| **rh_era5** | `REAL` |  |
| **wind_era5** | `REAL` |  |
| **solar_era5** | `REAL` |  |
| **rain_era5** | `REAL` |  |
| **delta_temp** | `REAL` |  |
| **delta_pres** | `REAL` |  |
| **delta_rh** | `REAL` |  |
| **delta_wind** | `REAL` |  |
| **delta_solar** | `REAL` |  |
| **delta_rain** | `REAL` |  |
| **abs_error_temp** | `REAL` |  |
| **abs_error_pres** | `REAL` |  |
| **abs_error_rh** | `REAL` |  |
| **abs_error_wind** | `REAL` |  |
| **abs_error_solar** | `REAL` |  |
| **abs_error_rain** | `REAL` |  |
| **perc_error_temp** | `REAL` |  |
| **perc_error_pres** | `REAL` |  |
| **perc_error_rh** | `REAL` |  |
| **perc_error_wind** | `REAL` |  |
| **perc_error_solar** | `REAL` |  |
| **perc_error_rain** | `REAL` |  |

---

### Model: `station_metadata`

**Schema:** `main`  
**Description:** Physical metadata and training parameters for deployment stations.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| **station_id** | `TEXT` |  |
| **station_name** | `TEXT` |  |
| **latitude** | `REAL` |  |
| **longitude** | `REAL` |  |
| **elevation_m** | `REAL` |  |
| **height_above_ground_m** | `REAL` |  |
| **min_training_days** | `INT` |  |
| **retrain_window_days** | `INT` |  |
| **updated_at** | `TIMESTAMP` |  |
| **sensor_specs** | `TEXT` |  |

---

### Model: `stg_ecowitt`

**Schema:** `main`  
**Description:** 

| Column | Data Type | Description |
| :--- | :--- | :--- |
| **timestamp** | `None` |  |
| **temperature** | `None` |  |
| **pressure_hpa** | `None` |  |
| **humidity** | `None` |  |
| **wind_speed** | `None` |  |
| **solar_radiation** | `None` |  |
| **hourly_rain** | `None` |  |

---

### Model: `stg_matches`

**Schema:** `main`  
**Description:** Unified validation dataset comparing Ecowitt local sensor observations and ERA5 reanalysis.

| Column | Data Type | Description |
| :--- | :--- | :--- |
| **timestamp** | `None` |  |
| **ecowitt_temp** | `None` |  |
| **era5_temp** | `None` |  |
| **bias_temp** | `None` | Calculated bias (difference) between Ecowitt and ERA5 temperature measurements. |

---

## 🗄️ Physical SQLite Databases & Tables

> Inspected directly from local SQLite database files.

---

### 📁 Database File: `backup/waid_mock-20260819.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_forecast`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias** | `REAL` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |

#### Table: `inference_prediction`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |

#### Table: `inference_quality`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `ANY` | NO | - | NO |
| **pred_rain** | `ANY` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |
| **temp_era5** | `ANY` | NO | - | NO |
| **pres_era5** | `ANY` | NO | - | NO |
| **rh_era5** | `ANY` | NO | - | NO |
| **wind_era5** | `ANY` | NO | - | NO |
| **solar_era5** | `ANY` | NO | - | NO |
| **rain_era5** | `ANY` | NO | - | NO |
| **delta_temp** | `ANY` | NO | - | NO |
| **delta_pres** | `ANY` | NO | - | NO |
| **delta_rh** | `ANY` | NO | - | NO |
| **delta_wind** | `ANY` | NO | - | NO |
| **delta_solar** | `ANY` | NO | - | NO |
| **delta_rain** | `ANY` | NO | - | NO |
| **abs_error_temp** | `ANY` | NO | - | NO |
| **abs_error_pres** | `ANY` | NO | - | NO |
| **abs_error_rh** | `ANY` | NO | - | NO |
| **abs_error_wind** | `ANY` | NO | - | NO |
| **abs_error_solar** | `ANY` | NO | - | NO |
| **abs_error_rain** | `ANY` | NO | - | NO |
| **perc_error_temp** | `ANY` | NO | - | NO |
| **perc_error_pres** | `ANY` | NO | - | NO |
| **perc_error_rh** | `ANY` | NO | - | NO |
| **perc_error_wind** | `ANY` | NO | - | NO |
| **perc_error_solar** | `ANY` | NO | - | NO |
| **perc_error_rain** | `ANY` | NO | - | NO |

#### Table: `inference_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **id** | `INTEGER` | NO | - | YES |
| **ts_emission** | `DATETIME` | NO | CURRENT_TIMESTAMP | NO |
| **ts_window_start** | `DATETIME` | NO | - | NO |
| **ts_window_end** | `DATETIME` | NO | - | NO |
| **timestamp** | `DATETIME` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **n_features_used** | `INTEGER` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_stats`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **avg_temp** | `ANY` | NO | - | NO |
| **std_temp** | `ANY` | NO | - | NO |
| **avg_pres** | `ANY` | NO | - | NO |
| **std_pres** | `ANY` | NO | - | NO |
| **avg_rh** | `ANY` | NO | - | NO |
| **std_rh** | `ANY` | NO | - | NO |
| **avg_wind** | `ANY` | NO | - | NO |
| **std_wind** | `ANY` | NO | - | NO |
| **avg_solar** | `ANY` | NO | - | NO |
| **std_solar** | `ANY` | NO | - | NO |
| **avg_rain** | `ANY` | NO | - | NO |
| **std_rain** | `ANY` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |
| **sensor_specs** | `TEXT` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup-data-20260817/main_dbt_test__audit.db`

#### Table: `dbt_utils_accepted_range_stg_ecowitt_hourly_rain__300__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_humidity__100__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_pressure_hpa__1100__800`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_solar_radiation__1500__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_temperature__50___30`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_wind_speed__80__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `not_null_stg_ecowitt_timestamp`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `unique_stg_ecowitt_timestamp`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **unique_field** | `TEXT` | NO | - | NO |
| **n_records** | `ANY` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup-data-20260817/waid.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_forecast`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `ANY` | NO | - | NO |
| **diff_rh** | `ANY` | NO | - | NO |
| **historical_bias_temp** | `ANY` | NO | - | NO |
| **drift_vs_bias** | `ANY` | NO | - | NO |
| **created_at** | `ANY` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |

#### Table: `inference_prediction`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |

#### Table: `inference_quality`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `ANY` | NO | - | NO |
| **pred_rain** | `ANY` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |
| **temp_era5** | `ANY` | NO | - | NO |
| **pres_era5** | `ANY` | NO | - | NO |
| **rh_era5** | `ANY` | NO | - | NO |
| **wind_era5** | `ANY` | NO | - | NO |
| **solar_era5** | `ANY` | NO | - | NO |
| **rain_era5** | `ANY` | NO | - | NO |
| **delta_temp** | `ANY` | NO | - | NO |
| **delta_pres** | `ANY` | NO | - | NO |
| **delta_rh** | `ANY` | NO | - | NO |
| **delta_wind** | `ANY` | NO | - | NO |
| **delta_solar** | `ANY` | NO | - | NO |
| **delta_rain** | `ANY` | NO | - | NO |
| **abs_error_temp** | `ANY` | NO | - | NO |
| **abs_error_pres** | `ANY` | NO | - | NO |
| **abs_error_rh** | `ANY` | NO | - | NO |
| **abs_error_wind** | `ANY` | NO | - | NO |
| **abs_error_solar** | `ANY` | NO | - | NO |
| **abs_error_rain** | `ANY` | NO | - | NO |
| **perc_error_temp** | `ANY` | NO | - | NO |
| **perc_error_pres** | `ANY` | NO | - | NO |
| **perc_error_rh** | `ANY` | NO | - | NO |
| **perc_error_wind** | `ANY` | NO | - | NO |
| **perc_error_solar** | `ANY` | NO | - | NO |
| **perc_error_rain** | `ANY` | NO | - | NO |

#### Table: `inference_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **id** | `INTEGER` | NO | - | YES |
| **ts_emission** | `DATETIME` | NO | CURRENT_TIMESTAMP | NO |
| **ts_window_start** | `DATETIME` | NO | - | NO |
| **ts_window_end** | `DATETIME` | NO | - | NO |
| **timestamp** | `DATETIME` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **n_features_used** | `INTEGER` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_stats`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **avg_temp** | `ANY` | NO | - | NO |
| **std_temp** | `ANY` | NO | - | NO |
| **avg_pres** | `ANY` | NO | - | NO |
| **std_pres** | `ANY` | NO | - | NO |
| **avg_rh** | `ANY` | NO | - | NO |
| **std_rh** | `ANY` | NO | - | NO |
| **avg_wind** | `ANY` | NO | - | NO |
| **std_wind** | `ANY` | NO | - | NO |
| **avg_solar** | `ANY` | NO | - | NO |
| **std_solar** | `ANY` | NO | - | NO |
| **avg_rain** | `ANY` | NO | - | NO |
| **std_rain** | `ANY` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |
| **sensor_specs** | `TEXT` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup-data-20260817/waid_deploy.db`

#### Table: `public_forecasts`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **temp_era5** | `TEXT` | NO | - | NO |
| **rh_era5** | `TEXT` | NO | - | NO |
| **pres_era5** | `TEXT` | NO | - | NO |
| **wind_era5** | `TEXT` | NO | - | NO |
| **rain_era5** | `TEXT` | NO | - | NO |
| **solar_era5** | `TEXT` | NO | - | NO |
| **abs_error_temp** | `TEXT` | NO | - | NO |
| **abs_error_rh** | `TEXT` | NO | - | NO |
| **abs_error_pres** | `TEXT` | NO | - | NO |
| **abs_error_wind** | `TEXT` | NO | - | NO |
| **abs_error_rain** | `TEXT` | NO | - | NO |
| **abs_error_solar** | `TEXT` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup-data-20260817/waid_mock.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_forecast`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `TEXT` | NO | - | NO |
| **diff_rh** | `TEXT` | NO | - | NO |
| **historical_bias_temp** | `TEXT` | NO | - | NO |
| **drift_vs_bias** | `TEXT` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **diff_pres** | `TEXT` | NO | - | NO |
| **diff_wind** | `TEXT` | NO | - | NO |
| **diff_solar** | `TEXT` | NO | - | NO |
| **diff_rain** | `TEXT` | NO | - | NO |
| **historical_bias_rh** | `TEXT` | NO | - | NO |
| **historical_bias_pres** | `TEXT` | NO | - | NO |
| **historical_bias_wind** | `TEXT` | NO | - | NO |
| **historical_bias_solar** | `TEXT` | NO | - | NO |
| **historical_bias_rain** | `TEXT` | NO | - | NO |
| **drift_vs_bias_temp** | `TEXT` | NO | - | NO |
| **drift_vs_bias_rh** | `TEXT` | NO | - | NO |
| **drift_vs_bias_pres** | `TEXT` | NO | - | NO |
| **drift_vs_bias_wind** | `TEXT` | NO | - | NO |
| **drift_vs_bias_solar** | `TEXT` | NO | - | NO |
| **drift_vs_bias_rain** | `TEXT` | NO | - | NO |

#### Table: `inference_prediction`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |

#### Table: `inference_quality`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `ANY` | NO | - | NO |
| **pred_rain** | `ANY` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |
| **temp_era5** | `ANY` | NO | - | NO |
| **pres_era5** | `ANY` | NO | - | NO |
| **rh_era5** | `ANY` | NO | - | NO |
| **wind_era5** | `ANY` | NO | - | NO |
| **solar_era5** | `ANY` | NO | - | NO |
| **rain_era5** | `ANY` | NO | - | NO |
| **delta_temp** | `ANY` | NO | - | NO |
| **delta_pres** | `ANY` | NO | - | NO |
| **delta_rh** | `ANY` | NO | - | NO |
| **delta_wind** | `ANY` | NO | - | NO |
| **delta_solar** | `ANY` | NO | - | NO |
| **delta_rain** | `ANY` | NO | - | NO |
| **abs_error_temp** | `ANY` | NO | - | NO |
| **abs_error_pres** | `ANY` | NO | - | NO |
| **abs_error_rh** | `ANY` | NO | - | NO |
| **abs_error_wind** | `ANY` | NO | - | NO |
| **abs_error_solar** | `ANY` | NO | - | NO |
| **abs_error_rain** | `ANY` | NO | - | NO |
| **perc_error_temp** | `ANY` | NO | - | NO |
| **perc_error_pres** | `ANY` | NO | - | NO |
| **perc_error_rh** | `ANY` | NO | - | NO |
| **perc_error_wind** | `ANY` | NO | - | NO |
| **perc_error_solar** | `ANY` | NO | - | NO |
| **perc_error_rain** | `ANY` | NO | - | NO |

#### Table: `inference_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **id** | `INTEGER` | NO | - | YES |
| **ts_emission** | `DATETIME` | NO | CURRENT_TIMESTAMP | NO |
| **ts_window_start** | `DATETIME` | NO | - | NO |
| **ts_window_end** | `DATETIME` | NO | - | NO |
| **timestamp** | `DATETIME` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **n_features_used** | `INTEGER` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_stats`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **avg_temp** | `ANY` | NO | - | NO |
| **std_temp** | `ANY` | NO | - | NO |
| **avg_pres** | `ANY` | NO | - | NO |
| **std_pres** | `ANY` | NO | - | NO |
| **avg_rh** | `ANY` | NO | - | NO |
| **std_rh** | `ANY` | NO | - | NO |
| **avg_wind** | `ANY` | NO | - | NO |
| **std_wind** | `ANY` | NO | - | NO |
| **avg_solar** | `ANY` | NO | - | NO |
| **std_solar** | `ANY` | NO | - | NO |
| **avg_rain** | `ANY` | NO | - | NO |
| **std_rain** | `ANY` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |
| **sensor_specs** | `TEXT` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup-data-20260817/waid_public.db`

#### Table: `public_forecasts`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **temp_era5** | `TEXT` | NO | - | NO |
| **rh_era5** | `TEXT` | NO | - | NO |
| **pres_era5** | `TEXT` | NO | - | NO |
| **wind_era5** | `TEXT` | NO | - | NO |
| **rain_era5** | `TEXT` | NO | - | NO |
| **solar_era5** | `TEXT` | NO | - | NO |
| **abs_error_temp** | `TEXT` | NO | - | NO |
| **abs_error_rh** | `TEXT` | NO | - | NO |
| **abs_error_pres** | `TEXT` | NO | - | NO |
| **abs_error_wind** | `TEXT` | NO | - | NO |
| **abs_error_rain** | `TEXT` | NO | - | NO |
| **abs_error_solar** | `TEXT` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260807_070401/main_dbt_test__audit.db`

#### Table: `dbt_utils_accepted_range_stg_ecowitt_hourly_rain__300__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_humidity__100__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_pressure_hpa__1100__800`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_solar_radiation__1500__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_temperature__50___30`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_wind_speed__80__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `not_null_stg_ecowitt_timestamp`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `unique_stg_ecowitt_timestamp`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **unique_field** | `TEXT` | NO | - | NO |
| **n_records** | `ANY` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260807_070401/waid-old-bad-delta.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_forecast_6h`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **ts_target** | `TEXT` | NO | - | YES |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **ecowitt_temp** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **ecowitt_wind** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **ecowitt_pres** | `REAL` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **ecowitt_rh** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **ecowitt_solar** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **ecowitt_rain** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |

#### Table: `inference_prediction`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **ts_target** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |

#### Table: `inference_quality`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **ts_target** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `ANY` | NO | - | NO |
| **pred_rain** | `ANY` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |
| **delta_temp** | `ANY` | NO | - | NO |
| **delta_pres** | `ANY` | NO | - | NO |
| **delta_rh** | `ANY` | NO | - | NO |
| **delta_wind** | `ANY` | NO | - | NO |
| **delta_solar** | `ANY` | NO | - | NO |
| **delta_rain** | `ANY` | NO | - | NO |
| **abs_error_temp** | `ANY` | NO | - | NO |
| **abs_error_pres** | `ANY` | NO | - | NO |
| **abs_error_rh** | `ANY` | NO | - | NO |
| **abs_error_wind** | `ANY` | NO | - | NO |
| **abs_error_solar** | `ANY` | NO | - | NO |
| **abs_error_rain** | `ANY` | NO | - | NO |
| **perc_error_temp** | `ANY` | NO | - | NO |
| **perc_error_pres** | `ANY` | NO | - | NO |
| **perc_error_rh** | `ANY` | NO | - | NO |
| **perc_error_wind** | `ANY` | NO | - | NO |
| **perc_error_solar** | `ANY` | NO | - | NO |
| **perc_error_rain** | `ANY` | NO | - | NO |

#### Table: `inference_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **id** | `INTEGER` | NO | - | YES |
| **ts_emission** | `DATETIME` | NO | CURRENT_TIMESTAMP | NO |
| **ts_window_start** | `DATETIME` | NO | - | NO |
| **ts_window_end** | `DATETIME` | NO | - | NO |
| **ts_target** | `DATETIME` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **n_features_used** | `INTEGER` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `inference_stats`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **avg_temp** | `ANY` | NO | - | NO |
| **std_temp** | `ANY` | NO | - | NO |
| **avg_pres** | `ANY` | NO | - | NO |
| **std_pres** | `ANY` | NO | - | NO |
| **avg_rh** | `ANY` | NO | - | NO |
| **std_rh** | `ANY` | NO | - | NO |
| **avg_wind** | `ANY` | NO | - | NO |
| **std_wind** | `ANY` | NO | - | NO |
| **avg_solar** | `ANY` | NO | - | NO |
| **std_solar** | `ANY` | NO | - | NO |
| **avg_rain** | `ANY` | NO | - | NO |
| **std_rain** | `ANY` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `int_matches_normalized`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |
| **raw_temp** | `ANY` | NO | - | NO |
| **raw_pres** | `ANY` | NO | - | NO |
| **raw_rh** | `ANY` | NO | - | NO |
| **raw_wind** | `ANY` | NO | - | NO |
| **raw_solar** | `ANY` | NO | - | NO |
| **raw_rain** | `ANY` | NO | - | NO |
| **temp_eco_norm** | `ANY` | NO | - | NO |
| **pres_eco_norm** | `ANY` | NO | - | NO |
| **rh_eco_norm** | `ANY` | NO | - | NO |
| **wind_eco_norm** | `ANY` | NO | - | NO |
| **solar_eco_norm** | `ANY` | NO | - | NO |
| **rain_eco_norm** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_era5_timestamp** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **model_health_status** | `INTEGER` | NO | 0 | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260807_070401/waid-old.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_forecast_6h`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **ts_target** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `ANY` | NO | - | NO |
| **pred_rain** | `ANY` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **ecowitt_wind** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **ecowitt_pres** | `REAL` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **ecowitt_rh** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **ecowitt_solar** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **ecowitt_rain** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |

#### Table: `inference_prediction`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **ts_target** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |

#### Table: `inference_quality`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **ts_target** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `ANY` | NO | - | NO |
| **pred_rain** | `ANY` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |
| **delta_temp** | `ANY` | NO | - | NO |
| **delta_pres** | `ANY` | NO | - | NO |
| **delta_rh** | `ANY` | NO | - | NO |
| **delta_wind** | `ANY` | NO | - | NO |
| **delta_solar** | `ANY` | NO | - | NO |
| **delta_rain** | `ANY` | NO | - | NO |
| **abs_error_temp** | `ANY` | NO | - | NO |
| **abs_error_pres** | `ANY` | NO | - | NO |
| **abs_error_rh** | `ANY` | NO | - | NO |
| **abs_error_wind** | `ANY` | NO | - | NO |
| **abs_error_solar** | `ANY` | NO | - | NO |
| **abs_error_rain** | `ANY` | NO | - | NO |
| **perc_error_temp** | `ANY` | NO | - | NO |
| **perc_error_pres** | `ANY` | NO | - | NO |
| **perc_error_rh** | `ANY` | NO | - | NO |
| **perc_error_wind** | `ANY` | NO | - | NO |
| **perc_error_solar** | `ANY` | NO | - | NO |
| **perc_error_rain** | `ANY` | NO | - | NO |

#### Table: `inference_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **id** | `INTEGER` | NO | - | YES |
| **ts_emission** | `DATETIME` | NO | CURRENT_TIMESTAMP | NO |
| **ts_window_start** | `DATETIME` | NO | - | NO |
| **ts_window_end** | `DATETIME` | NO | - | NO |
| **ts_target** | `DATETIME` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **n_features_used** | `INTEGER` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `inference_stats`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **avg_temp** | `ANY` | NO | - | NO |
| **std_temp** | `ANY` | NO | - | NO |
| **avg_pres** | `ANY` | NO | - | NO |
| **std_pres** | `ANY` | NO | - | NO |
| **avg_rh** | `ANY` | NO | - | NO |
| **std_rh** | `ANY` | NO | - | NO |
| **avg_wind** | `ANY` | NO | - | NO |
| **std_wind** | `ANY` | NO | - | NO |
| **avg_solar** | `ANY` | NO | - | NO |
| **std_solar** | `ANY` | NO | - | NO |
| **avg_rain** | `ANY` | NO | - | NO |
| **std_rain** | `ANY` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `int_matches_normalized`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |
| **raw_temp** | `ANY` | NO | - | NO |
| **raw_pres** | `ANY` | NO | - | NO |
| **raw_rh** | `ANY` | NO | - | NO |
| **raw_wind** | `ANY` | NO | - | NO |
| **raw_solar** | `ANY` | NO | - | NO |
| **raw_rain** | `ANY` | NO | - | NO |
| **temp_eco_norm** | `ANY` | NO | - | NO |
| **pres_eco_norm** | `ANY` | NO | - | NO |
| **rh_eco_norm** | `ANY` | NO | - | NO |
| **wind_eco_norm** | `ANY` | NO | - | NO |
| **solar_eco_norm** | `ANY` | NO | - | NO |
| **rain_eco_norm** | `ANY` | NO | - | NO |

#### Table: `live_forecast_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **ts_target** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_era5_timestamp** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **model_health_status** | `INTEGER` | NO | 0 | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260807_070401/waid.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_forecast_6h`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **ts_target** | `TEXT` | NO | - | YES |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **ecowitt_temp** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **ecowitt_wind** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **ecowitt_pres** | `REAL` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **ecowitt_rh** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **ecowitt_solar** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **ecowitt_rain** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |

#### Table: `inference_prediction`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **ts_target** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |

#### Table: `inference_quality`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **ts_target** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `ANY` | NO | - | NO |
| **pred_rain** | `ANY` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |
| **temp_era5** | `ANY` | NO | - | NO |
| **pres_era5** | `ANY` | NO | - | NO |
| **rh_era5** | `ANY` | NO | - | NO |
| **wind_era5** | `ANY` | NO | - | NO |
| **solar_era5** | `ANY` | NO | - | NO |
| **rain_era5** | `ANY` | NO | - | NO |
| **delta_temp** | `ANY` | NO | - | NO |
| **delta_pres** | `ANY` | NO | - | NO |
| **delta_rh** | `ANY` | NO | - | NO |
| **delta_wind** | `ANY` | NO | - | NO |
| **delta_solar** | `ANY` | NO | - | NO |
| **delta_rain** | `ANY` | NO | - | NO |
| **abs_error_temp** | `ANY` | NO | - | NO |
| **abs_error_pres** | `ANY` | NO | - | NO |
| **abs_error_rh** | `ANY` | NO | - | NO |
| **abs_error_wind** | `ANY` | NO | - | NO |
| **abs_error_solar** | `ANY` | NO | - | NO |
| **abs_error_rain** | `ANY` | NO | - | NO |
| **perc_error_temp** | `ANY` | NO | - | NO |
| **perc_error_pres** | `ANY` | NO | - | NO |
| **perc_error_rh** | `ANY` | NO | - | NO |
| **perc_error_wind** | `ANY` | NO | - | NO |
| **perc_error_solar** | `ANY` | NO | - | NO |
| **perc_error_rain** | `ANY` | NO | - | NO |

#### Table: `inference_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **id** | `INTEGER` | NO | - | YES |
| **ts_emission** | `DATETIME` | NO | CURRENT_TIMESTAMP | NO |
| **ts_window_start** | `DATETIME` | NO | - | NO |
| **ts_window_end** | `DATETIME` | NO | - | NO |
| **ts_target** | `DATETIME` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **n_features_used** | `INTEGER` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_stats`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **avg_temp** | `ANY` | NO | - | NO |
| **std_temp** | `ANY` | NO | - | NO |
| **avg_pres** | `ANY` | NO | - | NO |
| **std_pres** | `ANY` | NO | - | NO |
| **avg_rh** | `ANY` | NO | - | NO |
| **std_rh** | `ANY` | NO | - | NO |
| **avg_wind** | `ANY` | NO | - | NO |
| **std_wind** | `ANY` | NO | - | NO |
| **avg_solar** | `ANY` | NO | - | NO |
| **std_solar** | `ANY` | NO | - | NO |
| **avg_rain** | `ANY` | NO | - | NO |
| **std_rain** | `ANY` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `int_matches_normalized`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |
| **raw_temp** | `ANY` | NO | - | NO |
| **raw_pres** | `ANY` | NO | - | NO |
| **raw_rh** | `ANY` | NO | - | NO |
| **raw_wind** | `ANY` | NO | - | NO |
| **raw_solar** | `ANY` | NO | - | NO |
| **raw_rain** | `ANY` | NO | - | NO |
| **temp_eco_norm** | `ANY` | NO | - | NO |
| **pres_eco_norm** | `ANY` | NO | - | NO |
| **rh_eco_norm** | `ANY` | NO | - | NO |
| **wind_eco_norm** | `ANY` | NO | - | NO |
| **solar_eco_norm** | `ANY` | NO | - | NO |
| **rain_eco_norm** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260807_070401/waid_mock-old.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_forecast_6h`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **ts_target** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `TEXT` | NO | - | NO |
| **diff_temp** | `TEXT` | NO | - | NO |
| **ecowitt_wind** | `TEXT` | NO | - | NO |
| **diff_wind** | `TEXT` | NO | - | NO |
| **ecowitt_pres** | `TEXT` | NO | - | NO |
| **diff_pres** | `TEXT` | NO | - | NO |
| **ecowitt_rh** | `TEXT` | NO | - | NO |
| **diff_rh** | `TEXT` | NO | - | NO |
| **ecowitt_solar** | `TEXT` | NO | - | NO |
| **diff_solar** | `TEXT` | NO | - | NO |
| **ecowitt_rain** | `TEXT` | NO | - | NO |
| **diff_rain** | `TEXT` | NO | - | NO |

#### Table: `inference_prediction`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **ts_target** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |

#### Table: `inference_quality`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **ts_target** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `ANY` | NO | - | NO |
| **pred_rain** | `ANY` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |
| **delta_temp** | `ANY` | NO | - | NO |
| **delta_pres** | `ANY` | NO | - | NO |
| **delta_rh** | `ANY` | NO | - | NO |
| **delta_wind** | `ANY` | NO | - | NO |
| **delta_solar** | `ANY` | NO | - | NO |
| **delta_rain** | `ANY` | NO | - | NO |
| **abs_error_temp** | `ANY` | NO | - | NO |
| **abs_error_pres** | `ANY` | NO | - | NO |
| **abs_error_rh** | `ANY` | NO | - | NO |
| **abs_error_wind** | `ANY` | NO | - | NO |
| **abs_error_solar** | `ANY` | NO | - | NO |
| **abs_error_rain** | `ANY` | NO | - | NO |
| **perc_error_temp** | `ANY` | NO | - | NO |
| **perc_error_pres** | `ANY` | NO | - | NO |
| **perc_error_rh** | `ANY` | NO | - | NO |
| **perc_error_wind** | `ANY` | NO | - | NO |
| **perc_error_solar** | `ANY` | NO | - | NO |
| **perc_error_rain** | `ANY` | NO | - | NO |

#### Table: `inference_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **id** | `INTEGER` | NO | - | YES |
| **ts_emission** | `DATETIME` | NO | CURRENT_TIMESTAMP | NO |
| **ts_window_start** | `DATETIME` | NO | - | NO |
| **ts_window_end** | `DATETIME` | NO | - | NO |
| **ts_target** | `DATETIME` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **n_features_used** | `INTEGER` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `inference_stats`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **avg_temp** | `ANY` | NO | - | NO |
| **std_temp** | `ANY` | NO | - | NO |
| **avg_pres** | `ANY` | NO | - | NO |
| **std_pres** | `ANY` | NO | - | NO |
| **avg_rh** | `ANY` | NO | - | NO |
| **std_rh** | `ANY` | NO | - | NO |
| **avg_wind** | `ANY` | NO | - | NO |
| **std_wind** | `ANY` | NO | - | NO |
| **avg_solar** | `ANY` | NO | - | NO |
| **std_solar** | `ANY` | NO | - | NO |
| **avg_rain** | `ANY` | NO | - | NO |
| **std_rain** | `ANY` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `int_matches_normalized`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |
| **raw_temp** | `ANY` | NO | - | NO |
| **raw_pres** | `ANY` | NO | - | NO |
| **raw_rh** | `ANY` | NO | - | NO |
| **raw_wind** | `ANY` | NO | - | NO |
| **raw_solar** | `ANY` | NO | - | NO |
| **raw_rain** | `ANY` | NO | - | NO |
| **temp_eco_norm** | `ANY` | NO | - | NO |
| **pres_eco_norm** | `ANY` | NO | - | NO |
| **rh_eco_norm** | `ANY` | NO | - | NO |
| **wind_eco_norm** | `ANY` | NO | - | NO |
| **solar_eco_norm** | `ANY` | NO | - | NO |
| **rain_eco_norm** | `ANY` | NO | - | NO |

#### Table: `live_forecast_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **ts_target** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_era5_timestamp** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **model_health_status** | `INTEGER` | NO | 0 | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260807_070401/waid_mock.db`

_No user tables found in this database._

### 📁 Database File: `data/backups/backup_soft_reset_20260807_073912/main_dbt_test__audit.db`

#### Table: `dbt_utils_accepted_range_stg_ecowitt_hourly_rain__300__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_humidity__100__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_pressure_hpa__1100__800`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_solar_radiation__1500__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_temperature__50___30`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_wind_speed__80__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `not_null_stg_ecowitt_timestamp`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `unique_stg_ecowitt_timestamp`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **unique_field** | `TEXT` | NO | - | NO |
| **n_records** | `ANY` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260807_073912/waid.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `int_matches_normalized`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |
| **raw_temp** | `ANY` | NO | - | NO |
| **raw_pres** | `ANY` | NO | - | NO |
| **raw_rh** | `ANY` | NO | - | NO |
| **raw_wind** | `ANY` | NO | - | NO |
| **raw_solar** | `ANY` | NO | - | NO |
| **raw_rain** | `ANY` | NO | - | NO |
| **temp_eco_norm** | `ANY` | NO | - | NO |
| **pres_eco_norm** | `ANY` | NO | - | NO |
| **rh_eco_norm** | `ANY` | NO | - | NO |
| **wind_eco_norm** | `ANY` | NO | - | NO |
| **solar_eco_norm** | `ANY` | NO | - | NO |
| **rain_eco_norm** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260807_082712/main_dbt_test__audit.db`

#### Table: `dbt_utils_accepted_range_stg_ecowitt_hourly_rain__300__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_humidity__100__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_pressure_hpa__1100__800`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_solar_radiation__1500__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_temperature__50___30`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_wind_speed__80__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `not_null_stg_ecowitt_timestamp`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `unique_stg_ecowitt_timestamp`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **unique_field** | `TEXT` | NO | - | NO |
| **n_records** | `ANY` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260807_082712/waid.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `int_matches_normalized`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |
| **raw_temp** | `ANY` | NO | - | NO |
| **raw_pres** | `ANY` | NO | - | NO |
| **raw_rh** | `ANY` | NO | - | NO |
| **raw_wind** | `ANY` | NO | - | NO |
| **raw_solar** | `ANY` | NO | - | NO |
| **raw_rain** | `ANY` | NO | - | NO |
| **temp_eco_norm** | `ANY` | NO | - | NO |
| **pres_eco_norm** | `ANY` | NO | - | NO |
| **rh_eco_norm** | `ANY` | NO | - | NO |
| **wind_eco_norm** | `ANY` | NO | - | NO |
| **solar_eco_norm** | `ANY` | NO | - | NO |
| **rain_eco_norm** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260807_090007/main_dbt_test__audit.db`

#### Table: `dbt_utils_accepted_range_stg_ecowitt_hourly_rain__300__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_humidity__100__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_pressure_hpa__1100__800`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_solar_radiation__1500__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_temperature__50___30`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_wind_speed__80__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `not_null_stg_ecowitt_timestamp`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `unique_stg_ecowitt_timestamp`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **unique_field** | `TEXT` | NO | - | NO |
| **n_records** | `ANY` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260807_090007/waid.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `int_matches_normalized`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |
| **raw_temp** | `ANY` | NO | - | NO |
| **raw_pres** | `ANY` | NO | - | NO |
| **raw_rh** | `ANY` | NO | - | NO |
| **raw_wind** | `ANY` | NO | - | NO |
| **raw_solar** | `ANY` | NO | - | NO |
| **raw_rain** | `ANY` | NO | - | NO |
| **temp_eco_norm** | `ANY` | NO | - | NO |
| **pres_eco_norm** | `ANY` | NO | - | NO |
| **rh_eco_norm** | `ANY` | NO | - | NO |
| **wind_eco_norm** | `ANY` | NO | - | NO |
| **solar_eco_norm** | `ANY` | NO | - | NO |
| **rain_eco_norm** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260807_093722/main_dbt_test__audit.db`

#### Table: `dbt_utils_accepted_range_stg_ecowitt_hourly_rain__300__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_humidity__100__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_pressure_hpa__1100__800`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_solar_radiation__1500__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_temperature__50___30`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_wind_speed__80__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `not_null_stg_ecowitt_timestamp`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `unique_stg_ecowitt_timestamp`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **unique_field** | `TEXT` | NO | - | NO |
| **n_records** | `ANY` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260807_093722/waid.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `int_matches_normalized`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |
| **raw_temp** | `ANY` | NO | - | NO |
| **raw_pres** | `ANY` | NO | - | NO |
| **raw_rh** | `ANY` | NO | - | NO |
| **raw_wind** | `ANY` | NO | - | NO |
| **raw_solar** | `ANY` | NO | - | NO |
| **raw_rain** | `ANY` | NO | - | NO |
| **temp_eco_norm** | `ANY` | NO | - | NO |
| **pres_eco_norm** | `ANY` | NO | - | NO |
| **rh_eco_norm** | `ANY` | NO | - | NO |
| **wind_eco_norm** | `ANY` | NO | - | NO |
| **solar_eco_norm** | `ANY` | NO | - | NO |
| **rain_eco_norm** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260818_105447/main_dbt_test__audit.db`

#### Table: `dbt_utils_accepted_range_stg_ecowitt_hourly_rain__300__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_humidity__100__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_pressure_hpa__1100__800`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_solar_radiation__1500__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_temperature__50___30`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `dbt_utils_accepted_range_stg_ecowitt_wind_speed__80__0`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `not_null_stg_ecowitt_timestamp`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

#### Table: `unique_stg_ecowitt_timestamp`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **unique_field** | `TEXT` | NO | - | NO |
| **n_records** | `ANY` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260818_105447/mock.db`

_No user tables found in this database._

### 📁 Database File: `data/backups/backup_soft_reset_20260818_105447/waid.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_forecast`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **model_version** | `TEXT` | NO | - | YES |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias** | `REAL` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |

#### Table: `inference_prediction`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |

#### Table: `inference_quality`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `ANY` | NO | - | NO |
| **pred_rain** | `ANY` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |
| **temp_era5** | `ANY` | NO | - | NO |
| **pres_era5** | `ANY` | NO | - | NO |
| **rh_era5** | `ANY` | NO | - | NO |
| **wind_era5** | `ANY` | NO | - | NO |
| **solar_era5** | `ANY` | NO | - | NO |
| **rain_era5** | `ANY` | NO | - | NO |
| **delta_temp** | `ANY` | NO | - | NO |
| **delta_pres** | `ANY` | NO | - | NO |
| **delta_rh** | `ANY` | NO | - | NO |
| **delta_wind** | `ANY` | NO | - | NO |
| **delta_solar** | `ANY` | NO | - | NO |
| **delta_rain** | `ANY` | NO | - | NO |
| **abs_error_temp** | `ANY` | NO | - | NO |
| **abs_error_pres** | `ANY` | NO | - | NO |
| **abs_error_rh** | `ANY` | NO | - | NO |
| **abs_error_wind** | `ANY` | NO | - | NO |
| **abs_error_solar** | `ANY` | NO | - | NO |
| **abs_error_rain** | `ANY` | NO | - | NO |
| **perc_error_temp** | `ANY` | NO | - | NO |
| **perc_error_pres** | `ANY` | NO | - | NO |
| **perc_error_rh** | `ANY` | NO | - | NO |
| **perc_error_wind** | `ANY` | NO | - | NO |
| **perc_error_solar** | `ANY` | NO | - | NO |
| **perc_error_rain** | `ANY` | NO | - | NO |

#### Table: `inference_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **id** | `INTEGER` | NO | - | YES |
| **ts_emission** | `DATETIME` | NO | CURRENT_TIMESTAMP | NO |
| **ts_window_start** | `DATETIME` | NO | - | NO |
| **ts_window_end** | `DATETIME` | NO | - | NO |
| **timestamp** | `DATETIME` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **n_features_used** | `INTEGER` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_stats`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **avg_temp** | `ANY` | NO | - | NO |
| **std_temp** | `ANY` | NO | - | NO |
| **avg_pres** | `ANY` | NO | - | NO |
| **std_pres** | `ANY` | NO | - | NO |
| **avg_rh** | `ANY` | NO | - | NO |
| **std_rh** | `ANY` | NO | - | NO |
| **avg_wind** | `ANY` | NO | - | NO |
| **std_wind** | `ANY` | NO | - | NO |
| **avg_solar** | `ANY` | NO | - | NO |
| **std_solar** | `ANY` | NO | - | NO |
| **avg_rain** | `ANY` | NO | - | NO |
| **std_rain** | `ANY` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |
| **sensor_specs** | `TEXT` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260818_105447/waid_deploy.db`

#### Table: `public_forecasts`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **temp_era5** | `TEXT` | NO | - | NO |
| **rh_era5** | `TEXT` | NO | - | NO |
| **pres_era5** | `TEXT` | NO | - | NO |
| **wind_era5** | `TEXT` | NO | - | NO |
| **rain_era5** | `TEXT` | NO | - | NO |
| **solar_era5** | `TEXT` | NO | - | NO |
| **abs_error_temp** | `TEXT` | NO | - | NO |
| **abs_error_rh** | `TEXT` | NO | - | NO |
| **abs_error_pres** | `TEXT` | NO | - | NO |
| **abs_error_wind** | `TEXT` | NO | - | NO |
| **abs_error_rain** | `TEXT` | NO | - | NO |
| **abs_error_solar** | `TEXT` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260818_105447/waid_mock.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_forecast`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **model_version** | `TEXT` | NO | - | YES |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias** | `REAL` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |

#### Table: `inference_prediction`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |

#### Table: `inference_quality`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `ANY` | NO | - | NO |
| **pred_rain** | `ANY` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |
| **temp_era5** | `ANY` | NO | - | NO |
| **pres_era5** | `ANY` | NO | - | NO |
| **rh_era5** | `ANY` | NO | - | NO |
| **wind_era5** | `ANY` | NO | - | NO |
| **solar_era5** | `ANY` | NO | - | NO |
| **rain_era5** | `ANY` | NO | - | NO |
| **delta_temp** | `ANY` | NO | - | NO |
| **delta_pres** | `ANY` | NO | - | NO |
| **delta_rh** | `ANY` | NO | - | NO |
| **delta_wind** | `ANY` | NO | - | NO |
| **delta_solar** | `ANY` | NO | - | NO |
| **delta_rain** | `ANY` | NO | - | NO |
| **abs_error_temp** | `ANY` | NO | - | NO |
| **abs_error_pres** | `ANY` | NO | - | NO |
| **abs_error_rh** | `ANY` | NO | - | NO |
| **abs_error_wind** | `ANY` | NO | - | NO |
| **abs_error_solar** | `ANY` | NO | - | NO |
| **abs_error_rain** | `ANY` | NO | - | NO |
| **perc_error_temp** | `ANY` | NO | - | NO |
| **perc_error_pres** | `ANY` | NO | - | NO |
| **perc_error_rh** | `ANY` | NO | - | NO |
| **perc_error_wind** | `ANY` | NO | - | NO |
| **perc_error_solar** | `ANY` | NO | - | NO |
| **perc_error_rain** | `ANY` | NO | - | NO |

#### Table: `inference_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **id** | `INTEGER` | NO | - | YES |
| **ts_emission** | `DATETIME` | NO | CURRENT_TIMESTAMP | NO |
| **ts_window_start** | `DATETIME` | NO | - | NO |
| **ts_window_end** | `DATETIME` | NO | - | NO |
| **timestamp** | `DATETIME` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **n_features_used** | `INTEGER` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_stats`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **avg_temp** | `ANY` | NO | - | NO |
| **std_temp** | `ANY` | NO | - | NO |
| **avg_pres** | `ANY` | NO | - | NO |
| **std_pres** | `ANY` | NO | - | NO |
| **avg_rh** | `ANY` | NO | - | NO |
| **std_rh** | `ANY` | NO | - | NO |
| **avg_wind** | `ANY` | NO | - | NO |
| **std_wind** | `ANY` | NO | - | NO |
| **avg_solar** | `ANY` | NO | - | NO |
| **std_solar** | `ANY` | NO | - | NO |
| **avg_rain** | `ANY` | NO | - | NO |
| **std_rain** | `ANY` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |
| **sensor_specs** | `TEXT` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260825_165724/waid_mock-old.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_forecast`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias** | `REAL` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |

#### Table: `inference_prediction`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |

#### Table: `inference_quality`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `ANY` | NO | - | NO |
| **pred_rain** | `ANY` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |
| **temp_era5** | `ANY` | NO | - | NO |
| **pres_era5** | `ANY` | NO | - | NO |
| **rh_era5** | `ANY` | NO | - | NO |
| **wind_era5** | `ANY` | NO | - | NO |
| **solar_era5** | `ANY` | NO | - | NO |
| **rain_era5** | `ANY` | NO | - | NO |
| **delta_temp** | `ANY` | NO | - | NO |
| **delta_pres** | `ANY` | NO | - | NO |
| **delta_rh** | `ANY` | NO | - | NO |
| **delta_wind** | `ANY` | NO | - | NO |
| **delta_solar** | `ANY` | NO | - | NO |
| **delta_rain** | `ANY` | NO | - | NO |
| **abs_error_temp** | `ANY` | NO | - | NO |
| **abs_error_pres** | `ANY` | NO | - | NO |
| **abs_error_rh** | `ANY` | NO | - | NO |
| **abs_error_wind** | `ANY` | NO | - | NO |
| **abs_error_solar** | `ANY` | NO | - | NO |
| **abs_error_rain** | `ANY` | NO | - | NO |
| **perc_error_temp** | `ANY` | NO | - | NO |
| **perc_error_pres** | `ANY` | NO | - | NO |
| **perc_error_rh** | `ANY` | NO | - | NO |
| **perc_error_wind** | `ANY` | NO | - | NO |
| **perc_error_solar** | `ANY` | NO | - | NO |
| **perc_error_rain** | `ANY` | NO | - | NO |

#### Table: `inference_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **id** | `INTEGER` | NO | - | YES |
| **ts_emission** | `DATETIME` | NO | CURRENT_TIMESTAMP | NO |
| **ts_window_start** | `DATETIME` | NO | - | NO |
| **ts_window_end** | `DATETIME` | NO | - | NO |
| **timestamp** | `DATETIME` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **n_features_used** | `INTEGER` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_stats`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **avg_temp** | `ANY` | NO | - | NO |
| **std_temp** | `ANY` | NO | - | NO |
| **avg_pres** | `ANY` | NO | - | NO |
| **std_pres** | `ANY` | NO | - | NO |
| **avg_rh** | `ANY` | NO | - | NO |
| **std_rh** | `ANY` | NO | - | NO |
| **avg_wind** | `ANY` | NO | - | NO |
| **std_wind** | `ANY` | NO | - | NO |
| **avg_solar** | `ANY` | NO | - | NO |
| **std_solar** | `ANY` | NO | - | NO |
| **avg_rain** | `ANY` | NO | - | NO |
| **std_rain** | `ANY` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |
| **sensor_specs** | `TEXT` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260825_165724/waid_mock.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_forecast`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias** | `REAL` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |
| **ts_window_start** | `TEXT` | NO | - | NO |
| **ts_window_stop** | `TEXT` | NO | - | NO |

#### Table: `inference_prediction`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `NUM` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **ts_emission** | `NUM` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |

#### Table: `inference_quality`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `ANY` | NO | - | NO |
| **pred_rain** | `ANY` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |
| **temp_era5** | `ANY` | NO | - | NO |
| **pres_era5** | `ANY` | NO | - | NO |
| **rh_era5** | `ANY` | NO | - | NO |
| **wind_era5** | `ANY` | NO | - | NO |
| **solar_era5** | `ANY` | NO | - | NO |
| **rain_era5** | `ANY` | NO | - | NO |
| **delta_temp** | `ANY` | NO | - | NO |
| **delta_pres** | `ANY` | NO | - | NO |
| **delta_rh** | `ANY` | NO | - | NO |
| **delta_wind** | `ANY` | NO | - | NO |
| **delta_solar** | `ANY` | NO | - | NO |
| **delta_rain** | `ANY` | NO | - | NO |
| **abs_error_temp** | `ANY` | NO | - | NO |
| **abs_error_pres** | `ANY` | NO | - | NO |
| **abs_error_rh** | `ANY` | NO | - | NO |
| **abs_error_wind** | `ANY` | NO | - | NO |
| **abs_error_solar** | `ANY` | NO | - | NO |
| **abs_error_rain** | `ANY` | NO | - | NO |
| **perc_error_temp** | `ANY` | NO | - | NO |
| **perc_error_pres** | `ANY` | NO | - | NO |
| **perc_error_rh** | `ANY` | NO | - | NO |
| **perc_error_wind** | `ANY` | NO | - | NO |
| **perc_error_solar** | `ANY` | NO | - | NO |
| **perc_error_rain** | `ANY` | NO | - | NO |

#### Table: `inference_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **id** | `INTEGER` | NO | - | YES |
| **ts_emission** | `DATETIME` | NO | CURRENT_TIMESTAMP | NO |
| **ts_window_start** | `DATETIME` | NO | - | NO |
| **ts_window_end** | `DATETIME` | NO | - | NO |
| **timestamp** | `DATETIME` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **n_features_used** | `INTEGER` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_stats`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | NO |
| **timestamp** | `TEXT` | NO | - | NO |
| **n_votes** | `ANY` | NO | - | NO |
| **consensus_temp** | `ANY` | NO | - | NO |
| **std_temp** | `ANY` | NO | - | NO |
| **consensus_pres** | `ANY` | NO | - | NO |
| **std_pres** | `ANY` | NO | - | NO |
| **consensus_rh** | `ANY` | NO | - | NO |
| **std_rh** | `ANY` | NO | - | NO |
| **consensus_wind** | `ANY` | NO | - | NO |
| **std_wind** | `ANY` | NO | - | NO |
| **consensus_solar** | `ANY` | NO | - | NO |
| **std_solar** | `ANY` | NO | - | NO |
| **consensus_rain** | `ANY` | NO | - | NO |
| **std_rain** | `ANY` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |
| **sensor_specs** | `TEXT` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260825_165724/waid_mock_deploy.db`

#### Table: `public_forecasts`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **temp_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **abs_error_temp** | `REAL` | NO | - | NO |
| **abs_error_rh** | `REAL` | NO | - | NO |
| **abs_error_pres** | `REAL` | NO | - | NO |
| **abs_error_wind** | `REAL` | NO | - | NO |
| **abs_error_rain** | `REAL` | NO | - | NO |
| **abs_error_solar** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260915_162229/waid_mock.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_forecast`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias** | `REAL` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |
| **ts_window_start** | `TEXT` | NO | - | NO |
| **ts_window_stop** | `TEXT` | NO | - | NO |

#### Table: `inference_quality`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `ANY` | NO | - | NO |
| **pred_rain** | `ANY` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |
| **temp_era5** | `ANY` | NO | - | NO |
| **pres_era5** | `ANY` | NO | - | NO |
| **rh_era5** | `ANY` | NO | - | NO |
| **wind_era5** | `ANY` | NO | - | NO |
| **solar_era5** | `ANY` | NO | - | NO |
| **rain_era5** | `ANY` | NO | - | NO |
| **delta_temp** | `ANY` | NO | - | NO |
| **delta_pres** | `ANY` | NO | - | NO |
| **delta_rh** | `ANY` | NO | - | NO |
| **delta_wind** | `ANY` | NO | - | NO |
| **delta_solar** | `ANY` | NO | - | NO |
| **delta_rain** | `ANY` | NO | - | NO |
| **abs_error_temp** | `ANY` | NO | - | NO |
| **abs_error_pres** | `ANY` | NO | - | NO |
| **abs_error_rh** | `ANY` | NO | - | NO |
| **abs_error_wind** | `ANY` | NO | - | NO |
| **abs_error_solar** | `ANY` | NO | - | NO |
| **abs_error_rain** | `ANY` | NO | - | NO |
| **perc_error_temp** | `ANY` | NO | - | NO |
| **perc_error_pres** | `ANY` | NO | - | NO |
| **perc_error_rh** | `ANY` | NO | - | NO |
| **perc_error_wind** | `ANY` | NO | - | NO |
| **perc_error_solar** | `ANY` | NO | - | NO |
| **perc_error_rain** | `ANY` | NO | - | NO |

#### Table: `inference_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **id** | `INTEGER` | NO | - | YES |
| **ts_emission** | `DATETIME` | NO | CURRENT_TIMESTAMP | NO |
| **ts_window_start** | `DATETIME` | NO | - | NO |
| **ts_window_end** | `DATETIME` | NO | - | NO |
| **timestamp** | `DATETIME` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **n_features_used** | `INTEGER` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_stats`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | NO |
| **timestamp** | `TEXT` | NO | - | NO |
| **n_votes** | `ANY` | NO | - | NO |
| **consensus_temp** | `ANY` | NO | - | NO |
| **std_temp** | `ANY` | NO | - | NO |
| **consensus_pres** | `ANY` | NO | - | NO |
| **std_pres** | `ANY` | NO | - | NO |
| **consensus_rh** | `ANY` | NO | - | NO |
| **std_rh** | `ANY` | NO | - | NO |
| **consensus_wind** | `ANY` | NO | - | NO |
| **std_wind** | `ANY` | NO | - | NO |
| **consensus_solar** | `ANY` | NO | - | NO |
| **std_solar** | `ANY` | NO | - | NO |
| **consensus_rain** | `ANY` | NO | - | NO |
| **std_rain** | `ANY` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |
| **sensor_specs** | `TEXT` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260915_162229/waid_mock_deploy.db`

#### Table: `public_forecasts`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **temp_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **abs_error_temp** | `REAL` | NO | - | NO |
| **abs_error_rh** | `REAL` | NO | - | NO |
| **abs_error_pres** | `REAL` | NO | - | NO |
| **abs_error_wind** | `REAL` | NO | - | NO |
| **abs_error_rain** | `REAL` | NO | - | NO |
| **abs_error_solar** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260915_164154/waid_mock.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_forecast`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias** | `REAL` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |
| **ts_window_start** | `TEXT` | NO | - | NO |
| **ts_window_stop** | `TEXT` | NO | - | NO |

#### Table: `inference_quality`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `ANY` | NO | - | NO |
| **pred_rain** | `ANY` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |
| **temp_era5** | `ANY` | NO | - | NO |
| **pres_era5** | `ANY` | NO | - | NO |
| **rh_era5** | `ANY` | NO | - | NO |
| **wind_era5** | `ANY` | NO | - | NO |
| **solar_era5** | `ANY` | NO | - | NO |
| **rain_era5** | `ANY` | NO | - | NO |
| **delta_temp** | `ANY` | NO | - | NO |
| **delta_pres** | `ANY` | NO | - | NO |
| **delta_rh** | `ANY` | NO | - | NO |
| **delta_wind** | `ANY` | NO | - | NO |
| **delta_solar** | `ANY` | NO | - | NO |
| **delta_rain** | `ANY` | NO | - | NO |
| **abs_error_temp** | `ANY` | NO | - | NO |
| **abs_error_pres** | `ANY` | NO | - | NO |
| **abs_error_rh** | `ANY` | NO | - | NO |
| **abs_error_wind** | `ANY` | NO | - | NO |
| **abs_error_solar** | `ANY` | NO | - | NO |
| **abs_error_rain** | `ANY` | NO | - | NO |
| **perc_error_temp** | `ANY` | NO | - | NO |
| **perc_error_pres** | `ANY` | NO | - | NO |
| **perc_error_rh** | `ANY` | NO | - | NO |
| **perc_error_wind** | `ANY` | NO | - | NO |
| **perc_error_solar** | `ANY` | NO | - | NO |
| **perc_error_rain** | `ANY` | NO | - | NO |

#### Table: `inference_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **id** | `INTEGER` | NO | - | YES |
| **ts_emission** | `DATETIME` | NO | CURRENT_TIMESTAMP | NO |
| **ts_window_start** | `DATETIME` | NO | - | NO |
| **ts_window_end** | `DATETIME` | NO | - | NO |
| **timestamp** | `DATETIME` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **n_features_used** | `INTEGER` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_stats`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | NO |
| **timestamp** | `TEXT` | NO | - | NO |
| **n_votes** | `ANY` | NO | - | NO |
| **consensus_temp** | `ANY` | NO | - | NO |
| **std_temp** | `ANY` | NO | - | NO |
| **consensus_pres** | `ANY` | NO | - | NO |
| **std_pres** | `ANY` | NO | - | NO |
| **consensus_rh** | `ANY` | NO | - | NO |
| **std_rh** | `ANY` | NO | - | NO |
| **consensus_wind** | `ANY` | NO | - | NO |
| **std_wind** | `ANY` | NO | - | NO |
| **consensus_solar** | `ANY` | NO | - | NO |
| **std_solar** | `ANY` | NO | - | NO |
| **consensus_rain** | `ANY` | NO | - | NO |
| **std_rain** | `ANY` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |
| **sensor_specs** | `TEXT` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260915_164154/waid_mock_deploy.db`

#### Table: `public_forecasts`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **temp_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **abs_error_temp** | `REAL` | NO | - | NO |
| **abs_error_rh** | `REAL` | NO | - | NO |
| **abs_error_pres** | `REAL` | NO | - | NO |
| **abs_error_wind** | `REAL` | NO | - | NO |
| **abs_error_rain** | `REAL` | NO | - | NO |
| **abs_error_solar** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/backups/backup_soft_reset_20260915_164451/waid_mock.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_forecast`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **model_version** | `TEXT` | NO | - | YES |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias** | `REAL` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |
| **ts_window_start** | `TEXT` | NO | - | NO |
| **ts_window_stop** | `TEXT` | NO | - | NO |

#### Table: `inference_quality`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `ANY` | NO | - | NO |
| **pred_rain** | `ANY` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |
| **temp_era5** | `ANY` | NO | - | NO |
| **pres_era5** | `ANY` | NO | - | NO |
| **rh_era5** | `ANY` | NO | - | NO |
| **wind_era5** | `ANY` | NO | - | NO |
| **solar_era5** | `ANY` | NO | - | NO |
| **rain_era5** | `ANY` | NO | - | NO |
| **delta_temp** | `ANY` | NO | - | NO |
| **delta_pres** | `ANY` | NO | - | NO |
| **delta_rh** | `ANY` | NO | - | NO |
| **delta_wind** | `ANY` | NO | - | NO |
| **delta_solar** | `ANY` | NO | - | NO |
| **delta_rain** | `ANY` | NO | - | NO |
| **abs_error_temp** | `ANY` | NO | - | NO |
| **abs_error_pres** | `ANY` | NO | - | NO |
| **abs_error_rh** | `ANY` | NO | - | NO |
| **abs_error_wind** | `ANY` | NO | - | NO |
| **abs_error_solar** | `ANY` | NO | - | NO |
| **abs_error_rain** | `ANY` | NO | - | NO |
| **perc_error_temp** | `ANY` | NO | - | NO |
| **perc_error_pres** | `ANY` | NO | - | NO |
| **perc_error_rh** | `ANY` | NO | - | NO |
| **perc_error_wind** | `ANY` | NO | - | NO |
| **perc_error_solar** | `ANY` | NO | - | NO |
| **perc_error_rain** | `ANY` | NO | - | NO |

#### Table: `inference_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **id** | `INTEGER` | NO | - | YES |
| **ts_emission** | `DATETIME` | NO | CURRENT_TIMESTAMP | NO |
| **ts_window_start** | `DATETIME` | NO | - | NO |
| **ts_window_end** | `DATETIME` | NO | - | NO |
| **timestamp** | `DATETIME` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **model_version_tag** | `TEXT` | NO | - | NO |
| **n_features_used** | `INTEGER` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_stats`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | NO |
| **timestamp** | `TEXT` | NO | - | NO |
| **n_votes** | `ANY` | NO | - | NO |
| **consensus_temp** | `ANY` | NO | - | NO |
| **std_temp** | `ANY` | NO | - | NO |
| **consensus_pres** | `ANY` | NO | - | NO |
| **std_pres** | `ANY` | NO | - | NO |
| **consensus_rh** | `ANY` | NO | - | NO |
| **std_rh** | `ANY` | NO | - | NO |
| **consensus_wind** | `ANY` | NO | - | NO |
| **std_wind** | `ANY` | NO | - | NO |
| **consensus_solar** | `ANY` | NO | - | NO |
| **std_solar** | `ANY` | NO | - | NO |
| **consensus_rain** | `ANY` | NO | - | NO |
| **std_rain** | `ANY` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |
| **sensor_specs** | `TEXT` | NO | - | NO |

---

### 📁 Database File: `data/matches/all_matches.db`

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **time** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/waid.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_forecast`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **model_version** | `TEXT` | NO | - | YES |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias** | `REAL` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |
| **ts_window_start** | `TEXT` | NO | - | NO |
| **ts_window_stop** | `TEXT` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |

#### Table: `inference_quality`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `ANY` | NO | - | NO |
| **pred_rain** | `ANY` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |
| **temp_era5** | `ANY` | NO | - | NO |
| **pres_era5** | `ANY` | NO | - | NO |
| **rh_era5** | `ANY` | NO | - | NO |
| **wind_era5** | `ANY` | NO | - | NO |
| **solar_era5** | `ANY` | NO | - | NO |
| **rain_era5** | `ANY` | NO | - | NO |
| **delta_temp** | `ANY` | NO | - | NO |
| **delta_pres** | `ANY` | NO | - | NO |
| **delta_rh** | `ANY` | NO | - | NO |
| **delta_wind** | `ANY` | NO | - | NO |
| **delta_solar** | `ANY` | NO | - | NO |
| **delta_rain** | `ANY` | NO | - | NO |
| **abs_error_temp** | `ANY` | NO | - | NO |
| **abs_error_pres** | `ANY` | NO | - | NO |
| **abs_error_rh** | `ANY` | NO | - | NO |
| **abs_error_wind** | `ANY` | NO | - | NO |
| **abs_error_solar** | `ANY` | NO | - | NO |
| **abs_error_rain** | `ANY` | NO | - | NO |
| **perc_error_temp** | `ANY` | NO | - | NO |
| **perc_error_pres** | `ANY` | NO | - | NO |
| **perc_error_rh** | `ANY` | NO | - | NO |
| **perc_error_wind** | `ANY` | NO | - | NO |
| **perc_error_solar** | `ANY` | NO | - | NO |
| **perc_error_rain** | `ANY` | NO | - | NO |

#### Table: `inference_stats`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | NO |
| **timestamp** | `TEXT` | NO | - | NO |
| **n_votes** | `ANY` | NO | - | NO |
| **consensus_temp** | `ANY` | NO | - | NO |
| **std_temp** | `ANY` | NO | - | NO |
| **consensus_pres** | `ANY` | NO | - | NO |
| **std_pres** | `ANY` | NO | - | NO |
| **consensus_rh** | `ANY` | NO | - | NO |
| **std_rh** | `ANY` | NO | - | NO |
| **consensus_wind** | `ANY` | NO | - | NO |
| **std_wind** | `ANY` | NO | - | NO |
| **consensus_solar** | `ANY` | NO | - | NO |
| **std_solar** | `ANY` | NO | - | NO |
| **consensus_rain** | `ANY` | NO | - | NO |
| **std_rain** | `ANY` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |
| **sensor_specs** | `TEXT` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/waid_deploy.db`

#### Table: `public_forecasts`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **temp_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **abs_error_temp** | `REAL` | NO | - | NO |
| **abs_error_rh** | `REAL` | NO | - | NO |
| **abs_error_pres** | `REAL` | NO | - | NO |
| **abs_error_wind** | `REAL` | NO | - | NO |
| **abs_error_rain** | `REAL` | NO | - | NO |
| **abs_error_solar** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/waid_mock.db`

#### Table: `ecowitt_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **epoch_timestamp** | `INTEGER` | NO | - | NO |
| **indoor_temperature_c** | `REAL` | NO | - | NO |
| **indoor_humidity** | `REAL` | NO | - | NO |
| **outdoor_temperature_c** | `REAL` | NO | - | NO |
| **outdoor_humidity** | `REAL` | NO | - | NO |
| **dew_point_c** | `REAL` | NO | - | NO |
| **feels_like_c** | `REAL` | NO | - | NO |
| **vpd_kpa** | `REAL` | NO | - | NO |
| **wind_m_s** | `REAL` | NO | - | NO |
| **gust_m_s** | `REAL` | NO | - | NO |
| **wind_direction_deg** | `REAL` | NO | - | NO |
| **abs_pressure_hpa** | `REAL` | NO | - | NO |
| **rel_pressure_hpa** | `REAL` | NO | - | NO |
| **solar_rad_w_m2** | `REAL` | NO | - | NO |
| **uv_index** | `REAL` | NO | - | NO |
| **rain_rate_mm_hr** | `REAL` | NO | - | NO |
| **hourly_rain_mm** | `REAL` | NO | - | NO |
| **event_rain_mm** | `REAL` | NO | - | NO |
| **daily_rain_mm** | `REAL` | NO | - | NO |
| **weekly_rain_mm** | `REAL` | NO | - | NO |
| **monthly_rain_mm** | `REAL` | NO | - | NO |
| **yearly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_rate_mm_hr** | `REAL` | NO | - | NO |
| **piezo_hourly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_event_rain_mm** | `REAL` | NO | - | NO |
| **piezo_daily_rain_mm** | `REAL` | NO | - | NO |
| **piezo_weekly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_monthly_rain_mm** | `REAL` | NO | - | NO |
| **piezo_yearly_rain_mm** | `REAL` | NO | - | NO |

#### Table: `inference_forecast`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **model_version** | `TEXT` | NO | - | YES |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias** | `REAL` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |
| **ts_window_start** | `TEXT` | NO | - | NO |
| **ts_window_stop** | `TEXT` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |

#### Table: `inference_quality`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_solar** | `ANY` | NO | - | NO |
| **pred_rain** | `ANY` | NO | - | NO |
| **actual_temp** | `REAL` | NO | - | NO |
| **actual_pres** | `REAL` | NO | - | NO |
| **actual_rh** | `REAL` | NO | - | NO |
| **actual_wind** | `REAL` | NO | - | NO |
| **actual_solar** | `REAL` | NO | - | NO |
| **actual_rain** | `REAL` | NO | - | NO |
| **temp_era5** | `ANY` | NO | - | NO |
| **pres_era5** | `ANY` | NO | - | NO |
| **rh_era5** | `ANY` | NO | - | NO |
| **wind_era5** | `ANY` | NO | - | NO |
| **solar_era5** | `ANY` | NO | - | NO |
| **rain_era5** | `ANY` | NO | - | NO |
| **delta_temp** | `ANY` | NO | - | NO |
| **delta_pres** | `ANY` | NO | - | NO |
| **delta_rh** | `ANY` | NO | - | NO |
| **delta_wind** | `ANY` | NO | - | NO |
| **delta_solar** | `ANY` | NO | - | NO |
| **delta_rain** | `ANY` | NO | - | NO |
| **abs_error_temp** | `ANY` | NO | - | NO |
| **abs_error_pres** | `ANY` | NO | - | NO |
| **abs_error_rh** | `ANY` | NO | - | NO |
| **abs_error_wind** | `ANY` | NO | - | NO |
| **abs_error_solar** | `ANY` | NO | - | NO |
| **abs_error_rain** | `ANY` | NO | - | NO |
| **perc_error_temp** | `ANY` | NO | - | NO |
| **perc_error_pres** | `ANY` | NO | - | NO |
| **perc_error_rh** | `ANY` | NO | - | NO |
| **perc_error_wind** | `ANY` | NO | - | NO |
| **perc_error_solar** | `ANY` | NO | - | NO |
| **perc_error_rain** | `ANY` | NO | - | NO |

#### Table: `inference_stats`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | NO |
| **timestamp** | `TEXT` | NO | - | NO |
| **n_votes** | `ANY` | NO | - | NO |
| **consensus_temp** | `ANY` | NO | - | NO |
| **std_temp** | `ANY` | NO | - | NO |
| **consensus_pres** | `ANY` | NO | - | NO |
| **std_pres** | `ANY` | NO | - | NO |
| **consensus_rh** | `ANY` | NO | - | NO |
| **std_rh** | `ANY` | NO | - | NO |
| **consensus_wind** | `ANY` | NO | - | NO |
| **std_wind** | `ANY` | NO | - | NO |
| **consensus_solar** | `ANY` | NO | - | NO |
| **std_solar** | `ANY` | NO | - | NO |
| **consensus_rain** | `ANY` | NO | - | NO |
| **std_rain** | `ANY` | NO | - | NO |

#### Table: `int_matches_bias`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **ecowitt_temp** | `ANY` | NO | - | NO |
| **era5_temp** | `ANY` | NO | - | NO |
| **bias_temp** | `ANY` | NO | - | NO |
| **ecowitt_pres** | `ANY` | NO | - | NO |
| **era5_pres** | `ANY` | NO | - | NO |
| **bias_pres** | `ANY` | NO | - | NO |
| **ecowitt_rh** | `ANY` | NO | - | NO |
| **era5_rh** | `ANY` | NO | - | NO |
| **bias_rh** | `ANY` | NO | - | NO |
| **ecowitt_wind** | `ANY` | NO | - | NO |
| **era5_wind** | `ANY` | NO | - | NO |
| **bias_wind** | `ANY` | NO | - | NO |
| **ecowitt_solar** | `ANY` | NO | - | NO |
| **era5_solar** | `ANY` | NO | - | NO |
| **bias_solar** | `ANY` | NO | - | NO |
| **ecowitt_rain** | `ANY` | NO | - | NO |
| **era5_rain** | `ANY` | NO | - | NO |
| **bias_rain** | `ANY` | NO | - | NO |
| **bias_overflow_flag** | `ANY` | NO | - | NO |

#### Table: `match_records`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | YES |
| **temp_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **temp_eco** | `REAL` | NO | - | NO |
| **pres_eco** | `REAL` | NO | - | NO |
| **rh_eco** | `REAL` | NO | - | NO |
| **wind_eco** | `REAL` | NO | - | NO |
| **solar_eco** | `REAL` | NO | - | NO |
| **rain_eco** | `REAL` | NO | - | NO |

#### Table: `ml_model_registry`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **model_version** | `TEXT` | NO | - | YES |
| **station_id** | `TEXT` | YES | - | NO |
| **trained_at** | `TEXT` | YES | - | NO |
| **last_ecowitt_timestamp** | `TEXT` | YES | - | NO |
| **train_samples_count** | `INTEGER` | YES | - | NO |
| **x_scaler_path** | `TEXT` | YES | - | NO |
| **y_scaler_path** | `TEXT` | YES | - | NO |
| **model_path** | `TEXT` | YES | - | NO |
| **metrics_mse** | `REAL` | NO | - | NO |
| **is_active** | `INTEGER` | NO | 1 | NO |

#### Table: `station_metadata`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **station_id** | `ANY` | NO | - | NO |
| **station_name** | `ANY` | NO | - | NO |
| **latitude** | `REAL` | NO | - | NO |
| **longitude** | `REAL` | NO | - | NO |
| **elevation_m** | `ANY` | NO | - | NO |
| **height_above_ground_m** | `ANY` | NO | - | NO |
| **min_training_days** | `INT` | NO | - | NO |
| **retrain_window_days** | `INT` | NO | - | NO |
| **updated_at** | `ANY` | NO | - | NO |
| **sensor_specs** | `TEXT` | NO | - | NO |

#### Table: `stg_ecowitt`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **temperature** | `REAL` | NO | - | NO |
| **humidity** | `REAL` | NO | - | NO |
| **pressure_hpa** | `REAL` | NO | - | NO |
| **wind_speed** | `REAL` | NO | - | NO |
| **solar_radiation** | `REAL` | NO | - | NO |
| **hourly_rain** | `REAL` | NO | - | NO |

---

### 📁 Database File: `data/waid_mock_deploy.db`

#### Table: `public_forecasts`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **temp_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **abs_error_temp** | `REAL` | NO | - | NO |
| **abs_error_rh** | `REAL` | NO | - | NO |
| **abs_error_pres** | `REAL` | NO | - | NO |
| **abs_error_wind** | `REAL` | NO | - | NO |
| **abs_error_rain** | `REAL` | NO | - | NO |
| **abs_error_solar** | `REAL` | NO | - | NO |

---

### 📁 Database File: `deploy/data/waid_deploy.db`

#### Table: `public_forecasts`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **temp_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **abs_error_temp** | `REAL` | NO | - | NO |
| **abs_error_rh** | `REAL` | NO | - | NO |
| **abs_error_pres** | `REAL` | NO | - | NO |
| **abs_error_wind** | `REAL` | NO | - | NO |
| **abs_error_rain** | `REAL` | NO | - | NO |
| **abs_error_solar** | `REAL` | NO | - | NO |

---

### 📁 Database File: `deploy/data/waid_mock_deploy.db`

#### Table: `public_forecasts`

| Column | Type | NotNull | Default | PK |
| :--- | :--- | :--- | :--- | :--- |
| **timestamp** | `TEXT` | NO | - | NO |
| **created_at** | `TEXT` | NO | - | NO |
| **model_version** | `TEXT` | NO | - | NO |
| **pred_temp** | `REAL` | NO | - | NO |
| **pred_rh** | `REAL` | NO | - | NO |
| **pred_pres** | `REAL` | NO | - | NO |
| **pred_wind** | `REAL` | NO | - | NO |
| **pred_rain** | `REAL` | NO | - | NO |
| **pred_solar** | `REAL` | NO | - | NO |
| **diff_temp** | `REAL` | NO | - | NO |
| **diff_rh** | `REAL` | NO | - | NO |
| **diff_pres** | `REAL` | NO | - | NO |
| **diff_wind** | `REAL` | NO | - | NO |
| **diff_rain** | `REAL` | NO | - | NO |
| **diff_solar** | `REAL` | NO | - | NO |
| **historical_bias_temp** | `REAL` | NO | - | NO |
| **historical_bias_rh** | `REAL` | NO | - | NO |
| **historical_bias_pres** | `REAL` | NO | - | NO |
| **historical_bias_wind** | `REAL` | NO | - | NO |
| **historical_bias_rain** | `REAL` | NO | - | NO |
| **historical_bias_solar** | `REAL` | NO | - | NO |
| **drift_vs_bias_temp** | `REAL` | NO | - | NO |
| **drift_vs_bias_rh** | `REAL` | NO | - | NO |
| **drift_vs_bias_pres** | `REAL` | NO | - | NO |
| **drift_vs_bias_wind** | `REAL` | NO | - | NO |
| **drift_vs_bias_rain** | `REAL` | NO | - | NO |
| **drift_vs_bias_solar** | `REAL` | NO | - | NO |
| **temp_era5** | `REAL` | NO | - | NO |
| **rh_era5** | `REAL` | NO | - | NO |
| **pres_era5** | `REAL` | NO | - | NO |
| **wind_era5** | `REAL` | NO | - | NO |
| **rain_era5** | `REAL` | NO | - | NO |
| **solar_era5** | `REAL` | NO | - | NO |
| **abs_error_temp** | `REAL` | NO | - | NO |
| **abs_error_rh** | `REAL` | NO | - | NO |
| **abs_error_pres** | `REAL` | NO | - | NO |
| **abs_error_wind** | `REAL` | NO | - | NO |
| **abs_error_rain** | `REAL` | NO | - | NO |
| **abs_error_solar** | `REAL` | NO | - | NO |

---

