# PySQLit API 参考文档

## 🎯 概述

本文档提供了 PySQLit 的完整 API 参考，包括所有公共类、方法、异常和配置选项。API 设计遵循 Python 最佳实践，提供类型提示和详细的文档字符串。

## 📋 目录

- [核心类](#核心类)
- [数据库管理](#数据库管理)
- [表操作](#表操作)
- [事务管理](#事务管理)
- [备份恢复](#备份恢复)
- [异常处理](#异常处理)
- [配置选项](#配置选项)
- [工具类](#工具类)

## 🏗️ 核心类

### EnhancedDatabase
主数据库类，提供完整的数据库操作接口。

```python
from pysqlit.database import EnhancedDatabase

# 创建数据库连接
db = EnhancedDatabase("myapp.db")
# 或内存数据库
db = EnhancedDatabase(":memory:")
```

#### 构造函数
```python
EnhancedDatabase(
    filename: str,
    page_size: int = 4096,
    cache_size: int = 100,
    timeout: float = 5.0,
    isolation_level: IsolationLevel = IsolationLevel.REPEATABLE_READ
) -> None
```

**参数说明**:
- `filename`: 数据库文件路径，":memory:" 表示内存数据库
- `page_size`: 页大小，必须是512的倍数
- `cache_size`: 页缓存大小
- `timeout`: 锁等待超时时间（秒）
- `isolation_level`: 事务隔离级别

#### 核心方法

##### 基本操作
```python
# 执行SQL语句
result = db.execute(
    "SELECT * FROM users WHERE age > ?",
    (25,)
)

# 执行多个语句
db.executemany(
    "INSERT INTO users (name, email) VALUES (?, ?)",
    [("Alice", "alice@example.com"), ("Bob", "bob@example.com")]
)

# 执行脚本
db.executescript("""
    CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);
    INSERT INTO users (name) VALUES ('Charlie');
""")
```

##### 事务管理
```python
# 手动事务
tx_id = db.begin_transaction()
try:
    db.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
    db.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 2")
    db.commit_transaction(tx_id)
except Exception as e:
    db.rollback_transaction(tx_id)
    raise

# 上下文管理器
with db.transaction() as tx:
    db.execute("INSERT INTO users VALUES (?, ?)", (1, "Alice"))
    db.execute("INSERT INTO users VALUES (?, ?)", (2, "Bob"))
```

##### 表管理
```python
# 创建表
db.create_table("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "username": "TEXT UNIQUE NOT NULL",
    "email": "TEXT UNIQUE NOT NULL",
    "age": "INTEGER CHECK(age > 0)",
    "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
})

# 删除表
db.drop_table("users")

# 获取表信息
tables = db.list_tables()
schema = db.get_table_schema("users")
```

##### 备份恢复
```python
# 创建备份
backup_path = db.create_backup("daily_backup")
print(f"备份已创建: {backup_path}")

# 列出备份
backups = db.list_backups()
for backup in backups:
    print(f"{backup['name']} - {backup['created']}")

# 恢复备份
db.restore_backup("daily_backup")

# 删除备份
db.delete_backup("old_backup")
```

### EnhancedTable
表操作类，提供面向对象的表操作接口。

```python
from pysqlit.database import EnhancedTable

# 获取表实例
table = db.get_table("users")
```

#### 方法

##### 数据操作
```python
# 插入数据
row_id = table.insert_row({
    "username": "alice",
    "email": "alice@example.com",
    "age": 25
})

# 查询数据
rows = table.select_all()
rows = table.select_with_condition(
    WhereCondition("age", ">", 18)
)

# 更新数据
updated = table.update_rows(
    {"age": 26},
    WhereCondition("username", "=", "alice")
)

# 删除数据
deleted = table.delete_rows(
    WhereCondition("age", "<", 18)
)
```

##### 模式操作
```python
# 添加列
table.add_column("phone", "TEXT")

# 创建索引
table.create_index("idx_username", ["username"], unique=True)

# 删除索引
table.drop_index("idx_username")
```

### TransactionManager
事务管理器，提供ACID事务支持。

```python
from pysqlit.transaction import TransactionManager, IsolationLevel

# 获取事务管理器
tx_manager = db.transaction_manager

# 开始事务
tx_id = tx_manager.begin_transaction(
    isolation_level=IsolationLevel.SERIALIZABLE
)

# 提交事务
tx_manager.commit_transaction(tx_id)

# 回滚事务
tx_manager.rollback_transaction(tx_id)
```

#### 事务隔离级别
```python
class IsolationLevel(Enum):
    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"
```

### BackupManager
备份管理器，提供高级备份功能。

```python
from pysqlit.backup import BackupManager

# 创建备份管理器
backup_mgr = BackupManager("myapp.db")

# 创建备份
backup_name = backup_mgr.create_backup("manual_backup")

# 自动备份
backup_thread = backup_mgr.auto_backup(interval_hours=24)

# 验证备份
is_valid = backup_mgr.validate_backup("manual_backup")
```

## 🔧 数据模型

### Row
行数据模型，提供字典式访问。

```python
from pysqlit.models import Row

# 创建行
row = Row(
    id=1,
    username="alice",
    email="alice@example.com",
    age=25
)

# 访问数据
print(row["username"])  # "alice"
print(row.username)     # "alice"

# 转换为字典
data = row.to_dict()
```

### TableSchema
表模式定义。

```python
from pysqlit.models import TableSchema, ColumnDefinition, DataType

# 创建表模式
schema = TableSchema("users")
schema.add_column(ColumnDefinition(
    name="id",
    data_type=DataType.INTEGER,
    primary_key=True,
    auto_increment=True
))
schema.add_column(ColumnDefinition(
    name="username",
    data_type=DataType.TEXT,
    unique=True,
    not_null=True
))
```

### WhereCondition
WHERE条件构造器。

```python
from pysqlit.models import WhereCondition

# 创建条件
condition = WhereCondition("age", ">", 18)
condition = WhereCondition("username", "LIKE", "a%")
condition = WhereCondition("email", "IN", ["a@b.com", "c@d.com"])

# 复合条件
from pysqlit.models import AndCondition, OrCondition

complex_condition = AndCondition([
    WhereCondition("age", ">", 18),
    OrCondition([
        WhereCondition("status", "=", "active"),
        WhereCondition("role", "=", "admin")
    ])
])
```

## ⚙️ 配置选项

### DatabaseConfig
数据库配置类。

```python
from pysqlit.config import DatabaseConfig

config = DatabaseConfig(
    page_size=4096,
    cache_size=100,
    max_connections=10,
    timeout=5.0,
    isolation_level=IsolationLevel.REPEATABLE_READ,
    auto_vacuum=True,
    foreign_keys=True,
    journal_mode="WAL"
)
```

### 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page_size` | int | 4096 | 数据库页大小 |
| `cache_size` | int | 100 | 页缓存大小 |
| `max_connections` | int | 10 | 最大连接数 |
| `timeout` | float | 5.0 | 锁等待超时时间 |
| `isolation_level` | IsolationLevel | REPEATABLE_READ | 默认隔离级别 |
| `auto_vacuum` | bool | True | 自动清理空闲页 |
| `foreign_keys` | bool | True | 启用外键约束 |
| `journal_mode` | str | "WAL" | 日志模式 |

## 🚨 异常处理

### 异常层次结构
```python
PySQLitError
├── DatabaseError
│   ├── ConnectionError
│   ├── TransactionError
│   └── SchemaError
├── StorageError
│   ├── PageError
│   └── FileError
├── ParseError
│   ├── SQLSyntaxError
│   └── ValidationError
└── BackupError
    ├── BackupCreationError
    └── BackupRestoreError
```

### 异常处理示例
```python
from pysqlit.exceptions import (
    DatabaseError, StorageError, ParseError, TransactionError
)

try:
    db.execute("INVALID SQL")
except ParseError as e:
    print(f"SQL语法错误: {e}")
    
try:
    db.execute("INSERT INTO users VALUES (1, NULL)")
except DatabaseError as e:
    print(f"数据库错误: {e}")
    
try:
    with db.transaction():
        db.execute("UPDATE nonexistent SET x = 1")
except TransactionError as e:
    print(f"事务错误: {e}")
```

## 🛠️ 工具类

### ConnectionPool
连接池管理。

```python
from pysqlit.pool import ConnectionPool

# 创建连接池
pool = ConnectionPool(
    max_connections=10,
    database_path="myapp.db",
    timeout=5.0
)

# 获取连接
with pool.get_connection() as db:
    users = db.execute("SELECT * FROM users LIMIT 10")
    
# 或使用上下文管理器
with pool.context() as db:
    db.execute("INSERT INTO users VALUES (?, ?)", (1, "Alice"))
```

### QueryBuilder
查询构建器。

```python
from pysqlit.query import QueryBuilder

# 构建查询
query = (QueryBuilder()
    .select("id", "username", "email")
    .from_table("users")
    .where("age", ">", 18)
    .where("status", "=", "active")
    .order_by("created_at", "DESC")
    .limit(10)
)

# 执行查询
results = db.execute(str(query), query.params)
```

### MigrationManager
数据库迁移管理。

```python
from pysqlit.migration import MigrationManager

# 创建迁移
migration = MigrationManager(db)

# 添加迁移
migration.add_migration("001_add_users_table", """
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL
    )
""")

# 执行迁移
migration.migrate()
```

## 📊 性能监控

### PerformanceMonitor
性能监控器。

```python
from pysqlit.monitor import PerformanceMonitor

# 创建监控器
monitor = PerformanceMonitor(db)

# 启用监控
monitor.enable()

# 执行查询
results = db.execute("SELECT * FROM users")

# 获取统计
stats = monitor.get_stats()
print(f"查询次数: {stats['query_count']}")
print(f"平均查询时间: {stats['avg_query_time']}ms")
print(f"缓存命中率: {stats['cache_hit_rate']}%")
```

### QueryProfiler
查询分析器。

```python
from pysqlit.profile import QueryProfiler

# 分析查询
profiler = QueryProfiler(db)
result = profiler.profile("SELECT * FROM users WHERE age > 25")

print(f"执行时间: {result.execution_time}ms")
print(f"扫描行数: {result.rows_scanned}")
print(f"使用索引: {result.index_used}")
```

## 🧪 测试工具

### TestDatabase
测试专用数据库。

```python
from pysqlit.testing import TestDatabase

# 创建测试数据库
test_db = TestDatabase()

# 自动清理
with test_db as db:
    db.execute("CREATE TABLE test (id INTEGER, name TEXT)")
    db.execute("INSERT INTO test VALUES (1, 'Alice')")
    # 测试结束后自动清理
```

### MockDataGenerator
测试数据生成器。

```python
from pysqlit.testing import MockDataGenerator

# 生成测试数据
generator = MockDataGenerator(db)
generator.generate_users(count=1000)
generator.generate_posts(count=5000)
```

## 🔍 调试工具

### DebugDatabase
调试模式数据库。

```python
from pysqlit.debug import DebugDatabase

# 启用调试模式
db = DebugDatabase("myapp.db", debug=True)

# 查看执行计划
plan = db.explain("SELECT * FROM users WHERE age > 25")
print(plan)

# 查看锁信息
locks = db.get_lock_info()
print(locks)
```

### SQLLogger
SQL日志记录器。

```python
from pysqlit.debug import SQLLogger

# 启用SQL日志
logger = SQLLogger(db)
logger.enable()

# 执行查询
db.execute("SELECT * FROM users")

# 查看日志
for entry in logger.get_logs():
    print(f"{entry.timestamp}: {entry.sql} ({entry.duration}ms)")
```

---

**提示**: 所有API都提供了完整的类型提示和文档字符串，建议使用IDE的自动补全功能来探索更多功能！