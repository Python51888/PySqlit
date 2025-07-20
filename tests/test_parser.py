"""Unit tests for pysqlit/parser.py module."""


from pysqlit.parser import (
    EnhancedSQLParser,
    InsertStatement,
    SelectStatement,
    UpdateStatement,
    DeleteStatement,
    CreateTableStatement,
    DropTableStatement,
    WhereCondition,
    PrepareResult
)
from pysqlit.models import DataType


class TestEnhancedSQLParser:
    """Test cases for EnhancedSQLParser."""
    
    def test_parse_insert_statement(self):
        """Test parsing INSERT statement."""
        # 测试标准格式
        sql = "INSERT INTO users (id, name, age) VALUES (1, 'Alice', 30)"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, InsertStatement)
        assert statement.table_name == "users"
        assert statement.columns == ["id", "name", "age"]
        assert statement.values == [1, "Alice", 30]
    
    def test_parse_insert_legacy_with_id(self):
        """Test parsing legacy INSERT with id."""
        sql = "INSERT 1 Alice alice@example.com"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, InsertStatement)
        assert statement.table_name == "users"
        assert statement.columns == ["id", "username", "email"]
        assert statement.values == [1, "Alice", "alice@example.com"]
    
    def test_parse_insert_legacy_auto_increment(self):
        """Test parsing legacy INSERT with auto-increment."""
        sql = "INSERT Alice alice@example.com"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, InsertStatement)
        assert statement.table_name == "users"
        assert statement.columns == ["username", "email"]
        assert statement.values == ["Alice", "alice@example.com"]
    
    def test_parse_insert_legacy_minimal(self):
        """Test parsing minimal legacy INSERT (only username)."""
        sql = "INSERT Alice"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, InsertStatement)
        assert statement.table_name == "users"
        assert statement.columns == ["username", "email"]
        assert statement.values == ["Alice", ""]
    
    def test_parse_insert_legacy_insufficient_args(self):
        """Test parsing legacy INSERT with insufficient arguments."""
        sql = "INSERT"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SYNTAX_ERROR
        assert statement is None
    
    def test_parse_select_statement(self):
        """Test parsing SELECT statement."""
        sql = "SELECT id, name FROM users"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, SelectStatement)
        assert statement.table_name == "users"
        assert statement.columns == ["id", "name"]
        assert statement.where_clause is None
    
    def test_parse_select_with_where(self):
        """Test parsing SELECT with WHERE clause."""
        sql = "SELECT * FROM users WHERE age > 25"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, SelectStatement)
        assert statement.table_name == "users"
        assert statement.columns == ["*"]
        assert statement.where_clause is not None
    
    def test_parse_update_statement(self):
        """Test parsing UPDATE statement."""
        sql = "UPDATE users SET name = 'Bob', age = 31 WHERE id = 1"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, UpdateStatement)
        assert statement.table_name == "users"
        assert statement.updates == {"name": "Bob", "age": 31}
        assert statement.where_clause is not None
    
    def test_parse_delete_statement(self):
        """Test parsing DELETE statement."""
        sql = "DELETE FROM users WHERE age < 18"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, DeleteStatement)
        assert statement.table_name == "users"
        assert statement.where_clause is not None
    
    def test_parse_create_table_statement(self):
        """Test parsing CREATE TABLE statement."""
        sql = "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, CreateTableStatement)
        assert statement.table_name == "users"
        column_names = [col[0] for col in statement.columns]
        assert "id" in column_names
        assert "name" in column_names
        assert "age" in column_names
        # Check data types
        for col in statement.columns:
            if col[0] == "id":
                assert col[1] == DataType.INTEGER
            if col[0] == "name":
                assert col[1] == DataType.TEXT
    
    def test_parse_drop_table_statement(self):
        """Test parsing DROP TABLE statement."""
        sql = "DROP TABLE users"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, DropTableStatement)
        assert statement.table_name == "users"
    
    def test_parse_invalid_syntax(self):
        """Test parsing invalid SQL syntax."""
        sql = "INVALID SQL SYNTAX"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.UNRECOGNIZED_STATEMENT
        assert statement is None
    
    def test_parse_empty_statement(self):
        """Test parsing empty statement."""
        sql = ""
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.UNRECOGNIZED_STATEMENT
        assert statement is None
    
    def test_parse_unsupported_statement(self):
        """Test parsing unsupported SQL statement."""
        sql = "ALTER TABLE users ADD COLUMN email TEXT"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.UNRECOGNIZED_STATEMENT
        assert statement is None
    
    def test_parse_case_insensitive(self):
        """Test case insensitive parsing."""
        sql = "insert into users (id, name) values (1, 'Alice')"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, InsertStatement)
        assert statement.table_name == "users"
    def test_parse_create_table_with_multiple_columns(self):
        """Test parsing CREATE TABLE with multiple columns and data types."""
        sql = "CREATE TABLE products (id INTEGER, name TEXT, price REAL, in_stock BOOLEAN)"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, CreateTableStatement)
        assert statement.table_name == "products"
        assert len(statement.columns) == 4
        # 检查列名和数据类型
        assert statement.columns['id'][0] == DataType.INTEGER
        assert statement.columns['name'][0] == DataType.TEXT
        assert statement.columns['price'][0] == DataType.REAL
        assert statement.columns['in_stock'][0] == DataType.BOOLEAN

    def test_parse_create_table_with_constraints(self):
        """Test parsing CREATE TABLE with column constraints."""
        sql = "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, age INTEGER NOT NULL)"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, CreateTableStatement)
        assert statement.table_name == "users"
        # 检查约束
        assert statement.columns['id'][1] == True   # PRIMARY KEY
        assert statement.columns['id'][2] == True   # AUTOINCREMENT
        assert statement.columns['username'][3] == True   # UNIQUE
        assert statement.columns['username'][4] == True   # NOT NULL
        assert statement.columns['age'][4] == True    # NOT NULL

    def test_parse_create_table_with_unique_not_null(self):
        """Test parsing CREATE TABLE with UNIQUE and NOT NULL constraints (fixed case)."""
        sql = "CREATE TABLE animal (id INTEGER PRIMARY KEY, name TEXT UNIQUE not null, age integer)"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, CreateTableStatement)
        assert statement.table_name == "animal"
        # 检查约束
        assert statement.columns['id'][1] == True    # PRIMARY KEY
        assert statement.columns['name'][3] == True   # UNIQUE
        assert statement.columns['name'][4] == True   # NOT NULL
        assert statement.columns['age'][4] == False   # NOT NULL 应为False

    def test_parse_create_table_with_mixed_constraints(self):
        """Test parsing CREATE TABLE with mixed constraints."""
        sql = "CREATE TABLE product (id INTEGER PRIMARY KEY, name TEXT UNIQUE, price REAL NOT NULL, in_stock BOOLEAN)"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, CreateTableStatement)
        assert statement.table_name == "product"
        # 检查约束
        assert statement.columns['id'][1] == True    # PRIMARY KEY
        assert statement.columns['name'][3] == True   # UNIQUE
        assert statement.columns['price'][4] == True  # NOT NULL
        assert statement.columns['in_stock'][4] == False # NOT NULL 应为False

    def test_parse_create_table_case_insensitive_constraints(self):
        """Test case-insensitive parsing of constraints."""
        sql = "CREATE TABLE animal (id INTEGER primary key, name TEXT unique NOT NULL, age integer)"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, CreateTableStatement)
        assert statement.table_name == "animal"
        # 检查约束
        assert statement.columns['id'][1] == True   # PRIMARY KEY
        assert statement.columns['name'][3] == True   # UNIQUE
        assert statement.columns['name'][4] == True   # NOT NULL

    def test_parse_create_table_empty_columns(self):
        """Test parsing CREATE TABLE with empty columns (should fail)."""
        sql = "CREATE TABLE users ()"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        assert result == PrepareResult.SYNTAX_ERROR

    def test_parse_create_table_case_insensitive(self):
        """Test case-insensitive parsing of CREATE TABLE."""
        sql = "cReAte tAbLe products (id iNtEgEr, name TeXt)"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        assert result == PrepareResult.SUCCESS
        assert statement.table_name == "products"

    def test_parse_create_table_missing_tablename(self):
        """Test parsing CREATE TABLE with missing table name."""
        sql = "CREATE TABLE (id INTEGER)"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        assert result == PrepareResult.SYNTAX_ERROR


