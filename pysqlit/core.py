"""PySQLit核心架构模块，提供面向对象的数据库设计。

该模块定义了数据库系统的核心抽象和实现，包括：
- 存储接口和实现
- 索引接口和B树实现
- 表抽象
- 数据库管理器
- WHERE条件处理
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
import struct
from enum import Enum

from .constants import (
    PAGE_SIZE, ROW_SIZE, NODE_LEAF, NODE_INTERNAL,
    LEAF_NODE_MAX_CELLS, INTERNAL_NODE_MAX_KEYS
)
from .models import Row
from .exceptions import DatabaseError


class WhereCondition:
    """WHERE子句条件，用于过滤数据行。
    
    支持多种比较操作符（=, !=, >, <, >=, <=），
    并提供类型安全的比较功能。
    """
    
    def __init__(self, column: str, operator: str, value: Any):
        """初始化WHERE条件。
        
        Args:
            column: 列名
            operator: 比较操作符
            value: 比较值
        """
        self.column = column
        self.operator = operator
        self.value = value
    
    def evaluate(self, row: Row) -> bool:
        """根据行数据评估条件是否满足。
        
        Args:
            row: 要评估的数据行
            
        Returns:
            条件满足返回True，否则返回False
        """
        row_value = getattr(row, self.column, None)
        if row_value is None:
            return False
        
        # 将值转换为通用类型进行比较
        try:
            # 尝试将两个值都转换为浮点数
            try:
                row_float = float(row_value)
                value_float = float(self.value)
                row_value = row_float
                self.value = value_float
            except (ValueError, TypeError):
                # 如果不能转换为浮点数，则按字符串比较
                row_value = str(row_value)
                self.value = str(self.value)
            
            # 根据操作符执行比较
            if self.operator == "=":
                return row_value == self.value
            elif self.operator == "!=":
                return row_value != self.value
            elif self.operator == ">":
                return row_value > self.value
            elif self.operator == "<":
                return row_value < self.value
            elif self.operator == ">=":
                return row_value >= self.value
            elif self.operator == "<=":
                return row_value <= self.value
            else:
                return False
        except (TypeError, ValueError):
            return False


class StorageInterface(ABC):
    """存储接口抽象类。
    
    定义了所有存储实现必须提供的基本操作接口。
    """
    
    @abstractmethod
    def get_page(self, page_num: int) -> bytearray:
        """获取指定页号的页面数据。
        
        Args:
            page_num: 页号
            
        Returns:
            页面数据的字节数组
        """
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """将所有更改刷新到持久化存储。"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭存储连接并释放资源。"""
        pass


class IndexInterface(ABC):
    """索引接口抽象类。
    
    定义了所有索引实现必须提供的基本操作接口。
    """
    
    @abstractmethod
    def insert(self, key: int, value: bytes) -> None:
        """插入键值对。
        
        Args:
            key: 键
            value: 值的字节数组
        """
        pass
    
    @abstractmethod
    def delete(self, key: int) -> bool:
        """删除指定键的数据。
        
        Args:
            key: 要删除的键
            
        Returns:
            删除成功返回True，键不存在返回False
        """
        pass
    
    @abstractmethod
    def update(self, key: int, new_value: bytes) -> bool:
        """更新指定键的数据。
        
        Args:
            key: 要更新的键
            new_value: 新的值的字节数组
            
        Returns:
            更新成功返回True，键不存在返回False
        """
        pass
    
    @abstractmethod
    def find(self, key: int) -> Optional[bytes]:
        """根据键查找对应的值。
        
        Args:
            key: 要查找的键
            
        Returns:
            找到的值，如果键不存在返回None
        """
        pass
    
    @abstractmethod
    def scan(self) -> List[Tuple[int, bytes]]:
        """扫描所有键值对。
        
        Returns:
            所有键值对的列表
        """
        pass


class ParserInterface(ABC):
    """解析器接口抽象类。
    
    定义了所有SQL解析器必须提供的接口。
    """
    
    @abstractmethod
    def parse(self, sql: str) -> Any:
        """解析SQL语句。
        
        Args:
            sql: SQL语句字符串
            
        Returns:
            解析结果
        """
        pass


class ExecutorInterface(ABC):
    """执行器接口抽象类。
    
    定义了所有SQL执行器必须提供的接口。
    """
    
    @abstractmethod
    def execute(self, statement: Any) -> Any:
        """执行解析后的语句。
        
        Args:
            statement: 解析后的语句对象
            
        Returns:
            执行结果
        """
        pass


