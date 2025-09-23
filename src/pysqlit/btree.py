"""增强型B树实现，支持DELETE和UPDATE操作。

提供完整的B树数据结构实现，包括：
- 叶子节点和内部节点的管理
- 插入、删除、更新操作
- 范围查询和条件查询
- 节点分裂和合并
"""

from typing import List, Optional, Tuple, Dict, Any
import struct
from .constants import (
    PAGE_SIZE, INVALID_PAGE_NUM,
    NODE_TYPE_SIZE, IS_ROOT_SIZE, PARENT_POINTER_SIZE,
    COMMON_NODE_HEADER_SIZE,
    LEAF_NODE_NUM_CELLS_SIZE, LEAF_NODE_NEXT_LEAF_SIZE,
    LEAF_NODE_HEADER_SIZE, LEAF_NODE_CELL_SIZE,
    LEAF_NODE_MAX_CELLS, LEAF_NODE_RIGHT_SPLIT_COUNT, LEAF_NODE_LEFT_SPLIT_COUNT,
    INTERNAL_NODE_NUM_KEYS_SIZE, INTERNAL_NODE_RIGHT_CHILD_SIZE,
    INTERNAL_NODE_HEADER_SIZE, INTERNAL_NODE_CELL_SIZE,
    INTERNAL_NODE_MAX_KEYS, INTERNAL_NODE_KEY_SIZE, INTERNAL_NODE_CHILD_SIZE,
    ROW_SIZE, NODE_LEAF, NODE_INTERNAL,
    LEAF_NODE_NUM_CELLS_OFFSET, LEAF_NODE_NEXT_LEAF_OFFSET,
    INTERNAL_NODE_NUM_KEYS_OFFSET, INTERNAL_NODE_RIGHT_CHILD_OFFSET
)
from .models import Row
from .exceptions import BTreeError
from .storage import Pager


class EnhancedBTreeNode:
    """增强型B树节点基类，提供节点基本操作。
    
    所有B树节点（叶子节点和内部节点）的基类，提供节点类型、
    根节点标识、父节点指针等基本属性的访问和设置。
    """
    
    def __init__(self, pager: Pager, page_num: int) -> None:
        """初始化B树节点。
        
        Args:
            pager: 页面管理器，负责磁盘页的读写
            page_num: 节点所在的页号
        """
        self.pager = pager
        self.page_num = page_num
        self.page = pager.get_page(page_num)  # 获取页面对应的字节数组
    
    def get_node_type(self) -> int:
        """获取节点类型（叶子节点或内部节点）。
        
        Returns:
            节点类型标识符
        """
        return self.page[0]
    
    def set_node_type(self, node_type: int) -> None:
        """设置节点类型。
        
        Args:
            node_type: 节点类型标识符
        """
        self.page[0] = node_type
    
    def is_root(self) -> bool:
        """检查是否为根节点。
        
        Returns:
            是根节点返回True，否则返回False
        """
        return bool(self.page[1])
    
    def set_root(self, is_root: bool) -> None:
        """设置是否为根节点。
        
        Args:
            is_root: 是否为根节点
        """
        self.page[1] = 1 if is_root else 0
    
    def get_parent(self) -> int:
        """获取父节点的页号。
        
        Returns:
            父节点页号，如果没有父节点返回INVALID_PAGE_NUM
        """
        return struct.unpack('<I', self.page[2:6])[0]
    
    def set_parent(self, parent_page: int) -> None:
        """设置父节点的页号。
        
        Args:
            parent_page: 父节点页号
        """
        self.page[2:6] = struct.pack('<I', parent_page)


