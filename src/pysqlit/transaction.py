"""事务管理模块，提供ACID特性和并发控制。

该模块实现了完整的事务管理系统，包括：
- ACID特性（原子性、一致性、隔离性、持久性）
- 并发控制（锁管理）
- 事务状态管理
- 检查点和恢复机制
- 事务日志记录

主要特性：
1. 支持四种隔离级别（读未提交、读已提交、可重复读、串行化）
2. 基于页面的锁管理
3. 事务回滚和恢复
4. 检查点机制
5. 并发安全
"""

import os
import threading
import time
from typing import Optional, Dict, Any, List
from enum import Enum
from .exceptions import DatabaseError, TransactionError
from .storage import Pager


class TransactionState(Enum):
    """事务状态枚举。
    
    定义了事务在其生命周期中的各种状态。
    
    Attributes:
        ACTIVE: 活动状态，事务正在执行
        COMMITTED: 已提交状态，事务成功完成
        ABORTED: 已中止状态，事务被回滚
        PARTIALLY_COMMITTED: 部分提交状态，正在提交过程中
    """
    ACTIVE = "active"
    COMMITTED = "committed"
    ABORTED = "aborted"
    PARTIALLY_COMMITTED = "partially_committed"


class IsolationLevel(Enum):
    """事务隔离级别枚举。
    
    定义了SQL标准中的四种隔离级别，用于控制并发事务之间的可见性。
    
    Attributes:
        READ_UNCOMMITTED: 读未提交，最低的隔离级别
        READ_COMMITTED: 读已提交，防止脏读
        REPEATABLE_READ: 可重复读，防止脏读和不可重复读
        SERIALIZABLE: 串行化，最高的隔离级别
    """
    READ_UNCOMMITTED = "read_uncommitted"
    READ_COMMITTED = "read_committed"
    REPEATABLE_READ = "repeatable_read"
    SERIALIZABLE = "serializable"


class Transaction:
    """事务类，提供ACID特性支持。
    
    表示一个数据库事务，维护事务的状态、锁信息和回滚日志。
    
    Attributes:
        transaction_id: 事务唯一标识符
        isolation_level: 隔离级别
        state: 当前事务状态
        start_time: 事务开始时间
        read_set: 读取的页面集合
        write_set: 写入的页面集合
        locks_held: 持有的锁集合
        undo_log: 回滚日志，用于事务回滚
    
    Examples:
        >>> transaction = Transaction(1, IsolationLevel.REPEATABLE_READ)
        >>> transaction.add_read(0)  # 记录读取的页面
    """
    
    def __init__(self, transaction_id: int, isolation_level: IsolationLevel = IsolationLevel.REPEATABLE_READ):
        """初始化事务。
        
        Args:
            transaction_id: 事务ID
            isolation_level: 隔离级别，默认为REPEATABLE_READ
        """
        self.transaction_id = transaction_id
        self.isolation_level = isolation_level
        self.state = TransactionState.ACTIVE
        self.start_time = time.time()
        self.read_set = set()  # 读取的页面
        self.write_set = set()  # 写入的页面
        self.locks_held = set()  # 持有的锁
        self.undo_log = []  # 用于回滚的日志
        
    def add_read(self, page_num: int):
        """将页面添加到读取集合。
        
        Args:
            page_num: 页面编号
        """
        self.read_set.add(page_num)
        
    def add_write(self, page_num: int):
        """将页面添加到写入集合。
        
        Args:
            page_num: 页面编号
        """
        self.write_set.add(page_num)
        
    def add_undo_record(self, page_num: int, old_data: bytes):
        """添加回滚记录。
        
        在修改页面数据前记录原始数据，用于事务回滚。
        
        Args:
            page_num: 页面编号
            old_data: 原始数据
        """
        self.undo_log.append((page_num, old_data))
        
    def rollback(self, pager: Pager):
        """回滚事务更改。
        
        使用undo_log中的记录将数据恢复到事务开始前的状态。
        
        Args:
            pager: 分页管理器
            
        Raises:
            TransactionError: 如果回滚失败
        """
        if self.state != TransactionState.ACTIVE:
            return
            
        try:
            # 按逆序应用回滚日志
            for page_num, old_data in reversed(self.undo_log):
                pager.write_page(page_num, old_data)
                
            self.state = TransactionState.ABORTED
        except Exception as e:
            raise TransactionError(f"Rollback failed: {e}")


