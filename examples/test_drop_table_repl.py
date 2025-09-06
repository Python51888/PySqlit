import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from pysqlit.repl import EnhancedREPL

def test_drop_table_repl():
    """Test DROP TABLE error messages in REPL."""
    # Create REPL with in-memory database
    repl = EnhancedREPL(":memory:")
    
    print("Testing DROP TABLE error messages...")
    
    # Test 1: Drop non-existent table
    print("\n1. Dropping non-existent table:")
    repl.process_statement("DROP TABLE nonexistent")
    
    # Test 2: Create table with data
    print("\n2. Creating table with data:")
    repl.process_statement("CREATE TABLE animal (id INTEGER PRIMARY KEY, name TEXT)")
    repl.process_statement("INSERT INTO animal (name) VALUES ('Tom')")
    repl.process_statement("INSERT INTO animal (name) VALUES ('Jerry')")
    
    # Test 3: Drop table with data
    print("\n3. Dropping table with data:")
    repl.process_statement("DROP TABLE animal")
    
    repl.close()

if __name__ == "__main__":
    test_drop_table_repl()