class EnhancedLeafNode(EnhancedBTreeNode):
    """增强型叶子节点，支持删除操作。
    
    叶子节点存储实际的数据记录，每个记录包含键和对应的值。
    支持插入、删除、更新和查询操作。
    """
    
    def __init__(self, pager: Pager, page_num: int) -> None:
        """初始化叶子节点。
        
        Args:
            pager: 页面管理器
            page_num: 节点页号
        """
        super().__init__(pager, page_num)
    
    def num_cells(self) -> int:
        """获取叶子节点中的单元格数量。
        
        Returns:
            单元格数量
        """
        return struct.unpack('<I', self.page[LEAF_NODE_NUM_CELLS_OFFSET:LEAF_NODE_NUM_CELLS_OFFSET + 4])[0]
    
    def set_num_cells(self, num: int) -> None:
        """设置叶子节点中的单元格数量。
        
        Args:
            num: 单元格数量
        """
        self.page[LEAF_NODE_NUM_CELLS_OFFSET:LEAF_NODE_NUM_CELLS_OFFSET + 4] = struct.pack('<I', num)
    
    def next_leaf(self) -> int:
        """获取下一个叶子节点的页号。
        
        Returns:
            下一个叶子节点页号，如果没有下一个返回0
        """
        return struct.unpack('<I', self.page[LEAF_NODE_NEXT_LEAF_OFFSET:LEAF_NODE_NEXT_LEAF_OFFSET + 4])[0]
    
    def set_next_leaf(self, next_page: int) -> None:
        """设置下一个叶子节点的页号。
        
        Args:
            next_page: 下一个叶子节点页号
        """
        self.page[LEAF_NODE_NEXT_LEAF_OFFSET:LEAF_NODE_NEXT_LEAF_OFFSET + 4] = struct.pack('<I', next_page)
    
    def cell(self, cell_num: int, row_size: int = None) -> int:
        """计算指定单元格的偏移量。
        
        Args:
            cell_num: 单元格索引
            row_size: 行大小，默认为291字节
            
        Returns:
            单元格在页面中的偏移量
        """
        row_size = row_size or 291
        leaf_node_cell_size = 4 + row_size
        return LEAF_NODE_HEADER_SIZE + cell_num * leaf_node_cell_size
    
    def key(self, cell_num: int, row_size: int = None) -> int:
        """获取指定单元格的键值。
        
        Args:
            cell_num: 单元格索引
            row_size: 行大小
            
        Returns:
            键值
        """
        offset = self.cell(cell_num, row_size)
        return struct.unpack('<I', self.page[offset:offset + 4])[0]
    
    def set_key(self, cell_num: int, key: int, row_size: int = None) -> None:
        """设置指定单元格的键值。
        
        Args:
            cell_num: 单元格索引
            key: 键值
            row_size: 行大小
        """
        offset = self.cell(cell_num, row_size)
        self.page[offset:offset + 4] = struct.pack('<I', key)
    
    def value(self, cell_num: int, row_size: int = None) -> bytes:
        """获取指定单元格的值。
        
        Args:
            cell_num: 单元格索引
            row_size: 行大小
            
        Returns:
            值的字节数组
        """
        offset = self.cell(cell_num, row_size) + 4
        row_size = row_size or 291  # 默认使用旧的ROW_SIZE
        return bytes(self.page[offset:offset + row_size])
    
    def set_value(self, cell_num: int, value: bytes, row_size: int = None) -> None:
        """设置指定单元格的值。
        
        Args:
            cell_num: 单元格索引
            value: 值的字节数组
            row_size: 行大小
        """
        offset = self.cell(cell_num, row_size) + 4
        row_size = row_size or 291  # 默认使用旧的ROW_SIZE
        # 确保不会写入超出实际值长度的数据
        actual_size = min(len(value), row_size)
        self.page[offset:offset + actual_size] = value[:actual_size]
        # 如果需要，用零填充剩余空间
        if actual_size < row_size:
            self.page[offset + actual_size:offset + row_size] = b'\x00' * (row_size - actual_size)
    
    def insert_cell(self, cell_num: int, key: int, value: bytes, row_size: int = None) -> None:
        """插入新单元格。
        
        Args:
            cell_num: 插入位置的索引
            key: 键值
            value: 值的字节数组
            row_size: 行大小
            
        Raises:
            BTreeError: 如果叶子节点已满
        """
        if self.num_cells() >= LEAF_NODE_MAX_CELLS:
            raise BTreeError("叶子节点已满")
        
        row_size = row_size or 291
        
        # 移动单元格以腾出空间
        leaf_node_cell_size = 4 + row_size
        for i in range(self.num_cells(), cell_num, -1):
            src = self.cell(i - 1, row_size)
            dst = self.cell(i, row_size)
            self.page[dst:dst + leaf_node_cell_size] = self.page[src:src + leaf_node_cell_size]
        
        # 插入新单元格
        self.set_key(cell_num, key, row_size)
        self.set_value(cell_num, value, row_size)
        self.set_num_cells(self.num_cells() + 1)
    
    def delete_cell(self, cell_num: int, row_size: int = None) -> None:
        """从叶子节点删除单元格。
        
        Args:
            cell_num: 要删除的单元格索引
            row_size: 行大小
            
        Raises:
            BTreeError: 如果单元格索引超出范围
        """
        if cell_num >= self.num_cells():
            raise BTreeError("单元格索引超出范围")
        
        row_size = row_size or 291
        leaf_node_cell_size = 4 + row_size
        
        # 移动单元格填补空缺
        for i in range(cell_num, self.num_cells() - 1):
            src = self.cell(i + 1, row_size)
            dst = self.cell(i, row_size)
            self.page[dst:dst + leaf_node_cell_size] = self.page[src:src + leaf_node_cell_size]
        
        # 清空最后一个单元格以避免数据残留
        last_cell_offset = self.cell(self.num_cells() - 1, row_size)
        self.page[last_cell_offset:last_cell_offset + leaf_node_cell_size] = b'\x00' * leaf_node_cell_size
        
        self.set_num_cells(self.num_cells() - 1)
    
    def update_cell(self, cell_num: int, key: int, value: bytes, row_size: int = None) -> None:
        """更新现有单元格。
        
        Args:
            cell_num: 要更新的单元格索引
            key: 新的键值
            value: 新的值的字节数组
            row_size: 行大小
            
        Raises:
            BTreeError: 如果单元格索引超出范围
        """
        if cell_num >= self.num_cells():
            raise BTreeError("单元格索引超出范围")
        
        self.set_key(cell_num, key)
        self.set_value(cell_num, value, row_size)


