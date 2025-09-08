![输入图片说明](logo/Logo.png)
<center>
# PySQLit - 增强版SQLite数据库引擎

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)](tests/)
[![Code Coverage](https://img.shields.io/badge/coverage-92%25-green.svg)](tests/)

</center>
## 🚀 项目简介

PySQLit是一个纯Python实现的SQLite数据库引擎，采用现代Python架构设计，提供完整的SQL支持、ACID事务保证、并发控制和高级备份恢复功能。项目基于经典的C语言SQLite教程重构，使用面向对象设计模式，为教育、研究和生产环境提供可靠的数据存储解决方案。

### 🎯 核心优势

- **🔒 完整ACID事务** - 支持四种隔离级别，确保数据一致性
- **⚡ 并发安全** - 线程级和进程级文件锁定机制
- **💾 智能备份** - 自动备份、增量备份、时间点恢复
- **🛡️ 数据完整性** - 外键约束、唯一约束、检查约束
- **📊 性能优化** - 页缓存、索引优化、查询计划
- **🔧 企业级功能** - DDL操作、事务日志、崩溃恢复

## 📦 快速开始

### 安装

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
```

### 基础使用

``python
from pysqlit.database import EnhancedDatabase
import os

# 创建数据库连接
# 确保使用绝对路径以保证日志文件在正确的目录中创建
db_file = os.path.abspath("chao.db")
db = EnhancedDatabase(db_file)

# 创建表
db.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

# 插入数据
user_id = db.execute(
    "INSERT INTO users (username, email) VALUES (?, ?)",
    ("alice", "alice@example.com")
)

# 事务操作
with db.transaction():
    db.execute("UPDATE users SET email = ? WHERE id = ?", 
               ("new@example.com", user_id))
    
# 查询数据
users = db.execute("SELECT * FROM users WHERE username LIKE ?", ("ali%",))
for user in users:
    print(f"User: {user['username']}, Email: {user['email']}")

# 创建备份
backup_path = db.create_backup("daily_backup")
print(f"Backup created: {backup_path}")

db.close()
```

### 简化版接口

对于需要更简单API的用户，PySQLit还提供了简化版接口：

```python
from pysqlit.simple import SimpleDatabase

# 使用上下文管理器创建数据库连接
with SimpleDatabase("example.db") as db:
    # 创建表
    db.create_table(
        table_name="users",
        columns={
            "id": "INTEGER",
            "name": "TEXT",
            "email": "TEXT",
            "age": "INTEGER"
        },
        primary_key="id",
        unique_columns=["email"],
        not_null_columns=["name"]
    )
    
    # 插入数据
    db.insert("users", {"id": 1, "name": "张三", "email": "zhangsan@example.com", "age": 25})
    
    # 查询数据
    users = db.select("users")
    for user in users:
        print(user)
    
    # 更新数据
    db.update("users", {"age": 26}, where="id = 1")
    
    # 删除数据
    db.delete("users", where="id = 1")
```

### 数据文件操作接口

对于需要更强大功能的用户，PySQLit提供了数据文件操作接口，支持完整的数据库操作：

```python
from pysqlit.datafile import DataFile

# 使用上下文管理器创建数据文件操作对象
with DataFile("example.db") as df:
    # 创建表
    df.create_table(
        table_name="users",
        columns={
            "id": "INTEGER",
            "name": "TEXT",
            "email": "TEXT",
            "age": "INTEGER"
        },
        primary_key="id",
        unique_columns=["email"],
        not_null_columns=["name"]
    )
    
    # 插入数据
    df.insert("users", {"id": 1, "name": "张三", "email": "zhangsan@example.com", "age": 25})
    
    # 查询数据
    users = df.select("users")
    for user in users:
        print(user)
    
    # 更新数据
    df.update("users", {"age": 26}, where="id = 1")
    
    # 删除数据
    df.delete("users", where="id = 1")
    
    # 导入JSON数据
    df.import_from_json("users", "data.json")
    
    # 导出CSV数据
    df.export_to_csv("users", "data.csv")
```

### 增强版数据文件操作接口

对于需要更高级功能的用户，PySQLit还提供了增强版数据文件操作接口，支持更多高级数据库操作：

```python
from pysqlit.enhanced_datafile import EnhancedDataFile

# 使用上下文管理器创建增强版数据文件操作对象
with EnhancedDataFile("example.db") as edf:
    # 创建表
    edf.create_table(
        table_name="users",
        columns={
            "id": "INTEGER",
            "name": "TEXT",
            "email": "TEXT",
            "age": "INTEGER"
        },
        primary_key="id",
        unique_columns=["email"],
        not_null_columns=["name"]
    )
    
    # 批量插入数据
    batch_data = [
        {"id": 1, "name": "张三", "email": "zhangsan@example.com", "age": 25},
        {"id": 2, "name": "李四", "email": "lisi@example.com", "age": 30}
    ]
    edf.batch_insert("users", batch_data)
    
    # 多表连接查询
    joined_data = edf.select_with_join(
        tables=["users", "departments"],
        columns=["users.name", "departments.name as department"],
        join_conditions=["INNER JOIN departments ON users.department_id = departments.id"]
    )
    
    # 导入XML数据
    edf.import_from_xml("users", "data.xml")
    
    # 导出XML数据
    edf.export_to_xml("users", "data.xml")
    
    # 创建索引
    edf.create_index("users", "idx_users_age", ["age"])
```

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    应用层接口                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   SQL API   │  │   ORM API   │  │   CLI (REPL)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    核心引擎层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ SQL Parser  │  │  Executor   │  │ Transaction Mgr │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    存储管理层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   Tables    │  │   Indexes   │  │   Storage       │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 📁 项目结构

```
py-sqlit/
├── pysqlit/                    # 核心库
│   ├── __init__.py
│   ├── database.py            # 增强数据库类
│   ├── transaction.py         # 事务管理
│   ├── backup.py             # 备份恢复
│   ├── ddl.py                # DDL操作
│   ├── parser.py             # SQL解析器
│   ├── btree.py              # B树索引
│   ├── storage.py            # 存储引擎
│   ├── models.py             # 数据模型
│   ├── exceptions.py         # 异常定义
│   └── repl.py               # 交互式界面
├── tests/                    # 测试套件
├── docs/                     # 完整文档
├── examples/                 # 使用示例
├── db_logs/                  # 事务日志
├── backups/                  # 自动备份
├── main.py                   # 程序入口
├── pytest.ini               # 测试配置
└── requirements.txt          # 依赖列表
```

## 🛠️ 核心功能

### 1. 完整SQL支持
- ✅ SELECT, INSERT, UPDATE, DELETE
- ✅ WHERE子句、ORDER BY、LIMIT
- ✅ 聚合函数、GROUP BY
- ✅ 子查询、JOIN操作

### 2. 事务管理
- ✅ ACID特性保证
- ✅ 四种隔离级别（READ UNCOMMITTED, READ COMMITTED, REPEATABLE READ, SERIALIZABLE）
- ✅ 自动回滚和崩溃恢复
- ✅ 死锁检测和解决

### 3. 并发控制
- ✅ 文件级锁定（共享锁、排他锁）
- ✅ 跨平台支持（Windows、Linux、macOS）
- ✅ 死锁预防机制

### 4. 备份恢复
- ✅ 热备份（在线备份）
- ✅ 增量备份
- ✅ 时间点恢复
- ✅ 自动清理策略

### 5. 数据完整性
- ✅ 主键约束
- ✅ 唯一约束
- ✅ 外键约束
- ✅ 检查约束
- ✅ NOT NULL约束

## 📊 性能基准

| 操作类型 | 性能指标 | 测试数据 |
|----------|----------|----------|
| 插入操作 | 15,000+ 行/秒 | 100万行数据 |
| 查询操作 | 50,000+ 行/秒 | 带索引查询 |
| 更新操作 | 8,000+ 行/秒 | 条件更新 |
| 删除操作 | 12,000+ 行/秒 | 批量删除 |
| 内存使用 | < 10MB | 10万行数据 |

## 🚀 高级特性

### 内存数据库
```python
from pysqlit.database import EnhancedDatabase

# 创建内存数据库（测试用）
db = EnhancedDatabase(":memory:")
```

### 批量操作
```python
# 批量插入
users = [
    ("alice", "alice@example.com"),
    ("bob", "bob@example.com"),
    ("charlie", "charlie@example.com")
]
db.executemany(
    "INSERT INTO users (username, email) VALUES (?, ?)",
    users
)
```

### 复杂查询
```python
# 复杂条件查询
results = db.execute("""
    SELECT u.username, p.title, p.created_at
    FROM users u
    JOIN posts p ON u.id = p.user_id
    WHERE p.created_at > '2024-01-01'
    ORDER BY p.created_at DESC
    LIMIT 10
""")
```

## 🔧 开发指南

### 运行测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_database.py

# 覆盖率测试
python -m pytest --cov=pysqlit tests/
```

### 代码风格
```bash
# 格式化代码
black pysqlit/ tests/

# 类型检查
mypy pysqlit/
```

## 📚 文档导航

- **[📖 使用指南](docs/usage-guide.md)** - 详细的使用教程
- **[🏗️ 架构设计](docs/architecture.md)** - 系统架构详解
- **[🔧 API参考](docs/api-reference.md)** - 完整的API文档
- **[⚙️ 开发指南](docs/development.md)** - 开发环境设置
- **[⚠️ 限制说明](docs/limitations.md)** - 已知限制和改进计划

## 🤝 贡献指南

我们欢迎所有形式的贡献！请查看我们的[贡献指南](docs/development.md)了解如何参与项目开发。

### 快速贡献
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 感谢 [SQLite Tutorial](https://gitee.com/cstack/db_tutorial) 提供的优秀教程基础
- 感谢所有贡献者的辛勤工作
- 感谢开源社区的支持

---

**PySQLit** - 让数据存储更简单、更可靠、更高效！![输入图片说明](Logo.png)
