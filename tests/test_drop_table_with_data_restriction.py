"""Test DROP TABLE with data restriction functionality."""

import pytest
import tempfile
import os

from pysqlit.database import EnhancedDatabase
from pysqlit.models import Row
from pysqlit.exceptions import DatabaseError


def test_drop_table_with_data_should_fail():
    """Test that dropping table with existing data should fail."""
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
        table.insert_row(Row(id=2, name="Bob"))
        
        # 验证数据存在
        assert table.get_row_count() == 2
        
        # 尝试删除包含数据的表，应该失败
        with pytest.raises(DatabaseError, match="无法删除包含数据的表"):
            db.drop_table("test")
        
        # 验证表仍然存在
        assert "test" in db.tables
        
        # 验证数据仍然存在
        assert table.get_row_count() == 2
        
        db.close()
        
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_drop_empty_table_should_succeed():
    """Test that dropping empty table should succeed."""
    # 创建临时数据库文件
    temp_dir = tempfile.mkdtemp(prefix="pysqlit_test_")
    db_path = os.path.join(temp_dir, "test.db")
    
    try:
        # 创建数据库
        db = EnhancedDatabase(db_path)
        
        # 创建表（不插入数据）
        db.create_table("test", {"id": "INTEGER", "name": "TEXT"}, primary_key="id")
        table = db.tables["test"]
        
        # 验证表是空的
        assert table.get_row_count() == 0
        
        # 删除空表，应该成功
        result = db.drop_table("test")
        assert result is True
        assert "test" not in db.tables
        
        db.close()
        
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_drop_table_after_deleting_data_should_succeed():
    """Test that dropping table after deleting all data should succeed."""
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
        table.insert_row(Row(id=2, name="Bob"))
        
        # 验证数据存在
        assert table.get_row_count() == 2
        
        # 删除所有数据
        deleted_count = table.delete_rows()
        assert deleted_count == 2
        
        # 验证表现在是空的
        assert table.get_row_count() == 0
        
        # 删除空表，应该成功
        result = db.drop_table("test")
        assert result is True
        assert "test" not in db.tables
        
        db.close()
        
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_drop_table_with_data_should_fail()
    test_drop_empty_table_should_succeed()
    test_drop_table_after_deleting_data_should_succeed()
    print("All tests passed!")