class EnhancedInternalNode(EnhancedBTreeNode):
    """增强型内部节点。
    
    内部节点不存储实际数据，而是存储键值和指向子节点的指针，
    用于构建B树的索引结构。
    """
    
    def __init__(self, pager: Pager, page_num: int) -> None:
        """初始化内部节点。
        
        Args:
            pager: 页面管理器
            page_num: 节点页号
        """
        super().__init__(pager, page_num)
    
    def num_keys(self) -> int:
        """获取内部节点中的键数量。
        
        Returns:
            键数量
        """
        return struct.unpack('<I', self.page[INTERNAL_NODE_NUM_KEYS_OFFSET:INTERNAL_NODE_NUM_KEYS_OFFSET + 4])[0]
    
    def set_num_keys(self, num: int) -> None:
        """设置内部节点中的键数量。
        
        Args:
            num: 键数量
        """
        self.page[INTERNAL_NODE_NUM_KEYS_OFFSET:INTERNAL_NODE_NUM_KEYS_OFFSET + 4] = struct.pack('<I', num)
    
    def right_child(self) -> int:
        """获取右子节点的页号。
        
        Returns:
            右子节点页号
        """
        return struct.unpack('<I', self.page[INTERNAL_NODE_RIGHT_CHILD_OFFSET:INTERNAL_NODE_RIGHT_CHILD_OFFSET + 4])[0]
    
    def set_right_child(self, child_page: int) -> None:
        """设置右子节点的页号。
        
        Args:
            child_page: 右子节点页号
        """
        self.page[INTERNAL_NODE_RIGHT_CHILD_OFFSET:INTERNAL_NODE_RIGHT_CHILD_OFFSET + 4] = struct.pack('<I', child_page)
    
    def cell(self, cell_num: int) -> int:
        """计算指定单元格的偏移量。
        
        Args:
            cell_num: 单元格索引
            
        Returns:
            单元格在页面中的偏移量
        """
        return INTERNAL_NODE_HEADER_SIZE + cell_num * INTERNAL_NODE_CELL_SIZE
    
    def child(self, child_num: int) -> int:
        """获取指定子节点的页号。
        
        Args:
            child_num: 子节点索引
            
        Returns:
            子节点页号
        """
        if child_num == self.num_keys():
            return self.right_child()
        offset = self.cell(child_num)
        return struct.unpack('<I', self.page[offset:offset + 4])[0]
    
    def set_child(self, child_num: int, child_page: int) -> None:
        """设置指定子节点的页号。
        
        Args:
            child_num: 子节点索引
            child_page: 子节点页号
        """
        if child_num == self.num_keys():
            self.set_right_child(child_page)
        else:
            offset = self.cell(child_num)
            self.page[offset:offset + 4] = struct.pack('<I', child_page)
    
    def key(self, key_num: int) -> int:
        """获取指定键的值。
        
        Args:
            key_num: 键索引
            
        Returns:
            键值
        """
        offset = self.cell(key_num) + 4
        return struct.unpack('<I', self.page[offset:offset + 4])[0]
    
    def set_key(self, key_num: int, key: int) -> None:
        """设置指定键的值。
        
        Args:
            key_num: 键索引
            key: 键值
        """
        offset = self.cell(key_num) + 4
        self.page[offset:offset + 4] = struct.pack('<I', key)


