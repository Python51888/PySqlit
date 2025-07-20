"""PySQLit test suite

This package contains comprehensive unit tests for all PySQLit modules.
Tests are organized by module and follow pytest conventions.
"""

import os
import tempfile
import shutil
from pathlib import Path

# Test constants
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TEMP_DB_PREFIX = "test_pysqlit_"


def get_test_data_dir():
    """Get or create test data directory."""
    TEST_DATA_DIR.mkdir(exist_ok=True)
    return TEST_DATA_DIR


def create_temp_db(suffix=".db"):
    """Create a temporary database file for testing."""
    temp_dir = tempfile.mkdtemp(prefix=TEMP_DB_PREFIX)
    db_path = os.path.join(temp_dir, f"test{suffix}")
    return db_path, temp_dir


def cleanup_temp_db(temp_dir):
    """Clean up temporary database directory."""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def setup_test_environment():
    """Set up test environment with necessary directories."""
    get_test_data_dir()
    # Ensure backups directory exists
    backups_dir = get_test_data_dir() / "backups"
    backups_dir.mkdir(exist_ok=True)
    return get_test_data_dir()