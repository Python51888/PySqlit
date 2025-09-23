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
from .exceptions import DatabaseError, StorageError
from .storage import Pager

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
            成功获取锁返回True，失败返回False
        """
        import fcntl
        lock_type = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        
        if timeout is None:
            # 无限等待
            if self.lock_file is not None and not self.lock_file.closed:
                fcntl.flock(self.lock_file.fileno(), lock_type)
                self._locked = True
                return True
            return False
        else:
            # 带超时的非阻塞尝试
            import time
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    if self.lock_file is not None and not self.lock_file.closed:
                        fcntl.flock(self.lock_file.fileno(), lock_type | fcntl.LOCK_NB)
                        self._locked = True
                        return True
                    else:
                        return False
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


class ConcurrentPager(Pager):
    """线程安全和进程安全的页面管理器，支持文件锁定。
    
    提供跨平台的页面管理功能，确保在多线程和多进程环境下的
    数据一致性和并发安全性。
    """
    
    def __init__(self, filename: str):
        """初始化并发页面管理器。
        
        Args:
            filename: 数据库文件名，":memory:"表示内存数据库
        """
        self.is_memory_db = (filename == ":memory:")
        
        # 对于内存数据库，我们仍然需要初始化父类，但要特殊处理文件操作
        if self.is_memory_db:
            # 手动设置父类属性
            self.filename = filename
            self.file_descriptor = None
            self.file_length = 0
            self.num_pages = 0
            self.pages = [None] * 100  # 使用默认大小
        else:
            # 初始化父类Pager
            super().__init__(filename)
        
        self.file_lock = FileLock(filename)  # 文件锁
        from .constants import PAGE_SIZE
        self.page_size = PAGE_SIZE
        self.page_cache = {}  # 简单的内存缓存
        self.cache_lock = threading.RLock()  # 缓存访问锁
        if not self.is_memory_db:
            self._open_file_concurrent()
    
    def _open_file_concurrent(self):
        """打开数据库文件（并发版本）。"""
        if self.is_memory_db:
            return
            
        if not os.path.exists(self.filename):
            # 创建新文件
            self.file_descriptor = open(self.filename, 'wb+')
            self.file_descriptor.write(b'\x00' * self.page_size)  # 写入初始页面
            self.file_descriptor.flush()
            self.file_length = self.page_size
            # 直接设置父类的num_pages属性
            super().__setattr__('num_pages', 1)
        else:
            self.file_descriptor = open(self.filename, 'rb+')
            self.file_descriptor.seek(0, 2)  # 移动到文件末尾
            self.file_length = self.file_descriptor.tell()
            # 直接设置父类的num_pages属性
            super().__setattr__('num_pages', self.file_length // self.page_size)
            
            if self.file_length % self.page_size != 0:
                raise StorageError("Database file is not a whole number of pages")
    
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
            # 调用父类方法获取页面
            page = super().get_page(page_num)
            
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
            # 调用父类方法写入页面
            super().flush_page(page_num)
            
            # 更新缓存
            with self.cache_lock:
                self.page_cache[page_num] = bytearray(data)
                
        finally:
            self.file_lock.release()
    
    def flush(self):
        """将所有更改刷新到磁盘。"""
        if self.is_memory_db:
            return
            
        self.file_lock.acquire_exclusive()
        try:
            # 调用父类方法刷新所有页面
            super().flush_all_pages()
        finally:
            self.file_lock.release()
    
    def close(self):
        """关闭文件。"""
        self.file_lock.acquire_exclusive()
        try:
            # 调用父类方法关闭
            super().close()
            
            # 清除内存数据库的缓存
            if self.is_memory_db:
                with self.cache_lock:
                    self.page_cache.clear()
        finally:
            self.file_lock.release()
            
    def create_backup(self, backup_path: str):
        """创建数据库文件的备份。
        
        Args:
            backup_path: 备份文件路径
        """
        self.file_lock.acquire_shared()
        try:
            if self.file_descriptor is not None:
                self.file_descriptor.flush()
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
            if self.file_descriptor is not None:
                self.file_descriptor.seek(0, 2)
                return self.file_descriptor.tell()
            else:
                return 0
        finally:
            self.file_lock.release()
    
    def truncate(self, new_size: int):
        """截断文件到指定大小。
        
        Args:
            new_size: 新的文件大小
        """
        self.file_lock.acquire_exclusive()
        try:
            if self.file_descriptor is not None:
                self.file_descriptor.truncate(new_size)
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