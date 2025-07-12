"""
Core interfaces and abstract base classes for the podcast generation system.
These define the contracts that all implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Protocol
from dataclasses import dataclass
from enum import Enum


class ProcessingStatus(Enum):
    """Status of processing operations"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProcessingResult:
    """Standard result format for all processing operations"""
    status: ProcessingStatus
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def is_success(self) -> bool:
        return self.status == ProcessingStatus.COMPLETED
    
    @property
    def is_failure(self) -> bool:
        return self.status == ProcessingStatus.FAILED


# Content Interfaces
class ContentFetcher(ABC):
    """Interface for fetching content from various sources"""
    
    @abstractmethod
    def fetch_article(self, identifier: str) -> ProcessingResult:
        """Fetch a single article by identifier"""
        pass
    
    @abstractmethod
    def fetch_trending(self, count: int = 10) -> ProcessingResult:
        """Fetch trending articles"""
        pass
    
    @abstractmethod
    def fetch_featured(self, count: int = 10) -> ProcessingResult:
        """Fetch featured articles"""
        pass
    
    @abstractmethod
    def search_articles(self, query: str, limit: int = 10) -> ProcessingResult:
        """Search for articles matching query"""
        pass


class ContentProcessor(ABC):
    """Interface for processing and transforming content"""
    
    @abstractmethod
    def process_article(self, article: Any) -> ProcessingResult:
        """Process a single article"""
        pass
    
    @abstractmethod
    def batch_process(self, articles: List[Any]) -> List[ProcessingResult]:
        """Process multiple articles"""
        pass


# Script Generation Interfaces
class ScriptGenerator(ABC):
    """Interface for generating podcast scripts"""
    
    @abstractmethod
    def generate_script(self, 
                       content: Any, 
                       style: str = "conversational",
                       custom_instructions: Optional[str] = None,
                       target_duration: Optional[int] = None) -> ProcessingResult:
        """Generate a podcast script from content"""
        pass
    
    @abstractmethod
    def get_available_styles(self) -> Dict[str, Dict[str, Any]]:
        """Get available script styles"""
        pass


class ScriptProcessor(ABC):
    """Interface for processing and enhancing scripts"""
    
    @abstractmethod
    def process_for_tts(self, script: str) -> ProcessingResult:
        """Process script for text-to-speech optimization"""
        pass
    
    @abstractmethod
    def validate_script(self, script: str) -> ProcessingResult:
        """Validate script format and content"""
        pass


# Audio Generation Interfaces
class AudioGenerator(ABC):
    """Interface for generating audio from scripts"""
    
    @abstractmethod
    def generate_audio(self, 
                      script: str, 
                      voice: str = "default",
                      format: str = "mp3") -> ProcessingResult:
        """Generate audio from script"""
        pass
    
    @abstractmethod
    def get_available_voices(self) -> Dict[str, Dict[str, Any]]:
        """Get available TTS voices"""
        pass


class AudioProcessor(ABC):
    """Interface for post-processing audio"""
    
    @abstractmethod
    def enhance_audio(self, 
                     audio_path: str, 
                     enhancements: Dict[str, Any]) -> ProcessingResult:
        """Apply enhancements to audio"""
        pass
    
    @abstractmethod
    def combine_audio(self, audio_files: List[str]) -> ProcessingResult:
        """Combine multiple audio files"""
        pass


# Storage Interfaces
class CacheManager(ABC):
    """Interface for managing cached content"""
    
    @abstractmethod
    def store(self, key: str, data: Any, metadata: Optional[Dict] = None) -> bool:
        """Store data in cache"""
        pass
    
    @abstractmethod
    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data from cache"""
        pass
    
    @abstractmethod
    def list_items(self, pattern: Optional[str] = None) -> List[str]:
        """List cached items"""
        pass
    
    @abstractmethod
    def clear(self, pattern: Optional[str] = None) -> bool:
        """Clear cache items"""
        pass


# Configuration Interfaces
class ConfigManager(ABC):
    """Interface for managing configuration"""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value"""
        pass
    
    @abstractmethod
    def validate_config(self) -> ProcessingResult:
        """Validate current configuration"""
        pass


# Pipeline Interfaces
class PipelineStep(ABC):
    """Interface for individual pipeline steps"""
    
    @abstractmethod
    def execute(self, input_data: Any) -> ProcessingResult:
        """Execute this pipeline step"""
        pass
    
    @abstractmethod
    def can_process(self, input_data: Any) -> bool:
        """Check if this step can process the input"""
        pass


class Pipeline(ABC):
    """Interface for processing pipelines"""
    
    @abstractmethod
    def add_step(self, step: PipelineStep) -> None:
        """Add a step to the pipeline"""
        pass
    
    @abstractmethod
    def execute(self, input_data: Any) -> ProcessingResult:
        """Execute the entire pipeline"""
        pass


# Event System
class EventListener(Protocol):
    """Protocol for event listeners"""
    
    def handle_event(self, event_type: str, data: Any) -> None:
        """Handle an event"""
        pass


class EventBus(ABC):
    """Interface for event bus system"""
    
    @abstractmethod
    def subscribe(self, event_type: str, listener: EventListener) -> None:
        """Subscribe to events"""
        pass
    
    @abstractmethod
    def publish(self, event_type: str, data: Any) -> None:
        """Publish an event"""
        pass


# Factory Interfaces
class ComponentFactory(ABC):
    """Interface for creating system components"""
    
    @abstractmethod
    def create_content_fetcher(self) -> ContentFetcher:
        """Create content fetcher"""
        pass
    
    @abstractmethod
    def create_script_generator(self) -> ScriptGenerator:
        """Create script generator"""
        pass
    
    @abstractmethod
    def create_audio_generator(self) -> AudioGenerator:
        """Create audio generator"""
        pass


# Service Interfaces
class ServiceHealth(ABC):
    """Interface for service health checks"""
    
    @abstractmethod
    def check_health(self) -> ProcessingResult:
        """Check service health"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get detailed service status"""
        pass


# Quality Interfaces
class QualityChecker(ABC):
    """Interface for quality assessment"""
    
    @abstractmethod
    def assess_content(self, content: Any) -> ProcessingResult:
        """Assess content quality"""
        pass
    
    @abstractmethod
    def assess_script(self, script: str) -> ProcessingResult:
        """Assess script quality"""
        pass
    
    @abstractmethod
    def assess_audio(self, audio_path: str) -> ProcessingResult:
        """Assess audio quality"""
        pass


# Metrics Interfaces
class MetricsCollector(ABC):
    """Interface for collecting system metrics"""
    
    @abstractmethod
    def record_metric(self, name: str, value: float, tags: Optional[Dict] = None) -> None:
        """Record a metric"""
        pass
    
    @abstractmethod
    def get_metrics(self, pattern: Optional[str] = None) -> Dict[str, Any]:
        """Get collected metrics"""
        pass