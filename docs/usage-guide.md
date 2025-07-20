# PySQLit 使用指南

## 🚀 快速开始

### 1. 安装和设置

#### 1.1 系统要求
- Python 3.8 或更高版本
- 支持的操作系统：Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)

#### 1.2 安装方式

**方式一：从源码安装**
```bash
# 克隆项目
git clone https://gitee.com/Python51888/PySqlit.git
cd py-sqlit

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 安装开发版本
pip install -e .
```

**方式二：使用pip安装（未来支持）**
```bash
pip install py-sqlit
```

#### 1.3 验证安装
```python
import pysqlit
print(pysqlit.__version__)  # 应该显示版本号
```

### 2. 第一个数据库应用

#### 2.1 创建数据库
```python
from pysqlit.database import EnhancedDatabase

# 创建数据库
db = EnhancedDatabase("my_first_app.db")

# 创建用户表
db.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        age INTEGER CHECK(age > 0 AND age < 150),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

# 插入测试数据
users = [
    ("alice", "alice@example.com", 25),
    ("bob", "bob@example.com", 30),
    ("charlie", "charlie@example.com", 35)
]

for username, email, age in users:
    db.execute(
        "INSERT INTO users (username, email, age) VALUES (?, ?, ?)",
        (username, email, age)
    )

# 查询数据
all_users = db.execute("SELECT * FROM users")
for user in all_users:
    print(f"用户: {user['username']}, 邮箱: {user['email']}, 年龄: {user['age']}")

db.close()
```

#### 2.2 使用REPL
```bash
# 启动交互式界面
python -m pysqlit.repl myapp.db

# 在REPL中执行
SQLite [myapp.db]> CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL CHECK(price > 0),
    stock INTEGER DEFAULT 0
);

SQLite [myapp.db]> INSERT INTO products (name, price, stock) 
VALUES ('Laptop', 999.99, 10), ('Mouse', 29.99, 50);

SQLite [myapp.db]> SELECT * FROM products WHERE price > 100;
```

## 📖 基础使用

### 1. 连接管理

#### 1.1 基本连接
```python
from pysqlit.database import EnhancedDatabase

# 文件数据库
db = EnhancedDatabase("data.db")

# 内存数据库（测试用）
test_db = EnhancedDatabase(":memory:")

# 带配置的数据库
config = {
    "page_size": 8192,
    "cache_size": 200,
    "timeout": 10.0
}
db = EnhancedDatabase("data.db", **config)
```

#### 1.2 上下文管理器
```python
# 推荐方式：自动关闭
with EnhancedDatabase("data.db") as db:
    users = db.execute("SELECT * FROM users")
    # 自动关闭连接

# 传统方式
db = EnhancedDatabase("data.db")
try:
    # 使用数据库
    pass
finally:
    db.close()
```

### 2. 表操作

#### 2.1 创建表
```python
# 简单创建
db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")

# 复杂表定义
db.execute("""
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_amount REAL NOT NULL CHECK(total_amount > 0),
        status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'paid', 'shipped', 'delivered')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
""")

# 创建索引
db.execute("CREATE INDEX idx_orders_user ON orders(user_id)")
db.execute("CREATE INDEX idx_orders_status ON orders(status)")
db.execute("CREATE UNIQUE INDEX idx_orders_number ON orders(order_number)")
```

#### 2.2 修改表结构
```python
# 添加列
db.execute("ALTER TABLE users ADD COLUMN phone TEXT")

# 删除列
db.execute("ALTER TABLE users DROP COLUMN phone")

# 重命名列
db.execute("ALTER TABLE users RENAME COLUMN phone TO mobile")

# 添加约束
db.execute("ALTER TABLE users ADD CONSTRAINT chk_age CHECK (age >= 0)")
```

### 3. 数据操作

#### 3.1 插入数据
```python
# 单行插入
db.execute("INSERT INTO users (username, email) VALUES (?, ?)", 
           ("alice", "alice@example.com"))

# 多行插入
users_data = [
    ("bob", "bob@example.com"),
    ("charlie", "charlie@example.com"),
    ("dave", "dave@example.com")
]
db.executemany(
    "INSERT INTO users (username, email) VALUES (?, ?)",
    users_data
)

# 插入并获取ID
user_id = db.execute(
    "INSERT INTO users (username, email) VALUES (?, ?)",
    ("eve", "eve@example.com"),
    return_id=True
)
```

