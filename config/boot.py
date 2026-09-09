"""
@file boot.py
@brief Core bootstrap and configuration module for the WAID pipeline.
@details Handles environment variable resolution, validation, logging setup, 
         and global settings classes.
@author AF
@date 2026
"""

import os
import sys
import shutil
import pprint
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Any, List, Dict, Optional
from dataclasses import dataclass
import streamlit as st


# ==============================================================================
# Log management section
# ==============================================================================

# Pre-define environment variable for Loguru colorization
os.environ["LOGURU_COLORIZE"] = "1"

from dotenv import load_dotenv
from loguru import logger


# Direct read log variable to set up the required level or fallback to default 'INFO' 
current_log_level = os.getenv("WAID_LOG_LEVEL", "INFO").upper()
current_log_dir = Path(os.getenv("WAID_LOG_DIR", "logs"))
current_config_dir = Path(os.getenv("WAID_CONFIG_DIR", "config"))

# Protection against double initialization (executed once per process)
if not getattr(logger, "_waid_initialized", False):
    logger.remove()
    logger.add(
        sys.stderr,
        level=current_log_level,
        colorize=True,
        format="<level>{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:8} | {file.name}:{function}:{line} | {message}</level>"
    )

    if current_log_dir:
        current_log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = current_log_dir / f"waid_pipeline_{datetime.now().strftime('%Y%m%d')}.log"
        logger.add(
            str(log_file_path),
            level=current_log_level,
            colorize=False,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:8} | {file.name}:{function}:{line} | {message}"
        )

    logger._waid_initialized = True


# Start new log cycle for each entrypoint script execution
caller_script = Path(sys.argv[0]).name
ENTRYPOINT_SCRIPTS = {"waid_scheduler_lab.py", "waid_orchestrate_lab.py"}
if caller_script in ENTRYPOINT_SCRIPTS:
    logger.info("=" * 90)
    logger.info(f">>> NEW WAID PIPELINE CYCLE STARTED | Entrypoint: {caller_script}")
    logger.info("=" * 90)
else:
    logger.info(f"--- Booting module context: {caller_script} ---")


# ==============================================================================
# EXCEPTIONS & CONSTANTS
# ==============================================================================

class WError(Exception):
    """
    @brief Custom Base Exception for the application.
    """
    def __init__(self, message: str, code: int = 1) -> None:
        """
        @brief Initializes the custom application exception with a message and error code.
        
        @param message Error description message.
        @param code Numeric error exit status code.
        """
        self.message = message
        self.code = code
        super().__init__(message)

    def __str__(self) -> str:
        """
        @brief Returns the string representation of the exception message.
        
        @return Error message string.
        """
        return self.message


class WaidExit:
    """
    @brief Exit status codes for process termination.
    """
    SUCCESS = 0
    CRITICAL_FAIL = 1
    INPUT_FAIL = 2
    DATA_FAIL = 3
    CONFIG_FAIL = 4
    VALIDATION_FAIL = 5
    DATA_NOT_FINALIZED = 6
    INTERNAL_ERROR = 7


@dataclass(frozen=True)
class DBCredentials:
    """
    @brief Immutable database configuration object.
    """

    host: str
    user: str
    password: str
    port: int
    dbname: str


def get_env_with_fallback(name: str, default: Any, var_type: type = str) -> Any:
    """
    @brief Retrieves environment variable with logging and fallback mechanism.
    
    @param name Environment variable name.
    @param default Fallback value if missing or empty.
    @param var_type Expected output datatype for casting.
    @return Parsed environment value or fallback.
    """
    val = os.getenv(name)
    if val is None or not str(val).strip():
        logger.warning(f"[CONFIG_FALLBACK] {name} is missing or empty. Using default fallback: {default}")
        return default

    try:
        return var_type(val)
    except ValueError:
        logger.warning(f"[CONFIG_FALLBACK] Failed to parse {name} as {var_type.__name__}. Using default fallback: {default}")
        return default


