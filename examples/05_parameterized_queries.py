#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数化查询和SQL注入防护示例
演示如何使用参数化查询防止SQL注入攻击
"""

import sqlite3
from pathlib import Path
import re

def setup_security_demo():
    """设置安全演示环境"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 创建用户认证表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_auth (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 清空现有数据
        cursor.execute("DELETE FROM user_auth")
        
        # 插入示例用户（包括管理员）
        users = [
            ('admin', 'admin123', 'admin@example.com', 1),
            ('alice', 'alice123', 'alice@example.com', 0),
            ('bob', 'bob123', 'bob@example.com', 0),
            ('charlie', 'charlie123', 'charlie@example.com', 0),
            ("admin'--", 'fakepass', 'fake@example.com', 0)  # 恶意用户名示例
        ]
        
        cursor.executemany(
            "INSERT INTO user_auth (username, password, email, is_admin) VALUES (?, ?, ?, ?)",
            users
        )
        
        conn.commit()
        print("安全演示环境设置完成")
        
    except sqlite3.Error as e:
        print(f"设置安全演示环境时出错: {e}")
        conn.rollback()
    finally:
        conn.close()

def vulnerable_login(username, password):
    """不安全的登录函数（演示SQL注入风险）"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 危险的字符串拼接方式
        query = f"SELECT * FROM user_auth WHERE username = '{username}' AND password = '{password}'"
        print(f"执行的查询: {query}")
        
        cursor.execute(query)
        user = cursor.fetchone()
        
        if user:
            print(f"❌ 登录成功! 用户: {user[1]}, 管理员权限: {'是' if user[4] else '否'}")
            return True
        else:
            print("❌ 登录失败")
            return False
            
    except sqlite3.Error as e:
        print(f"查询错误: {e}")
        return False
    finally:
        conn.close()

def secure_login(username, password):
    """安全的登录函数（使用参数化查询）"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 安全的参数化查询
        query = "SELECT * FROM user_auth WHERE username = ? AND password = ?"
        print(f"执行的查询: {query} 参数: ({username}, {password})")
        
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        
        if user:
            print(f"✅ 登录成功! 用户: {user[1]}, 管理员权限: {'是' if user[4] else '否'}")
            return True
        else:
            print("✅ 登录失败")
            return False
            
    except sqlite3.Error as e:
        print(f"查询错误: {e}")
        return False
    finally:
        conn.close()

def sql_injection_demo():
    """SQL注入攻击演示"""
    
    print("\n=== SQL注入攻击演示 ===")
    
    # 常见的SQL注入攻击示例
    injection_attacks = [
        # 绕过认证
        ("admin'--", "any_password"),
        ("admin' OR '1'='1", "any_password"),
        ("' OR 1=1--", "any_password"),
        ("' UNION SELECT null, username, password, email, is_admin FROM user_auth--", "any"),
        
        # 数据泄露
        ("' OR 1=1 LIMIT 1 OFFSET 1--", "any"),
    ]
    
    print("\n--- 使用不安全的登录函数 ---")
    for username, password in injection_attacks:
        print(f"\n尝试攻击: 用户名='{username}', 密码='{password}'")
        vulnerable_login(username, password)
    
    print("\n--- 使用安全的登录函数 ---")
    for username, password in injection_attacks:
        print(f"\n尝试攻击: 用户名='{username}', 密码='{password}'")
        secure_login(username, password)

