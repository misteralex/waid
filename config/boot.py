#!/usr/bin/env python3

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
from pathlib import Path

# Detect if running on Streamlit Cloud environment
is_streamlit_cloud = "STREAMLIT_SHARING_MODE" in os.environ or Path("/mount/src").exists()

# If on Streamlit Cloud, inject st.secrets into os.environ automatically
if is_streamlit_cloud:
    try:
        import streamlit as st
        for key, value in st.secrets.items():
            if isinstance(value, str):
                os.environ[key] = value
            elif isinstance(value, dict):
                for sub_key, sub_val in value.items():
                    os.environ[f"{key}_{sub_key}"] = str(sub_val)
    except Exception:
        pass

    # Set default WAID_SOURCE for Streamlit Cloud if missing
    if not os.environ.get("WAID_SOURCE"):
        os.environ["WAID_SOURCE"] = "/mount/src/waid-draft"

# Check current source (WAID_SOURCE should be set up)
if not os.environ.get("WAID_SOURCE"):
    sys.exit("[CRITICAL] WAID_SOURCE environment variable is missing. Export it first.")

# Check current python environment (VIRTUAL_ENV or standard venv paths)
python_path = Path(sys.executable)
is_in_venv = (
    "VIRTUAL_ENV" in os.environ
    or ".venv" in python_path.parts
    or "venv" in python_path.parts
    or is_streamlit_cloud
)

if not is_in_venv:
    sys.exit(
        "[CRITICAL] Current Python environment does not match venv. "
        "Activate the correct virtual environment first."
    )

# Load base environment file (boot.env) to ensure all critical variables are available
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(os.environ.get("WAID_SOURCE")) / "config" / "boot.env", override=os.environ.get("WAID_ALLOW_ENV_OVERRIDE"))

# Pre-define environment variable for Loguru colorization
os.environ["LOGURU_COLORIZE"] = "1"
from loguru import logger

import shutil
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Any, List, Dict, Optional
from dataclasses import dataclass
import streamlit as st
import re

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
    DB_ALREADY_EXISTS = 8


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
        log_file_path = current_log_dir / f"waid_{os.getenv('WAID_LOG_PREFIX', 'pipeline')}_{datetime.now().strftime('%Y%m%d')}.log"
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
    logger.info(f"=== 🔶 Booting module context: {caller_script} ===")

