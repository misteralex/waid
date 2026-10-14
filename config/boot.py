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
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Any, List, Dict, Optional
from dataclasses import dataclass
import streamlit as st

# Pre-define environment variable for Loguru colorization
os.environ["LOGURU_COLORIZE"] = "1"

from dotenv import load_dotenv
from loguru import logger

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

# CRITICAL CHECK: Ensure WAID_SOURCE is available in the environment
waid_source = os.environ.get("WAID_SOURCE")
if not waid_source or not waid_source.strip():
    logger.error("[CRITICAL] WAID_SOURCE environment variable is not defined or empty!", file=sys.stderr)
    logger.error(
        "WAID_SOURCE is a critical configuration variable and must be set externally.\n",
        file=sys.stderr
    )
    sys.exit(WaidExit.CONFIG_FAIL)

logger.info(f"WAID_SOURCE successfully resolved from environment: {waid_source}")

# Load base environment file (boot.env) to ensure all critical variables are available
load_dotenv(dotenv_path=Path(waid_source) / "config" / "boot.env", override=os.environ.get("WAID_ALLOW_ENV_OVERRIDE"))

# ==============================================================================
# Log management section
# ==============================================================================

current_log_level = os.getenv("WAID_LOG_LEVEL", "INFO").upper()
current_log_dir = Path(os.getenv("WAID_LOG_DIR", "logs"))

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
    @return DBCredentials instance containing database access parameters.
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
    @return None
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


# Start new log cycle for each entrypoint script execution
caller_script = Path(sys.argv[0]).name
ENTRYPOINT_SCRIPTS = {"waid_scheduler_lab.py", "waid_orchestrate_lab.py"}
if caller_script in ENTRYPOINT_SCRIPTS:
    logger.info("=" * 90)
    logger.info(f">>> NEW WAID PIPELINE CYCLE STARTED | Entrypoint: {caller_script}")
    logger.info("=" * 90)
else:
    logger.info(f"--- Booting module context: {caller_script} ---")

# Check WAID_CONFIG_DIR dynamically based on current WAID_SOURCE
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
load_dotenv(dotenv_path=env_file, override=os.environ.get("WAID_ALLOW_ENV_OVERRIDE"))
_expand_environment_variables(iterations=2)


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
# DATABASE MANAGER CLASS 
# ==============================================================================

