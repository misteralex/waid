{{ config(
    materialized='incremental',
    unique_key='timestamp',
    incremental_strategy='merge',
    indexes=[{'columns': ['timestamp']}]
) }}

/**
 * @file inference_stats.sql
 * @brief dbt incremental model to accumulate and update forecast consensus statistics.
 * @details Groups model inference runs by model version and target timestamp to compute
 *          ensemble averages (consensus) and standard deviations (forecast uncertainty)
 *          across weather metrics.
 * @author AF
 * @date 2026
 */

SELECT
    model_version,
    timestamp,
    
    -- Total prediction runs/votes aggregated for this timestamp
    COUNT(*) AS n_votes,
    
    -- Temperature Consensus & Uncertainty
    AVG(pred_temp) AS consensus_temp,
    SQRT(AVG(pred_temp * pred_temp) - AVG(pred_temp) * AVG(pred_temp)) AS std_temp,
    
    -- Atmospheric Pressure Consensus & Uncertainty
    AVG(pred_pres) AS consensus_pres,
    SQRT(AVG(pred_pres * pred_pres) - AVG(pred_pres) * AVG(pred_pres)) AS std_pres,
    
    -- Relative Humidity Consensus & Uncertainty
    AVG(pred_rh) AS consensus_rh,
    SQRT(AVG(pred_rh * pred_rh) - AVG(pred_rh) * AVG(pred_rh)) AS std_rh,
    
    -- Wind Speed Consensus & Uncertainty
    AVG(pred_wind) AS consensus_wind,
    SQRT(AVG(pred_wind * pred_wind) - AVG(pred_wind) * AVG(pred_wind)) AS std_wind,
    
    -- Solar Radiation Consensus & Uncertainty
    AVG(pred_solar) AS consensus_solar,
    SQRT(AVG(pred_solar * pred_solar) - AVG(pred_solar) * AVG(pred_solar)) AS std_solar,
    
    -- Hourly Rain Consensus & Uncertainty
    AVG(pred_rain) AS consensus_rain,
    SQRT(AVG(pred_rain * pred_rain) - AVG(pred_rain) * AVG(pred_rain)) AS std_rain

FROM {{ source('external_raw', 'inference_forecast') }}

{% if is_incremental() %}
  -- Filter records strictly greater than the max timestamp present in target table
  WHERE timestamp > coalesce((SELECT MAX(timestamp) FROM {{ this }}), '1970-01-01 00:00:00')
{% endif %}

GROUP BY model_version, timestamp