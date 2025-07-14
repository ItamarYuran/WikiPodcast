"""
Configuration Management System
Centralized configuration with validation and environment support
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, Type, TypeVar, List
from dataclasses import dataclass, field
from dotenv import load_dotenv
import json


T = TypeVar('T')


@dataclass
class APIConfig:
    """API configuration settings"""
    openai_api_key: str = ""
    google_cloud_project: str = ""
    google_cloud_credentials_path: str = ""
    
    def __post_init__(self):
        # Load from environment if not provided
        if not self.openai_api_key:
            self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        if not self.google_cloud_project:
            self.google_cloud_project = os.getenv('GOOGLE_CLOUD_PROJECT', '')
        if not self.google_cloud_credentials_path:
            self.google_cloud_credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
    
    def is_valid(self) -> bool:
        """Check if all required API keys are present"""
        return bool(self.openai_api_key and self.google_cloud_project)


@dataclass
class ContentSourceConfig:
    """Content source configuration"""
    wikipedia_api_url: str = "https://en.wikipedia.org/api/rest_v1"
    wikipedia_rate_limit: float = 2.0  # requests per second
    max_article_length: int = 50000  # characters
    min_article_length: int = 1000   # characters
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    
    # User agent for API requests
    user_agent: str = "Wikipedia-Podcast-Pipeline/1.0 (Educational Use)"


@dataclass
class AudioConfig:
    """Audio processing configuration"""
    default_voice: str = "en-US-Journey-D"
    audio_format: str = "mp3"
    sample_rate: int = 24000
    enable_ssml: bool = True
    chunk_size: int = 2000  # characters per TTS chunk
    
    # Production settings
    enable_production_effects: bool = True
    normalize_audio: bool = True
    
    # Output paths
    output_directory: str = "output/audio"
    temp_directory: str = "temp/audio"


@dataclass
class ScriptConfig:
    """Script generation configuration"""
    default_style: str = "conversational"
    target_duration_minutes: int = 10
    max_duration_minutes: int = 30
    
    # Chapter editing settings
    enable_chapter_editing: bool = True
    chapter_edit_threshold_words: int = 3000
    
    # Cache settings
    cache_enabled: bool = True
    cache_directory: str = "cache/scripts"


@dataclass
class CacheConfig:
    """Caching configuration"""
    enabled: bool = True
    base_directory: str = "cache"
    max_size_mb: int = 1000
    default_ttl_hours: int = 24
    
    # Cache directories
    articles_cache: str = "cache/articles"
    scripts_cache: str = "cache/scripts"
    audio_cache: str = "cache/audio"


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    file_path: str = "logs/pipeline.log"
    console_enabled: bool = True


@dataclass
class PipelineConfig:
    """Main pipeline configuration"""
    # Component configurations
    api: APIConfig = field(default_factory=APIConfig)
    content_source: ContentSourceConfig = field(default_factory=ContentSourceConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    script: ScriptConfig = field(default_factory=ScriptConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Global settings
    project_root: str = ""
    environment: str = "development"  # development, production
    debug_mode: bool = True
    
    def __post_init__(self):
        if not self.project_root:
            self.project_root = str(Path.cwd())


class ConfigurationError(Exception):
    """Configuration-related errors"""
    pass


class ConfigManager:
    """
    Centralized configuration management with validation and environment support
    """
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self._config: Optional[PipelineConfig] = None
        self._load_environment()
    
    def load_config(self, config_file: Optional[str] = None) -> PipelineConfig:
        """
        Load configuration from file and environment
        
        Args:
            config_file: Optional config file name (JSON)
            
        Returns:
            Loaded configuration
            
        Raises:
            ConfigurationError: If configuration cannot be loaded or is invalid
        """
        try:
            # Start with default configuration
            config_data = {}
            
            # Load from JSON file if specified
            if config_file:
                config_path = self.config_dir / config_file
                if config_path.exists():
                    with config_path.open() as f:
                        config_data = json.load(f)
            
            # Create configuration object
            self._config = self._create_config_from_dict(config_data)
            
            # Validate configuration
            self._validate_config(self._config)
            
            return self._config
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def get_config(self) -> PipelineConfig:
        """
        Get current configuration, loading default if not loaded
        
        Returns:
            Current configuration
        """
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def save_config(self, config: PipelineConfig, config_file: str = "pipeline_config.json") -> None:
        """
        Save configuration to file
        
        Args:
            config: Configuration to save
            config_file: Output file name
            
        Raises:
            ConfigurationError: If configuration cannot be saved
        """
        try:
            self.config_dir.mkdir(exist_ok=True)
            config_path = self.config_dir / config_file
            
            # Convert to dictionary (excluding sensitive data)
            config_dict = self._config_to_dict(config, include_secrets=False)
            
            with config_path.open('w') as f:
                json.dump(config_dict, f, indent=2)
                
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def get_api_config(self) -> APIConfig:
        """Get API configuration"""
        return self.get_config().api
    
    def get_content_source_config(self) -> ContentSourceConfig:
        """Get content source configuration"""
        return self.get_config().content_source
    
    def get_audio_config(self) -> AudioConfig:
        """Get audio configuration"""
        return self.get_config().audio
    
    def get_script_config(self) -> ScriptConfig:
        """Get script configuration"""
        return self.get_config().script
    
    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration"""
        return self.get_config().cache
    
    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration"""
        return self.get_config().logging
    
    def update_config(self, **kwargs) -> None:
        """
        Update configuration values
        
        Args:
            **kwargs: Configuration values to update
        """
        if self._config is None:
            self._config = self.load_config()
        
        # Update configuration fields
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
    
    def _load_environment(self) -> None:
        """Load environment variables from .env files"""
        # Look for .env files in config directory and project root
        env_files = [
            self.config_dir / "api_keys.env",
            self.config_dir / ".env",
            Path(".env")
        ]
        
        for env_file in env_files:
            if env_file.exists():
                load_dotenv(env_file)
    
    def _create_config_from_dict(self, config_data: Dict[str, Any]) -> PipelineConfig:
        """Create configuration object from dictionary"""
        
        def create_dataclass_from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
            """Helper to create dataclass from dictionary"""
            if not data:
                return cls()
            
            # Filter out unknown fields
            valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
            filtered_data = {k: v for k, v in data.items() if k in valid_fields}
            
            return cls(**filtered_data)
        
        # Create component configurations
        api_config = create_dataclass_from_dict(APIConfig, config_data.get('api', {}))
        content_config = create_dataclass_from_dict(ContentSourceConfig, config_data.get('content_source', {}))
        audio_config = create_dataclass_from_dict(AudioConfig, config_data.get('audio', {}))
        script_config = create_dataclass_from_dict(ScriptConfig, config_data.get('script', {}))
        cache_config = create_dataclass_from_dict(CacheConfig, config_data.get('cache', {}))
        logging_config = create_dataclass_from_dict(LoggingConfig, config_data.get('logging', {}))
        
        # Create main configuration
        main_data = {k: v for k, v in config_data.items() 
                    if k not in ['api', 'content_source', 'audio', 'script', 'cache', 'logging']}
        
        return PipelineConfig(
            api=api_config,
            content_source=content_config,
            audio=audio_config,
            script=script_config,
            cache=cache_config,
            logging=logging_config,
            **main_data
        )
    
    def _config_to_dict(self, config: PipelineConfig, include_secrets: bool = False) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        def dataclass_to_dict(obj) -> Dict[str, Any]:
            result = {}
            for field_name, field_value in obj.__dict__.items():
                if hasattr(field_value, '__dict__'):  # Nested dataclass
                    result[field_name] = dataclass_to_dict(field_value)
                else:
                    # Skip sensitive data unless explicitly requested
                    if not include_secrets and 'key' in field_name.lower():
                        result[field_name] = "[REDACTED]"
                    else:
                        result[field_name] = field_value
            return result
        
        return dataclass_to_dict(config)
    
    def _validate_config(self, config: PipelineConfig) -> None:
        """
        Validate configuration
        
        Args:
            config: Configuration to validate
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        errors = []
        
        # Validate API configuration
        if not config.api.is_valid():
            errors.append("Missing required API keys (OpenAI API key and Google Cloud project)")
        
        # Validate paths
        if config.api.google_cloud_credentials_path:
            creds_path = Path(config.api.google_cloud_credentials_path)
            if not creds_path.exists():
                errors.append(f"Google Cloud credentials file not found: {creds_path}")
        
        # Validate numeric ranges
        if config.audio.sample_rate <= 0:
            errors.append("Audio sample rate must be positive")
        
        if config.script.target_duration_minutes <= 0:
            errors.append("Target duration must be positive")
        
        if config.cache.max_size_mb <= 0:
            errors.append("Cache max size must be positive")
        
        if errors:
            raise ConfigurationError("Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> PipelineConfig:
    """Get current configuration"""
    return get_config_manager().get_config()


def get_api_config() -> APIConfig:
    """Get API configuration"""
    return get_config_manager().get_api_config()


def get_content_source_config() -> ContentSourceConfig:
    """Get content source configuration"""
    return get_config_manager().get_content_source_config()


def get_audio_config() -> AudioConfig:
    """Get audio configuration"""
    return get_config_manager().get_audio_config()


def get_script_config() -> ScriptConfig:
    """Get script configuration"""
    return get_config_manager().get_script_config()


def get_cache_config() -> CacheConfig:
    """Get cache configuration"""
    return get_config_manager().get_cache_config()