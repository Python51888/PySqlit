#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事务处理示例
演示如何使用Python sqlite3库进行事务处理，包括提交和回滚
"""

import sqlite3
from pathlib import Path
import random

def setup_accounts_table():
    """创建账户表用于事务示例"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 创建账户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_number VARCHAR(20) UNIQUE NOT NULL,
                account_holder VARCHAR(50) NOT NULL,
                balance DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 清空现有数据
        cursor.execute("DELETE FROM accounts")
        
        # 插入示例账户
        accounts = [
            ('ACC001', '张三', 1000.00),
            ('ACC002', '李四', 2000.00),
            ('ACC003', '王五', 1500.00),
            ('ACC004', '赵六', 3000.00)
        ]
        
        cursor.executemany(
            "INSERT INTO accounts (account_number, account_holder, balance) VALUES (?, ?, ?)",
            accounts
        )
        
        conn.commit()
        print("账户表创建成功，示例数据已插入")
        
    except sqlite3.Error as e:
        print(f"创建账户表时出错: {e}")
        conn.rollback()
    finally:
        conn.close()

def transfer_money(from_account, to_account, amount):
    """转账示例 - 使用事务确保数据一致性"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print(f"\n=== 转账前余额 ===")
        cursor.execute("SELECT account_number, account_holder, balance FROM accounts")
        for account in cursor.fetchall():
            print(f"{account[0]} - {account[1]}: ¥{account[2]:.2f}")
        
        # 开始事务（默认情况下，sqlite3会自动开始事务）
        
        # 检查转出账户余额是否足够
        cursor.execute(
            "SELECT balance FROM accounts WHERE account_number = ?",
            (from_account,)
        )
        from_balance = cursor.fetchone()
        
        if not from_balance:
            raise ValueError(f"转出账户 {from_account} 不存在")
        
        if from_balance[0] < amount:
            raise ValueError(f"转出账户余额不足，当前余额: ¥{from_balance[0]:.2f}")
        
        # 检查转入账户是否存在
        cursor.execute(
            "SELECT balance FROM accounts WHERE account_number = ?",
            (to_account,)
        )
        to_balance = cursor.fetchone()
        
        if not to_balance:
            raise ValueError(f"转入账户 {to_account} 不存在")
        
        # 执行转账操作
        # 1. 从转出账户扣款
        cursor.execute(
            "UPDATE accounts SET balance = balance - ? WHERE account_number = ?",
            (amount, from_account)
        )
        
        # 2. 向转入账户加款
        cursor.execute(
            "UPDATE accounts SET balance = balance + ? WHERE account_number = ?",
            (amount, to_account)
        )
        
        # 3. 记录交易日志
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_account VARCHAR(20),
                to_account VARCHAR(20),
                amount DECIMAL(10,2),
                transaction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute(
            "INSERT INTO transactions (from_account, to_account, amount) VALUES (?, ?, ?)",
            (from_account, to_account, amount)
        )
        
        # 提交事务
        conn.commit()
        print(f"\n✅ 转账成功: {from_account} -> {to_account}, 金额: ¥{amount:.2f}")
        
        print(f"\n=== 转账后余额 ===")
        cursor.execute("SELECT account_number, account_holder, balance FROM accounts")
        for account in cursor.fetchall():
            print(f"{account[0]} - {account[1]}: ¥{account[2]:.2f}")
        
    except (sqlite3.Error, ValueError) as e:
        # 发生错误时回滚事务
        conn.rollback()
        print(f"\n❌ 转账失败: {e}")
        print("事务已回滚，所有更改已撤销")
    finally:
        conn.close()

def transaction_rollback_demo():
    """事务回滚演示"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== 事务回滚演示 ===")
        
        # 显示初始余额
        cursor.execute("SELECT account_number, balance FROM accounts WHERE account_number = 'ACC001'")
        initial_balance = cursor.fetchone()[1]
        print(f"ACC001初始余额: ¥{initial_balance:.2f}")
        
        # 开始一系列操作
        cursor.execute(
            "UPDATE accounts SET balance = balance - 100 WHERE account_number = 'ACC001'"
        )
        
        cursor.execute(
            "UPDATE accounts SET balance = balance + 100 WHERE account_number = 'ACC002'"
        )
        
        # 模拟一个错误
        raise Exception("模拟错误，触发回滚")
        
        # 这行代码不会执行
        conn.commit()
        
    except Exception as e:
        # 回滚所有更改
        conn.rollback()
        print(f"发生错误: {e}")
        print("事务已回滚")
        
        # 验证余额是否恢复
        cursor.execute("SELECT account_number, balance FROM accounts WHERE account_number = 'ACC001'")
        final_balance = cursor.fetchone()[1]
        print(f"ACC001最终余额: ¥{final_balance:.2f} (应该与初始余额相同)")
        
    finally:
        conn.close()

def savepoint_demo():
    """保存点(Savepoint)示例"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== 保存点演示 ===")
        
        # 显示初始余额
        cursor.execute("SELECT account_number, balance FROM accounts WHERE account_number = 'ACC001'")
        initial_balance = cursor.fetchone()[1]
        print(f"ACC001初始余额: ¥{initial_balance:.2f}")
        
        # 创建保存点
        cursor.execute("SAVEPOINT sp1")
        
        # 第一次更新
        cursor.execute(
            "UPDATE accounts SET balance = balance - 200 WHERE account_number = 'ACC001'"
        )
        
        cursor.execute("SELECT balance FROM accounts WHERE account_number = 'ACC001'")
        balance_after_first = cursor.fetchone()[0]
        print(f"第一次扣款后余额: ¥{balance_after_first:.2f}")
        
        # 创建第二个保存点
        cursor.execute("SAVEPOINT sp2")
        
        # 第二次更新
        cursor.execute(
            "UPDATE accounts SET balance = balance - 300 WHERE account_number = 'ACC001'"
        )
        
        cursor.execute("SELECT balance FROM accounts WHERE account_number = 'ACC001'")
        balance_after_second = cursor.fetchone()[0]
        print(f"第二次扣款后余额: ¥{balance_after_second:.2f}")
        
        # 回滚到第一个保存点
        cursor.execute("ROLLBACK TO SAVEPOINT sp1")
        
        cursor.execute("SELECT balance FROM accounts WHERE account_number = 'ACC001'")
        final_balance = cursor.fetchone()[0]
        print(f"回滚到保存点后余额: ¥{final_balance:.2f}")
        
        # 释放保存点
        cursor.execute("RELEASE SAVEPOINT sp1")
        
        conn.commit()
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"保存点操作出错: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # 设置环境
    setup_accounts_table()
    
    # 执行事务示例
    transfer_money('ACC001', 'ACC002', 500.00)
    transfer_money('ACC001', 'ACC003', 2000.00)  # 应该失败（余额不足）
    
    # 回滚演示
    transaction_rollback_demo()
    
    # 保存点演示
    savepoint_demo()