#### 3.2 查询数据
```python
# 基础查询
users = db.execute("SELECT * FROM users")

# 条件查询
adults = db.execute("SELECT * FROM users WHERE age > ?", (18,))

# 排序和限制
recent_users = db.execute(
    "SELECT * FROM users ORDER BY created_at DESC LIMIT 10"
)

# 聚合查询
stats = db.execute("""
    SELECT 
        COUNT(*) as total_users,
        AVG(age) as avg_age,
        MAX(age) as max_age,
        MIN(age) as min_age
    FROM users
""")

# 分组查询
age_groups = db.execute("""
    SELECT 
        CASE 
            WHEN age < 18 THEN 'minor'
            WHEN age < 65 THEN 'adult'
            ELSE 'senior'
        END as age_group,
        COUNT(*) as count
    FROM users
    GROUP BY age_group
""")
```

#### 3.3 更新数据
```python
# 简单更新
db.execute("UPDATE users SET age = 26 WHERE username = ?", ("alice",))

# 条件更新
db.execute("""
    UPDATE users 
    SET status = 'inactive', updated_at = CURRENT_TIMESTAMP 
    WHERE last_login < datetime('now', '-30 days')
""")

# 批量更新
db.execute("""
    UPDATE users 
    SET age = age + 1 
    WHERE birthday = date('now')
""")
```

#### 3.4 删除数据
```python
# 删除特定记录
db.execute("DELETE FROM users WHERE username = ?", ("alice",))

# 批量删除
db.execute("DELETE FROM users WHERE last_login < datetime('now', '-1 year')")

# 清空表
db.execute("DELETE FROM users")  # 保留表结构
db.execute("DROP TABLE users")   # 删除表
```

## 🔒 事务管理

### 1. 事务基础

#### 1.1 手动事务
```python
# 开始事务
tx_id = db.begin_transaction()

try:
    # 执行操作
    db.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
    db.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 2")
    
    # 提交事务
    db.commit_transaction(tx_id)
    
except Exception as e:
    # 回滚事务
    db.rollback_transaction(tx_id)
    raise
```

#### 1.2 上下文管理器
```python
# 自动事务管理
with db.transaction() as tx:
    db.execute("INSERT INTO users VALUES (?, ?)", (1, "Alice"))
    db.execute("INSERT INTO users VALUES (?, ?)", (2, "Bob"))
    # 自动提交或回滚

# 指定隔离级别
with db.transaction(isolation_level="SERIALIZABLE") as tx:
    # 执行操作
    pass
```

### 2. 事务隔离级别

#### 2.1 四种隔离级别
```python
from pysqlit.transaction import IsolationLevel

# READ UNCOMMITTED - 读未提交
with db.transaction(isolation_level=IsolationLevel.READ_UNCOMMITTED):
    pass

# READ COMMITTED - 读已提交
with db.transaction(isolation_level=IsolationLevel.READ_COMMITTED):
    pass

# REPEATABLE READ - 可重复读（默认）
with db.transaction(isolation_level=IsolationLevel.REPEATABLE_READ):
    pass

# SERIALIZABLE - 串行化
with db.transaction(isolation_level=IsolationLevel.SERIALIZABLE):
    pass
```

#### 2.2 事务示例
```python
# 转账操作
def transfer_money(from_account: int, to_account: int, amount: float):
    with db.transaction(isolation_level=IsolationLevel.SERIALIZABLE) as tx:
        # 检查余额
        balance = db.execute(
            "SELECT balance FROM accounts WHERE id = ?",
            (from_account,)
        )[0]['balance']
        
        if balance < amount:
            raise ValueError("Insufficient funds")
        
        # 执行转账
        db.execute(
            "UPDATE accounts SET balance = balance - ? WHERE id = ?",
            (amount, from_account)
        )
        db.execute(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?",
            (amount, to_account)
        )
        
        # 记录交易
        db.execute(
            "INSERT INTO transactions (from_account, to_account, amount) VALUES (?, ?, ?)",
            (from_account, to_account, amount)
        )
```

