"""Unit tests for main.py module."""

import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import pytest

from main import main


class TestMain:
    """Test cases for main module."""
    
    def test_main_with_database_argument(self):
        """Test main function with database file argument."""
        test_db = "test_database.db"
        
        with patch('sys.argv', ['main.py', test_db]):
            with patch('pysqlit.repl.EnhancedREPL') as mock_repl:
                mock_instance = MagicMock()
                mock_repl.return_value = mock_instance
                
                main()
                
                mock_repl.assert_called_once_with(os.path.abspath(test_db))
                mock_instance.run.assert_called_once()
    
    def test_main_without_database_argument(self):
        """Test main function without database file argument."""
        with patch('sys.argv', ['main.py']):
            with patch('pysqlit.repl.EnhancedREPL') as mock_repl:
                mock_instance = MagicMock()
                mock_repl.return_value = mock_instance
                
                main()
                
                # Should use default "test.db"
                expected_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'test.db')
                mock_repl.assert_called_once_with(os.path.abspath(expected_path))
                mock_instance.run.assert_called_once()
    
    def test_main_with_relative_path(self):
        """Test main function with relative database path."""
        relative_path = "data/mydb.db"
        
        with patch('sys.argv', ['main.py', relative_path]):
            with patch('pysqlit.repl.EnhancedREPL') as mock_repl:
                mock_instance = MagicMock()
                mock_repl.return_value = mock_instance
                
                main()
                
                expected_path = os.path.abspath(relative_path)
                mock_repl.assert_called_once_with(expected_path)
                mock_instance.run.assert_called_once()
    
    def test_main_with_absolute_path(self):
        """Test main function with absolute database path."""
        absolute_path = "/tmp/test.db"
        
        with patch('sys.argv', ['main.py', absolute_path]):
            with patch('pysqlit.repl.EnhancedREPL') as mock_repl:
                mock_instance = MagicMock()
                mock_repl.return_value = mock_instance
                
                main()
                
                mock_repl.assert_called_once_with(absolute_path)
                mock_instance.run.assert_called_once()
    
    def test_main_import_as_module(self):
        """Test that main can be imported without executing."""
        # This test ensures the module can be imported
        import main
        assert hasattr(main, 'main')
        assert callable(main.main)