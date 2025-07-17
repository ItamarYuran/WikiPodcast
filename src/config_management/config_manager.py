"""
Simplified Configuration Management System
"""
import os
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass, field
from dotenv import load_dotenv
import json

@dataclass
class PipelineConfig:
    """Main pipeline configuration"""
    # API settings
    openai_api_key: str = ""
    google_cloud_project: str = ""
    google_cloud_credentials_path: str = ""
    
    # Content source settings
    wikipedia_api_url: str = "https://en.wikipedia.org/api/rest_v1"
    user_agent: str = "Wikipedia-Podcast-Pipeline/1.0 (Educational Use)"
    
    # Audio settings
    default_voice: str = "en-US-Journey-D"
    audio_format: str = "mp3"
    
    # Script settings
    default_style: str = "conversational"
    target_duration_minutes: int = 10
    
    # Cache settings
    cache_enabled: bool = True
    cache_dir: str = "processed_scripts"  # Changed from "cache" to "processed_scripts"
    
    def __post_init__(self):
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    
    def get(self, key: str, default=None):
        """
        Provide dict-like access to configuration values.
        This is needed for the script generator which expects config.get().
        """
        if hasattr(self, key):
            return getattr(self, key)
        return default
    
    def __contains__(self, key: str) -> bool:
        """
        Support 'in' operator for checking if a key exists.
        This is needed for code like: if 'openai_api_key' in self.config
        """
        return hasattr(self, key)
    
    def __getitem__(self, key: str):
        """Allow dict-like access with brackets"""
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"Configuration key '{key}' not found")
    
    def __setitem__(self, key: str, value):
        """Allow dict-like assignment with brackets"""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise KeyError(f"Configuration key '{key}' not found")

class ConfigManager:
    """
    Centralized configuration management with validation and environment support.
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initializes the configuration manager.
        
        Args:
            config_path: The path to the configuration file.
        """
        self.config_path = Path(config_path) if config_path else Path("config.json")
        self._config: Optional[PipelineConfig] = None
        self._load_environment()
    
    def get_config(self) -> PipelineConfig:
        """
        Gets the current configuration, loading it if it hasn't been loaded yet.
        
        Returns:
            The current configuration.
        """
        if self._config is None:
            self._config = self._load_config()
        return self._config
    
    def _load_config(self) -> PipelineConfig:
        """
        Loads the configuration from the configuration file.
        
        Returns:
            The loaded configuration.
        """
        if self.config_path.exists():
            with self.config_path.open() as f:
                config_data = json.load(f)
            return PipelineConfig(**config_data)
        return PipelineConfig()
    
    def _load_environment(self) -> None:
        """
        Loads environment variables from .env files.
        """
        env_files = [Path(".env"), Path("../config/api_keys.env")]
        for env_file in env_files:
            if env_file.exists():
                load_dotenv(env_file)

# Global configuration instance
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """Gets the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_config() -> PipelineConfig:
    """Gets the current configuration."""
    return get_config_manager().get_config()