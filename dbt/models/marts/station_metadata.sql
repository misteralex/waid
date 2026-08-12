{{ config(
    materialized='table',
    unique_key='station_id',
    post_hook=[
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_station_metadata_station_id ON {{ this.table }} (station_id)"
    ]
) }}

/**
 * @file station_metadata.sql
 * @brief dbt model to materialize station configuration and hyperparameters from environment variables.
 * @details Extracts station settings, computes fallback heights if elevation is missing, and sets up unique indexes.
 * @author AF
 * @date 2026
 */

WITH source_config AS (
    -- Extract station configuration parameters from system environment variables with safe defaults
    SELECT
        '{{ env_var("WAID_ECOWITT_STATION_ID", "default_station") }}' AS station_id,
        '{{ env_var("WAID_ECOWITT_STATION_NAME", "Default Station") }}' AS station_name,
        CAST('{{ env_var("WAID_ECOWITT_LATITUDE", "0.0") }}' AS REAL) AS latitude,
        CAST('{{ env_var("WAID_ECOWITT_LONGITUDE", "0.0") }}' AS REAL) AS longitude,
        CAST(NULLIF('{{ env_var("WAID_ECOWITT_ELEVATION_M", "") }}', '') AS REAL) AS raw_elevation,
        CAST('{{ env_var("WAID_ECOWITT_FLOOR", "0") }}' AS INTEGER) AS raw_floor,
        CAST('{{ env_var("WAID_ML_MIN_TRAINING_DAYS", "14") }}' AS INTEGER) AS min_training_days,
        CAST('{{ env_var("WAID_ML_RETRAIN_WINDOW_DAYS", "30") }}' AS INTEGER) AS retrain_window_days
),
calculated AS (
    -- Apply conditional logic to determine station height and elevation metrics
    SELECT
        station_id,
        station_name,
        latitude,
        longitude,
        CASE 
            WHEN raw_elevation IS NOT NULL AND raw_elevation > 0 THEN CAST(raw_elevation AS INTEGER)
            WHEN raw_floor <= 0 THEN 2
            ELSE CAST(ROUND(raw_floor * 3.0 + 1.5) AS INTEGER)
        END AS height_above_ground_m,
        min_training_days,
        retrain_window_days
    FROM source_config
)

-- Select final columns and append update timestamp for the metadata record
SELECT
    station_id,
    station_name,
    latitude,
    longitude,
    height_above_ground_m AS elevation_m,
    height_above_ground_m,
    min_training_days,
    retrain_window_days,
    CURRENT_TIMESTAMP AS updated_at
FROM calculated