def get_db_credentials(target: str) -> DBCredentials:
    """
    @brief Retrieve database credentials based on explicit target resolution.
    
    @param target Database target scope (e.g., 'draft', 'prod', 'retro').
    @return DBCredentials instance.
    """
    t = target.upper()

    return DBCredentials(
        host=get_env_with_fallback(f"WAID_{t}_DB_HOST", "host_placeholder", var_type=str),
        user=get_env_with_fallback(f"WAID_{t}_DB_USER", "user_placeholder", var_type=str),
        password=get_env_with_fallback(f"WAID_{t}_DB_PASSWORD", "password_placeholder", var_type=str),
        port=get_env_with_fallback(f"WAID_{t}_DB_PORT", "6543", var_type=str),
        dbname=get_env_with_fallback(f"WAID_{t}_DB_NAME", "postgres", var_type=str),
    )


# ==============================================================================
# ENVIRONMENT RESOLUTION HELPERS
# ==============================================================================

def _expand_environment_variables(iterations: int = 2) -> None:
    """
    @brief Pass through os.environ multiple times to resolve nested environment variables.
    
    @param iterations Number of times to traverse and expand environment variables.
    """
    for _ in range(iterations):
        for key, value in os.environ.items():
            os.environ[key] = os.path.expandvars(value)


def execution_guard(guard_name: str) -> bool:
    """
    @brief Replicates '#ifndef GUARD_NAME' behavior to prevent repetitive execution.
    
    @param guard_name Identifier name for the execution guard check.
    @return True if execution can proceed, False if it was already executed.
    """
    env_var = f"PRJ_GUARD_{guard_name.upper()}"
    if os.environ.get(env_var) == "1":
        return False
    os.environ[env_var] = "1"
    return True


# ==============================================================================
# PRELIMINARY ENVIRONMENT CHECK
# ==============================================================================

# Ensure WAID_SOURCE is available before proceeding
waid_source = os.environ.get("WAID_SOURCE")
if not waid_source:
    logger.error("[CRITICAL] WAID_SOURCE environment variable is not defined or empty!", file=sys.stderr)
    logger.error("Please initialize your environment first using './config/boot.env'.\n", file=sys.stderr)
    sys.exit(WaidExit.CONFIG_FAIL)
    
# Load base environment file
SCRIPT_DIR = Path(__file__).parent.resolve()
load_dotenv(dotenv_path=SCRIPT_DIR / "boot.env", override=True)

# FORCE WAID_SOURCE override if provided by environment (e.g., Docker /app)
os.environ["WAID_SOURCE"] = waid_source

# Re-evaluate WAID_CONFIG_DIR dynamically based on current WAID_SOURCE
config_dir = Path(waid_source) / "config"
env_file = config_dir / "waid.env"
example_file = config_dir / "waid.env.example"
os.environ["WAID_CONFIG_DIR"] = str(config_dir)

if not env_file.exists():
    if example_file.exists():
        shutil.copy(example_file, env_file)
        print(
            "WARNING: waid.env not found. Automatically generated from waid.env.example. Please update it with actual configurations if needed."
        )
    else:
        raise FileNotFoundError(
            f"Critical: Neither waid.env nor waid.env.example found in {config_dir}"
        )

# Load global target environment file (waid.env)
WAID_ENV_FILE = config_dir / "waid.env"
if WAID_ENV_FILE.exists():
    load_dotenv(dotenv_path=WAID_ENV_FILE, override=True)
    _expand_environment_variables(iterations=2)
else:
    logger.critical(f"[!] Critical: WAID Configuration file not found at {WAID_ENV_FILE}")
    sys.exit(WaidExit.INPUT_FAIL)

# ==============================================================================
# STREAMLIT SECRETS INTEGRATION
# ==============================================================================
try:
    logger.debug("Try to process Streamlit secrets...")
    if hasattr(st, "secrets") and len(st.secrets) > 0:
        for key, value in st.secrets.items():
            if isinstance(value, str):
                os.environ[key] = value
    logger.success("Streamlit secrets successfully loaded")
except Exception:
    logger.debug("Not running under Streamlit or no secrets found...")
    pass

# ==============================================================================
# CONFIGURATION BASE & SETTINGS CLASSES
# ==============================================================================

