"""
DROP TABLE error messages example.

This example demonstrates the improved error messages for DROP TABLE operations:
1. When trying to drop a non-existent table
2. When trying to drop a table that contains data
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pysqlit.database import EnhancedDatabase
from pysqlit.models import Row
from pysqlit.exceptions import DatabaseError

def main():
    # Create an in-memory database
    db = EnhancedDatabase(":memory:")
    
    print("=== DROP TABLE Error Messages Example ===\n")
    
    # Try to drop a non-existent table
    print("1. Trying to drop a non-existent table...")
    try:
        db.drop_table("nonexistent_table")
        print("ERROR: This should have failed!")
    except DatabaseError as e:
        print(f"   Expected error: {e}")
    
    # Create a table with data
    print("\n2. Creating a table with data...")
    db.create_table(
        "users",
        {"id": "INTEGER", "name": "TEXT", "email": "TEXT"},
        primary_key="id"
    )
    
    # Insert some data
    table = db.tables["users"]
    table.insert_row(Row(id=1, name="Alice", email="alice@example.com"))
    table.insert_row(Row(id=2, name="Bob", email="bob@example.com"))
    
    print(f"   Table 'users' created with {table.get_row_count()} rows")
    
    # Try to drop the table with data
    print("\n3. Trying to drop table with data...")
    try:
        db.drop_table("users")
        print("ERROR: This should have failed!")
    except DatabaseError as e:
        print(f"   Expected error: {e}")
    
    # Delete all data
    print("\n4. Deleting all data from the table...")
    deleted_count = table.delete_rows()
    print(f"   Deleted {deleted_count} rows")
    
    # Now drop the empty table
    print("\n5. Dropping the now-empty table...")
    try:
        db.drop_table("users")
        print("   Table dropped successfully!")
    except DatabaseError as e:
        print(f"   Unexpected error: {e}")
    
    # Verify table is gone
    tables = db.list_tables()
    print(f"\n6. Current tables: {tables}")
    
    # Close database
    db.close()
    print("\nExample completed successfully!")

if __name__ == "__main__":
    main()