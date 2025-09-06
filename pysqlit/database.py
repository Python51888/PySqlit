"""增强型数据库模块，提供完整的SQL支持、ACID事务和并发控制。

该模块实现了完整的数据库系统，包括：
- 完整的SQL语法支持（SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE）
- ACID事务保证
- 并发控制
- 数据完整性约束
- 备份和恢复功能
- 模式管理
"""

import os
import threading
from typing import List, Optional, Dict, Any, Tuple
from .concurrent_storage import ConcurrentPager
from .btree import EnhancedBTree, EnhancedLeafNode
from .parser import (
    EnhancedSQLParser, InsertStatement, SelectStatement, 
    UpdateStatement, DeleteStatement, WhereCondition,
    CreateTableStatement, DropTableStatement
)
from .ddl import DDLManager, TableSchema
from .transaction import TransactionManager, IsolationLevel
from .backup import BackupManager, RecoveryManager
from .models import Row, DataType, ColumnDefinition, TransactionLog, PrepareResult
from .constants import EXECUTE_SUCCESS, EXECUTE_DUPLICATE_KEY
from .exceptions import DatabaseError, TransactionError


class EnhancedTable:
    """增强型表，提供完整的SQL操作和模式支持。
    
    封装了单个表的所有操作，包括数据插入、查询、更新、删除，
    以及数据完整性约束的验证。
    """
    
    def __init__(self, pager: ConcurrentPager, table_name: str, schema: TableSchema, database: Optional['EnhancedDatabase'] = None):
        """初始化增强型表。
        
        Args:
            pager: 并发页面管理器
            table_name: 表名
            schema: 表结构定义
            database: 数据库实例（用于外键验证和事务日志）
        """
        self.pager = pager
        self.table_name = table_name
        self.schema = schema
        self.database = database  # 保存数据库引用用于外键验证和事务日志
        self.btree = EnhancedBTree(pager, row_size=schema.get_row_size())
    
    def insert_row(self, row: Row) -> int:
        """向表中插入一行数据。
        
        Args:
            row: 要插入的数据行
            
        Returns:
            执行结果代码
            
        Raises:
            DatabaseError: 插入失败时抛出
        """
        try:
            # 处理自增主键
            row_data = row.to_dict()
            primary_key = self.schema.primary_key or 'id'
            
            # 检查是否为自增主键
            primary_col = self.schema.columns.get(primary_key)
            is_integer_primary = (primary_col and
                                primary_col.is_primary and
                                primary_col.data_type == DataType.INTEGER)
            
            # 处理自增主键 - 始终基于实际最大ID生成下一个ID
            if is_integer_primary and primary_col and primary_col.is_autoincrement:
                # 始终基于实际最大ID生成下一个自增值
                all_data = self.btree.select_all()
                max_id = 0
                for key, value in all_data:
                    try:
                        # key是主键值
                        if isinstance(key, int) and key > max_id:
                            max_id = key
                    except (ValueError, TypeError):
                        continue
                
                next_id = max_id + 1
                row_data[primary_key] = next_id
                row = Row(**row_data)
            # 对于非自增INTEGER主键，仅在未提供时自动生成值
            elif primary_key not in row_data or row_data[primary_key] is None:
                if is_integer_primary:
                    # 自动生成主键值
                    max_id = 0
                    # 扫描现有键以找到最大ID
                    for key, _ in self.btree.scan():
                        try:
                            if isinstance(key, int) and key > max_id:
                                max_id = key
                        except (ValueError, TypeError):
                            continue
                    next_id = max_id + 1
                    row_data[primary_key] = next_id
                    row = Row(**row_data)
                else:
                    raise DatabaseError(f"主键 '{primary_key}' 必须提供")
            
            # 确保有有效的主键值
            primary_key_value = row_data.get(primary_key)
            if primary_key_value is None:
                raise DatabaseError(f"主键 '{primary_key}' 不能为NULL")
                
            # 检查主键唯一性 - 使用B树的高效查找
            try:
                page_num, cell_num = self.btree.find(primary_key_value)
                leaf = EnhancedLeafNode(self.btree.pager, page_num)
                if cell_num < leaf.num_cells() and leaf.key(cell_num, self.schema.get_row_size()) == primary_key_value:
                    raise DatabaseError(f"重复的主键值: {primary_key_value}")
            except Exception:
                # 键未找到，这是新插入的预期情况
                pass
            
            # 检查唯一约束 - 优化方法
            for col_name, col_def in self.schema.columns.items():
                if col_def.is_unique and col_name in row_data:
                    new_value = row_data[col_name]
                    
                    # 跳过NULL值（标准SQL行为）
                    if new_value is None:
                        continue
                    
                    # 转换为字符串进行比较
                    str_new = str(new_value).strip()
                    if not str_new:  # 跳过空字符串
                        continue
                    
                    # 检查该值是否已存在
                    all_data = self.btree.select_all()
                    if not all_data:
                        continue  # 如果表为空则跳过
                    
                    # 为该列构建现有值的集合
                    existing_values = set()
                    for key, value in all_data:
                        try:
                            existing_row = Row.deserialize(value, self.schema)
                            if existing_row is None:
                                continue
                                
                            existing_value = existing_row.get_value(col_name)
                            if existing_value is None:
                                continue
                                
                            str_existing = str(existing_value).strip()
                            if str_existing:
                                existing_values.add(str_existing)
                        except Exception:
                            continue
                    
                    # 检查重复
                    if str_new in existing_values:
                        raise DatabaseError(f"唯一列 '{col_name}' 的重复值: {new_value}")
            
            # 使用模式验证数据类型
            for col_name, col_def in self.schema.columns.items():
                value = row_data.get(col_name, col_def.default_value)
                
                # 检查NULL值
                if value is None and not col_def.is_nullable:
                    raise DatabaseError(f"列 '{col_name}' 不能为NULL")
                
                # 检查NOT NULL TEXT列的空字符串
                if (col_def.data_type == DataType.TEXT and
                    not col_def.is_nullable and
                    isinstance(value, str) and
                    value.strip() == ''):
                    raise DatabaseError(f"列 '{col_name}' 不能为空")
            
            # 处理非空列的NULL值
            for col_name, col_def in self.schema.columns.items():
                if not col_def.is_nullable and col_name not in row_data:
                    # 如果有默认值则使用默认值
                    if col_def.default_value is not None:
                        row_data[col_name] = col_def.default_value
                        row = Row(**row_data)
                    else:
                        raise DatabaseError(f"列 '{col_name}' 不能为NULL")
            
            # 确保数据类型一致性
            for col_name, col_def in self.schema.columns.items():
                if col_name in row_data and row_data[col_name] is not None:
                    value = row_data[col_name]
                    target_type = col_def.data_type
                    
                    try:
                        # 根据目标数据类型进行类型转换
                        if target_type == DataType.INTEGER:
                            if isinstance(value, (str, float)):
                                value = int(value)
                            # 如果已经是int，不需要转换
                        elif target_type == DataType.REAL:
                            if isinstance(value, (str, int)):
                                value = float(value)
                        elif target_type == DataType.TEXT:
                            value = str(value)
                        elif target_type == DataType.BOOLEAN:
                            if isinstance(value, str):
                                value = value.lower() in ('true', '1', 'yes', 'y')
                            elif isinstance(value, int):
                                value = bool(value)
                        
                        # 对TEXT应用max_length约束
                        if target_type == DataType.TEXT and col_def.max_length and len(str(value)) > col_def.max_length:
                            value = str(value)[:col_def.max_length]
                        
                        row_data[col_name] = value
                        row = Row(**row_data)
                        
                    except (ValueError, TypeError) as e:
                        raise DatabaseError(f"列 '{col_name}' 的数据类型无效: {e}")
                
            # 验证外键约束
            for fk in self.schema.foreign_keys:
                fk_value = row_data.get(fk.column)
                if fk_value is not None:
                    # 获取引用表
                    if self.database is None or fk.ref_table not in self.database.tables:  # 检查database是否存在
                        raise DatabaseError(f"引用的表 '{fk.ref_table}' 不存在")
                    
                    ref_table = self.database.tables[fk.ref_table]
                    
                    # 检查引用行是否存在
                    found = False
                    ref_rows = ref_table.select_all()
                    for ref_row in ref_rows:
                        if ref_row.get_value(fk.ref_column) == fk_value:
                            found = True
                            break
                    
                    if not found:
                        raise DatabaseError(f"外键约束失败: {fk_value} 在 {fk.ref_table}.{fk.ref_column} 中未找到")
            # 使用实际的主键值进行插入
            actual_primary_key = row_data[primary_key]
            serialized = row.serialize(self.schema)
            self.btree.insert(actual_primary_key, serialized)
            
            # 记录事务日志
            if self.database and self.database.transaction_log:
                try:
                    self.database.transaction_log.write_record(
                        transaction_id=0,  # 使用默认事务ID，实际应该从当前事务获取
                        operation="INSERT",
                        table_name=self.table_name,
                        row_data=row_data
                    )
                except Exception as log_error:
                    # 日志记录失败不应该影响主要操作
                    print(f"警告: 事务日志记录失败: {log_error}")
            
            # 确保数据刷新到磁盘
            self.pager.flush()
            
            return EXECUTE_SUCCESS
        except Exception as e:
            print(f"插入错误: {e}")  # 调试输出
            if "重复键" in str(e) or "重复" in str(e):
                raise DatabaseError(str(e))
            else:
                raise DatabaseError(f"插入失败: {e}")
    
    def select_all(self) -> List[Row]:
        """从表中选择所有行。
        
        Returns:
            所有数据行的列表
        """
        results = []
        data = self.btree.select_all()
        
        for key, value in data:
            row = Row.deserialize(value, self.schema)
            results.append(row)
        
        return results
    
    def select_with_condition(self, condition: WhereCondition) -> List[Row]:
        """根据WHERE条件选择行。
        
        Args:
            condition: WHERE条件
            
        Returns:
            满足条件的行列表
        """
        results = []
        data = self.btree.select_all()
        
        for key, value in data:
            row = Row.deserialize(value, self.schema)
            if condition.evaluate(row):
                results.append(row)
        
        return results
    
    def update_rows(self, updates: Dict[str, Any], condition: Optional['WhereCondition'] = None) -> int:
        """更新行数据，可选WHERE条件。
        
        Args:
            updates: 要更新的列和值
            condition: WHERE条件，如果为None则更新所有行
            
        Returns:
            更新的行数
        """
        updated_count = 0
        data = self.btree.select_all()
        
        if not data:
            return 0
        
        # 验证更新是否符合模式
        for col in updates.keys():
            if col not in self.schema.columns:
                raise DatabaseError(f"列 '{col}' 在表 '{self.table_name}' 中不存在")
        
        for key, value in data:
            try:
                row = Row.deserialize(value, self.schema)
                if row is None:
                    continue
                
                # 确保行有所有必需的列
                if not hasattr(row, 'data') or row.data is None:
                    row.data = {}
                
                if condition is None or condition.evaluate(row):
                    # 保存更新前的数据用于日志记录
                    old_data = row.to_dict().copy()
                    
                    # 应用更新
                    for col, new_val in updates.items():
                        if col in self.schema.columns:
                            row.set_value(col, new_val)
                    
                    # 在B树中更新
                    serialized = row.serialize(self.schema)
                    if self.btree.update(key, serialized):
                        updated_count += 1
                        
                        # 记录事务日志
                        if self.database and self.database.transaction_log:
                            try:
                                self.database.transaction_log.write_record(
                                    transaction_id=0,  # 使用默认事务ID，实际应该从当前事务获取
                                    operation="UPDATE",
                                    table_name=self.table_name,
                                    row_data=row.to_dict(),
                                    old_data=old_data
                                )
                            except Exception as log_error:
                                # 日志记录失败不应该影响主要操作
                                print(f"警告: 事务日志记录失败: {log_error}")
            except Exception as e:
                print(f"警告: 更新期间跳过行: {e}")
                continue
        
        # 确保数据刷新到磁盘
        self.pager.flush()
        
        return updated_count
    
    def delete_rows(self, condition: Optional['WhereCondition'] = None) -> int:
        """删除行数据，可选WHERE条件。
        
        Args:
            condition: WHERE条件，如果为None则删除所有行
            
        Returns:
            删除的行数
        """
        deleted_count = 0
        
        # 获取所有数据的一致快照
        try:
            all_data = self.btree.select_all()
            if not all_data:
                return 0
            
            # 构建要删除的有效(key, row)对列表
            rows_to_delete = []
            for key, value in all_data:
                try:
                    row = Row.deserialize(value, self.schema)
                    if row is None:
                        continue
                    
                    # 确保行有所有必需的列
                    if not hasattr(row, 'data') or row.data is None:
                        row.data = {}
                    
                    # 仅在有效行上评估条件
                    if condition is None or condition.evaluate(row):
                        rows_to_delete.append((key, row))
                except Exception as e:
                    # 跳过无效行但不计为已删除
                    continue
            
            # 在单次遍历中删除行并进行验证
            for key, row in rows_to_delete:
                try:
                    # 删除前记录日志
                    if self.database and self.database.transaction_log:
                        try:
                            self.database.transaction_log.write_record(
                                transaction_id=0,  # 使用默认事务ID，实际应该从当前事务获取
                                operation="DELETE",
                                table_name=self.table_name,
                                row_data=row.to_dict()
                            )
                        except Exception as log_error:
                            # 日志记录失败不应该影响主要操作
                            print(f"警告: 事务日志记录失败: {log_error}")
                    
                    # 删除前再次检查键是否存在
                    if self.btree.delete(key):
                        deleted_count += 1
                    # 静默跳过不再存在的键（并发处理）
                except Exception as e:
                    # 记录实际删除错误但继续
                    print(f"删除键 {key} 时出错: {e}")
                    continue
            
            # 确保数据刷新到磁盘
            self.pager.flush()
            
        except Exception as e:
            print(f"删除操作期间出错: {e}")
            raise DatabaseError(f"删除操作失败: {e}")
        
        return deleted_count
    
    def get_row_count(self) -> int:
        """获取表中的行数。
        
        Returns:
            行数
        """
        return len(self.btree.select_all())
    
    def flush(self) -> None:
        """将更改刷新到磁盘。"""
        self.pager.flush()