# 具体实现类
class Page:
    """页面抽象类，封装了页面的读写操作。
    
    提供了对页面数据的结构化访问，支持整数和字节数组的读写。
    """
    
    def __init__(self, data: bytearray, page_num: int):
        """初始化页面。
        
        Args:
            data: 页面数据的字节数组
            page_num: 页号
        """
        self.data = data
        self.page_num = page_num
    
    def read_int(self, offset: int) -> int:
        """从指定偏移量读取4字节整数。
        
        Args:
            offset: 偏移量
            
        Returns:
            读取的整数值
        """
        return struct.unpack('<I', self.data[offset:offset+4])[0]
    
    def write_int(self, offset: int, value: int) -> None:
        """在指定偏移量写入4字节整数。
        
        Args:
            offset: 偏移量
            value: 要写入的整数值
        """
        self.data[offset:offset+4] = struct.pack('<I', value)
    
    def read_bytes(self, offset: int, length: int) -> bytes:
        """从指定偏移量读取字节数组。
        
        Args:
            offset: 偏移量
            length: 要读取的字节数
            
        Returns:
            读取的字节数组
        """
        return bytes(self.data[offset:offset+length])
    
    def write_bytes(self, offset: int, data: bytes) -> None:
        """在指定偏移量写入字节数组。
        
        Args:
            offset: 偏移量
            data: 要写入的字节数组
        """
        self.data[offset:offset+len(data)] = data


class BTreeNode(ABC):
    """B树节点抽象类。
    
    定义了B树节点的基本接口和行为。
    """
    
    def __init__(self, page: Page):
        """初始化B树节点。
        
        Args:
            page: 节点所在的页面
        """
        self.page = page
    
    def get_type(self) -> int:
        """获取节点类型。
        
        Returns:
            节点类型标识符
        """
        return self.page.read_int(0)
    
    def is_full(self) -> bool:
        """检查节点是否已满。
        
        Returns:
            节点已满返回True，否则返回False
        """
        return False
    
    def insert(self, key: int, value: bytes) -> None:
        """插入键值对。
        
        Args:
            key: 键
            value: 值的字节数组
        """
        pass
    
    def delete(self, key: int) -> bool:
        """删除键值对。
        
        Args:
            key: 要删除的键
            
        Returns:
            删除成功返回True，否则返回False
        """
        return False


