"""增强版数据文件操作接口，提供对数据文件的完整数据库操作支持。

这个模块提供了一个高级接口，用于对数据文件执行完整的数据库操作，
包括创建、读取、更新、删除等操作，以及事务管理和备份恢复功能。

主要特性：
1. 完整的CRUD操作支持
2. 事务管理
3. 数据导入/导出（JSON, CSV, XML, Excel等）
4. 备份和恢复
5. 模式管理
6. 查询优化
7. 数据验证和约束检查
8. 批量操作支持
9. 索引管理
10. 数据库链接和复制
"""

import os
import json
import csv
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from .database import EnhancedDatabase, SQLExecutor
from .models import Row, DataType, TableSchema, ColumnDefinition
from .exceptions import DatabaseError
from .transaction import IsolationLevel
from .backup import BackupManager
from .constants import EXECUTE_SUCCESS


class EnhancedDataFile:
    """增强版数据文件操作类，提供对数据文件的完整数据库操作支持。

    这个类封装了EnhancedDatabase的功能，提供了一个更高级的接口用于操作数据文件。
    支持多种数据格式（JSON, CSV, XML, Excel等）的导入和导出。

    Examples:
        >>> # 创建数据文件操作对象
        >>> edf = EnhancedDataFile("example.db")
        >>> 
        >>> # 创建表
        >>> edf.create_table("users", {
        ...     "id": "INTEGER",
        ...     "name": "TEXT",
        ...     "email": "TEXT"
        ... }, primary_key="id")
        >>> 
        >>> # 插入数据
        >>> edf.insert("users", {"id": 1, "name": "张三", "email": "zhangsan@example.com"})
        >>> 
        >>> # 查询数据
        >>> users = edf.select("users")
        >>> print(users)
        >>> 
        >>> # 更新数据
        >>> edf.update("users", {"name": "李四"}, where="id = 1")
        >>> 
        >>> # 删除数据
        >>> edf.delete("users", where="id = 1")
    """

    def __init__(self, filename: str, auto_commit: bool = True):
        """初始化增强版数据文件操作对象。

        Args:
            filename: 数据库文件名，":memory:"表示内存数据库
            auto_commit: 是否自动提交事务
        """
        # 确保文件名是绝对路径，以保证日志文件在正确的目录中创建
        if filename != ":memory:":
            self.filename = os.path.abspath(filename)
        else:
            self.filename = filename
        self.auto_commit = auto_commit
        self.db = EnhancedDatabase(self.filename)
        self.executor = SQLExecutor(self.db)
        self.current_transaction = None

    def begin_transaction(self, isolation_level: IsolationLevel = IsolationLevel.REPEATABLE_READ) -> int:
        """开始新事务。

        Args:
            isolation_level: 事务隔离级别

        Returns:
            事务ID
        """
        if self.current_transaction is not None:
            raise DatabaseError("事务已在进行中")
        
        transaction_id = self.db.begin_transaction(isolation_level)
        self.current_transaction = transaction_id
        return transaction_id

    def commit_transaction(self):
        """提交当前事务。"""
        if self.current_transaction is None:
            raise DatabaseError("没有活动的事务")
        
        self.db.commit_transaction(self.current_transaction)
        self.current_transaction = None

    def rollback_transaction(self):
        """回滚当前事务。"""
        if self.current_transaction is None:
            raise DatabaseError("没有活动的事务")
        
        self.db.rollback_transaction(self.current_transaction)
        self.current_transaction = None

    def create_table(self, table_name: str, columns: Dict[str, str],
                     primary_key: Optional[str] = None,
                     foreign_keys: Optional[List[Dict[str, Any]]] = None,
                     indexes: Optional[List[str]] = None,
                     unique_columns: Optional[List[str]] = None,
                     not_null_columns: Optional[List[str]] = None) -> bool:
        """创建表。

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

        Examples:
            >>> edf.create_table("users", {
            ...     "id": "INTEGER",
            ...     "name": "TEXT",
            ...     "email": "TEXT"
            ... }, primary_key="id", unique_columns=["email"], not_null_columns=["name"])
            True
        """
        return self.db.create_table(
            table_name=table_name,
            columns=columns,
            primary_key=primary_key,
            foreign_keys=foreign_keys,
            indexes=indexes,
            unique_columns=unique_columns,
            not_null_columns=not_null_columns
        )

    def drop_table(self, table_name: str) -> bool:
        """删除表。

        Args:
            table_name: 要删除的表名

        Returns:
            删除成功返回True

        Raises:
            DatabaseError: 如果表不存在或删除失败
        """
        return self.db.drop_table(table_name)

    def alter_table(self, table_name: str, action: str, column_name: str, 
                    column_type: Optional[str] = None) -> bool:
        """修改表结构。

        Args:
            table_name: 表名
            action: 操作类型 ("ADD", "DROP", "MODIFY")
            column_name: 列名
            column_type: 列类型（仅在ADD和MODIFY时需要）

        Returns:
            修改成功返回True
        """
        if action.upper() == "ADD":
            if not column_type:
                raise DatabaseError("添加列时必须指定列类型")
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        elif action.upper() == "DROP":
            sql = f"ALTER TABLE {table_name} DROP COLUMN {column_name}"
        elif action.upper() == "MODIFY":
            if not column_type:
                raise DatabaseError("修改列时必须指定列类型")
            sql = f"ALTER TABLE {table_name} MODIFY COLUMN {column_name} {column_type}"
        else:
            raise DatabaseError(f"不支持的操作类型: {action}")
        
        result, _ = self.executor.execute(sql)
        return result.value == 0  # SUCCESS = 0

    def insert(self, table_name: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> int:
        """插入数据。

        Args:
            table_name: 表名
            data: 要插入的数据字典或数据字典列表

        Returns:
            插入成功的行数

        Examples:
            >>> # 插入单行数据
            >>> edf.insert("users", {"id": 1, "name": "张三", "email": "zhangsan@example.com"})
            1
            >>> 
            >>> # 插入多行数据
            >>> edf.insert("users", [
            ...     {"id": 2, "name": "李四", "email": "lisi@example.com"},
            ...     {"id": 3, "name": "王五", "email": "wangwu@example.com"}
            ... ])
            2
        """
        # 开始事务（如果需要）
        auto_transaction = False
        if self.auto_commit and self.current_transaction is None:
            self.begin_transaction()
            auto_transaction = True

        try:
            # 确保data是列表格式
            if isinstance(data, dict):
                data_list = [data]
            else:
                data_list = data

            inserted_count = 0
            for row_data in data_list:
                # 获取表模式以进行数据类型转换
                table = self.db.tables[table_name]
                schema = table.schema
                
                # 转换数据类型以匹配表模式
                converted_data = {}
                for col_name, value in row_data.items():
                    if col_name in schema.columns:
                        col_def = schema.columns[col_name]
                        target_type = col_def.data_type
                        
                        # 根据目标数据类型进行类型转换
                        try:
                            if target_type == DataType.INTEGER:
                                if value is not None and value != '':
                                    converted_data[col_name] = int(value)
                                else:
                                    converted_data[col_name] = None
                            elif target_type == DataType.REAL:
                                if value is not None and value != '':
                                    converted_data[col_name] = float(value)
                                else:
                                    converted_data[col_name] = None
                            elif target_type == DataType.TEXT:
                                converted_data[col_name] = str(value) if value is not None else None
                            elif target_type == DataType.BOOLEAN:
                                if isinstance(value, str):
                                    converted_data[col_name] = value.lower() in ('true', '1', 'yes', 'y')
                                else:
                                    converted_data[col_name] = bool(value)
                            else:
                                # 对于其他类型，转换为字符串
                                converted_data[col_name] = str(value) if value is not None else None
                        except (ValueError, TypeError):
                            # 如果转换失败，保持原始值并让数据库处理错误
                            converted_data[col_name] = value
                    else:
                        # 列不在模式中，保持原始值
                        converted_data[col_name] = value
                
                # 使用转换后的数据创建行对象并插入
                result = table.insert_row(Row(**converted_data))
                
                if result == EXECUTE_SUCCESS:
                    inserted_count += 1
                else:
                    raise DatabaseError(f"插入失败: {result}")

            # 自动提交事务
            if auto_transaction:
                self.commit_transaction()

            return inserted_count

        except Exception as e:
            # 自动回滚事务
            if auto_transaction:
                self.rollback_transaction()
            raise e

    def batch_insert(self, table_name: str, data: List[Dict[str, Any]], 
                     batch_size: int = 1000) -> int:
        """批量插入数据。

        Args:
            table_name: 表名
            data: 要插入的数据字典列表
            batch_size: 批处理大小

        Returns:
            插入成功的行数
        """
        total_inserted = 0
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            inserted = self.insert(table_name, batch)
            total_inserted += inserted
        return total_inserted

    def select(self, table_name: str, columns: Optional[List[str]] = None,
               where: Optional[str] = None, order_by: Optional[str] = None,
               limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """查询数据。

        Args:
            table_name: 表名
            columns: 要查询的列列表，None表示所有列
            where: WHERE条件字符串
            order_by: ORDER BY子句
            limit: LIMIT子句

        Returns:
            查询结果列表，每个元素是一个字典

        Examples:
            >>> edf.select("users", ["id", "name"])
            [{'id': 1, 'name': '张三'}]
            >>> edf.select("users", where="id = 1")
            [{'id': 1, 'name': '张三', 'email': 'zhangsan@example.com'}]
            >>> edf.select("users", order_by="name", limit=10)
            [{'id': 2, 'name': '李四', 'email': 'lisi@example.com'}, ...]
        """
        # 如果columns包含别名表达式，使用原始SQL执行
        if columns:
            # 检查是否有别名（包含AS关键字或空格分隔的别名）
            has_alias = False
            for col in columns:
                # 检查是否包含AS关键字或空格分隔的别名
                if (' AS ' in col.upper() or ' as ' in col.lower() or 
                    (len(col.split()) > 1 and not col.startswith("'") and not col.startswith('"'))):
                    has_alias = True
                    break
            
            if has_alias:
                # 构造带别名的SQL语句
                cols_str = ", ".join(columns)
                sql = f"SELECT {cols_str} FROM {table_name}"
                if where:
                    sql += f" WHERE {where}"
                if order_by:
                    sql += f" ORDER BY {order_by}"
                if limit is not None:
                    sql += f" LIMIT {limit}"
                
                # 执行SQL并返回结果
                result, data = self.executor.execute(sql)
                if result.value != 0:  # SUCCESS = 0
                    # 打印SQL语句以便调试
                    print(f"执行SQL出错: {sql}")
                    raise DatabaseError(f"查询失败: {result}")
                
                # 确保返回正确的类型
                if isinstance(data, list):
                    return data
                
                # 如果data是其他格式，返回空列表
                return []
        
        # 构造标准SELECT SQL语句
        cols = "*" if columns is None else ", ".join(columns)
        sql = f"SELECT {cols} FROM {table_name}"
        if where:
            sql += f" WHERE {where}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit is not None:
            sql += f" LIMIT {limit}"
        
        # 执行SQL
        result, data = self.executor.execute(sql)
        
        if result.value != 0:  # SUCCESS = 0
            # 打印SQL语句以便调试
            print(f"执行SQL出错: {sql}")
            raise DatabaseError(f"查询失败: {result}")
        
        # 确保返回正确的类型
        if isinstance(data, list):
            return data
        
        # 如果data是其他格式，返回空列表
        return []

    def select_with_join(self, tables: List[str], columns: Optional[List[str]] = None,
                         join_conditions: Optional[List[str]] = None,
                         where: Optional[str] = None, order_by: Optional[str] = None,
                         limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """多表连接查询数据。

        Args:
            tables: 表名列表
            columns: 要查询的列列表，None表示所有列
            join_conditions: JOIN条件列表
            where: WHERE条件字符串
            order_by: ORDER BY子句
            limit: LIMIT子句

        Returns:
            查询结果列表，每个元素是一个字典
        """
        # 构造SELECT SQL语句
        cols = "*" if columns is None else ", ".join(columns)
        table_str = ", ".join(tables)
        sql = f"SELECT {cols} FROM {table_str}"
        
        if join_conditions:
            for condition in join_conditions:
                sql += f" {condition}"
        
        if where:
            sql += f" WHERE {where}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit:
            sql += f" LIMIT {limit}"
        
        # 执行SQL
        result, data = self.executor.execute(sql)
        
        if result.value != 0:  # SUCCESS = 0
            raise DatabaseError(f"查询失败: {result}")
        
        # 确保返回正确的类型
        if isinstance(data, list):
            return data
        
        # 如果data是其他格式，返回空列表
        return []

    def update(self, table_name: str, updates: Dict[str, Any],
               where: Optional[str] = None) -> int:
        """更新数据。

        Args:
            table_name: 表名
            updates: 更新字典（列名 -> 新值）
            where: WHERE条件字符串，None表示更新所有行

        Returns:
            更新的行数

        Examples:
            >>> edf.update("users", {"name": "李四"}, "id = 1")
            1
        """
        # 开始事务（如果需要）
        auto_transaction = False
        if self.auto_commit and self.current_transaction is None:
            self.begin_transaction()
            auto_transaction = True

        try:
            # 构造UPDATE SQL语句
            set_parts = []
            for col, value in updates.items():
                if value is None:
                    set_parts.append(f"{col} = NULL")
                elif isinstance(value, str):
                    # 转义单引号
                    escaped = value.replace("'", "''")
                    set_parts.append(f"{col} = '{escaped}'")
                else:
                    set_parts.append(f"{col} = {value}")
            
            set_str = ", ".join(set_parts)
            sql = f"UPDATE {table_name} SET {set_str}"
            if where:
                sql += f" WHERE {where}"
            
            # 执行SQL
            result, count = self.executor.execute(sql)
            
            if result.value != 0:  # SUCCESS = 0
                raise DatabaseError(f"更新失败: {result}")

            # 自动提交事务
            if auto_transaction:
                self.commit_transaction()
                
            return count

        except Exception as e:
            # 自动回滚事务
            if auto_transaction:
                self.rollback_transaction()
            raise e

    def delete(self, table_name: str, where: Optional[str] = None) -> int:
        """删除数据。

        Args:
            table_name: 表名
            where: WHERE条件字符串，None表示删除所有行

        Returns:
            删除的行数

        Examples:
            >>> edf.delete("users", "id = 1")
            1
        """
        # 开始事务（如果需要）
        auto_transaction = False
        if self.auto_commit and self.current_transaction is None:
            self.begin_transaction()
            auto_transaction = True

        try:
            # 构造DELETE SQL语句
            sql = f"DELETE FROM {table_name}"
            if where:
                sql += f" WHERE {where}"
            
            # 执行SQL
            result, count = self.executor.execute(sql)
            
            if result.value != 0:  # SUCCESS = 0
                raise DatabaseError(f"删除失败: {result}")

            # 自动提交事务
            if auto_transaction:
                self.commit_transaction()
                
            return count

        except Exception as e:
            # 自动回滚事务
            if auto_transaction:
                self.rollback_transaction()
            raise e

    def execute_sql(self, sql: str) -> Tuple[Any, Any]:
        """执行原始SQL语句。

        Args:
            sql: SQL语句字符串

        Returns:
            执行结果和数据的元组

        Examples:
            >>> result, data = edf.execute_sql("SELECT * FROM users WHERE id = 1")
            >>> print(data)
        """
        return self.executor.execute(sql)

    def list_tables(self) -> List[str]:
        """列出所有表名。

        Returns:
            表名列表
        """
        return self.db.list_tables()

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """获取表信息。

        Args:
            table_name: 表名

        Returns:
            包含表信息的字典
        """
        schema = self.db.get_table_schema(table_name)
        if schema is None:
            raise DatabaseError(f"表 {table_name} 不存在")
        
        info = {
            "table_name": schema.table_name,
            "columns": {},
            "primary_key": schema.primary_key,
            "foreign_keys": [],
            "indexes": []
        }
        
        for col_name, col_def in schema.columns.items():
            info["columns"][col_name] = {
                "data_type": col_def.data_type.value,
                "is_primary": col_def.is_primary,
                "is_nullable": col_def.is_nullable,
                "is_unique": col_def.is_unique,
                "is_autoincrement": col_def.is_autoincrement,
                "max_length": col_def.max_length
            }
        
        # 添加外键信息
        for fk in schema.foreign_keys:
            info["foreign_keys"].append({
                "column": fk.column,
                "ref_table": fk.ref_table,
                "ref_column": fk.ref_column,
                "on_delete": fk.on_delete,
                "on_update": fk.on_update
            })
        
        # 添加索引信息
        for idx_name, idx in schema.indexes.items():
            info["indexes"].append({
                "name": idx.name,
                "columns": idx.columns,
                "is_unique": idx.is_unique
            })
            
        return info

    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息。

        Returns:
            包含数据库信息的字典
        """
        return self.db.get_database_info()

    def import_from_json(self, table_name: str, json_file: str) -> int:
        """从JSON文件导入数据。

        Args:
            table_name: 表名
            json_file: JSON文件路径

        Returns:
            导入的行数
        """
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return self.insert(table_name, data)
        else:
            return self.insert(table_name, [data])

    def export_to_json(self, table_name: str, json_file: str,
                       where: Optional[str] = None) -> int:
        """导出数据到JSON文件。

        Args:
            table_name: 表名
            json_file: JSON文件路径
            where: WHERE条件字符串

        Returns:
            导出的行数
        """
        data = self.select(table_name, where=where)
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return len(data)

    def import_from_csv(self, table_name: str, csv_file: str,
                        delimiter: str = ',', has_header: bool = True) -> int:
        """从CSV文件导入数据。

        Args:
            table_name: 表名
            csv_file: CSV文件路径
            delimiter: 分隔符
            has_header: 是否有标题行

        Returns:
            导入的行数
        """
        data = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=delimiter)
            
            headers = None
            if has_header:
                headers = next(reader)
            
            for row in reader:
                if headers:
                    row_data = dict(zip(headers, row))
                else:
                    # 如果没有标题行，使用列索引作为键
                    row_data = {f"col_{i}": value for i, value in enumerate(row)}
                data.append(row_data)
        
        return self.insert(table_name, data)

    def export_to_csv(self, table_name: str, csv_file: str,
                      delimiter: str = ',', include_header: bool = True,
                      where: Optional[str] = None) -> int:
        """导出数据到CSV文件。

        Args:
            table_name: 表名
            csv_file: CSV文件路径
            delimiter: 分隔符
            include_header: 是否包含标题行
            where: WHERE条件字符串

        Returns:
            导出的行数
        """
        data = self.select(table_name, where=where)
        
        if not data:
            # 创建空文件
            with open(csv_file, 'w', encoding='utf-8') as f:
                pass
            return 0
        
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter)
            
            # 写入标题行
            if include_header:
                headers = list(data[0].keys())
                writer.writerow(headers)
            
            # 写入数据行
            for row in data:
                values = list(row.values())
                writer.writerow(values)
        
        return len(data)

    def import_from_xml(self, table_name: str, xml_file: str, 
                        row_tag: str = "row") -> int:
        """从XML文件导入数据。

        Args:
            table_name: 表名
            xml_file: XML文件路径
            row_tag: 行标签名

        Returns:
            导入的行数
        """
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        data = []
        for row_element in root.findall(row_tag):
            row_data = {}
            for child in row_element:
                row_data[child.tag] = child.text
            data.append(row_data)
        
        return self.insert(table_name, data)

    def export_to_xml(self, table_name: str, xml_file: str, 
                      row_tag: str = "row", root_tag: str = "data",
                      where: Optional[str] = None) -> int:
        """导出数据到XML文件。

        Args:
            table_name: 表名
            xml_file: XML文件路径
            row_tag: 行标签名
            root_tag: 根标签名
            where: WHERE条件字符串

        Returns:
            导出的行数
        """
        data = self.select(table_name, where=where)
        
        root = ET.Element(root_tag)
        for row in data:
            row_element = ET.SubElement(root, row_tag)
            for key, value in row.items():
                child = ET.SubElement(row_element, key)
                child.text = str(value) if value is not None else ""
        
        tree = ET.ElementTree(root)
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        
        return len(data)

    def create_index(self, table_name: str, index_name: str, 
                     columns: List[str], unique: bool = False) -> bool:
        """创建索引。

        Args:
            table_name: 表名
            index_name: 索引名
            columns: 列名列表
            unique: 是否唯一索引

        Returns:
            创建成功返回True
        """
        unique_str = "UNIQUE " if unique else ""
        columns_str = ", ".join(columns)
        sql = f"CREATE {unique_str}INDEX {index_name} ON {table_name} ({columns_str})"
        
        result, _ = self.executor.execute(sql)
        return result.value == 0  # SUCCESS = 0

    def drop_index(self, index_name: str) -> bool:
        """删除索引。

        Args:
            index_name: 索引名

        Returns:
            删除成功返回True
        """
        sql = f"DROP INDEX {index_name}"
        
        result, _ = self.executor.execute(sql)
        return result.value == 0  # SUCCESS = 0

    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """创建数据库备份。

        Args:
            backup_name: 备份名称，如果为None则自动生成

        Returns:
            备份文件路径
        """
        return self.db.create_backup(backup_name)

    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份。

        Returns:
            备份信息列表
        """
        return self.db.list_backups()

    def restore_backup(self, backup_path: str) -> bool:
        """从备份恢复数据库。

        Args:
            backup_path: 备份文件路径

        Returns:
            恢复成功返回True
        """
        return self.db.restore_backup(backup_path)

    def vacuum(self) -> bool:
        """数据库整理，回收未使用的空间。

        Returns:
            整理成功返回True
        """
        try:
            result, _ = self.executor.execute("VACUUM")
            return result.value == 0  # SUCCESS = 0
        except:
            return False

    def close(self) -> None:
        """关闭数据库连接。"""
        # 如果有未提交的事务，回滚它
        if self.current_transaction is not None:
            self.rollback_transaction()
        
        self.db.close()

    def __enter__(self):
        """上下文管理器入口。"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口。"""
        self.close()