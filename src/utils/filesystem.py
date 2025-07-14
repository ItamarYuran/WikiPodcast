"""
File System Utilities
Centralized file operations with proper error handling and path management
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from datetime import datetime
import tempfile
import hashlib


@dataclass
class FileInfo:
    """File information container"""
    path: Path
    size: int
    modified: datetime
    exists: bool
    is_file: bool
    is_directory: bool
    extension: str
    
    @classmethod
    def from_path(cls, path: Union[str, Path]) -> 'FileInfo':
        """Create FileInfo from path"""
        path = Path(path)
        
        if path.exists():
            stat = path.stat()
            return cls(
                path=path,
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime),
                exists=True,
                is_file=path.is_file(),
                is_directory=path.is_dir(),
                extension=path.suffix.lower()
            )
        else:
            return cls(
                path=path,
                size=0,
                modified=datetime.min,
                exists=False,
                is_file=False,
                is_directory=False,
                extension=path.suffix.lower()
            )


class FileSystemError(Exception):
    """Base exception for file system operations"""
    pass


class FileManager:
    """
    Centralized file system operations with proper error handling
    """
    
    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """
        Initialize FileManager
        
        Args:
            base_path: Base directory for relative path operations
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        
    def ensure_directory(self, path: Union[str, Path]) -> Path:
        """
        Ensure directory exists, create if necessary
        
        Args:
            path: Directory path to ensure
            
        Returns:
            Path object of the directory
            
        Raises:
            FileSystemError: If directory cannot be created
        """
        try:
            dir_path = self._resolve_path(path)
            dir_path.mkdir(parents=True, exist_ok=True)
            return dir_path
        except OSError as e:
            raise FileSystemError(f"Failed to create directory {path}: {e}")
    
    def read_file(self, path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """
        Read text file content
        
        Args:
            path: File path to read
            encoding: Text encoding
            
        Returns:
            File content as string
            
        Raises:
            FileSystemError: If file cannot be read
        """
        try:
            file_path = self._resolve_path(path)
            return file_path.read_text(encoding=encoding)
        except (OSError, UnicodeDecodeError) as e:
            raise FileSystemError(f"Failed to read file {path}: {e}")
    
    def write_file(self, path: Union[str, Path], content: str, encoding: str = 'utf-8') -> None:
        """
        Write text content to file
        
        Args:
            path: File path to write
            content: Content to write
            encoding: Text encoding
            
        Raises:
            FileSystemError: If file cannot be written
        """
        try:
            file_path = self._resolve_path(path)
            # Ensure parent directory exists
            self.ensure_directory(file_path.parent)
            file_path.write_text(content, encoding=encoding)
        except OSError as e:
            raise FileSystemError(f"Failed to write file {path}: {e}")
    
    def read_json(self, path: Union[str, Path]) -> Dict[str, Any]:
        """
        Read JSON file
        
        Args:
            path: JSON file path
            
        Returns:
            Parsed JSON data
            
        Raises:
            FileSystemError: If file cannot be read or parsed
        """
        try:
            content = self.read_file(path)
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise FileSystemError(f"Invalid JSON in file {path}: {e}")
    
    def write_json(self, path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> None:
        """
        Write data as JSON file
        
        Args:
            path: JSON file path
            data: Data to write
            indent: JSON indentation
            
        Raises:
            FileSystemError: If file cannot be written
        """
        try:
            content = json.dumps(data, indent=indent, ensure_ascii=False)
            self.write_file(path, content)
        except (TypeError, ValueError) as e:
            raise FileSystemError(f"Failed to serialize JSON for {path}: {e}")
    
    def copy_file(self, src: Union[str, Path], dst: Union[str, Path]) -> Path:
        """
        Copy file from source to destination
        
        Args:
            src: Source file path
            dst: Destination file path
            
        Returns:
            Destination path
            
        Raises:
            FileSystemError: If file cannot be copied
        """
        try:
            src_path = self._resolve_path(src)
            dst_path = self._resolve_path(dst)
            
            # Ensure destination directory exists
            self.ensure_directory(dst_path.parent)
            
            shutil.copy2(src_path, dst_path)
            return dst_path
        except OSError as e:
            raise FileSystemError(f"Failed to copy {src} to {dst}: {e}")
    
    def move_file(self, src: Union[str, Path], dst: Union[str, Path]) -> Path:
        """
        Move file from source to destination
        
        Args:
            src: Source file path
            dst: Destination file path
            
        Returns:
            Destination path
            
        Raises:
            FileSystemError: If file cannot be moved
        """
        try:
            src_path = self._resolve_path(src)
            dst_path = self._resolve_path(dst)
            
            # Ensure destination directory exists
            self.ensure_directory(dst_path.parent)
            
            shutil.move(str(src_path), str(dst_path))
            return dst_path
        except OSError as e:
            raise FileSystemError(f"Failed to move {src} to {dst}: {e}")
    
    def delete_file(self, path: Union[str, Path]) -> bool:
        """
        Delete file if it exists
        
        Args:
            path: File path to delete
            
        Returns:
            True if file was deleted, False if it didn't exist
            
        Raises:
            FileSystemError: If file cannot be deleted
        """
        try:
            file_path = self._resolve_path(path)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except OSError as e:
            raise FileSystemError(f"Failed to delete file {path}: {e}")
    
    def delete_directory(self, path: Union[str, Path], recursive: bool = False) -> bool:
        """
        Delete directory
        
        Args:
            path: Directory path to delete
            recursive: Whether to delete non-empty directories
            
        Returns:
            True if directory was deleted, False if it didn't exist
            
        Raises:
            FileSystemError: If directory cannot be deleted
        """
        try:
            dir_path = self._resolve_path(path)
            if dir_path.exists():
                if recursive:
                    shutil.rmtree(dir_path)
                else:
                    dir_path.rmdir()
                return True
            return False
        except OSError as e:
            raise FileSystemError(f"Failed to delete directory {path}: {e}")
    
    def list_files(self, path: Union[str, Path], pattern: str = "*", recursive: bool = False) -> List[Path]:
        """
        List files in directory
        
        Args:
            path: Directory path
            pattern: File pattern (glob)
            recursive: Whether to search recursively
            
        Returns:
            List of file paths
            
        Raises:
            FileSystemError: If directory cannot be accessed
        """
        try:
            dir_path = self._resolve_path(path)
            if recursive:
                return list(dir_path.rglob(pattern))
            else:
                return list(dir_path.glob(pattern))
        except OSError as e:
            raise FileSystemError(f"Failed to list files in {path}: {e}")
    
    def get_file_info(self, path: Union[str, Path]) -> FileInfo:
        """
        Get file information
        
        Args:
            path: File path
            
        Returns:
            FileInfo object
        """
        return FileInfo.from_path(self._resolve_path(path))
    
    def make_safe_filename(self, filename: str, max_length: int = 255) -> str:
        """
        Convert string to safe filename
        
        Args:
            filename: Original filename
            max_length: Maximum filename length
            
        Returns:
            Safe filename string
        """
        # Replace problematic characters
        safe_chars = []
        for char in filename:
            if char.isalnum() or char in '-_.() ':
                safe_chars.append(char)
            else:
                safe_chars.append('_')
        
        safe_name = ''.join(safe_chars).strip()
        
        # Remove multiple consecutive spaces/underscores
        while '  ' in safe_name:
            safe_name = safe_name.replace('  ', ' ')
        while '__' in safe_name:
            safe_name = safe_name.replace('__', '_')
        
        # Truncate if too long
        if len(safe_name) > max_length:
            safe_name = safe_name[:max_length].rstrip()
        
        return safe_name or 'unnamed'
    
    def get_file_hash(self, path: Union[str, Path], algorithm: str = 'md5') -> str:
        """
        Calculate file hash
        
        Args:
            path: File path
            algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
            
        Returns:
            Hex digest of file hash
            
        Raises:
            FileSystemError: If file cannot be read or algorithm is invalid
        """
        try:
            file_path = self._resolve_path(path)
            hash_obj = hashlib.new(algorithm)
            
            with file_path.open('rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
        except (OSError, ValueError) as e:
            raise FileSystemError(f"Failed to calculate {algorithm} hash for {path}: {e}")
    
    def create_temp_file(self, suffix: str = '', prefix: str = 'tmp', text: bool = True) -> Path:
        """
        Create temporary file
        
        Args:
            suffix: File suffix
            prefix: File prefix
            text: Whether file is for text content
            
        Returns:
            Path to temporary file
        """
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, text=text)
        os.close(fd)  # Close the file descriptor
        return Path(temp_path)
    
    def create_temp_directory(self, prefix: str = 'tmp') -> Path:
        """
        Create temporary directory
        
        Args:
            prefix: Directory prefix
            
        Returns:
            Path to temporary directory
        """
        return Path(tempfile.mkdtemp(prefix=prefix))
    
    def _resolve_path(self, path: Union[str, Path]) -> Path:
        """Resolve path relative to base_path if not absolute"""
        path = Path(path)
        if not path.is_absolute():
            path = self.base_path / path
        return path.resolve()


# Convenience factory functions
def create_cache_manager(cache_dir: Union[str, Path] = "cache") -> FileManager:
    """Create FileManager for cache operations"""
    return FileManager(cache_dir)


def create_output_manager(output_dir: Union[str, Path] = "output") -> FileManager:
    """Create FileManager for output operations"""
    return FileManager(output_dir)


def create_config_manager(config_dir: Union[str, Path] = "config") -> FileManager:
    """Create FileManager for configuration files"""
    return FileManager(config_dir)