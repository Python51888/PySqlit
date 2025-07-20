import sys
sys.path.append(".")
from pysqlit import Database

# Create in-memory database for testing
db = Database(":memory:")

# Create table and insert data
db.execute("CREATE TABLE animal (id INTEGER PRIMARY KEY, name TEXT)")
db.execute("INSERT INTO animal (name) VALUES ('Tom')")
db.execute("INSERT INTO animal (name) VALUES ('Jerry')")
db.execute("INSERT INTO animal (name) VALUES ('HaHa')")
db.execute("INSERT INTO animal (name) VALUES ('WangWang')")

# Test DELETE operation
print("Before DELETE:")
result = db.execute("SELECT id, name FROM animal")
for row in result:
    print(f"{row[0]} | {row[1]}")

print("\nDeleting id=3...")
db.execute("DELETE FROM animal WHERE id = 3")

print("\nAfter DELETE:")
result = db.execute("SELECT id, name FROM animal")
for row in result:
    print(f"{row[0]} | {row[1]}")

# Test DROP TABLE operation
print("\nDropping table...")
db.execute("DROP TABLE animal")

# Verify table is gone
try:
    db.execute("SELECT * FROM animal")
    print("Table still exists!")
except Exception as e:
    print(f"Table dropped successfully! Error when accessing: {e}")