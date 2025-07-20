"""PySQLit增强数据模型模块，支持DDL和事务操作。

该模块定义了PySQLit数据库系统的核心数据模型，包括：
- SQL语句类型枚举
- 数据类型定义（完整SQLite3兼容性）
- 表模式定义（支持外键、索引、约束）
- 行数据模型（支持序列化/反序列化）
- 事务日志模型

主要功能：
1. 完整的数据类型支持（SQLite3兼容）
2. 表模式管理（列定义、约束、索引）
3. 行数据的序列化和反序列化
4. 外键约束支持
5. 事务日志记录
"""

import struct
import json
import os
from datetime import datetime
from enum import Enum
from typing import Tuple, Dict, List, Any, Optional, Union
from dataclasses import dataclass


class MetaCommandResult(Enum):
    """元命令处理结果枚举。
    
    用于表示REPL环境中元命令的执行结果。
    
    Attributes:
        SUCCESS: 命令执行成功
        UNRECOGNIZED_COMMAND: 无法识别的命令
    """
    SUCCESS = 0
    UNRECOGNIZED_COMMAND = 1


class PrepareResult(Enum):
    """SQL语句预处理结果枚举。
    
    用于表示SQL语句在预处理阶段的结果。
    
    Attributes:
        SUCCESS: 预处理成功
        NEGATIVE_ID: 负ID错误
        STRING_TOO_LONG: 字符串过长
        SYNTAX_ERROR: 语法错误
        UNRECOGNIZED_STATEMENT: 无法识别的语句
    """
    SUCCESS = 0
    NEGATIVE_ID = 1
    STRING_TOO_LONG = 2
    SYNTAX_ERROR = 3
    UNRECOGNIZED_STATEMENT = 4


class ExecuteResult(Enum):
    """SQL语句执行结果枚举。
    
    用于表示SQL语句在执行阶段的结果。
    
    Attributes:
        SUCCESS: 执行成功
        TABLE_FULL: 表已满
        DUPLICATE_KEY: 重复键值
    """
    SUCCESS = 0
    TABLE_FULL = 1
    DUPLICATE_KEY = 2


class StatementType(Enum):
    """SQL语句类型枚举。
    
    定义了PySQLit支持的所有SQL语句类型。
    
    Attributes:
        INSERT: 插入语句
        SELECT: 查询语句
        UPDATE: 更新语句
        DELETE: 删除语句
        CREATE_TABLE: 创建表
        DROP_TABLE: 删除表
        ALTER_TABLE: 修改表
        CREATE_INDEX: 创建索引
        DROP_INDEX: 删除索引
    """
    INSERT = 0
    SELECT = 1
    UPDATE = 2
    DELETE = 3
    CREATE_TABLE = 4
    DROP_TABLE = 5
    ALTER_TABLE = 6
    CREATE_INDEX = 7
    DROP_INDEX = 8


