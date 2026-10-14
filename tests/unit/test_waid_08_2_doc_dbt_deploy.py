#!/usr/bin/env python3

"""
@file test_waid_08_2_doc_dbt_deploy.py
@brief Unit tests for the WAID dbt documentation and deployment synchronization script.
@details Uses pytest, sqlite3, and mock objects to validate dbt models hashing,
         live tables discovery, and Markdown table metadata extraction.
@author AF
@date 2026
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import sqlite3
import pytest

# Set a dummy environment variable to bypass initial check
os.environ.setdefault("WAID_SOURCE", "/dummy/path")

# Mock boot and shared modules prior to import
sys_modules_patch = patch.dict("sys.modules", {
    "boot": MagicMock(),
})
sys_modules_patch.start()

import waid_08_2_doc_dbt_deploy as doc_deploy


def test_calculate_models_hash(tmp_path: Path) -> None:
    """
    @brief Tests the calculation of a unique hash representing the dbt models directory state.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    # Create a dummy directory structure for dbt models
    dbt_dir = tmp_path / "dbt_project"
    models_dir = dbt_dir / "models"
    models_dir.mkdir(parents=True)
    
    # Create a test .sql file
    model_file = models_dir / "test_model.sql"
    model_file.write_text("SELECT 1 AS id;")
    
    file_hash = doc_deploy.calculate_models_hash(dbt_dir)
    assert isinstance(file_hash, str)
    assert len(file_hash) == 32  # Typical MD5 hash length


def test_get_pure_live_tables_non_existent(tmp_path: Path) -> None:
    """
    @brief Tests that querying live tables from a non-existent database returns an empty list.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    # Non-existent database must return an empty list
    non_existent_db = tmp_path / "non_existent.db"
    tables = doc_deploy.get_pure_live_tables(non_existent_db)
    assert tables == []


def test_get_pure_live_tables_success(tmp_path: Path) -> None:
    """
    @brief Tests successful discovery of user tables while filtering out internal system tables.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    # Create a temporary SQLite database with a valid user table
    db_path = tmp_path / "test_live.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);")
    conn.commit()
    conn.close()

    tables = doc_deploy.get_pure_live_tables(db_path)
    # Verify that the user table is present
    assert "users" in tables
    assert not any(t.startswith("sqlite_") for t in tables)


def test_extract_table_info(tmp_path: Path) -> None:
    """
    @brief Tests extraction of table schema information into Markdown format.
    @param tmp_path Pytest fixture providing a temporary directory.
    """
    # Create a database and a table to test Markdown table info extraction
    db_path = tmp_path / "info_test.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, title TEXT NOT NULL);")
    conn.commit()

    cursor.execute('PRAGMA table_info("items")')
    markdown_content = doc_deploy.extract_table_info(cursor, "items")
    
    conn.close()

    assert "#### Table: `items`" in markdown_content
    assert "id" in markdown_content
    assert "title" in markdown_content
    assert "YES" in markdown_content  # Corresponding PK or NotNull status