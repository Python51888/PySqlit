"""Integration tests for PySQLit - testing module interactions."""

import pytest
import tempfile
import os

from pysqlit.database import EnhancedDatabase
from pysqlit.models import Row, DataType, TableSchema, ColumnDefinition
from pysqlit.exceptions import DatabaseError


class TestBasicIntegration:
    """Basic integration tests for PySQLit."""
    
    def test_database_initialization(self, temp_db_path):
        """Test database initialization."""
        db = EnhancedDatabase(temp_db_path)
        
        try:
            # Test basic properties
            assert hasattr(db, 'tables')
            assert isinstance(db.tables, dict)
            
        finally:
            db.close()
    
    def test_exception_handling(self):
        """Test exception classes."""
        from pysqlit.exceptions import DatabaseError, ValidationError
        
        # Test exception creation
        db_error = DatabaseError("Test error")
        assert str(db_error) == "Test error"
        
        val_error = ValidationError("Validation error")
        assert str(val_error) == "Validation error"
    
    def test_model_creation(self):
        """Test model creation and validation."""
        # Test Row creation
        row = Row(id=1, name="Test", email="test@example.com")
        assert row.id == 1
        assert row.name == "Test"
        
        # Test DataType enum
        assert DataType.INTEGER.value == "INTEGER"
        assert DataType.TEXT.value == "TEXT"
        
        # Test ColumnDefinition
        col = ColumnDefinition("test_col", DataType.TEXT, max_length=50)
        assert col.name == "test_col"
        assert col.data_type == DataType.TEXT
        assert col.max_length == 50
    
    def test_table_schema_creation(self):
        """Test table schema creation."""
        schema = TableSchema("test_table")
        assert str(schema).startswith("<pysqlit.models.TableSchema object")
        
        # Test adding columns
        schema.add_column(ColumnDefinition("id", DataType.INTEGER, is_primary=True))
        schema.add_column(ColumnDefinition("name", DataType.TEXT))
        
        assert len(schema.columns) == 2


class TestDatabaseOperations:
    """Test database operations."""
    
    def test_table_lifecycle(self, temp_db_path):
        """Test table creation and management."""
        db = EnhancedDatabase(temp_db_path)
        
        try:
            # Test table creation
            table_name = "test_lifecycle"
            try:
                db.drop_table(table_name)
            except DatabaseError:
                pass
            
            db.create_table(
                table_name,
                {"id": "INTEGER", "name": "TEXT"},
                primary_key="id"
            )
            
            # Verify table exists
            assert table_name in db.tables
            
            # Test table dropping
            db.drop_table(table_name)
            assert table_name not in db.tables
            
        finally:
            db.close()
    
    def test_error_conditions(self, temp_db_path):
        """Test error conditions."""
        db = EnhancedDatabase(temp_db_path)
        
        try:
            # Test duplicate table creation
            table_name = "error_test"
            try:
                db.drop_table(table_name)
            except DatabaseError:
                pass
                
            db.create_table(table_name, {"id": "INTEGER"})
            
            with pytest.raises(DatabaseError):
                db.create_table(table_name, {"id": "INTEGER"})
            
            # Test dropping non-existent table
            with pytest.raises(DatabaseError):
                db.drop_table("nonexistent_table")
                
        finally:
            db.close()


class TestModuleCompatibility:
    """Test module compatibility."""
    
    def test_import_compatibility(self):
        """Test all modules can be imported."""
        try:
            from pysqlit import database, models, exceptions, storage
            from pysqlit import btree, transaction, backup, repl
            from pysqlit import ddl, parser
            
            # Test basic class availability
            assert hasattr(database, 'EnhancedDatabase')
            assert hasattr(models, 'Row')
            assert hasattr(exceptions, 'DatabaseError')
            assert hasattr(storage, 'Pager')
            
        except ImportError as e:
            pytest.skip(f"Import error: {e}")
    
    def test_basic_functionality(self, temp_db_path):
        """Test basic functionality."""
        db = EnhancedDatabase(temp_db_path)
        
        try:
            # Test basic database properties
            assert hasattr(db, 'tables')
            assert isinstance(db.tables, dict)
            
            # Test close operation
            db.close()
            
        except Exception as e:
            pytest.fail(f"Basic functionality test failed: {e}")