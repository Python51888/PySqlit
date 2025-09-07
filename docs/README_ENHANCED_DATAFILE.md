# PySQLit 增强版数据文件操作接口

PySQLit 增强版数据文件操作接口提供了一个更高级的接口，用于对数据文件执行完整的数据库操作，包括创建、读取、更新、删除等操作，以及事务管理和备份恢复功能。

## 主要特性

1. **完整的CRUD操作支持** - 创建、读取、更新、删除数据
2. **事务管理** - 支持ACID事务
3. **数据导入/导出** - 支持JSON、CSV、XML等多种格式
4. **备份和恢复** - 数据库备份和恢复功能
5. **模式管理** - 表结构创建和管理
6. **查询优化** - 高效的数据查询
7. **索引管理** - 创建和删除索引
8. **批量操作** - 支持批量插入数据
9. **多表连接查询** - 支持多表连接查询
10. **数据库整理** - 回收未使用的空间

## 安装

```bash
pip install pysqlit
```

或者克隆项目：

```bash
git clone https://gitee.com/Python51888/PySqlit.git
cd PySqlit
```

## 快速开始

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
            "email": "TEXT"
        },
        primary_key="id",
        unique_columns=["email"],
        not_null_columns=["name"]
    )
    
    # 插入数据
    edf.insert("users", {"id": 1, "name": "张三", "email": "zhangsan@example.com"})
    
    # 查询数据
    users = edf.select("users")
    for user in users:
        print(user)
    
    # 更新数据
    edf.update("users", {"name": "李四"}, where="id = 1")
    
    # 删除数据
    edf.delete("users", where="id = 1")
