"""
DROP TABLE with data example.

This example demonstrates that DROP TABLE now works correctly
even when the table contains data.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pysqlit.database import EnhancedDatabase
from pysqlit.models import Row

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
    
    # Now drop the table with data
    print("\nDropping table 'users' (which contains data)...")
    db.drop_table("users")
    print("Table dropped successfully!")
    
    # Verify table is gone
    tables = db.list_tables()
    print(f"Remaining tables: {tables}")
    
    # Recreate the table
    print("\nRecreating table 'users'...")
    db.create_table(
        "users",
        {"id": "INTEGER", "name": "TEXT", "email": "TEXT"},
        primary_key="id"
    )
    
    # Verify new table is empty
    new_table = db.tables["users"]
    rows = new_table.select_all()
    print(f"New table contains {len(rows)} rows: {rows}")
    
    # Close database
    db.close()
    print("\nExample completed successfully!")

if __name__ == "__main__":
    main()