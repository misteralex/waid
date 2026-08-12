{{ config(materialized='view') }}

/**
 * @file stg_matches.sql
 * @brief Creates a staging view to calculate biases between Ecowitt and ERA5 datasets.
 * @details Computes delta (bias) for temperature, pressure, humidity, wind, solar, and rain.
 * @author AF
 * @date 2026
 */

SELECT
    timestamp,

    -- Temperature metrics
    temp_eco AS ecowitt_temp,
    temp_era5 AS era5_temp,
    (temp_eco - temp_era5) AS bias_temp,

    -- Pressure metrics
    pres_eco AS ecowitt_pres,
    pres_era5 AS era5_pres,
    (pres_eco - pres_era5) AS bias_pres,

    -- Humidity metrics
    rh_eco AS ecowitt_rh,
    rh_era5 AS era5_rh,
    (rh_eco - rh_era5) AS bias_rh,

    -- Wind metrics
    wind_eco AS ecowitt_wind,
    wind_era5 AS era5_wind,
    (wind_eco - wind_era5) AS bias_wind,

    -- Solar radiation metrics
    solar_eco AS ecowitt_solar,
    solar_era5 AS era5_solar,
    (solar_eco - solar_era5) AS bias_solar,

    -- Rain metrics
    rain_eco AS ecowitt_rain,
    rain_era5 AS era5_rain,
    (rain_eco - rain_era5) AS bias_rain

FROM {{ source('external_raw', 'match_records') }}