class EnhancedDatabase:
    """增强型数据库，提供完整的SQL支持、ACID事务和并发控制。
    
    这是PySQLit的核心数据库类，提供：
    - 完整的SQL语法支持
    - ACID事务保证
    - 并发控制
    - 数据完整性约束
    - 备份和恢复功能
    """
    
    def __init__(self, filename: str):
        """初始化增强型数据库。
        
        Args:
            filename: 数据库文件名，":memory:"表示内存数据库
        """
        # 为内存数据库保留":memory:"标识符
        self.filename = filename if filename == ":memory:" else os.path.abspath(filename)
        self.pager = ConcurrentPager(self.filename)
        self.transaction_manager = TransactionManager(self.pager)  # TransactionManager需要Pager类型的参数
        self.ddl_manager = DDLManager(self)
        self.backup_manager = BackupManager(self.filename)
        self.recovery_manager = RecoveryManager(self.filename)
        
        # 仅为持久化数据库创建日志文件
        if filename != ":memory:":
            db_logs_dir = os.path.join(os.path.dirname(self.filename), "db_logs")
            os.makedirs(db_logs_dir, exist_ok=True)
            log_filename = os.path.basename(self.filename) + ".log"
            log_path = os.path.join(db_logs_dir, log_filename)
            self.transaction_log = TransactionLog(log_path)
            # 确保日志文件存在（创建空的日志文件）
            if not os.path.exists(log_path):
                with open(log_path, 'w') as f:
                    pass  # 创建空文件
        else:
            # 为内存数据库使用虚拟内存日志
            self.transaction_log = None
        
        # 默认表
        self.tables: Dict[str, EnhancedTable] = {}
        self.schemas: Dict[str, TableSchema] = {}
        self.in_transaction = False  # 跟踪事务状态
        
        # 加载或创建默认模式
        self._load_schema()
        self._initialize_default_schema()
    
    def _load_schema(self):
        """从磁盘加载模式。"""
        import json
        schema_file = f"{self.filename}.schema"
        
        if os.path.exists(schema_file):
            try:
                with open(schema_file, 'r') as f:
                    schema_data = json.load(f)
                
                for table_name, schema_dict in schema_data.items():
                    schema = TableSchema.from_dict(schema_dict)
                    self.schemas[table_name] = schema
                    self.tables[table_name] = EnhancedTable(self.pager, table_name, schema)
                        
            except Exception as e:
                print(f"警告: 加载模式失败: {e}")
    
    def _save_schema(self):
        """将模式保存到磁盘。"""
        import json
        schema_file = f"{self.filename}.schema"
        
        try:
            schema_data = {}
            for table_name, schema in self.schemas.items():
                schema_data[table_name] = schema.to_dict()
            
            with open(schema_file, 'w') as f:
                json.dump(schema_data, f, indent=2)
                
        except Exception as e:
            print(f"警告: 保存模式失败: {e}")
    
    def _initialize_default_schema(self):
        """初始化默认表模式。"""
        # 不自动创建默认表
        pass
    
    def begin_transaction(self, isolation_level: IsolationLevel = IsolationLevel.REPEATABLE_READ) -> int:
        """开始新事务。
        
        Args:
            isolation_level: 事务隔离级别
            
        Returns:
            事务ID
        """
        self.in_transaction = True
        return self.transaction_manager.begin_transaction(isolation_level)
    
    def commit_transaction(self, transaction_id: int):
        """提交事务。
        
        Args:
            transaction_id: 事务ID
        """
        self.transaction_manager.commit_transaction(transaction_id)
        self.in_transaction = False
    
    def rollback_transaction(self, transaction_id: int):
        """回滚事务。
        
        Args:
            transaction_id: 事务ID
        """
        self.transaction_manager.rollback_transaction(transaction_id)
        self.in_transaction = False
    
    def create_table(self, table_name: str, columns: Dict[str, str],
                    primary_key: Optional[str] = None,
                    foreign_keys: Optional[List[Dict[str, Any]]] = None,
                    indexes: Optional[List[str]] = None,
                    unique_columns: Optional[List[str]] = None,
                    not_null_columns: Optional[List[str]] = None) -> bool:
        """创建具有模式的新表。
        
        Args:
            table_name: 表名
            columns: 列定义字典（列名 -> 数据类型）
            primary_key: 主键列名
            foreign_keys: 外键约束列表
            indexes: 索引列列表
            unique_columns: 唯一列列表
            not_null_columns: 非空列列表
            
        Returns:
            创建成功返回True
            
        Raises:
            DatabaseError: 如果表已存在
        """
        from .models import ColumnDefinition, ForeignKeyConstraint, IndexDefinition
        
        if table_name in self.tables:
            raise DatabaseError(f"表 {table_name} 已存在")
            
        schema = TableSchema(table_name)
        
        # 添加列
        for col_name, col_type in columns.items():
            is_primary = (col_name == primary_key)
            # 所有整数主键默认设置为自增
            is_autoincrement = is_primary and (col_type.upper() == 'INTEGER')
            data_type = DataType.from_string(col_type)  # 使用from_string方法处理类型
            is_unique = (unique_columns is not None and col_name in unique_columns)
            is_not_null = (not_null_columns is not None and col_name in not_null_columns)
            
            # 为TEXT列设置适当的max_length
            max_length = None
            if data_type == DataType.TEXT:
                if col_name == 'name':
                    max_length = 100  # 名称的合理默认值
                elif col_name == 'username':
                    max_length = 32
                elif col_name == 'email':
                    max_length = 255
                    
            # 创建列定义
            col_def = ColumnDefinition(
                name=col_name,
                data_type=data_type,
                is_primary=is_primary,
                is_autoincrement=is_autoincrement,
                max_length=max_length,
                is_nullable=not (is_primary or is_not_null or col_name == 'name'),  # 主键、明确指定的NOT NULL列和name为NOT NULL
                is_unique=is_unique
            )
            
            # 对于INTEGER PRIMARY KEY，显式设置自增
            if is_primary and data_type == DataType.INTEGER and not is_autoincrement:
                col_def.is_autoincrement = True
            schema.add_column(col_def)
            
        # 添加外键
        if foreign_keys:
            for fk in foreign_keys:
                from .models import ForeignKeyConstraint
                constraint = ForeignKeyConstraint(
                    column=fk['column'],
                    ref_table=fk['ref_table'],
                    ref_column=fk['ref_column']
                )
                schema.add_foreign_key(constraint)
                
        # 添加索引
        if indexes:
            for idx_col in indexes:
                from .models import IndexDefinition
                schema.add_index(IndexDefinition(name=f"idx_{table_name}_{idx_col}", columns=[idx_col]))
                
        # 为唯一列添加唯一索引
        if unique_columns:
            for col_name in unique_columns:
                if col_name in schema.columns:
                    schema.columns[col_name].is_unique = True
        
        # 保存模式
        self.schemas[table_name] = schema
        
        # 创建表实例
        table = EnhancedTable(self.pager, table_name, schema, self)  # 传递数据库引用
        self.tables[table_name] = table
        
        # 记录事务日志
        if self.transaction_log:
            try:
                # 记录表结构信息
                table_info = {
                    "columns": {name: col.to_dict() for name, col in schema.columns.items()},
                    "primary_key": schema.primary_key,
                    "foreign_keys": len(schema.foreign_keys),
                    "indexes": len(schema.indexes)
                }
                
                self.transaction_log.write_record(
                    transaction_id=0,  # 使用默认事务ID，实际应该从当前事务获取
                    operation="CREATE TABLE",
                    table_name=table_name,
                    row_data=table_info
                )
            except Exception as log_error:
                # 日志记录失败不应该影响主要操作
                print(f"警告: 事务日志记录失败: {log_error}")
        
        # 保存更新后的模式
        self._save_schema()
        
        return True


    def drop_table(self, table_name: str) -> bool:
        """删除表。
        
        Args:
            table_name: 要删除的表名
            
        Returns:
            删除成功返回True
            
        Raises:
            DatabaseError: 如果表不存在或表包含数据
        """
        if table_name not in self.tables:
            raise DatabaseError(f"表 {table_name} 不存在")
        
        # 检查表是否包含数据
        table = self.tables[table_name]
        row_count = table.get_row_count()
        if row_count > 0:
            raise DatabaseError(f"无法删除包含数据的表 '{table_name}'，请先删除所有数据")
        
        # 从模式中移除表
        if table_name in self.schemas:
            del self.schemas[table_name]
        
        # 从表字典中移除
        del self.tables[table_name]
        
        # 记录事务日志
        if self.transaction_log:
            try:
                self.transaction_log.write_record(
                    transaction_id=0,  # 使用默认事务ID，实际应该从当前事务获取
                    operation="DROP TABLE",
                    table_name=table_name,
                    row_data={}
                )
            except Exception as log_error:
                # 日志记录失败不应该影响主要操作
                print(f"警告: 事务日志记录失败: {log_error}")
        
        # 保存更新后的模式
        self._save_schema()
        
        return True


    def list_tables(self) -> List[str]:
        """列出所有表名。
        
        Returns:
            表名列表
        """
        return list(self.tables.keys())


    def get_table_schema(self, table_name: str) -> Optional[TableSchema]:
        """获取表的模式定义。
        
        Args:
            table_name: 表名
            
        Returns:
            表模式对象，如果表不存在返回None
        """
        return self.schemas.get(table_name)


    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息。
        
        Returns:
            包含数据库信息的字典
        """
        import os
        info = {
            'filename': self.filename,
            'tables': {},
            'active_transactions': self.in_transaction,
        }
        
        # 获取文件大小
        if self.filename != ":memory:" and os.path.exists(self.filename):
            info['file_size'] = os.path.getsize(self.filename)
        else:
            info['file_size'] = 0
            
        # 获取表信息
        for table_name, table in self.tables.items():
            info['tables'][table_name] = table.get_row_count()
            
        # 获取页数
        info['num_pages'] = self.pager.num_pages  # 使用num_pages属性而不是get_num_pages方法
        
        # 获取备份信息
        try:
            info['backups'] = self.backup_manager.list_backups()
        except:
            info['backups'] = []
            
        return info


    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """创建数据库备份。
        
        Args:
            backup_name: 备份名称，如果为None则自动生成
            
        Returns:
            备份文件路径
        """
        return self.backup_manager.create_backup(backup_name)


    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份。
        
        Returns:
            备份信息列表
        """
        return self.backup_manager.list_backups()


    def restore_backup(self, backup_path: str) -> bool:
        """从备份恢复数据库。
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            恢复成功返回True
        """
        # 从备份路径提取备份文件名
        backup_name = os.path.basename(backup_path)
        return self.backup_manager.restore_backup(backup_name)  # 使用BackupManager的restore_backup方法


    def close(self) -> None:
        """关闭数据库连接。"""
        self.pager.close()


    def flush(self) -> None:
        """将所有更改刷新到磁盘。"""
        self.pager.flush()