class LeafNode(BTreeNode):
    """叶子节点实现类。
    
    叶子节点存储实际的数据记录，支持插入、删除和查询操作。
    """
    
    def __init__(self, page: Page):
        """初始化叶子节点。
        
        Args:
            page: 节点所在的页面
        """
        super().__init__(page)
        self._initialize()
    
    def _initialize(self) -> None:
        """初始化叶子节点的默认状态。"""
        if self.page.read_int(0) == 0:
            self.page.data[0] = NODE_LEAF
            self.page.write_int(6, 0)  # 设置单元格数量为0
    
    def get_type(self) -> int:
        """获取节点类型。
        
        Returns:
            节点类型标识符
        """
        return self.page.read_int(0)
    
    def is_full(self) -> bool:
        """检查叶子节点是否已满。
        
        Returns:
            节点已满返回True，否则返回False
        """
        return self.num_cells() >= LEAF_NODE_MAX_CELLS
    
    def num_cells(self) -> int:
        """获取叶子节点中的单元格数量。
        
        Returns:
            单元格数量
        """
        return self.page.read_int(6)
    
    def insert(self, key: int, value: bytes) -> None:
        """插入键值对。
        
        Args:
            key: 键
            value: 值的字节数组
            
        Raises:
            DatabaseError: 如果节点已满
        """
        if self.is_full():
            raise DatabaseError("叶子节点已满")
        
        cell_num = self._find_insert_position(key)
        self._insert_at(cell_num, key, value)
    
    def delete(self, key: int) -> bool:
        """删除键值对。
        
        Args:
            key: 要删除的键
            
        Returns:
            删除成功返回True，键不存在返回False
        """
        cell_num = self._find_key_position(key)
        if cell_num < 0:
            return False
        
        self._delete_at(cell_num)
        return True
    
    def _find_insert_position(self, key: int) -> int:
        """使用二分查找确定插入位置。
        
        Args:
            key: 要插入的键
            
        Returns:
            插入位置的索引
        """
        low, high = 0, self.num_cells()
        while low < high:
            mid = (low + high) // 2
            mid_key = self._get_key(mid)
            if mid_key < key:
                low = mid + 1
            else:
                high = mid
        return low
    
    def _find_key_position(self, key: int) -> int:
        """查找键的精确位置。
        
        Args:
            key: 要查找的键
            
        Returns:
            键的索引，如果键不存在返回-1
        """
        for i in range(self.num_cells()):
            if self._get_key(i) == key:
                return i
        return -1
    
    def _insert_at(self, cell_num: int, key: int, value: bytes) -> None:
        """在指定位置插入键值对。
        
        Args:
            cell_num: 插入位置的索引
            key: 键
            value: 值的字节数组
        """
        # 移动单元格以腾出空间
        for i in range(self.num_cells(), cell_num, -1):
            src = 14 + (i-1) * (4 + ROW_SIZE)
            dst = 14 + i * (4 + ROW_SIZE)
            self.page.write_bytes(dst, self.page.read_bytes(src, 4 + ROW_SIZE))
        
        # 插入新单元格
        offset = 14 + cell_num * (4 + ROW_SIZE)
        self.page.write_int(offset, key)
        self.page.write_bytes(offset + 4, value)
        
        # 更新单元格计数
        self.page.write_int(6, self.num_cells() + 1)
    
    def _delete_at(self, cell_num: int) -> None:
        """删除指定位置的单元格。
        
        Args:
            cell_num: 要删除的单元格索引
        """
        # 移动单元格填补空缺
        for i in range(cell_num, self.num_cells() - 1):
            src = 14 + (i+1) * (4 + ROW_SIZE)
            dst = 14 + i * (4 + ROW_SIZE)
            self.page.write_bytes(dst, self.page.read_bytes(src, 4 + ROW_SIZE))
        
        # 更新单元格计数
        self.page.write_int(6, self.num_cells() - 1)
    
    def _get_key(self, cell_num: int) -> int:
        """获取指定单元格的键。
        
        Args:
            cell_num: 单元格索引
            
        Returns:
            键值
        """
        offset = 14 + cell_num * (4 + ROW_SIZE)
        return self.page.read_int(offset)
    
    def get_value(self, cell_num: int) -> bytes:
        """获取指定单元格的值。
        
        Args:
            cell_num: 单元格索引
            
        Returns:
            值的字节数组
        """
        offset = 14 + cell_num * (4 + ROW_SIZE) + 4
        return self.page.read_bytes(offset, ROW_SIZE)


class InternalNode(BTreeNode):
    """内部节点实现类。
    
    内部节点存储键和指向子节点的指针，不存储实际数据。
    """
    
    def __init__(self, page: Page):
        """初始化内部节点。
        
        Args:
            page: 节点所在的页面
        """
        super().__init__(page)
    
    def get_type(self) -> int:
        """获取节点类型。
        
        Returns:
            节点类型标识符
        """
        return self.page.read_int(0)
    
    def is_full(self) -> bool:
        """检查内部节点是否已满。
        
        Returns:
            节点已满返回True，否则返回False
        """
        return self.num_keys() >= INTERNAL_NODE_MAX_KEYS
    
    def num_keys(self) -> int:
        """获取内部节点中的键数量。
        
        Returns:
            键数量
        """
        return self.page.read_int(6)
    
    def insert(self, key: int, value: bytes) -> None:
        """内部节点不直接存储值。
        
        Args:
            key: 键
            value: 值的字节数组
        """
        # 内部节点不存储实际值，仅用于索引
        pass
    
    def delete(self, key: int) -> bool:
        """内部节点处理键的删除。
        
        Args:
            key: 要删除的键
            
        Returns:
            删除成功返回True，否则返回False
        """
        # 内部节点处理键的删除逻辑
        return False


