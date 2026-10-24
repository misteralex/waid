#!/usr/bin/env python3

"""
@file waid_init_main_db.py
@brief Initialization tool to create the raw SQLite database (waid.db).
@details Parses for the Markdown SSOT file (WAID_DBT_SSOT_FILE) to extract 
         [DB-Raw] fixed tables and initialize the database.
@author AF
@date 2026
"""

import os
os.environ["WAID_LOG_PREFIX"] = "ops_db_init"
from config.boot import (
    WaidBoot,
    WError,
    WaidExit,
)
import sys
import sqlite3
import re
from pathlib import Path
from loguru import logger

    
def _get_ssot_markdown_path(env: WaidBoot) -> Path:
    """
    @brief Validates and retrieves the path of the SSOT markdown documentation file.
    @param env WaidBoot instance containing configuration paths.
    @return Path to the SSOT file (WAID_DBT_SSOT_FILE)
    """
    doc_filename = env.dbt_ssot_file
    
    # Check in docs directory first, then fallback to data directory
    doc_path = Path(env.docs_dir) / env.dbt_ssot_file
    if not doc_path.is_file():
        doc_path = Path(env.waid_data_dir) / env.dbt_ssot_file
        
    if not doc_path.is_file():
        logger.error(
            f"[CRITICAL] Mandatory SSOT documentation file '{env.dbt_ssot_file}' is missing."
            f" Please check: {doc_path}. This file must be generated or updated via waid_08_2."
        )
        sys.exit(env.waid_exit.INTERNAL_ERROR)
        
    logger.info(f"Using SSOT documentation file: {doc_path}")
    return doc_path


def _parse_raw_tables_from_ssot(ssot_path: Path) -> dict:
    """
    @brief Parses the SSOT Markdown file to extract fixed raw tables and their schemas.
    @param ssot_path Path to the Markdown SSOT file (WAID_DBT_SSOT_FILE).
    @return Dictionary mapping table names to their SQL create statements.
    """
    content = ssot_path.read_text(encoding="utf-8")
    
    # Isolate the Fixed Raw Operational Tables section
    section_match = re.search(r'## Fixed Raw Operational Tables \(SSOT\)(.*?)'
                              '(?=\n## dbt Transform Models Details)', content, re.DOTALL)    
    if not section_match:
        logger.warning("Fixed Raw Operational Tables section not found in SSOT.")
        return {}
        
    section_text = section_match.group(1)
    
    # Find all tables defined in this section (#### Table: `table_name`)
    table_blocks = re.split(r'####\s+Table:\s+`([^`]+)`', section_text)
    
    tables_specs = {}
    
    # re.split with capture group alternates: [before, name1, block1, name2, block2, ...]
    for i in range(1, len(table_blocks), 2):
        tname = table_blocks[i].strip()
        block_content = table_blocks[i+1]
        
        # Parse markdown table rows: | **col** | `type` | notnull | default | pk |
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
            
            if len(pk_cols) == 1:
                # Se c'è una sola PK, possiamo marcarla direttamente nel tipo se non già fatto, oppure aggiungere il vincolo
                pass 
            elif len(pk_cols) > 1:
                columns_def.append(f"    PRIMARY KEY ({', '.join(pk_cols)})")
                
            create_sql = f"CREATE TABLE IF NOT EXISTS {tname} (\n" + ",\n".join(columns_def) + "\n);"
            tables_specs[tname] = create_sql

    if not tables_specs:
        logger.warning(f"Empty list, unexpected format: {list(tables_specs.keys())}")
    else:
        logger.info(f"Successfully parsed DB-Raw tables from SSOT section: {list(tables_specs.keys())}")
    
    return tables_specs


def _create_raw_tables_from_ssot(db_path: Path, ssot_path: Path) -> None:
    """
    @brief Creates all DB-Raw tables in the SQLite database dynamically parsed from the SSOT Markdown.
    @param db_path Path to the SQLite database file.
    @param ssot_path Path to the Markdown SSOT file (WAID_DBT_SSOT_FILE).
    """
    tables_specs = _parse_raw_tables_from_ssot(ssot_path)
    
    if not tables_specs:
        raise WError("No valid DB-Raw table specifications could be extracted from SSOT.", 1)

    logger.info(f"Connecting to SQLite database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign key support
    cursor.execute("PRAGMA foreign_keys = ON;")

    for table_name, sql_query in tables_specs.items():
        logger.info(f"Creating table: {table_name}")
        cursor.execute(sql_query)

    conn.commit()
    conn.close()
    logger.info("All DB-Raw tables successfully created from SSOT definitions.")


def _check_main_database(env: WaidBoot) -> int:
    """
    @brief Check if main SQLite database already exists.
    @param env WaidBoot instance containing configuration paths.
    @return Process exit code integer.
    """
    waid_db_file = Path(env.waid_db_file)
    if waid_db_file.exists():
        logger.warning(f"Database file {waid_db_file} already exists. Stopping initialization.")
        return getattr(env.waid_exit, "DB_ALREADY_EXISTS", 8)
        
    return env.waid_exit.SUCCESS


def main() -> int:
    """
    @brief Main execution entry point for database initialization.
    @return Process exit code integer.
    """
    try:
        env = WaidBoot()
        
        # Check database existence -> Stop with warning if exists
        db_check_result = _check_main_database(env)
        if db_check_result != env.waid_exit.SUCCESS:
            return db_check_result
            
        # Get and validate SSOT documentation path
        ssot_path = _get_ssot_markdown_path(env)

        # Create database and tables dynamically from SSOT
        waid_db_file = Path(env.waid_db_file)
        waid_db_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Creating new SQLite database at: {waid_db_file}")
        _create_raw_tables_from_ssot(waid_db_file, ssot_path)
        
        logger.success("=== Database Initialization Successfully Completed ===")

    except WError as e:
        logger.error(e)
        return e.code

    except Exception:
        logger.exception("Unexpected error while initializing database.")
        return env.waid_exit.INTERNAL_ERROR

    return env.waid_exit.SUCCESS


if __name__ == "__main__":
    sys.exit(main())