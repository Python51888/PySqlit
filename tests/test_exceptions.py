"""Unit tests for pysqlit/exceptions.py module."""

import pytest
from pysqlit.exceptions import DatabaseError, TransactionError


class TestDatabaseError:
    """Test cases for DatabaseError exception."""
    
    def test_database_error_creation(self):
        """Test basic DatabaseError creation."""
        error = DatabaseError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_database_error_with_cause(self):
        """Test DatabaseError with underlying cause."""
        cause = ValueError("Underlying error")
        error = DatabaseError("Database error")
        assert "Database error" in str(error)
        assert error.__cause__ is None  # Standard Exception doesn't store cause this way
    
    def test_database_error_inheritance(self):
        """Test DatabaseError inheritance."""
        error = DatabaseError("test")
        assert isinstance(error, Exception)
        assert type(error).__name__ == "DatabaseError"


class TestTransactionError:
    """Test cases for TransactionError exception."""
    
    def test_transaction_error_creation(self):
        """Test basic TransactionError creation."""
        error = TransactionError("Transaction failed")
        assert str(error) == "Transaction failed"
        assert isinstance(error, DatabaseError)
    
    def test_transaction_error_inheritance(self):
        """Test TransactionError inheritance."""
        error = TransactionError("test")
        assert isinstance(error, TransactionError)
        assert isinstance(error, DatabaseError)
        assert isinstance(error, Exception)
    
    def test_transaction_error_with_details(self):
        """Test TransactionError with transaction details."""
        error = TransactionError("Transaction 123 failed due to deadlock")
        assert "Transaction 123" in str(error)
        assert "deadlock" in str(error)


class TestExceptionUsage:
    """Test cases for exception usage patterns."""
    
    def test_database_error_raising(self):
        """Test raising DatabaseError."""
        with pytest.raises(DatabaseError) as exc_info:
            raise DatabaseError("Database connection failed")
        
        assert str(exc_info.value) == "Database connection failed"
    
    def test_transaction_error_raising(self):
        """Test raising TransactionError."""
        with pytest.raises(TransactionError) as exc_info:
            raise TransactionError("Transaction rollback failed")
        
        assert str(exc_info.value) == "Transaction rollback failed"
        assert isinstance(exc_info.value, DatabaseError)
    
    def test_exception_catching(self):
        """Test catching specific exceptions."""
        try:
            raise DatabaseError("Test error")
        except DatabaseError as e:
            assert str(e) == "Test error"
        
        try:
            raise TransactionError("Test transaction error")
        except TransactionError as e:
            assert str(e) == "Test transaction error"
        
        # Test catching DatabaseError also catches TransactionError
        try:
            raise TransactionError("Test transaction error")
        except DatabaseError as e:
            assert str(e) == "Test transaction error"
    
    def test_exception_with_formatting(self):
        """Test exception with formatted messages."""
        table_name = "users"
        error = DatabaseError(f"Table {table_name} does not exist")
        assert str(error) == "Table users does not exist"
        
        tx_id = 123
        error = TransactionError(f"Transaction {tx_id} timed out")
        assert str(error) == "Transaction 123 timed out"