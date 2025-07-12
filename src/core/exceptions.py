"""
Custom exceptions for the podcast generation system.
Provides specific error types for better error handling and debugging.
"""

from typing import Optional, Dict, Any


class PodcastGenerationError(Exception):
    """Base exception for all podcast generation errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {super().__str__()}"
        return super().__str__()


class ConfigurationError(PodcastGenerationError):
    """Raised when there's a configuration problem"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)
        self.config_key = config_key


class ContentFetchError(PodcastGenerationError):
    """Raised when content fetching fails"""
    
    def __init__(self, message: str, source: Optional[str] = None, url: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="CONTENT_FETCH_ERROR", **kwargs)
        self.source = source
        self.url = url


class ContentValidationError(PodcastGenerationError):
    """Raised when content validation fails"""
    
    def __init__(self, message: str, validation_type: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="CONTENT_VALIDATION_ERROR", **kwargs)
        self.validation_type = validation_type


class ScriptGenerationError(PodcastGenerationError):
    """Raised when script generation fails"""
    
    def __init__(self, message: str, style: Optional[str] = None, article_id: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="SCRIPT_GENERATION_ERROR", **kwargs)
        self.style = style
        self.article_id = article_id


class ScriptProcessingError(PodcastGenerationError):
    """Raised when script processing fails"""
    
    def __init__(self, message: str, processing_type: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="SCRIPT_PROCESSING_ERROR", **kwargs)
        self.processing_type = processing_type


class AudioGenerationError(PodcastGenerationError):
    """Raised when audio generation fails"""
    
    def __init__(self, message: str, voice: Optional[str] = None, provider: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="AUDIO_GENERATION_ERROR", **kwargs)
        self.voice = voice
        self.provider = provider


class AudioProcessingError(PodcastGenerationError):
    """Raised when audio processing fails"""
    
    def __init__(self, message: str, processing_type: Optional[str] = None, audio_file: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="AUDIO_PROCESSING_ERROR", **kwargs)
        self.processing_type = processing_type
        self.audio_file = audio_file


class CacheError(PodcastGenerationError):
    """Raised when cache operations fail"""
    
    def __init__(self, message: str, cache_key: Optional[str] = None, operation: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="CACHE_ERROR", **kwargs)
        self.cache_key = cache_key
        self.operation = operation


class ValidationError(PodcastGenerationError):
    """Raised when validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None, **kwargs):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        self.field = field
        self.value = value


class APIError(PodcastGenerationError):
    """Raised when external API calls fail"""
    
    def __init__(self, message: str, api_name: Optional[str] = None, status_code: Optional[int] = None, **kwargs):
        super().__init__(message, error_code="API_ERROR", **kwargs)
        self.api_name = api_name
        self.status_code = status_code


class RateLimitError(APIError):
    """Raised when API rate limits are exceeded"""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, error_code="RATE_LIMIT_ERROR", **kwargs)
        self.retry_after = retry_after


class AuthenticationError(APIError):
    """Raised when API authentication fails"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="AUTHENTICATION_ERROR", **kwargs)


class QuotaExceededError(APIError):
    """Raised when API quota is exceeded"""
    
    def __init__(self, message: str, quota_type: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="QUOTA_EXCEEDED_ERROR", **kwargs)
        self.quota_type = quota_type


class PipelineError(PodcastGenerationError):
    """Raised when pipeline execution fails"""
    
    def __init__(self, message: str, step: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="PIPELINE_ERROR", **kwargs)
        self.step = step


class TimeoutError(PodcastGenerationError):
    """Raised when operations timeout"""
    
    def __init__(self, message: str, timeout_duration: Optional[int] = None, **kwargs):
        super().__init__(message, error_code="TIMEOUT_ERROR", **kwargs)
        self.timeout_duration = timeout_duration


class DependencyError(PodcastGenerationError):
    """Raised when required dependencies are missing"""
    
    def __init__(self, message: str, dependency: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="DEPENDENCY_ERROR", **kwargs)
        self.dependency = dependency


class StorageError(PodcastGenerationError):
    """Raised when storage operations fail"""
    
    def __init__(self, message: str, path: Optional[str] = None, operation: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="STORAGE_ERROR", **kwargs)
        self.path = path
        self.operation = operation


class QualityError(PodcastGenerationError):
    """Raised when quality checks fail"""
    
    def __init__(self, message: str, quality_check: Optional[str] = None, threshold: Optional[float] = None, **kwargs):
        super().__init__(message, error_code="QUALITY_ERROR", **kwargs)
        self.quality_check = quality_check
        self.threshold = threshold


# Exception mapping for easy lookup
EXCEPTION_MAP = {
    "CONFIG_ERROR": ConfigurationError,
    "CONTENT_FETCH_ERROR": ContentFetchError,
    "CONTENT_VALIDATION_ERROR": ContentValidationError,
    "SCRIPT_GENERATION_ERROR": ScriptGenerationError,
    "SCRIPT_PROCESSING_ERROR": ScriptProcessingError,
    "AUDIO_GENERATION_ERROR": AudioGenerationError,
    "AUDIO_PROCESSING_ERROR": AudioProcessingError,
    "CACHE_ERROR": CacheError,
    "VALIDATION_ERROR": ValidationError,
    "API_ERROR": APIError,
    "RATE_LIMIT_ERROR": RateLimitError,
    "AUTHENTICATION_ERROR": AuthenticationError,
    "QUOTA_EXCEEDED_ERROR": QuotaExceededError,
    "PIPELINE_ERROR": PipelineError,
    "TIMEOUT_ERROR": TimeoutError,
    "DEPENDENCY_ERROR": DependencyError,
    "STORAGE_ERROR": StorageError,
    "QUALITY_ERROR": QualityError
}


def get_exception_class(error_code: str) -> type:
    """Get exception class by error code"""
    return EXCEPTION_MAP.get(error_code, PodcastGenerationError)


def create_exception(error_code: str, message: str, **kwargs) -> PodcastGenerationError:
    """Create exception instance by error code"""
    exception_class = get_exception_class(error_code)
    return exception_class(message, **kwargs)