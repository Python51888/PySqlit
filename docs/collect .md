# Python SQLite 操作示例集

这个目录包含了使用Python内置sqlite3库操作SQLite数据库的完整示例集，从基础操作到高级优化技巧。

## 示例文件说明

### 1. 基础操作示例
- **[01_basic_connection.py](01_basic_connection.py)** - 数据库连接和表创建
  - 创建数据库连接
  - 创建用户表和产品表
  - 查看数据库结构

### 2. 数据操作示例
- **[02_insert_and_query.py](02_insert_and_query.py)** - 数据插入和查询
  - 批量插入示例数据
  - 基本查询操作
  - 条件查询和聚合函数

### 3. 数据维护示例
- **[03_update_and_delete.py](03_update_and_delete.py)** - 数据更新和删除
  - 单条和批量更新
  - 单条和批量删除
  - 安全删除确认机制

### 4. 事务处理示例
- **[04_transactions.py](04_transactions.py)** - 事务处理
  - 转账事务示例
  - 事务回滚演示
  - 保存点(Savepoint)使用

### 5. 安全防护示例
- **[05_parameterized_queries.py](05_parameterized_queries.py)** - 参数化查询和SQL注入防护
  - SQL注入攻击演示
  - 参数化查询防护
  - 输入验证和清理

### 6. 备份恢复示例
- **[06_backup_and_restore.py](06_backup_and_restore.py)** - 数据库备份和恢复
  - 多种备份方式（文件复制、SQLite API、压缩备份）
  - 增量备份
  - 备份验证和恢复

### 7. 批量操作示例
- **[07_batch_operations.py](07_batch_operations.py)** - 高效批量操作
  - 单条插入 vs 批量插入性能对比
  - 大数据集处理
  - 内存数据库 vs 文件数据库性能对比

### 8. 性能优化示例
- **[08_indexing_and_optimization.py](08_indexing_and_optimization.py)** - 索引和性能优化
  - 索引创建和性能测试
  - 查询计划分析
  - 数据库优化命令

## 使用说明

### 运行顺序
建议按以下顺序运行示例：
1. `01_basic_connection.py` - 创建基础环境
2. `02_insert_and_query.py` - 插入测试数据
3. 其他示例可以按需运行

### 运行单个示例
```bash
python 01_basic_connection.py
```

### 运行所有示例
```bash
# 在examples目录下运行
python -m 01_basic_connection.py
python -m 02_insert_and_query.py
# ... 以此类推
```

## 数据库文件
- `example.db` - 主要示例数据库
- `backups/` - 备份文件目录（由06_backup_and_restore.py创建）

## 技术要求
- Python 3.6+
- 无需额外依赖，仅使用Python标准库

## 学习路径

### 初学者路径
1. 01 → 02 → 03：掌握基础CRUD操作
2. 04：学习事务处理
3. 05：了解安全防护

### 进阶路径
1. 06：掌握备份恢复
2. 07：优化批量操作
3. 08：性能调优

### 完整学习
按顺序运行所有示例，全面了解SQLite操作

## 注意事项
- 示例会创建和修改数据库文件
- 部分示例会删除现有数据
- 建议在测试环境中运行
- 生产环境使用前请修改配置

## 扩展学习
- 查看[官方SQLite文档](https://sqlite.org/docs.html)
- 了解[Python sqlite3模块文档](https://docs.python.org/3/library/sqlite3.html)
- 探索更多高级特性如FTS全文搜索、JSON支持等