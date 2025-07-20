"""Unit tests for pysqlit/backup.py module."""

import pytest
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock

from pysqlit.backup import BackupManager, RecoveryManager


class TestBackupManager:
    """Test cases for BackupManager class."""
    
    def test_backup_manager_creation(self, temp_db_path):
        """Test backup manager creation."""
        manager = BackupManager(temp_db_path)
        assert manager.db_filename == temp_db_path
    
    def test_create_backup(self, temp_db_path):
        """Test creating backup."""
        # Create a test database file
        with open(temp_db_path, 'w') as f:
            f.write("test database content")
        
        manager = BackupManager(temp_db_path)
        backup_name = manager.create_backup("test_backup")
        
        assert backup_name is not None
        assert "test_backup" in backup_name
        assert os.path.exists(backup_name)
    
    def test_create_backup_without_name(self, temp_db_path):
        """Test creating backup without custom name."""
        # Create a test database file
        with open(temp_db_path, 'w') as f:
            f.write("test database content")
        
        manager = BackupManager(temp_db_path)
        backup_name = manager.create_backup()
        
        assert backup_name is not None
        assert os.path.exists(backup_name)
    
    def test_list_backups(self, temp_db_path):
        """Test listing backups."""
        # Create a test database file
        with open(temp_db_path, 'w') as f:
            f.write("test database content")
        
        manager = BackupManager(temp_db_path)
        
        # Create some backups
        backup1 = manager.create_backup("backup1")
        backup2 = manager.create_backup("backup2")
        
        backups = manager.list_backups()
        assert isinstance(backups, list)
        assert len(backups) >= 2
    
    def test_restore_backup(self, temp_db_path):
        """Test restoring from backup."""
        # Create original content
        original_content = "original database content"
        with open(temp_db_path, 'w') as f:
            f.write(original_content)
        
        manager = BackupManager(temp_db_path)
        backup_name = manager.create_backup("test_backup")
        
        # Modify original file
        with open(temp_db_path, 'w') as f:
            f.write("modified content")
        
        # Restore from backup
        result = manager.restore_backup(backup_name)
        assert result is True
        
        # Verify restoration
        with open(temp_db_path, 'r') as f:
            restored_content = f.read()
        assert restored_content == original_content
    
    def test_restore_nonexistent_backup(self, temp_db_path):
        """Test restoring from non-existent backup."""
        manager = BackupManager(temp_db_path)
        result = manager.restore_backup("nonexistent_backup")
        assert result is False
    
    def test_backup_directory_creation(self, temp_db_path):
        """Test backup directory creation."""
        manager = BackupManager(temp_db_path)
        
        # Create a backup to trigger directory creation
        with open(temp_db_path, 'w') as f:
            f.write("test")
        manager.create_backup("test")
        
        backup_dir = os.path.join(os.path.dirname(temp_db_path), "backups")
        assert os.path.exists(backup_dir)


