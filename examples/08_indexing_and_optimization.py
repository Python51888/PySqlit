#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
索引和性能优化示例
演示如何使用Python sqlite3库创建索引和优化查询性能
"""

import sqlite3
from pathlib import Path
import time
import random
from datetime import datetime, timedelta

def setup_optimization_demo():
    """设置性能优化演示环境"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 创建性能测试表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_name VARCHAR(100),
                category VARCHAR(50),
                price DECIMAL(10,2),
                quantity INTEGER,
                order_date DATE,
                status VARCHAR(20),
                region VARCHAR(50),
                customer_email VARCHAR(100)
            )
        """)
        
        # 创建索引测试表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS index_test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username VARCHAR(50),
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 清空表
        cursor.execute("DELETE FROM performance_test")
        cursor.execute("DELETE FROM index_test")
        
        conn.commit()
        print("性能优化演示环境设置完成")
        
    except sqlite3.Error as e:
        print(f"设置环境时出错: {e}")
        conn.rollback()
    finally:
        conn.close()

def generate_large_dataset(count):
    """生成大数据集用于性能测试"""
    
    products = [
        '笔记本电脑', '智能手机', '无线耳机', '机械键盘', '显示器',
        '办公椅', '办公桌', '台灯', '咖啡机', '空气净化器',
        '鼠标', '键盘', '摄像头', '打印机', '扫描仪'
    ]
    
    categories = ['电子产品', '家具', '家电', '办公用品', '数码配件']
    regions = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京', '天津']
    statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    
    data = []
    
    for i in range(count):
        user_id = random.randint(1, 10000)
        product = random.choice(products)
        category = random.choice(categories)
        price = round(random.uniform(10, 5000), 2)
        quantity = random.randint(1, 10)
        
        # 生成随机日期
        days_offset = random.randint(0, 730)  # 2年数据
        order_date = (datetime.now() - timedelta(days=days_offset)).strftime('%Y-%m-%d')
        
        status = random.choice(statuses)
        region = random.choice(regions)
        email = f"user{user_id}@example.com"
        
        data.append((
            user_id, product, category, price, quantity,
            order_date, status, region, email
        ))
    
    return data

def performance_test_without_index():
    """无索引情况下的性能测试"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== 无索引性能测试 ===")
        
        # 插入测试数据
        print("插入测试数据...")
        data = generate_large_dataset(50000)
        
        start_time = time.time()
        cursor.executemany("""
            INSERT INTO performance_test 
            (user_id, product_name, category, price, quantity, order_date, status, region, customer_email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        insert_time = time.time() - start_time
        
        print(f"插入 {len(data)} 条记录耗时: {insert_time:.3f} 秒")
        
        # 测试查询性能
        test_queries = [
            ("按用户ID查询", "SELECT * FROM performance_test WHERE user_id = 1234"),
            ("按产品名称查询", "SELECT * FROM performance_test WHERE product_name = '笔记本电脑'"),
            ("按价格范围查询", "SELECT * FROM performance_test WHERE price BETWEEN 1000 AND 2000"),
            ("按日期范围查询", "SELECT * FROM performance_test WHERE order_date BETWEEN '2024-01-01' AND '2024-03-31'"),
            ("按状态查询", "SELECT * FROM performance_test WHERE status = 'delivered'"),
            ("按区域查询", "SELECT * FROM performance_test WHERE region = '北京'"),
            ("复合条件查询", "SELECT * FROM performance_test WHERE category = '电子产品' AND price > 1000 AND region = '上海'"),
            ("聚合查询", "SELECT region, COUNT(*) as order_count, AVG(price) as avg_price FROM performance_test GROUP BY region"),
            ("排序查询", "SELECT * FROM performance_test ORDER BY price DESC LIMIT 100"),
            ("连接查询", "SELECT p1.* FROM performance_test p1 JOIN performance_test p2 ON p1.user_id = p2.user_id WHERE p1.category = '电子产品'")
        ]
        
        print("\n执行无索引查询测试...")
        for query_name, query in test_queries:
            start_time = time.time()
            cursor.execute(query)
            results = cursor.fetchall()
            query_time = time.time() - start_time
            
            print(f"{query_name}: {query_time:.3f} 秒 ({len(results)} 条结果)")
        
    except sqlite3.Error as e:
        print(f"无索引测试出错: {e}")
    finally:
        conn.close()

def create_indexes():
    """创建索引"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== 创建索引 ===")
        
        # 单列索引
        indexes = [
            ("idx_user_id", "CREATE INDEX idx_user_id ON performance_test(user_id)"),
            ("idx_product_name", "CREATE INDEX idx_product_name ON performance_test(product_name)"),
            ("idx_price", "CREATE INDEX idx_price ON performance_test(price)"),
            ("idx_order_date", "CREATE INDEX idx_order_date ON performance_test(order_date)"),
            ("idx_status", "CREATE INDEX idx_status ON performance_test(status)"),
            ("idx_region", "CREATE INDEX idx_region ON performance_test(region)"),
            ("idx_category", "CREATE INDEX idx_category ON performance_test(category)")
        ]
        
        for index_name, create_sql in indexes:
            start_time = time.time()
            cursor.execute(create_sql)
            create_time = time.time() - start_time
            print(f"创建 {index_name} 耗时: {create_time:.3f} 秒")
        
        # 复合索引
        composite_indexes = [
            ("idx_category_price", "CREATE INDEX idx_category_price ON performance_test(category, price)"),
            ("idx_region_status", "CREATE INDEX idx_region_status ON performance_test(region, status)"),
            ("idx_date_user", "CREATE INDEX idx_date_user ON performance_test(order_date, user_id)")
        ]
        
        for index_name, create_sql in composite_indexes:
            start_time = time.time()
            cursor.execute(create_sql)
            create_time = time.time() - start_time
            print(f"创建 {index_name} 耗时: {create_time:.3f} 秒")
        
        conn.commit()
        print("所有索引创建完成")
        
    except sqlite3.Error as e:
        print(f"创建索引出错: {e}")
    finally:
        conn.close()

