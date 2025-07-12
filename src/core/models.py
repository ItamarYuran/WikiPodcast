"""
Core domain models for the podcast generation system.
These represent the key entities and value objects used throughout the system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import json


class ContentType(Enum):
    """Types of content that can be processed"""
    WIKIPEDIA_ARTICLE = "wikipedia_article"
    NEWS_ARTICLE = "news_article"
    BLOG_POST = "blog_post"
    RESEARCH_PAPER = "research_paper"
    CUSTOM_TEXT = "custom_text"


class ScriptStyle(Enum):
    """Available script styles"""
    CONVERSATIONAL = "conversational"
    EDUCATIONAL = "educational"
    NARRATIVE = "narrative"
    INTERVIEW = "interview"
    NEWS = "news"
    DOCUMENTARY = "documentary"


class AudioFormat(Enum):
    """Supported audio formats"""
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    M4A = "m4a"


class QualityLevel(Enum):
    """Quality levels for content and processing"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PREMIUM = "premium"


@dataclass
class ContentMetadata:
    """Metadata about content"""
    source: str
    language: str = "en"
    categories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    page_views: int = 0
    last_modified: Optional[datetime] = None
    references: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "source": self.source,
            "language": self.language,
            "categories": self.categories,
            "tags": self.tags,
            "quality_score": self.quality_score,
            "page_views": self.page_views,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "references": self.references,
            "images": self.images
        }


@dataclass
class Article:
    """Represents an article from any source"""
    id: str
    title: str
    content: str
    summary: str
    content_type: ContentType
    metadata: ContentMetadata
    url: Optional[str] = None
    word_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Calculate word count if not provided"""
        if self.word_count == 0:
            self.word_count = len(self.content.split())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "content_type": self.content_type.value,
            "metadata": self.metadata.to_dict(),
            "url": self.url,
            "word_count": self.word_count,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Article':
        """Create from dictionary"""
        metadata = ContentMetadata(**data["metadata"])
        return cls(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            summary=data["summary"],
            content_type=ContentType(data["content_type"]),
            metadata=metadata,
            url=data.get("url"),
            word_count=data.get("word_count", 0),
            created_at=datetime.fromisoformat(data["created_at"])
        )


@dataclass
class ScriptSegment:
    """Represents a segment of a podcast script"""
    id: str
    content: str
    segment_type: str  # intro, main, outro, transition
    estimated_duration: int  # in seconds
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "segment_type": self.segment_type,
            "estimated_duration": self.estimated_duration,
            "metadata": self.metadata
        }


@dataclass
class PodcastScript:
    """Represents a complete podcast script"""
    id: str
    title: str
    style: ScriptStyle
    source_article_id: str
    segments: List[ScriptSegment]
    script_text: str  # Full script with instructions
    tts_ready_text: str  # Cleaned for TTS
    estimated_duration: int  # in seconds
    word_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    custom_instructions: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Calculate word count if not provided"""
        if self.word_count == 0:
            self.word_count = len(self.tts_ready_text.split())
    
    @property
    def intro_segment(self) -> Optional[ScriptSegment]:
        """Get the intro segment"""
        return next((s for s in self.segments if s.segment_type == "intro"), None)
    
    @property
    def outro_segment(self) -> Optional[ScriptSegment]:
        """Get the outro segment"""
        return next((s for s in self.segments if s.segment_type == "outro"), None)
    
    @property
    def main_segments(self) -> List[ScriptSegment]:
        """Get all main content segments"""
        return [s for s in self.segments if s.segment_type == "main"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "style": self.style.value,
            "source_article_id": self.source_article_id,
            "segments": [s.to_dict() for s in self.segments],
            "script_text": self.script_text,
            "tts_ready_text": self.tts_ready_text,
            "estimated_duration": self.estimated_duration,
            "word_count": self.word_count,
            "metadata": self.metadata,
            "custom_instructions": self.custom_instructions,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PodcastScript':
        """Create from dictionary"""
        segments = [ScriptSegment(**s) for s in data["segments"]]
        return cls(
            id=data["id"],
            title=data["title"],
            style=ScriptStyle(data["style"]),
            source_article_id=data["source_article_id"],
            segments=segments,
            script_text=data["script_text"],
            tts_ready_text=data["tts_ready_text"],
            estimated_duration=data["estimated_duration"],
            word_count=data["word_count"],
            metadata=data.get("metadata", {}),
            custom_instructions=data.get("custom_instructions"),
            created_at=datetime.fromisoformat(data["created_at"])
        )


@dataclass
class VoiceConfig:
    """Configuration for TTS voice"""
    name: str
    language: str
    gender: str  # male, female, neutral
    quality: QualityLevel
    provider: str  # google, openai, elevenlabs, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "language": self.language,
            "gender": self.gender,
            "quality": self.quality.value,
            "provider": self.provider,
            "parameters": self.parameters
        }


