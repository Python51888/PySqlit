"""Unit tests for pysqlit/storage.py module."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

from pysqlit.storage import Pager
from pysqlit.constants import PAGE_SIZE, TABLE_MAX_PAGES


class TestPager:
    """Test cases for Pager class."""
    
    def test_pager_creation(self, temp_db_path):
        """Test pager creation."""
        pager = Pager(temp_db_path)
        assert pager.filename == temp_db_path
        assert pager.file_length == 0
        assert len(pager.pages) == TABLE_MAX_PAGES
        assert all(page is None for page in pager.pages)
        pager.close()
    
    def test_get_page_new_file(self, temp_db_path):
        """Test getting page from new file."""
        pager = Pager(temp_db_path)
        page = pager.get_page(0)
        assert isinstance(page, bytearray)
        assert len(page) == PAGE_SIZE
        assert all(b == 0 for b in page)
        pager.close()
    
    def test_get_page_existing_page(self, temp_db_path):
        """Test getting existing page."""
        pager = Pager(temp_db_path)
        page1 = pager.get_page(0)
        page2 = pager.get_page(0)
        assert page1 is page2  # Should return same instance
        pager.close()
    
    def test_get_page_multiple_pages(self, temp_db_path):
        """Test getting multiple pages."""
        pager = Pager(temp_db_path)
        page1 = pager.get_page(0)
        page2 = pager.get_page(1)
        page3 = pager.get_page(2)
        
        assert isinstance(page1, bytearray)
        assert isinstance(page2, bytearray)
        assert isinstance(page3, bytearray)
        assert len(page1) == PAGE_SIZE
        assert len(page2) == PAGE_SIZE
        assert len(page3) == PAGE_SIZE
        pager.close()
    
    def test_flush_all_pages_empty(self, temp_db_path):
        """Test flushing empty pager."""
        pager = Pager(temp_db_path)
        pager.flush_all_pages()  # Should not raise exception
        pager.close()
    
    def test_flush_all_pages_with_data(self, temp_db_path):
        """Test flushing pages with data."""
        pager = Pager(temp_db_path)
        page = pager.get_page(0)
        page[:5] = b"test"
        
        pager.flush_all_pages()
        assert os.path.exists(temp_db_path)
        pager.close()
    
    def test_get_page_count(self, temp_db_path):
        """Test getting page count."""
        pager = Pager(temp_db_path)
        assert pager.num_pages == 0
        
        # Accessing a page should increase page count
        pager.get_page(0)
        assert pager.num_pages == 1
        
        pager.get_page(2)
        assert pager.num_pages == 3  # Should be max accessed + 1
        pager.close()
    
    def test_file_length_calculation(self, temp_db_path):
        """Test file length calculation."""
        pager = Pager(temp_db_path)
        assert pager.file_length == 0
        
        # Access a page and flush
        pager.get_page(0)
        pager.flush_all_pages()
        
        # File should now have at least PAGE_SIZE bytes
        assert os.path.getsize(temp_db_path) >= PAGE_SIZE
        pager.close()
    
    def test_close_pager(self, temp_db_path):
        """Test closing pager."""
        pager = Pager(temp_db_path)
        pager.close()
        # Should not raise exception
    
    def test_pager_context_manager(self, temp_db_path):
        """Test pager as context manager."""
        with Pager(temp_db_path) as pager:
            page = pager.get_page(0)
            assert isinstance(page, bytearray)
            assert len(page) == PAGE_SIZE
        
        # Should be closed after context
    
    def test_page_data_persistence(self, temp_db_path):
        """Test that page data persists after flush."""
        test_data = b"persistent data"
        
        # Write data
        with Pager(temp_db_path) as pager:
            page = pager.get_page(0)
            page[:len(test_data)] = test_data
            pager.flush_all_pages()
        
        # Read data back
        with Pager(temp_db_path) as pager:
            page = pager.get_page(0)
            assert page[:len(test_data)] == test_data
    
    def test_multiple_page_operations(self, temp_db_path):
        """Test operations with multiple pages."""
        with Pager(temp_db_path) as pager:
            # Create multiple pages
            for i in range(5):
                page = pager.get_page(i)
                test_data = f"page{i}".encode()
                page[:len(test_data)] = test_data
            
            pager.flush_all_pages()
            
            # Verify all pages
            for i in range(5):
                page = pager.get_page(i)
                test_data = f"page{i}".encode()
                assert page[:len(test_data)] == test_data
    
    def test_page_boundary_conditions(self, temp_db_path):
        """Test page boundary conditions."""
        with Pager(temp_db_path) as pager:
            # Test valid page numbers
            page = pager.get_page(0)
            assert isinstance(page, bytearray)
            
            page = pager.get_page(TABLE_MAX_PAGES - 1)
            assert isinstance(page, bytearray)
            
            # Test invalid page number
            with pytest.raises(Exception):
                pager.get_page(TABLE_MAX_PAGES)
    
    def test_pager_initialization_with_existing_file(self, temp_db_path):
        """Test pager initialization with existing file."""
        # Create file with some data
        with open(temp_db_path, 'wb') as f:
            f.write(b'\x00' * (PAGE_SIZE * 3))
        
        pager = Pager(temp_db_path)
        assert pager.file_length == PAGE_SIZE * 3
        
        # Should be able to get existing pages
        page = pager.get_page(1)
        assert isinstance(page, bytearray)
        assert len(page) == PAGE_SIZE
        pager.close()
    
    def test_page_modification(self, temp_db_path):
        """Test page modification."""
        with Pager(temp_db_path) as pager:
            page = pager.get_page(0)
            
            # Modify page
            page[0:4] = b"test"
            assert page[0:4] == b"test"
            
            # Modify different parts
            page[100:105] = b"hello"
            assert page[100:105] == b"hello"
    
    def test_page_zeroing(self, temp_db_path):
        """Test that new pages are zero-initialized."""
        with Pager(temp_db_path) as pager:
            page = pager.get_page(5)  # Get a new page
            assert all(b == 0 for b in page)
    
    def test_file_operations(self, temp_db_path):
        """Test file operations."""
        # Test with non-existent file
        non_existent = temp_db_path + "_nonexistent"
        pager = Pager(non_existent)
        assert pager.file_length == 0
        assert pager.num_pages == 0
        pager.close()
        
        # Test with existing empty file
        with open(temp_db_path, 'wb') as f:
            pass
        
        pager = Pager(temp_db_path)
        assert pager.file_length == 0
        pager.close()