"""
Script Caching System
Production implementation for saving and retrieving generated scripts.
"""

import json
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

from core.models import PodcastScript
from core import ProcessingResult, ProcessingStatus


class ScriptCache:
    """
    Production script cache implementation that actually saves and loads scripts.
    """
    
    def __init__(self, cache_dir: str = "processed_scripts"):
        """
        Initialize the script cache.
        
        Args:
            cache_dir: Directory to store cached scripts
        """
        self.cache_dir = Path(cache_dir)
        self.logger = logging.getLogger(__name__)
        
        # Ensure cache directory exists
        self._ensure_cache_structure()
        
        print(f"📋 ScriptCache initialized (working) - {self.cache_dir}")
    
    def _ensure_cache_structure(self):
        """Ensure cache directory and style subdirectories exist"""
        try:
            self.cache_dir.mkdir(exist_ok=True)
            
            # Create style subdirectories
            style_dirs = [
                'conversational', 'educational', 'documentary', 'narrative',
                'interview', 'news_report', 'storytelling', 'comedy',
                'academic', 'kids_educational'
            ]
            
            for style in style_dirs:
                style_dir = self.cache_dir / style
                style_dir.mkdir(exist_ok=True)
            
            self.logger.info(f"Cache structure ensured at {self.cache_dir.absolute()}")
            
        except Exception as e:
            self.logger.error(f"Failed to create cache structure: {e}")
            # Fallback to current directory
            self.cache_dir = Path(".")
    
    def set(self, cache_key: str, script: PodcastScript) -> bool:
        """
        Save a script to cache.
        
        Args:
            cache_key: Unique identifier for the script
            script: PodcastScript object to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_title = self._make_safe_filename(script.title)
            filename = f"{safe_title}_{timestamp}.json"
            
            # Determine style directory
            style_name = script.style.value if hasattr(script.style, 'value') else str(script.style)
            style_dir = self.cache_dir / style_name
            style_dir.mkdir(exist_ok=True)
            
            # Full file path
            file_path = style_dir / filename
            
            # Convert script to dictionary for JSON serialization
            script_data = script.to_dict()
            
            # Add cache metadata
            script_data['cached_at'] = datetime.now().isoformat()
            script_data['cache_key'] = cache_key
            script_data['cache_version'] = '1.0'
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Script cached successfully: {file_path}")
            print(f"📝 Script cached: {filename}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cache script: {e}", exc_info=True)
            print(f"❌ Failed to cache script: {e}")
            return False
    
    def get(self, cache_key: str) -> Optional[PodcastScript]:
        """
        Retrieve a script from cache by key.
        
        Args:
            cache_key: Unique identifier for the script
            
        Returns:
            PodcastScript if found, None otherwise
        """
        try:
            # Search all style directories for the cache key
            for style_dir in self.cache_dir.iterdir():
                if style_dir.is_dir():
                    for script_file in style_dir.glob('*.json'):
                        try:
                            with open(script_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            if data.get('cache_key') == cache_key:
                                # Convert back to PodcastScript object
                                return PodcastScript.from_dict(data)
                                
                        except Exception as e:
                            self.logger.warning(f"Corrupted cache file {script_file}: {e}")
                            continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve script from cache: {e}")
            return None
    
    def list_cached_scripts(self) -> List[Dict[str, Any]]:
        """
        List all cached scripts with metadata.
        
        Returns:
            List of script metadata dictionaries
        """
        scripts = []
        
        try:
            # Scan all style directories
            for style_dir in self.cache_dir.iterdir():
                if style_dir.is_dir() and not style_dir.name.startswith('.'):
                    for script_file in style_dir.glob('*.json'):
                        try:
                            with open(script_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            # Extract metadata
                            script_info = {
                                'filename': script_file.name,
                                'filepath': str(script_file),
                                'title': data.get('title', script_file.stem),
                                'style': data.get('style', style_dir.name),
                                'duration': self._format_duration(data.get('estimated_duration', 0)),
                                'word_count': data.get('word_count', 0),
                                'created_at': data.get('cached_at', data.get('created_at', '')),
                                'source_article_id': data.get('source_article_id', ''),
                                'cache_key': data.get('cache_key', ''),
                                'file_size': script_file.stat().st_size
                            }
                            
                            scripts.append(script_info)
                            
                        except Exception as e:
                            self.logger.warning(f"Failed to read script metadata from {script_file}: {e}")
                            # Add basic info for corrupted files
                            scripts.append({
                                'filename': script_file.name,
                                'filepath': str(script_file),
                                'title': f"Corrupted: {script_file.stem}",
                                'style': style_dir.name,
                                'duration': "Unknown",
                                'word_count': 0,
                                'created_at': '',
                                'source_article_id': '',
                                'cache_key': '',
                                'file_size': script_file.stat().st_size
                            })
            
            # Sort by creation date (newest first)
            scripts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            self.logger.info(f"Found {len(scripts)} cached scripts")
            
        except Exception as e:
            self.logger.error(f"Failed to list cached scripts: {e}")
        
        return scripts
    
    def load_script_by_filename(self, filename: str) -> Optional[PodcastScript]:
        """
        Load a script by its filename.
        
        Args:
            filename: Name of the script file
            
        Returns:
            PodcastScript if found, None otherwise
        """
        try:
            # Search all style directories
            for style_dir in self.cache_dir.iterdir():
                if style_dir.is_dir():
                    script_file = style_dir / filename
                    if script_file.exists():
                        with open(script_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        return PodcastScript.from_dict(data)
            
            self.logger.warning(f"Script file not found: {filename}")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to load script {filename}: {e}")
            return None
    
    def delete_script(self, filename: str) -> bool:
        """
        Delete a cached script.
        
        Args:
            filename: Name of the script file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Search all style directories
            for style_dir in self.cache_dir.iterdir():
                if style_dir.is_dir():
                    script_file = style_dir / filename
                    if script_file.exists():
                        script_file.unlink()
                        self.logger.info(f"Deleted script: {script_file}")
                        print(f"🗑️ Deleted script: {filename}")
                        return True
            
            self.logger.warning(f"Script file not found for deletion: {filename}")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to delete script {filename}: {e}")
            return False
    
    def cleanup_old_scripts(self, max_age_days: int = 30) -> int:
        """
        Clean up scripts older than specified days.
        
        Args:
            max_age_days: Maximum age in days before deletion
            
        Returns:
            Number of scripts deleted
        """
        deleted_count = 0
        cutoff_timestamp = datetime.now().timestamp() - (max_age_days * 24 * 3600)
        
        try:
            for style_dir in self.cache_dir.iterdir():
                if style_dir.is_dir():
                    for script_file in style_dir.glob('*.json'):
                        if script_file.stat().st_mtime < cutoff_timestamp:
                            script_file.unlink()
                            deleted_count += 1
                            self.logger.info(f"Deleted old script: {script_file}")
            
            if deleted_count > 0:
                print(f"🧹 Cleaned up {deleted_count} old scripts")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old scripts: {e}")
        
        return deleted_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            'total_scripts': 0,
            'scripts_by_style': {},
            'total_size_mb': 0,
            'oldest_script': None,
            'newest_script': None
        }
        
        try:
            total_size = 0
            oldest_date = None
            newest_date = None
            
            for style_dir in self.cache_dir.iterdir():
                if style_dir.is_dir() and not style_dir.name.startswith('.'):
                    style_count = 0
                    for script_file in style_dir.glob('*.json'):
                        style_count += 1
                        total_size += script_file.stat().st_size
                        
                        # Track oldest and newest
                        file_time = datetime.fromtimestamp(script_file.stat().st_mtime)
                        if oldest_date is None or file_time < oldest_date:
                            oldest_date = file_time
                        if newest_date is None or file_time > newest_date:
                            newest_date = file_time
                    
                    if style_count > 0:
                        stats['scripts_by_style'][style_dir.name] = style_count
                        stats['total_scripts'] += style_count
            
            stats['total_size_mb'] = total_size / (1024 * 1024)
            stats['oldest_script'] = oldest_date.isoformat() if oldest_date else None
            stats['newest_script'] = newest_date.isoformat() if newest_date else None
            
        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {e}")
        
        return stats
    
    def _make_safe_filename(self, title: str) -> str:
        """Convert title to safe filename"""
        # Remove or replace unsafe characters
        safe_title = re.sub(r'[^\w\s\-_]', '', title)
        safe_title = re.sub(r'\s+', '_', safe_title)
        safe_title = safe_title.strip('_')
        
        # Limit length
        if len(safe_title) > 50:
            safe_title = safe_title[:50]
        
        # Ensure it's not empty
        if not safe_title:
            safe_title = "untitled"
        
        return safe_title
    
    def _format_duration(self, duration_seconds: int) -> str:
        """Format duration in seconds to human-readable string"""
        if duration_seconds == 0:
            return "Unknown"
        
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        
        if minutes > 0:
            return f"{minutes}m{seconds:02d}s"
        else:
            return f"{seconds}s"
    
    def repair_corrupted_files(self) -> int:
        """
        Attempt to repair or remove corrupted cache files.
        
        Returns:
            Number of files processed
        """
        processed_count = 0
        
        try:
            for style_dir in self.cache_dir.iterdir():
                if style_dir.is_dir():
                    for script_file in style_dir.glob('*.json'):
                        try:
                            with open(script_file, 'r', encoding='utf-8') as f:
                                json.load(f)  # Try to parse JSON
                        except json.JSONDecodeError:
                            # File is corrupted, remove it
                            script_file.unlink()
                            processed_count += 1
                            self.logger.warning(f"Removed corrupted file: {script_file}")
                        except Exception as e:
                            self.logger.error(f"Error checking file {script_file}: {e}")
            
            if processed_count > 0:
                print(f"🔧 Repaired cache: removed {processed_count} corrupted files")
            
        except Exception as e:
            self.logger.error(f"Failed to repair cache: {e}")
        
        return processed_count


class CacheManager:
    """
    Manager for multiple cache types.
    """
    
    def __init__(self):
        self.script_cache = ScriptCache()
        self.logger = logging.getLogger(__name__)
    
    def get_script_cache(self) -> ScriptCache:
        """Get the script cache instance"""
        return self.script_cache
    
    def cleanup_all_caches(self, max_age_days: int = 30) -> Dict[str, int]:
        """
        Clean up all caches.
        
        Args:
            max_age_days: Maximum age in days before deletion
            
        Returns:
            Dictionary with cleanup results
        """
        results = {}
        
        try:
            results['scripts_deleted'] = self.script_cache.cleanup_old_scripts(max_age_days)
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup caches: {e}")
            results['error'] = str(e)
        
        return results
    
    def get_all_cache_stats(self) -> Dict[str, Any]:
        """Get statistics for all caches"""
        try:
            return {
                'script_cache': self.script_cache.get_cache_stats()
            }
        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {e}")
            return {'error': str(e)}