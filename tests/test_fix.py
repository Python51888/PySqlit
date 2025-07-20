import sys
from pysqlit.repl import REPL

# 创建 REPL 实例
repl = REPL()

# 执行测试 SQL
sql_statements = [
    "CREATE TABLE animal (id INTEGER PRIMARY KEY, name TEXT);",
    "INSERT INTO animal (name) VALUES ('Tom');",
    "SELECT * FROM animal;"
]

for sql in sql_statements:
    print(f"执行: {sql}")
    repl.process_statement(sql)

print("✅ 测试完成")