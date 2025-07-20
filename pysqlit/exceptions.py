"""PySQLit自定义异常模块。

该模块定义了PySQLit数据库系统中使用的所有自定义异常类，
提供了清晰的错误分类和层次结构，便于错误处理和调试。

异常层次结构：
- PySQLitError: 所有PySQLit异常的基类
  ├── DatabaseError: 数据库相关错误
  │   ├── StorageError: 存储和文件I/O错误
  │   ├── ExecutionError: 查询执行错误
  │   ├── BTreeError: B树操作错误
  │   ├── TransactionError: 事务相关错误
  │   ├── BackupError: 备份和恢复错误
  │   └── LockError: 文件锁定错误
  ├── ParseError: SQL解析错误
  └── ValidationError: 数据验证错误
"""


class PySQLitError(Exception):
    """PySQLit所有异常的基类。
    
    这是所有PySQLit自定义异常的根异常类，用于捕获所有PySQLit相关的错误。
    
    Examples:
        >>> try:
        ...     # PySQLit操作
        ... except PySQLitError as e:
        ...     print(f"PySQLit错误: {e}")
    """
    pass


class DatabaseError(PySQLitError):
    """数据库相关错误的基类。
    
    所有与数据库操作相关的异常都继承自此类。
    
    Examples:
        >>> try:
        ...     # 数据库操作
        ... except DatabaseError as e:
        ...     print(f"数据库错误: {e}")
    """
    pass


class StorageError(DatabaseError):
    """存储和文件I/O错误。
    
    当发生以下情况时抛出：
    - 文件读写失败
    - 磁盘空间不足
    - 文件权限问题
    - 文件损坏
    
    Examples:
        >>> try:
        ...     # 文件操作
        ... except StorageError as e:
        ...     print(f"存储错误: {e}")
    """
    pass


class ParseError(PySQLitError):
    """SQL解析错误。
    
    当SQL语句语法错误或无法解析时抛出。
    
    Examples:
        >>> try:
        ...     # 解析SQL
        ... except ParseError as e:
        ...     print(f"SQL解析错误: {e}")
    """
    pass


class ExecutionError(DatabaseError):
    """查询执行错误。
    
    当SQL查询执行失败时抛出，如：
    - 表不存在
    - 列不存在
    - 数据类型不匹配
    - 约束违反
    
    Examples:
        >>> try:
        ...     # 执行查询
        ... except ExecutionError as e:
        ...     print(f"执行错误: {e}")
    """
    pass


class ValidationError(PySQLitError):
    """数据验证错误。
    
    当数据不符合预期格式或约束时抛出，如：
    - 数据类型验证失败
    - 约束检查失败
    - 必填字段为空
    
    Examples:
        >>> try:
        ...     # 数据验证
        ... except ValidationError as e:
        ...     print(f"验证错误: {e}")
    """
    pass


class BTreeError(DatabaseError):
    """B树操作错误。
    
    当B树数据结构操作失败时抛出，如：
    - 节点分裂失败
    - 平衡操作失败
    - 键值冲突
    
    Examples:
        >>> try:
        ...     # B树操作
        ... except BTreeError as e:
        ...     print(f"B树错误: {e}")
    """
    pass


class TransactionError(DatabaseError):
    """事务相关错误。
    
    当事务操作失败时抛出，如：
    - 事务回滚失败
    - 死锁检测
    - 并发冲突
    
    Examples:
        >>> try:
        ...     # 事务操作
        ... except TransactionError as e:
        ...     print(f"事务错误: {e}")
    """
    pass


class BackupError(DatabaseError):
    """备份和恢复错误。
    
    当备份或恢复操作失败时抛出，如：
    - 备份文件创建失败
    - 恢复数据损坏
    - 备份版本不兼容
    
    Examples:
        >>> try:
        ...     # 备份操作
        ... except BackupError as e:
        ...     print(f"备份错误: {e}")
    """
    pass


class LockError(DatabaseError):
    """文件锁定错误。
    
    当文件锁定操作失败时抛出，如：
    - 无法获取锁
    - 锁超时
    - 死锁
    
    Examples:
        >>> try:
        ...     # 文件锁定
        ... except LockError as e:
        ...     print(f"锁定错误: {e}")
    """
    pass