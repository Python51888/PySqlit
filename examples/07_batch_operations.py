#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量操作示例
演示如何使用Python sqlite3库进行高效的批量数据操作
"""

import sqlite3
from pathlib import Path
import time
import random
from datetime import datetime, timedelta

def setup_batch_demo():
    """设置批量操作演示环境"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 创建批量操作演示表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                customer_id INTEGER,
                quantity INTEGER,
                price DECIMAL(10,2),
                sale_date DATE,
                region VARCHAR(50)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products_batch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100),
                category VARCHAR(50),
                price DECIMAL(10,2),
                stock INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 清空表
        cursor.execute("DELETE FROM sales")
        cursor.execute("DELETE FROM products_batch")
        
        conn.commit()
        print("批量操作演示环境设置完成")
        
    except sqlite3.Error as e:
        print(f"设置环境时出错: {e}")
        conn.rollback()
    finally:
        conn.close()

def generate_sample_data(count):
    """生成示例数据"""
    
    products = [
        ('笔记本电脑', '电子产品', 5999.99),
        ('智能手机', '电子产品', 2999.99),
        ('无线耳机', '电子产品', 299.99),
        ('机械键盘', '电子产品', 399.99),
        ('显示器', '电子产品', 1299.99),
        ('办公椅', '家具', 899.99),
        ('办公桌', '家具', 1299.99),
        ('台灯', '家具', 199.99),
        ('咖啡机', '家电', 899.99),
        ('空气净化器', '家电', 1299.99)
    ]
    
    regions = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安']
    
    sales_data = []
    start_date = datetime(2024, 1, 1)
    
    for i in range(count):
        product = random.choice(products)
        days_offset = random.randint(0, 365)
        sale_date = start_date + timedelta(days=days_offset)
        
        sales_data.append((
            random.randint(1, 1000),  # product_id
            random.randint(1, 500),   # customer_id
            random.randint(1, 10),    # quantity
            product[2],               # price
            sale_date.strftime('%Y-%m-%d'),
            random.choice(regions)    # region
        ))
    
    return sales_data, products

def single_insert_vs_batch_insert():
    """单条插入 vs 批量插入性能对比"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    # 生成测试数据
    sales_data, _ = generate_sample_data(1000)
    
    print("\n=== 单条插入 vs 批量插入性能对比 ===")
    
    # 方法1: 单条插入
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    start_time = time.time()
    
    cursor.execute("DELETE FROM sales")
    
    for sale in sales_data:
        cursor.execute("""
            INSERT INTO sales (product_id, customer_id, quantity, price, sale_date, region)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sale)
    
    conn.commit()
    single_insert_time = time.time() - start_time
    conn.close()
    
    # 方法2: 批量插入 executemany
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    start_time = time.time()
    
    cursor.execute("DELETE FROM sales")
    
    cursor.executemany("""
        INSERT INTO sales (product_id, customer_id, quantity, price, sale_date, region)
        VALUES (?, ?, ?, ?, ?, ?)
    """, sales_data)
    
    conn.commit()
    batch_insert_time = time.time() - start_time
    conn.close()
    
    print(f"单条插入耗时: {single_insert_time:.3f} 秒")
    print(f"批量插入耗时: {batch_insert_time:.3f} 秒")
    print(f"性能提升: {single_insert_time / batch_insert_time:.1f}x")
    
    return single_insert_time, batch_insert_time

def batch_update_demo():
    """批量更新示例"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== 批量更新示例 ===")
        
        # 插入测试数据
        sales_data, _ = generate_sample_data(100)
        cursor.executemany("""
            INSERT INTO sales (product_id, customer_id, quantity, price, sale_date, region)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sales_data)
        conn.commit()
        
        # 显示更新前数据
        cursor.execute("SELECT COUNT(*) FROM sales WHERE region = '北京'")
        beijing_count_before = cursor.fetchone()[0]
        print(f"更新前北京区域订单数: {beijing_count_before}")
        
        # 批量更新
        start_time = time.time()
        
        cursor.execute("""
            UPDATE sales 
            SET region = '北京-更新' 
            WHERE region = '北京'
        """)
        
        conn.commit()
        update_time = time.time() - start_time
        
        cursor.execute("SELECT COUNT(*) FROM sales WHERE region = '北京-更新'")
        updated_count = cursor.fetchone()[0]
        
        print(f"批量更新耗时: {update_time:.3f} 秒")
        print(f"更新记录数: {updated_count}")
        
    except sqlite3.Error as e:
        print(f"批量更新出错: {e}")
        conn.rollback()
    finally:
        conn.close()

def batch_delete_demo():
    """批量删除示例"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== 批量删除示例 ===")
        
        # 插入测试数据
        sales_data, _ = generate_sample_data(200)
        cursor.executemany("""
            INSERT INTO sales (product_id, customer_id, quantity, price, sale_date, region)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sales_data)
        conn.commit()
        
        # 显示删除前总数
        cursor.execute("SELECT COUNT(*) FROM sales")
        total_before = cursor.fetchone()[0]
        print(f"删除前总记录数: {total_before}")
        
        # 批量删除
        start_time = time.time()
        
        cursor.execute("""
            DELETE FROM sales 
            WHERE quantity < 3 AND price < 1000
        """)
        
        deleted_count = cursor.rowcount
        conn.commit()
        delete_time = time.time() - start_time
        
        cursor.execute("SELECT COUNT(*) FROM sales")
        total_after = cursor.fetchone()[0]
        
        print(f"批量删除耗时: {delete_time:.3f} 秒")
        print(f"删除记录数: {deleted_count}")
        print(f"剩余记录数: {total_after}")
        
    except sqlite3.Error as e:
        print(f"批量删除出错: {e}")
        conn.rollback()
    finally:
        conn.close()

