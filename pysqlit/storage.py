"""PySQLit存储层 - 处理文件I/O和数据序列化。

该模块提供了数据库的底层存储功能，包括：
- 文件I/O管理（分页存储）
- 数据序列化和反序列化
- 表数据管理
- 自动增量ID管理
- 物理删除和标记删除

主要特性：
1. 基于分页的文件存储
2. 自动增量ID管理
3. 数据完整性验证
4. 支持物理删除和标记删除
5. 上下文管理器支持
"""

import os
import struct
from typing import Optional, List
from dataclasses import dataclass

from .constants import (
    PAGE_SIZE, TABLE_MAX_PAGES, INVALID_PAGE_NUM,
    ROW_SIZE, ID_SIZE, USERNAME_SIZE, EMAIL_SIZE,
    ID_OFFSET, USERNAME_OFFSET, EMAIL_OFFSET
)
from .models import Row
from .exceptions import StorageError


class Pager:
    """分页管理器，负责文件I/O和页面缓存。
    
    提供数据库文件的分页读写功能，支持页面缓存和自动刷新。
    
    Attributes:
        filename: 数据库文件名
        file_descriptor: 文件描述符
        file_length: 文件长度（字节）
        num_pages: 页面数量
        pages: 页面缓存数组
    
    Examples:
        >>> with Pager("test.db") as pager:
        ...     page = pager.get_page(0)
        ...     # 使用页面数据
    """
    
    def __init__(self, filename: str) -> None:
        """初始化分页管理器。
        
        Args:
            filename: 数据库文件名
        """
        self.filename = filename
        self.file_descriptor = None
        self.file_length = 0
        self.num_pages = 0
        self.pages = [None] * TABLE_MAX_PAGES
        
        self._open_file()
    
    def _open_file(self) -> None:
        """打开数据库文件。
        
        如果文件不存在则创建新文件，并验证文件完整性。
        """
        try:
            if os.path.exists(self.filename):
                self.file_descriptor = open(self.filename, 'r+b')
                self.file_descriptor.seek(0, 2)  # 移动到文件末尾
                self.file_length = self.file_descriptor.tell()
                self.num_pages = self.file_length // PAGE_SIZE
                
                if self.file_length % PAGE_SIZE != 0:
                    raise StorageError("Database file is not a whole number of pages")
            else:
                self.file_descriptor = open(self.filename, 'w+b')
                self.file_length = 0
                self.num_pages = 0
        except IOError as e:
            raise StorageError(f"Unable to open database file: {e}")
    
    def get_page(self, page_num: int) -> bytearray:
        """从缓存或文件获取页面数据。
        
        如果页面不在缓存中，则从文件加载；如果页面是新页面，则创建新页面。
        
        Args:
            page_num: 页面编号
            
        Returns:
            bytearray: 页面数据
            
        Raises:
            StorageError: 如果页面编号超出最大限制
        """
        if page_num >= TABLE_MAX_PAGES:
            raise StorageError(f"Page number {page_num} exceeds maximum {TABLE_MAX_PAGES}")
        
        if self.pages[page_num] is None:
            # 缓存未命中 - 从文件加载
            page = bytearray(PAGE_SIZE)
            
            if page_num < self.num_pages:
                # 页面存在于文件中
                self.file_descriptor.seek(page_num * PAGE_SIZE)
                data = self.file_descriptor.read(PAGE_SIZE)
                if len(data) == PAGE_SIZE:
                    page[:] = data
                elif len(data) > 0:
                    # 部分页面 - 对于有效文件不应发生
                    page[:len(data)] = data
            
            self.pages[page_num] = page
            
            if page_num >= self.num_pages:
                self.num_pages = page_num + 1
        
        return self.pages[page_num]
    
    def flush_page(self, page_num: int) -> None:
        """将页面刷新到磁盘。
        
        Args:
            page_num: 要刷新的页面编号
        """
        if page_num >= self.num_pages:
            return
        
        if self.pages[page_num] is None:
            return
        
        self.file_descriptor.seek(page_num * PAGE_SIZE)
        self.file_descriptor.write(self.pages[page_num])
        self.file_descriptor.flush()
    
    def flush_all_pages(self) -> None:
        """将所有脏页面刷新到磁盘。"""
        for i in range(self.num_pages):
            if self.pages[i] is not None:
                self.flush_page(i)
    
    def close(self) -> None:
        """关闭分页管理器并清理资源。
        
        在关闭前会确保所有页面数据都已写入磁盘。
        """
        if self.file_descriptor:
            self.flush_all_pages()
            self.file_descriptor.close()
            self.file_descriptor = None
    
    def __enter__(self):
        """上下文管理器入口。
        
        Returns:
            Pager: 分页管理器实例
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口。"""
        self.close()


