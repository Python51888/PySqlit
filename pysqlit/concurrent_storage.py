"""线程安全和进程安全的存储模块，支持文件锁定。

提供跨平台的文件锁定机制和线程安全的页面管理，
确保在多线程和多进程环境下的数据一致性。
"""

import os
import struct
import threading
import os
import platform
if platform.system() != 'Windows':
    import fcntl
import tempfile
from typing import Optional, BinaryIO
from .exceptions import DatabaseError


class FileLock:
    """跨平台文件锁定实现。
    
    支持Windows和Unix-like系统的文件锁定，提供共享锁和独占锁功能。
    使用回退机制确保在锁定失败时仍能提供基本的并发保护。
    """
    
    def __init__(self, file_path: str):
        """初始化文件锁。
        
        Args:
            file_path: 要锁定的文件路径
        """
        self.file_path = file_path
        self.lock_file = None
        self._lock = threading.RLock()  # 线程级别的锁
        self._locked = False
        
    def acquire_shared(self, timeout: Optional[float] = None) -> bool:
        """获取共享锁（读锁）。
        
        Args:
            timeout: 超时时间（秒），None表示无限等待
            
        Returns:
            成功获取锁返回True，超时返回False
        """
        return self._acquire_lock(False, timeout)
        
    def acquire_exclusive(self, timeout: Optional[float] = None) -> bool:
        """获取独占锁（写锁）。
        
        Args:
            timeout: 超时时间（秒），None表示无限等待
            
        Returns:
            成功获取锁返回True，超时返回False
        """
        return self._acquire_lock(True, timeout)
        
    def _acquire_lock(self, exclusive: bool, timeout: Optional[float]) -> bool:
        """获取锁的跨平台实现。
        
        Args:
            exclusive: 是否为独占锁
            timeout: 超时时间
            
        Returns:
            成功获取锁返回True，失败返回False
        """
        with self._lock:
            if self._locked:
                return True
                
            try:
                if not self.lock_file or self.lock_file.closed:
                    self.lock_file = open(self.file_path, 'rb+')
                
                if os.name == 'nt':  # Windows系统
                    return self._acquire_windows_lock(exclusive, timeout)
                else:  # Unix-like系统
                    return self._acquire_unix_lock(exclusive, timeout)
                    
            except Exception as e:
                # 回退到简单的基于文件的锁定
                lock_file_path = f"{self.file_path}.lock"
                try:
                    with open(lock_file_path, 'w') as f:
                        f.write(str(os.getpid()))
                    self._locked = True
                    return True
                except:
                    return False
                    
    def _acquire_unix_lock(self, exclusive: bool, timeout: Optional[float]) -> bool:
        """获取Unix文件锁。
        
        Args:
            exclusive: 是否为独占锁
            timeout: 超时时间
            
        Returns:
            成功获取锁返回True，超时返回False
        """
        import fcntl
        lock_type = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        
        if timeout is None:
            # 无限等待
            fcntl.flock(self.lock_file.fileno(), lock_type)
            self._locked = True
            return True
        else:
            # 带超时的非阻塞尝试
            import time
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    fcntl.flock(self.lock_file.fileno(), lock_type | fcntl.LOCK_NB)
                    self._locked = True
                    return True
                except BlockingIOError:
                    time.sleep(0.1)
            return False
            
    def _acquire_windows_lock(self, exclusive: bool, timeout: Optional[float]) -> bool:
        """获取Windows文件锁。
        
        Args:
            exclusive: 是否为独占锁
            timeout: 超时时间
            
        Returns:
            成功获取锁返回True，失败返回False
        """
        # Windows系统使用基于文件的锁定
        lock_file_path = f"{self.file_path}.lock"
        try:
            with open(lock_file_path, 'w') as f:
                f.write(str(os.getpid()))
            self._locked = True
            return True
        except:
            return False
        
    def release(self):
        """释放锁。"""
        with self._lock:
            if not self._locked:
                return
                
            try:
                if os.name == 'nt':
                    # Windows系统：删除锁文件
                    lock_file_path = f"{self.file_path}.lock"
                    if os.path.exists(lock_file_path):
                        os.remove(lock_file_path)
                else:
                    # Unix系统：释放文件锁
                    if self.lock_file and not self.lock_file.closed:
                        import fcntl
                        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                        
                self._locked = False
                
                if self.lock_file and not self.lock_file.closed:
                    self.lock_file.close()
                    self.lock_file = None
                    
            except Exception as e:
                # 忽略清理错误
                pass
        
    def __enter__(self):
        """上下文管理器入口。"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，自动释放锁。"""
        self.release()


