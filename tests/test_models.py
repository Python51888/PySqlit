"""Unit tests for pysqlit/models.py module."""

import json
import os
import tempfile
import shutil
from datetime import datetime
import pytest

from pysqlit.models import (
    DataType,
    ColumnDefinition,
    TableSchema,
    Row,
    TransactionLog,
    MetaCommandResult,
    PrepareResult,
    ExecuteResult,
    StatementType,
    ForeignKeyConstraint,
    IndexDefinition
)


class TestDataType:
    """Test cases for DataType enum."""
    
    def test_data_type_values(self):
        """Test DataType enum values."""
        assert DataType.INTEGER.value == "INTEGER"
        assert DataType.TEXT.value == "TEXT"
        assert DataType.REAL.value == "REAL"
        assert DataType.BLOB.value == "BLOB"
        assert DataType.NULL.value == "NULL"
    
    def test_data_type_from_string_exact_match(self):
        """Test from_string with exact matches."""
        assert DataType.from_string("INTEGER") == DataType.INTEGER
        assert DataType.from_string("TEXT") == DataType.TEXT
        assert DataType.from_string("REAL") == DataType.REAL
        assert DataType.from_string("BLOB") == DataType.BLOB
        assert DataType.from_string("NULL") == DataType.NULL
    
    def test_data_type_from_string_case_insensitive(self):
        """Test from_string is case insensitive."""
        assert DataType.from_string("integer") == DataType.INTEGER
        assert DataType.from_string("TEXT") == DataType.TEXT
        assert DataType.from_string("Real") == DataType.REAL
    
    def test_data_type_from_string_affinity_mapping(self):
        """Test from_string with type affinity mappings."""
        assert DataType.from_string("INT") == DataType.INTEGER
        assert DataType.from_string("VARCHAR") == DataType.TEXT
        assert DataType.from_string("FLOAT") == DataType.REAL
        assert DataType.from_string("BOOLEAN") == DataType.INTEGER
    
    def test_data_type_from_string_unknown_type(self):
        """Test from_string with unknown type defaults to TEXT."""
        assert DataType.from_string("UNKNOWN_TYPE") == DataType.TEXT
        assert DataType.from_string("CUSTOM_TYPE") == DataType.TEXT


class TestColumnDefinition:
    """Test cases for ColumnDefinition."""
    
    def test_column_definition_creation(self):
        """Test basic column definition creation."""
        col = ColumnDefinition("test_col", DataType.TEXT)
        assert col.name == "test_col"
        assert col.data_type == DataType.TEXT
        assert col.is_primary is False
        assert col.is_nullable is True
        assert col.is_unique is False
        assert col.default_value is None
        assert col.max_length is None
    
    def test_column_definition_with_all_options(self):
        """Test column definition with all options."""
        col = ColumnDefinition(
            name="id",
            data_type=DataType.INTEGER,
            is_primary=True,
            is_nullable=False,
            is_unique=True,
            default_value=0,
            max_length=10
        )
        assert col.name == "id"
        assert col.data_type == DataType.INTEGER
        assert col.is_primary is True
        assert col.is_nullable is False
        assert col.is_unique is True
        assert col.default_value == 0
        assert col.max_length == 10
    
    def test_column_definition_to_dict(self):
        """Test converting column definition to dictionary."""
        col = ColumnDefinition(
            name="email",
            data_type=DataType.TEXT,
            is_primary=False,
            is_nullable=False,
            is_unique=True,
            max_length=255
        )
        
        expected = {
            'name': 'email',
            'data_type': 'TEXT',
            'is_primary': False,
            'is_nullable': False,
            'is_unique': True,
            'is_autoincrement': False,
            'default_value': None,
            'max_length': 255,
            'foreign_key': None
        }
        
        assert col.to_dict() == expected
    
    def test_column_definition_from_dict(self):
        """Test creating column definition from dictionary."""
        data = {
            'name': 'username',
            'data_type': 'TEXT',
            'is_primary': True,
            'is_nullable': False,
            'is_unique': True,
            'default_value': 'guest',
            'max_length': 50
        }
        
        col = ColumnDefinition.from_dict(data)
        assert col.name == 'username'
        assert col.data_type == DataType.TEXT
        assert col.is_primary is True
        assert col.is_nullable is False
        assert col.is_unique is True
        assert col.default_value == 'guest'
        assert col.max_length == 50


