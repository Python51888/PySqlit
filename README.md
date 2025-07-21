# PySQLit - 增强版SQLite数据库引擎

PySQLit 是一个增强版的 SQLite 数据库引擎，旨在提供更强大的功能和更好的性能。它不仅支持完整的 SQL 语法，还提供了事务管理、并发控制、备份恢复等高级功能。

## 核心优势

- **完整 SQL 支持**：支持完整的 SQL 语法，包括复杂的查询和事务操作。
- **事务管理**：支持 ACID 事务，确保数据的一致性和可靠性。
- **并发控制**：通过锁机制和事务隔离级别，支持高并发访问。
- **备份恢复**：提供数据库备份和恢复功能，确保数据安全。
- **数据完整性**：通过约束和索引，确保数据的完整性和一致性。

## 快速开始

### 安装

你可以通过克隆项目来获取 PySQLit：

```bash
git clone https://gitee.com/Python51888/PySqlit.git
```

### 创建虚拟环境

推荐使用虚拟环境来管理依赖：

```bash
python -m venv venv
source venv/bin/activate  # 在 Windows 上使用 `venv\Scripts\activate`
```

### 安装依赖

安装项目所需的依赖：

```bash
pip install -r requirements.txt
```

### 基础使用

#### 创建数据库连接

```python
from pysqlit.database import EnhancedDatabase

db = EnhancedDatabase("example.db")
```

#### 创建表

```python
db.create_table("users", {
    "id": "INTEGER PRIMARY KEY",
    "name": "TEXT",
    "email": "TEXT UNIQUE"
})
```

#### 插入数据

```python
db.execute("INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com')")
```

#### 事务操作

```python
with db.begin_transaction():
    db.execute("UPDATE users SET name = 'Bob' WHERE id = 1")
    db.execute("UPDATE users SET name = 'Charlie' WHERE id = 2")
```

#### 查询数据

```python
results = db.execute("SELECT * FROM users")
for row in results:
    print(row)
```

#### 创建备份

```python
from pysqlit.backup import BackupManager

backup_manager = BackupManager("example.db")
backup_manager.create_backup("backup_20231001")
```

## 架构概览

PySQLit 的架构设计分为多个层次，包括应用层、业务逻辑层、数据访问层和存储引擎层。每一层都有明确的职责，确保系统的模块化和可扩展性。

### 项目结构

- **应用层**：提供命令行接口和 Python API。
- **业务逻辑层**：处理 SQL 解析、查询执行和优化。
- **数据访问层**：管理表、索引和约束。
- **存储引擎层**：负责数据的持久化存储和管理。

## 核心功能

1. **完整 SQL 支持**：支持完整的 SQL 语法，包括复杂的查询和事务操作。
2. **事务管理**：支持 ACID 事务，确保数据的一致性和可靠性。
3. **并发控制**：通过锁机制和事务隔离级别，支持高并发访问。
4. **备份恢复**：提供数据库备份和恢复功能，确保数据安全。
5. **数据完整性**：通过约束和索引，确保数据的完整性和一致性。

## 性能基准

PySQLit 在性能方面进行了优化，支持高并发和大规模数据处理。通过缓存策略和连接池，确保系统的高效运行。

## 高级特性

### 内存数据库

你可以创建一个内存数据库用于测试：

```python
db = EnhancedDatabase(":memory:")
```

### 批量操作

#### 批量插入

```python
data = [
    ("Alice", "alice@example.com"),
    ("Bob", "bob@example.com"),
    ("Charlie", "charlie@example.com")
]
db.executemany("INSERT INTO users (name, email) VALUES (?, ?)", data)
```

#### 复杂查询

```python
results = db.execute("SELECT * FROM users WHERE name LIKE 'A%'")
for row in results:
    print(row)
```

## 开发指南

### 运行测试

你可以运行所有测试来验证安装：

```bash
pytest tests/
```

### 代码风格

确保遵循项目的代码风格和命名规范，以保持代码的一致性。

### 格式化代码

使用 `black` 和 `isort` 来格式化代码：

```bash
black .
isort .
```

### 类型检查

使用 `mypy` 进行类型检查：

```bash
mypy .
```

## 文档导航

- [快速开始](docs/index.md#快速开始)
- [用户指南](docs/usage-guide.md)
- [架构设计](docs/architecture.md)
- [API 参考](docs/api-reference.md)
- [开发指南](docs/development.md)
- [限制说明](docs/limitations.md)
- [高级主题](docs/advanced-topics.md)

## 贡献指南

欢迎贡献代码和文档。请遵循项目的贡献指南，确保代码质量和一致性。

## 许可证

PySQLit 使用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 致谢

感谢所有为 PySQLit 做出贡献的开发者和社区成员。