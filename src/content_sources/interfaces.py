"""
Content Sources - Interface Definitions
Defines contracts for all content source operations
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..core.models import ProcessingResult


class ContentLength(Enum):
    """Content length options for articles"""
    SHORT = "short"      # ~5 minutes
    MEDIUM = "medium"    # ~10 minutes  
    LONG = "long"        # ~15 minutes
    FULL = "full"        # No limit


@dataclass
class ArticleMetadata:
    """Metadata for an article"""
    title: str
    url: str
    page_views: int
    last_modified: str
    categories: List[str]
    quality_score: float
    word_count: int
    estimated_duration: Tuple[int, str]  # (seconds, formatted)


@dataclass
class ArticleSuggestion:
    """Article suggestion with relevance scoring"""
    title: str
    snippet: str
    similarity_score: float
    page_views: int
    is_disambiguation: bool
    metadata: Optional[ArticleMetadata] = None


@dataclass
class Article:
    """Complete article data structure"""
    title: str
    url: str
    content: str
    summary: str
    categories: List[str]
    page_views: int
    last_modified: str
    references: List[str]
    images: List[str]
    word_count: int
    quality_score: float
    
    @property
    def metadata(self) -> ArticleMetadata:
        """Get article metadata"""
        return ArticleMetadata(
            title=self.title,
            url=self.url,
            page_views=self.page_views,
            last_modified=self.last_modified,
            categories=self.categories,
            quality_score=self.quality_score,
            word_count=self.word_count,
            estimated_duration=self._estimate_duration()
        )
    
    def _estimate_duration(self, wpm: int = 160) -> Tuple[int, str]:
        """Estimate reading duration"""
        duration_minutes = self.word_count / wpm
        duration_seconds = int(duration_minutes * 60)
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        formatted = f"{minutes}:{seconds:02d}"
        return duration_seconds, formatted


@dataclass
class SearchCriteria:
    """Criteria for content search and filtering"""
    query: str
    max_results: int = 10
    min_views: int = 1000
    exclude_categories: List[str] = None
    target_length: ContentLength = ContentLength.FULL
    include_references: bool = True
    quality_threshold: float = 0.3
    
    def __post_init__(self):
        if self.exclude_categories is None:
            self.exclude_categories = [
                'Disambiguation pages',
                'Redirects', 
                'Wikipedia',
                'Articles with dead external links'
            ]


@dataclass
class BatchFetchResult:
    """Result of batch fetching operation"""
    successful: List[Article]
    failed: List[Tuple[str, Exception]]
    total_requested: int
    success_rate: float
    processing_time: float
    
    def __post_init__(self):
        self.success_rate = len(self.successful) / max(self.total_requested, 1)


class ContentSource(ABC):
    """Base interface for content sources"""
    
    @abstractmethod
    async def fetch_article(self, title: str, criteria: SearchCriteria) -> ProcessingResult[Article]:
        """
        Fetch a single article by title
        
        Args:
            title: Article title or identifier
            criteria: Search and processing criteria
            
        Returns:
            ProcessingResult containing Article or error
        """
        pass
    
    @abstractmethod
    async def search_articles(self, criteria: SearchCriteria) -> ProcessingResult[List[Article]]:
        """
        Search for articles matching criteria
        
        Args:
            criteria: Search criteria
            
        Returns:
            ProcessingResult containing list of Articles
        """
        pass
    
    @abstractmethod
    async def get_suggestions(self, query: str, max_results: int = 10) -> ProcessingResult[List[ArticleSuggestion]]:
        """
        Get article suggestions for a query
        
        Args:
            query: Search query
            max_results: Maximum number of suggestions
            
        Returns:
            ProcessingResult containing list of suggestions
        """
        pass
    
    @abstractmethod
    def supports_source(self, identifier: str) -> bool:
        """
        Check if this source can handle the given identifier
        
        Args:
            identifier: Source identifier (URL, title, etc.)
            
        Returns:
            True if this source can handle the identifier
        """
        pass


class TrendingContentSource(ABC):
    """Interface for sources that can provide trending content"""
    
    @abstractmethod
    async def get_trending_articles(self, criteria: SearchCriteria) -> ProcessingResult[List[Article]]:
        """
        Get currently trending articles
        
        Args:
            criteria: Filtering criteria
            
        Returns:
            ProcessingResult containing trending articles
        """
        pass


class FeaturedContentSource(ABC):
    """Interface for sources that can provide featured/high-quality content"""
    
    @abstractmethod
    async def get_featured_articles(self, criteria: SearchCriteria) -> ProcessingResult[List[Article]]:
        """
        Get featured/high-quality articles
        
        Args:
            criteria: Filtering criteria
            
        Returns:
            ProcessingResult containing featured articles
        """
        pass


class CategoryContentSource(ABC):
    """Interface for sources that can provide content by category"""
    
    @abstractmethod
    async def get_articles_by_category(self, category: str, criteria: SearchCriteria) -> ProcessingResult[List[Article]]:
        """
        Get articles from a specific category
        
        Args:
            category: Category name
            criteria: Filtering criteria
            
        Returns:
            ProcessingResult containing articles from category
        """
        pass
    
    @abstractmethod
    async def get_available_categories(self) -> ProcessingResult[List[str]]:
        """
        Get list of available categories
        
        Returns:
            ProcessingResult containing category names
        """
        pass


class HistoricalContentSource(ABC):
    """Interface for sources that can provide historical content"""
    
    @abstractmethod
    async def get_on_this_day(self, date: Optional[datetime] = None, criteria: SearchCriteria = None) -> ProcessingResult[List[Article]]:
        """
        Get articles related to events on this day in history
        
        Args:
            date: Specific date (defaults to today)
            criteria: Filtering criteria
            
        Returns:
            ProcessingResult containing historical articles
        """
        pass


class ContentProcessor(ABC):
    """Interface for content processing operations"""
    
    @abstractmethod
    async def process_content(self, content: str, target_length: ContentLength) -> ProcessingResult[str]:
        """
        Process and potentially shorten content to target length
        
        Args:
            content: Original content
            target_length: Target content length
            
        Returns:
            ProcessingResult containing processed content
        """
        pass
    
    @abstractmethod
    def calculate_quality_score(self, article: Article) -> float:
        """
        Calculate quality score for an article
        
        Args:
            article: Article to score
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        pass
    
    @abstractmethod
    def estimate_duration(self, word_count: int, style: str = "conversational") -> Tuple[int, str]:
        """
        Estimate podcast duration based on word count and style
        
        Args:
            word_count: Number of words
            style: Speaking style
            
        Returns:
            Tuple of (duration_seconds, formatted_duration)
        """
        pass


