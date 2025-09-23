#!/usr/bin/env python3
"""Enhanced PySQLit main entry point with ACID compliance and concurrent access."""

import sys
import os

# 添加src目录到Python路径，确保可以正确导入pysqlit模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from pysqlit.repl import EnhancedREPL
from pysqlit.art import pr_art


def main():
    
    # Prompt user for database name
    db_name = input("请输入数据库名称(将以.db结尾): ")
    if not db_name.endswith('.db'):
        db_name += '.db'
    database_file = db_name
    
    # Ensure we're in the correct directory and use absolute path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(database_file):
        database_file = os.path.join(project_root, database_file)
    # 检查数据库是否已存在
    if os.path.exists(database_file):
        print(f"数据库 '{db_name}' 已存在")
    else:
        # 创建空数据库文件
        open(database_file, 'w').close()
        print(f"已创建数据库: {db_name}")
        print('')

    pr_art()
    repl = EnhancedREPL(database_file)
    repl.run()

if __name__ == "__main__":
    main()