class BaseConfig:
    """
    @brief Base class providing automated validation and introspection capabilities.
    """
    
    def _validate_config(self, optional_fields: Optional[set] = None) -> None:
        """
        @brief Validates configuration instance attributes, checking for missing or unresolved values.
        
        @param optional_fields Set of field names to ignore during validation checks.
        """
        missing_fields = []
        unresolved_fields = []
        optional_fields = optional_fields or set()
        
        for key, value in self.__dict__.items():
            if key.startswith('_') or key in optional_fields:
                continue
            if value is None:
                missing_fields.append(key.upper())
                continue
            if isinstance(value, str) and "$" in value:
                unresolved_fields.append(f"{key.upper()} ({value})")
        
        error_messages = []
        if missing_fields:
            error_messages.append(f" Missing (None): {', '.join(missing_fields)}")
        if unresolved_fields:
            error_messages.append(f" Unresolved ($): {', '.join(unresolved_fields)}")          
            
        if error_messages:
            logger.critical("\n[!] CONFIGURATION ERROR:\n" + "\n".join(error_messages))
            sys.exit(WaidExit.CONFIG_FAIL)

    def dump(self) -> None:
        """
        @brief Log active configuration settings for debugging purposes.
        """
        class_name = self.__class__.__name__
        logger.debug(f"=== [DEBUG] {class_name} COMPLETE CONFIG ===")
        for key, value in self.__dict__.items():
            if key.lower() == "password":
                logger.debug(f"  {key}: ********")
            elif hasattr(value, "__dict__"):
                logger.debug(f"[{key.upper()} SECTION]:")
                safe_dict = {k: ("********" if "password" in k.lower() else v) for k, v in value.__dict__.items()}
                logger.debug(safe_dict)
            else:
                logger.debug(f"  {key}: {value}")

    @staticmethod
    def _get_path_env(name: str) -> Optional[Path]:
        """
        @brief Retrieves a path string from environment variables and converts it to a resolved Path object.
        
        @param name Environment variable name.
        @return Resolved Path object or None if absent.
        """
        value = os.getenv(name)
        return Path(value).resolve() if value else None

    @staticmethod
    def _get_int_env(name: str, default: Optional[int] = None) -> Optional[int]:
        """
        @brief Retrieves an integer value from environment variables.
        
        @param name Environment variable name.
        @param default Fallback value if parsing fails or variable is missing.
        @return Parsed integer value or default fallback.
        """
        value = os.getenv(name)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Failed to parse environment variable '{name}' with value '{value}' as integer.")
            return default

    @staticmethod
    def _get_float_env(name: str, default: Optional[float] = None) -> Optional[float]:
        """
        @brief Retrieves a float value from environment variables.
        
        @param name Environment variable name.
        @param default Fallback value if parsing fails, variable is missing, or empty.
        @return Parsed float value or default fallback.
        """
        value = os.getenv(name)
        
        # If the variable does not exist OR is an empty string (e.g. WAID_THRESHOLD=)
        if not value or not value.strip():
            return default
            
        try:
            return float(value)
        except ValueError:
            logger.warning(f"Failed to parse environment variable '{name}' with value '{value}' as float.")
            return default


class BootSettings(BaseConfig):
    """
    @brief Essential settings required to bootstrap application execution.
    """
    
    def __init__(self) -> None:
        """
        @brief Initializes core boot settings from environment parameters.
        """
        self.waid_source_dir: Optional[Path] = self._get_path_env("WAID_SOURCE")
        self.waid_data_dir: Optional[Path] = self._get_path_env("WAID_DATA_DIR")
        self.log_dir: Optional[Path] = self._get_path_env("WAID_LOG_DIR")
        self.log_level: str = os.getenv("WAID_LOG_LEVEL", "INFO")
        self.debug_mode: bool = os.getenv("WAID_LOG_LEVEL", "info").lower() == "debug"
        self._validate_config()
        if self.debug_mode and execution_guard("BOOT_DUMP"):
            self.dump()
        
        # Check current WAID_SETUP_MODE environment variable 
        waid_setup_mode = os.getenv("WAID_SETUP_MODE")
        if not waid_setup_mode or not waid_setup_mode.strip():
            waid_setup_mode = "0"
            logger.debug(f"[CONFIG_FALLBACK] WAID_SETUP_MODE is missing or empty. Using default fallback: {waid_setup_mode}")
        else:
            logger.warning(f"Using required fallback WAID_SETUP_MODE: {waid_setup_mode}")
        self.setup_mode = int(waid_setup_mode.strip() or 0)