class ContentValidator(ABC):
    """Interface for content validation"""
    
    @abstractmethod
    def validate_article(self, article: Article, criteria: SearchCriteria) -> ProcessingResult[Article]:
        """
        Validate article meets quality and content criteria
        
        Args:
            article: Article to validate
            criteria: Validation criteria
            
        Returns:
            ProcessingResult with validated article or validation errors
        """
        pass
    
    @abstractmethod
    def is_suitable_for_podcast(self, article: Article, criteria: SearchCriteria) -> bool:
        """
        Check if article is suitable for podcast generation
        
        Args:
            article: Article to check
            criteria: Suitability criteria
            
        Returns:
            True if suitable for podcast
        """
        pass


class SuggestionProvider(ABC):
    """Interface for article suggestion services"""
    
    @abstractmethod
    async def get_smart_suggestions(self, query: str, max_results: int = 10) -> ProcessingResult[List[ArticleSuggestion]]:
        """
        Get intelligent article suggestions using multiple strategies
        
        Args:
            query: Search query
            max_results: Maximum suggestions to return
            
        Returns:
            ProcessingResult containing ranked suggestions
        """
        pass
    
    @abstractmethod
    async def get_related_articles(self, article_title: str, max_results: int = 5) -> ProcessingResult[List[str]]:
        """
        Get articles related to the given article
        
        Args:
            article_title: Source article title
            max_results: Maximum related articles to return
            
        Returns:
            ProcessingResult containing related article titles
        """
        pass
    
    @abstractmethod
    def calculate_similarity(self, query: str, title: str) -> float:
        """
        Calculate similarity score between query and title
        
        Args:
            query: Search query
            title: Article title
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        pass


class ContentCache(ABC):
    """Interface for content caching operations"""
    
    @abstractmethod
    async def get_cached_article(self, key: str) -> Optional[Article]:
        """
        Get article from cache
        
        Args:
            key: Cache key (usually article title)
            
        Returns:
            Cached article or None if not found/expired
        """
        pass
    
    @abstractmethod
    async def cache_article(self, key: str, article: Article, ttl_hours: int = 24) -> bool:
        """
        Cache an article
        
        Args:
            key: Cache key
            article: Article to cache
            ttl_hours: Time to live in hours
            
        Returns:
            True if cached successfully
        """
        pass
    
    @abstractmethod
    async def cache_batch(self, articles: List[Article], prefix: str = "") -> int:
        """
        Cache multiple articles
        
        Args:
            articles: Articles to cache
            prefix: Optional prefix for cache keys
            
        Returns:
            Number of articles successfully cached
        """
        pass
    
    @abstractmethod
    async def get_cache_stats(self) -> Dict[str, Union[int, float]]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        pass
    
    @abstractmethod
    async def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear cached articles
        
        Args:
            older_than_days: Only clear items older than this many days
            
        Returns:
            Number of items cleared
        """
        pass


class InteractiveSelector(ABC):
    """Interface for interactive article selection"""
    
    @abstractmethod
    async def select_from_suggestions(self, query: str, suggestions: List[ArticleSuggestion]) -> Optional[str]:
        """
        Allow user to interactively select from suggestions
        
        Args:
            query: Original search query
            suggestions: List of article suggestions
            
        Returns:
            Selected article title or None if cancelled
        """
        pass
    
    @abstractmethod
    def display_suggestions(self, query: str, suggestions: List[ArticleSuggestion]) -> None:
        """
        Display suggestions to user
        
        Args:
            query: Original search query
            suggestions: List of suggestions to display
        """
        pass