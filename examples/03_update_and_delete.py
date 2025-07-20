#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据更新和删除示例
演示如何使用Python sqlite3库更新和删除数据
"""

import sqlite3
from pathlib import Path

def update_data():
    """更新数据示例"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("=== 更新数据前 ===")
        cursor.execute("SELECT id, username, age FROM users WHERE username = 'alice'")
        alice_before = cursor.fetchone()
        print(f"Alice更新前: ID={alice_before[0]}, 年龄={alice_before[2]}")
        
        # 更新单个字段
        cursor.execute(
            "UPDATE users SET age = ? WHERE username = ?",
            (29, 'alice')
        )
        
        # 更新多个字段
        cursor.execute(
            "UPDATE products SET price = ?, stock = ? WHERE name = ?",
            (2499.99, 30, '智能手机')
        )
        
        conn.commit()
        print("数据更新成功")
        
        print("\n=== 更新数据后 ===")
        cursor.execute("SELECT id, username, age FROM users WHERE username = 'alice'")
        alice_after = cursor.fetchone()
        print(f"Alice更新后: ID={alice_after[0]}, 年龄={alice_after[2]}")
        
        cursor.execute("SELECT name, price, stock FROM products WHERE name = '智能手机'")
        phone = cursor.fetchone()
        print(f"智能手机更新后: 价格=¥{phone[1]}, 库存={phone[2]}")
        
        # 批量更新
        print("\n=== 批量更新示例 ===")
        cursor.execute(
            "UPDATE products SET stock = stock + 10 WHERE stock < 20"
        )
        conn.commit()
        
        cursor.execute("SELECT name, stock FROM products WHERE stock >= 20")
        updated_products = cursor.fetchall()
        print("库存更新后的产品:", updated_products)
        
    except sqlite3.Error as e:
        print(f"更新数据时出错: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_data():
    """删除数据示例"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== 删除数据前统计 ===")
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count_before = cursor.fetchone()[0]
        print(f"删除前用户总数: {user_count_before}")
        
        # 删除单条记录
        cursor.execute("DELETE FROM users WHERE username = 'eve'")
        
        # 删除多条记录（基于条件）
        cursor.execute("DELETE FROM products WHERE stock = 0")
        
        conn.commit()
        print("数据删除成功")
        
        print("\n=== 删除数据后统计 ===")
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count_after = cursor.fetchone()[0]
        print(f"删除后用户总数: {user_count_after}")
        
        # 显示剩余用户
        cursor.execute("SELECT id, username FROM users ORDER BY id")
        remaining_users = cursor.fetchall()
        print("剩余用户:", remaining_users)
        
        # 清空整个表
        print("\n=== 清空表示例 ===")
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        print(f"清空前产品总数: {product_count}")
        
        # 使用TRUNCATE方式（SQLite使用DELETE）
        cursor.execute("DELETE FROM products")
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count_after = cursor.fetchone()[0]
        print(f"清空后产品总数: {product_count_after}")
        
    except sqlite3.Error as e:
        print(f"删除数据时出错: {e}")
        conn.rollback()
    finally:
        conn.close()

def safe_delete_example():
    """安全删除示例（带确认）"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 重新插入一些数据用于删除示例
        sample_data = [
            ('test1', 'test1@example.com', 25),
            ('test2', 'test2@example.com', 30),
            ('test3', 'test3@example.com', 35)
        ]
        
        cursor.executemany(
            "INSERT INTO users (username, email, age) VALUES (?, ?, ?)",
            sample_data
        )
        conn.commit()
        
        print("\n=== 安全删除示例 ===")
        
        # 显示将要删除的数据
        cursor.execute("SELECT id, username, age FROM users WHERE username LIKE 'test%'")
        to_delete = cursor.fetchall()
        print("将要删除的用户:", to_delete)
        
        # 确认删除
        confirm = input("确认删除这些用户吗? (y/n): ")
        if confirm.lower() == 'y':
            cursor.execute("DELETE FROM users WHERE username LIKE 'test%'")
            conn.commit()
            print("测试用户已删除")
        else:
            print("取消删除操作")
        
        # 验证删除结果
        cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE 'test%'")
        remaining = cursor.fetchone()[0]
        print(f"剩余的测试用户: {remaining}")
        
    except sqlite3.Error as e:
        print(f"删除数据时出错: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    # 确保有数据可以操作
    import subprocess
    examples_dir = Path(__file__).parent
    
    subprocess.run(["python", "01_basic_connection.py"], cwd=examples_dir)
    subprocess.run(["python", "02_insert_and_query.py"], cwd=examples_dir)
    
    # 执行更新和删除操作
    update_data()
    delete_data()
    safe_delete_example()