class WaidSettings(BaseConfig):
    """
    @brief Application-level configurations and pipeline specifications.
    """
        
    # Unified Weather Features Configuration mapping
    ML_OUTPUT_FEATURES: List[Dict[str, str]] = [
        {
            "name": "Temperature",
            "unit": "°C",
            "bias_col": "bias_temp",
            "ecowitt_match": "ecowitt_temp",
            "standard": "temperature",
            "ecowitt_field": "outdoor_temperature_c",
        },
        {
            "name": "Humidity",
            "unit": "%",
            "bias_col": "bias_rh",
            "ecowitt_match": "ecowitt_rh",
            "standard": "humidity",
            "ecowitt_field": "outdoor_humidity",
        },
        {
            "name": "Pressure",
            "unit": "hPa",
            "bias_col": "bias_pres",
            "ecowitt_match": "ecowitt_pres",
            "standard": "pressure_hpa",
            "ecowitt_field": "abs_pressure_hpa",
        },
        {
            "name": "Wind speed",
            "unit": "m/s",
            "bias_col": "bias_wind",
            "ecowitt_match": "ecowitt_wind",
            "standard": "wind_speed",
            "ecowitt_field": "wind_m_s",
        },
        {
            "name": "Solar radiation",
            "unit": "W/m²",
            "bias_col": "bias_solar",
            "ecowitt_match": "ecowitt_solar",
            "standard": "solar_radiation",
            "ecowitt_field": "solar_rad_w_m2",
        },
        {
            "name": "Hourly rain",
            "unit": "mm",
            "bias_col": "bias_rain",
            "ecowitt_match": "ecowitt_rain",
            "standard": "hourly_rain",
            "ecowitt_field": "hourly_rain_mm",
        },
    ]
    
    # Input features added by the model pipeline
    ML_AUXILIARY_FEATURES = [
        "hour_sin",
        "hour_cos",
        "doy_sin",
        "doy_cos",
        "theo_solar",
    ]
    ML_INPUT_FEATURES = ([f["ecowitt_field"] for f in ML_OUTPUT_FEATURES] + ML_AUXILIARY_FEATURES)
    ML_INPUT_FEATURES_MATCH = ([f["ecowitt_match"] for f in ML_OUTPUT_FEATURES] + ML_AUXILIARY_FEATURES)

    def __init__(self, boot_settings: BootSettings) -> None:
        """
        @brief Initializes pipeline-level settings and model features based on boot settings.
        
        @param boot_settings The loaded bootstrap settings instance.
        """
        self.config_dir: Optional[Path] = self._get_path_env("WAID_CONFIG_DIR")
        self.log_dir: Optional[Path] = self._get_path_env("WAID_LOG_DIR")
        self.deploy_dir: Optional[Path] = self._get_path_env("WAID_DEPLOY_DIR")
        self.docs_dir: Optional[Path] = self._get_path_env("WAID_DOCS_DIR")
        self.version: Optional[str] = os.getenv("WAID_VERSION")
        self.tools_dir: Optional[Path] = self._get_path_env("WAID_TOOLS_DIR")
        
        # Unified Weather Features Configuration mapping
        self.output_features = self.ML_OUTPUT_FEATURES
        self.input_features = self.ML_INPUT_FEATURES
        self.input_features_match = self.ML_INPUT_FEATURES_MATCH
        self.n_input_features: int = len(self.input_features)
        self.n_output_features: int = len(self.output_features)

        # Dynamic Simulation vs Production DB toggle
        self.waid_sim_mode: bool = os.getenv("WAID_SIM_MODE", "false").lower() == "true"
        if self.waid_sim_mode:
            self.waid_db: Optional[str] = os.getenv("WAID_DB_MOCK_FILE")
            self.deploy_db_file: Optional[str] = os.getenv("WAID_DEPLOY_MOCK_FILE")
        else:
            self.waid_db: Optional[str] = os.getenv("WAID_DB_FILE")
            self.deploy_db_file: Optional[str] = os.getenv("WAID_DEPLOY_FILE")

        # Deploy configuration
        self.deploy_mode: Optional[str] = get_env_with_fallback("WAID_DEPLOY_MODE", "local", var_type=str).lower()
        
        # Directories & Tables
        self.ecowitt_dir: Optional[Path] = self._get_path_env("WAID_ECOWITT_DIR")
        self.ecowitt_table: Optional[str] = os.getenv("WAID_ECOWITT_TABLE")
        self.era5_data_dir: Optional[Path] = self._get_path_env("WAID_ERA5_DATA_DIR")
        self.dbt_dir: Optional[Path] = self._get_path_env("WAID_DBT_DIR")
        self.dbt_profiles_dir: Optional[Path] = self._get_path_env("WAID_DBT_PROFILES_DIR")
        self.dbt_bin = Path(os.getenv("WAID_SOURCE")) / ".venv-dbt" / "bin" / "dbt"
        
        # Ecowitt Gateway Configurations
        self.ecowitt_gw_ip: Optional[str] = get_env_with_fallback("WAID_ECOWITT_GW_IP", "192.168.1.100", var_type=str)
        self.ecowitt_gw_port: Optional[int] = self._get_int_env("WAID_ECOWITT_GW_PORT")
        self.ecowitt_gw_timeout_sec: Optional[int] = self._get_int_env("WAID_ECOWITT_GW_TIMEOUT_SEC", 10)
        
        # Ecowitt Station Specs
        self.ecowitt_station_id: Optional[str] = get_env_with_fallback("WAID_ECOWITT_STATION_ID", "STATION_01", var_type=str)
        self.ecowitt_station_name: Optional[str] = get_env_with_fallback("WAID_ECOWITT_STATION_NAME", "Local Home Weather Station", var_type=str)
        self.ecowitt_latitude = get_env_with_fallback("WAID_ECOWITT_LATITUDE", 41.9028, var_type=float)
        self.ecowitt_longitude: float = get_env_with_fallback("WAID_ECOWITT_LONGITUDE", 12.4964, var_type=float)
        self.ecowitt_elevation_m: Optional[float] = get_env_with_fallback("WAID_ECOWITT_ELEVATION_M", 20.0, var_type=float)
        self.ecowitt_floor: Optional[float] = get_env_with_fallback("WAID_ECOWITT_FLOOR", 2, var_type=int)
        
        # Retrieve the variable and apply the fallback if it is None, empty, or whitespace only
        raw_tz = get_env_with_fallback("WAID_TIMEZONE", "Europe/Rome", var_type=str)
        self.tz_timezone = self._validate_timezone(raw_tz)
        
        self.resample_interval_min: Optional[int] = self._get_int_env("WAID_RESAMPLE_INTERVAL_MIN", 60)
        self.max_interpolate_hours: Optional[int] = self._get_int_env("WAID_MAX_INTERPOLATE_HOURS", 2) 
        
        # External Services (ERA5, Services ports)
        self.era5_api_url: Optional[str] = os.getenv("WAID_ERA5_API_URL")
        self.era5_api_key: str = get_env_with_fallback("WAID_ERA5_API_KEY", "placeholder_era5_key", var_type=str)
        
        # Forecasting & Lookback Parameters
        self.forecast_horizon_hours: Optional[int] = self._get_int_env("WAID_FORECAST_HORIZON_HOURS")
        self.lookback_hours: Optional[int] = self._get_int_env("WAID_LOOKBACK_HOURS", 24)
        self.fastapi_port: Optional[int] = self._get_int_env("WAID_FASTAPI_PORT", 8000)      
        self.streamlit_port: Optional[int] = self._get_int_env("WAID_STREAMLIT_PORT", 8501)
        
        # ML Pipelines Configurations
        self.ml_matches_dir: Optional[Path] = self._get_path_env("WAID_ML_MATCHES_DIR")
        self.ml_matches_table: Optional[str] = os.getenv("WAID_ML_MATCHES_TABLE")
        self.ml_tensors_dir: Optional[Path] = self._get_path_env("WAID_ML_TENSORS_DIR")
        self.ml_models_dir: Optional[Path] = self._get_path_env("WAID_ML_MODELS_DIR")
        self.ml_threshold_min: Optional[int] = self._get_int_env("WAID_ML_THRESHOLD_MIN")
        
        # Bias Parameters
        self.max_bias_temp: Optional[float] = self._get_float_env("WAID_ML_BIAS_TEMP")
        self.max_bias_pres: Optional[float] = self._get_float_env("WAID_ML_BIAS_PRES")
        self.max_bias_rh: Optional[float] = self._get_float_env("WAID_ML_BIAS_RH")
        self.max_bias_wind: Optional[float] = self._get_float_env("WAID_ML_BIAS_WIND")
        self.max_bias_solar: Optional[float] = self._get_float_env("WAID_ML_BIAS_SOLAR")
        self.max_bias_rain: Optional[float] = self._get_float_env("WAID_ML_BIAS_RAIN")
        
        # Guardrail Training Parameters
        self.ml_min_training_days: Optional[int] = self._get_int_env("WAID_ML_MIN_TRAINING_DAYS", 14)
        self.ml_retrain_window_days: Optional[int] = self._get_int_env("WAID_ML_RETRAIN_WINDOW_DAYS", 30)
        
        # ML Model File Names
        self.ml_model_h5_file: Optional[str] = os.getenv("WAID_ML_MODEL_H5_FILE")
        self.ml_input_scaler_pkl_file: Optional[str] = os.getenv("WAID_ML_INPUT_SCALER_PKL_FILE")
        self.ml_output_scaler_pkl_file: Optional[str] = os.getenv("WAID_ML_OUTPUT_SCALER_PKL_FILE")

        # Configuration scheduler settings
        self.scheduled_interval_sec: Optional[int] = self._get_int_env("SCHEDULER_INTERVAL_SEC", 3600)
        
        # 1. Backfill opzionali -> allow_none=True
        self.backfill_begin_period: Optional[datetime] = validate_period(os.getenv("SCHEDULER_BACKFILL_BEGIN_PERIOD"), allow_none=True)
        self.backfill_end_period: Optional[datetime] = validate_period(os.getenv("SCHEDULER_BACKFILL_END_PERIOD"), allow_none=True)
        
        # 2. Periodo dell'app (se vuoto va in fallback sul mese corrente UTC) -> allow_none=False
        self.period: Optional[datetime] = validate_period(os.getenv("WAID_PERIOD"), allow_none=False)
        
        self.auto_backfill: bool = os.getenv("AUTO_BACKFILL", "false").lower() == "true"
        
        self.mock_now: Optional[datetime] = validate_mock_timestamp(os.getenv("WAID_MOCK_NOW"))
        self.mock_interval_hours: int = self._get_int_env("WAID_MOCK_INTERVAL_HOURS", 1)

        # Number of lookback days for historical prediction reconciliation
        self.reconciliation_cutoff_days: Optional[int] = self._get_int_env("WAID_RECONCILIATION_CUTOFF_DAYS", 6)
        
        # Sanity check for expected schema target (e.g. Supabase)
        self.db_schema_target: Optional[str] = os.getenv("WAID_DB_SCHEMA_TARGET", "draft")

        # Backend platform configurations (multi-target Supabase database)
        self.dev_db_config: DBCredentials = get_db_credentials("draft")
        self.prod_db_config: DBCredentials = get_db_credentials("prod")
        self.retro_db_config: DBCredentials = get_db_credentials("retro")

        # Fallback/Default active configuration based on WAID_DB_SCHEMA_TARGET or Cloud injection
        self.active_db_config: DBCredentials = get_db_credentials(self.db_schema_target)

        self._validate_config()
        if boot_settings.debug_mode and execution_guard("WAID_DUMP"):
            self.dump()

    def _validate_config(self) -> None:
        """
        @brief Overridden configuration validator.
        @details 1. Validates base configuration excluding explicitly optional fields.
                    - 'mock_now' and 'backfill_period' are optional for business logic.
                 2. Performs sanity checks on station metadata and structural requirements.
        """
        super()._validate_config(optional_fields={
            "mock_now", 
            "backfill_begin_period", 
            "backfill_end_period",
            "ecowitt_latitude",
            "ecowitt_longitude",
            "ecowitt_elevation_m",
            "ecowitt_floor",
            "ecowitt_api_key",
            "ecowitt_application_key",
            "ecowitt_gw_ip"
        })
        
        station_errors = []
        
        # Simulation mode check: requires mock file if enabled
        if self.waid_sim_mode and not self.waid_db:
            station_errors.append(
                "WAID_SIM_MODE is True, but WAID_DB_MOCK_FILE is missing in environment config."
            )

        # Block execution if errors exist
        if station_errors:
            logger.critical(
                "\n[!] STATION METADATA SANITY CHECK FAILURE:\n" + 
                "\n".join(f" - {err}" for err in station_errors)
            )
            sys.exit(WaidExit.CONFIG_FAIL)

    def _validate_timezone(self, tz_str: str) -> str:
        """
        @brief Validates the timezone identifier string against IANA database.
        
        @param tz_str The timezone string to validate (e.g., 'Europe/Rome').
        @return Validated timezone string.
        """
        # If the field is empty or None, skip validation and return as is (or handle the default upstream)
        if not tz_str or not tz_str.strip():
            return tz_str

        try:
            ZoneInfo(tz_str)
            return tz_str
        except (ZoneInfoNotFoundError, ValueError):
            logger.critical(
                f"[CRITICAL CONFIG ERROR] Invalid timezone provided: '{tz_str}'. "
                f"Please update WAID_TIMEZONE in your .env file with a valid IANA name (e.g., 'Europe/Rome')."
            )
            sys.exit(WaidExit.INPUT_FAIL)


