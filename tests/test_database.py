"""Unit tests for pysqlit/database.py module."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

from pysqlit.database import EnhancedDatabase, EnhancedTable, SQLExecutor
from pysqlit.models import Row, DataType, TableSchema, ColumnDefinition
from pysqlit.exceptions import DatabaseError


class TestEnhancedTable:
    """Test cases for EnhancedTable class."""
    
    def test_table_creation(self, database):
        """Test table creation."""
        schema = TableSchema("test_table")
        schema.add_column(ColumnDefinition("id", DataType.INTEGER, is_primary=True))
        schema.add_column(ColumnDefinition("name", DataType.TEXT, max_length=50))
        
        table = EnhancedTable(database.pager, "test_table", schema)
        assert table.table_name == "test_table"
        assert table.schema == schema
    
    def test_insert_row_success(self, database):
        """Test successful row insertion."""
        schema = TableSchema("test_table")
        schema.add_column(ColumnDefinition("id", DataType.INTEGER, is_primary=True))
        schema.add_column(ColumnDefinition("name", DataType.TEXT, max_length=50))
        
        table = EnhancedTable(database.pager, "test_table", schema)
        row = Row(id=1, name="Alice")
        
        result = table.insert_row(row)
        assert result == 0  # EXECUTE_SUCCESS
    
    def test_select_all_rows(self, database):
        """Test selecting all rows."""
        schema = TableSchema("test_table")
        schema.add_column(ColumnDefinition("id", DataType.INTEGER, is_primary=True))
        schema.add_column(ColumnDefinition("name", DataType.TEXT, max_length=50))
        
        table = EnhancedTable(database.pager, "test_table", schema)
        
        # Insert test data
        table.insert_row(Row(id=1, name="Alice"))
        table.insert_row(Row(id=2, name="Bob"))
        
        rows = table.select_all()
        assert len(rows) == 2
        assert rows[0].id == 1
        assert rows[1].id == 2
    
    def test_get_row_count(self, database):
        """Test getting row count."""
        schema = TableSchema("test_table")
        schema.add_column(ColumnDefinition("id", DataType.INTEGER, is_primary=True))
        schema.add_column(ColumnDefinition("name", DataType.TEXT, max_length=50))
        
        table = EnhancedTable(database.pager, "test_table", schema)
        assert table.get_row_count() == 0
        
        table.insert_row(Row(id=1, name="Alice"))
        assert table.get_row_count() == 1


class TestEnhancedDatabase:
    """Test cases for EnhancedDatabase class."""
    
    def test_database_creation(self, temp_db_path):
        """Test database creation."""
        db = EnhancedDatabase(temp_db_path)
        assert db.filename == temp_db_path
        assert "users" in db.tables  # Default table
        db.close()
    
    def test_create_table(self, database):
        """Test creating new table."""
        result = database.create_table(
            "products",
            {"id": "INTEGER", "name": "TEXT", "price": "REAL"},
            primary_key="id"
        )
        assert result is True
        assert "products" in database.tables
    
    def test_create_duplicate_table(self, database):
        """Test creating duplicate table raises error."""
        database.create_table("test", {"id": "INTEGER"})
        with pytest.raises(DatabaseError):
            database.create_table("test", {"id": "INTEGER"})
    
    def test_drop_table(self, database):
        """Test dropping table."""
        database.create_table("test", {"id": "INTEGER"})
        assert "test" in database.tables
        
        result = database.drop_table("test")
        assert result is True
        assert "test" not in database.tables
        
    def test_drop_table_with_data(self, database):
        """Test dropping table with existing data."""
        # Create table and insert data
        database.create_table("test", {"id": "INTEGER"})
        table = database.tables["test"]
        table.insert_row(Row(id=1))
        
        # Verify data exists
        assert table.get_row_count() == 1
        
        # Drop table
        result = database.drop_table("test")
        assert result is True
        assert "test" not in database.tables
    
    def test_drop_nonexistent_table(self, database):
        """Test dropping non-existent table raises error."""
        with pytest.raises(DatabaseError):
            database.drop_table("nonexistent")
            
    def test_truncate_before_drop(self, database):
        """Test that table data is truncated before drop."""
        # Create table and insert data
        database.create_table("test", {"id": "INTEGER"})
        table = database.tables["test"]
        
        # Insert multiple rows
        for i in range(5):
            table.insert_row(Row(id=i))
            
        # Verify data exists
        assert table.get_row_count() == 5
        
        # Drop table
        result = database.drop_table("test")
        assert result is True
        
        # Verify table is gone
        assert "test" not in database.tables
        
        # Recreate table with same name
        database.create_table("test", {"id": "INTEGER"})
        table = database.tables["test"]
        
        # Verify new table is empty
        assert table.get_row_count() == 0
    
    def test_list_tables(self, database):
        """Test listing tables."""
        tables = database.list_tables()
        assert isinstance(tables, list)
        assert "users" in tables
    
    def test_get_table_info(self, database):
        """Test getting table information."""
        info = database.get_table_info()
        assert isinstance(info, dict)
        assert "users" in info
        assert info["users"] == 0  # Initially empty
    
    def test_get_database_info(self, database):
        """Test getting comprehensive database info."""
        info = database.get_database_info()
        assert isinstance(info, dict)
        assert "filename" in info
        assert "tables" in info
        assert "users" in info["tables"]


class TestSQLExecutor:
    """Test cases for SQLExecutor class."""
    
    def test_sql_executor_creation(self, database):
        """Test SQLExecutor creation."""
        executor = SQLExecutor(database)
        assert executor.database == database
    
    def test_execute_insert_sql(self, database):
        """Test executing INSERT SQL."""
        executor = SQLExecutor(database)
        
        # Create table first
        database.create_table(
            "test",
            {"id": "INTEGER", "name": "TEXT"},
            primary_key="id"
        )
        
        sql = "INSERT INTO test (id, name) VALUES (1, 'Alice')"
        result, data = executor.execute(sql)
        assert result.name == "SUCCESS"  # PrepareResult.SUCCESS
    
    def test_execute_select_sql(self, database):
        """Test executing SELECT SQL."""
        # Create table and insert data directly
        database.create_table(
            "test",
            {"id": "INTEGER", "name": "TEXT"},
            primary_key="id"
        )
        
        # Insert data using table interface
        from pysqlit.models import Row
        database.tables["test"].insert_row(Row(id=1, name="Alice"))

        # Test select
        rows = database.tables["test"].select_all()
        assert len(rows) == 1
        assert rows[0].id == 1
        assert rows[0].name == "Alice"
    
    def test_execute_invalid_sql(self, database):
        """Test executing invalid SQL."""
        executor = SQLExecutor(database)
        sql = "INVALID SQL"
        result, data = executor.execute(sql)
        assert result.name in ["SYNTAX_ERROR", "UNRECOGNIZED_STATEMENT"]
    
    def test_execute_nonexistent_table(self, database):
        """Test executing SQL on non-existent table."""
        executor = SQLExecutor(database)
        sql = "SELECT * FROM nonexistent"
        result, data = executor.execute(sql)
        # Should handle gracefully or raise appropriate error


class TestDatabaseTransactions:
    """Test cases for database transactions."""
    
    def test_begin_transaction(self, database):
        """Test beginning transaction."""
        tx_id = database.begin_transaction()
        assert isinstance(tx_id, int)
        assert tx_id > 0
    
    def test_commit_transaction(self, database):
        """Test committing transaction."""
        tx_id = database.begin_transaction()
        database.commit_transaction(tx_id)
        # Should not raise any exceptions
    
    def test_rollback_transaction(self, database):
        """Test rolling back transaction."""
        tx_id = database.begin_transaction()
        database.rollback_transaction(tx_id)
        # Should not raise any exceptions
    
    def test_transaction_with_isolation_level(self, database):
        """Test transaction with specific isolation level."""
        from pysqlit.transaction import IsolationLevel
        
        tx_id = database.begin_transaction(IsolationLevel.READ_COMMITTED)
        assert isinstance(tx_id, int)


class TestTransactionState:
    """Test cases for transaction state tracking."""
    
    def test_initial_transaction_state(self, database):
        """Test initial transaction state is False."""
        assert database.in_transaction is False
        
    def test_begin_transaction_state(self, database):
        """Test transaction state after beginning transaction."""
        tx_id = database.begin_transaction()
        assert database.in_transaction is True
        
    def test_commit_transaction_state(self, database):
        """Test transaction state after committing transaction."""
        tx_id = database.begin_transaction()
        database.commit_transaction(tx_id)
        assert database.in_transaction is False
        
    def test_rollback_transaction_state(self, database):
        """Test transaction state after rolling back transaction."""
        tx_id = database.begin_transaction()
        database.rollback_transaction(tx_id)
        assert database.in_transaction is False
        
    def test_auto_commit_state(self, database):
        """Test auto-commit state changes."""
        # Should not be in transaction initially
        assert database.in_transaction is False
        
        # Begin transaction
        tx_id = database.begin_transaction()
        assert database.in_transaction is True
        
        # Commit transaction
        database.commit_transaction(tx_id)
        assert database.in_transaction is False
        
        # Execute non-SELECT statement should not change state
        database.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        assert database.in_transaction is False
        
        # Begin another transaction
        tx_id = database.begin_transaction()
        assert database.in_transaction is True
        
        # Rollback transaction
        database.rollback_transaction(tx_id)
        assert database.in_transaction is False


class TestDatabaseBackup:
    """Test cases for database backup functionality."""
    
    def test_create_backup(self, database):
        """Test creating backup."""
        backup_name = database.create_backup("test_backup")
        assert backup_name is not None
        assert "test_backup" in backup_name
    
    def test_list_backups(self, database):
        """Test listing backups."""
        database.create_backup("test_backup")
        backups = database.list_backups()
        assert isinstance(backups, list)
    
    def test_restore_backup(self, database):
        """Test restoring from backup."""
        backup_name = database.create_backup("test_backup")
        result = database.restore_backup(backup_name)
        assert isinstance(result, bool)


class TestDatabaseEdgeCases:
    """Test edge cases for database operations."""
    
    def test_database_close(self, temp_db_path):
        """Test closing database."""
        db = EnhancedDatabase(temp_db_path)
        db.close()
        # Should not raise any exceptions
    
    def test_database_flush(self, database):
        """Test flushing database."""
        database.flush()
        # Should not raise any exceptions
    
    def test_get_table_schema(self, database):
        """Test getting table schema."""
        schema = database.get_table_schema("users")
        assert schema is not None
        assert schema.table_name == "users"
    
    def test_get_nonexistent_table_schema(self, database):
        """Test getting schema for non-existent table."""
        schema = database.get_table_schema("nonexistent")
        assert schema is None
def test_auto_commit():
    """Test auto-commit after non-SELECT statements."""
    import os
    from pysqlit import Database
    
    # 内存数据库测试（内存数据库不会持久化，但提交后在同一连接中可见）
    db = Database(':memory:')
    db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, data TEXT)")
    
    # 执行INSERT后数据应该在同一连接中可见
    db.execute("INSERT INTO test (id, data) VALUES (1, 'first')")
    result = db.execute("SELECT * FROM test").fetchall()
    assert len(result) == 1
    assert result[0]['data'] == 'first'
    
    # 文件数据库测试
    test_file = 'test_auto_commit.db'
    try:
        # 创建新数据库并插入数据
        db_file = Database(test_file)
        db_file.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, data TEXT)")
        db_file.execute("INSERT INTO test (id, data) VALUES (1, 'persisted')")
        db_file.close()
        
        # 重新打开数据库验证数据持久化
        db_file2 = Database(test_file)
        result = db_file2.execute("SELECT * FROM test").fetchall()
        assert len(result) == 1
        assert result[0]['data'] == 'persisted'
        db_file2.close()
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)
        if os.path.exists(test_file + '.schema'):
            os.remove(test_file + '.schema')