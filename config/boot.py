"""
@file boot.py
@brief Core bootstrap and configuration module for the WAID pipeline.
@details Handles environment variable resolution, validation, logging setup, 
         and global settings classes.
"""

import os
import sys
import shutil
import pprint
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Any, List, Dict, Optional
from dataclasses import dataclass

# Pre-define environment variable for Loguru colorization
os.environ["LOGURU_COLORIZE"] = "1"

from dotenv import load_dotenv
from loguru import logger


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
    """Immutable database configuration object."""

    host: str
    user: str
    password: str
    port: int
    dbname: str


def get_db_credentials(target: Optional[str] = None) -> DBCredentials:
    """Retrieve database credentials based on runtime context or specific target.

    Priority:
    1. Direct injection (e.g. Docker, Cloud, CI/CD with flat WAID_DB_* variables).
    2. Explicit target requested as function parameter (e.g., 'draft', 'prod', 'retro').
    3. Default target defined in WAID_TARGET_ENV (fallback to 'draft').
    """
    # 1. Direct Cloud/Docker flat injection check
    if os.getenv("WAID_DB_HOST"):
        return DBCredentials(
            host=os.getenv("WAID_DB_HOST", ""),
            user=os.getenv("WAID_DB_USER", ""),
            password=os.getenv("WAID_DB_PASSWORD", ""),
            port=int(os.getenv("WAID_DB_PORT", "6543")),
            dbname=os.getenv("WAID_DB_NAME", "postgres"),
        )

    # 2. Local Multi-Target Resolution
    selected_target = (target or os.getenv("WAID_TARGET_ENV", "draft")).upper()

    return DBCredentials(
        host=os.getenv(f"WAID_{selected_target}_DB_HOST", ""),
        user=os.getenv(f"WAID_{selected_target}_DB_USER", ""),
        password=os.getenv(f"WAID_{selected_target}_DB_PASSWORD", ""),
        port=int(os.getenv(f"WAID_{selected_target}_DB_PORT", "6543")),
        dbname=os.getenv(f"WAID_{selected_target}_DB_NAME", "postgres"),
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
    logger.error("   Please initialize your environment first using './config/boot.env'.\n", file=sys.stderr)
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
            if hasattr(value, "__dict__"):
                logger.debug(f"[{key.upper()} SECTION]:")
                pprint.pprint(value.__dict__, indent=8)
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
        @param default Fallback value if parsing fails or variable is missing.
        @return Parsed float value or default fallback.
        """
        value = os.getenv(name)
        if value is None:
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
        else:
            self.waid_db: Optional[str] = os.getenv("WAID_DB_FILE")

        # Deploy configuration
        self.deploy_file: Optional[str] = os.getenv("WAID_DEPLOY_FILE")
        self.deploy_mode: Optional[str] = os.getenv("WAID_DEPLOY_MODE", "local").lower()
        
        # Directories & Tables
        self.ecowitt_dir: Optional[Path] = self._get_path_env("WAID_ECOWITT_DIR")
        self.ecowitt_table: Optional[str] = os.getenv("WAID_ECOWITT_TABLE")
        self.era5_data_dir: Optional[Path] = self._get_path_env("WAID_ERA5_DATA_DIR")
        self.dbt_dir: Optional[Path] = self._get_path_env("WAID_DBT_DIR")
        self.dbt_profiles_dir: Optional[Path] = self._get_path_env("WAID_DBT_PROFILES_DIR")
        
        # Ecowitt Gateway Configurations
        self.ecowitt_gw_ip: Optional[str] = os.getenv("WAID_ECOWITT_GW_IP")
        self.ecowitt_gw_port: Optional[int] = self._get_int_env("WAID_ECOWITT_GW_PORT")
        self.ecowitt_gw_timeout_sec: Optional[int] = self._get_int_env("WAID_ECOWITT_GW_TIMEOUT_SEC", 10)
        
        # Ecowitt API Credentials & Station Specs
        self.ecowitt_station_id: Optional[str] = os.getenv("WAID_ECOWITT_STATION_ID")
        self.ecowitt_station_name: Optional[str] = os.getenv("WAID_ECOWITT_STATION_NAME")
        self.ecowitt_api_key: Optional[str] = os.getenv("WAID_ECOWITT_API_KEY")
        self.ecowitt_application_key: Optional[str] = os.getenv("WAID_ECOWITT_APPLICATION_KEY")
        
        self.ecowitt_latitude: Optional[float] = self._get_float_env("WAID_ECOWITT_LATITUDE")
        self.ecowitt_longitude: Optional[float] = self._get_float_env("WAID_ECOWITT_LONGITUDE")
        self.ecowitt_elevation_m: Optional[float] = self._get_float_env("WAID_ECOWITT_ELEVATION_M")
        self.ecowitt_floor: Optional[float] = self._get_float_env("WAID_ECOWITT_FLOOR")
        self.tz_timezone: str = self._validate_timezone(os.getenv("WAID_TIMEZONE", "Europe/Rome"))
        self.resample_interval_min: Optional[int] = self._get_int_env("WAID_RESAMPLE_INTERVAL_MIN", 60)
        self.max_interpolate_hours: Optional[int] = self._get_int_env("WAID_MAX_INTERPOLATE_HOURS", 2) 
        
        # External Services (ERA5, Services ports)
        self.era5_api_url: Optional[str] = os.getenv("WAID_ERA5_API_URL")
        self.era5_api_key: Optional[str] = os.getenv("WAID_ERA5_API_KEY")
        
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
        self.backfill_begin_period: Optional[datetime] = validate_period(os.getenv("SCHEDULER_BACKFILL_BEGIN_PERIOD"))
        self.backfill_end_period: Optional[datetime] = validate_period(os.getenv("SCHEDULER_BACKFILL_END_PERIOD"))
        self.mock_now: Optional[datetime] = validate_mock_timestamp(os.getenv("WAID_MOCK_NOW"))
        self.mock_interval_hours: int = self._get_int_env("WAID_MOCK_INTERVAL_HOURS", 1)

        # Number of lookback days for historical prediction reconciliation
        self.reconciliation_cutoff_days: Optional[int] = self._get_int_env("WAID_RECONCILIATION_CUTOFF_DAYS", 6)

        # Backend platform configurations (multi-target Supabase database)
        self.dev_db_config: DBCredentials = get_db_credentials("draft")
        self.prod_db_config: DBCredentials = get_db_credentials("prod")
        self.retro_db_config: DBCredentials = get_db_credentials("retro")

        # Fallback/Default active configuration based on WAID_TARGET_ENV or Cloud injection
        self.active_db_config: DBCredentials = get_db_credentials()

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
            "backfill_end_period"
        })
        
        station_errors = []

        # Station ID check
        if not self.ecowitt_station_id or not str(self.ecowitt_station_id).strip():
            station_errors.append("WAID_ECOWITT_STATION_ID is missing or empty.")

        # Station Name check
        if not self.ecowitt_station_name or not str(self.ecowitt_station_name).strip():
            station_errors.append("WAID_ECOWITT_STATION_NAME is missing or empty.")

        # Elevation vs Floor check
        if self.ecowitt_elevation_m is None and self.ecowitt_floor is None:
            station_errors.append(
                "Missing station height configuration! Specify either WAID_ECOWITT_ELEVATION_M "
                "(relative height in meters) or WAID_ECOWITT_FLOOR in environment config."
            )

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

def validate_period(value: str) -> datetime:
    """
    @brief Validates YYYY-MM inputs and converts them into standard datetime instances.
    
    @param value Period string formatted as YYYY-MM.
    @return Parsed datetime instance.
    """
    try:
        return datetime.strptime(value, "%Y-%m")
    except ValueError:
        logger.error(f"[CRITICAL] Invalid month format: '{value}'. Expected format is YYYY-MM (e.g., 2025-12).", file=sys.stderr)
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

logger.info("Boot WAID pipeline...")

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

logger.remove()
logger.add(
    sys.stderr,
    level=boot_env.log_level.upper(),
    colorize=True,
    format="<level>{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:8} | {file.name}:{function}:{line} | {message}</level>"
)

if waid_settings_instance.log_dir:
    waid_settings_instance.log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = waid_settings_instance.log_dir / f"waid_pipeline_{datetime.now().strftime('%Y%m%d')}.log"
    logger.add(
        str(log_file_path),
        level=boot_env.log_level.upper(),
        colorize=False,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:8} | {file.name}:{function}:{line} | {message}"
    )

logger.debug("Debugging successfully activated")