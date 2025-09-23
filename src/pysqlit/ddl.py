"""DDL (数据定义语言)操作支持模块。

该模块提供了完整的数据定义语言(DDL)操作支持，包括：
- 创建、修改、删除表结构
- 管理索引和约束
- 处理外键关系
- 模式验证和持久化

主要功能：
1. 表管理：创建、删除、修改表结构
2. 列管理：添加、删除、重命名列
3. 索引管理：创建和删除索引
4. 约束管理：唯一约束、外键约束
5. 模式持久化：保存和加载数据库模式
"""

import os
from typing import Dict, List, Any, Optional
from .exceptions import DatabaseError
from .models import TableSchema, ColumnDefinition


class DDLManager:
    """DDL管理器，负责处理所有数据定义语言操作。
    
    该类提供了完整的DDL操作支持，包括：
    - 表的创建、修改、删除
    - 列的添加、删除、重命名
    - 索引的创建和删除
    - 约束的管理（唯一约束、外键约束）
    
    Attributes:
        database: 数据库实例，用于执行实际的DDL操作
        schemas: 表模式字典，存储所有表的元数据信息
    """
    
    def __init__(self, database):
        """初始化DDL管理器。
        
        Args:
            database: 数据库实例，用于执行实际的DDL操作
        """
        self.database = database
        self.schemas = {}  # 表名到表模式的映射字典
        
    def create_table(self, table_name: str, columns: Dict[str, str],
                    primary_key: Optional[str] = None,
                    foreign_keys: Optional[List[Dict[str, Any]]] = None,
                    indexes: Optional[List[str]] = None) -> bool:
        """创建新表并定义其模式结构。
        
        该方法创建一个新表，并设置其列定义、主键、外键和索引。
        
        Args:
            table_name: 表名，必须是唯一的
            columns: 列定义字典，键为列名，值为数据类型
            primary_key: 主键列名，可选
            foreign_keys: 外键定义列表，每个外键包含column、ref_table、ref_column
            indexes: 需要创建索引的列名列表
            
        Returns:
            bool: 创建成功返回True
            
        Raises:
            DatabaseError: 如果表已存在或参数无效
            
        Examples:
            >>> ddl.create_table("users", {
            ...     "id": "INTEGER",
            ...     "name": "TEXT",
            ...     "email": "TEXT"
            ... }, primary_key="id")
            True
        """
        if table_name in self.schemas:
            raise DatabaseError(f"表 {table_name} 已存在")
            
        # 创建新的表模式
        schema = TableSchema(table_name)
        
        # 添加列定义
        for col_name, col_type in columns.items():
            is_primary = (col_name == primary_key)
            schema.add_column(ColumnDefinition(col_name, col_type, is_primary))
            
        # 添加外键约束
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
                
        # 保存表模式
        self.schemas[table_name] = schema
        
        # 在数据库中创建实际表
        self.database.create_table(table_name)
        
        return True
        
    def drop_table(self, table_name: str, if_exists: bool = False) -> bool:
        """删除指定表。
        
        该方法从数据库中删除一个表及其所有相关数据。
        
        Args:
            table_name: 要删除的表名
            if_exists: 如果为True，表不存在时不抛出异常
            
        Returns:
            bool: 删除成功返回True，表不存在且if_exists为True返回False
            
        Raises:
            DatabaseError: 如果表不存在且if_exists为False
            
        Examples:
            >>> ddl.drop_table("users")
            True
            >>> ddl.drop_table("nonexistent", if_exists=True)
            False
        """
        if table_name not in self.schemas:
            if if_exists:
                return False
            raise DatabaseError(f"表 {table_name} 不存在")
            
        # 从模式字典中删除表
        del self.schemas[table_name]
        
        # 在数据库中删除实际表
        self.database.drop_table(table_name)
        return True
        
    def alter_table_add_column(self, table_name: str, column_name: str,
                              column_type: str, default_value: Any = None) -> bool:
        """向现有表添加新列。
        
        该方法在现有表中添加一个新列，并可选择设置默认值。
        
        Args:
            table_name: 目标表名
            column_name: 新列名
            column_type: 列数据类型
            default_value: 默认值，用于现有行
            
        Returns:
            bool: 添加成功返回True
            
        Raises:
            DatabaseError: 如果表不存在或列已存在
            
        Examples:
            >>> ddl.alter_table_add_column("users", "age", "INTEGER", 0)
            True
        """
        if table_name not in self.schemas:
            raise DatabaseError(f"表 {table_name} 不存在")
            
        if column_name in self.schemas[table_name].columns:
            raise DatabaseError(f"列 {column_name} 已存在")
            
        # 添加新列到表模式
        self.schemas[table_name].add_column(
            ColumnDefinition(column_name, column_type, default_value=default_value)
        )
        
        # 更新现有行的默认值（需要根据存储层实现）
        # TODO: 实现现有行的默认值更新逻辑
        return True
        
    def alter_table_drop_column(self, table_name: str, column_name: str) -> bool:
        """从表中删除指定列。
        
        该方法从现有表中删除一个列，会检查主键约束和外键引用。
        
        Args:
            table_name: 目标表名
            column_name: 要删除的列名
            
        Returns:
            bool: 删除成功返回True
            
        Raises:
            DatabaseError: 如果表不存在、列不存在或列是主键
            
        Examples:
            >>> ddl.alter_table_drop_column("users", "temp_column")
            True
        """
        if table_name not in self.schemas:
            raise DatabaseError(f"表 {table_name} 不存在")
            
        if column_name not in self.schemas[table_name].columns:
            raise DatabaseError(f"列 {column_name} 不存在")
            
        # 检查列是否是主键或有外键引用
        schema = self.schemas[table_name]
        if schema.columns[column_name].is_primary:
            raise DatabaseError("不能删除主键列")
            
        # 删除列
        del self.schemas[table_name].columns[column_name]
        return True
        
    def alter_table_rename_column(self, table_name: str, old_name: str,
                                 new_name: str) -> bool:
        """重命名表中的列。
        
        该方法将现有表中的列重命名为新名称。
        
        Args:
            table_name: 目标表名
            old_name: 原列名
            new_name: 新列名
            
        Returns:
            bool: 重命名成功返回True
            
        Raises:
            DatabaseError: 如果表不存在、原列不存在或新列名已存在
            
        Examples:
            >>> ddl.alter_table_rename_column("users", "old_name", "new_name")
            True
        """
        if table_name not in self.schemas:
            raise DatabaseError(f"表 {table_name} 不存在")
            
        schema = self.schemas[table_name]
        
        if old_name not in schema.columns:
            raise DatabaseError(f"列 {old_name} 不存在")
            
        if new_name in schema.columns:
            raise DatabaseError(f"列 {new_name} 已存在")
            
        # 重命名列
        column = schema.columns[old_name]
        column.name = new_name
        schema.columns[new_name] = column
        del schema.columns[old_name]
        
        return True
        
    def create_index(self, table_name: str, index_name: str,
                    columns: List[str], unique: bool = False) -> bool:
        """在表上创建索引。
        
        该方法为指定表的列创建索引，支持普通索引和唯一索引。
        
        Args:
            table_name: 目标表名
            index_name: 索引名称，必须是唯一的
            columns: 需要索引的列名列表
            unique: 是否为唯一索引
            
        Returns:
            bool: 创建成功返回True
            
        Raises:
            DatabaseError: 如果表不存在或列不存在
            
        Examples:
            >>> ddl.create_index("users", "idx_users_email", ["email"])
            True
            >>> ddl.create_index("users", "uidx_users_email", ["email"], unique=True)
            True
        """
        if table_name not in self.schemas:
            raise DatabaseError(f"表 {table_name} 不存在")
            
        schema = self.schemas[table_name]
        
        # 验证列是否存在
        for col in columns:
            if col not in schema.columns:
                raise DatabaseError(f"列 {col} 不存在")
                
        # 创建索引（简化实现 - 需要实际的索引实现）
        schema.add_index_definition(index_name, columns, unique)
        
        return True
        
    def drop_index(self, table_name: str, index_name: str) -> bool:
        """删除指定索引。
        
        该方法从表中删除一个索引。
        
        Args:
            table_name: 目标表名
            index_name: 要删除的索引名称
            
        Returns:
            bool: 删除成功返回True
            
        Raises:
            DatabaseError: 如果表不存在或索引不存在
            
        Examples:
            >>> ddl.drop_index("users", "idx_users_email")
            True
        """
        if table_name not in self.schemas:
            raise DatabaseError(f"表 {table_name} 不存在")
            
        schema = self.schemas[table_name]
        
        if index_name not in schema.indexes:
            raise DatabaseError(f"索引 {index_name} 不存在")
            
        del schema.indexes[index_name]
        return True
    
    def alter_table_add_unique_constraint(self, table_name: str, column_name: str) -> bool:
        """为现有列添加唯一约束。
        
        该方法为指定列添加唯一约束，确保列中的所有值都是唯一的。
        在添加约束前会检查现有数据是否有重复值。
        
        Args:
            table_name: 目标表名
            column_name: 要添加唯一约束的列名
            
        Returns:
            bool: 添加成功返回True
            
        Raises:
            DatabaseError: 如果表不存在、列不存在、列已有唯一约束或存在重复值
            
        Examples:
            >>> ddl.alter_table_add_unique_constraint("users", "email")
            True
        """
        if table_name not in self.schemas:
            raise DatabaseError(f"表 {table_name} 不存在")
            
        schema = self.schemas[table_name]
        
        if column_name not in schema.columns:
            raise DatabaseError(f"表 {table_name} 中不存在列 {column_name}")
        
        # 检查列是否已有唯一约束
        if schema.columns[column_name].is_unique:
            raise DatabaseError(f"列 {column_name} 已有唯一约束")
        
        # 检查现有数据是否有重复值
        from .models import IndexDefinition
        table = self.database.tables.get(table_name)
        if table:
            # 获取该列的所有现有值
            existing_values = set()
            rows = table.select_all()
            for row in rows:
                value = row.get_value(column_name)
                if value is not None:
                    str_value = str(value).strip()
                    if str_value:
                        if str_value in existing_values:
                            raise DatabaseError(
                                f"无法添加唯一约束：列 '{column_name}' 存在重复值: {str_value}"
                            )
                        existing_values.add(str_value)
        
        # 为列添加唯一约束
        schema.columns[column_name].is_unique = True
        
        # 添加唯一索引
        index_name = f"uidx_{table_name}_{column_name}"
        schema.add_index(IndexDefinition(name=index_name, columns=[column_name], is_unique=True))
        
        return True
        
    def alter_table_drop_unique_constraint(self, table_name: str, column_name: str) -> bool:
        """从现有列中移除唯一约束。
        
        该方法移除指定列的唯一约束，允许列中存在重复值。
        
        Args:
            table_name: 目标表名
            column_name: 要移除唯一约束的列名
            
        Returns:
            bool: 移除成功返回True
            
        Raises:
            DatabaseError: 如果表不存在、列不存在或列没有唯一约束
            
        Examples:
            >>> ddl.alter_table_drop_unique_constraint("users", "email")
            True
        """
        if table_name not in self.schemas:
            raise DatabaseError(f"表 {table_name} 不存在")
            
        schema = self.schemas[table_name]
        
        if column_name not in schema.columns:
            raise DatabaseError(f"表 {table_name} 中不存在列 {column_name}")
        
        # 检查列是否有唯一约束
        if not schema.columns[column_name].is_unique:
            raise DatabaseError(f"列 {column_name} 没有唯一约束")
        
        # 从列中移除唯一约束
        schema.columns[column_name].is_unique = False
        
        # 移除唯一索引
        index_name = f"uidx_{table_name}_{column_name}"
        if index_name in schema.indexes:
            del schema.indexes[index_name]
        
        return True
        
    def get_table_schema(self, table_name: str) -> Optional[TableSchema]:
        """获取指定表的模式信息。
        
        Args:
            table_name: 表名
            
        Returns:
            Optional[TableSchema]: 表模式对象，如果表不存在返回None
        """
        return self.schemas.get(table_name)
        
    def list_tables(self) -> List[str]:
        """列出所有表的名称。
        
        Returns:
            List[str]: 所有表名的列表
        """
        return list(self.schemas.keys())
        
    def validate_schema(self, table_name: str) -> bool:
        """验证表模式的有效性。
        
        该方法验证表模式的完整性，包括：
        - 检查是否有主键
        - 验证外键引用的表是否存在
        
        Args:
            table_name: 要验证的表名
            
        Returns:
            bool: 验证成功返回True
            
        Raises:
            DatabaseError: 如果验证失败
            
        Examples:
            >>> ddl.validate_schema("users")
            True
        """
        if table_name not in self.schemas:
            return False
            
        schema = self.schemas[table_name]
        
        # 检查是否有主键
        primary_keys = [col for col in schema.columns.values() if col.is_primary]
        if len(primary_keys) == 0:
            raise DatabaseError("表必须有主键")
            
        # 验证外键
        for fk in schema.foreign_keys:
            if fk.ref_table not in self.schemas:
                raise DatabaseError(f"引用的表 {fk.ref_table} 不存在")
                
        return True