class BTreeIndex(IndexInterface):
    """B树索引实现类。
    
    提供基于B树的键值存储和检索功能。
    """
    
    def __init__(self, storage):
        """初始化B树索引。
        
        Args:
            storage: 存储接口实例
        """
        self.storage = storage
        self.root_page = 0
        self._initialize()
    
    def _initialize(self) -> None:
        """初始化B树索引。"""
        if hasattr(self.storage, 'get_page') and self.storage.get_page(0):
            root_page = Page(self.storage.get_page(0), 0)
            root_node = LeafNode(root_page)
    
    def insert(self, key: int, value: bytes) -> None:
        """插入键值对。
        
        Args:
            key: 键
            value: 值的字节数组
        """
        root_page = Page(self.storage.get_page(self.root_page), self.root_page)
        root_node = LeafNode(root_page)
        
        if root_node.is_full():
            self._split_root()
        
        root_node.insert(key, value)
    
    def delete(self, key: int) -> bool:
        """删除键值对。
        
        Args:
            key: 要删除的键
            
        Returns:
            删除成功返回True，键不存在返回False
        """
        root_page = Page(self.storage.get_page(self.root_page), self.root_page)
        root_node = LeafNode(root_page)
        return root_node.delete(key)
    
    def update(self, key: int, new_value: bytes) -> bool:
        """更新键值对。
        
        Args:
            key: 要更新的键
            new_value: 新的值的字节数组
            
        Returns:
            更新成功返回True，键不存在返回False
        """
        if self.delete(key):
            self.insert(key, new_value)
            return True
        return False
    
    def find(self, key: int) -> Optional[bytes]:
        """根据键查找对应的值。
        
        Args:
            key: 要查找的键
            
        Returns:
            找到的值，如果键不存在返回None
        """
        root_page = Page(self.storage.get_page(self.root_page), self.root_page)
        root_node = LeafNode(root_page)
        
        for i in range(root_node.num_cells()):
            if root_node._get_key(i) == key:
                return root_node.get_value(i)
        return None
    
    def scan(self) -> List[Tuple[int, bytes]]:
        """扫描所有键值对。
        
        Returns:
            所有键值对的列表
        """
        root_page = Page(self.storage.get_page(self.root_page), self.root_page)
        root_node = LeafNode(root_page)
        
        results = []
        for i in range(root_node.num_cells()):
            key = root_node._get_key(i)
            value = root_node.get_value(i)
            results.append((key, value))
        
        return results
    
    def _split_root(self) -> None:
        """当根节点满时分裂根节点。"""
        # 简化实现，仅用于演示
        pass


class Table:
    """表抽象类。
    
    封装了表的基本操作，包括插入、查询、更新和删除。
    """
    
    def __init__(self, name: str, storage, index):
        """初始化表。
        
        Args:
            name: 表名
            storage: 存储接口实例
            index: 索引接口实例
        """
        self.name = name
        self.storage = storage
        self.index = index
        self.schema = {
            'id': 'INTEGER',
            'username': 'TEXT(32)',
            'email': 'TEXT(255)'
        }
    
    def insert(self, row: Row, schema: Any) -> bool:
        """插入一行数据。
        
        Args:
            row: 要插入的数据行
            schema: 表结构定义
            
        Returns:
            插入成功返回True
            
        Raises:
            DatabaseError: 插入失败时抛出
        """
        try:
            serialized = row.serialize(schema)
            self.index.insert(row.id, serialized)
            return True
        except Exception as e:
            raise DatabaseError(f"插入失败: {e}")
    
    def select(self, where_clause: Optional[WhereCondition] = None) -> List[Row]:
        """查询数据行。
        
        Args:
            where_clause: WHERE条件，如果为None则查询所有行
            
        Returns:
            满足条件的行列表
        """
        results = []
        data = self.index.scan()
        
        for key, value in data:
            row = Row.deserialize(value)
            if where_clause is None or where_clause.evaluate(row):
                results.append(row)
        
        return results
    
    def update(self, updates: Dict[str, Any], where_clause: Optional[WhereCondition] = None) -> int:
        """更新数据行。
        
        Args:
            updates: 要更新的列和值
            where_clause: WHERE条件，如果为None则更新所有行
            
        Returns:
            更新的行数
        """
        updated_count = 0
        data = self.index.scan()
        
        for key, value in data:
            row = Row.deserialize(value)
            if where_clause is None or where_clause.evaluate(row):
                # 应用更新
                for col, new_val in updates.items():
                    setattr(row, col, new_val)
                
                serialized = row.serialize()
                self.index.update(key, serialized)
                updated_count += 1
        
        return updated_count
    
    def delete(self, where_clause: Optional[WhereCondition] = None) -> int:
        """删除数据行。
        
        Args:
            where_clause: WHERE条件，如果为None则删除所有行
            
        Returns:
            删除的行数
        """
        # 首先收集所有要删除的键
        keys_to_delete = []
        for key, value in self.index.scan():
            row = Row.deserialize(value)
            if where_clause is None or where_clause.evaluate(row):
                keys_to_delete.append(key)
        
        # 然后删除这些键
        deleted_count = 0
        for key in keys_to_delete:
            if self.index.delete(key):
                deleted_count += 1
        
        # 清理任何剩余的无效数据
        self.clean_invalid_data()
        
        return deleted_count

    def clean_invalid_data(self):
        """清理索引中的任何无效数据。
        
        这是一个占位符，用于实际的数据清理逻辑。
        在真实实现中，这将删除任何无效条目。
        """
        # 这是一个占位符，用于实际的数据清理逻辑
        # 在真实实现中，这将删除任何无效条目
        pass
    
    def get_row_count(self) -> int:
        """获取表中的行数。
        
        Returns:
            行数
        """
        return len(self.index.scan())