# Check WAID_CONFIG_DIR dynamically based on current WAID_SOURCE
config_dir = Path(os.environ.get("WAID_SOURCE")) / "config"
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
        
        # Retrieve the docs directory from the global context or set a safe fallback
        self.docs_dir = getattr(waid_settings_instance, "docs_dir", Path("docs"))
        self.registry_filename = registry_filename or os.getenv("WAID_DBT_SSOT_FILE")
        self.dbt_registry_name = os.getenv("WAID_DBT_REGISTRY_NAME", "Active Table Registry")
        self.loaded_tables: List[str] = []
        
        logger.debug("[DB_REGISTRY] WaidDB initialized with")
        logger.debug(f"[DB_REGISTRY] data_dir: {self.data_dir}")
        logger.debug(f"[DB_REGISTRY] registry_filename: {self.registry_filename}")
        self.load_active_registry()
        
    def resolve_registry_path(self) -> Path:
        """
        @brief Resolves SSOT path with automatic fallback from data dir to docs dir (cold start handling).
        @return Path to the resolved registry file.
        """
        registry_path = Path(self.data_dir) / self.registry_filename
        
        if not registry_path.exists():
            docs_registry = Path(self.docs_dir) / self.registry_filename
            if docs_registry.exists():
                logger.info(f"[SSOT] Registry not found in data dir. Copying from docs SSOT: {docs_registry}")
                registry_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(docs_registry, registry_path)
            else:
                logger.warning(f"[SSOT] Registry file not found in data or docs directories: {registry_path}")
                
        return registry_path

    def load_active_registry(self) -> list:
        """
        @brief Parses the active table registry section to load tables.
        @return List of active table names.
        """
        registry_path = self.resolve_registry_path()
        if not registry_path.exists():
            return []

        loaded_tables = []
        try:
            content = registry_path.read_text(encoding="utf-8")
            in_registry = False
            
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("##") and self.dbt_registry_name in line:
                    in_registry = True
                    continue
                elif in_registry and line.startswith("## "):
                    break
                
                # Filter registry lines containing the [DB-Model] or [DB-Raw] tags
                if in_registry and line.startswith("- ") and "[DB-" in line:
                    parts = line.split("`")
                    if len(parts) >= 4:
                        table_name = parts[3]
                        setattr(self, table_name, table_name)
                        if table_name not in self.loaded_tables:
                            self.loaded_tables.append(table_name)
                        if table_name not in loaded_tables:
                            loaded_tables.append(table_name)
            
            logger.debug(f"[SSOT] Successfully parsed {len(loaded_tables)} active tables.")
        except Exception as exc:
            logger.error(f"[SSOT] Failed to parse active table registry: {exc}")
        
        return loaded_tables

    def parse_raw_tables_specs(self) -> dict:
        """
        @brief Parses the Fixed Raw Operational Tables section to extract SQL schemas from SSOT.
        @return Dictionary mapping table names to their SQL create statements.
        """
        registry_path = self.resolve_registry_path()
        if not registry_path.exists():
            return {}

        content = registry_path.read_text(encoding="utf-8")
        
        # Flexible regex to match Fixed Raw Operational Tables regardless of emojis or exact separators
        section_match = re.search(r'##\s*(?:[^\n]*?)Fixed Raw Operational Tables[^\n]*\n(.*?)(?:\n## |\Z)', content, re.DOTALL | re.IGNORECASE)
        if not section_match:
            logger.warning("[SSOT] Fixed Raw Operational Tables section not found.")
            return {}
            
        section_text = section_match.group(1)
        table_blocks = re.split(r'####\s+Table:\s+`([^`]+)`', section_text)
        
        tables_specs = {}
        for i in range(1, len(table_blocks), 2):
            tname = table_blocks[i].strip()
            block_content = table_blocks[i+1]
            
            rows = re.findall(r'\|\s*\*\*([^*]+)\*\*\s*\|\s*`([^`]+)`\s*\|\s*([^\|]+)\s*\|\s*([^\|]+)\s*\|\s*([^\|]+)\s*\|', block_content)
            if rows:
                columns_def = []
                pk_cols = []
                
                for col_match in rows:
                    col_name = col_match[0].strip()
                    col_type = col_match[1].strip()
                    not_null = col_match[2].strip().upper()
                    default_val = col_match[3].strip()
                    is_pk = col_match[4].strip().upper()
                    
                    col_def = f"    {col_name} {col_type}"
                    if not_null == "YES":
                        col_def += " NOT NULL"
                    if default_val != "-":
                        col_def += f" DEFAULT {default_val}"
                        
                    columns_def.append(col_def)
                    if is_pk == "YES":
                        pk_cols.append(col_name)
                
                if len(pk_cols) > 1:
                    columns_def.append(f"    PRIMARY KEY ({', '.join(pk_cols)})")
                    
                create_sql = f"CREATE TABLE IF NOT EXISTS {tname} (\n" + ",\n".join(columns_def) + "\n);"
                tables_specs[tname] = create_sql

        return tables_specs

    def init_main_database(self, db_file_path: str) -> int:
        """
        @brief Initializes the main SQLite database and creates raw tables from SSOT.
        @param db_file_path Path to the SQLite database file.
        @return Status code (SUCCESS=0 or DB_ALREADY_EXISTS=8).
        """
        db_path = Path(db_file_path)
        if db_path.exists():
            logger.warning(f"Database file {db_path} already exists. Skipping initialization.")
            return 8  # DB_ALREADY_EXISTS
            
        tables_specs = self.parse_raw_tables_specs()
        if not tables_specs:
            logger.error("[DB_INIT] No valid DB-Raw table specifications could be extracted from SSOT.")
            return 1

        db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Connecting to SQLite database at: {db_path}")
        
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            for table_name, sql_query in tables_specs.items():
                logger.info(f"Creating table: {table_name}")
                cursor.execute(sql_query)

            conn.commit()
            conn.close()
            logger.info("All DB-Raw tables successfully created from SSOT definitions.")
        except Exception as exc:
            logger.error(f"[DB_INIT] Failed to initialize database tables: {exc}")
            return 1
            
        return 0
    
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
        self.dbt_ssot_file: Optional[str] = os.getenv("WAID_DBT_SSOT_FILE")
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
        
        self.streamlit_port: Optional[int] = self._get_int_env("WAID_STREAMLIT_PORT", 8501)
        self.streamlit_url: Optional[str] = os.getenv("WAID_STREAMLIT_URL", "https://waid-analytics.streamlit.app/")
        self.streamlit_dir: Optional[str] = os.getenv("WAID_STREAMLIT_APP_DIR")
        self.streamlit_dir: Optional[Path] = self._get_path_env("WAID_STREAMLIT_APP_DIR")
        
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
            data_dir=self.waid_data_dir,
            registry_filename=self.dbt_ssot_file
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
                excluded_attrs = {
                    "data_dir", "docs_dir", "registry_filename", "dbt_registry_name", 
                    "loaded_tables", "dump", "resolve_registry_path", 
                    "load_active_registry", "parse_raw_tables_specs", "init_main_database"
                }                
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