class RowSerializer:
    """行数据序列化器，处理Row对象的序列化和反序列化。
    
    提供将Row对象转换为字节流和从字节流恢复Row对象的功能。
    
    Examples:
        >>> row = Row(id=1, username="alice", email="alice@example.com")
        >>> data = RowSerializer.serialize(row)
        >>> new_row = RowSerializer.deserialize(data)
    """
    
    @staticmethod
    def serialize(row: Row) -> bytes:
        """将Row对象序列化为字节流。
        
        使用固定长度的二进制格式存储数据：
        - ID: 4字节无符号整数
        - 用户名: 32字节固定长度字符串
        - 邮箱: 255字节固定长度字符串
        
        Args:
            row: 要序列化的Row对象
            
        Returns:
            bytes: 序列化后的字节数据
        """
        # 将ID打包为4字节无符号整数
        id_bytes = struct.pack('<I', row.id)
        
        # 将用户名打包为固定长度字符串（32字节）
        username_bytes = row.username.encode('utf-8')
        username_bytes = username_bytes.ljust(USERNAME_SIZE, b'\x00')[:USERNAME_SIZE]
        
        # 将邮箱打包为固定长度字符串（255字节）
        email_bytes = row.email.encode('utf-8')
        email_bytes = email_bytes.ljust(EMAIL_SIZE, b'\x00')[:EMAIL_SIZE]
        
        return id_bytes + username_bytes + email_bytes
    
    @staticmethod
    def deserialize(data: bytes) -> Row:
        """将字节流反序列化为Row对象。
        
        Args:
            data: 要反序列化的字节数据
            
        Returns:
            Row: 反序列化后的Row对象
            
        Raises:
            StorageError: 如果数据长度不匹配
        """
        if len(data) != ROW_SIZE:
            raise StorageError(f"Invalid row data size: {len(data)}, expected {ROW_SIZE}")
        
        # 解包ID
        id_value = struct.unpack('<I', data[ID_OFFSET:ID_OFFSET + ID_SIZE])[0]
        
        # 解包用户名
        username_bytes = data[USERNAME_OFFSET:USERNAME_OFFSET + USERNAME_SIZE]
        username = username_bytes.rstrip(b'\x00').decode('utf-8')
        
        # 解包邮箱
        email_bytes = data[EMAIL_OFFSET:EMAIL_OFFSET + EMAIL_SIZE]
        email = email_bytes.rstrip(b'\x00').decode('utf-8')
        
        return Row(id=id_value, username=username, email=email)


