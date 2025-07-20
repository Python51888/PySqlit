#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库备份和恢复示例
演示如何使用Python sqlite3库进行数据库备份和恢复
"""

import sqlite3
import shutil
import os
from pathlib import Path
from datetime import datetime
import gzip

def create_backup_directory():
    """创建备份目录"""
    
    examples_dir = Path(__file__).parent
    backup_dir = examples_dir / "backups"
    
    if not backup_dir.exists():
        backup_dir.mkdir()
        print(f"创建备份目录: {backup_dir}")
    
    return backup_dir

def simple_file_copy_backup():
    """简单的文件复制备份"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    backup_dir = create_backup_directory()
    
    if not db_path.exists():
        print("数据库文件不存在，请先运行前面的示例")
        return
    
    try:
        # 创建带时间戳的备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"example_backup_{timestamp}.db"
        
        # 执行文件复制
        shutil.copy2(db_path, backup_path)
        
        print(f"✅ 简单备份完成")
        print(f"源文件: {db_path}")
        print(f"备份文件: {backup_path}")
        print(f"文件大小: {backup_path.stat().st_size} 字节")
        
        return backup_path
        
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return None

def sqlite_backup_api():
    """使用SQLite备份API进行备份"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    backup_dir = create_backup_directory()
    
    if not db_path.exists():
        print("数据库文件不存在，请先运行前面的示例")
        return
    
    try:
        # 创建备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"example_sqlite_backup_{timestamp}.db"
        
        # 使用SQLite备份API
        source = sqlite3.connect(str(db_path))
        backup = sqlite3.connect(str(backup_path))
        
        source.backup(backup)
        
        backup.close()
        source.close()
        
        print(f"✅ SQLite备份API完成")
        print(f"备份文件: {backup_path}")
        
        return backup_path
        
    except Exception as e:
        print(f"❌ SQLite备份失败: {e}")
        return None

def compressed_backup():
    """压缩备份"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    backup_dir = create_backup_directory()
    
    if not db_path.exists():
        print("数据库文件不存在，请先运行前面的示例")
        return
    
    try:
        # 创建压缩备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"example_backup_{timestamp}.db.gz"
        
        # 读取数据库文件并压缩
        with open(db_path, 'rb') as f_in:
            with gzip.open(backup_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        original_size = db_path.stat().st_size
        compressed_size = backup_path.stat().st_size
        compression_ratio = (original_size - compressed_size) / original_size * 100
        
        print(f"✅ 压缩备份完成")
        print(f"原始大小: {original_size} 字节")
        print(f"压缩后大小: {compressed_size} 字节")
        print(f"压缩率: {compression_ratio:.1f}%")
        
        return backup_path
        
    except Exception as e:
        print(f"❌ 压缩备份失败: {e}")
        return None

def restore_from_backup(backup_path):
    """从备份文件恢复"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    
    if not backup_path.exists():
        print(f"❌ 备份文件不存在: {backup_path}")
        return False
    
    try:
        # 创建恢复前的备份
        if db_path.exists():
            restore_backup_path = db_path.with_suffix('.db.restore_backup')
            shutil.copy2(db_path, restore_backup_path)
            print(f"已创建恢复前备份: {restore_backup_path}")
        
        # 执行恢复
        if str(backup_path).endswith('.gz'):
            # 解压恢复
            with gzip.open(backup_path, 'rb') as f_in:
                with open(db_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            print("✅ 从压缩备份恢复完成")
        else:
            # 直接复制恢复
            shutil.copy2(backup_path, db_path)
            print("✅ 从备份文件恢复完成")
        
        print(f"恢复文件: {backup_path}")
        print(f"目标文件: {db_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        return False

def incremental_backup():
    """增量备份示例（基于时间戳）"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    backup_dir = create_backup_directory()
    
    if not db_path.exists():
        print("数据库文件不存在，请先运行前面的示例")
        return
    
    try:
        # 获取文件修改时间
        db_mtime = datetime.fromtimestamp(db_path.stat().st_mtime)
        
        # 检查是否有新的备份需要
        backup_files = list(backup_dir.glob("example_incremental_*.db"))
        latest_backup = None
        
        if backup_files:
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            latest_backup_time = datetime.fromtimestamp(latest_backup.stat().st_mtime)
            
            if db_mtime <= latest_backup_time:
                print("数据库没有新的更改，无需增量备份")
                return
        
        # 创建增量备份
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"example_incremental_{timestamp}.db"
        
        shutil.copy2(db_path, backup_path)
        
        print(f"✅ 增量备份完成")
        print(f"备份文件: {backup_path}")
        
        # 清理旧备份（保留最近5个）
        all_backups = sorted(backup_dir.glob("example_incremental_*.db"), 
                           key=lambda x: x.stat().st_mtime, reverse=True)
        
        for old_backup in all_backups[5:]:
            old_backup.unlink()
            print(f"删除旧备份: {old_backup}")
        
        return backup_path
        
    except Exception as e:
        print(f"❌ 增量备份失败: {e}")
        return None

def backup_with_metadata():
    """带元数据的备份"""
    
    examples_dir = Path(__file__).parent
    db_path = examples_dir / "example.db"
    backup_dir = create_backup_directory()
    
    if not db_path.exists():
        print("数据库文件不存在，请先运行前面的示例")
        return
    
    try:
        # 创建备份
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"example_metadata_backup_{timestamp}.db"
        
        shutil.copy2(db_path, backup_path)
        
        # 创建元数据文件
        metadata_path = backup_path.with_suffix('.metadata')
        
        # 获取数据库信息
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 获取表信息
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        # 获取每个表的记录数
        table_counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            table_counts[table] = cursor.fetchone()[0]
        
        conn.close()
        
        # 写入元数据
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.write(f"备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"数据库文件: {db_path}\n")
            f.write(f"备份文件: {backup_path}\n")
            f.write(f"文件大小: {backup_path.stat().st_size} 字节\n")
            f.write("\n表信息:\n")
            for table, count in table_counts.items():
                f.write(f"  {table}: {count} 条记录\n")
        
        print(f"✅ 带元数据的备份完成")
        print(f"备份文件: {backup_path}")
        print(f"元数据文件: {metadata_path}")
        
        return backup_path
        
    except Exception as e:
        print(f"❌ 元数据备份失败: {e}")
        return None

def list_backups():
    """列出所有备份文件"""
    
    examples_dir = Path(__file__).parent
    backup_dir = examples_dir / "backups"
    
    if not backup_dir.exists():
        print("备份目录不存在")
        return
    
    print("\n=== 备份文件列表 ===")
    
    backup_files = list(backup_dir.glob("example_*.db*"))
    
    if not backup_files:
        print("没有找到备份文件")
        return
    
    for backup_file in sorted(backup_files):
        size = backup_file.stat().st_size
        mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
        print(f"{backup_file.name} - 大小: {size} 字节 - 创建时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")

def verify_backup_integrity(backup_path):
    """验证备份文件完整性"""
    
    try:
        # 尝试连接备份文件
        conn = sqlite3.connect(str(backup_path))
        cursor = conn.cursor()
        
        # 检查数据库完整性
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        
        # 获取表信息
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        conn.close()
        
        if result == 'ok':
            print(f"✅ 备份文件完整性检查通过")
            print(f"包含的表: {[table[0] for table in tables]}")
            return True
        else:
            print(f"❌ 备份文件完整性检查失败: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 验证备份文件时出错: {e}")
        return False

if __name__ == "__main__":
    print("=== 数据库备份和恢复示例 ===\n")
    
    # 确保有数据库文件
    import subprocess
    examples_dir = Path(__file__).parent
    
    if not (examples_dir / "example.db").exists():
        subprocess.run(["python", "01_basic_connection.py"], cwd=examples_dir)
        subprocess.run(["python", "02_insert_and_query.py"], cwd=examples_dir)
    
    # 执行各种备份方法
    print("\n1. 简单文件复制备份")
    backup1 = simple_file_copy_backup()
    
    print("\n2. SQLite备份API")
    backup2 = sqlite_backup_api()
    
    print("\n3. 压缩备份")
    backup3 = compressed_backup()
    
    print("\n4. 增量备份")
    backup4 = incremental_backup()
    
    print("\n5. 带元数据的备份")
    backup5 = backup_with_metadata()
    
    # 列出所有备份
    list_backups()
    
    # 验证备份完整性
    if backup1:
        print(f"\n验证备份完整性: {backup1}")
        verify_backup_integrity(backup1)
    
    # 恢复示例（可选）
    if backup1 and input("\n是否要从备份恢复? (y/n): ").lower() == 'y':
        restore_from_backup(backup1)
