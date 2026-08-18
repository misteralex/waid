{{ config(
    materialized='incremental',
    unique_key='timestamp',
    indexes=[{'columns': ['timestamp']}]
) }}

/**
 * @file inference_prediction.sql
 * @brief Incremental staging model for live inference data processing.
 * @details Extracts and standardizes new prediction records from the raw source table using an incremental strategy.
 * @author AF
 * @date 2026
 */

{% set mock_now = env_var('WAID_MOCK_NOW', '') %}

WITH new_predictions AS (
    SELECT
        lp.timestamp,
        lp.model_version,
        lp.outdoor_temperature_c AS pred_temp,
        lp.abs_pressure_hpa AS pred_pres,
        lp.outdoor_humidity AS pred_rh,
        lp.wind_m_s AS pred_wind,
        lp.solar_rad_w_m2 AS pred_solar,
        lp.hourly_rain_mm AS pred_rain
    FROM {{ source('external_raw', 'inference_records') }} lp
    WHERE 1=1
    {% if mock_now is not none %}
      AND lp.timestamp <= '{{ mock_now }}'
    {% endif %}

    {% if is_incremental() %}
      -- Process only predictions subsequent to the last saved one
      AND lp.timestamp > (SELECT COALESCE(MAX(timestamp), '1970-01-01 00:00:00') FROM {{ this }})
    {% endif %}
)

SELECT * FROM new_predictions