{{ config(materialized='table') }}

/**
 * @file int_matches_bias.sql
 * @brief Intermediate dbt model for computing and evaluating operational biases between Ecowitt and ERA5.
 * @details Cleans raw string values to NULL, casts features to float, calculates feature deltas, and flags threshold overflows.
 * @author AF
 * @date 2026
 */

WITH cleaned_source AS (
    SELECT
        timestamp,
        -- Force empty/blank strings to actual NULLs for SQLite mathematical safety
        CASE WHEN temp_era5 = '' OR TRIM(temp_era5) = '' THEN NULL ELSE CAST(temp_era5 AS FLOAT) END AS temp_era5,
        CASE WHEN temp_eco = '' OR TRIM(temp_eco) = '' THEN NULL ELSE CAST(temp_eco AS FLOAT) END AS temp_eco,
        
        CASE WHEN pres_era5 = '' OR TRIM(pres_era5) = '' THEN NULL ELSE CAST(pres_era5 AS FLOAT) END AS pres_era5,
        CASE WHEN pres_eco = '' OR TRIM(pres_eco) = '' THEN NULL ELSE CAST(pres_eco AS FLOAT) END AS pres_eco,
        
        CASE WHEN rh_era5 = '' OR TRIM(rh_era5) = '' THEN NULL ELSE CAST(rh_era5 AS FLOAT) END AS rh_era5,
        CASE WHEN rh_eco = '' OR TRIM(rh_eco) = '' THEN NULL ELSE CAST(rh_eco AS FLOAT) END AS rh_eco,
        
        CASE WHEN wind_era5 = '' OR TRIM(wind_era5) = '' THEN NULL ELSE CAST(wind_era5 AS FLOAT) END AS wind_era5,
        CASE WHEN wind_eco = '' OR TRIM(wind_eco) = '' THEN NULL ELSE CAST(wind_eco AS FLOAT) END AS wind_eco,
        
        CASE WHEN solar_era5 = '' OR TRIM(solar_era5) = '' THEN NULL ELSE CAST(solar_era5 AS FLOAT) END AS solar_era5,
        CASE WHEN solar_eco = '' OR TRIM(solar_eco) = '' THEN NULL ELSE CAST(solar_eco AS FLOAT) END AS solar_eco,
        
        CASE WHEN rain_era5 = '' OR TRIM(rain_era5) = '' THEN NULL ELSE CAST(rain_era5 AS FLOAT) END AS rain_era5,
        CASE WHEN rain_eco = '' OR TRIM(rain_eco) = '' THEN NULL ELSE CAST(rain_eco AS FLOAT) END AS rain_eco
    FROM {{ source('external_raw', 'match_records') }}
),

base_biases AS (
    -- Compute raw differences (biases) between local sensor records and ERA5 baseline
    SELECT
        timestamp,
        temp_eco AS ecowitt_temp,
        temp_era5 AS era5_temp,
        (temp_eco - temp_era5) AS bias_temp,

        pres_eco AS ecowitt_pres,
        pres_era5 AS era5_pres,
        (pres_eco - pres_era5) AS bias_pres,

        rh_eco AS ecowitt_rh,
        rh_era5 AS era5_rh,
        (rh_eco - rh_era5) AS bias_rh,

        wind_eco AS ecowitt_wind,
        wind_era5 AS era5_wind,
        (wind_eco - wind_era5) AS bias_wind,

        solar_eco AS ecowitt_solar,
        solar_era5 AS era5_solar,
        (solar_eco - solar_era5) AS bias_solar,

        rain_eco AS ecowitt_rain,
        rain_era5 AS era5_rain,
        (rain_eco - rain_era5) AS bias_rain
    FROM cleaned_source
)

SELECT
    *,
    -- Evaluate absolute thresholds strictly against numeric values and flag overflows
    CASE 
        WHEN ABS(bias_temp)  > CAST('{{ var("max_bias_temp") }}' AS FLOAT)  OR
             ABS(bias_pres)  > CAST('{{ var("max_bias_pres") }}' AS FLOAT)  OR
             ABS(bias_rh)    > CAST('{{ var("max_bias_rh") }}' AS FLOAT)    OR
             ABS(bias_wind)  > CAST('{{ var("max_bias_wind") }}' AS FLOAT)  OR
             ABS(bias_solar) > CAST('{{ var("max_bias_solar") }}' AS FLOAT) OR
             ABS(bias_rain)  > CAST('{{ var("max_bias_rain") }}' AS FLOAT)
        THEN 1
        ELSE 0
    END AS bias_overflow_flag
FROM base_biases