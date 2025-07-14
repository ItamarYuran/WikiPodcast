"""
Content Source Manager
Main orchestrator for all content source operations with caching and validation
"""

import asyncio
from typing import List, Dict, Optional, Tuple, Union
from datetime import datetime

from ..core.models import ProcessingResult
from .interfaces import (
    ContentSource, Article, ArticleSuggestion, SearchCriteria, 
    ContentLength, BatchFetchResult
)
from .wikipedia_source import WikipediaContentSource
from .content_processors import (
    WikipediaContentProcessor, WikipediaContentValidator, 
    FileBasedContentCache, ConsoleInteractiveSelector,
    create_content_processor, create_content_validator, 
    create_file_cache, create_console_selector
)
from ..utils.async_utils import AsyncBatch


class ContentSourceManager:
    """
    Main manager for all content source operations
    Provides unified interface with caching, validation, and smart suggestions
    """
    
    def __init__(
        self,
        wikipedia_source: Optional[WikipediaContentSource] = None,
        content_processor: Optional[WikipediaContentProcessor] = None,
        content_validator: Optional[WikipediaContentValidator] = None,
        content_cache: Optional[FileBasedContentCache] = None,
        interactive_selector: Optional[ConsoleInteractiveSelector] = None
    ):
        """
        Initialize content source manager
        
        Args:
            wikipedia_source: Wikipedia content source
            content_processor: Content processor
            content_validator: Content validator  
            content_cache: Content cache
            interactive_selector: Interactive selector for user choices
        """
        # Initialize components with defaults if not provided
        self.wikipedia_source = wikipedia_source or WikipediaContentSource()
        self.content_processor = content_processor or create_content_processor()
        self.content_validator = content_validator or create_content_validator(self.content_processor)
        self.content_cache = content_cache or create_file_cache()
        self.interactive_selector = interactive_selector or create_console_selector()
        
        # Statistics tracking
        self._stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'api_calls': 0,
            'validation_failures': 0,
            'total_articles_fetched': 0
        }
    
    async def fetch_article(
        self, 
        title: str, 
        criteria: Optional[SearchCriteria] = None,
        use_cache: bool = True,
        interactive: bool = True
    ) -> ProcessingResult[Article]:
        """
        Fetch a single article with smart search, caching, and validation
        
        Args:
            title: Article title or query
            criteria: Search criteria (uses defaults if None)
            use_cache: Whether to use caching
            interactive: Whether to show suggestions on failure
            
        Returns:
            ProcessingResult containing Article
        """
        if criteria is None:
            criteria = SearchCriteria(query=title)
        
        try:
            # Check cache first
            cached_article = None
            if use_cache:
                cached_article = await self.content_cache.get_cached_article(title)
                if cached_article:
                    self._stats['cache_hits'] += 1
                    
                    # Validate cached article
                    validation_result = self.content_validator.validate_article(cached_article, criteria)
                    if validation_result.success:
                        return ProcessingResult.success(cached_article, metadata={'source': 'cache'})
                    else:
                        # Cached article no longer meets criteria, fetch fresh
                        pass
                else:
                    self._stats['cache_misses'] += 1
            
            # Fetch from Wikipedia
            self._stats['api_calls'] += 1
            fetch_result = await self.wikipedia_source.fetch_article(title, criteria)
            
            if fetch_result.success:
                article = fetch_result.data
                
                # Validate article
                validation_result = self.content_validator.validate_article(article, criteria)
                if not validation_result.success:
                    self._stats['validation_failures'] += 1
                    return ProcessingResult.failure(
                        f"Article validation failed: {validation_result.error}",
                        error_code="VALIDATION_FAILED",
                        metadata=validation_result.metadata
                    )
                
                # Cache the validated article
                if use_cache:
                    await self.content_cache.cache_article(title, article)
                
                self._stats['total_articles_fetched'] += 1
                return ProcessingResult.success(
                    article, 
                    metadata={'source': 'wikipedia', 'warnings': validation_result.metadata.get('warnings', [])}
                )
            
            # If direct fetch failed, try suggestions
            if interactive and fetch_result.error_code == "ARTICLE_NOT_FOUND":
                suggestions_result = await self.wikipedia_source.get_smart_suggestions(title, max_results=10)
                
                if suggestions_result.success and suggestions_result.data:
                    selected_title = await self.interactive_selector.select_from_suggestions(
                        title, suggestions_result.data
                    )
                    
                    if selected_title:
                        # Recursively fetch the selected article (without interactive to avoid loops)
                        return await self.fetch_article(selected_title, criteria, use_cache, interactive=False)
            
            return fetch_result
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error in content source manager: {str(e)}",
                error_code="MANAGER_ERROR",
                exception=e
            )
    
    async def fetch_multiple_articles(
        self,
        titles: List[str],
        criteria: Optional[SearchCriteria] = None,
        use_cache: bool = True,
        max_concurrent: int = 5
    ) -> BatchFetchResult:
        """
        Fetch multiple articles concurrently
        
        Args:
            titles: List of article titles
            criteria: Search criteria
            use_cache: Whether to use caching
            max_concurrent: Maximum concurrent fetches
            
        Returns:
            BatchFetchResult with successful and failed articles
        """
        if criteria is None:
            criteria = SearchCriteria(query="", max_results=len(titles))
        
        start_time = asyncio.get_event_loop().time()
        
        # Create batch processor
        batch_processor = AsyncBatch(
            batch_size=max_concurrent,
            max_concurrent=max_concurrent,
            rate_limit=2.0  # Respect Wikipedia rate limits
        )
        
        async def fetch_single(title):
            result = await self.fetch_article(title, criteria, use_cache, interactive=False)
            if result.success:
                return result.data
            else:
                raise Exception(result.error)
        
        # Process batch
        batch_result = await batch_processor.process_batch(titles, fetch_single)
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        return BatchFetchResult(
            successful=batch_result.successful,
            failed=batch_result.failed,
            total_requested=len(titles),
            success_rate=batch_result.success_rate,
            processing_time=processing_time
        )
    
    async def get_trending_articles(
        self,
        count: int = 20,
        criteria: Optional[SearchCriteria] = None,
        use_cache: bool = True
    ) -> ProcessingResult[List[Article]]:
        """
        Get trending Wikipedia articles
        
        Args:
            count: Number of articles to return
            criteria: Filtering criteria
            use_cache: Whether to use caching
            
        Returns:
            ProcessingResult containing trending articles
        """
        if criteria is None:
            criteria = SearchCriteria(query="trending", max_results=count)
        else:
            criteria.max_results = count
        
        try:
            # Try to get from cache first (trending data cached for shorter time)
            cache_key = f"trending_{count}_{criteria.min_views}"
            cached_articles = None
            
            if use_cache:
                # For trending, we could implement a shorter cache TTL
                # but for now use the standard cache
                pass
            
            # Fetch fresh trending articles
            trending_result = await self.wikipedia_source.get_trending_articles(criteria)
            
            if not trending_result.success:
                return trending_result
            
            articles = trending_result.data
            
            # Validate all articles
            validated_articles = []
            for article in articles:
                validation_result = self.content_validator.validate_article(article, criteria)
                if validation_result.success:
                    validated_articles.append(article)
                else:
                    self._stats['validation_failures'] += 1
            
            # Cache the validated articles
            if use_cache and validated_articles:
                await self.content_cache.cache_batch(validated_articles, prefix="trending_")
            
            self._stats['total_articles_fetched'] += len(validated_articles)
            
            return ProcessingResult.success(validated_articles)
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error fetching trending articles: {str(e)}",
                error_code="TRENDING_ERROR",
                exception=e
            )
    
    async def get_featured_articles(
        self,
        count: int = 10,
        criteria: Optional[SearchCriteria] = None,
        use_cache: bool = True
    ) -> ProcessingResult[List[Article]]:
        """
        Get featured Wikipedia articles
        
        Args:
            count: Number of articles to return
            criteria: Filtering criteria
            use_cache: Whether to use caching
            
        Returns:
            ProcessingResult containing featured articles
        """
        if criteria is None:
            criteria = SearchCriteria(query="featured", max_results=count)
        else:
            criteria.max_results = count
        
        try:
            # Fetch featured articles
            featured_result = await self.wikipedia_source.get_featured_articles(criteria)
            
            if not featured_result.success:
                return featured_result
            
            articles = featured_result.data
            
            # Featured articles should generally be high quality, but still validate
            validated_articles = []
            for article in articles:
                validation_result = self.content_validator.validate_article(article, criteria)
                if validation_result.success:
                    validated_articles.append(article)
                else:
                    self._stats['validation_failures'] += 1
            
            # Cache the validated articles
            if use_cache and validated_articles:
                await self.content_cache.cache_batch(validated_articles, prefix="featured_")
            
            self._stats['total_articles_fetched'] += len(validated_articles)
            
            return ProcessingResult.success(validated_articles)
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error fetching featured articles: {str(e)}",
                error_code="FEATURED_ERROR",
                exception=e
            )
    
    async def search_articles(
        self,
        query: str,
        criteria: Optional[SearchCriteria] = None,
        use_cache: bool = True
    ) -> ProcessingResult[List[Article]]:
        """
        Search for articles matching a query
        
        Args:
            query: Search query
            criteria: Search criteria
            use_cache: Whether to use caching
            
        Returns:
            ProcessingResult containing matching articles
        """
        if criteria is None:
            criteria = SearchCriteria(query=query)
        else:
            criteria.query = query
        
        try:
            # Search using Wikipedia source
            search_result = await self.wikipedia_source.search_articles(criteria)
            
            if not search_result.success:
                return search_result
            
            articles = search_result.data
            
            # Validate search results
            validated_articles = []
            for article in articles:
                validation_result = self.content_validator.validate_article(article, criteria)
                if validation_result.success:
                    validated_articles.append(article)
                    
                    # Cache individual articles
                    if use_cache:
                        await self.content_cache.cache_article(article.title, article)
                else:
                    self._stats['validation_failures'] += 1
            
            self._stats['total_articles_fetched'] += len(validated_articles)
            
            return ProcessingResult.success(validated_articles)
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error searching articles: {str(e)}",
                error_code="SEARCH_ERROR",
                exception=e
            )
    
    async def get_suggestions(
        self,
        query: str,
        max_results: int = 10,
        interactive: bool = False
    ) -> ProcessingResult[Union[List[ArticleSuggestion], str]]:
        """
        Get article suggestions for a query
        
        Args:
            query: Search query
            max_results: Maximum suggestions to return
            interactive: Whether to show interactive selection
            
        Returns:
            ProcessingResult containing suggestions or selected title
        """
        try:
            suggestions_result = await self.wikipedia_source.get_smart_suggestions(query, max_results)
            
            if not suggestions_result.success:
                return suggestions_result
            
            suggestions = suggestions_result.data
            
            if not suggestions:
                return ProcessingResult.success([])
            
            # If interactive mode, let user select
            if interactive:
                selected_title = await self.interactive_selector.select_from_suggestions(query, suggestions)
                return ProcessingResult.success(selected_title)
            
            return ProcessingResult.success(suggestions)
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error getting suggestions: {str(e)}",
                error_code="SUGGESTIONS_ERROR",
                exception=e
            )
    
    async def get_cache_stats(self) -> Dict[str, Union[int, float]]:
        """Get comprehensive cache and usage statistics"""
        cache_stats = await self.content_cache.get_cache_stats()
        
        # Add manager stats
        cache_stats.update(self._stats)
        
        # Calculate hit rate
        total_requests = self._stats['cache_hits'] + self._stats['cache_misses']
        cache_stats['cache_hit_rate'] = (
            self._stats['cache_hits'] / total_requests 
            if total_requests > 0 else 0.0
        )
        
        return cache_stats
    
    async def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        """Clear content cache"""
        return await self.content_cache.clear_cache(older_than_days)
    
    def reset_stats(self) -> None:
        """Reset usage statistics"""
        self._stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'api_calls': 0,
            'validation_failures': 0,
            'total_articles_fetched': 0
        }
    
    # Convenience methods that match the original API
    
    async def smart_fetch_article(
        self,
        query: str,
        interactive: bool = True,
        max_suggestions: int = 10,
        include_references: bool = True,
        force_refresh: bool = False,
        target_length: str = "full"
    ) -> Optional[Article]:
        """
        Smart article fetcher with backward compatibility
        
        Args:
            query: Search query/title
            interactive: Whether to prompt user for selection
            max_suggestions: Maximum number of suggestions to show
            include_references: Whether to fetch reference links
            force_refresh: Force re-fetch even if cached
            target_length: Content length ("short", "medium", "long", "full")
            
        Returns:
            Article object or None if not found/cancelled
        """
        # Convert target_length to enum
        length_mapping = {
            "short": ContentLength.SHORT,
            "medium": ContentLength.MEDIUM,
            "long": ContentLength.LONG,
            "full": ContentLength.FULL
        }
        
        criteria = SearchCriteria(
            query=query,
            max_results=max_suggestions,
            include_references=include_references,
            target_length=length_mapping.get(target_length, ContentLength.FULL)
        )
        
        result = await self.fetch_article(
            query, 
            criteria, 
            use_cache=not force_refresh, 
            interactive=interactive
        )
        
        return result.data if result.success else None
    
    async def get_on_this_day(
        self, 
        date: Optional[datetime] = None,
        count: int = 10
    ) -> ProcessingResult[List[Article]]:
        """
        Get articles related to events on this day in history
        
        Args:
            date: Specific date (defaults to today)
            count: Number of articles to return
            
        Returns:
            ProcessingResult containing historical articles
        """
        criteria = SearchCriteria(query="on_this_day", max_results=count)
        
        try:
            result = await self.wikipedia_source.get_on_this_day(date, criteria)
            
            if not result.success:
                return result
            
            # Validate articles
            validated_articles = []
            for article in result.data:
                validation_result = self.content_validator.validate_article(article, criteria)
                if validation_result.success:
                    validated_articles.append(article)
            
            return ProcessingResult.success(validated_articles)
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error fetching 'on this day' articles: {str(e)}",
                error_code="HISTORICAL_ERROR",
                exception=e
            )


# Convenience factory function
def create_content_source_manager(
    cache_dir: Optional[str] = None,
    language: str = 'en'
) -> ContentSourceManager:
    """
    Create a fully configured content source manager
    
    Args:
        cache_dir: Cache directory path
        language: Wikipedia language code
        
    Returns:
        Configured ContentSourceManager
    """
    wikipedia_source = WikipediaContentSource(language=language)
    content_processor = create_content_processor()
    content_validator = create_content_validator(content_processor)
    content_cache = create_file_cache(cache_dir)
    interactive_selector = create_console_selector()
    
    return ContentSourceManager(
        wikipedia_source=wikipedia_source,
        content_processor=content_processor,
        content_validator=content_validator,
        content_cache=content_cache,
        interactive_selector=interactive_selector
    )