def performance_test_with_index():
    """有索引情况下的性能测试"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== 有索引性能测试 ===")
        
        # 使用相同的测试查询
        test_queries = [
            ("按用户ID查询", "SELECT * FROM performance_test WHERE user_id = 1234"),
            ("按产品名称查询", "SELECT * FROM performance_test WHERE product_name = '笔记本电脑'"),
            ("按价格范围查询", "SELECT * FROM performance_test WHERE price BETWEEN 1000 AND 2000"),
            ("按日期范围查询", "SELECT * FROM performance_test WHERE order_date BETWEEN '2024-01-01' AND '2024-03-31'"),
            ("按状态查询", "SELECT * FROM performance_test WHERE status = 'delivered'"),
            ("按区域查询", "SELECT * FROM performance_test WHERE region = '北京'"),
            ("复合条件查询", "SELECT * FROM performance_test WHERE category = '电子产品' AND price > 1000 AND region = '上海'"),
            ("聚合查询", "SELECT region, COUNT(*) as order_count, AVG(price) as avg_price FROM performance_test GROUP BY region"),
            ("排序查询", "SELECT * FROM performance_test ORDER BY price DESC LIMIT 100"),
            ("连接查询", "SELECT p1.* FROM performance_test p1 JOIN performance_test p2 ON p1.user_id = p2.user_id WHERE p1.category = '电子产品'")
        ]
        
        print("\n执行有索引查询测试...")
        for query_name, query in test_queries:
            start_time = time.time()
            cursor.execute(query)
            results = cursor.fetchall()
            query_time = time.time() - start_time
            
            print(f"{query_name}: {query_time:.3f} 秒 ({len(results)} 条结果)")
        
    except sqlite3.Error as e:
        print(f"有索引测试出错: {e}")
    finally:
        conn.close()

def analyze_query_plan():
    """查询计划分析"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== 查询计划分析 ===")
        
        # 分析查询计划
        queries_to_analyze = [
            "SELECT * FROM performance_test WHERE user_id = 1234",
            "SELECT * FROM performance_test WHERE category = '电子产品' AND price > 1000",
            "SELECT * FROM performance_test WHERE order_date BETWEEN '2024-01-01' AND '2024-03-31'"
        ]
        
        for query in queries_to_analyze:
            print(f"\n查询: {query}")
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            plan = cursor.fetchall()
            
            for row in plan:
                print(f"  {row}")
        
    except sqlite3.Error as e:
        print(f"查询计划分析出错: {e}")
    finally:
        conn.close()

def index_size_analysis():
    """索引大小分析"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== 索引大小分析 ===")
        
        # 获取所有索引
        cursor.execute("""
            SELECT name, sql FROM sqlite_master 
            WHERE type='index' AND tbl_name='performance_test'
        """)
        indexes = cursor.fetchall()
        
        print(f"总索引数: {len(indexes)}")
        
        # 获取数据库大小
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        
        db_size = page_count * page_size
        
        print(f"数据库总大小: {db_size} 字节 ({db_size/1024/1024:.2f} MB)")
        
        # 获取表大小
        cursor.execute("SELECT COUNT(*) FROM performance_test")
        table_rows = cursor.fetchone()[0]
        print(f"表记录数: {table_rows}")
        
    except sqlite3.Error as e:
        print(f"索引大小分析出错: {e}")
    finally:
        conn.close()

def optimize_database():
    """数据库优化"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    
    try:
        print("\n=== 数据库优化 ===")
        
        # 分析数据库
        conn.execute("ANALYZE")
        print("已执行ANALYZE命令")
        
        # 重建索引
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='performance_test'")
        indexes = cursor.fetchall()
        
        for index_name, in indexes:
            cursor.execute(f"REINDEX {index_name}")
            print(f"已重建索引: {index_name}")
        
        # 清理数据库
        conn.execute("VACUUM")
        print("已执行VACUUM命令")
        
        conn.commit()
        print("数据库优化完成")
        
    except sqlite3.Error as e:
        print(f"数据库优化出错: {e}")
    finally:
        conn.close()

def partial_index_demo():
    """部分索引示例"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== 部分索引示例 ===")
        
        # 创建部分索引（只为特定条件的记录创建索引）
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_high_value_orders 
            ON performance_test(price) 
            WHERE price > 3000
        """)
        
        # 创建表达式索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_total_value 
            ON performance_test(price * quantity)
        """)
        
        conn.commit()
        print("部分索引创建完成")
        
    except sqlite3.Error as e:
        print(f"部分索引创建出错: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # 设置环境
    setup_optimization_demo()
    
    # 无索引性能测试
    performance_test_without_index()
    
    # 创建索引
    create_indexes()
    
    # 有索引性能测试
    performance_test_with_index()
    
    # 查询计划分析
    analyze_query_plan()
    
    # 索引大小分析
    index_size_analysis()
    
    # 部分索引演示
    partial_index_demo()
    
    # 数据库优化
    optimize_database()