{{ config(
    materialized='incremental',
    unique_key=['timestamp', 'model_version'],
    indexes=[{'columns': ['timestamp']}]
) }}

/**
 * @file inference_quality.sql
 * @brief dbt incremental model to evaluate forecast quality vs actuals and ERA5 benchmark.
 * @details Joins ML model inference predictions with Ecowitt ground-truth observations 
 *          and ERA5 reanalysis data to compute absolute deltas and percentage error metrics.
 */

-- Retrieve the mock timestamp either from dbt --vars or from environment variable
{% set mock_now = var('waid_mock_now', env_var('WAID_MOCK_NOW', '')) %}

WITH source_predictions AS (
    /**
     * @brief Extract raw model forecast predictions.
     * @details Filters predictions based on incremental lookback window (-3 days) 
     *          and optional mock timestamp boundary. Clips non-physical values.
     */
    SELECT
        timestamp,
        model_version,
        created_at AS ts_emission,
        pred_temp,
        pred_pres,
        pred_rh,
        pred_wind,
        CASE WHEN pred_solar > 0.0 THEN pred_solar ELSE 0.0 END AS pred_solar,
        CASE WHEN pred_rain > 0.0 THEN pred_rain ELSE 0.0 END AS pred_rain
    FROM {{ source('external_raw', 'inference_forecast') }}
    WHERE 1=1

    {% if is_incremental() %}
    AND created_at >= datetime((SELECT COALESCE(MAX(timestamp), '1970-01-01 00:00:00') FROM {{ this }}), '-3 day')
    {% endif %}
    
    {% if mock_now != '' %}
    AND created_at <= '{{ mock_now }}'
    {% endif %}
),

source_actuals AS (
    /**
     * @brief Extract actual ground-truth weather station observations.
     */
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

source_era5 AS (
    /**
     * @brief Extract ERA5 reanalysis benchmark dataset.
     */
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
    
    -- Deltas (vs Ecowitt)
    (p.pred_temp - a.actual_temp) AS delta_temp,
    (p.pred_pres - a.actual_pres) AS delta_pres,
    (p.pred_rh - a.actual_rh) AS delta_rh,
    (p.pred_wind - a.actual_wind) AS delta_wind,
    (p.pred_solar - a.actual_solar) AS delta_solar,
    (p.pred_rain - a.actual_rain) AS delta_rain,

    -- Absolute Errors (vs ERA5 Reanalysis Benchmark)
    ABS(p.pred_temp - e.temp_era5) AS abs_error_temp,
    ABS(p.pred_pres - e.pres_era5) AS abs_error_pres,
    ABS(p.pred_rh - e.rh_era5) AS abs_error_rh,
    ABS(p.pred_wind - e.wind_era5) AS abs_error_wind,
    ABS(p.pred_solar - e.solar_era5) AS abs_error_solar,
    ABS(p.pred_rain - e.rain_era5) AS abs_error_rain,
    
    -- Percentage Errors (vs ERA5)
    (ABS(p.pred_temp - e.temp_era5) / NULLIF(e.temp_era5, 0)) * 100 AS perc_error_temp,
    (ABS(p.pred_pres - e.pres_era5) / NULLIF(e.pres_era5, 0)) * 100 AS perc_error_pres,
    (ABS(p.pred_rh - e.rh_era5) / NULLIF(e.rh_era5, 0)) * 100 AS perc_error_rh,
    (ABS(p.pred_wind - e.wind_era5) / NULLIF(e.wind_era5, 0)) * 100 AS perc_error_wind,
    (ABS(p.pred_solar - e.solar_era5) / NULLIF(e.solar_era5, 0)) * 100 AS perc_error_solar,
    (ABS(p.pred_rain - e.rain_era5) / NULLIF(e.rain_era5, 0)) * 100 AS perc_error_rain

FROM source_predictions p
LEFT JOIN source_actuals a 
    ON p.timestamp = a.timestamp
LEFT JOIN source_era5 e
    ON p.timestamp = e.timestamp