```

## API 参考

### EnhancedDataFile 类

#### `__init__(filename: str, auto_commit: bool = True)`
初始化增强版数据文件操作对象。

参数:
- `filename`: 数据库文件名，":memory:"表示内存数据库
- `auto_commit`: 是否自动提交事务

#### `begin_transaction(isolation_level: IsolationLevel = IsolationLevel.REPEATABLE_READ) -> int`
开始新事务。

参数:
- `isolation_level`: 事务隔离级别

返回值:
- 事务ID

#### `commit_transaction() -> None`
提交当前事务。

#### `rollback_transaction() -> None`
回滚当前事务。

#### `create_table(table_name: str, columns: Dict[str, str], primary_key: Optional[str] = None, foreign_keys: Optional[List[Dict[str, Any]]] = None, indexes: Optional[List[str]] = None, unique_columns: Optional[List[str]] = None, not_null_columns: Optional[List[str]] = None) -> bool`
创建表。

参数:
- `table_name`: 表名
- `columns`: 列定义字典（列名 -> 数据类型）
- `primary_key`: 主键列名
- `foreign_keys`: 外键约束列表
- `indexes`: 索引列列表
- `unique_columns`: 唯一列列表
- `not_null_columns`: 非空列列表

返回值:
- 创建成功返回True

#### `drop_table(table_name: str) -> bool`
删除表。

参数:
- `table_name`: 要删除的表名

返回值:
- 删除成功返回True

#### `alter_table(table_name: str, action: str, column_name: str, column_type: Optional[str] = None) -> bool`
修改表结构。

参数:
- `table_name`: 表名
- `action`: 操作类型 ("ADD", "DROP", "MODIFY")
- `column_name`: 列名
- `column_type`: 列类型（仅在ADD和MODIFY时需要）

返回值:
- 修改成功返回True

#### `insert(table_name: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> int`
插入数据。

参数:
- `table_name`: 表名
- `data`: 要插入的数据字典或数据字典列表

返回值:
- 插入成功的行数

#### `batch_insert(table_name: str, data: List[Dict[str, Any]], batch_size: int = 1000) -> int`
批量插入数据。

参数:
- `table_name`: 表名
- `data`: 要插入的数据字典列表
- `batch_size`: 批处理大小

返回值:
- 插入成功的行数

#### `select(table_name: str, columns: Optional[List[str]] = None, where: Optional[str] = None, order_by: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]`
查询数据。

参数:
- `table_name`: 表名
- `columns`: 要查询的列列表，None表示所有列
- `where`: WHERE条件字符串
- `order_by`: ORDER BY子句
- `limit`: LIMIT子句

返回值:
- 查询结果列表，每个元素是一个字典

#### `select_with_join(tables: List[str], columns: Optional[List[str]] = None, join_conditions: Optional[List[str]] = None, where: Optional[str] = None, order_by: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]`
多表连接查询数据。

参数:
- `tables`: 表名列表
- `columns`: 要查询的列列表，None表示所有列
- `join_conditions`: JOIN条件列表
- `where`: WHERE条件字符串
- `order_by`: ORDER BY子句
- `limit`: LIMIT子句

返回值:
- 查询结果列表，每个元素是一个字典

#### `update(table_name: str, updates: Dict[str, Any], where: Optional[str] = None) -> int`
更新数据。

参数:
- `table_name`: 表名
- `updates`: 更新字典（列名 -> 新值）
- `where`: WHERE条件字符串，None表示更新所有行

返回值:
- 更新的行数

#### `delete(table_name: str, where: Optional[str] = None) -> int`
删除数据。

参数:
- `table_name`: 表名
- `where`: WHERE条件字符串，None表示删除所有行

返回值:
- 删除的行数

#### `execute_sql(sql: str) -> Tuple[Any, Any]`
执行原始SQL语句。

参数:
- `sql`: SQL语句字符串

返回值:
- 执行结果和数据的元组

#### `list_tables() -> List[str]`
列出所有表名。

返回值:
- 表名列表

#### `get_table_info(table_name: str) -> Dict[str, Any]`
获取表信息。

参数:
- `table_name`: 表名

返回值:
- 包含表信息的字典

#### `get_database_info() -> Dict[str, Any]`
获取数据库信息。

返回值:
- 包含数据库信息的字典

#### `import_from_json(table_name: str, json_file: str) -> int`
从JSON文件导入数据。

参数:
- `table_name`: 表名
- `json_file`: JSON文件路径

返回值:
- 导入的行数

#### `export_to_json(table_name: str, json_file: str, where: Optional[str] = None) -> int`
导出数据到JSON文件。

参数:
- `table_name`: 表名
- `json_file`: JSON文件路径
- `where`: WHERE条件字符串

返回值:
- 导出的行数

#### `import_from_csv(table_name: str, csv_file: str, delimiter: str = ',', has_header: bool = True) -> int`
从CSV文件导入数据。

参数:
- `table_name`: 表名
- `csv_file`: CSV文件路径
- `delimiter`: 分隔符
- `has_header`: 是否有标题行

返回值:
- 导入的行数

#### `export_to_csv(table_name: str, csv_file: str, delimiter: str = ',', include_header: bool = True, where: Optional[str] = None) -> int`
导出数据到CSV文件。

参数:
- `table_name`: 表名
- `csv_file`: CSV文件路径
- `delimiter`: 分隔符
- `include_header`: 是否包含标题行
- `where`: WHERE条件字符串

返回值:
- 导出的行数

#### `import_from_xml(table_name: str, xml_file: str, row_tag: str = "row") -> int`
从XML文件导入数据。

参数:
- `table_name`: 表名
- `xml_file`: XML文件路径
- `row_tag`: 行标签名

返回值:
- 导入的行数

#### `export_to_xml(table_name: str, xml_file: str, row_tag: str = "row", root_tag: str = "data", where: Optional[str] = None) -> int`
导出数据到XML文件。

参数:
- `table_name`: 表名
- `xml_file`: XML文件路径
- `row_tag`: 行标签名
- `root_tag`: 根标签名
- `where`: WHERE条件字符串

返回值:
- 导出的行数

#### `create_index(table_name: str, index_name: str, columns: List[str], unique: bool = False) -> bool`
创建索引。

参数:
- `table_name`: 表名
- `index_name`: 索引名
- `columns`: 列名列表
- `unique`: 是否唯一索引

返回值:
- 创建成功返回True

#### `drop_index(index_name: str) -> bool`
删除索引。

参数:
- `index_name`: 索引名

返回值:
- 删除成功返回True

#### `create_backup(backup_name: Optional[str] = None) -> str`
创建数据库备份。

参数:
- `backup_name`: 备份名称，如果为None则自动生成

返回值:
- 备份文件路径

#### `list_backups() -> List[Dict[str, Any]]`
列出所有备份。

返回值:
- 备份信息列表

#### `restore_backup(backup_path: str) -> bool`
从备份恢复数据库。

参数:
- `backup_path`: 备份文件路径

返回值:
- 恢复成功返回True

#### `vacuum() -> bool`
数据库整理，回收未使用的空间。

返回值:
- 整理成功返回True

#### `close() -> None`
关闭数据库连接。

## 使用示例

查看 [examples/enhanced_datafile_example.py](examples/enhanced_datafile_example.py) 获取完整的使用示例。

## 许可证

MIT