class TestTableSchema:
    """Test cases for TableSchema."""
    
    def test_table_schema_creation(self):
        """Test basic table schema creation."""
        schema = TableSchema("users")
        assert schema.table_name == "users"
        assert len(schema.columns) == 0
        assert schema.primary_key is None
        assert len(schema.foreign_keys) == 0
        assert len(schema.indexes) == 0
        assert schema.auto_increment_value == 1
    
    def test_add_column(self):
        """Test adding columns to schema."""
        schema = TableSchema("users")
        col1 = ColumnDefinition("id", DataType.INTEGER, is_primary=True)
        col2 = ColumnDefinition("name", DataType.TEXT, max_length=50)
        
        schema.add_column(col1)
        schema.add_column(col2)
        
        assert len(schema.columns) == 2
        assert schema.columns["id"] == col1
        assert schema.columns["name"] == col2
        assert schema.primary_key == "id"
    
    def test_add_foreign_key(self):
        """Test adding foreign key constraints."""
        schema = TableSchema("orders")
        fk = ForeignKeyConstraint(
            column="user_id",
            ref_table="users",
            ref_column="id",
            on_delete="CASCADE",
            on_update="CASCADE"
        )
        
        schema.add_foreign_key(fk)
        assert len(schema.foreign_keys) == 1
        assert schema.foreign_keys[0] == fk
    
    def test_add_index(self):
        """Test adding indexes."""
        schema = TableSchema("users")
        index = IndexDefinition(
            name="idx_email",
            columns=["email"],
            is_unique=True
        )
        
        schema.add_index(index)
        assert len(schema.indexes) == 1
        assert schema.indexes["idx_email"] == index
    
    def test_get_column(self):
        """Test getting column by name."""
        schema = TableSchema("users")
        col = ColumnDefinition("name", DataType.TEXT)
        schema.add_column(col)
        
        assert schema.get_column("name") == col
        assert schema.get_column("nonexistent") is None
    
    def test_validate_row_success(self):
        """Test successful row validation."""
        schema = TableSchema("users")
        schema.add_column(ColumnDefinition("id", DataType.INTEGER, is_primary=True))
        schema.add_column(ColumnDefinition("name", DataType.TEXT, is_nullable=False))
        schema.add_column(ColumnDefinition("age", DataType.INTEGER, is_nullable=True))
        
        row_data = {"id": 1, "name": "Alice", "age": 30}
        assert schema.validate_row(row_data) is True
    
    def test_validate_row_missing_required(self):
        """Test row validation with missing required field."""
        schema = TableSchema("users")
        schema.add_column(ColumnDefinition("id", DataType.INTEGER, is_primary=True))
        schema.add_column(ColumnDefinition("name", DataType.TEXT, is_nullable=False))
        
        row_data = {"id": 1}  # Missing required 'name'
        assert schema.validate_row(row_data) is False
    
    def test_validate_row_null_in_non_nullable(self):
        """Test row validation with null in non-nullable field."""
        schema = TableSchema("users")
        schema.add_column(ColumnDefinition("id", DataType.INTEGER, is_primary=True))
        schema.add_column(ColumnDefinition("name", DataType.TEXT, is_nullable=False))
        
        row_data = {"id": 1, "name": None}
        assert schema.validate_row(row_data) is False
    
    def test_validate_row_auto_increment_primary_key(self):
        """Test row validation with auto-increment primary key."""
        schema = TableSchema("users")
        schema.add_column(ColumnDefinition("id", DataType.INTEGER, is_primary=True))
        schema.add_column(ColumnDefinition("name", DataType.TEXT))
        
        # Missing primary key should be allowed for auto-increment
        row_data = {"name": "Alice"}
        assert schema.validate_row(row_data) is True
    
    def test_get_next_auto_increment(self):
        """Test auto-increment value generation."""
        schema = TableSchema("users")
        assert schema.get_next_auto_increment() == 1
        assert schema.get_next_auto_increment() == 2
        assert schema.get_next_auto_increment() == 3
    
    def test_table_schema_to_dict(self):
        """Test converting table schema to dictionary."""
        schema = TableSchema("users")
        schema.add_column(ColumnDefinition("id", DataType.INTEGER, is_primary=True))
        schema.add_column(ColumnDefinition("name", DataType.TEXT, max_length=50))
        
        result = schema.to_dict()
        
        assert result["table_name"] == "users"
        assert result["primary_key"] == "id"
        assert len(result["columns"]) == 2
        assert "id" in result["columns"]
        assert "name" in result["columns"]
    
    def test_table_schema_from_dict(self):
        """Test creating table schema from dictionary."""
        data = {
            'table_name': 'products',
            'columns': {
                'id': {
                    'name': 'id',
                    'data_type': 'INTEGER',
                    'is_primary': True,
                    'is_nullable': True,
                    'is_unique': False,
                    'default_value': None,
                    'max_length': None
                },
                'name': {
                    'name': 'name',
                    'data_type': 'TEXT',
                    'is_primary': False,
                    'is_nullable': False,
                    'is_unique': True,
                    'default_value': None,
                    'max_length': 100
                }
            },
            'primary_key': 'id',
            'foreign_keys': [],
            'indexes': {}
        }
        
        schema = TableSchema.from_dict(data)
        assert schema.table_name == 'products'
        assert schema.primary_key == 'id'
        assert len(schema.columns) == 2
        assert 'id' in schema.columns
        assert 'name' in schema.columns


