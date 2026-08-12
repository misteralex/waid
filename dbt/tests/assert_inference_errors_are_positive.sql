{{ config(severity='warn') }}

SELECT
    ts_target,
    abs_error_temp,
    abs_error_pres
FROM {{ ref('inference_quality') }}
WHERE abs_error_temp < 0 
   OR abs_error_pres < 0