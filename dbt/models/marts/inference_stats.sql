{{ config(
    materialized='table',
    indexes=[{'columns': ['model_version']}]
) }}

/**
 * @file inference_stats.sql
 * @brief dbt model to compute statistical metrics across model inference records.
 * @details Aggregates temperature, pressure, humidity, wind, solar, and rain forecasts grouped by model version and tag.
 * @author AF
 * @date 2026
 */

-- Definizione della variabile dallo standard d'ambiente
{% set mock_now = env_var('WAID_MOCK_NOW', '') %}

SELECT
    model_version,
    model_version_tag,
    
    -- Temperature Forecast Stats
    AVG(outdoor_temperature_c) AS avg_temp,
    SQRT(AVG(outdoor_temperature_c * outdoor_temperature_c) - AVG(outdoor_temperature_c) * AVG(outdoor_temperature_c)) AS std_temp,
    
    -- Pressure Forecast Stats
    AVG(abs_pressure_hpa) AS avg_pres,
    SQRT(AVG(abs_pressure_hpa * abs_pressure_hpa) - AVG(abs_pressure_hpa) * AVG(abs_pressure_hpa)) AS std_pres,
    
    -- Humidity Forecast Stats
    AVG(outdoor_humidity) AS avg_rh,
    SQRT(AVG(outdoor_humidity * outdoor_humidity) - AVG(outdoor_humidity) * AVG(outdoor_humidity)) AS std_rh,
    
    -- Wind Forecast Stats
    AVG(wind_m_s) AS avg_wind,
    SQRT(AVG(wind_m_s * wind_m_s) - AVG(wind_m_s) * AVG(wind_m_s)) AS std_wind,
    
    -- Solar Forecast Stats
    AVG(solar_rad_w_m2) AS avg_solar,
    SQRT(AVG(solar_rad_w_m2 * solar_rad_w_m2) - AVG(solar_rad_w_m2) * AVG(solar_rad_w_m2)) AS std_solar,
    
    -- Rain Forecast Stats
    AVG(hourly_rain_mm) AS avg_rain,
    SQRT(AVG(hourly_rain_mm * hourly_rain_mm) - AVG(hourly_rain_mm) * AVG(hourly_rain_mm)) AS std_rain

FROM {{ source('external_raw', 'inference_records') }}
WHERE 1=1
{% if mock_now is not none %}
  AND timestamp <= '{{ mock_now }}'
{% endif %}
GROUP BY model_version, model_version_tag