class TestRow:
    """Test cases for Row class."""
    
    def test_row_creation(self):
        """Test basic row creation."""
        row = Row(id=1, name="Alice", age=30)
        assert row.id == 1
        assert row.name == "Alice"
        assert row.age == 30
    
    def test_row_dynamic_attribute_access(self):
        """Test dynamic attribute access."""
        row = Row(name="Bob", email="bob@example.com")
        assert row.name == "Bob"
        assert row.email == "bob@example.com"
        
        with pytest.raises(AttributeError):
            _ = row.nonexistent
    
    def test_row_dynamic_attribute_setting(self):
        """Test dynamic attribute setting."""
        row = Row()
        row.name = "Charlie"
        row.age = 25
        assert row.name == "Charlie"
        assert row.age == 25
    
    def test_row_to_dict(self):
        """Test converting row to dictionary."""
        row = Row(id=1, name="Alice", age=30)
        result = row.to_dict()
        expected = {"id": 1, "name": "Alice", "age": 30}
        assert result == expected
    
    def test_row_from_dict(self):
        """Test creating row from dictionary."""
        data = {"id": 2, "name": "Bob", "age": 25}
        row = Row.from_dict(data)
        assert row.id == 2
        assert row.name == "Bob"
        assert row.age == 25
    
    def test_row_equality(self):
        """Test row equality."""
        row1 = Row(id=1, name="Alice")
        row2 = Row(id=1, name="Alice")
        row3 = Row(id=2, name="Bob")
        
        assert row1 == row2
        assert row1 != row3
        assert row1 != "not a row"
    
    def test_row_repr(self):
        """Test row string representation."""
        row = Row(id=1, name="Alice")
        repr_str = repr(row)
        assert "Row" in repr_str
        assert "id" in repr_str
        assert "Alice" in repr_str
    
    def test_row_get_value(self):
        """Test getting column value."""
        row = Row(name="Alice", age=30)
        assert row.get_value("name") == "Alice"
        assert row.get_value("age") == 30
        assert row.get_value("nonexistent") is None
    
    def test_row_set_value(self):
        """Test setting column value."""
        row = Row()
        row.set_value("name", "Bob")
        row.set_value("age", 25)
        assert row.name == "Bob"
        assert row.age == 25
    
    def test_row_serialization_deserialization(self):
        """Test row serialization and deserialization."""
        # Create a simple schema
        schema = TableSchema("test")
        schema.add_column(ColumnDefinition("id", DataType.INTEGER))
        schema.add_column(ColumnDefinition("name", DataType.TEXT, max_length=50))
        
        # Create row
        original_row = Row(id=123, name="Test Name")
        
        # Serialize
        serialized = original_row.serialize(schema)
        assert isinstance(serialized, bytes)
        assert len(serialized) > 0
        
        # Deserialize
        deserialized_row = Row.deserialize(serialized, schema)
        assert deserialized_row.id == 123
        assert deserialized_row.name == "Test Name"
        assert original_row == deserialized_row
    
    def test_row_serialization_with_nulls(self):
        """Test row serialization with null values."""
        schema = TableSchema("test")
        schema.add_column(ColumnDefinition("id", DataType.INTEGER))
        schema.add_column(ColumnDefinition("name", DataType.TEXT, max_length=50))
        schema.add_column(ColumnDefinition("age", DataType.INTEGER))
        
        row = Row(id=1, name=None, age=25)
        serialized = row.serialize(schema)
        deserialized = Row.deserialize(serialized, schema)
        
        assert deserialized.id == 1
        assert deserialized.name is None  # Null text should be None
        assert deserialized.age == 25