# ==============================================================================
# UTILITY FUNCTIONS & LOGGING SETUP
# ==============================================================================

def validate_period(value: Optional[str], allow_none: bool = True) -> Optional[datetime]:
    """
    @brief Validates YYYY-MM inputs and converts them into standard datetime instances.
    
    @param value Period string formatted as YYYY-MM.
    @param allow_none If True, returns None when input is empty/missing instead of defaulting.
    @return Parsed datetime instance or None.
    """
    if not value or not str(value).strip():
        if allow_none:
            return None
        
        current_period = datetime.now(timezone.utc).strftime("%Y-%m")
        logger.warning(
            f"[CONFIG_FALLBACK] WAID_PERIOD is missing or empty. Using default fallback: '{current_period}'"
        )
        value = current_period

    try:
        return datetime.strptime(value.strip(), "%Y-%m")
    except (ValueError, TypeError):
        logger.error(
            f"[CRITICAL] Invalid month format: '{value}'. Expected format is YYYY-MM (e.g., 2025-12).",
            file=sys.stderr,
        )
        sys.exit(WaidExit.INPUT_FAIL)


def validate_mock_timestamp(value: Optional[str]) -> Optional[datetime]:
    """
    @brief Validates YYYY-MM-DD HH:MM:SS inputs for mock simulation and converts them into standard datetime instances.
    
    @param value Timestamp string.
    @return Parsed datetime instance or None if not provided.
    """
    if value is None or str(value).lower() in ("none", "null", ""):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        logger.error(f"[CRITICAL] Invalid mock timestamp format: '{value}'. Expected format is YYYY-MM-DD HH:MM:SS.", file=sys.stderr)
        sys.exit(WaidExit.INPUT_FAIL)
        
        
# ==============================================================================
# INITIALIZATION RUNTIME
# ==============================================================================

boot_env = BootSettings()
waid_settings_instance = WaidSettings(boot_settings=boot_env)

class WaidBoot:
    """
    @brief Unified access interface for bootstrap configuration components.
    """
    def __init__(
        self, 
        boot_settings: Optional[BootSettings] = None, 
        settings: Optional[WaidSettings] = None
    ) -> None:
        """
        @brief Initializes the unified boot access wrapper.
        
        @param boot_settings BootSettings instance.
        @param settings WaidSettings instance.
        """
        self._boot_settings = boot_settings or boot_env
        self._settings = settings or waid_settings_instance
        self.waid_exit = WaidExit()

    def __getattr__(self, name: str) -> Any:
        """
        @brief Delegates attribute access to underlying configuration instances.
        
        @param name Attribute name to retrieve.
        @return Requested attribute value.
        """
        if hasattr(self._boot_settings, name):
            return getattr(self._boot_settings, name)
        if hasattr(self._settings, name):
            return getattr(self._settings, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

if boot_env.debug_mode:
    logger.debug(f"WAID_VERSION = {repr(os.environ.get('WAID_VERSION'))} (configuration source: waid.env)")