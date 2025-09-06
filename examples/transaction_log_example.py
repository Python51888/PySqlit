#!/usr/bin/env python3
"""
事务日志示例
演示PySQLit的事务日志功能
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pysqlit.database import EnhancedDatabase
from pysqlit.models import Row

def main():
    # 使用chao.db数据库
    db_file = "chao.db"
    
    # 初始化数据库
    print(f"初始化数据库: {db_file}")
    db = EnhancedDatabase(db_file)
    
    try:
        # 创建表（如果不存在）
        if "users" not in db.list_tables():
            print("创建users表...")
            db.create_table(
                table_name="users",
                columns={
                    "id": "INTEGER",
                    "name": "TEXT",
                    "email": "TEXT"
                },
                primary_key="id"
            )
        
        # 获取表实例
        table = db.tables["users"]
        
        # 插入一些数据
        print("插入数据...")
        table.insert_row(Row(id=1, name="张三", email="zhangsan@example.com"))
        table.insert_row(Row(id=2, name="李四", email="lisi@example.com"))
        
        # 更新数据
        print("更新数据...")
        table.update_rows(
            updates={"email": "zhangsan.new@example.com"},
            condition=None  # 更新所有行（仅更新第一条）
        )
        
        # 删除数据
        print("删除数据...")
        table.delete_rows(condition=None)  # 删除所有行
        
        # 检查日志文件
        log_file = os.path.join("db_logs", db_file + ".log")
        print(f"日志文件路径: {log_file}")
        
        if os.path.exists(log_file):
            print("日志文件存在")
            with open(log_file, 'r') as f:
                content = f.read()
                if content:
                    print("日志内容:")
                    # 格式化显示日志
                    import json
                    for line in content.strip().split('\n'):
                        if line.strip():
                            try:
                                record = json.loads(line)
                                print(f"  时间: {record['timestamp']}")
                                print(f"  操作: {record['operation']}")
                                print(f"  表名: {record['table_name']}")
                                print(f"  数据: {record['row_data']}")
                                if record.get('old_data'):
                                    print(f"  旧数据: {record['old_data']}")
                                print()
                            except json.JSONDecodeError:
                                print(f"  无法解析的日志行: {line}")
                else:
                    print("日志文件为空")
        else:
            print("日志文件不存在")
            
    except Exception as e:
        print(f"执行过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭数据库
        db.close()

if __name__ == "__main__":
    main()