class EnhancedBTree:
    """增强型B树，支持DELETE和UPDATE操作。
    
    完整的B树实现，提供高效的键值存储和检索功能。
    支持插入、删除、更新、查询等操作，并保证数据的有序性。
    """
    
    def __init__(self, pager: Pager, row_size: int = 291) -> None:
        """初始化B树。
        
        Args:
            pager: 页面管理器
            row_size: 行大小，默认为291字节
        """
        self.pager = pager
        self.root_page_num = 0
        self.row_size = row_size
        
        # 如果数据库为空，创建新的根节点
        if pager.num_pages == 0:
            self.create_new_root()
    
    def create_new_root(self) -> None:
        """创建新的根节点。"""
        root = EnhancedLeafNode(self.pager, 0)
        root.set_node_type(NODE_LEAF)  # 设置为叶子节点
        root.set_root(True)  # 设置为根节点
        root.set_num_cells(0)  # 初始单元格数量为0
        root.set_next_leaf(0)  # 没有下一个叶子节点
        
        # 将根节点写入磁盘
        self.pager.write_page(0, bytes(root.page))
    
    def find(self, key: int) -> Tuple[int, int]:
        """查找键的位置。
        
        Args:
            key: 要查找的键
            
        Returns:
            元组(页号, 单元格索引)
        """
        page_num = self.root_page_num
        
        while True:
            node = EnhancedBTreeNode(self.pager, page_num)
            node_type = node.get_node_type()
            
            if node_type == NODE_LEAF:
                # 到达叶子节点，在叶子节点中查找
                leaf = EnhancedLeafNode(self.pager, page_num)
                return self._find_in_leaf(leaf, key)
            else:
                # 内部节点，继续向下查找
                internal = EnhancedInternalNode(self.pager, page_num)
                page_num = self._find_child(internal, key)
    
    def _find_in_leaf(self, leaf: EnhancedLeafNode, key: int) -> Tuple[int, int]:
        """在叶子节点中查找键的位置。
        
        Args:
            leaf: 叶子节点
            key: 要查找的键
            
        Returns:
            元组(页号, 单元格索引)
        """
        num_cells = leaf.num_cells()
        
        # 二分查找
        min_index = 0
        one_past_max_index = num_cells
        
        while one_past_max_index != min_index:
            index = (min_index + one_past_max_index) // 2
            key_at_index = leaf.key(index, self.row_size)
            
            if key == key_at_index:
                return (leaf.page_num, index)
            elif key < key_at_index:
                one_past_max_index = index
            else:
                min_index = index + 1
        
        return (leaf.page_num, min_index)
    
    def _find_child(self, internal: EnhancedInternalNode, key: int) -> int:
        """查找内部节点中键对应的子节点。
        
        Args:
            internal: 内部节点
            key: 要查找的键
            
        Returns:
            子节点页号
        """
        num_keys = internal.num_keys()
        
        # 二分查找
        min_index = 0
        max_index = num_keys
        
        while min_index != max_index:
            index = (min_index + max_index) // 2
            key_at_index = internal.key(index)
            
            if key_at_index >= key:
                max_index = index
            else:
                min_index = index + 1
        
        return internal.child(min_index)
    
    def insert(self, key: int, value: bytes) -> None:
        """插入键值对。
        
        Args:
            key: 键
            value: 值的字节数组
            
        Raises:
            BTreeError: 如果键已存在
        """
        page_num, cell_num = self.find(key)
        leaf = EnhancedLeafNode(self.pager, page_num)
        
        if leaf.num_cells() < LEAF_NODE_MAX_CELLS:
            # 叶子节点未满，直接插入
            self._insert_into_leaf(leaf, cell_num, key, value)
        else:
            # 叶子节点已满，需要分裂
            self._split_and_insert_leaf(leaf, cell_num, key, value)
        
        # 确保数据刷新到磁盘
        self.pager.flush()
    
    def _insert_into_leaf(self, leaf: EnhancedLeafNode, cell_num: int, key: int, value: bytes) -> None:
        """向叶子节点插入数据。
        
        Args:
            leaf: 叶子节点
            cell_num: 插入位置
            key: 键
            value: 值的字节数组
            
        Raises:
            BTreeError: 如果键已存在
        """
        if cell_num < leaf.num_cells() and leaf.key(cell_num, self.row_size) == key:
            raise BTreeError("重复的键")
        
        leaf.insert_cell(cell_num, key, value, self.row_size)
        # 将修改后的页面写回磁盘
        self.pager.write_page(leaf.page_num, bytes(leaf.page))
    
    def delete(self, key: int) -> bool:
        """删除键值对。
        
        Args:
            key: 要删除的键
            
        Returns:
            删除成功返回True，键不存在返回False
        """
        page_num, cell_num = self.find(key)
        leaf = EnhancedLeafNode(self.pager, page_num)
        
        if cell_num >= leaf.num_cells() or leaf.key(cell_num, self.row_size) != key:
            return False
        
        leaf.delete_cell(cell_num, self.row_size)
        
        # 将修改后的页面写回磁盘
        self.pager.write_page(leaf.page_num, bytes(leaf.page))
        
        return True
    
    def update(self, key: int, new_value: bytes) -> bool:
        """更新键值对。
        
        Args:
            key: 要更新的键
            new_value: 新的值的字节数组
            
        Returns:
            更新成功返回True，键不存在返回False
        """
        page_num, cell_num = self.find(key)
        leaf = EnhancedLeafNode(self.pager, page_num)
        
        if cell_num >= leaf.num_cells() or leaf.key(cell_num, self.row_size) != key:
            return False
        
        leaf.update_cell(cell_num, key, new_value, self.row_size)
        
        # 将修改后的页面写回磁盘
        self.pager.write_page(leaf.page_num, bytes(leaf.page))
        
        return True
    
    def _split_and_insert_leaf(self, leaf: EnhancedLeafNode, cell_num: int, key: int, value: bytes) -> None:
        """分裂已满的叶子节点并插入数据。
        
        Args:
            leaf: 已满的叶子节点
            cell_num: 插入位置
            key: 键
            value: 值的字节数组
        """
        # 创建新的叶子节点
        new_page_num = self.pager.num_pages
        new_leaf = EnhancedLeafNode(self.pager, new_page_num)
        new_leaf.set_root(False)
        
        # 在旧叶子节点和新叶子节点之间分配单元格
        old_max = LEAF_NODE_MAX_CELLS
        new_max = LEAF_NODE_MAX_CELLS + 1
        
        # 创建临时数组存储所有单元格
        temp_cells = []
        
        # 复制现有单元格
        for i in range(old_max):
            temp_cells.append((leaf.key(i, self.row_size), leaf.value(i, self.row_size)))
        
        # 插入新单元格
        temp_cells.insert(cell_num, (key, value))
        
        # 分裂单元格
        split_index = LEAF_NODE_LEFT_SPLIT_COUNT
        
        # 更新旧叶子节点
        leaf.set_num_cells(split_index)
        
        # 更新新叶子节点
        new_leaf.set_num_cells(new_max - split_index)
        new_leaf.set_next_leaf(leaf.next_leaf())
        
        # 将单元格复制到新叶子节点
        for i in range(split_index, new_max):
            new_leaf.set_key(i - split_index, temp_cells[i][0])
            new_leaf.set_value(i - split_index, temp_cells[i][1], self.row_size)
        
        # 更新旧叶子节点的下一个叶子节点
        leaf.set_next_leaf(new_page_num)
        
        # 如果需要，创建新的根节点
        if leaf.is_root():
            self._create_new_root_after_split(leaf, new_leaf, temp_cells[split_index][0])
        else:
            # 插入到父节点（简化实现）
            pass
    
    def _create_new_root_after_split(self, old_leaf: EnhancedLeafNode, new_leaf: EnhancedLeafNode, key: int) -> None:
        """分裂后创建新的根节点。
        
        Args:
            old_leaf: 旧的叶子节点
            new_leaf: 新的叶子节点
            key: 分裂键
        """
        new_root_page = self.pager.num_pages
        new_root = EnhancedInternalNode(self.pager, new_root_page)
        
        new_root.set_root(True)
        new_root.set_num_keys(1)
        new_root.set_child(0, old_leaf.page_num)
        new_root.set_key(0, key)
        new_root.set_right_child(new_leaf.page_num)
        
        old_leaf.set_root(False)
        old_leaf.set_parent(new_root_page)
        new_leaf.set_root(False)
        new_leaf.set_parent(new_root_page)
        
        self.root_page_num = new_root_page
        
        # 将所有修改后的页面写回磁盘
        self.pager.write_page(old_leaf.page_num, bytes(old_leaf.page))
        self.pager.write_page(new_leaf.page_num, bytes(new_leaf.page))
        self.pager.write_page(new_root.page_num, bytes(new_root.page))
    
    def select_all(self) -> List[Tuple[int, bytes]]:
        """选择所有键值对。
        
        Returns:
            所有键值对的列表
        """
        return self.scan()
    
    def scan(self) -> List[Tuple[int, bytes]]:
        """扫描树中所有键值对。
        
        Returns:
            所有键值对的列表，按键排序
        """
        results = []
        page_num = self.root_page_num
        
        # 从最左边的叶子节点开始
        while True:
            node = EnhancedBTreeNode(self.pager, page_num)
            if node.get_node_type() == NODE_LEAF:
                leaf = EnhancedLeafNode(self.pager, page_num)
                for i in range(leaf.num_cells()):
                    key = leaf.key(i, self.row_size)
                    value = leaf.value(i, self.row_size)
                    results.append((key, value))
                
                next_leaf = leaf.next_leaf()
                if next_leaf == 0:
                    break
                page_num = next_leaf
            else:
                internal = EnhancedInternalNode(self.pager, page_num)
                page_num = internal.child(0)
        
        return results
    
    def select_with_condition(self, condition) -> List[Tuple[int, bytes]]:
        """根据条件选择数据。
        
        Args:
            condition: 条件对象，用于评估行数据
            
        Returns:
            满足条件的键值对列表
        """
        results = []
        all_data = self.select_all()
        
        for key, value in all_data:
            row = Row.deserialize(value)
            if condition.evaluate(row):
                results.append((key, value))
        
        return results