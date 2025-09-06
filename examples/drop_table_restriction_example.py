"""
DROP TABLE restriction example.

This example demonstrates that DROP TABLE now correctly fails
when the table contains data, requiring the user to delete
the data first.
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
    
    # Create a table
    print("Creating table 'users'...")
    db.create_table(
        "users",
        {"id": "INTEGER", "name": "TEXT", "email": "TEXT"},
        primary_key="id"
    )
    
    # Insert some data
    print("Inserting data into 'users' table...")
    table = db.tables["users"]
    table.insert_row(Row(id=1, name="Alice", email="alice@example.com"))
    table.insert_row(Row(id=2, name="Bob", email="bob@example.com"))
    table.insert_row(Row(id=3, name="Charlie", email="charlie@example.com"))
    
    # Verify data exists
    rows = table.select_all()
    print(f"Table contains {len(rows)} rows:")
    for row in rows:
        print(f"  {row}")
    
    # Try to drop the table with data (should fail)
    print("\nTrying to drop table 'users' (which contains data)...")
    try:
        db.drop_table("users")
        print("ERROR: Table was dropped successfully, but it should have failed!")
    except DatabaseError as e:
        print(f"Expected error occurred: {e}")
        print("This is the correct behavior - table with data cannot be dropped")
    
    # Verify table still exists
    tables = db.list_tables()
    print(f"\nCurrent tables: {tables}")
    if "users" in tables:
        print("Table 'users' still exists (as expected)")
    else:
        print("ERROR: Table 'users' was incorrectly dropped")
        return
    
    # Delete all data from the table
    print("\nDeleting all data from 'users' table...")
    deleted_count = table.delete_rows()
    print(f"Deleted {deleted_count} rows")
    
    # Verify table is now empty
    rows = table.select_all()
    print(f"Table now contains {len(rows)} rows: {rows}")
    
    # Now drop the empty table (should succeed)
    print("\nDropping empty table 'users'...")
    try:
        db.drop_table("users")
        print("Table dropped successfully!")
    except DatabaseError as e:
        print(f"Unexpected error: {e}")
        return
    
    # Verify table is gone
    tables = db.list_tables()
    print(f"\nCurrent tables: {tables}")
    if "users" not in tables:
        print("Table 'users' was correctly dropped")
    else:
        print("ERROR: Table 'users' still exists")
    
    # Close database
    db.close()
    print("\nExample completed successfully!")

if __name__ == "__main__":
    main()