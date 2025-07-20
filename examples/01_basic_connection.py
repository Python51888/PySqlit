#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础数据库连接和表创建示例
演示如何使用Python内置的sqlite3库创建数据库连接和表
"""

import sqlite3
import os
from pathlib import Path

def create_database():
    """创建数据库和示例表"""
    
    # 确保examples目录存在
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    # 如果数据库已存在，先删除（仅用于示例）
    if db_path.exists():
        os.remove(db_path)
    
    # 创建数据库连接
    conn = sqlite3.connect(db_path)
    print(f"成功连接到数据库: {db_path}")
    
    # 创建游标对象
    cursor = conn.cursor()
    
    # 创建用户表
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        age INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    # 创建产品表
    create_products_table = """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        stock INTEGER DEFAULT 0,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    try:
        # 执行创建表的SQL语句
        cursor.execute(create_users_table)
        cursor.execute(create_products_table)
        
        # 提交事务
        conn.commit()
        print("成功创建users和products表")
        
        # 查看所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("数据库中的表:", [table[0] for table in tables])
        
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        conn.rollback()
    finally:
        # 关闭连接
        conn.close()
        print("数据库连接已关闭")

if __name__ == "__main__":
    create_database()