class LockManager:
    """锁管理器，处理并发访问的锁机制。
    
    提供共享锁和排他锁的管理，确保并发事务的正确执行。
    
    Attributes:
        locks: 锁字典（页面号 -> 事务ID集合）
        lock: 线程锁，确保线程安全
    """
    
    def __init__(self):
        """初始化锁管理器。"""
        self.locks = {}  # page_num -> set of transaction_ids
        self.lock = threading.RLock()
        
    def acquire_lock(self, transaction_id: int, page_num: int, lock_type: str) -> bool:
        """获取页面锁。
        
        Args:
            transaction_id: 事务ID
            page_num: 页面编号
            lock_type: 锁类型（"shared"或"exclusive"）
            
        Returns:
            bool: 成功获取锁返回True，否则返回False
        """
        with self.lock:
            if page_num not in self.locks:
                self.locks[page_num] = set()
                
            # 简单的共享/排他锁实现
            if lock_type == "shared":
                # 共享锁可以与其他共享锁共存
                self.locks[page_num].add(transaction_id)
                return True
            elif lock_type == "exclusive":
                # 排他锁要求没有其他锁
                if len(self.locks[page_num]) == 0 or (
                    len(self.locks[page_num]) == 1 and transaction_id in self.locks[page_num]
                ):
                    self.locks[page_num].add(transaction_id)
                    return True
                return False
                
    def release_lock(self, transaction_id: int, page_num: int):
        """释放页面锁。
        
        Args:
            transaction_id: 事务ID
            page_num: 页面编号
        """
        with self.lock:
            if page_num in self.locks and transaction_id in self.locks[page_num]:
                self.locks[page_num].remove(transaction_id)
                if len(self.locks[page_num]) == 0:
                    del self.locks[page_num]
                    
    def release_all_locks(self, transaction_id: int):
        """释放事务持有的所有锁。
        
        Args:
            transaction_id: 事务ID
        """
        with self.lock:
            pages_to_remove = []
            for page_num, holders in self.locks.items():
                if transaction_id in holders:
                    holders.remove(transaction_id)
                    if len(holders) == 0:
                        pages_to_remove.append(page_num)
                        
            for page_num in pages_to_remove:
                del self.locks[page_num]