class Table:
    """简单表实现，使用平面文件存储和自动增量ID。
    
    提供基本的表操作功能，包括插入、查询、删除等，支持自动增量ID。
    
    Attributes:
        pager: 分页管理器
        num_rows: 行数量
        max_id: 最大ID值（用于自动增量）
    
    Examples:
        >>> with Pager("test.db") as pager:
        ...     table = Table(pager)
        ...     table.insert_row(Row(username="alice", email="alice@example.com"))
        ...     rows = table.select_all()
    """
    
    def __init__(self, pager: Pager) -> None:
        """初始化表。
        
        Args:
            pager: 分页管理器实例
        """
        self.pager = pager
        self.num_rows = 0
        self.max_id = 0  # 跟踪最大ID用于自动增量
        
        # 计算初始行数
        if pager.file_length > 0:
            self.num_rows = pager.file_length // ROW_SIZE
        
        # 从计数器文件加载max_id
        self._load_max_id()
    
    def _load_max_id(self) -> None:
        """从计数器文件加载max_id，如果不存在则初始化。
        
        如果计数器文件不存在，则扫描现有数据找到最大ID。
        """
        counter_file = self.pager.filename + ".cnt"
        try:
            if os.path.exists(counter_file):
                with open(counter_file, 'r') as f:
                    self.max_id = int(f.read().strip())
            else:
                # 在现有数据中找到最大ID
                max_id = 0
                for i in range(self.num_rows):
                    row_position = i * ROW_SIZE
                    page_num = row_position // PAGE_SIZE
                    byte_offset = row_position % PAGE_SIZE
                    
                    page = self.pager.get_page(page_num)
                    id_bytes = bytes(page[byte_offset:byte_offset + ID_SIZE])
                    row_id = struct.unpack('<I', id_bytes)[0]
                    if row_id > max_id:
                        max_id = row_id
                
                self.max_id = max_id
                self._save_max_id()
        except Exception as e:
            raise StorageError(f"Failed to load max_id: {e}")
    
    def _save_max_id(self) -> None:
        """将max_id保存到计数器文件。
        
        确保在程序异常退出时也能正确保存最大ID值。
        """
        counter_file = self.pager.filename + ".cnt"
        try:
            with open(counter_file, 'w') as f:
                f.write(str(self.max_id))
        except Exception as e:
            raise StorageError(f"Failed to save max_id: {e}")
    
    def insert_row(self, row: Row) -> None:
        """向表中插入一行数据，支持自动增量ID。
        
        处理数据类型转换、唯一性检查和自动ID生成。
        
        Args:
            row: 要插入的Row对象
            
        Raises:
            StorageError: 如果表已满、数据类型错误或重复值
        """
        if self.num_rows >= TABLE_MAX_PAGES * (PAGE_SIZE // ROW_SIZE):
            raise StorageError("Table is full")
        
        # 确保所有数值字段都是正确的类型
        for field in ['id', 'age']:  # 添加其他数值字段
            if hasattr(row, field):
                try:
                    # 获取当前值并转换为整数
                    value = getattr(row, field)
                    if value is not None:
                        setattr(row, field, int(value))
                except (ValueError, TypeError):
                    raise StorageError(f"{field} must be an integer")
        
        # 处理自动增量ID
        try:
            id_val = row.id
            if id_val is None or id_val == 0:
                self.max_id += 1
                row.id = self.max_id
            elif id_val > self.max_id:
                self.max_id = id_val
        except AttributeError:
            # 当id属性不存在时，自动生成ID
            self.max_id += 1
            row.id = self.max_id
        
        # 保存更新后的max_id
        self._save_max_id()

        # 检查重复名称（用户名列）
        existing_rows = self.select_all()
        for existing_row in existing_rows:
            if existing_row.username == row.username:
                raise StorageError(f"Duplicate name value: {row.username}")
        
        # 计算位置
        row_position = self.num_rows * ROW_SIZE
        page_num = row_position // PAGE_SIZE
        byte_offset = row_position % PAGE_SIZE
        
        # 检查是否需要处理页面边界
        if byte_offset + ROW_SIZE > PAGE_SIZE:
            raise StorageError("Row would span page boundary")
        
        # 获取页面并写入行数据
        page = self.pager.get_page(page_num)
        serialized = RowSerializer.serialize(row)
        
        page[byte_offset:byte_offset + ROW_SIZE] = serialized
        self.num_rows += 1
    
    def select_all(self) -> List[Row]:
        """选择表中所有有效行，跳过已删除（全零）的行。
        
        Returns:
            List[Row]: 所有有效行的列表
        """
        rows = []
        
        for i in range(self.num_rows):
            row_position = i * ROW_SIZE
            page_num = row_position // PAGE_SIZE
            byte_offset = row_position % PAGE_SIZE
            
            page = self.pager.get_page(page_num)
            row_data = bytes(page[byte_offset:byte_offset + ROW_SIZE])
            
            # 跳过全零行（已删除的行）
            if all(b == 0 for b in row_data):
                continue
                
            try:
                row = RowSerializer.deserialize(row_data)
                rows.append(row)
            except StorageError:
                # 跳过无效行
                continue
        
        return rows
    
    def delete_row(self, row_id: int) -> bool:
        """按ID物理删除行，必要时更新max_id。
        
        通过将行数据设置为全零来标记删除，并更新行计数。
        
        Args:
            row_id: 要删除的行ID
            
        Returns:
            bool: 如果找到并删除行返回True，否则返回False
        """
        found = False
        new_rows = []
        
        # 收集除要删除的行外的所有有效行
        for i in range(self.num_rows):
            row_position = i * ROW_SIZE
            page_num = row_position // PAGE_SIZE
            byte_offset = row_position % PAGE_SIZE
            
            page = self.pager.get_page(page_num)
            row_data = bytes(page[byte_offset:byte_offset + ROW_SIZE])
            
            try:
                row = RowSerializer.deserialize(row_data)
                # 跳过已删除（全零）的行
                if all(b == 0 for b in row_data):
                    continue
                    
                if row.id == row_id:
                    # 通过设置为全零标记为已删除
                    page[byte_offset:byte_offset + ROW_SIZE] = bytearray(ROW_SIZE)
                    found = True
                    # 如果删除了max_id行，更新max_id
                    if row_id == self.max_id:
                        self._find_max_id()
                        self._save_max_id()
                else:
                    new_rows.append((page_num, byte_offset, row))
            except StorageError:
                # 跳过无效行
                continue
        
        # 如果删除了行，更新行计数
        if found:
            self.num_rows -= 1
        
        return found
    
    def delete_all(self) -> int:
        """删除表中的所有行。
        
        通过将所有行数据设置为全零来标记删除，并重置计数器。
        
        Returns:
            int: 删除的行数
        """
        deleted_count = 0
        
        for i in range(self.num_rows):
            row_position = i * ROW_SIZE
            page_num = row_position // PAGE_SIZE
            byte_offset = row_position % PAGE_SIZE
            
            page = self.pager.get_page(page_num)
            row_data = bytes(page[byte_offset:byte_offset + ROW_SIZE])
            
            # 跳过已删除的行
            if all(b == 0 for b in row_data):
                continue
                
            # 标记为已删除
            page[byte_offset:byte_offset + ROW_SIZE] = bytearray(ROW_SIZE)
            deleted_count += 1
        
        self.num_rows = 0
        self.max_id = 0
        self._save_max_id()
        return deleted_count
    
    def close(self) -> None:
        """关闭表。
        
        关闭关联的分页管理器。
        """
        self.pager.close()


# 使用示例
if __name__ == "__main__":
    # 简单测试
    with Pager("test.db") as pager:
        table = Table(pager)
        
        # 插入一些测试数据
        test_rows = [
            Row(1, "alice", "alice@example.com"),
            Row(2, "bob", "bob@example.com"),
            Row(3, "charlie", "charlie@example.com")
        ]
        
        for row in test_rows:
            table.insert_row(row)
        
        # 读回数据
        rows = table.select_all()
        for row in rows:
            print(row)