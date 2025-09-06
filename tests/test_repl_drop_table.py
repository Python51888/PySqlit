"""Test DROP TABLE error messages in REPL."""

import sys
import os
import io
import contextlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pysqlit.repl import EnhancedREPL
from pysqlit.database import EnhancedDatabase

def test_repl_drop_table_errors():
    """Test that REPL shows proper error messages for DROP TABLE operations."""
    
    # Create REPL with in-memory database
    repl = EnhancedREPL(":memory:")
    
    print("=== Testing REPL DROP TABLE Error Messages ===\n")
    
    # Capture stdout to check error messages
    captured_output = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured_output
    
    try:
        # Test 1: Drop non-existent table
        print("1. Testing drop non-existent table...")
        repl.process_statement("DROP TABLE nonexistent")
        output1 = captured_output.getvalue()
        captured_output.seek(0)
        captured_output.truncate(0)
        print(f"   Output: {output1.strip()}")
        # Print the actual output for debugging
        print(f"   Actual output: '{output1.strip()}'")
        
        # Test 2: Create table with data
        print("2. Creating table with data...")
        repl.process_statement("CREATE TABLE animal (id INTEGER PRIMARY KEY, name TEXT)")
        repl.process_statement("INSERT INTO animal (name) VALUES ('Tom')")
        repl.process_statement("INSERT INTO animal (name) VALUES ('Jerry')")
        captured_output.seek(0)
        captured_output.truncate(0)
        
        # Test 3: Drop table with data
        print("3. Testing drop table with data...")
        repl.process_statement("DROP TABLE animal")
        output3 = captured_output.getvalue()
        captured_output.seek(0)
        captured_output.truncate(0)
        print(f"   Output: {output3.strip()}")
        # Print the actual output for debugging
        print(f"   Actual output: '{output3.strip()}'")
        
        print("\nTest completed - check outputs above for correctness.")
        
    finally:
        sys.stdout = old_stdout
        repl.close()

if __name__ == "__main__":
    test_repl_drop_table_errors()