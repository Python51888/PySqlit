#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据插入和查询示例
演示如何使用Python sqlite3库插入数据和执行查询操作
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random

def insert_sample_data():
    """插入示例数据"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 清空现有数据（仅用于示例）
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM products")
        
        # 插入用户数据
        users_data = [
            ('alice', 'alice@example.com', 28),
            ('bob', 'bob@example.com', 35),
            ('charlie', 'charlie@example.com', 22),
            ('diana', 'diana@example.com', 31),
            ('eve', 'eve@example.com', 27)
        ]
        
        cursor.executemany(
            "INSERT INTO users (username, email, age) VALUES (?, ?, ?)",
            users_data
        )
        
        # 插入产品数据
        products_data = [
            ('笔记本电脑', 5999.99, 10, '高性能轻薄笔记本'),
            ('智能手机', 2999.99, 25, '5G全网通智能手机'),
            ('无线耳机', 299.99, 50, '蓝牙5.0降噪耳机'),
            ('机械键盘', 399.99, 15, 'RGB背光机械键盘'),
            ('显示器', 1299.99, 8, '27英寸4K显示器')
        ]
        
        cursor.executemany(
            "INSERT INTO products (name, price, stock, description) VALUES (?, ?, ?, ?)",
            products_data
        )
        
        conn.commit()
        print("成功插入示例数据")
        print(f"插入用户数: {cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]}")
        print(f"插入产品数: {cursor.execute('SELECT COUNT(*) FROM products').fetchone()[0]}")
        
    except sqlite3.Error as e:
        print(f"插入数据时出错: {e}")
        conn.rollback()
    finally:
        conn.close()

def query_data():
    """查询数据示例"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== 查询所有用户 ===")
        cursor.execute("SELECT * FROM users ORDER BY id")
        users = cursor.fetchall()
        
        print("ID | 用户名 | 邮箱 | 年龄 | 创建时间")
        print("-" * 60)
        for user in users:
            print(f"{user[0]} | {user[1]} | {user[2]} | {user[3]} | {user[4]}")
        
        print("\n=== 查询所有产品 ===")
        cursor.execute("SELECT * FROM products ORDER BY price DESC")
        products = cursor.fetchall()
        
        print("ID | 产品名称 | 价格 | 库存 | 描述")
        print("-" * 70)
        for product in products:
            print(f"{product[0]} | {product[1]} | ¥{product[2]} | {product[3]} | {product[4]}")
        
        print("\n=== 条件查询示例 ===")
        
        # 查询年龄大于25岁的用户
        cursor.execute("SELECT username, age FROM users WHERE age > 25 ORDER BY age DESC")
        adult_users = cursor.fetchall()
        print("年龄大于25岁的用户:", adult_users)
        
        # 查询价格在1000元以上的产品
        cursor.execute("SELECT name, price FROM products WHERE price > 1000 ORDER BY price")
        expensive_products = cursor.fetchall()
        print("价格1000元以上的产品:", expensive_products)
        
        # 查询库存少于20的产品
        cursor.execute("SELECT name, stock FROM products WHERE stock < 20")
        low_stock_products = cursor.fetchall()
        print("库存少于20的产品:", low_stock_products)
        
        # 使用聚合函数
        cursor.execute("SELECT COUNT(*) as total_users, AVG(age) as avg_age FROM users")
        stats = cursor.fetchone()
        print(f"用户总数: {stats[0]}, 平均年龄: {stats[1]:.1f}岁")
        
        cursor.execute("SELECT SUM(price * stock) as total_value FROM products")
        total_value = cursor.fetchone()[0]
        print(f"产品总库存价值: ¥{total_value:.2f}")
        
    except sqlite3.Error as e:
        print(f"查询数据时出错: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # 确保数据库和表存在
    import subprocess
    subprocess.run(["python", "01_basic_connection.py"], cwd=Path(__file__).parent)
    
    # 插入和查询数据
    insert_sample_data()
    query_data()