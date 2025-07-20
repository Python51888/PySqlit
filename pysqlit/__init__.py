"""PySQLit - 一个具有ACID兼容性的Python SQLite实现。"""

__version__ = "1.0.0"
__author__ = "PySQLit团队"

# 从各个模块导入核心类
from .database import EnhancedDatabase as Database  # 数据库主类，提供数据库操作接口
from .repl import EnhancedREPL  # 增强型REPL交互式命令行界面
from .transaction import TransactionManager, IsolationLevel  # 事务管理器和隔离级别定义
from .backup import BackupManager  # 备份管理器，负责数据库备份和恢复
from .ddl import DDLManager  # 数据定义语言管理器，处理表结构操作
from .models import Row, DataType, TableSchema, ColumnDefinition  # 数据模型定义

# 定义公共API，这些符号将被导出供外部使用
__all__ = [
    "Database",  # 主数据库类
    "EnhancedREPL",  # 增强型REPL
    "TransactionManager",  # 事务管理器
    "IsolationLevel",  # 事务隔离级别枚举
    "BackupManager",  # 备份管理器
    "DDLManager",  # DDL管理器
    "Row",  # 数据行类
    "DataType",  # 数据类型枚举
    "TableSchema",  # 表结构定义
    "ColumnDefinition"  # 列定义类
]