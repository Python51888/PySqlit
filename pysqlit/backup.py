"""数据库备份和恢复管理模块。

提供数据库备份、恢复、验证和自动备份功能，确保数据安全性和可靠性。
"""

import os
import shutil
import time
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime
from .exceptions import DatabaseError


class BackupManager:
    """管理数据库备份和恢复的核心类。
    
    提供完整的数据库备份解决方案，包括：
    - 创建和管理数据库备份
    - 从备份恢复数据库
    - 自动清理旧备份
    - 备份完整性验证
    - 自动备份调度
    """
    
    def __init__(self, db_path: str):
        """初始化备份管理器。
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        # 设置备份目录为数据库所在目录的backups子目录
        self.backup_dir = os.path.join(os.path.dirname(db_path), "backups")
        self.max_backups = 10  # 最大保留备份数量
        self.lock = threading.RLock()  # 线程锁，确保并发安全
        
        # 创建备份目录（如果不存在）
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 确保备份目录正确配置
        if not os.path.exists(self.backup_dir):
            try:
                os.makedirs(self.backup_dir, exist_ok=True)
            except OSError as e:
                raise DatabaseError(f"创建备份目录失败: {e}")
        
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """创建数据库备份。
        
        Args:
            backup_name: 备份文件名，如果为None则使用自动生成的名称
            
        Returns:
            备份文件的完整路径
            
        Raises:
            DatabaseError: 备份创建失败时抛出
        """
        with self.lock:
            if not os.path.exists(self.db_path):
                raise DatabaseError("数据库文件不存在")
                
            if backup_name is None:
                # 使用时间戳生成唯一的备份文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}.db"
                
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            try:
                # 使用shutil.copy2保留文件元数据
                shutil.copy2(self.db_path, backup_path)
                
                # 创建元数据文件，记录备份信息
                metadata_path = f"{backup_path}.meta"
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    f.write(f"备份创建时间: {datetime.now()}\n")
                    f.write(f"原始文件: {self.db_path}\n")
                    f.write(f"文件大小: {os.path.getsize(self.db_path)} 字节\n")
                    
                # 清理旧备份，保持备份数量在限制范围内
                self._cleanup_old_backups()
                
                return backup_path
                
            except Exception as e:
                raise DatabaseError(f"备份创建失败: {e}")
                
    def restore_backup(self, backup_name: str) -> bool:
        """从备份恢复数据库。
        
        Args:
            backup_name: 要恢复的备份文件名
            
        Returns:
            恢复成功返回True
            
        Raises:
            DatabaseError: 恢复失败时抛出
        """
        with self.lock:
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            if not os.path.exists(backup_path):
                raise DatabaseError(f"备份文件未找到: {backup_name}")
                
            try:
                # 创建当前数据库的安全备份
                if os.path.exists(self.db_path):
                    safety_backup = f"{self.db_path}.safety_{int(time.time())}"
                    shutil.copy2(self.db_path, safety_backup)
                    
                # 从备份恢复数据库
                shutil.copy2(backup_path, self.db_path)
                return True
                
            except Exception as e:
                raise DatabaseError(f"恢复失败: {e}")
                
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有可用的备份。
        
        Returns:
            备份信息列表，每个备份包含名称、路径、大小、创建时间等信息
        """
        with self.lock:
            backups = []
            
            # 遍历备份目录中的所有.db文件（不包括.meta文件）
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.db') and not filename.endswith('.meta'):
                    backup_path = os.path.join(self.backup_dir, filename)
                    metadata_path = f"{backup_path}.meta"
                    
                    backup_info = {
                        'name': filename,
                        'path': backup_path,
                        'size': os.path.getsize(backup_path),
                        'created': datetime.fromtimestamp(os.path.getctime(backup_path))
                    }
                    
                    # 如果存在元数据文件，读取其中的信息
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                backup_info['metadata'] = f.read()
                        except:
                            pass
                            
                    backups.append(backup_info)
                    
            # 按创建时间降序排序，最新的备份在前
            return sorted(backups, key=lambda x: x['created'], reverse=True)
            
    def delete_backup(self, backup_name: str) -> bool:
        """删除指定的备份。
        
        Args:
            backup_name: 要删除的备份文件名
            
        Returns:
            删除成功返回True
            
        Raises:
            DatabaseError: 删除失败时抛出
        """
        with self.lock:
            backup_path = os.path.join(self.backup_dir, backup_name)
            metadata_path = f"{backup_path}.meta"
            
            try:
                # 删除备份文件和对应的元数据文件
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                return True
            except Exception as e:
                raise DatabaseError(f"删除备份失败: {e}")
                
    def _cleanup_old_backups(self):
        """清理超出最大保留数量的旧备份。"""
        backups = self.list_backups()
        
        if len(backups) > self.max_backups:
            # 按创建时间排序，最旧的备份在后
            old_backups = backups[self.max_backups:]
            
            for backup in old_backups:
                try:
                    # 删除旧备份文件和元数据
                    os.remove(backup['path'])
                    metadata_path = f"{backup['path']}.meta"
                    if os.path.exists(metadata_path):
                        os.remove(metadata_path)
                except:
                    pass  # 清理过程中忽略错误，不影响主流程
                    
    def auto_backup(self, interval_hours: int = 24) -> threading.Thread:
        """启动自动备份线程。
        
        Args:
            interval_hours: 备份间隔时间（小时）
            
        Returns:
            备份线程对象
        """
        def backup_worker():
            """后台备份工作线程。"""
            while True:
                time.sleep(interval_hours * 3600)  # 转换为秒
                try:
                    # 创建自动备份，文件名包含时间戳
                    self.create_backup(f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
                except:
                    pass  # 自动备份失败时忽略错误，不影响主程序
                    
        # 创建并启动守护线程
        thread = threading.Thread(target=backup_worker, daemon=True)
        thread.start()
        return thread
        
    def validate_backup(self, backup_name: str) -> bool:
        """验证备份文件的完整性。
        
        Args:
            backup_name: 要验证的备份文件名
            
        Returns:
            备份文件有效返回True，否则返回False
        """
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        if not os.path.exists(backup_path):
            return False
            
        try:
            # 基础验证 - 检查是否为有效的SQLite文件
            with open(backup_path, 'rb') as f:
                header = f.read(100)
                # SQLite文件头包含"SQLite"标识
                return len(header) >= 16 and b'SQLite' in header
        except:
            return False


class RecoveryManager:
    """管理数据库崩溃后的恢复操作。
    
    处理数据库异常关闭后的恢复工作，包括：
    - 检查是否需要恢复
    - 执行数据库恢复
    - 清理临时文件
    """
    
    def __init__(self, db_path: str):
        """初始化恢复管理器。
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.wal_path = f"{db_path}.wal"  # 预写日志文件路径
        self.journal_path = f"{db_path}.journal"  # 回滚日志文件路径
        
    def check_recovery_needed(self) -> bool:
        """检查崩溃后是否需要恢复。
        
        Returns:
            需要恢复返回True，否则返回False
        """
        # 如果存在WAL或journal文件，说明需要恢复
        return os.path.exists(self.wal_path) or os.path.exists(self.journal_path)
        
    def perform_recovery(self) -> bool:
        """执行数据库恢复。
        
        Returns:
            恢复成功返回True
            
        Raises:
            DatabaseError: 恢复失败时抛出
        """
        try:
            # 简单恢复 - 仅删除WAL和journal文件
            # 在实际实现中，这里会重放事务日志
            
            # 删除预写日志文件
            if os.path.exists(self.wal_path):
                os.remove(self.wal_path)
                
            # 删除回滚日志文件
            if os.path.exists(self.journal_path):
                os.remove(self.journal_path)
                
            return True
            
        except Exception as e:
            raise DatabaseError(f"恢复失败: {e}")
            
    def create_checkpoint(self):
        """创建恢复检查点。
        
        在实际实现中，这里会执行WAL检查点操作，
        将内存中的数据刷新到磁盘。
        """
        # 这里将实现适当的WAL检查点机制
        pass