class DatabaseManager:
    """数据库管理器，提供面向对象的数据库设计。
    
    管理数据库中的所有表，并提供SQL执行功能。
    """
    
    def __init__(self, filename: str):
        """初始化数据库管理器。
        
        Args:
            filename: 数据库文件名
        """
        from .storage import Pager
        self.storage = Pager(filename)
        self.tables: Dict[str, Table] = {}
        self._initialize_tables()
    
    def _initialize_tables(self) -> None:
        """初始化默认表。"""
        self.create_table("users")
    
    def create_table(self, name: str) -> None:
        """创建新表。
        
        Args:
            name: 表名
            
        Raises:
            DatabaseError: 如果表已存在
        """
        if name in self.tables:
            raise DatabaseError(f"表 {name} 已存在")
        
        index = BTreeIndex(self.storage)
        self.tables[name] = Table(name, self.storage, index)
    
    def drop_table(self, name: str) -> None:
        """删除表。
        
        Args:
            name: 表名
            
        Raises:
            DatabaseError: 如果表不存在
        """
        if name not in self.tables:
            raise DatabaseError(f"表 {name} 不存在")
        
        # 清除所有数据
        self.tables[name].delete()
        del self.tables[name]
    
    def execute_sql(self, sql: str) -> Any:
        """执行SQL语句。
        
        Args:
            sql: SQL语句字符串
            
        Returns:
            执行结果
        """
        from .parser import EnhancedSQLParser as SQLParser
        
        result, statement = SQLParser.parse_statement(sql)
        
        if result.value != 0:
            return result, None
        
        try:
            if isinstance(statement, SQLParser.InsertStatement):
                table = self.tables[statement.table_name]
                # 转换为行列表并插入每一行
                rows = statement.to_rows(schema=table.schema)
                for row in rows:
                    table.insert(row, table.schema)
                return result, len(rows)
            
            elif isinstance(statement, SQLParser.SelectStatement):
                table = self.tables[statement.table_name]
                rows = table.select(statement.where_clause)
                # 将行转换为字典格式，包含选定的列和别名
                dict_rows = []
                
                for row in rows:
                    row_dict = {}
                    # 如果列是['*']，选择所有列
                    if statement.columns == ['*']:
                        # 使用表结构获取所有列名
                        for col_name in table.schema.keys():
                            value = getattr(row, col_name, None)
                            row_dict[col_name] = value
                    else:
                        for col_expr in statement.columns:
                            # 检查此列是否有别名
                            alias = statement.alias_mapping.get(col_expr, col_expr)
                            value = getattr(row, col_expr, None)
                            row_dict[alias] = value
                    
                    dict_rows.append(row_dict)
                
                return result, dict_rows
            
            elif isinstance(statement, SQLParser.UpdateStatement):
                table = self.tables[statement.table_name]
                count = table.update(statement.updates, statement.where_clause)
                return result, count
            
            elif isinstance(statement, SQLParser.DeleteStatement):
                table = self.tables[statement.table_name]
                count = table.delete(statement.where_clause)
                return result, count
            
            else:
                return result, None
                
        except Exception as e:
            raise DatabaseError(f"执行SQL失败: {e}")
    
    def get_table_info(self) -> Dict[str, Dict[str, Any]]:
        """获取表信息。
        
        Returns:
            表信息的字典
        """
        info = {}
        for name, table in self.tables.items():
            info[name] = {
                'row_count': table.get_row_count(),
                'schema': table.schema
            }
        return info
    
    def close(self):
        """关闭数据库连接。"""
        self.storage.close()


class DatabaseFactory:
    """数据库实例工厂类。
    
    提供创建数据库实例的静态方法。
    """
    
    @staticmethod
    def create_database(filename: str) -> DatabaseManager:
        """创建数据库实例。
        
        Args:
            filename: 数据库文件名
            
        Returns:
            数据库管理器实例
        """
        return DatabaseManager(filename)
    
    @staticmethod
    def create_memory_database() -> DatabaseManager:
        """创建内存数据库实例。
        
        Returns:
            内存数据库管理器实例
        """
        return DatabaseManager(":memory:")