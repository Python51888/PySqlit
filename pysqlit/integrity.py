#!/usr/bin/env python3
"""数据库完整性检查和验证模块。

该模块提供了数据库文件的完整性检查功能，包括：
- 页面大小验证
- 文件结构检查
- 数据一致性验证
- 自动修复功能

主要功能：
1. 验证数据库文件是否符合预期的页面大小
2. 检测并修复页面大小不匹配的问题
3. 执行全面的数据库完整性检查
4. 提供详细的检查报告
"""

import os
from typing import Optional
from .constants import PAGE_SIZE
from .exceptions import DatabaseError


class IntegrityChecker:
    """数据库完整性检查器。
    
    该类提供了一系列静态方法来检查和验证数据库文件的完整性，
    确保数据库文件结构正确且数据一致。
    
    主要检查项目：
    - 文件存在性检查
    - 页面大小验证
    - 文件大小对齐检查
    - 数据完整性验证
    
    Examples:
        >>> # 检查数据库完整性
        >>> result = IntegrityChecker.check_database_integrity("test.db")
        >>> if result['page_size_valid']:
        ...     print("数据库文件结构正常")
    """
    
    @staticmethod
    def validate_page_size(file_path: str) -> bool:
        """验证数据库文件的页面大小是否正确。
        
        检查数据库文件大小是否是页面大小的整数倍，这是数据库文件
        结构完整性的基本要求。
        
        Args:
            file_path: 数据库文件路径
            
        Returns:
            bool: 验证通过返回True
            
        Raises:
            DatabaseError: 如果文件大小不是页面大小的整数倍
            
        Examples:
            >>> IntegrityChecker.validate_page_size("test.db")
            True
        """
        if not os.path.exists(file_path):
            return True  # 新文件视为有效
            
        file_size = os.path.getsize(file_path)
        
        if file_size == 0:
            return True  # 空文件视为有效
            
        if file_size % PAGE_SIZE != 0:
            raise DatabaseError(
                f"数据库文件大小 {file_size} 不是页面大小 {PAGE_SIZE} 的整数倍。 "
                f"余数: {file_size % PAGE_SIZE} 字节"
            )
            
        return True
    
    @staticmethod
    def repair_page_size(file_path: str) -> bool:
        """尝试通过零填充修复页面大小问题。
        
        当数据库文件大小不是页面大小的整数倍时，通过在文件末尾
        添加零字节来修复这个问题。
        
        Args:
            file_path: 数据库文件路径
            
        Returns:
            bool: 修复成功返回True
            
        Raises:
            DatabaseError: 如果修复失败
            
        Examples:
            >>> IntegrityChecker.repair_page_size("test.db")
            True
        """
        if not os.path.exists(file_path):
            return False
            
        file_size = os.path.getsize(file_path)
        remainder = file_size % PAGE_SIZE
        
        if remainder == 0:
            return True  # 已经正确，无需修复
            
        padding_needed = PAGE_SIZE - remainder
        
        try:
            with open(file_path, 'ab') as f:
                f.write(b'\x00' * padding_needed)
            return True
        except Exception as e:
            raise DatabaseError(f"修复页面大小失败: {e}")
    
    @staticmethod
    def check_database_integrity(file_path: str) -> dict:
        """执行全面的数据库完整性检查。
        
        该方法对数据库文件进行全面的完整性检查，返回详细的检查结果。
        
        Args:
            file_path: 数据库文件路径
            
        Returns:
            dict: 检查结果字典，包含：
                - file_exists: 文件是否存在
                - page_size_valid: 页面大小是否有效
                - file_size: 文件大小（字节）
                - num_pages: 页面数量
                - errors: 错误信息列表
                
        Examples:
            >>> result = IntegrityChecker.check_database_integrity("test.db")
            >>> print(f"页面数量: {result['num_pages']}")
            >>> print(f"错误数量: {len(result['errors'])}")
        """
        result = {
            'file_exists': False,
            'page_size_valid': False,
            'file_size': 0,
            'num_pages': 0,
            'errors': []
        }
        
        if not os.path.exists(file_path):
            result['errors'].append("数据库文件不存在")
            return result
            
        result['file_exists'] = True
        result['file_size'] = os.path.getsize(file_path)
        
        try:
            IntegrityChecker.validate_page_size(file_path)
            result['page_size_valid'] = True
            result['num_pages'] = result['file_size'] // PAGE_SIZE
        except DatabaseError as e:
            result['errors'].append(str(e))
            
        return result