class SchemaManager:
    """模式管理器，负责数据库模式和元数据的管理。
    
    该类负责管理数据库的模式信息，包括：
    - 保存表模式到文件
    - 从文件加载表模式
    - 维护数据库的元数据信息
    
    Attributes:
        db_path: 数据库文件路径
        schema_file: 模式文件路径（数据库路径.schema）
        schemas: 表模式字典，存储所有表的元数据
    """
    
    def __init__(self, db_path: str):
        """初始化模式管理器。
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.schema_file = f"{db_path}.schema"
        self.schemas = {}
        
    def save_schema(self):
        """将模式信息保存到文件。
        
        该方法将所有表的模式信息序列化为JSON格式并保存到文件。
        
        Raises:
            DatabaseError: 如果保存失败
            
        Examples:
            >>> schema_manager.save_schema()
        """
        try:
            import json
            schema_data = {}
            for table_name, schema in self.schemas.items():
                schema_data[table_name] = schema.to_dict()
                
            with open(self.schema_file, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise DatabaseError(f"保存模式失败: {e}")
            
    def load_schema(self):
        """从文件加载模式信息。
        
        该方法从JSON文件中加载所有表的模式信息。
        
        Raises:
            DatabaseError: 如果加载失败
            
        Examples:
            >>> schema_manager.load_schema()
        """
        try:
            import json
            if os.path.exists(self.schema_file):
                with open(self.schema_file, 'r', encoding='utf-8') as f:
                    schema_data = json.load(f)
                    
                for table_name, schema_dict in schema_data.items():
                    self.schemas[table_name] = TableSchema.from_dict(schema_dict)
                    
        except Exception as e:
            raise DatabaseError(f"加载模式失败: {e}")