## 💾 备份恢复

### 1. 基础备份

#### 1.1 创建备份
```python
# 创建完整备份
backup_path = db.create_backup("daily_backup")
print(f"备份已创建: {backup_path}")

# 创建带描述的备份
backup_path = db.create_backup(
    "weekly_backup",
    description="Weekly full backup"
)

# 创建压缩备份
backup_path = db.create_backup(
    "compressed_backup",
    compress=True
)
```

#### 1.2 恢复备份
```python
# 列出所有备份
backups = db.list_backups()
for backup in backups:
    print(f"""
    名称: {backup['name']}
    创建时间: {backup['created']}
    大小: {backup['size_mb']} MB
    描述: {backup.get('description', 'N/A')}
    """)

# 从备份恢复
db.restore_backup("daily_backup")

# 恢复到新文件
db.restore_backup("daily_backup", new_filename="restored.db")
```

### 2. 高级备份功能

#### 2.1 自动备份
```python
# 设置自动备份
backup_thread = db.auto_backup(
    interval_hours=24,
    backup_name_prefix="auto",
    max_backups=7,
    compress=True
)

# 停止自动备份
backup_thread.stop()
```

#### 2.2 增量备份
```python
# 创建增量备份
db.create_incremental_backup("incremental_1")

# 恢复增量备份
db.restore_incremental_backup("base_backup", ["incremental_1", "incremental_2"])
```

## 📊 性能优化

### 1. 索引优化

#### 1.1 创建索引
```python
# 单列索引
db.execute("CREATE INDEX idx_users_email ON users(email)")

# 复合索引
db.execute("CREATE INDEX idx_users_name_age ON users(name, age)")

# 唯一索引
db.execute("CREATE UNIQUE INDEX idx_users_username ON users(username)")

# 部分索引
db.execute("""
    CREATE INDEX idx_active_users ON users(last_login) 
    WHERE status = 'active'
""")

# 表达式索引
db.execute("CREATE INDEX idx_users_lower_email ON users(LOWER(email))")
```

#### 1.2 索引最佳实践
```python
# 分析查询计划
plan = db.explain("SELECT * FROM users WHERE email = 'alice@example.com'")
print(plan)

# 查看索引使用情况
stats = db.execute("""
    SELECT name, stat FROM sqlite_master 
    WHERE type = 'index' AND tbl_name = 'users'
""")

# 删除无用索引
db.execute("DROP INDEX IF EXISTS idx_unused")
```

### 2. 查询优化

#### 2.1 查询重写
```python
# 避免SELECT *
# ❌ 不推荐
users = db.execute("SELECT * FROM users")

# ✅ 推荐
users = db.execute("SELECT id, username, email FROM users")

# 使用LIMIT
recent_users = db.execute(
    "SELECT id, username FROM users ORDER BY created_at DESC LIMIT 10"
)

# 使用索引列过滤
active_users = db.execute("""
    SELECT id, username 
    FROM users 
    WHERE status = 'active' 
    AND created_at > datetime('now', '-30 days')
""")
```

#### 2.2 批量操作
```python
# 批量插入
users_data = [
    ("user1", "user1@example.com", 25),
    ("user2", "user2@example.com", 30),
    # ... 更多数据
]

# ✅ 使用executemany
db.executemany(
    "INSERT INTO users (username, email, age) VALUES (?, ?, ?)",
    users_data
)

# ❌ 避免循环插入
for username, email, age in users_data:
    db.execute("INSERT INTO users ...")  # 性能差
```

### 3. 连接池

#### 3.1 使用连接池
```python
from pysqlit.pool import ConnectionPool

# 创建连接池
pool = ConnectionPool(
    database_path="myapp.db",
    max_connections=20,
    timeout=10.0
)

# 使用连接池
with pool.get_connection() as db:
    users = db.execute("SELECT * FROM users LIMIT 100")
    
# 上下文管理器
with pool.context() as db:
    db.execute("INSERT INTO users VALUES (?, ?)", (1, "Alice"))
```

