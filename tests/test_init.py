"""Unit tests for pysqlit/__init__.py module."""

import pytest
from pysqlit import (
    EnhancedDatabase,
    EnhancedREPL,
    TransactionManager,
    IsolationLevel,
    BackupManager,
    DDLManager,
    Row,
    DataType,
    TableSchema,
    ColumnDefinition
)


class TestInit:
    """Test cases for pysqlit package initialization."""
    
    def test_import_enhanced_database(self):
        """Test EnhancedDatabase can be imported."""
        assert EnhancedDatabase is not None
        assert callable(EnhancedDatabase)
    
    def test_import_enhanced_repl(self):
        """Test EnhancedREPL can be imported."""
        assert EnhancedREPL is not None
        assert callable(EnhancedREPL)
    
    def test_import_transaction_manager(self):
        """Test TransactionManager can be imported."""
        assert TransactionManager is not None
        assert callable(TransactionManager)
    
    def test_import_isolation_level(self):
        """Test IsolationLevel can be imported."""
        assert IsolationLevel is not None
        assert hasattr(IsolationLevel, 'READ_UNCOMMITTED')
        assert hasattr(IsolationLevel, 'READ_COMMITTED')
        assert hasattr(IsolationLevel, 'REPEATABLE_READ')
        assert hasattr(IsolationLevel, 'SERIALIZABLE')
    
    def test_import_backup_manager(self):
        """Test BackupManager can be imported."""
        assert BackupManager is not None
        assert callable(BackupManager)
    
    def test_import_ddl_manager(self):
        """Test DDLManager can be imported."""
        assert DDLManager is not None
        assert callable(DDLManager)
    
    def test_import_row(self):
        """Test Row can be imported."""
        assert Row is not None
        assert callable(Row)
    
    def test_import_data_type(self):
        """Test DataType can be imported."""
        assert DataType is not None
        assert hasattr(DataType, 'INTEGER')
        assert hasattr(DataType, 'TEXT')
        assert hasattr(DataType, 'REAL')
        assert hasattr(DataType, 'BLOB')
        assert hasattr(DataType, 'NULL')
    
    def test_import_table_schema(self):
        """Test TableSchema can be imported."""
        assert TableSchema is not None
        assert callable(TableSchema)
    
    def test_import_column_definition(self):
        """Test ColumnDefinition can be imported."""
        assert ColumnDefinition is not None
        assert callable(ColumnDefinition)
    
    def test_all_exports(self):
        """Test __all__ contains expected exports."""
        import pysqlit
        
        expected_exports = [
            "EnhancedDatabase",
            "EnhancedREPL",
            "TransactionManager",
            "IsolationLevel",
            "BackupManager",
            "DDLManager",
            "Row",
            "DataType",
            "TableSchema",
            "ColumnDefinition"
        ]
        
        for export in expected_exports:
            assert hasattr(pysqlit, export)
            assert export in pysqlit.__all__
    
    def test_version_info(self):
        """Test version information is available."""
        import pysqlit
        
        assert hasattr(pysqlit, '__version__')
        assert hasattr(pysqlit, '__author__')
        assert pysqlit.__version__ == "1.0.0"
        assert pysqlit.__author__ == "PySQLit Team"
    
    def test_package_initialization(self):
        """Test package can be imported without errors."""
        import pysqlit
        
        # Should not raise any exceptions
        assert pysqlit is not None
        
        # Check that it's a proper package
        assert hasattr(pysqlit, '__path__')
        assert hasattr(pysqlit, '__file__')