class TestInsertStatement:
    """Test cases for InsertStatement."""
    
    def test_insert_statement_creation(self):
        """Test InsertStatement creation."""
        statement = InsertStatement(
            table_name="users",
            columns=["id", "name", "age"],
            values=[1, "Alice", 30]
        )
        
        assert statement.table_name == "users"
        assert statement.columns == ["id", "name", "age"]
        assert statement.values == [1, "Alice", 30]
    
    def test_insert_statement_to_row(self):
        """Test converting InsertStatement to Row."""
        statement = InsertStatement(
            table_name="users",
            columns=["id", "name", "age"],
            values=[1, "Alice", 30]
        )
        
        rows = statement.to_rows()
        assert len(rows) == 1
        row = rows[0]
        assert row.id == 1
        assert row.name == "Alice"
        assert row.age == 30
    
    def test_insert_statement_repr(self):
        """Test InsertStatement string representation."""
        statement = InsertStatement("users", ["id"], [1])
        repr_str = repr(statement)
        assert "InsertStatement" in repr_str
        assert "users" in repr_str


class TestSelectStatement:
    """Test cases for SelectStatement."""
    
    def test_select_statement_creation(self):
        """Test SelectStatement creation."""
        statement = SelectStatement(
            table_name="users",
            columns=["id", "name"],
            where_clause=None
        )
        
        assert statement.table_name == "users"
        assert statement.columns == ["id", "name"]
        assert statement.where_clause is None
    
    def test_select_statement_with_where(self):
        """Test SelectStatement with WHERE clause."""
        where_clause = WhereCondition("age", ">", 25)
        statement = SelectStatement(
            table_name="users",
            columns=["*"],
            where_clause=where_clause
        )
        
        assert statement.table_name == "users"
        assert statement.columns == ["*"]
        assert statement.where_clause == where_clause
    
    def test_select_statement_repr(self):
        """Test SelectStatement string representation."""
        statement = SelectStatement("users", ["id", "name"], None)
        repr_str = repr(statement)
        assert "SelectStatement" in repr_str
        assert "users" in repr_str