def transaction_batch_operations():
    """事务中的批量操作"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== 事务中的批量操作 ===")
        
        # 清空产品表
        cursor.execute("DELETE FROM products_batch")
        
        # 生成产品数据
        _, products = generate_sample_data(0)
        
        start_time = time.time()
        
        # 开始事务
        cursor.executemany("""
            INSERT INTO products_batch (name, category, price, stock)
            VALUES (?, ?, ?, ?)
        """, [(p[0], p[1], p[2], random.randint(10, 100)) for p in products * 10])
        
        # 批量更新库存
        cursor.execute("""
            UPDATE products_batch 
            SET stock = stock + 50 
            WHERE category = '电子产品'
        """)
        
        # 批量更新价格
        cursor.execute("""
            UPDATE products_batch 
            SET price = price * 1.1 
            WHERE price < 1000
        """)
        
        # 提交事务
        conn.commit()
        transaction_time = time.time() - start_time
        
        # 验证结果
        cursor.execute("SELECT COUNT(*) FROM products_batch")
        total_products = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(stock) FROM products_batch")
        total_stock = cursor.fetchone()[0]
        
        print(f"事务批量操作耗时: {transaction_time:.3f} 秒")
        print(f"总产品数: {total_products}")
        print(f"总库存: {total_stock}")
        
    except sqlite3.Error as e:
        print(f"事务批量操作出错: {e}")
        conn.rollback()
    finally:
        conn.close()

def large_dataset_handling():
    """大数据集处理示例"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== 大数据集处理示例 ===")
        
        # 清空销售表
        cursor.execute("DELETE FROM sales")
        
        # 生成大数据集
        large_dataset, _ = generate_sample_data(10000)
        
        # 分批处理
        batch_size = 1000
        total_batches = len(large_dataset) // batch_size + (1 if len(large_dataset) % batch_size else 0)
        
        start_time = time.time()
        
        for i in range(0, len(large_dataset), batch_size):
            batch = large_dataset[i:i+batch_size]
            cursor.executemany("""
                INSERT INTO sales (product_id, customer_id, quantity, price, sale_date, region)
                VALUES (?, ?, ?, ?, ?, ?)
            """, batch)
            
            if (i // batch_size + 1) % 5 == 0:
                conn.commit()
                print(f"已处理 {i // batch_size + 1}/{total_batches} 批次")
        
        conn.commit()
        total_time = time.time() - start_time
        
        cursor.execute("SELECT COUNT(*) FROM sales")
        total_records = cursor.fetchone()[0]
        
        print(f"大数据集处理完成")
        print(f"总记录数: {total_records}")
        print(f"总耗时: {total_time:.3f} 秒")
        print(f"平均速度: {total_records/total_time:.0f} 条/秒")
        
    except sqlite3.Error as e:
        print(f"大数据集处理出错: {e}")
        conn.rollback()
    finally:
        conn.close()

def memory_vs_file_performance():
    """内存数据库 vs 文件数据库性能对比"""
    
    print("\n=== 内存数据库 vs 文件数据库性能对比 ===")
    
    # 生成测试数据
    sales_data, _ = generate_sample_data(5000)
    
    # 内存数据库测试
    conn_mem = sqlite3.connect(':memory:')
    cursor_mem = conn_mem.cursor()
    
    # 创建表
    cursor_mem.execute("""
        CREATE TABLE sales_mem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            customer_id INTEGER,
            quantity INTEGER,
            price DECIMAL(10,2),
            sale_date DATE,
            region VARCHAR(50)
        )
    """)
    
    start_time = time.time()
    cursor_mem.executemany("""
        INSERT INTO sales_mem (product_id, customer_id, quantity, price, sale_date, region)
        VALUES (?, ?, ?, ?, ?, ?)
    """, sales_data)
    conn_mem.commit()
    mem_time = time.time() - start_time
    
    # 文件数据库测试
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn_file = sqlite3.connect(db_path)
    cursor_file = conn_file.cursor()
    
    cursor_file.execute("DELETE FROM sales")
    
    start_time = time.time()
    cursor_file.executemany("""
        INSERT INTO sales (product_id, customer_id, quantity, price, sale_date, region)
        VALUES (?, ?, ?, ?, ?, ?)
    """, sales_data)
    conn_file.commit()
    file_time = time.time() - start_time
    
    conn_mem.close()
    conn_file.close()
    
    print(f"内存数据库插入耗时: {mem_time:.3f} 秒")
    print(f"文件数据库插入耗时: {file_time:.3f} 秒")
    print(f"内存数据库性能提升: {file_time/mem_time:.1f}x")

if __name__ == "__main__":
    # 设置环境
    setup_batch_demo()
    
    # 性能对比
    single_insert_vs_batch_insert()
    
    # 批量操作演示
    batch_update_demo()
    batch_delete_demo()
    transaction_batch_operations()
    
    # 大数据集处理
    large_dataset_handling()
    
    # 内存 vs 文件性能对比
    memory_vs_file_performance()