class DataType(Enum):
    """支持的SQL数据类型 - 完整SQLite3兼容性。
    
    提供了完整SQLite3数据类型支持，包括：
    - SQLite3存储类（NULL, INTEGER, REAL, TEXT, BLOB）
    - SQLite3类型亲和性（NUMERIC）
    - 常见SQL类型映射
    - 整数变体（TINYINT, SMALLINT等）
    - 字符变体（VARCHAR, CHAR等）
    
    Examples:
        >>> # 从字符串获取数据类型
        >>> dtype = DataType.from_string("VARCHAR(255)")
        >>> print(dtype)  # DataType.TEXT
    """
    # SQLite3存储类
    NULL = "NULL"
    INTEGER = "INTEGER"
    REAL = "REAL"
    TEXT = "TEXT"
    BLOB = "BLOB"
    
    # SQLite3类型亲和性
    NUMERIC = "NUMERIC"
    
    # 常见SQL类型（映射到SQLite3存储类）
    VARCHAR = "TEXT"
    CHAR = "TEXT"
    STRING = "TEXT"
    FLOAT = "REAL"
    DOUBLE = "REAL"
    DECIMAL = "REAL"
    BOOLEAN = "INTEGER"
    DATE = "TEXT"
    DATETIME = "TEXT"
    TIME = "TEXT"
    TIMESTAMP = "TEXT"
    CLOB = "TEXT"
    
    # 整数变体
    TINYINT = "INTEGER"
    SMALLINT = "INTEGER"
    MEDIUMINT = "INTEGER"
    BIGINT = "INTEGER"
    UNSIGNED_BIG_INT = "INTEGER"
    INT2 = "INTEGER"
    INT8 = "INTEGER"
    
    # 字符变体
    CHARACTER = "TEXT"
    VARYING_CHARACTER = "TEXT"
    NCHAR = "TEXT"
    NATIVE_CHARACTER = "TEXT"
    NVARCHAR = "TEXT"

    @classmethod
    def from_string(cls, type_str: str) -> 'DataType':
        """将字符串转换为DataType，处理SQLite3类型亲和性。
        
        Args:
            type_str: 类型字符串（如"VARCHAR(255)"）
            
        Returns:
            DataType: 对应的数据类型枚举值
            
        Examples:
            >>> DataType.from_string("VARCHAR")
            DataType.TEXT
            >>> DataType.from_string("INT")
            DataType.INTEGER
        """
        type_str = type_str.upper().strip()
        
        # 直接映射
        for dt in cls:
            if dt.name == type_str or dt.value == type_str:
                return dt
        
        # 处理类型亲和性映射
        affinity_map = {
            'INT': cls.INTEGER,
            'INTEGER': cls.INTEGER,  # 为INTEGER添加显式映射
            'TINYINT': cls.INTEGER,
            'SMALLINT': cls.INTEGER,
            'MEDIUMINT': cls.INTEGER,
            'BIGINT': cls.INTEGER,
            'UNSIGNED BIG INT': cls.INTEGER,
            'INT2': cls.INTEGER,
            'INT8': cls.INTEGER,
            'CHARACTER': cls.TEXT,
            'VARCHAR': cls.TEXT,
            'VARYING CHARACTER': cls.TEXT,
            'NCHAR': cls.TEXT,
            'NATIVE_CHARACTER': cls.TEXT,
            'NVARCHAR': cls.TEXT,
            'CLOB': cls.TEXT,
            'DOUBLE': cls.REAL,
            'DOUBLE PRECISION': cls.REAL,
            'FLOAT': cls.REAL,
            'DECIMAL': cls.REAL,
            'BOOLEAN': cls.INTEGER,
            'DATE': cls.TEXT,
            'DATETIME': cls.TEXT,
            'TIME': "TEXT",
            'TIMESTAMP': "TEXT",
        }
        
        return affinity_map.get(type_str, cls.TEXT)


@dataclass
class ForeignKey:
    """外键定义。
    
    用于定义表之间的外键关系。
    
    Attributes:
        column: 当前表中的列名
        ref_table: 引用的表名
        ref_column: 引用表中的列名
    """
    column: str
    ref_table: str
    ref_column: str