class TestUpdateStatement:
    """Test cases for UpdateStatement."""
    
    def test_update_statement_creation(self):
        """Test UpdateStatement creation."""
        statement = UpdateStatement(
            table_name="users",
            updates={"name": "Bob", "age": 31},
            where_clause=None
        )
        
        assert statement.table_name == "users"
        assert statement.updates == {"name": "Bob", "age": 31}
        assert statement.where_clause is None
    
    def test_update_statement_with_where(self):
        """Test UpdateStatement with WHERE clause."""
        where_clause = WhereCondition("id", "=", 1)
        statement = UpdateStatement(
            table_name="users",
            updates={"name": "Bob"},
            where_clause=where_clause
        )
        
        assert statement.table_name == "users"
        assert statement.updates == {"name": "Bob"}
        assert statement.where_clause == where_clause
    
    def test_update_statement_repr(self):
        """Test UpdateStatement string representation."""
        statement = UpdateStatement("users", {"name": "Bob"}, None)
        repr_str = repr(statement)
        assert "UpdateStatement" in repr_str
        assert "users" in repr_str


class TestDeleteStatement:
    """Test cases for DeleteStatement."""
    
    def test_delete_statement_creation(self):
        """Test DeleteStatement creation."""
        where_clause = WhereCondition("age", "<", 18)
        statement = DeleteStatement(
            table_name="users",
            where_clause=where_clause
        )
        
        assert statement.table_name == "users"
        assert statement.where_clause == where_clause
    
    def test_delete_statement_without_where(self):
        """Test DeleteStatement without WHERE clause."""
        statement = DeleteStatement(
            table_name="users",
            where_clause=None
        )
        
        assert statement.table_name == "users"
        assert statement.where_clause is None
    
    def test_delete_statement_repr(self):
        """Test DeleteStatement string representation."""
        statement = DeleteStatement("users", None)
        repr_str = repr(statement)
        assert "DeleteStatement" in repr_str
        assert "users" in repr_str


