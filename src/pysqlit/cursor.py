"""游标实现模块，用于B树的遍历。

提供游标功能来遍历B树中的数据，支持：
- 顺序遍历
- 随机访问
- 插入、删除操作
- 游标定位
"""

from typing import Optional, Tuple
from .btree import BTree, LeafNode, InternalNode
from .storage import Pager
from .models import Row


class Cursor:
    """B树遍历游标。
    
    提供对B树中数据的顺序访问和随机访问功能。
    支持向前移动、获取当前值、插入和删除操作。
    """
    
    def __init__(self, btree: BTree, page_num: int, cell_num: int, end_of_table: bool = False) -> None:
        """初始化游标。
        
        Args:
            btree: 关联的B树实例
            page_num: 当前页号
            cell_num: 当前单元格索引
            end_of_table: 是否到达表末尾
        """
        self.btree = btree
        self.page_num = page_num
        self.cell_num = cell_num
        self.end_of_table = end_of_table
    
    def advance(self) -> None:
        """将游标移动到下一个位置。
        
        如果当前叶子节点的单元格已经遍历完，
        则移动到下一个叶子节点。
        """
        if self.end_of_table:
            return
        
        leaf = LeafNode(self.btree.pager, self.page_num)
        
        self.cell_num += 1
        if self.cell_num >= leaf.num_cells():
            # 移动到下一个叶子节点
            next_page = leaf.next_leaf()
            if next_page == 0:
                self.end_of_table = True
            else:
                self.page_num = next_page
                self.cell_num = 0
    
    def get_value(self) -> Optional[Row]:
        """获取当前行的值。
        
        Returns:
            当前行的Row对象，如果到达末尾返回None
        """
        if self.end_of_table:
            return None
        
        leaf = LeafNode(self.btree.pager, self.page_num)
        if self.cell_num >= leaf.num_cells():
            return None
        
        value = leaf.value(self.cell_num)
        return Row.deserialize(value)
    
    def get_key(self) -> Optional[int]:
        """获取当前键的值。
        
        Returns:
            当前键值，如果到达末尾返回None
        """
        if self.end_of_table:
            return None
        
        leaf = LeafNode(self.btree.pager, self.page_num)
        if self.cell_num >= leaf.num_cells():
            return None
        
        return leaf.key(self.cell_num)
    
    def insert(self, row: Row) -> None:
        """在当前位置插入一行数据。
        
        Args:
            row: 要插入的数据行
        """
        if self.end_of_table:
            # 在末尾插入
            key = self.btree.pager.num_pages * 1000 + self.cell_num
        else:
            key = self.get_key()
        
        serialized = row.serialize()
        self.btree.insert(key, serialized)
    
    def delete(self) -> None:
        """删除当前行。
        
        TODO: 实现删除功能
        """
        # TODO: 实现删除功能
        pass
    
    def is_at_end(self) -> bool:
        """检查游标是否在表末尾。
        
        Returns:
            在末尾返回True，否则返回False
        """
        return self.end_of_table
    
    def reset(self) -> None:
        """将游标重置到表开始位置。
        
        找到最左边的叶子节点，并将游标定位到第一个单元格。
        """
        # 找到最左边的叶子节点
        page_num = self.btree.root_page_num
        
        while True:
            node = self.btree.pager.get_page(page_num)
            if node[0] == 0:  # 叶子节点
                self.page_num = page_num
                self.cell_num = 0
                self.end_of_table = False
                break
            else:
                # 内部节点 - 转到最左边的子节点
                internal = InternalNode(self.btree.pager, page_num)
                page_num = internal.child(0)


class CursorFactory:
    """游标工厂类，用于创建各种类型的游标。
    
    提供创建不同位置游标的便捷方法。
    """
    
    def __init__(self, btree: BTree) -> None:
        """初始化游标工厂。
        
        Args:
            btree: 关联的B树实例
        """
        self.btree = btree
    
    def create_start_cursor(self) -> Cursor:
        """创建指向表开始的游标。
        
        Returns:
            指向第一个数据行的游标
        """
        # 找到最左边的叶子节点
        page_num = self.btree.root_page_num
        
        while True:
            node = self.btree.pager.get_page(page_num)
            if node[0] == 0:  # 叶子节点
                return Cursor(self.btree, page_num, 0, False)
            else:
                # 内部节点 - 转到最左边的子节点
                internal = InternalNode(self.btree.pager, page_num)
                page_num = internal.child(0)
    
    def create_end_cursor(self) -> Cursor:
        """创建指向表末尾的游标。
        
        Returns:
            指向表末尾的游标
        """
        # 找到最右边的叶子节点
        page_num = self.btree.root_page_num
        
        while True:
            node = self.btree.pager.get_page(page_num)
            if node[0] == 0:  # 叶子节点
                leaf = LeafNode(self.btree.pager, page_num)
                if leaf.num_cells() == 0:
                    return Cursor(self.btree, page_num, 0, True)
                else:
                    return Cursor(self.btree, page_num, leaf.num_cells(), True)
            else:
                # 内部节点 - 转到最右边的子节点
                internal = InternalNode(self.btree.pager, page_num)
                page_num = internal.right_child()
    
    def create_find_cursor(self, key: int) -> Cursor:
        """创建指向特定键的游标。
        
        Args:
            key: 要查找的键
            
        Returns:
            指向该键的游标，如果键不存在则指向插入位置
        """
        page_num, cell_num = self.btree.find(key)
        leaf = LeafNode(self.btree.pager, page_num)
        
        if cell_num < leaf.num_cells() and leaf.key(cell_num) == key:
            return Cursor(self.btree, page_num, cell_num, False)
        else:
            # 键未找到，返回指向插入位置的游标
            return Cursor(self.btree, page_num, cell_num, False)