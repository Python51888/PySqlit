"""Test DROP TABLE fix for proper error messages."""

import pytest
import tempfile
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pysqlit.database import EnhancedDatabase
from pysqlit.models import Row
from pysqlit.exceptions import DatabaseError


def test_drop_nonexistent_table_error_message():
    """Test that dropping a non-existent table shows proper error message."""
    # 创建临时数据库文件
    temp_dir = tempfile.mkdtemp(prefix="pysqlit_test_")
    db_path = os.path.join(temp_dir, "test.db")
    
    try:
        # 创建数据库
        db = EnhancedDatabase(db_path)
        
        # 尝试删除不存在的表，应该显示"表不存在"错误
        try:
            db.drop_table("nonexistent")
            assert False, "Should have raised DatabaseError"
        except DatabaseError as e:
            error_msg = str(e)
            assert "不存在" in error_msg or "not found" in error_msg.lower()
        
        db.close()
        
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_drop_table_with_data_error_message():
    """Test that dropping table with data shows proper error message."""
    # 创建临时数据库文件
    temp_dir = tempfile.mkdtemp(prefix="pysqlit_test_")
    db_path = os.path.join(temp_dir, "test.db")
    
    try:
        # 创建数据库
        db = EnhancedDatabase(db_path)
        
        # 创建表并插入数据
        db.create_table("test", {"id": "INTEGER", "name": "TEXT"}, primary_key="id")
        table = db.tables["test"]
        table.insert_row(Row(id=1, name="Alice"))
        
        # 验证数据存在
        assert table.get_row_count() == 1
        
        # 尝试删除包含数据的表，应该显示"表不为空"错误
        try:
            db.drop_table("test")
            assert False, "Should have raised DatabaseError"
        except DatabaseError as e:
            error_msg = str(e)
            assert "无法删除包含数据的表" in error_msg or "not empty" in error_msg.lower() or "数据" in error_msg
        
        # 验证表仍然存在
        assert "test" in db.tables
        
        db.close()
        
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_drop_nonexistent_table_error_message()
    test_drop_table_with_data_error_message()
    print("All tests passed!")