## 🛠️ 高级功能

### 1. 复杂查询

#### 1.1 连接查询
```python
# 内连接
results = db.execute("""
    SELECT u.username, p.title, p.content
    FROM users u
    INNER JOIN posts p ON u.id = p.user_id
    WHERE p.created_at > datetime('now', '-7 days')
""")

# 左连接
results = db.execute("""
    SELECT u.username, COUNT(p.id) as post_count
    FROM users u
    LEFT JOIN posts p ON u.id = p.user_id
    GROUP BY u.id
""")

# 多表连接
results = db.execute("""
    SELECT u.username, c.name as category, COUNT(o.id) as order_count
    FROM users u
    INNER JOIN orders o ON u.id = o.user_id
    INNER JOIN products p ON o.product_id = p.id
    INNER JOIN categories c ON p.category_id = c.id
    WHERE o.created_at > datetime('now', '-30 days')
    GROUP BY u.id, c.id
""")
```

#### 1.2 子查询
```python
# IN子查询
results = db.execute("""
    SELECT * FROM users 
    WHERE id IN (
        SELECT user_id FROM orders 
        WHERE total_amount > 1000
    )
""")

# EXISTS子查询
results = db.execute("""
    SELECT * FROM users u
    WHERE EXISTS (
        SELECT 1 FROM orders o 
        WHERE o.user_id = u.id 
        AND o.status = 'completed'
    )
""")

# 相关子查询
results = db.execute("""
    SELECT u.username, (
        SELECT COUNT(*) FROM posts p 
        WHERE p.user_id = u.id
    ) as post_count
    FROM users u
""")
```

### 2. 视图和触发器

#### 2.1 创建视图
```python
# 创建视图
db.execute("""
    CREATE VIEW active_users AS
    SELECT id, username, email
    FROM users
    WHERE status = 'active'
    AND last_login > datetime('now', '-30 days')
""")

# 查询视图
active_users = db.execute("SELECT * FROM active_users")

# 删除视图
db.execute("DROP VIEW IF EXISTS active_users")
```

#### 2.2 创建触发器
```python
# 创建触发器
db.execute("""
    CREATE TRIGGER update_users_timestamp
    AFTER UPDATE ON users
    BEGIN
        UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END
""")

# 插入触发器
db.execute("""
    CREATE TRIGGER log_user_insert
    AFTER INSERT ON users
    BEGIN
        INSERT INTO user_logs (user_id, action, timestamp)
        VALUES (NEW.id, 'INSERT', CURRENT_TIMESTAMP);
    END
""")

# 删除触发器
db.execute("DROP TRIGGER IF EXISTS update_users_timestamp")
```

### 3. 全文搜索

#### 3.1 创建全文索引
```python
# 创建虚拟表用于全文搜索
db.execute("""
    CREATE VIRTUAL TABLE posts_fts USING fts5(
        title, 
        content, 
        content='posts', 
        content_rowid='id'
    )
""")

# 填充全文索引
db.execute("""
    INSERT INTO posts_fts(rowid, title, content)
    SELECT id, title, content FROM posts
""")

# 执行全文搜索
results = db.execute("""
    SELECT p.*, rank
    FROM posts p
    JOIN posts_fts f ON p.id = f.rowid
    WHERE posts_fts MATCH 'python database'
    ORDER BY rank
""")
```

## 🧪 测试和调试

### 1. 单元测试

#### 1.1 测试数据库操作
```python
import unittest
from pysqlit.database import EnhancedDatabase
from pysqlit.testing import TestDatabase

class TestUserOperations(unittest.TestCase):
    def setUp(self):
        self.db = TestDatabase()
        self.db.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        """)
    
    def tearDown(self):
        self.db.close()
    
    def test_insert_user(self):
        user_id = self.db.execute(
            "INSERT INTO users (username, email) VALUES (?, ?)",
            ("testuser", "test@example.com"),
            return_id=True
        )
        self.assertIsNotNone(user_id)
        
        user = self.db.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )[0]
        self.assertEqual(user['username'], "testuser")
    
    def test_unique_constraint(self):
        self.db.execute(
            "INSERT INTO users (username, email) VALUES (?, ?)",
            ("user1", "user1@example.com")
        )
        
        with self.assertRaises(Exception):
            self.db.execute(
                "INSERT INTO users (username, email) VALUES (?, ?)",
                ("user1", "user2@example.com")
            )
```

