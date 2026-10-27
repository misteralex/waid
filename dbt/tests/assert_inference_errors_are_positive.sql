{{ config(severity='warn') }}

SELECT
    timestamp,
    abs_error_temp,
    abs_error_pres,
    abs_error_rh,
    abs_error_wind,
    abs_error_solar,
    abs_error_rain,
    pred_temp,
    pred_pres,
    pred_rh,
    pred_wind,
    pred_solar,
    pred_rain,
    actual_temp,
    actual_pres,
    actual_rh,
    actual_wind,
    actual_solar,
    actual_rain,
    temp_era5,
    pres_era5,
    rh_era5,
    wind_era5,
    solar_era5,
    rain_era5
FROM {{ ref('inference_quality') }}
WHERE 
    -- 1. Check for disallowed NULL values ​​(prediction key fields, actual values, and their corresponding errors)
    timestamp IS NULL
    OR pred_temp IS NULL OR actual_temp IS NULL
    OR pred_pres IS NULL OR actual_pres IS NULL
    OR pred_rh IS NULL OR actual_rh IS NULL
    OR pred_wind IS NULL OR actual_wind IS NULL
    OR pred_solar IS NULL OR actual_solar IS NULL
    OR pred_rain IS NULL OR actual_rain IS NULL
    OR abs_error_temp IS NULL
    OR abs_error_pres IS NULL
    OR abs_error_rh IS NULL
    OR abs_error_wind IS NULL
    OR abs_error_solar IS NULL
    OR abs_error_rain IS NULL

    -- 2. Checking for negative absolute errors
    OR abs_error_temp < 0 
    OR abs_error_pres < 0
    OR abs_error_rh < 0
    OR abs_error_wind < 0
    OR abs_error_solar < 0
    OR abs_error_rain < 0

    -- 3. Physical sanity check for local variables: strictly positive pressure
    OR pred_pres <= 0 OR actual_pres <= 0

    -- 4. Local physical sanity checks: local wind, solar, and rainfall values ​​are non-negative
    OR pred_wind < 0 OR actual_wind < 0 
    OR pred_solar < 0 OR actual_solar < 0 
    OR pred_rain < 0 OR actual_rain < 0 

    -- 5. Local humidity sanity check (range 0–100%)
    OR pred_rh < 0 OR pred_rh > 100
    OR actual_rh < 0 OR actual_rh > 100

    -- 6. Conditional sanity checks for ERA5 (active only for historical records > 6 days)
    -- Avoid false positives in recent data while accounting for Copernicus latency
    OR (
        timestamp <= datetime('now', '-6 days')
        AND (
            temp_era5 IS NULL 
            OR pres_era5 IS NULL 
            OR rh_era5 IS NULL 
            OR wind_era5 IS NULL 
            OR solar_era5 IS NULL 
            OR rain_era5 IS NULL
            OR pres_era5 <= 0
            OR wind_era5 < 0 
            OR solar_era5 < 0 
            OR rain_era5 < 0
            OR rh_era5 < 0 OR rh_era5 > 100
        )
    )