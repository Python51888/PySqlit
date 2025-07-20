import os
import unittest
from pysqlit.database import EnhancedDatabase

class TestDelete(unittest.TestCase):
    def setUp(self):
        self.db = EnhancedDatabase('test.db')
        self.db.execute('CREATE TABLE animal (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)')
        self.db.execute("INSERT INTO animal (name, age) VALUES ('Tom', 20)")
        self.db.execute("INSERT INTO animal (name, age) VALUES ('Jerry', 20)")
        self.db.execute("INSERT INTO animal (name, age) VALUES ('Spike', NULL)")

    def tearDown(self):
        os.remove('test.db')

    def test_unconditional_delete(self):
        result = self.db.execute('DELETE FROM animal')
        self.assertEqual(result, 3)
        
        rows = self.db.execute('SELECT * FROM animal')
        self.assertEqual(len(rows), 0)

    def test_conditional_delete(self):
        result = self.db.execute("DELETE FROM animal WHERE age = 20")
        self.assertEqual(result, 2)
        
        rows = self.db.execute('SELECT * FROM animal')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].name, 'Spike')

if __name__ == '__main__':
    unittest.main()