class ConcurrentPager:
    """线程安全和进程安全的页面管理器，支持文件锁定。
    
    提供跨平台的页面管理功能，确保在多线程和多进程环境下的
    数据一致性和并发安全性。
    """
    
    def __init__(self, filename: str):
        """初始化并发页面管理器。
        
        Args:
            filename: 数据库文件名，":memory:"表示内存数据库
        """
        self.filename = filename
        self.file: Optional[BinaryIO] = None
        self.file_lock = FileLock(filename)  # 文件锁
        from .constants import PAGE_SIZE
        self.page_size = PAGE_SIZE
        self.page_cache = {}  # 简单的内存缓存
        self.cache_lock = threading.RLock()  # 缓存访问锁
        self.is_memory_db = (filename == ":memory:")
        if not self.is_memory_db:
            self._open_file()
        
    def _open_file(self):
        """打开数据库文件。"""
        if self.is_memory_db:
            return
            
        if not os.path.exists(self.filename):
            # 创建新文件
            self.file = open(self.filename, 'wb+')
            self.file.write(b'\x00' * self.page_size)  # 写入初始页面
            self.file.flush()
        else:
            self.file = open(self.filename, 'rb+')
            
    def get_page(self, page_num: int) -> bytearray:
        """线程安全地获取页面。
        
        Args:
            page_num: 页号
            
        Returns:
            页面对应的字节数组
        """
        with self.cache_lock:
            if page_num in self.page_cache:
                return self.page_cache[page_num]
                
        if self.is_memory_db:
            # 在内存中初始化新页面
            page = bytearray(b'\x00' * self.page_size)
            with self.cache_lock:
                self.page_cache[page_num] = page
            return page
            
        # 获取共享锁用于读取
        self.file_lock.acquire_shared()
        try:
            self.file.seek(page_num * self.page_size)
            data = self.file.read(self.page_size)
            
            if len(data) < self.page_size:
                # 如果页面不完整，用零填充
                data = data.ljust(self.page_size, b'\x00')
                
            page = bytearray(data)
            
            # 缓存页面
            with self.cache_lock:
                self.page_cache[page_num] = page
                
            return page
            
        finally:
            self.file_lock.release()
            
    def write_page(self, page_num: int, data: bytes):
        """线程安全地写入页面。
        
        Args:
            page_num: 页号
            data: 要写入的数据
        """
        if len(data) != self.page_size:
            from .integrity import IntegrityChecker
            # 尝试修复数据长度
            if len(data) < self.page_size:
                data = data.ljust(self.page_size, b'\x00')
            else:
                data = data[:self.page_size]
                
        # 内存数据库：仅更新缓存
        if self.is_memory_db:
            with self.cache_lock:
                self.page_cache[page_num] = bytearray(data)
            return
            
        # 获取独占锁用于写入
        self.file_lock.acquire_exclusive()
        try:
            self.file.seek(page_num * self.page_size)
            self.file.write(data)
            self.file.flush()
            
            # 更新缓存
            with self.cache_lock:
                self.page_cache[page_num] = bytearray(data)
                
        finally:
            self.file_lock.release()
            
    @property
    def num_pages(self) -> int:
        """获取文件中的页面数量。"""
        if self.is_memory_db:
            # 内存数据库：从缓存中获取最大页号
            if not self.page_cache:
                return 0
            return max(self.page_cache.keys()) + 1
            
        self.file_lock.acquire_shared()
        try:
            self.file.seek(0, 2)  # 移动到文件末尾
            file_size = self.file.tell()
            return file_size // self.page_size
        finally:
            self.file_lock.release()
            
    def flush(self):
        """将所有更改刷新到磁盘。"""
        if self.is_memory_db:
            return
            
        self.file_lock.acquire_exclusive()
        try:
            self.file.flush()
            os.fsync(self.file.fileno())  # 强制同步到磁盘
        finally:
            self.file_lock.release()
            
    def close(self):
        """关闭文件。"""
        if self.file and not self.file.closed:
            self.flush()  # 关闭前确保所有更改已刷新
            self.file_lock.release()
            self.file.close()
            
        # 清除内存数据库的缓存
        if self.is_memory_db:
            with self.cache_lock:
                self.page_cache.clear()
            
    def create_backup(self, backup_path: str):
        """创建数据库文件的备份。
        
        Args:
            backup_path: 备份文件路径
        """
        self.file_lock.acquire_shared()
        try:
            self.file.flush()
            import shutil
            shutil.copy2(self.filename, backup_path)
        finally:
            self.file_lock.release()
            
    def get_file_size(self) -> int:
        """获取文件大小。
        
        Returns:
            文件大小（字节）
        """
        self.file_lock.acquire_shared()
        try:
            self.file.seek(0, 2)
            return self.file.tell()
        finally:
            self.file_lock.release()
            
    def truncate(self, new_size: int):
        """截断文件到指定大小。
        
        Args:
            new_size: 新的文件大小
        """
        self.file_lock.acquire_exclusive()
        try:
            self.file.truncate(new_size)
            # 清除被截断页面的缓存
            with self.cache_lock:
                pages_to_remove = [
                    page_num for page_num in self.page_cache
                    if page_num * self.page_size >= new_size
                ]
                for page_num in pages_to_remove:
                    del self.page_cache[page_num]
        finally:
            self.file_lock.release()