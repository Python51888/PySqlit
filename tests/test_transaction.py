"""Unit tests for pysqlit/transaction.py module."""

import pytest
import tempfile
import os

from pysqlit.transaction import TransactionManager, IsolationLevel


class TestIsolationLevel:
    """Test cases for IsolationLevel enum."""
    
    def test_isolation_level_values(self):
        """Test isolation level enum values."""
        assert IsolationLevel.READ_UNCOMMITTED.value == "READ_UNCOMMITTED"
        assert IsolationLevel.READ_COMMITTED.value == "READ_COMMITTED"
        assert IsolationLevel.REPEATABLE_READ.value == "REPEATABLE_READ"
        assert IsolationLevel.SERIALIZABLE.value == "SERIALIZABLE"


class TestTransactionManager:
    """Test cases for TransactionManager class."""
    
    def test_transaction_manager_creation(self, temp_db_path):
        """Test transaction manager creation."""
        from pysqlit.concurrent_storage import ConcurrentPager
        
        pager = ConcurrentPager(temp_db_path)
        manager = TransactionManager(pager)
        assert manager.pager == pager
        pager.close()
    
    def test_begin_transaction(self, temp_db_path):
        """Test beginning transaction."""
        from pysqlit.concurrent_storage import ConcurrentPager
        
        pager = ConcurrentPager(temp_db_path)
        manager = TransactionManager(pager)
        
        tx_id = manager.begin_transaction()
        assert isinstance(tx_id, int)
        assert tx_id > 0
        
        pager.close()
    
    def test_begin_transaction_with_isolation_level(self, temp_db_path):
        """Test beginning transaction with specific isolation level."""
        from pysqlit.concurrent_storage import ConcurrentPager
        
        pager = ConcurrentPager(temp_db_path)
        manager = TransactionManager(pager)
        
        tx_id = manager.begin_transaction(IsolationLevel.READ_COMMITTED)
        assert isinstance(tx_id, int)
        
        pager.close()
    
    def test_commit_transaction(self, temp_db_path):
        """Test committing transaction."""
        from pysqlit.concurrent_storage import ConcurrentPager
        
        pager = ConcurrentPager(temp_db_path)
        manager = TransactionManager(pager)
        
        tx_id = manager.begin_transaction()
        manager.commit_transaction(tx_id)
        
        pager.close()
    
    def test_rollback_transaction(self, temp_db_path):
        """Test rolling back transaction."""
        from pysqlit.concurrent_storage import ConcurrentPager
        
        pager = ConcurrentPager(temp_db_path)
        manager = TransactionManager(pager)
        
        tx_id = manager.begin_transaction()
        manager.rollback_transaction(tx_id)
        
        pager.close()
    
    def test_is_in_transaction(self, temp_db_path):
        """Test checking if in transaction."""
        from pysqlit.concurrent_storage import ConcurrentPager
        
        pager = ConcurrentPager(temp_db_path)
        manager = TransactionManager(pager)
        
        tx_id = manager.begin_transaction()
        assert manager.is_in_transaction(tx_id) is True
        
        manager.commit_transaction(tx_id)
        assert manager.is_in_transaction(tx_id) is False
        
        pager.close()
    
    def test_get_active_transaction_count(self, temp_db_path):
        """Test getting active transaction count."""
        from pysqlit.concurrent_storage import ConcurrentPager
        
        pager = ConcurrentPager(temp_db_path)
        manager = TransactionManager(pager)
        
        assert manager.get_active_transaction_count() == 0
        
        tx_id1 = manager.begin_transaction()
        assert manager.get_active_transaction_count() == 1
        
        tx_id2 = manager.begin_transaction()
        assert manager.get_active_transaction_count() == 2
        
        manager.commit_transaction(tx_id1)
        assert manager.get_active_transaction_count() == 1
        
        manager.rollback_transaction(tx_id2)
        assert manager.get_active_transaction_count() == 0
        
        pager.close()
    
    def test_multiple_transactions(self, temp_db_path):
        """Test multiple concurrent transactions."""
        from pysqlit.concurrent_storage import ConcurrentPager
        
        pager = ConcurrentPager(temp_db_path)
        manager = TransactionManager(pager)
        
        tx_ids = []
        for i in range(5):
            tx_id = manager.begin_transaction()
            tx_ids.append(tx_id)
        
        assert len(tx_ids) == 5
        assert len(set(tx_ids)) == 5  # All IDs should be unique
        
        for tx_id in tx_ids:
            manager.commit_transaction(tx_id)
        
        pager.close()
    
    def test_transaction_isolation_levels(self, temp_db_path):
        """Test different isolation levels."""
        from pysqlit.concurrent_storage import ConcurrentPager
        
        pager = ConcurrentPager(temp_db_path)
        manager = TransactionManager(pager)
        
        levels = [
            IsolationLevel.READ_UNCOMMITTED,
            IsolationLevel.READ_COMMITTED,
            IsolationLevel.REPEATABLE_READ,
            IsolationLevel.SERIALIZABLE
        ]
        
        for level in levels:
            tx_id = manager.begin_transaction(level)
            assert tx_id > 0
            manager.commit_transaction(tx_id)
        
        pager.close()