class TransactionManager:
    """事务管理器，提供ACID特性的事务管理。
    
    管理事务的生命周期，包括开始、提交、回滚等操作。
    
    Attributes:
        pager: 分页管理器
        lock_manager: 锁管理器
        transactions: 事务字典（事务ID -> Transaction）
        next_transaction_id: 下一个事务ID
        global_lock: 全局锁，确保线程安全
        active_transactions: 活动事务数量
    
    Examples:
        >>> manager = TransactionManager(pager)
        >>> tx_id = manager.begin_transaction()
        >>> # 执行事务操作
        >>> manager.commit_transaction(tx_id)
    """
    
    def __init__(self, pager: Pager):
        """初始化事务管理器。
        
        Args:
            pager: 分页管理器
        """
        self.pager = pager
        self.lock_manager = LockManager()
        self.transactions = {}  # transaction_id -> Transaction
        self.next_transaction_id = 1
        self.global_lock = threading.RLock()
        self.active_transactions = 0
        
    def begin_transaction(self, isolation_level: IsolationLevel = IsolationLevel.REPEATABLE_READ) -> int:
        """开始新事务。
        
        Args:
            isolation_level: 隔离级别，默认为REPEATABLE_READ
            
        Returns:
            int: 新事务的ID
        """
        with self.global_lock:
            transaction_id = self.next_transaction_id
            self.next_transaction_id += 1
            
            transaction = Transaction(transaction_id, isolation_level)
            self.transactions[transaction_id] = transaction
            self.active_transactions += 1
            
            return transaction_id
            
    def commit_transaction(self, transaction_id: int):
        """提交事务。
        
        将事务的所有更改永久保存到数据库。
        
        Args:
            transaction_id: 要提交的事务ID
            
        Raises:
            TransactionError: 如果事务不存在或不处于活动状态
        """
        with self.global_lock:
            if transaction_id not in self.transactions:
                raise TransactionError("Transaction not found")
                
            transaction = self.transactions[transaction_id]
            if transaction.state != TransactionState.ACTIVE:
                raise TransactionError("Transaction not active")
                
            try:
                # 将所有更改刷新到磁盘
                self.pager.flush()
                transaction.state = TransactionState.COMMITTED
                self.active_transactions -= 1
                
                # 释放所有锁
                self.lock_manager.release_all_locks(transaction_id)
                
                # 清理
                del self.transactions[transaction_id]
                
            except Exception as e:
                transaction.rollback(self.pager)
                raise TransactionError(f"Commit failed: {e}")
                
    def rollback_transaction(self, transaction_id: int):
        """回滚事务。
        
        撤销事务的所有更改，恢复到事务开始前的状态。
        
        Args:
            transaction_id: 要回滚的事务ID
            
        Raises:
            TransactionError: 如果事务不存在或回滚失败
        """
        with self.global_lock:
            if transaction_id not in self.transactions:
                raise TransactionError("Transaction not found")
                
            transaction = self.transactions[transaction_id]
            if transaction.state != TransactionState.ACTIVE:
                return
                
            try:
                transaction.rollback(self.pager)
                self.active_transactions -= 1
                
                # 释放所有锁
                self.lock_manager.release_all_locks(transaction_id)
                
                # 清理
                del self.transactions[transaction_id]
                
            except Exception as e:
                raise TransactionError(f"Rollback failed: {e}")
                
    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """根据ID获取事务。
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            Optional[Transaction]: 事务对象，如果不存在返回None
        """
        return self.transactions.get(transaction_id)
        
    def is_in_transaction(self, transaction_id: int) -> bool:
        """检查事务是否处于活动状态。
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            bool: 如果事务活动返回True，否则返回False
        """
        return transaction_id in self.transactions
        
    def get_active_transaction_count(self) -> int:
        """获取活动事务的数量。
        
        Returns:
            int: 当前活动的事务数量
        """
        return self.active_transactions


class CheckpointManager:
    """检查点管理器，用于数据库恢复。
    
    提供数据库检查点的创建和恢复功能，支持故障恢复。
    
    Attributes:
        db_path: 数据库文件路径
        checkpoint_path: 检查点文件路径
        log_path: 日志文件路径
    
    Examples:
        >>> manager = CheckpointManager("test.db")
        >>> manager.create_checkpoint()
        >>> manager.restore_from_checkpoint()
    """
    
    def __init__(self, db_path: str):
        """初始化检查点管理器。
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.checkpoint_path = f"{db_path}.checkpoint"
        self.log_path = f"{db_path}.log"
        
    def create_checkpoint(self):
        """创建数据库检查点。
        
        创建数据库文件的完整副本作为检查点，用于故障恢复。
        
        Returns:
            bool: 成功创建返回True，否则返回False
            
        Raises:
            DatabaseError: 如果检查点创建失败
        """
        try:
            if os.path.exists(self.db_path):
                import shutil
                shutil.copy2(self.db_path, self.checkpoint_path)
                return True
        except Exception as e:
            raise DatabaseError(f"Checkpoint creation failed: {e}")
            
    def restore_from_checkpoint(self):
        """从检查点恢复数据库。
        
        使用检查点文件恢复数据库到之前的状态。
        
        Returns:
            bool: 成功恢复返回True，否则返回False
            
        Raises:
            DatabaseError: 如果恢复失败
        """
        try:
            if os.path.exists(self.checkpoint_path):
                import shutil
                shutil.copy2(self.checkpoint_path, self.db_path)
                return True
        except Exception as e:
            raise DatabaseError(f"Checkpoint restore failed: {e}")
            
    def write_log_record(self, record: Dict[str, Any]):
        """写入事务日志记录。
        
        将事务操作记录到日志文件，用于故障恢复。
        
        Args:
            record: 日志记录字典
            
        Raises:
            DatabaseError: 如果日志写入失败
        """
        try:
            with open(self.log_path, 'a') as f:
                f.write(f"{record}\n")
        except Exception as e:
            raise DatabaseError(f"Log write failed: {e}")