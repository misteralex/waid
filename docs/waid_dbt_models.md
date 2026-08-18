# 📊 Documentazione Modelli dbt

> Report generato automaticamente dal `manifest.json` di dbt.

---

## 🏗️ Modello: `int_matches_bias`

**Schema:** `main`  
**Descrizione:** Calculated operational bias between Ecowitt telemetry and ERA5 baseline.

| Colonna | Tipo Dati | Descrizione |
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

## 🏗️ Modello: `inference_stats`

**Schema:** `main`  
**Descrizione:** 

| Colonna | Tipo Dati | Descrizione |
| :--- | :--- | :--- |
| **model_version** | `TEXT` |  |
| **model_version_tag** | `TEXT` |  |
| **avg_temp** | `UNKNOWN` |  |
| **std_temp** | `UNKNOWN` |  |
| **avg_pres** | `UNKNOWN` |  |
| **std_pres** | `UNKNOWN` |  |
| **avg_rh** | `UNKNOWN` |  |
| **std_rh** | `UNKNOWN` |  |
| **avg_wind** | `UNKNOWN` |  |
| **std_wind** | `UNKNOWN` |  |
| **avg_solar** | `UNKNOWN` |  |
| **std_solar** | `UNKNOWN` |  |
| **avg_rain** | `UNKNOWN` |  |
| **std_rain** | `UNKNOWN` |  |

---

## 🏗️ Modello: `inference_quality`

**Schema:** `main`  
**Descrizione:** 

| Colonna | Tipo Dati | Descrizione |
| :--- | :--- | :--- |
| **timestamp** | `NUM` |  |
| **model_version** | `TEXT` |  |
| **pred_temp** | `REAL` |  |
| **pred_pres** | `REAL` |  |
| **pred_rh** | `REAL` |  |
| **pred_wind** | `REAL` |  |
| **pred_solar** | `UNKNOWN` |  |
| **pred_rain** | `UNKNOWN` |  |
| **actual_temp** | `REAL` |  |
| **actual_pres** | `REAL` |  |
| **actual_rh** | `REAL` |  |
| **actual_wind** | `REAL` |  |
| **actual_solar** | `REAL` |  |
| **actual_rain** | `REAL` |  |
| **temp_era5** | `UNKNOWN` |  |
| **pres_era5** | `UNKNOWN` |  |
| **rh_era5** | `UNKNOWN` |  |
| **wind_era5** | `UNKNOWN` |  |
| **solar_era5** | `UNKNOWN` |  |
| **rain_era5** | `UNKNOWN` |  |
| **delta_temp** | `UNKNOWN` |  |
| **delta_pres** | `UNKNOWN` |  |
| **delta_rh** | `UNKNOWN` |  |
| **delta_wind** | `UNKNOWN` |  |
| **delta_solar** | `UNKNOWN` |  |
| **delta_rain** | `UNKNOWN` |  |
| **abs_error_temp** | `UNKNOWN` |  |
| **abs_error_pres** | `UNKNOWN` |  |
| **abs_error_rh** | `UNKNOWN` |  |
| **abs_error_wind** | `UNKNOWN` |  |
| **abs_error_solar** | `UNKNOWN` |  |
| **abs_error_rain** | `UNKNOWN` |  |
| **perc_error_temp** | `UNKNOWN` |  |
| **perc_error_pres** | `UNKNOWN` |  |
| **perc_error_rh** | `UNKNOWN` |  |
| **perc_error_wind** | `UNKNOWN` |  |
| **perc_error_solar** | `UNKNOWN` |  |
| **perc_error_rain** | `UNKNOWN` |  |

---

## 🏗️ Modello: `inference_prediction`

**Schema:** `main`  
**Descrizione:** 

| Colonna | Tipo Dati | Descrizione |
| :--- | :--- | :--- |
| **timestamp** | `NUM` |  |
| **model_version** | `TEXT` |  |
| **pred_temp** | `REAL` |  |
| **pred_pres** | `REAL` |  |
| **pred_rh** | `REAL` |  |
| **pred_wind** | `REAL` |  |
| **pred_solar** | `REAL` |  |
| **pred_rain** | `REAL` |  |

---

## 🏗️ Modello: `station_metadata`

**Schema:** `main`  
**Descrizione:** 

| Colonna | Tipo Dati | Descrizione |
| :--- | :--- | :--- |
| **station_id** | `UNKNOWN` |  |
| **station_name** | `UNKNOWN` |  |
| **latitude** | `REAL` |  |
| **longitude** | `REAL` |  |
| **elevation_m** | `UNKNOWN` |  |
| **height_above_ground_m** | `UNKNOWN` |  |
| **min_training_days** | `INT` |  |
| **retrain_window_days** | `INT` |  |
| **updated_at** | `UNKNOWN` |  |
| **sensor_specs** | `TEXT` |  |

---

## 🏗️ Modello: `stg_ecowitt`

**Schema:** `main`  
**Descrizione:** 

| Colonna | Tipo Dati | Descrizione |
| :--- | :--- | :--- |
| **timestamp** | `None` |  |
| **temperature** | `None` |  |
| **pressure_hpa** | `None` |  |
| **humidity** | `None` |  |
| **wind_speed** | `None` |  |
| **solar_radiation** | `None` |  |
| **hourly_rain** | `None` |  |

---

## 🏗️ Modello: `stg_matches`

**Schema:** `main`  
**Descrizione:** Dataset unificato di validazione tra Ecowitt e ERA5

| Colonna | Tipo Dati | Descrizione |
| :--- | :--- | :--- |
| **timestamp** | `None` |  |
| **ecowitt_temp** | `None` |  |
| **era5_temp** | `None` |  |
| **bias_temp** | `None` | Differenza assoluta tra temperatura Ecowitt e ERA5 |

---