### 2. 性能测试

#### 2.1 基准测试
```python
import time
from pysqlit.database import EnhancedDatabase

def benchmark_insert_performance():
    db = EnhancedDatabase(":memory:")
    db.execute("CREATE TABLE test (id INTEGER, name TEXT)")
    
    start_time = time.time()
    
    # 测试批量插入
    data = [(i, f"User{i}") for i in range(10000)]
    db.executemany("INSERT INTO test VALUES (?, ?)", data)
    
    elapsed = time.time() - start_time
    print(f"插入10000条记录耗时: {elapsed:.2f}秒")
    print(f"平均速度: {10000/elapsed:.0f} 条/秒")
    
    db.close()

if __name__ == "__main__":
    benchmark_insert_performance()
```

### 3. 调试工具

#### 3.1 查询分析
```python
from pysqlit.debug import QueryProfiler

# 创建分析器
profiler = QueryProfiler(db)

# 分析查询
result = profiler.profile("""
    SELECT u.username, COUNT(o.id) as order_count
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    GROUP BY u.id
""")

print(f"执行时间: {result.execution_time:.3f}ms")
print(f"扫描行数: {result.rows_scanned}")
print(f"使用索引: {result.index_used}")
print(f"查询计划: {result.query_plan}")
```

#### 3.2 日志调试
```python
import logging
from pysqlit.debug import SQLLogger

# 配置日志
logging.basicConfig(level=logging.DEBUG)

# 创建SQL日志记录器
logger = SQLLogger(db)
logger.enable()

# 执行查询
db.execute("SELECT * FROM users WHERE age > 25")

# 查看日志
for entry in logger.get_logs():
    print(f"{entry.timestamp}: {entry.sql} ({entry.duration}ms)")
```

## 📈 最佳实践

### 1. 数据库设计

#### 1.1 表设计原则
```python
# ✅ 好的设计
db.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

# 创建必要的索引
db.execute("CREATE INDEX idx_users_email ON users(email)")
db.execute("CREATE INDEX idx_users_created ON users(created_at)")

# ❌ 不好的设计
# 避免过多的列
# 避免NULLable列过多
# 避免重复数据
```

#### 1.2 命名规范
```python
# 表名使用复数
db.execute("CREATE TABLE users (...)")  # ✅
db.execute("CREATE TABLE user (...)")   # ❌

# 列名使用小写+下划线
db.execute("CREATE TABLE users (first_name TEXT)")  # ✅
db.execute("CREATE TABLE users (FirstName TEXT)")   # ❌

# 外键使用表名_id
db.execute("CREATE TABLE orders (user_id INTEGER, FOREIGN KEY(user_id) REFERENCES users(id))")
```

### 2. 查询优化

#### 2.1 索引优化
```python
# 为WHERE子句中的列创建索引
db.execute("CREATE INDEX idx_users_age ON users(age)")

# 为JOIN条件中的列创建索引
db.execute("CREATE INDEX idx_orders_user_id ON orders(user_id)")

# 为ORDER BY子句中的列创建索引
db.execute("CREATE INDEX idx_orders_created ON orders(created_at DESC)")

# 复合索引的顺序很重要
db.execute("CREATE INDEX idx_users_status_created ON users(status, created_at)")
```

#### 2.2 查询模式
```python
# ✅ 使用参数化查询
db.execute("SELECT * FROM users WHERE username = ?", (username,))

# ❌ 避免字符串拼接
# db.execute(f"SELECT * FROM users WHERE username = '{username}'")

# ✅ 使用LIMIT限制结果
users = db.execute("SELECT * FROM users LIMIT 100")

# ✅ 使用EXISTS代替IN
exists = db.execute("""
    SELECT EXISTS(
        SELECT 1 FROM orders WHERE user_id = ?
    )
""", (user_id,))[0][0]
```

### 3. 错误处理

