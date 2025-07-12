"""
Core package for the podcast generation system.
Contains interfaces, models, and foundational components.
"""

# Import key interfaces for easy access
from .interfaces import (
    ContentFetcher,
    ContentProcessor,
    ScriptGenerator,
    ScriptProcessor,
    AudioGenerator,
    AudioProcessor,
    CacheManager,
    ConfigManager,
    Pipeline,
    PipelineStep,
    ProcessingResult,
    ProcessingStatus
)

# Import core models
from .models import (
    Article,
    PodcastScript,
    ScriptSegment,
    PodcastEpisode,
    VoiceConfig,
    AudioMetadata,
    ContentMetadata,
    ProcessingJob,
    PipelineConfig,
    ContentType,
    ScriptStyle,
    AudioFormat,
    QualityLevel
)

# Import exceptions
from .exceptions import (
    PodcastGenerationError,
    ConfigurationError,
    ContentFetchError,
    ScriptGenerationError,
    AudioGenerationError,
    CacheError,
    ValidationError,
    APIError,
    ContentValidationError,
    ScriptProcessingError,
    AudioProcessingError,
    RateLimitError,
    AuthenticationError,
    QuotaExceededError,
    PipelineError,
    TimeoutError,
    DependencyError,
    StorageError,
    QualityError
)

__version__ = "1.0.0"
__all__ = [
    # Interfaces
    "ContentFetcher",
    "ContentProcessor", 
    "ScriptGenerator",
    "ScriptProcessor",
    "AudioGenerator",
    "AudioProcessor",
    "CacheManager",
    "ConfigManager",
    "Pipeline",
    "PipelineStep",
    "ProcessingResult",
    "ProcessingStatus",
    
    # Models
    "Article",
    "PodcastScript",
    "ScriptSegment", 
    "PodcastEpisode",
    "VoiceConfig",
    "AudioMetadata",
    "ContentMetadata",
    "ProcessingJob",
    "PipelineConfig",
    "ContentType",
    "ScriptStyle",
    "AudioFormat",
    "QualityLevel",
    
    # Exceptions
    "PodcastGenerationError",
    "ConfigurationError",
    "ContentFetchError",
    "ScriptGenerationError",
    "AudioGenerationError",
    "CacheError",
    "ValidationError",
    "APIError",
    "ContentValidationError",
    "ScriptProcessingError",
    "AudioProcessingError",
    "RateLimitError",
    "AuthenticationError",
    "QuotaExceededError",
    "PipelineError",
    "TimeoutError",
    "DependencyError",
    "StorageError",
    "QualityError"
]