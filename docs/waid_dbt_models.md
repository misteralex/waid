# 📊 dbt Models Documentation

> Automatically generated report from dbt `manifest.json`.

---

## 🏗️ Model: `int_matches_bias`

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

## 🏗️ Model: `inference_stats`

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

## 🏗️ Model: `inference_quality`

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

## 🏗️ Model: `station_metadata`

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

## 🏗️ Model: `stg_ecowitt`

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

## 🏗️ Model: `stg_matches`

**Schema:** `main`  
**Description:** Dataset unificato di validazione tra Ecowitt e ERA5

| Column | Data Type | Description |
| :--- | :--- | :--- |
| **timestamp** | `None` |  |
| **ecowitt_temp** | `None` |  |
| **era5_temp** | `None` |  |
| **bias_temp** | `None` | Differenza assoluta tra temperatura Ecowitt e ERA5 |

---