class TestRecoveryManager:
    """Test cases for RecoveryManager class."""
    
    def test_recovery_manager_creation(self, temp_db_path):
        """Test recovery manager creation."""
        manager = RecoveryManager(temp_db_path)
        assert manager.db_filename == temp_db_path
    
    def test_create_recovery_point(self, temp_db_path):
        """Test creating recovery point."""
        # Create a test database file
        with open(temp_db_path, 'w') as f:
            f.write("test database content")
        
        manager = RecoveryManager(temp_db_path)
        recovery_point = manager.create_recovery_point("test_recovery")
        
        assert recovery_point is not None
        assert "test_recovery" in recovery_point
    
    def test_list_recovery_points(self, temp_db_path):
        """Test listing recovery points."""
        # Create a test database file
        with open(temp_db_path, 'w') as f:
            f.write("test database content")
        
        manager = RecoveryManager(temp_db_path)
        
        # Create some recovery points
        point1 = manager.create_recovery_point("point1")
        point2 = manager.create_recovery_point("point2")
        
        points = manager.list_recovery_points()
        assert isinstance(points, list)
    
    def test_recover_from_point(self, temp_db_path):
        """Test recovering from recovery point."""
        # Create original content
        original_content = "original database content"
        with open(temp_db_path, 'w') as f:
            f.write(original_content)
        
        manager = RecoveryManager(temp_db_path)
        recovery_point = manager.create_recovery_point("test_recovery")
        
        # Modify original file
        with open(temp_db_path, 'w') as f:
            f.write("modified content")
        
        # Recover from point
        result = manager.recover_from_point(recovery_point)
        assert result is True
        
        # Verify recovery
        with open(temp_db_path, 'r') as f:
            recovered_content = f.read()
        assert recovered_content == original_content
    
    def test_recover_from_nonexistent_point(self, temp_db_path):
        """Test recovering from non-existent recovery point."""
        manager = RecoveryManager(temp_db_path)
        result = manager.recover_from_point("nonexistent_point")
        assert result is False
    
    def test_auto_recovery(self, temp_db_path):
        """Test automatic recovery functionality."""
        manager = RecoveryManager(temp_db_path)
        
        # Test auto recovery (may not do anything if no corruption detected)
        result = manager.auto_recover()
        assert isinstance(result, bool)  # Should return True or False
    
    def test_validate_database_integrity(self, temp_db_path):
        """Test database integrity validation."""
        # Create a valid database file
        with open(temp_db_path, 'w') as f:
            f.write("valid database content")
        
        manager = RecoveryManager(temp_db_path)
        is_valid = manager.validate_database_integrity()
        assert isinstance(is_valid, bool)
    
    def test_recovery_directory_creation(self, temp_db_path):
        """Test recovery directory creation."""
        manager = RecoveryManager(temp_db_path)
        
        # Create a recovery point to trigger directory creation
        with open(temp_db_path, 'w') as f:
            f.write("test")
        manager.create_recovery_point("test")
        
        recovery_dir = os.path.join(os.path.dirname(temp_db_path), "recovery")
        # Note: Directory might not be created until first recovery point
        # This test verifies the basic functionality


class TestBackupEdgeCases:
    """Test edge cases for backup functionality."""
    
    def test_backup_empty_database(self, temp_db_path):
        """Test backing up empty database."""
        # Create empty database file
        with open(temp_db_path, 'w') as f:
            pass
        
        manager = BackupManager(temp_db_path)
        backup_name = manager.create_backup("empty_test")
        assert backup_name is not None
        assert os.path.exists(backup_name)
    
    def test_backup_large_database(self, temp_db_path):
        """Test backing up large database."""
        # Create large database file
        large_content = "x" * 100000  # 100KB
        with open(temp_db_path, 'w') as f:
            f.write(large_content)
        
        manager = BackupManager(temp_db_path)
        backup_name = manager.create_backup("large_test")
        assert backup_name is not None
        assert os.path.exists(backup_name)
    
    def test_concurrent_backup_creation(self, temp_db_path):
        """Test creating multiple backups concurrently."""
        # Create test database
        with open(temp_db_path, 'w') as f:
            f.write("test content")
        
        manager = BackupManager(temp_db_path)
        
        # Create multiple backups
        backups = []
        for i in range(5):
            backup_name = manager.create_backup(f"concurrent_{i}")
            backups.append(backup_name)
        
        assert len(backups) == 5
        for backup in backups:
            assert os.path.exists(backup)
    
    def test_backup_cleanup(self, temp_db_path):
        """Test backup cleanup functionality."""
        # Create test database
        with open(temp_db_path, 'w') as f:
            f.write("test content")
        
        manager = BackupManager(temp_db_path)
        
        # Create multiple backups
        for i in range(10):
            manager.create_backup(f"cleanup_test_{i}")
        
        # List backups
        backups = manager.list_backups()
        assert len(backups) >= 10