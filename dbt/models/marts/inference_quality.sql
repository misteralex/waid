{{ config(
    materialized='incremental',
    unique_key='timestamp',
    indexes=[{'columns': ['timestamp']}]
) }}

/**
 * @file inference_evaluation.sql
 * @brief Incremental dbt model to evaluate model prediction performance against actuals and ERA5 benchmarks.
 * @details Joins predictions, local Ecowitt actuals, and ERA5 baselines to compute deltas, absolute errors, and percentage errors.
 * @author AF
 * @date 2026
 */

WITH source_predictions AS (
    -- Extract and clean model predictions with incremental window filtering
    SELECT
        timestamp,
        model_version,
        pred_temp,
        pred_pres,
        pred_rh,
        pred_wind,
        CASE WHEN pred_solar > 0.0 THEN pred_solar ELSE 0.0 END AS pred_solar,
        CASE WHEN pred_rain > 0.0 THEN pred_rain ELSE 0.0 END AS pred_rain
    FROM {{ ref('inference_prediction') }}
    {% if is_incremental() %}
    -- Process records from the last 3 days for incremental efficiency
    WHERE timestamp >= datetime((SELECT COALESCE(MAX(timestamp), '1970-01-01 00:00:00') FROM {{ this }}), '-3 day')
    {% endif %}
),

source_actuals AS (
    -- Extract actual verified weather records from the Ecowitt staging model
    SELECT 
        timestamp,
        temperature AS actual_temp,
        pressure_hpa AS actual_pres,
        humidity AS actual_rh,
        wind_speed AS actual_wind,
        solar_radiation AS actual_solar,
        hourly_rain AS actual_rain
    FROM {{ ref('stg_ecowitt') }}
    WHERE temperature IS NOT NULL
),

-- Refactored to use int_matches_bias instead of the deleted int_matches_normalized
source_era5 AS (
    -- Extract ERA5 reanalysis baseline values for comparison
    SELECT
        timestamp,
        era5_temp AS temp_era5,
        era5_pres AS pres_era5,
        era5_rh AS rh_era5,
        era5_wind AS wind_era5,
        era5_solar AS solar_era5,
        era5_rain AS rain_era5
    FROM {{ ref('int_matches_bias') }}
)

-- Combine predictions, actuals, and benchmarks to compute evaluation metrics
SELECT
    p.timestamp,
    p.model_version,
    
    -- Predicted Values
    p.pred_temp,
    p.pred_pres,
    p.pred_rh,
    p.pred_wind,
    p.pred_solar,
    p.pred_rain,
    
    -- Actual Ecowitt Values
    a.actual_temp,
    a.actual_pres,
    a.actual_rh,
    a.actual_wind,
    a.actual_solar,
    a.actual_rain,

    -- ERA5 Benchmark Values
    e.temp_era5,
    e.pres_era5,
    e.rh_era5,
    e.wind_era5,
    e.solar_era5,
    e.rain_era5,
    
    -- Deltas (Prediction vs Actual Ecowitt)
    (p.pred_temp - a.actual_temp) AS delta_temp,
    (p.pred_pres - a.actual_pres) AS delta_pres,
    (p.pred_rh - a.actual_rh) AS delta_rh,
    (p.pred_wind - a.actual_wind) AS delta_wind,
    (p.pred_solar - a.actual_solar) AS delta_solar,
    (p.pred_rain - a.actual_rain) AS delta_rain,

    -- Absolute Errors (Prediction vs Actual Ecowitt)
    ABS(p.pred_temp - a.actual_temp) AS abs_error_temp,
    ABS(p.pred_pres - a.actual_pres) AS abs_error_pres,
    ABS(p.pred_rh - a.actual_rh) AS abs_error_rh,
    ABS(p.pred_wind - a.actual_wind) AS abs_error_wind,
    ABS(p.pred_solar - a.actual_solar) AS abs_error_solar,
    ABS(p.pred_rain - a.actual_rain) AS abs_error_rain,
    
    -- Percentage Errors (Prediction vs Actual Ecowitt)
    (ABS(p.pred_temp - a.actual_temp) / NULLIF(a.actual_temp, 0)) * 100 AS perc_error_temp,
    (ABS(p.pred_pres - a.actual_pres) / NULLIF(a.actual_pres, 0)) * 100 AS perc_error_pres,
    (ABS(p.pred_rh - a.actual_rh) / NULLIF(a.actual_rh, 0)) * 100 AS perc_error_rh,
    (ABS(p.pred_wind - a.actual_wind) / NULLIF(a.actual_wind, 0)) * 100 AS perc_error_wind,
    (ABS(p.pred_solar - a.actual_solar) / NULLIF(a.actual_solar, 0)) * 100 AS perc_error_solar,
    (ABS(p.pred_rain - a.actual_rain) / NULLIF(a.actual_rain, 0)) * 100 AS perc_error_rain

FROM source_predictions p
INNER JOIN source_actuals a 
    ON p.timestamp = a.timestamp
LEFT JOIN source_era5 e
    ON p.timestamp = e.timestamp