@dataclass
class ColumnDefinition:
    """列定义，用于表模式。
    
    定义表中的列，包括数据类型、约束和默认值等信息。
    
    Attributes:
        name: 列名
        data_type: 数据类型
        is_primary: 是否为主键
        is_nullable: 是否允许NULL值
        is_unique: 是否有唯一约束
        is_autoincrement: 是否自增
        default_value: 默认值
        max_length: 最大长度（文本类型）
        foreign_key: 外键定义
    
    Examples:
        >>> col = ColumnDefinition("id", DataType.INTEGER, is_primary=True, is_autoincrement=True)
        >>> print(col)
        <Column id INTEGER PK AUTO>
    """
    name: str
    data_type: DataType
    is_primary: bool = False
    is_nullable: bool = True
    is_unique: bool = False
    is_autoincrement: bool = False
    default_value: Any = None
    max_length: Optional[int] = None
    foreign_key: Optional[ForeignKey] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。
        
        Returns:
            Dict[str, Any]: 包含列所有属性的字典
        """
        return {
            'name': self.name,
            'data_type': self.data_type.value,
            'is_primary': self.is_primary,
            'is_nullable': self.is_nullable,
            'is_unique': self.is_unique,
            'is_autoincrement': self.is_autoincrement,
            'foreign_key': self.foreign_key.to_dict() if self.foreign_key else None,
            'default_value': self.default_value,
            'max_length': self.max_length
        }

    def __repr__(self) -> str:
        """字符串表示形式。
        
        Returns:
            str: 列的详细描述字符串
        """
        return f"<Column {self.name} {self.data_type.name}{f'({self.max_length})' if self.max_length else ''}{' PK' if self.is_primary else ''}{' AUTO' if self.is_autoincrement else ''}{' UNIQUE' if self.is_unique else ''}{' NOT NULL' if not self.is_nullable else ''}>"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColumnDefinition':
        """从字典创建列定义。
        
        Args:
            data: 包含列属性的字典
            
        Returns:
            ColumnDefinition: 列定义对象
        """
        return cls(
            name=data['name'],
            data_type=DataType(data['data_type']),
            is_primary=data.get('is_primary', False),
            is_nullable=data.get('is_nullable', True),
            is_unique=data.get('is_unique', False),
            is_autoincrement=data.get('is_autoincrement', False),
            default_value=data.get('default_value'),
            max_length=data.get('max_length')
        )


@dataclass
class ForeignKeyConstraint:
    """外键约束定义。
    
    定义表之间的外键约束关系。
    
    Attributes:
        column: 当前表中的列名
        ref_table: 引用的表名
        ref_column: 引用表中的列名
        on_delete: 删除时的操作（默认NO ACTION）
        on_update: 更新时的操作（默认NO ACTION）
    """
    column: str
    ref_table: str
    ref_column: str
    on_delete: str = "NO ACTION"
    on_update: str = "NO ACTION"


@dataclass
class IndexDefinition:
    """索引定义。
    
    定义表的索引信息。
    
    Attributes:
        name: 索引名称
        columns: 索引列列表
        is_unique: 是否为唯一索引
    """
    name: str
    columns: List[str]
    is_unique: bool = False


class TableSchema:
    """表模式定义。
    
    定义数据库表的结构，包括列定义、主键、外键、索引等信息。
    
    Attributes:
        table_name: 表名
        columns: 列定义字典（列名 -> ColumnDefinition）
        primary_key: 主键列名
        foreign_keys: 外键约束列表
        indexes: 索引字典（索引名 -> IndexDefinition）
        auto_increment_value: 自增计数器
    
    Examples:
        >>> schema = TableSchema("users")
        >>> schema.add_column(ColumnDefinition("id", DataType.INTEGER, is_primary=True))
        >>> schema.add_column(ColumnDefinition("name", DataType.TEXT, max_length=50))
    """
    
    def __init__(self, table_name: str):
        """初始化表模式。
        
        Args:
            table_name: 表名
        """
        self.table_name = table_name
        self.columns: Dict[str, ColumnDefinition] = {}
        self.primary_key: Optional[str] = None
        self.foreign_keys: List[ForeignKeyConstraint] = []
        self.indexes: Dict[str, IndexDefinition] = {}
        self.auto_increment_value: int = 1  # 自增主键计数器
        
    def add_foreign_key(self, constraint: ForeignKeyConstraint):
        """添加外键约束。
        
        Args:
            constraint: 外键约束对象
        """
        self.foreign_keys.append(constraint)
        
    def add_column(self, column: ColumnDefinition):
        """向表中添加列。
        
        Args:
            column: 列定义对象
        """
        self.columns[column.name] = column
        if column.is_primary:
            self.primary_key = column.name
            
    def add_index_definition(self, name: str, columns: List[str], unique: bool = False):
        """添加索引定义。
        
        Args:
            name: 索引名称
            columns: 索引列列表
            unique: 是否为唯一索引
        """
        self.indexes[name] = IndexDefinition(name, columns, unique)
        
    def add_index(self, index: IndexDefinition):
        """添加索引。
        
        Args:
            index: 索引定义对象
        """
        self.indexes[index.name] = index
        
    def get_column(self, name: str) -> Optional[ColumnDefinition]:
        """根据名称获取列定义。
        
        Args:
            name: 列名
            
        Returns:
            Optional[ColumnDefinition]: 列定义对象，不存在返回None
        """
        return self.columns.get(name)
        
    def validate_row(self, row_data: Dict[str, Any], storage: Any = None) -> bool:
        """根据模式验证行数据，包括外键约束。
        
        验证内容包括：
        - 数据类型检查
        - 非空约束检查
        - 唯一约束检查
        - 外键约束检查
        
        Args:
            row_data: 行数据字典
            storage: 存储对象（用于外键验证）
            
        Returns:
            bool: 验证通过返回True
            
        Examples:
            >>> schema.validate_row({"id": 1, "name": "张三"})
            True
        """
        # 验证列级约束
        for col_name, col_def in self.columns.items():
            value = row_data.get(col_name, col_def.default_value)
            
            if value is None:
                if not col_def.is_nullable:
                    return False
            else:
                # 检查数据类型
                if col_def.data_type == DataType.TEXT and not isinstance(value, str):
                    return False
                elif col_def.data_type == DataType.INTEGER and not isinstance(value, int):
                    return False
                elif col_def.data_type == DataType.REAL and not isinstance(value, float):
                    return False
            
            # 检查文本最大长度
            if col_def.data_type == DataType.TEXT and col_def.max_length:
                if len(value) > col_def.max_length:
                    return False
        
        # 验证外键约束
        if storage:
            for fk in self.foreign_keys:
                fk_value = row_data.get(fk.column)
                if fk_value is not None:
                    ref_table = storage.get_table(fk.ref_table)
                    if not ref_table:
                        return False
                    
                    # 检查引用行是否存在
                    found = False
                    for row in ref_table.rows():
                        if row.get_value(fk.ref_column) == fk_value:
                            found = True
                            break
                    
                    if not found:
                        return False
        
        return True
    
    def get_next_auto_increment(self) -> int:
        """获取下一个自增值。
        
        基于实际最大ID获取下一个自增值。
        
        Returns:
            int: 下一个自增值
        """
        # 目前使用简单的计数器方式
        # 在实际实现中，这会查询实际的最大ID
        current = self.auto_increment_value
        self.auto_increment_value += 1
        return current
    
    def has_auto_increment(self) -> bool:
        """检查表是否有自增主键。
        
        Returns:
            bool: 有自增主键返回True
        """
        if not self.primary_key:
            return False
        primary_col = self.columns.get(self.primary_key)
        return primary_col and primary_col.is_primary and primary_col.is_autoincrement
    
    def get_row_size(self) -> int:
        """根据列定义计算实际行大小。
        
        Returns:
            int: 行大小（字节）
        """
        total_size = 0
        for col_name, col_def in self.columns.items():
            if col_def.data_type == DataType.INTEGER:
                total_size += 4
            elif col_def.data_type == DataType.REAL:
                total_size += 8
            elif col_def.data_type == DataType.TEXT:
                total_size += col_def.max_length or 255
            elif col_def.data_type == DataType.BOOLEAN:
                total_size += 1
            elif col_def.data_type == DataType.NULL:
                total_size += 4
            else:
                total_size += 4  # 默认32位整数
        return total_size
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。
        
        Returns:
            Dict[str, Any]: 包含表所有信息的字典
        """
        return {
            'table_name': self.table_name,
            'columns': {name: col.to_dict() for name, col in self.columns.items()},
            'primary_key': self.primary_key,
            'foreign_keys': [
                {
                    'column': fk.column,
                    'ref_table': fk.ref_table,
                    'ref_column': fk.ref_column,
                    'on_delete': fk.on_delete,
                    'on_update': fk.on_update
                }
                for fk in self.foreign_keys
            ],
            'indexes': {
                name: {
                    'name': idx.name,
                    'columns': idx.columns,
                    'is_unique': idx.is_unique
                }
                for name, idx in self.indexes.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TableSchema':
        """从字典创建表模式。
        
        Args:
            data: 包含表信息的字典
            
        Returns:
            TableSchema: 表模式对象
        """
        schema = cls(data['table_name'])
        
        for col_name, col_data in data['columns'].items():
            schema.add_column(ColumnDefinition.from_dict(col_data))
            
        schema.primary_key = data.get('primary_key')
        
        for fk_data in data.get('foreign_keys', []):
            schema.add_foreign_key(ForeignKeyConstraint(
                column=fk_data['column'],
                ref_table=fk_data['ref_table'],
                ref_column=fk_data['ref_column'],
                on_delete=fk_data.get('on_delete', 'NO ACTION'),
                on_update=fk_data.get('on_update', 'NO ACTION')
            ))
            
        for idx_name, idx_data in data.get('indexes', {}).items():
            schema.add_index(IndexDefinition(
                name=idx_data['name'],
                columns=idx_data['columns'],
                is_unique=idx_data.get('is_unique', False)
            ))
            
        return schema


class Row:
    """数据库行数据模型。
    
    表示数据库中的一行数据，支持动态列和序列化/反序列化功能。
    
    Attributes:
        data: 行数据字典（列名 -> 值）
    
    Examples:
        >>> row = Row(id=1, name="张三", email="zhangsan@example.com")
        >>> print(row.name)  # 张三
        >>> row.age = 25  # 动态添加列
    """
    
    def __init__(self, **kwargs):
        """初始化行数据。
        
        Args:
            **kwargs: 列名和值的键值对
        """
        self.data = kwargs
        
    def __getattr__(self, name):
        """动态属性访问。
        
        允许通过点语法访问列值。
        
        Args:
            name: 列名
            
        Returns:
            列值
            
        Raises:
            AttributeError: 如果列不存在
        """
        if name in self.data:
            return self.data[name]
        raise AttributeError(f"Column '{name}' not found")
        
    def __setattr__(self, name, value):
        """动态属性设置。
        
        允许通过点语法设置列值。
        
        Args:
            name: 列名
            value: 列值
        """
        if name == 'data':
            super().__setattr__(name, value)
        else:
            self.data[name] = value
            
    def __repr__(self) -> str:
        """字符串表示。
        
        Returns:
            str: 行数据的字符串表示
        """
        return f"Row({self.data})"
    
    def __eq__(self, other) -> bool:
        """检查与另一行的相等性。
        
        Args:
            other: 另一个Row对象
            
        Returns:
            bool: 数据相等返回True
        """
        if not isinstance(other, Row):
            return False
        return self.data == other.data
    
    def get_value(self, column_name: str) -> Any:
        """获取指定列的值。
        
        Args:
            column_name: 列名
            
        Returns:
            Any: 列值，不存在返回None
        """
        return self.data.get(column_name)
        
    def set_value(self, column_name: str, value: Any):
        """设置指定列的值。
        
        Args:
            column_name: 列名
            value: 列值
        """
        self.data[column_name] = value
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。
        
        Returns:
            Dict[str, Any]: 行数据的字典副本
        """
        return self.data.copy()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Row':
        """从字典创建行对象。
        
        Args:
            data: 包含行数据的字典
            
        Returns:
            Row: 行对象
        """
        return cls(**data)
    
    def serialize(self, schema: TableSchema) -> bytes:
        """根据表模式将行数据序列化为字节流。
        
        支持多种数据类型的序列化，包括外键支持。
        
        Args:
            schema: 表模式对象
            
        Returns:
            bytes: 序列化后的字节数据
            
        Examples:
            >>> schema = TableSchema("users")
            >>> schema.add_column(ColumnDefinition("id", DataType.INTEGER, is_primary=True))
            >>> row = Row(id=1)
            >>> data = row.serialize(schema)
        """
        result = b''
        
        for col_name, col_def in schema.columns.items():
            value = self.data.get(col_name, col_def.default_value)
            
            # 处理数据值
            if value is None:
                # NULL值标记
                result += b'\x00\x00\x00\x00'
            else:
                if col_def.data_type == DataType.INTEGER:
                    # 直接使用整数值，无需转换
                    result += struct.pack('<I', value)
                elif col_def.data_type == DataType.REAL:
                    result += struct.pack('<d', float(value))
                elif col_def.data_type == DataType.TEXT:
                    text_value = str(value)
                    max_len = col_def.max_length or 255
                    # 必要时截断
                    if len(text_value) > max_len:
                        text_value = text_value[:max_len]
                    # 转换为字节
                    text_bytes = text_value.encode('utf-8')
                    result += struct.pack('<I', len(text_bytes))
                    result += text_bytes
                elif col_def.data_type == DataType.BOOLEAN:
                    result += struct.pack('<?', bool(value))
                else:
                    # 回退到文本
                    text_bytes = str(value).encode('utf-8')
                    result += struct.pack('<I', len(text_bytes))
                    result += text_bytes
        
        return result
    
    @classmethod
    def deserialize(cls, data: bytes, schema: TableSchema) -> 'Row':
        """根据表模式将字节流反序列化为行数据。
        
        Args:
            data: 序列化后的字节数据
            schema: 表模式对象
            
        Returns:
            Row: 反序列化后的行对象
            
        Examples:
            >>> row = Row.deserialize(data, schema)
            >>> print(row.id)  # 1
        """
        # 空数据返回空行
        if not data or len(data) == 0:
            return cls()
            
        offset = 0
        row_data = {}
        
        # 按模式顺序处理每个列
        for col_name, col_def in schema.columns.items():
            # 如果到达数据末尾则跳过
            if offset >= len(data):
                row_data[col_name] = None
                continue
                
            # 处理NULL标记（4个空字节）
            if offset + 4 <= len(data) and data[offset:offset+4] == b'\x00\x00\x00\x00':
                row_data[col_name] = None
                offset += 4
                continue
                
            try:
                # 根据数据类型处理
                data_type = col_def.data_type.value
                value = None
                
                # 处理INTEGER类型
                if data_type == 'INTEGER':
                    if offset + 4 <= len(data):
                        value = struct.unpack('<I', data[offset:offset+4])[0]
                    else:
                        value = 0
                    offset += 4
                    
                # 处理REAL类型
                elif data_type == 'REAL':
                    if offset + 8 <= len(data):
                        value = struct.unpack('<d', data[offset:offset+8])[0]
                    else:
                        value = 0.0
                    offset += 8
                    
                # 处理TEXT类型
                elif data_type == 'TEXT':
                    if offset + 4 > len(data):
                        value = ''
                        offset += 4
                    else:
                        length = struct.unpack('<I', data[offset:offset+4])[0]
                        offset += 4
                        if offset + length > len(data):
                            value = ''
                        else:
                            value = data[offset:offset+length].decode('utf-8').rstrip('\x00')
                        offset += length
                    
                # 处理BOOLEAN类型
                elif data_type == 'BOOLEAN':
                    if offset + 1 <= len(data):
                        value = struct.unpack('<?', data[offset:offset+1])[0]
                    else:
                        value = False
                    offset += 1
                    
                # 处理其他类型
                else:
                    offset += 4
                    value = None
                
                row_data[col_name] = value
                
            except Exception as e:
                # 优雅处理反序列化错误
                row_data[col_name] = None
        
        return cls(**row_data)


# 验证常量定义
COLUMN_USERNAME_SIZE = 32
COLUMN_EMAIL_SIZE = 255


class TransactionLog:
    """事务日志类，用于恢复和审计。
    
    提供事务操作的持久化记录，支持故障恢复和数据审计。
    
    Attributes:
        log_path: 日志文件路径
    
    Examples:
        >>> log = TransactionLog("database.log")
        >>> log.write_record(1, "INSERT", "users", {"id": 1, "name": "张三"})
    """
    
    def __init__(self, log_path: str):
        """初始化事务日志。
        
        Args:
            log_path: 日志文件路径
        """
        self.log_path = log_path
        
    def write_record(self, transaction_id: int, operation: str, 
                    table_name: str, row_data: Dict[str, Any], 
                    old_data: Optional[Dict[str, Any]] = None):
        """写入事务日志记录。
        
        记录事务操作的详细信息，包括时间戳、事务ID、操作类型等。
        
        Args:
            transaction_id: 事务ID
            operation: 操作类型（INSERT/UPDATE/DELETE）
            table_name: 表名
            row_data: 行数据
            old_data: 旧数据（用于UPDATE操作）
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'transaction_id': transaction_id,
            'operation': operation,
            'table_name': table_name,
            'row_data': row_data,
            'old_data': old_data
        }
        
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(record) + '\n')
            
    def read_records(self, transaction_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """读取事务日志记录。
        
        可以按事务ID过滤，也可以读取所有记录。
        
        Args:
            transaction_id: 事务ID，None表示读取所有记录
            
        Returns:
            List[Dict[str, Any]]: 事务记录列表
        """
        records = []
        
        if not os.path.exists(self.log_path):
            return records
            
        with open(self.log_path, 'r') as f:
            for line in f:
                record = json.loads(line.strip())
                if transaction_id is None or record['transaction_id'] == transaction_id:
                    records.append(record)
                    
        return records