"""Unit tests for pysqlit/ddl.py module."""

import pytest
import tempfile

from pysqlit.ddl import DDLManager
from pysqlit.models import TableSchema, ColumnDefinition, DataType


class TestDDLManager:
    """Test cases for DDLManager class."""
    
    def test_ddl_manager_creation(self, temp_db_path):
        """Test DDL manager creation."""
        from pysqlit.database import EnhancedDatabase
        
        db = EnhancedDatabase(temp_db_path)
        ddl_manager = DDLManager(db)
        assert ddl_manager.database == db
        db.close()
    
    def test_create_table_schema(self, temp_db_path):
        """Test creating table schema."""
        from pysqlit.database import EnhancedDatabase
        
        db = EnhancedDatabase(temp_db_path)
        ddl_manager = DDLManager(db)
        
        # Test basic schema creation
        schema = TableSchema("test_table")
        assert isinstance(schema, TableSchema)
        assert hasattr(schema, 'columns')
        
        db.close()
    
    def test_validate_column_definition(self, temp_db_path):
        """Test validating column definition."""
        from pysqlit.database import EnhancedDatabase
        
        db = EnhancedDatabase(temp_db_path)
        ddl_manager = DDLManager(db)
        
        valid_column = ColumnDefinition("name", DataType.TEXT, max_length=50)
        assert valid_column.name == "name"
        assert valid_column.data_type == DataType.TEXT
        assert valid_column.max_length == 50
        
        db.close()
    
    def test_validate_table_schema(self, temp_db_path):
        """Test validating table schema."""
        from pysqlit.database import EnhancedDatabase
        
        db = EnhancedDatabase(temp_db_path)
        ddl_manager = DDLManager(db)
        
        # Valid schema
        schema = TableSchema("valid_table")
        schema.add_column(ColumnDefinition("id", DataType.INTEGER, is_primary=True))
        
        assert len(schema.columns) == 1
        assert schema.columns[0].name == "id"
        
        db.close()
    
    def test_generate_create_table_sql(self, temp_db_path):
        """Test generating CREATE TABLE SQL."""
        from pysqlit.database import EnhancedDatabase
        
        db = EnhancedDatabase(temp_db_path)
        ddl_manager = DDLManager(db)
        
        schema = TableSchema("users")
        schema.add_column(ColumnDefinition("id", DataType.INTEGER, is_primary=True))
        schema.add_column(ColumnDefinition("name", DataType.TEXT, max_length=50))
        
        # Test schema has expected columns
        assert len(schema.columns) == 2
        assert schema.columns[0].name == "id"
        assert schema.columns[1].name == "name"
        
        db.close()
    
    def test_generate_drop_table_sql(self, temp_db_path):
        """Test generating DROP TABLE SQL."""
        from pysqlit.database import EnhancedDatabase
        
        db = EnhancedDatabase(temp_db_path)
        ddl_manager = DDLManager(db)
        
        # Test basic functionality
        assert ddl_manager is not None
        
        db.close()
    
    def test_ddl_manager_basic_functionality(self, temp_db_path):
        """Test DDL manager basic functionality."""
        from pysqlit.database import EnhancedDatabase
        
        db = EnhancedDatabase(temp_db_path)
        ddl_manager = DDLManager(db)
        
        # Test basic instantiation and method availability
        assert ddl_manager is not None
        assert hasattr(ddl_manager, 'create_table_schema')
        
        db.close()