class TestTransactionLog:
    """Test cases for TransactionLog."""
    
    def test_transaction_log_creation(self):
        """Test transaction log creation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            log_path = f.name
        
        try:
            log = TransactionLog(log_path)
            assert log.log_path == log_path
        finally:
            os.unlink(log_path)
    
    def test_write_record(self):
        """Test writing transaction log record."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            log_path = f.name
        
        try:
            log = TransactionLog(log_path)
            
            # Write a record
            log.write_record(
                transaction_id=1,
                operation="INSERT",
                table_name="users",
                row_data={"id": 1, "name": "Alice"}
            )
            
            # Verify file exists and has content
            assert os.path.exists(log_path)
            with open(log_path, 'r') as f:
                content = f.read()
                assert "INSERT" in content
                assert "users" in content
                assert "Alice" in content
        
        finally:
            os.unlink(log_path)
    
    def test_read_records(self):
        """Test reading transaction log records."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            log_path = f.name
        
        try:
            log = TransactionLog(log_path)
            
            # Write multiple records
            log.write_record(1, "INSERT", "users", {"id": 1, "name": "Alice"})
            log.write_record(2, "UPDATE", "users", {"id": 1, "name": "Bob"})
            log.write_record(1, "DELETE", "users", {"id": 1, "name": "Alice"})
            
            # Read all records
            records = log.read_records()
            assert len(records) == 3
            
            # Read specific transaction records
            tx1_records = log.read_records(transaction_id=1)
            assert len(tx1_records) == 2
            
            # Verify record structure
            for record in records:
                assert 'timestamp' in record
                assert 'transaction_id' in record
                assert 'operation' in record
                assert 'table_name' in record
                assert 'row_data' in record
        
        finally:
            os.unlink(log_path)
    
    def test_read_empty_log(self):
        """Test reading from empty/non-existent log file."""
        log = TransactionLog("/nonexistent/path/test.log")
        records = log.read_records()
        assert records == []
    
    def test_write_record_with_old_data(self):
        """Test writing record with old data for updates."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            log_path = f.name
        
        try:
            log = TransactionLog(log_path)
            
            log.write_record(
                transaction_id=1,
                operation="UPDATE",
                table_name="users",
                row_data={"id": 1, "name": "Updated"},
                old_data={"id": 1, "name": "Original"}
            )
            
            records = log.read_records()
            assert len(records) == 1
            assert records[0]['old_data'] == {"id": 1, "name": "Original"}
        
        finally:
            os.unlink(log_path)


class TestEnums:
    """Test cases for various enums."""
    
    def test_meta_command_result(self):
        """Test MetaCommandResult enum."""
        assert MetaCommandResult.SUCCESS.value == 0
        assert MetaCommandResult.UNRECOGNIZED_COMMAND.value == 1
    
    def test_prepare_result(self):
        """Test PrepareResult enum."""
        assert PrepareResult.SUCCESS.value == 0
        assert PrepareResult.NEGATIVE_ID.value == 1
        assert PrepareResult.STRING_TOO_LONG.value == 2
        assert PrepareResult.SYNTAX_ERROR.value == 3
        assert PrepareResult.UNRECOGNIZED_STATEMENT.value == 4
    
    def test_execute_result(self):
        """Test ExecuteResult enum."""
        assert ExecuteResult.SUCCESS.value == 0
        assert ExecuteResult.TABLE_FULL.value == 1
        assert ExecuteResult.DUPLICATE_KEY.value == 2
    
    def test_statement_type(self):
        """Test StatementType enum."""
        assert StatementType.INSERT.value == 0
        assert StatementType.SELECT.value == 1
        assert StatementType.UPDATE.value == 2
        assert StatementType.DELETE.value == 3
        assert StatementType.CREATE_TABLE.value == 4
        assert StatementType.DROP_TABLE.value == 5
        assert StatementType.ALTER_TABLE.value == 6
        assert StatementType.CREATE_INDEX.value == 7
        assert StatementType.DROP_INDEX.value == 8


class TestForeignKeyConstraint:
    """Test cases for ForeignKeyConstraint."""
    
    def test_foreign_key_creation(self):
        """Test foreign key constraint creation."""
        fk = ForeignKeyConstraint(
            column="user_id",
            ref_table="users",
            ref_column="id",
            on_delete="CASCADE",
            on_update="RESTRICT"
        )
        
        assert fk.column == "user_id"
        assert fk.ref_table == "users"
        assert fk.ref_column == "id"
        assert fk.on_delete == "CASCADE"
        assert fk.on_update == "RESTRICT"
    
    def test_foreign_key_defaults(self):
        """Test foreign key constraint defaults."""
        fk = ForeignKeyConstraint("user_id", "users", "id")
        
        assert fk.on_delete == "NO ACTION"
        assert fk.on_update == "NO ACTION"


class TestIndexDefinition:
    """Test cases for IndexDefinition."""
    
    def test_index_creation(self):
        """Test index definition creation."""
        index = IndexDefinition(
            name="idx_email",
            columns=["email"],
            is_unique=True
        )
        
        assert index.name == "idx_email"
        assert index.columns == ["email"]
        assert index.is_unique is True
    
    def test_index_defaults(self):
        """Test index definition defaults."""
        index = IndexDefinition("idx_name", ["first_name", "last_name"])
        
        assert index.is_unique is False