class WaidDB:
    """
    @brief Encapsulates database schema registry, table references, and DB utilities.
    """
    def __init__(self, data_dir: Optional[Path], registry_filename: Optional[str]) -> None:
        """
        @brief Initializes the WaidDB instance by parsing the active table registry.

        @param data_dir Path to the active data directory.
        @param registry_filename Filename of the dbt models markdown registry.
        @return None
        """
        self.data_dir = Path(data_dir) if data_dir else Path(".")
        self.registry_filename = registry_filename or "waid_dbt_models.md"
        self.dbt_registry_name = os.getenv("WAID_DBT_REGISTRY_NAME", "Active Table Registry")
        self.loaded_tables: List[str] = []
        
        logger.debug("[DB_REGISTRY] WaidDB initialized with")
        logger.debug(f"[DB_REGISTRY] data_dir: {self.data_dir}")
        logger.debug(f"[DB_REGISTRY] registry_filename: {self.registry_filename}")
        self._load_active_registry()
        
    def _load_active_registry(self) -> None:
        """
        @brief Parses the markdown registry file to dynamically expose active physical tables as attributes.
        """
        registry_path = self.data_dir / self.registry_filename
        if not registry_path.exists():
            logger.warning(f"[DB_REGISTRY] Registry file not found at: {registry_path}")
            return

        try:
            content = registry_path.read_text(encoding="utf-8")
            in_registry = False
            loaded_count = 0
            
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("##") and self.dbt_registry_name in line:
                    in_registry = True
                    continue
                elif in_registry and line.startswith("## "):
                    break
                
                if in_registry and line.startswith("- "):
                    parts = line.split("`")
                    if len(parts) >= 4:
                        table_name = parts[3]
                        setattr(self, table_name, table_name)
                        if table_name not in self.loaded_tables:
                            self.loaded_tables.append(table_name)
                        loaded_count += 1
            
            if loaded_count == 0:
                logger.critical(f"[DB_REGISTRY] No table entries found in {registry_path.name}.")
                sys.exit(WaidExit.CONFIG_FAIL)
                
            logger.debug(f"[DB_REGISTRY] Successfully loaded {loaded_count} active tables from {registry_path.name}")
        except Exception as exc:
            logger.error(f"[DB_REGISTRY] Failed to parse active table registry: {exc}")
        
    def dump(self) -> dict:
        """
        @brief Dumps the database registry status and active loaded tables.

        @return dict containing registry filename and active table names.
        """
        return {
            "registry_filename": self.registry_filename,
            "loaded_tables": self.loaded_tables
        }
            
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
        @return None
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

        @return None
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

        @return None
        """
        self.waid_source_dir: Optional[Path] = self._get_path_env("WAID_SOURCE")
        self.waid_mock_dir: Optional[Path] = self._get_path_env("WAID_MOCK_DIR")
        self.waid_mock_data_dir: Optional[Path] = self._get_path_env("WAID_MOCK_DATA_DIR")
        self.log_dir: Optional[Path] = self._get_path_env("WAID_LOG_DIR")
        self.log_level: str = os.getenv("WAID_LOG_LEVEL", "INFO")
        self.debug_mode: bool = os.getenv("WAID_LOG_LEVEL", "info").lower() == "debug"
        self._validate_config()

        waid_setup_mode = os.getenv("WAID_SETUP_MODE")
        if not waid_setup_mode or not waid_setup_mode.strip():
            waid_setup_mode = "0"
            logger.debug(f"[CONFIG_FALLBACK] WAID_SETUP_MODE is missing or empty. Using default fallback: {waid_setup_mode}")
        else:
            logger.warning(f"Using required fallback WAID_SETUP_MODE: {waid_setup_mode}")

        self.setup_mode = int(waid_setup_mode.strip() or 0)
        self.waid_sim_mode: bool = os.getenv("WAID_SIM_MODE", "false").lower() == "true"
        
        if self.waid_sim_mode:
            self.waid_data_dir: Optional[Path] = self.waid_mock_data_dir
        else:
            self.waid_data_dir: Optional[Path] = self._get_path_env("WAID_DATA_DIR")

class WaidSettings(BaseConfig):
    """
    @brief Application-level configurations and pipeline specifications.
    """

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
        @return None
        """
        self.config_dir: Optional[Path] = self._get_path_env("WAID_CONFIG_DIR")
        self.log_dir: Optional[Path] = self._get_path_env("WAID_LOG_DIR")
        self.deploy_dir: Optional[Path] = self._get_path_env("WAID_DEPLOY_DIR")
        self.docs_dir: Optional[Path] = self._get_path_env("WAID_DOCS_DIR")
        self.tools_dir: Optional[Path] = self._get_path_env("WAID_TOOLS_DIR")
        
        if boot_settings.waid_sim_mode:
            self.waid_data_dir: Optional[Path] = boot_settings.waid_mock_data_dir
            self.ecowitt_dir: Optional[Path] = \
                boot_settings.waid_mock_data_dir / Path(self._get_path_env("WAID_ECOWITT_DIR")).name
            self.era5_data_dir: Optional[Path] = \
                boot_settings.waid_mock_data_dir / Path(self._get_path_env("WAID_ERA5_DATA_DIR")).name
            self.ml_matches_dir: Optional[Path] = \
                boot_settings.waid_mock_data_dir / Path(self._get_path_env("WAID_ML_MATCHES_DIR")).name
            self.ml_tensors_dir: Optional[Path] = \
                boot_settings.waid_mock_data_dir / Path(self._get_path_env("WAID_ML_TENSORS_DIR")).name
            self.ml_models_dir: Optional[Path] = \
                boot_settings.waid_mock_data_dir / Path(self._get_path_env("WAID_ML_MODELS_DIR")).name
            
            self.waid_db_file: Optional[str] = os.getenv("WAID_DB_MOCK_FILE")
            self.deploy_db_file: Optional[str] = os.getenv("WAID_DEPLOY_MOCK_FILE")
        else:
            self.waid_data_dir: Optional[Path] = self._get_path_env("WAID_DATA_DIR")
            self.ecowitt_dir: Optional[Path] = self._get_path_env("WAID_ECOWITT_DIR")
            self.era5_data_dir: Optional[Path] = self._get_path_env("WAID_ERA5_DATA_DIR")
            self.ml_matches_dir: Optional[Path] = self._get_path_env("WAID_ML_MATCHES_DIR")
            self.ml_tensors_dir: Optional[Path] = self._get_path_env("WAID_ML_TENSORS_DIR")
            self.ml_models_dir: Optional[Path] = self._get_path_env("WAID_ML_MODELS_DIR")

            self.waid_db_file: Optional[str] = os.getenv("WAID_DB_FILE")
            self.deploy_db_file: Optional[str] = os.getenv("WAID_DEPLOY_FILE")
            
        critical_data_dirs = {
            "WAID_DATA_DIR": self.waid_data_dir,
            "WAID_ECOWITT_DIR": self.ecowitt_dir,
            "WAID_ERA5_DATA_DIR": self.era5_data_dir,
            "WAID_ML_MATCHES_DIR": self.ml_matches_dir,
            "WAID_ML_MODELS_DIR": self.ml_models_dir,
            "WAID_ML_TENSORS_DIR": self.ml_tensors_dir,
        }
        for env_key, dir_path in critical_data_dirs.items():
            logger.debug(f"{env_key} = {dir_path}")
            if dir_path:
                path_obj = Path(dir_path)
                if not path_obj.exists():
                    path_obj.mkdir(parents=True, exist_ok=True)
                    logger.info(f"[BOOT] Automatically created missing data directory: {path_obj}")

        self.version: Optional[str] = os.getenv("WAID_VERSION")
        
        self.output_features = self.ML_OUTPUT_FEATURES
        self.input_features = self.ML_INPUT_FEATURES
        self.input_features_match = self.ML_INPUT_FEATURES_MATCH
        self.n_input_features: int = len(self.input_features)
        self.n_output_features: int = len(self.output_features)
        
        self.deploy_mode: Optional[str] = get_env_with_fallback("WAID_DEPLOY_MODE", "local", var_type=str).lower()

        self.dbt_dir: Optional[Path] = self._get_path_env("WAID_DBT_DIR")
        self.dbt_profiles_dir: Optional[Path] = self._get_path_env("WAID_DBT_PROFILES_DIR")
        self.dbt_models_md_file: Optional[str] = os.getenv("WAID_DBT_MODELS_MD_FILE")
        self.dbt_hash_file : Optional[str] = os.getenv("WAID_DBT_HASH_FILE")
        self.dbt_registry_name: Optional[str] = os.getenv("WAID_DBT_REGISTRY_NAME", "Active Table Registry")
        self.dbt_bin_file = Path(os.getenv("WAID_SOURCE")) / ".venv-dbt" / "bin" / "dbt"

        self.ecowitt_gw_ip: Optional[str] = get_env_with_fallback("WAID_ECOWITT_GW_IP", "192.168.1.100", var_type=str)
        self.ecowitt_gw_port: Optional[int] = self._get_int_env("WAID_ECOWITT_GW_PORT")
        self.ecowitt_gw_timeout_sec: Optional[int] = self._get_int_env("WAID_ECOWITT_GW_TIMEOUT_SEC", 10)

        self.ecowitt_station_id: Optional[str] = get_env_with_fallback("WAID_ECOWITT_STATION_ID", "STATION_01", var_type=str)
        self.ecowitt_station_name: Optional[str] = get_env_with_fallback("WAID_ECOWITT_STATION_NAME", "Local Home Weather Station", var_type=str)
        self.ecowitt_latitude = get_env_with_fallback("WAID_ECOWITT_LATITUDE", 41.9028, var_type=float)
        self.ecowitt_longitude: float = get_env_with_fallback("WAID_ECOWITT_LONGITUDE", 12.4964, var_type=float)
        self.ecowitt_elevation_m: Optional[float] = get_env_with_fallback("WAID_ECOWITT_ELEVATION_M", 20.0, var_type=float)
        self.ecowitt_floor: Optional[float] = get_env_with_fallback("WAID_ECOWITT_FLOOR", 2, var_type=int)

        raw_tz = get_env_with_fallback("WAID_TIMEZONE", "Europe/Rome", var_type=str)
        self.tz_timezone = self._validate_timezone(raw_tz)

        self.resample_interval_min: Optional[int] = self._get_int_env("WAID_RESAMPLE_INTERVAL_MIN", 60)
        self.max_interpolate_hours: Optional[int] = self._get_int_env("WAID_MAX_INTERPOLATE_HOURS", 2)

        self.era5_api_url: Optional[str] = os.getenv("WAID_ERA5_API_URL")
        self.era5_api_key: str = get_env_with_fallback("WAID_ERA5_API_KEY", "placeholder_era5_key", var_type=str)

        self.forecast_horizon_hours: Optional[int] = self._get_int_env("WAID_FORECAST_HORIZON_HOURS")
        self.lookback_hours: Optional[int] = self._get_int_env("WAID_LOOKBACK_HOURS", 24)
        self.fastapi_port: Optional[int] = self._get_int_env("WAID_FASTAPI_PORT", 8000)
        self.streamlit_port: Optional[int] = self._get_int_env("WAID_STREAMLIT_PORT", 8501)
        self.streamlit_url: Optional[str] = os.getenv("WAID_STREAMLIT_URL", "https://waid-analytics.streamlit.app/")

        self.ml_threshold_min: Optional[int] = self._get_int_env("WAID_ML_THRESHOLD_MIN")

        self.max_bias_temp: Optional[float] = self._get_float_env("WAID_ML_BIAS_TEMP")
        self.max_bias_pres: Optional[float] = self._get_float_env("WAID_ML_BIAS_PRES")
        self.max_bias_rh: Optional[float] = self._get_float_env("WAID_ML_BIAS_RH")
        self.max_bias_wind: Optional[float] = self._get_float_env("WAID_ML_BIAS_WIND")
        self.max_bias_solar: Optional[float] = self._get_float_env("WAID_ML_BIAS_SOLAR")
        self.max_bias_rain: Optional[float] = self._get_float_env("WAID_ML_BIAS_RAIN")

        self.ml_min_training_days: Optional[int] = self._get_int_env("WAID_ML_MIN_TRAINING_DAYS", 14)
        self.ml_retrain_window_days: Optional[int] = self._get_int_env("WAID_ML_RETRAIN_WINDOW_DAYS", 30)

        self.ml_model_h5_file: Optional[str] = os.getenv("WAID_ML_MODEL_H5_FILE")
        self.ml_input_scaler_pkl_file: Optional[str] = os.getenv("WAID_ML_INPUT_SCALER_PKL_FILE")
        self.ml_output_scaler_pkl_file: Optional[str] = os.getenv("WAID_ML_OUTPUT_SCALER_PKL_FILE")

        self.scheduled_interval_hours: Optional[int] = self._get_int_env("SCHEDULER_INTERVAL_HOURS", 1)

        self.backfill_begin_period: Optional[datetime] = validate_period(os.getenv("SCHEDULER_BACKFILL_BEGIN_PERIOD"), allow_none=True)
        self.backfill_end_period: Optional[datetime] = validate_period(os.getenv("SCHEDULER_BACKFILL_END_PERIOD"), allow_none=True)
        self.auto_backfill: bool = os.getenv("AUTO_BACKFILL", "false").lower() == "true"

        self.retro_now: Optional[datetime] = validate_mock_timestamp(os.getenv("WAID_RETRO_NOW"))
        self.mock_interval_hours: int = self._get_int_env("WAID_RETRO_INTERVAL_HOURS", 1)
        self.retro_cleanup: bool = os.getenv("WAID_RETRO_CLEANUP", "false").lower() == "true"

        self.reconciliation_cutoff_days: Optional[int] = self._get_int_env("WAID_RECONCILIATION_CUTOFF_DAYS", 6)

        self.db_schema_target: Optional[str] = os.getenv("WAID_DB_SCHEMA_TARGET", "draft")

        self.dev_db_config: DBCredentials = get_db_credentials("draft")
        self.prod_db_config: DBCredentials = get_db_credentials("prod")
        self.retro_db_config: DBCredentials = get_db_credentials("retro")

        self.active_db_config: DBCredentials = get_db_credentials(self.db_schema_target)

        self._validate_config(boot_settings)
            
    def _validate_config(self, boot_settings: BootSettings) -> None:
        """
        @brief Overridden configuration validator.
        @param boot_settings The loaded bootstrap settings instance.
        @details 1. Validates base configuration excluding explicitly optional fields.
                 2. Performs sanity checks on station metadata and structural requirements.

        @return None
        """
        super()._validate_config(optional_fields={
            "retro_now",
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

        if boot_settings.waid_sim_mode and not self.waid_db_file:
            station_errors.append(
                "WAID_SIM_MODE is True, but WAID_DB_MOCK_FILE is missing in environment config."
            )

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


def logger_format_value(value: Any) -> str:
    """
    @brief Formats array-like or sequence input values into space-separated string representation.

    @param value Input object containing data or numpy array-like object with flatten capability.
    @return Space-separated string representation of values.
    """
    if hasattr(value, "flatten"):
        value = value.flatten()
    return " ".join(str(x) for x in value)


# ==============================================================================
# INITIALIZATION RUNTIME
# ==============================================================================

boot_env = BootSettings()
waid_settings_instance = WaidSettings(boot_settings=boot_env)

class WaidBoot:
    """
    @brief Unified access interface for bootstrap configuration components and database registry.
    """
    def __init__(
        self,
        boot_settings: Optional[BootSettings] = None,
        settings: Optional[WaidSettings] = None
    ) -> None:
        """
        @brief Initializes the unified boot access wrapper and triggers configuration/registry dumps.

        @param boot_settings BootSettings instance.
        @param settings WaidSettings instance.
        @return None
        """
        self._boot_settings = boot_settings or boot_env
        self._settings = settings or waid_settings_instance
        self.waid_exit = WaidExit()
        
        self.db = WaidDB(
            data_dir=getattr(self._settings, "waid_data_dir", None),
            registry_filename=getattr(self._settings, "dbt_models_md_file", None)
        )
        
        if execution_guard("WAID_BOOT_DUMP"):
            self.dump()
        
    def dump(self) -> None:
        """
        @brief Log active configuration settings and database registry states for debugging purposes.

        @return None
        """
        logger.info("=== [DEBUG] WAID BOOT UNIFIED CONFIGURATION DUMP ===")
        
        if hasattr(self._boot_settings, "dump"):
            self._boot_settings.dump()
        if hasattr(self._settings, "dump"):
            self._settings.dump()
        
        if hasattr(self, "db"):
            logger.debug("=== [DB_REGISTRY] WAID_DB ACTIVE TABLES REGISTRY ===")
            logger.debug(f"[DB_REGISTRY] data_dir: {getattr(self.db, 'data_dir', 'N/A')}")
            logger.debug(f"[DB_REGISTRY] registry_filename: {getattr(self.db, 'registry_filename', 'N/A')}")
            
            try:
                # Explicitly exclude WaidDB configuration and service attributes
                excluded_attrs = {"data_dir", "registry_filename", "dbt_registry_name", "loaded_tables", "dump"}
                tables_list = [
                    attr for attr in dir(self.db) 
                    if not attr.startswith("_") and attr not in excluded_attrs and not callable(getattr(self.db, attr))
                ]
                logger.debug(f"[DB_REGISTRY] loaded_tables ({len(tables_list)}): {tables_list}")
            except Exception as e:
                logger.debug(f"[DB_REGISTRY] loaded_tables retrieval error: {e}")
            
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

waid_boot = WaidBoot()