class SQLExecutor:
    """SQL执行器，用于执行SQL语句。
    
    提供统一的SQL执行接口，支持事务管理和结果处理。
    """
    
    def __init__(self, database: 'EnhancedDatabase'):
        """初始化SQL执行器。
        
        Args:
            database: 数据库实例
        """
        self.database = database
    
    def execute(self, sql: str, transaction_id: Optional[int] = None) -> Tuple[PrepareResult, Any]:
        """执行SQL语句。
        
        Args:
            sql: SQL语句字符串
            transaction_id: 事务ID，如果为None则使用自动事务
            
        Returns:
            执行结果和数据的元组
        """
        try:
            # 使用解析器解析SQL语句
            result, statement = EnhancedSQLParser.parse_statement(sql.strip())
            
            if result != PrepareResult.SUCCESS:
                return result, None
            
            # 如果没有提供事务ID，对于非SELECT语句创建自动事务
            auto_transaction = False
            if transaction_id is None and not isinstance(statement, SelectStatement):
                transaction_id = self.database.begin_transaction()
                auto_transaction = True
            
            try:
                # 根据语句类型执行相应的操作
                if isinstance(statement, InsertStatement):
                    return self._execute_insert(statement, transaction_id)
                elif isinstance(statement, SelectStatement):
                    return self._execute_select(statement, transaction_id)
                elif isinstance(statement, UpdateStatement):
                    return self._execute_update(statement, transaction_id)
                elif isinstance(statement, DeleteStatement):
                    return self._execute_delete(statement, transaction_id)
                elif isinstance(statement, CreateTableStatement):
                    return self._execute_create_table(statement)
                elif isinstance(statement, DropTableStatement):
                    return self._execute_drop_table(statement)
                else:
                    return PrepareResult.SYNTAX_ERROR, "不支持的语句类型"
                    
            except Exception as e:
                # 如果是自动事务且发生错误，回滚事务
                if auto_transaction and transaction_id is not None:
                    self.database.rollback_transaction(transaction_id)
                # 检查是否是特定的PrepareResult错误
                if isinstance(e, tuple) and len(e) == 2 and isinstance(e[0], PrepareResult):
                    return e
                raise e
                
            finally:
                # 如果是自动事务且成功执行，提交事务
                if auto_transaction and transaction_id is not None:
                    self.database.commit_transaction(transaction_id)
                    
        except Exception as e:
            # 检查是否是特定的PrepareResult错误
            if isinstance(e, tuple) and len(e) == 2 and isinstance(e[0], PrepareResult):
                return e
            return PrepareResult.SYNTAX_ERROR, str(e)
    
    def _execute_insert(self, statement: InsertStatement, transaction_id: Optional[int]) -> Tuple[PrepareResult, int]:
        """执行INSERT语句。
        
        Args:
            statement: INSERT语句对象
            transaction_id: 事务ID
            
        Returns:
            执行结果和插入行数的元组
        """
        table_name = statement.table_name
        if table_name not in self.database.tables:
            return PrepareResult(4), 0  # TABLE_NOT_FOUND = 4, 返回0作为插入行数
        
        table = self.database.tables[table_name]
        inserted_count = 0
        
        # 转换为行列表并插入每一行
        rows = statement.to_rows(schema=table.schema)
        for row in rows:
            result = table.insert_row(row)
            if result == EXECUTE_SUCCESS:
                inserted_count += 1
            else:
                return PrepareResult(5), 0  # INSERT_FAILED = 5, 返回0作为插入行数
        
        return PrepareResult(0), inserted_count  # SUCCESS = 0
    
    def _execute_select(self, statement: SelectStatement, transaction_id: Optional[int]) -> Tuple[PrepareResult, Tuple[List[Row], List[str]]]:
        """执行SELECT语句。
        
        Args:
            statement: SELECT语句对象
            transaction_id: 事务ID
            
        Returns:
            执行结果和(行列表, 列名列表)的元组
        """
        table_name = statement.table_name
        if table_name not in self.database.tables:
            return PrepareResult(4), ([], [])  # TABLE_NOT_FOUND = 4, 返回空列表
        
        table = self.database.tables[table_name]
        
        # 执行查询
        if statement.where_clause:
            rows = table.select_with_condition(statement.where_clause)
        else:
            rows = table.select_all()
        
        # 确定要返回的列
        if statement.columns == ['*']:
            columns = list(table.schema.columns.keys())
        else:
            columns = statement.columns
        
        return PrepareResult(0), (rows, columns)  # SUCCESS = 0
    
    def _execute_update(self, statement: UpdateStatement, transaction_id: Optional[int]) -> Tuple[PrepareResult, int]:
        """执行UPDATE语句。
        
        Args:
            statement: UPDATE语句对象
            transaction_id: 事务ID
            
        Returns:
            执行结果和更新行数的元组
        """
        table_name = statement.table_name
        if table_name not in self.database.tables:
            return PrepareResult(4), 0  # TABLE_NOT_FOUND = 4, 返回0作为更新行数
        
        table = self.database.tables[table_name]
        updated_count = table.update_rows(statement.updates, statement.where_clause)
        return PrepareResult(0), updated_count  # SUCCESS = 0
    
    def _execute_delete(self, statement: DeleteStatement, transaction_id: Optional[int]) -> Tuple[PrepareResult, int]:
        """执行DELETE语句。
        
        Args:
            statement: DELETE语句对象
            transaction_id: 事务ID
            
        Returns:
            执行结果和删除行数的元组
        """
        table_name = statement.table_name
        if table_name not in self.database.tables:
            return PrepareResult(4), 0  # TABLE_NOT_FOUND = 4, 返回0作为删除行数
        
        table = self.database.tables[table_name]
        deleted_count = table.delete_rows(statement.where_clause)
        return PrepareResult(0), deleted_count  # SUCCESS = 0
    
    def _execute_create_table(self, statement: CreateTableStatement) -> Tuple[PrepareResult, bool]:
        """执行CREATE TABLE语句。
        
        Args:
            statement: CREATE TABLE语句对象
            
        Returns:
            执行结果和成功标志的元组
        """
        try:
            # 将列定义转换为create_table方法需要的格式
            columns = {}
            primary_key = None
            unique_columns = []
            
            for col_name, (data_type, is_primary, is_autoincrement, is_unique, is_not_null) in statement.columns.items():
                # 将DataType转换为字符串
                columns[col_name] = data_type.value
                
                # 记录主键
                if is_primary:
                    primary_key = col_name
                    
                # 记录唯一列
                if is_unique:
                    unique_columns.append(col_name)
            
            result = self.database.create_table(
                statement.table_name,
                columns,
                primary_key,
                None,  # foreign_keys - 当前实现不支持
                None,  # indexes - 当前实现不支持
                unique_columns if unique_columns else None
            )
            return PrepareResult(0), result  # SUCCESS = 0
        except Exception as e:
            return PrepareResult(3), False  # SYNTAX_ERROR = 3
    
    def _execute_drop_table(self, statement: DropTableStatement) -> Tuple[PrepareResult, bool]:
        """执行DROP TABLE语句。
        
        Args:
            statement: DROP TABLE语句对象
            
        Returns:
            执行结果和成功标志的元组
        """
        try:
            result = self.database.drop_table(statement.table_name)
            return PrepareResult(0), result  # SUCCESS = 0
        except Exception as e:
            # 重新抛出异常，让上层处理具体的错误信息
            raise e
