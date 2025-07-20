"""Unit tests for pysqlit/repl.py module."""

import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

from pysqlit.repl import EnhancedREPL


class TestEnhancedREPL:
    """Test cases for EnhancedREPL class."""
    
    def test_repl_creation(self, temp_db_path):
        """Test REPL creation."""
        repl = EnhancedREPL(temp_db_path)
        assert repl.database.filename == temp_db_path
        repl.close()
    
    def test_repl_close(self, temp_db_path):
        """Test REPL close."""
        repl = EnhancedREPL(temp_db_path)
        repl.close()
        # Should not raise exception
    
    def test_repl_run_with_exit(self, temp_db_path):
        """Test REPL run with exit command."""
        repl = EnhancedREPL(temp_db_path)
        
        with patch('builtins.input', side_effect=['.exit']):
            repl.run()
        
        repl.close()
    
    def test_repl_help_command(self, temp_db_path):
        """Test REPL help command."""
        repl = EnhancedREPL(temp_db_path)
        
        with patch('builtins.input', side_effect=['.help', '.exit']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                repl.run()
                output = mock_stdout.getvalue()
                assert "help" in output.lower()
        
        repl.close()
    
    def test_repl_tables_command(self, temp_db_path):
        """Test REPL tables command."""
        repl = EnhancedREPL(temp_db_path)
        
        with patch('builtins.input', side_effect=['.tables', '.exit']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                repl.run()
                output = mock_stdout.getvalue()
                assert "users" in output
        
        repl.close()
    
    def test_repl_database_info_command(self, temp_db_path):
        """Test REPL database info command."""
        repl = EnhancedREPL(temp_db_path)
        
        with patch('builtins.input', side_effect=['.dbinfo', '.exit']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                repl.run()
                output = mock_stdout.getvalue()
                assert "Database" in output
        
        repl.close()
    
    def test_repl_invalid_command(self, temp_db_path):
        """Test REPL invalid command."""
        repl = EnhancedREPL(temp_db_path)
        
        with patch('builtins.input', side_effect=['.invalid', '.exit']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                repl.run()
                output = mock_stdout.getvalue()
                assert "Unrecognized" in output or "invalid" in output.lower()
        
        repl.close()
    
    def test_repl_sql_insert(self, temp_db_path):
        """Test REPL SQL INSERT command."""
        repl = EnhancedREPL(temp_db_path)
        
        with patch('builtins.input', side_effect=[
            "INSERT INTO users (id, username, email) VALUES (1, 'Alice', 'alice@example.com')",
            ".exit"
        ]):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                repl.run()
                output = mock_stdout.getvalue()
                # Should handle the SQL command
        
        repl.close()
    
    def test_repl_sql_select(self, temp_db_path):
        """Test REPL SQL SELECT command."""
        repl = EnhancedREPL(temp_db_path)
        
        with patch('builtins.input', side_effect=[
            "SELECT * FROM users",
            ".exit"
        ]):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                repl.run()
                output = mock_stdout.getvalue()
                # Should handle the SQL command
        
        repl.close()
    
    def test_repl_empty_input(self, temp_db_path):
        """Test REPL empty input."""
        repl = EnhancedREPL(temp_db_path)
        
        with patch('builtins.input', side_effect=['', '.exit']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                repl.run()
                output = mock_stdout.getvalue()
                # Should handle empty input gracefully
        
        repl.close()
    
    def test_repl_whitespace_input(self, temp_db_path):
        """Test REPL whitespace input."""
        repl = EnhancedREPL(temp_db_path)
        
        with patch('builtins.input', side_effect=['   ', '.exit']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                repl.run()
                output = mock_stdout.getvalue()
                # Should handle whitespace input gracefully
        
        repl.close()
    
    def test_repl_meta_command_case_insensitive(self, temp_db_path):
        """Test REPL meta command case insensitivity."""
        repl = EnhancedREPL(temp_db_path)
        
        with patch('builtins.input', side_effect=['.HELP', '.EXIT']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                repl.run()
                output = mock_stdout.getvalue()
                assert "help" in output.lower()
        
        repl.close()
    
    def test_repl_sql_syntax_error(self, temp_db_path):
        """Test REPL SQL syntax error handling."""
        repl = EnhancedREPL(temp_db_path)
        
        with patch('builtins.input', side_effect=[
            "INVALID SQL SYNTAX",
            ".exit"
        ]):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                repl.run()
                output = mock_stdout.getvalue()
                # Should handle syntax error gracefully
        
        repl.close()
    
    def test_repl_keyboard_interrupt(self, temp_db_path):
        """Test REPL keyboard interrupt handling."""
        repl = EnhancedREPL(temp_db_path)
        
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                repl.run()
                output = mock_stdout.getvalue()
                # Should handle keyboard interrupt
        
        repl.close()
    
    def test_repl_eof_handling(self, temp_db_path):
        """Test REPL EOF handling."""
        repl = EnhancedREPL(temp_db_path)
        
        with patch('builtins.input', side_effect=EOFError):
            repl.run()
        
    def test_repl_alias_column_display(self, temp_db_path):
        """Test REPL correctly displays column aliases."""
        repl = EnhancedREPL(temp_db_path)
        
        # Create table and insert data
        with patch('builtins.input', side_effect=[
            "CREATE TABLE animal (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)",
            "INSERT INTO animal (id, name, age) VALUES (100, 'Tom', 20)",
            "SELECT name, age as nianling FROM animal",
            ".exit"
        ]):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                repl.run()
                output = mock_stdout.getvalue()
                # Verify column headers
                assert "name | nianling" in output
                # Verify data row
                assert "Tom | 20" in output
        
        repl.close()