class TestCreateTableStatement:
    """Test cases for CreateTableStatement."""
    
    def test_create_table_statement_creation(self):
        """Test CreateTableStatement creation."""
        columns = {
            "id": DataType.INTEGER,
            "name": DataType.TEXT,
            "age": DataType.INTEGER
        }
        statement = CreateTableStatement(
            table_name="users",
            columns=columns
        )
        
        assert statement.table_name == "users"
        assert statement.columns == columns
    
    def test_create_table_statement_repr(self):
        """Test CreateTableStatement string representation."""
        statement = CreateTableStatement("users", {"id": DataType.INTEGER})
        repr_str = repr(statement)
        assert "CreateTableStatement" in repr_str
        assert "users" in repr_str


class TestDropTableStatement:
    """Test cases for DropTableStatement."""
    
    def test_drop_table_statement_creation(self):
        """Test DropTableStatement creation."""
        statement = DropTableStatement(table_name="users")
        assert statement.table_name == "users"
    
    def test_drop_table_statement_repr(self):
        """Test DropTableStatement string representation."""
        statement = DropTableStatement("users")
        repr_str = repr(statement)
        assert "DropTableStatement" in repr_str
        assert "users" in repr_str


class TestWhereCondition:
    """Test cases for WhereCondition."""
    
    def test_where_condition_creation(self):
        """Test WhereCondition creation."""
        condition = WhereCondition("age", ">", 25)
        assert condition.column == "age"
        assert condition.operator == ">"
        assert condition.value == 25
    
    def test_where_condition_evaluate(self):
        """Test WhereCondition evaluation."""
        condition = WhereCondition("age", ">", 25)
        
        # Mock row for evaluation
        class MockRow:
            def __init__(self, age):
                self.age = age
        
        row1 = MockRow(30)
        row2 = MockRow(20)
        
        # Test evaluation logic
        assert condition.evaluate(row1) is True
        assert condition.evaluate(row2) is False
    
    def test_where_condition_repr(self):
        """Test WhereCondition string representation."""
        condition = WhereCondition("name", "=", "Alice")
        # For string values, include quotes in the representation
        assert repr(condition) == "WhereCondition(column='name', operator='=', value='Alice')"
        
        # Test with integer value
        int_condition = WhereCondition("age", ">", 25)
        assert repr(int_condition) == "WhereCondition(column='age', operator='>', value=25)"


class TestParserEdgeCases:
    """Test edge cases for parser."""
    
    def test_parse_with_extra_whitespace(self):
        """Test parsing with extra whitespace."""
        sql = "  INSERT   INTO   users   (id, name)   VALUES   (1, 'Alice')  "
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, InsertStatement)
    
    def test_parse_with_newlines(self):
        """Test parsing with newlines."""
        sql = """
        SELECT id,
               name
        FROM users
        WHERE age > 25
        """
        result, statement = EnhancedSQLParser.parse_statement(sql)
    
        # Ensure parser handles newlines correctly
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, SelectStatement)
        assert statement.columns == ["id", "name"]
        assert statement.table_name == "users"
        assert statement.where_clause is not None
        assert statement.where_clause.column == "age"
        assert statement.where_clause.operator == ">"
        assert statement.where_clause.value == 25
        
        # Test more complex newline patterns
        sql = "SELECT id, email,\n username\nFROM\n users\nWHERE\n age > 30 \nAND name LIKE '%John%'"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, SelectStatement)
        assert statement.table_name == "users"
        assert statement.columns == ["id", "email", "username"]
        assert statement.where_clause is not None
    
    def test_parse_quoted_strings(self):
        """Test parsing with quoted strings."""
        sql = "INSERT INTO users (name) VALUES ('O''Brien')"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, InsertStatement)
    
    def test_parse_numeric_values(self):
        """Test parsing numeric values."""
        sql = "INSERT INTO products (id, price, quantity) VALUES (1, 29.99, 100)"
        result, statement = EnhancedSQLParser.parse_statement(sql)
        
        assert result == PrepareResult.SUCCESS
        assert isinstance(statement, InsertStatement)
        assert statement.values == [1, 29.99, 100]