#### 3.1 异常处理模式
```python
from pysqlit.exceptions import (
    DatabaseError, StorageError, ParseError, TransactionError
)

def safe_insert_user(db, username, email):
    try:
        user_id = db.execute(
            "INSERT INTO users (username, email) VALUES (?, ?)",
            (username, email),
            return_id=True
        )
        return user_id
        
    except ParseError as e:
        logger.error(f"SQL语法错误: {e}")
        raise
        
    except DatabaseError as e:
        if "UNIQUE constraint failed" in str(e):
            logger.error(f"用户名或邮箱已存在: {username}, {email}")
            raise ValueError("用户名或邮箱已存在")
        else:
            logger.error(f"数据库错误: {e}")
            raise
            
    except Exception as e:
        logger.error(f"未知错误: {e}")
        raise
```

### 4. 安全配置

#### 4.1 连接安全
```python
# 设置合理的超时时间
db = EnhancedDatabase(
    "data.db",
    timeout=30.0,  # 30秒超时
    isolation_level=IsolationLevel.REPEATABLE_READ
)

# 限制连接数
pool = ConnectionPool(
    database_path="data.db",
    max_connections=50,
    timeout=10.0
)
```

#### 4.2 数据验证
```python
def validate_user_data(username, email, age):
    """验证用户数据"""
    if not username or len(username) < 3:
        raise ValueError("用户名至少3个字符")
    
    if not email or "@" not in email:
        raise ValueError("邮箱格式不正确")
    
    if not isinstance(age, int) or age < 0 or age > 150:
        raise ValueError("年龄必须在0-150之间")
    
    return True

# 使用验证
def create_user(db, username, email, age):
    validate_user_data(username, email, age)
    
    return db.execute(
        "INSERT INTO users (username, email, age) VALUES (?, ?, ?)",
        (username, email, age),
        return_id=True
    )
```

## 🎯 常见场景示例

### 1. 用户管理系统
```python
class UserManager:
    def __init__(self, db_path):
        self.db = EnhancedDatabase(db_path)
        self._init_tables()
    
    def _init_tables(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                birth_date DATE,
                phone TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
    
    def create_user(self, username, email, password):
        """创建新用户"""
        import hashlib
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        with self.db.transaction():
            user_id = self.db.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash),
                return_id=True
            )
            
            self.db.execute(
                "INSERT INTO user_profiles (user_id) VALUES (?)",
                (user_id,)
            )
            
            return user_id
    
    def get_user(self, user_id):
        """获取用户信息"""
        return self.db.execute("""
            SELECT u.*, p.first_name, p.last_name, p.birth_date, p.phone
            FROM users u
            LEFT JOIN user_profiles p ON u.id = p.user_id
            WHERE u.id = ?
        """, (user_id,))[0]
```

### 2. 电商订单系统
```python
class OrderManager:
    def __init__(self, db_path):
        self.db = EnhancedDatabase(db_path)
        self._init_tables()
    
    def _init_tables(self):
        # 产品表
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL CHECK(price > 0),
                stock INTEGER DEFAULT 0 CHECK(stock >= 0),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 订单表
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 订单详情表
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
    
    def create_order(self, user_id, items):
        """创建订单"""
        with self.db.transaction():
            # 计算总金额
            total_amount = 0
            for item in items:
                product = self.db.execute(
                    "SELECT price FROM products WHERE id = ?",
                    (item['product_id'],)
                )[0]
                total_amount += product['price'] * item['quantity']
            
            # 创建订单
            order_id = self.db.execute(
                "INSERT INTO orders (user_id, total_amount) VALUES (?, ?)",
                (user_id, total_amount),
                return_id=True
            )
            
            # 添加订单项
            for item in items:
                self.db.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                    (order_id, item['product_id'], item['quantity'], 
                     item.get('unit_price', product['price']))
                )
                
                # 更新库存
                self.db.execute(
                    "UPDATE products SET stock = stock - ? WHERE id = ?",
                    (item['quantity'], item['product_id'])
                )
            
            return order_id
```

---

**下一步**: 查看[开发指南](development.md)了解如何贡献代码，或查看[架构设计](architecture.md)深入了解系统实现！