def advanced_parameterized_queries():
    """高级参数化查询示例"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== 高级参数化查询示例 ===")
        
        # 创建订单表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_name VARCHAR(100),
                quantity INTEGER,
                price DECIMAL(10,2),
                order_date DATE,
                status VARCHAR(20) DEFAULT 'pending'
            )
        """)
        
        # 清空订单表
        cursor.execute("DELETE FROM orders")
        
        # 插入示例订单
        orders = [
            (1, '笔记本电脑', 2, 5999.99, '2024-01-15'),
            (2, '智能手机', 1, 2999.99, '2024-01-16'),
            (1, '无线耳机', 3, 299.99, '2024-01-17'),
            (3, '机械键盘', 1, 399.99, '2024-01-18'),
            (2, '显示器', 2, 1299.99, '2024-01-19')
        ]
        
        cursor.executemany(
            "INSERT INTO orders (user_id, product_name, quantity, price, order_date) VALUES (?, ?, ?, ?, ?)",
            orders
        )
        
        conn.commit()
        
        # 1. 使用IN查询
        user_ids = [1, 2, 3]
        placeholders = ','.join('?' * len(user_ids))
        query = f"SELECT * FROM orders WHERE user_id IN ({placeholders})"
        cursor.execute(query, user_ids)
        results = cursor.fetchall()
        print(f"用户 {user_ids} 的订单: {len(results)} 条")
        
        # 2. 使用LIKE查询（带通配符）
        search_term = '%笔记本%'
        cursor.execute(
            "SELECT * FROM orders WHERE product_name LIKE ?",
            (search_term,)
        )
        results = cursor.fetchall()
        print(f"产品包含'笔记本'的订单: {len(results)} 条")
        
        # 3. 使用BETWEEN查询
        cursor.execute(
            "SELECT * FROM orders WHERE price BETWEEN ? AND ?",
            (1000, 5000)
        )
        results = cursor.fetchall()
        print(f"价格在1000-5000之间的订单: {len(results)} 条")
        
        # 4. 使用日期范围查询
        cursor.execute(
            "SELECT * FROM orders WHERE order_date BETWEEN ? AND ?",
            ('2024-01-15', '2024-01-17')
        )
        results = cursor.fetchall()
        print(f"2024-01-15到2024-01-17的订单: {len(results)} 条")
        
        # 5. 动态构建查询
        conditions = []
        params = []
        
        # 动态添加条件
        min_price = 500
        max_price = 4000
        user_id = 1
        
        conditions.append("price >= ?")
        params.append(min_price)
        
        conditions.append("price <= ?")
        params.append(max_price)
        
        conditions.append("user_id = ?")
        params.append(user_id)
        
        where_clause = " AND ".join(conditions)
        query = f"SELECT * FROM orders WHERE {where_clause}"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        print(f"动态查询结果: {len(results)} 条")
        
    except sqlite3.Error as e:
        print(f"高级查询出错: {e}")
        conn.rollback()
    finally:
        conn.close()

def input_validation_demo():
    """输入验证和清理示例"""
    
    def validate_username(username):
        """验证用户名格式"""
        if not username:
            return False, "用户名不能为空"
        
        if len(username) < 3 or len(username) > 20:
            return False, "用户名长度必须在3-20个字符之间"
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "用户名只能包含字母、数字和下划线"
        
        return True, "用户名有效"
    
    def sanitize_input(user_input):
        """清理用户输入"""
        # 移除前后空格
        user_input = user_input.strip()
        
        # 移除潜在的SQL注入字符
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_']
        for char in dangerous_chars:
            user_input = user_input.replace(char, '')
        
        return user_input
    
    print("\n=== 输入验证和清理示例 ===")
    
    test_inputs = [
        "admin",
        "user123",
        "admin'--",
        "user; DROP TABLE users--",
        "  user  ",
        "user@123",
        "a",
        "verylongusernamethatexceedslimit"
    ]
    
    for test_input in test_inputs:
        is_valid, message = validate_username(test_input)
        sanitized = sanitize_input(test_input)
        print(f"输入: '{test_input}' -> 有效: {is_valid}, 消息: {message}, 清理后: '{sanitized}'")

if __name__ == "__main__":
    # 设置环境
    setup_security_demo()
    
    # SQL注入演示
    sql_injection_demo()
    
    # 高级参数化查询
    advanced_parameterized_queries()
    
    # 输入验证演示
    input_validation_demo()