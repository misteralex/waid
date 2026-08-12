import os
import sys
import pprint
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Any, List, Dict, Optional, TypeVar, Type

# Pre-define environment variable for Loguru colorization
os.environ["LOGURU_COLORIZE"] = "1"
from dotenv import load_dotenv
from loguru import logger


# ==============================================================================
# EXCEPTIONS & CONSTANTS
# ==============================================================================

class WError(Exception):
    """Custom Base Exception for the application."""
    def __init__(self, message: str, code: int = 1):
        self.message = message
        self.code = code
        super().__init__(message)

    def __str__(self) -> str:
        return self.message


class WaidExit:
    """Exit status codes for process termination."""
    SUCCESS = 0
    CRITICAL_FAIL = 1
    INPUT_FAIL = 2
    DATA_FAIL = 3
    CONFIG_FAIL = 4
    VALIDATION_FAIL = 5
    DATA_NOT_FINALIZED = 6
    INTERNAL_ERROR = 7


# ==============================================================================
# ENVIRONMENT RESOLUTION HELPERS
# ==============================================================================

def _expand_environment_variables(iterations: int = 2) -> None:
    """Pass through os.environ multiple times to resolve nested environment variables."""
    for _ in range(iterations):
        for key, value in os.environ.items():
            os.environ[key] = os.path.expandvars(value)


def execution_guard(guard_name: str) -> bool:
    """Replicates '#ifndef GUARD_NAME' behavior to prevent repetitive execution."""
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
os.environ["WAID_CONFIG_DIR"] = str(config_dir)

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
    """Base class providing automated validation and introspection capabilities."""
    
    def _validate_config(self) -> None:
        missing_fields = []
        unresolved_fields = []
        
        for key, value in self.__dict__.items():
            if key.startswith('_'):
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
        """Log active configuration settings for debugging purposes."""
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
        value = os.getenv(name)
        return Path(value).resolve() if value else None

    @staticmethod
    def _get_int_env(name: str, default: Optional[int] = None) -> Optional[int]:
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
        value = os.getenv(name)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            logger.warning(f"Failed to parse environment variable '{name}' with value '{value}' as float.")
            return default


class BootSettings(BaseConfig):
    """Essential settings required to bootstrap application execution."""
    
    def __init__(self) -> None:
        self.waid_source_dir: Optional[Path] = self._get_path_env("WAID_SOURCE")
        self.waid_data_dir: Optional[Path] = self._get_path_env("WAID_DATA_DIR")
        self.log_dir: Optional[Path] = self._get_path_env("WAID_LOG_DIR")
        self.log_level: str = os.getenv("WAID_LOG_LEVEL", "INFO")
        self.debug_mode: bool = os.getenv("WAID_LOG_LEVEL", "info").lower() == "debug"
        self._validate_config()
        if self.debug_mode and execution_guard("BOOT_DUMP"):
            self.dump()


class WaidSettings(BaseConfig):
    """Application-level configurations and pipeline specifications."""
        
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
            #"ecowitt_field": "rel_pressure_hpa"
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

        self.waid_db_deploy_file: Optional[str] = os.getenv("WAID_DB_DEPLOY_FILE")
        
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

        # Number of lookback days for historical prediction reconciliation
        self.reconciliation_cutoff_days: Optional[int] = self._get_int_env("WAID_RECONCILIATION_CUTOFF_DAYS", 6)

        self._validate_config()
        if boot_settings.debug_mode and execution_guard("WAID_DUMP"):
            self.dump()

    def _validate_config(self) -> None:
        """Overridden configuration validator including station metadata sanity checks."""
        super()._validate_config()
        station_errors = []

        if not self.ecowitt_station_id or not str(self.ecowitt_station_id).strip():
            station_errors.append("WAID_ECOWITT_STATION_ID is missing or empty.")

        if not self.ecowitt_station_name or not str(self.ecowitt_station_name).strip():
            station_errors.append("WAID_ECOWITT_STATION_NAME is missing or empty.")

        if self.ecowitt_elevation_m is None and self.ecowitt_floor is None:
            station_errors.append(
                "Missing station height configuration! Specify either WAID_ECOWITT_ELEVATION_M "
                "(relative height in meters) or WAID_ECOWITT_FLOOR in environment config."
            )

        if station_errors:
            logger.critical("\n[!] STATION METADATA SANITY CHECK FAILURE:\n" + "\n".join(f" - {err}" for err in station_errors))
            sys.exit(WaidExit.CONFIG_FAIL)

    def _validate_timezone(self, tz_str: str) -> str:
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
    """Validates YYYY-MM inputs and converts them into standard datetime instances."""
    try:
        return datetime.strptime(value, "%Y-%m")
    except ValueError:
        logger.error(f"[CRITICAL] Invalid month format: '{value}'. Expected format is YYYY-MM (e.g., 2025-12).", file=sys.stderr)
        sys.exit(WaidExit.INPUT_FAIL)


# ==============================================================================
# INITIALIZATION RUNTIME
# ==============================================================================

logger.info("Boot WAID pipeline...")

boot_env = BootSettings()
waid_settings_instance = WaidSettings(boot_settings=boot_env)

class WaidBoot:
    """Unified access interface for bootstrap configuration components."""
    def __init__(
        self, 
        boot_settings: Optional[BootSettings] = None, 
        settings: Optional[WaidSettings] = None
    ) -> None:
        self._boot_settings = boot_settings or boot_env
        self._settings = settings or waid_settings_instance
        self.waid_exit = WaidExit()

    def __getattr__(self, name: str) -> Any:
        if hasattr(self._boot_settings, name):
            return getattr(self._boot_settings, name)
        if hasattr(self._settings, name):
            return getattr(self._settings, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


#if boot_env.log_level.upper() == "DEBUG":
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