{{ config(
    materialized='table'
) }}

/**
 * @file stg_ecowitt.sql
 * @brief Staging model to clean, type-cast, and standardize raw Ecowitt weather records.
 * @details Pulls raw data from the external source, filters invalid timestamps, and casts parameters to REAL.
 * @author AF
 * @date 2026
 */

WITH source_data AS (
    -- Select all records from the raw Ecowitt source table
    SELECT * FROM {{ source('external_raw', 'ecowitt_records') }}
)

SELECT
    timestamp,
    CAST(outdoor_temperature_c AS REAL) AS temperature,
    CAST(outdoor_humidity AS REAL) AS humidity,
    CAST(abs_pressure_hpa AS REAL) AS pressure_hpa,
    CAST(wind_m_s AS REAL) AS wind_speed,
    CAST(solar_rad_w_m2 AS REAL) AS solar_radiation,
    CAST(hourly_rain_mm AS REAL) AS hourly_rain
FROM source_data
WHERE timestamp IS NOT NULL