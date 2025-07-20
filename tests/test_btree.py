"""Unit tests for pysqlit/btree.py module."""

import pytest
import tempfile
import os

from pysqlit.btree import EnhancedBTree
from pysqlit.storage import Pager


class TestEnhancedBTree:
    """Test cases for EnhancedBTree class."""
    
    def test_btree_creation(self, temp_db_path):
        """Test BTree creation."""
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            assert btree.pager == pager
    
    def test_insert_single_key(self, temp_db_path):
        """Test inserting single key-value pair."""
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            result = btree.insert(1, b"value1")
            assert result is True
    
    def test_insert_multiple_keys(self, temp_db_path):
        """Test inserting multiple key-value pairs."""
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            
            keys_values = [(1, b"one"), (2, b"two"), (3, b"three")]
            for key, value in keys_values:
                result = btree.insert(key, value)
                assert result is True
    
    def test_select_single_key(self, temp_db_path):
        """Test selecting single key."""
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            btree.insert(1, b"value1")
            
            result = btree.select(1)
            assert result == b"value1"
    
    def test_select_nonexistent_key(self, temp_db_path):
        """Test selecting non-existent key."""
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            result = btree.select(999)
            assert result is None
    
    def test_update_existing_key(self, temp_db_path):
        """Test updating existing key."""
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            btree.insert(1, b"original")
            btree.update(1, b"updated")
            
            result = btree.select(1)
            assert result == b"updated"
    
    def test_delete_key(self, temp_db_path):
        """Test deleting key."""
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            btree.insert(1, b"value1")
            
            result = btree.delete(1)
            assert result is True
            
            # Verify deletion
            assert btree.select(1) is None
    
    def test_delete_nonexistent_key(self, temp_db_path):
        """Test deleting non-existent key."""
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            result = btree.delete(999)
            assert result is False
    
    def test_select_all_empty(self, temp_db_path):
        """Test selecting all from empty tree."""
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            results = btree.select_all()
            assert results == []
    
    def test_select_all_multiple_keys(self, temp_db_path):
        """Test selecting all key-value pairs."""
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            
            test_data = [(3, b"three"), (1, b"one"), (2, b"two")]
            for key, value in test_data:
                btree.insert(key, value)
            
            results = btree.select_all()
            assert len(results) == 3
            
            # Results should be sorted by key
            keys = [k for k, v in results]
            assert keys == [1, 2, 3]
    
    def test_insert_duplicate_key(self, temp_db_path):
        """Test inserting duplicate key."""
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            btree.insert(1, b"first")
            
            # Inserting duplicate should return False
            result = btree.insert(1, b"second")
            assert result is False
    
    def test_large_number_of_keys(self, temp_db_path):
        """Test inserting large number of keys."""
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            
            num_keys = 1000
            for i in range(num_keys):
                result = btree.insert(i, f"value{i}".encode())
                assert result is True
            
            # Verify all keys are present
            results = btree.select_all()
            assert len(results) == num_keys
    
    def test_negative_keys(self, temp_db_path):
        """Test inserting negative keys."""
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            
            keys = [-3, -1, 0, 1, 3]
            for key in keys:
                result = btree.insert(key, f"value{key}".encode())
                assert result is True
            
            results = btree.select_all()
            assert len(results) == 5
    
    def test_string_keys(self, temp_db_path):
        """Test inserting string keys."""
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            
            keys = ["apple", "banana", "cherry"]
            for key in keys:
                result = btree.insert(key, f"value_{key}".encode())
                assert result is True
            
            results = btree.select_all()
            assert len(results) == 3
    
    def test_mixed_data_types(self, temp_db_path):
        """Test inserting mixed data types as values."""
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            
            test_data = [
                (1, b"string"),
                (2, b"12345"),
                (3, b"\x00\x01\x02\x03"),
                (4, b""),
            ]
            
            for key, value in test_data:
                result = btree.insert(key, value)
                assert result is True
            
            results = btree.select_all()
            assert len(results) == 4
    
    def test_btree_persistence(self, temp_db_path):
        """Test BTree data persistence across instances."""
        # Insert data
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            btree.insert(1, b"persistent")
            btree.insert(2, b"data")
        
        # Read data in new instance
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            assert btree.select(1) == b"persistent"
            assert btree.select(2) == b"data"
    
    def test_update_nonexistent_key(self, temp_db_path):
        """Test updating non-existent key."""
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            result = btree.update(999, b"new_value")
            assert result is False
    
    def test_edge_case_keys(self, temp_db_path):
        """Test edge case keys."""
        with Pager(temp_db_path) as pager:
            btree = EnhancedBTree(pager)
            
            edge_keys = [0, 1, -1, 999999, -999999]
            for key in edge_keys:
                result = btree.insert(key, f"value{key}".encode())
                assert result is True
            
            results = btree.select_all()
            assert len(results) == len(edge_keys)