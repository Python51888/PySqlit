"""Pytest configuration and fixtures for PySQLit tests."""

import os
import tempfile
import shutil
import pytest
from pathlib import Path

from pysqlit.database import EnhancedDatabase
from pysqlit.models import Row, DataType, TableSchema, ColumnDefinition


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    temp_dir = tempfile.mkdtemp(prefix="pysqlit_test_")
    db_path = os.path.join(temp_dir, "test.db")
    yield db_path
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def database(temp_db_path):
    """Create a fresh EnhancedDatabase instance."""
    db = EnhancedDatabase(temp_db_path)
    yield db
    db.close()


@pytest.fixture
def sample_table_schema():
    """Create a sample table schema for testing."""
    schema = TableSchema("test_table")
    schema.add_column(ColumnDefinition("id", DataType.INTEGER, is_primary=True))
    schema.add_column(ColumnDefinition("name", DataType.TEXT, max_length=50))
    schema.add_column(ColumnDefinition("age", DataType.INTEGER))
    schema.add_column(ColumnDefinition("email", DataType.TEXT, max_length=100, is_unique=True))
    return schema


@pytest.fixture
def sample_rows():
    """Create sample rows for testing."""
    return [
        Row(id=1, name="Alice", age=30, email="alice@example.com"),
        Row(id=2, name="Bob", age=25, email="bob@example.com"),
        Row(id=3, name="Charlie", age=35, email="charlie@example.com"),
    ]


@pytest.fixture
def populated_database(database, sample_table_schema, sample_rows):
    """Create a database with a populated table."""
    # Create table
    database.create_table(
        "test_table",
        {
            "id": "INTEGER",
            "name": "TEXT",
            "age": "INTEGER",
            "email": "TEXT"
        },
        primary_key="id"
    )
    
    # Insert sample data
    for row in sample_rows:
        database.tables["test_table"].insert_row(row)
    
    return database


@pytest.fixture
def empty_database(database):
    """Create an empty database for testing."""
    return database


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Create test data directory
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    # Create backups directory
    backups_dir = test_data_dir / "backups"
    backups_dir.mkdir(exist_ok=True)
    
    yield
    
    # Cleanup after test
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir, ignore_errors=True)


@pytest.fixture
def mock_file_locks(mocker):
    """Mock file locking for concurrent tests."""
    mocker.patch('pysqlit.concurrent_storage.filelock.FileLock')
    return mocker


@pytest.fixture
def temp_log_file():
    """Create a temporary log file."""
    temp_dir = tempfile.mkdtemp(prefix="pysqlit_log_")
    log_path = os.path.join(temp_dir, "test.log")
    yield log_path
    shutil.rmtree(temp_dir, ignore_errors=True)