@dataclass
class AudioMetadata:
    """Metadata about generated audio"""
    duration: float  # in seconds
    format: AudioFormat
    sample_rate: int
    bitrate: int
    file_size: int  # in bytes
    voice_used: VoiceConfig
    processing_effects: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "duration": self.duration,
            "format": self.format.value,
            "sample_rate": self.sample_rate,
            "bitrate": self.bitrate,
            "file_size": self.file_size,
            "voice_used": self.voice_used.to_dict(),
            "processing_effects": self.processing_effects
        }


@dataclass
class PodcastEpisode:
    """Represents a complete podcast episode"""
    id: str
    title: str
    description: str
    script_id: str
    audio_file_path: str
    audio_metadata: AudioMetadata
    publish_date: datetime
    tags: List[str] = field(default_factory=list)
    show_notes: str = ""
    thumbnail_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "script_id": self.script_id,
            "audio_file_path": self.audio_file_path,
            "audio_metadata": self.audio_metadata.to_dict(),
            "publish_date": self.publish_date.isoformat(),
            "tags": self.tags,
            "show_notes": self.show_notes,
            "thumbnail_path": self.thumbnail_path,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PodcastEpisode':
        """Create from dictionary"""
        audio_metadata = AudioMetadata(**data["audio_metadata"])
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            script_id=data["script_id"],
            audio_file_path=data["audio_file_path"],
            audio_metadata=audio_metadata,
            publish_date=datetime.fromisoformat(data["publish_date"]),
            tags=data.get("tags", []),
            show_notes=data.get("show_notes", ""),
            thumbnail_path=data.get("thumbnail_path"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
        )


@dataclass
class ProcessingJob:
    """Represents a processing job in the pipeline"""
    id: str
    job_type: str  # fetch, script, audio, etc.
    status: str  # pending, processing, completed, failed
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "job_type": self.job_type,
            "status": self.status,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "progress": self.progress,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class PipelineConfig:
    """Configuration for the podcast generation pipeline"""
    # Content fetching
    content_sources: List[str] = field(default_factory=list)
    content_filters: Dict[str, Any] = field(default_factory=dict)
    
    # Script generation
    default_style: ScriptStyle = ScriptStyle.CONVERSATIONAL
    target_duration: int = 900  # 15 minutes
    enable_chapter_editing: bool = True
    
    # Audio generation
    default_voice: str = "en-US-Neural2-A"
    audio_format: AudioFormat = AudioFormat.MP3
    enable_post_processing: bool = True
    
    # Quality settings
    quality_level: QualityLevel = QualityLevel.HIGH
    enable_quality_checks: bool = True
    
    # Cache settings
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour
    
    # API settings
    api_rate_limits: Dict[str, int] = field(default_factory=dict)
    retry_attempts: int = 3
    timeout: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content_sources": self.content_sources,
            "content_filters": self.content_filters,
            "default_style": self.default_style.value,
            "target_duration": self.target_duration,
            "enable_chapter_editing": self.enable_chapter_editing,
            "default_voice": self.default_voice,
            "audio_format": self.audio_format.value,
            "enable_post_processing": self.enable_post_processing,
            "quality_level": self.quality_level.value,
            "enable_quality_checks": self.enable_quality_checks,
            "enable_caching": self.enable_caching,
            "cache_ttl": self.cache_ttl,
            "api_rate_limits": self.api_rate_limits,
            "retry_attempts": self.retry_attempts,
            "timeout": self.timeout
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PipelineConfig':
        """Create from dictionary"""
        return cls(
            content_sources=data.get("content_sources", []),
            content_filters=data.get("content_filters", {}),
            default_style=ScriptStyle(data.get("default_style", "conversational")),
            target_duration=data.get("target_duration", 900),
            enable_chapter_editing=data.get("enable_chapter_editing", True),
            default_voice=data.get("default_voice", "en-US-Neural2-A"),
            audio_format=AudioFormat(data.get("audio_format", "mp3")),
            enable_post_processing=data.get("enable_post_processing", True),
            quality_level=QualityLevel(data.get("quality_level", "high")),
            enable_quality_checks=data.get("enable_quality_checks", True),
            enable_caching=data.get("enable_caching", True),
            cache_ttl=data.get("cache_ttl", 3600),
            api_rate_limits=data.get("api_rate_limits", {}),
            retry_attempts=data.get("retry_attempts", 3),
            timeout=data.get("timeout", 30)
        )