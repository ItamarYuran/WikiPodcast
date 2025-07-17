"""
Backward Compatibility Layer
Maintains compatibility with existing WikipediaContentFetcher API
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import json

from content_sources.manager import ContentSourceManager, create_content_source_manager
from content_sources.interfaces import SearchCriteria, ContentLength
from core.models import Article

@dataclass
class WikipediaArticle:
    """Original article structure for backward compatibility"""
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
    
    @classmethod
    def from_article(cls, article: Article) -> 'WikipediaArticle':
        """Convert new Article to legacy WikipediaArticle"""
        return cls(
            title=article.title,
            url=article.url,
            content=article.content,
            summary=article.summary,
            categories=article.categories,
            page_views=article.page_views,
            last_modified=article.last_modified,
            references=article.references,
            images=article.images,
            word_count=article.word_count,
            quality_score=article.quality_score
        )


@dataclass
class ArticleSuggestion:
    """Original suggestion structure for backward compatibility"""
    title: str
    snippet: str
    similarity_score: float
    page_views: int
    is_disambiguation: bool


class WikipediaContentFetcher:
    """
    Backward compatibility wrapper for the original WikipediaContentFetcher
    Delegates to the new modular content source system while maintaining the original API
    """
    
    def __init__(self, language='en', user_agent='WikipediaPodcastBot/1.0', cache_dir='../raw_articles'):
        """
        Initialize content fetcher with original API
        
        Args:
            language: Wikipedia language code
            user_agent: User agent string (maintained for compatibility but not used)
            cache_dir: Cache directory path
        """
        self.language = language
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize the new modular system
        self._manager = create_content_source_manager(
            cache_dir=str(self.cache_dir),
            language=language
        )
        
        # Legacy attributes for compatibility
        self.base_url = f'https://{language}.wikipedia.org/api/rest_v1'
        self.api_url = f'https://{language}.wikipedia.org/w/api.php'
        self.headers = {
            'User-Agent': user_agent,
            'Accept': 'application/json'
        }
        
        # In-memory cache for current session (maintained for compatibility)
        self.memory_cache = {}
        self.trending_cache = {}
        self.trending_cache_expiry = None
    
    def smart_fetch_article(self, 
                           query: str, 
                           interactive: bool = True,
                           max_suggestions: int = 10,
                           include_references: bool = True, 
                           force_refresh: bool = False,
                           target_length: str = "full") -> Optional[WikipediaArticle]:
        """
        Smart article fetcher that provides suggestions when exact match fails
        
        Args:
            query: Search query/title
            interactive: Whether to prompt user for selection
            max_suggestions: Maximum number of suggestions to show
            include_references: Whether to fetch reference links
            force_refresh: Force re-fetch even if cached
            target_length: Content length ("short", "medium", "long", "full")
            
        Returns:
            WikipediaArticle object or None if not found/cancelled
        """
        try:
            article = asyncio.run(self._manager.smart_fetch_article(
                query=query,
                interactive=interactive,
                max_suggestions=max_suggestions,
                include_references=include_references,
                force_refresh=force_refresh,
                target_length=target_length
            ))
            
            return WikipediaArticle.from_article(article) if article else None
            
        except Exception as e:
            print(f"❌ Error in smart_fetch_article: {e}")
            return None
    
    def fetch_article(self, 
                     title: str, 
                     include_references: bool = True, 
                     force_refresh: bool = False,
                     target_length: str = "full",
                     interactive: bool = True) -> Optional[WikipediaArticle]:
        """
        Fetch a specific Wikipedia article by title with smart fallback
        
        Args:
            title: Wikipedia article title
            include_references: Whether to fetch reference links
            force_refresh: Force re-fetch even if cached
            target_length: Content length ("short", "medium", "long", "full")
            interactive: Whether to show suggestions if article fails to fetch
            
        Returns:
            WikipediaArticle object or None if not found
        """
        try:
            # Convert target_length to enum
            length_mapping = {
                "short": ContentLength.SHORT,
                "medium": ContentLength.MEDIUM,
                "long": ContentLength.LONG,
                "full": ContentLength.FULL
            }
            
            criteria = SearchCriteria(
                query=title,
                include_references=include_references,
                target_length=length_mapping.get(target_length, ContentLength.FULL)
            )
            
            result = asyncio.run(self._manager.fetch_article(
                title=title,
                criteria=criteria,
                use_cache=not force_refresh,
                interactive=interactive
            ))
            
            if result.success:
                return WikipediaArticle.from_article(result.data)
            else:
                print(f"❌ Failed to fetch article: {result.error}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching article '{title}': {e}")
            return None
    
    def get_trending_articles(self, 
                            count: int = 20, 
                            min_views: int = 1000,
                            exclude_categories: List[str] = None,
                            save_batch: bool = True) -> List[WikipediaArticle]:
        """
        Get trending Wikipedia articles based on recent page views
        
        Args:
            count: Number of articles to return
            min_views: Minimum page views to consider
            exclude_categories: Categories to exclude
            save_batch: Whether to save the trending batch to file (maintained for compatibility)
            
        Returns:
            List of trending WikipediaArticle objects
        """
        try:
            if exclude_categories is None:
                exclude_categories = [
                    'Disambiguation pages',
                    'Redirects',
                    'Wikipedia',
                    'Articles with dead external links'
                ]
            
            criteria = SearchCriteria(
                query="trending",
                max_results=count,
                min_views=min_views,
                exclude_categories=exclude_categories
            )
            
            result = asyncio.run(self._manager.get_trending_articles(count, criteria))
            
            if result.success:
                return [WikipediaArticle.from_article(article) for article in result.data]
            else:
                print(f"❌ Failed to get trending articles: {result.error}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching trending articles: {e}")
            return []
    
    def get_featured_articles(self, count: int = 10, save_batch: bool = True) -> List[WikipediaArticle]:
        """
        Get Wikipedia's featured articles (highest quality content)
        
        Args:
            count: Number of articles to return
            save_batch: Whether to save the featured batch to file (maintained for compatibility)
        
        Returns:
            List of featured WikipediaArticle objects
        """
        try:
            criteria = SearchCriteria(query="featured", max_results=count)
            result = asyncio.run(self._manager.get_featured_articles(count, criteria))
            
            if result.success:
                return [WikipediaArticle.from_article(article) for article in result.data]
            else:
                print(f"❌ Failed to get featured articles: {result.error}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching featured articles: {e}")
            return []
    
    def get_articles_by_category(self, category: str, count: int = 10) -> List[WikipediaArticle]:
        """
        Get articles from a specific Wikipedia category
        
        Args:
            category: Category name
            count: Number of articles to return
            
        Returns:
            List of WikipediaArticle objects from the category
        """
        try:
            criteria = SearchCriteria(query=category, max_results=count)
            result = asyncio.run(self._manager.wikipedia_source.get_articles_by_category(category, criteria))
            
            if result.success:
                # Validate the articles
                validated_articles = []
                for article in result.data:
                    validation_result = self._manager.content_validator.validate_article(article, criteria)
                    if validation_result.success:
                        validated_articles.append(WikipediaArticle.from_article(article))
                
                return validated_articles
            else:
                print(f"❌ Failed to get articles from category '{category}': {result.error}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching articles from category '{category}': {e}")
            return []
    
    def search_articles(self, query: str, count: int = 10) -> List[WikipediaArticle]:
        """
        Search for Wikipedia articles matching a query
        
        Args:
            query: Search query
            count: Number of results to return
            
        Returns:
            List of matching WikipediaArticle objects
        """
        try:
            criteria = SearchCriteria(query=query, max_results=count)
            result = asyncio.run(self._manager.search_articles(query, criteria))
            
            if result.success:
                return [WikipediaArticle.from_article(article) for article in result.data]
            else:
                print(f"❌ Failed to search articles: {result.error}")
                return []
                
        except Exception as e:
            print(f"❌ Error searching articles for '{query}': {e}")
            return []
    
    def get_on_this_day(self, date: Optional[datetime] = None) -> List[WikipediaArticle]:
        """
        Get articles related to events that happened on this day in history
        
        Args:
            date: Specific date to check (defaults to today)
            
        Returns:
            List of historical event WikipediaArticle objects
        """
        try:
            result = asyncio.run(self._manager.get_on_this_day(date))
            
            if result.success:
                return [WikipediaArticle.from_article(article) for article in result.data]
            else:
                print(f"❌ Failed to get 'on this day' articles: {result.error}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching 'on this day' articles: {e}")
            return []
    
    def get_smart_suggestions(self, query: str, max_results: int = 10) -> List[ArticleSuggestion]:
        """
        Get smart article suggestions using multiple strategies
        
        Args:
            query: Search query
            max_results: Maximum number of suggestions
            
        Returns:
            List of ArticleSuggestion objects, sorted by relevance
        """
        try:
            result = asyncio.run(self._manager.get_suggestions(query, max_results))
            
            if result.success and isinstance(result.data, list):
                # Convert new suggestions to legacy format
                legacy_suggestions = []
                for suggestion in result.data:
                    legacy_suggestions.append(ArticleSuggestion(
                        title=suggestion.title,
                        snippet=suggestion.snippet,
                        similarity_score=suggestion.similarity_score,
                        page_views=suggestion.page_views,
                        is_disambiguation=suggestion.is_disambiguation
                    ))
                return legacy_suggestions
            else:
                return []
                
        except Exception as e:
            print(f"❌ Error getting suggestions: {e}")
            return []
    
    def suggest_titles(self, partial_title: str, count: int = 5) -> List[str]:
        """
        Suggest Wikipedia article titles based on partial input
        
        Args:
            partial_title: Partial or approximate title
            count: Number of suggestions to return
            
        Returns:
            List of suggested titles
        """
        suggestions = self.get_smart_suggestions(partial_title, count)
        return [suggestion.title for suggestion in suggestions]
    
    def find_exact_title(self, approximate_title: str) -> Optional[str]:
        """
        Find the exact Wikipedia title for an approximate search
        
        Args:
            approximate_title: The title you're looking for
            
        Returns:
            Exact Wikipedia title if found, None otherwise
        """
        article = self.fetch_article(approximate_title, interactive=False)
        return article.title if article else None
    

    def load_cached_article(self, filename: str) -> Optional[WikipediaArticle]:
        """Load a cached article from JSON file"""
        try:
            file_path = self.cache_dir / filename
            
            if not file_path.exists():
                print(f"❌ Cached article not found: {filename}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Remove timestamp if present
            data.pop('cached_timestamp', None)
            
            # Handle missing fields gracefully (old vs new cache format)
            defaults = {
                'page_views': 0,
                'last_modified': '',
                'references': [],
                'images': [],
                'word_count': 0,
                'quality_score': 0.0
            }
            
            for key, default_value in defaults.items():
                if key not in data:
                    data[key] = default_value
            
            # Ensure word_count is calculated if missing or zero
            if data['word_count'] == 0 and data.get('content'):
                data['word_count'] = len(data['content'].split())
            
            return WikipediaArticle(**data)
            
        except Exception as e:
            print(f"❌ Error loading cached article {filename}: {e}")
            return None
    
    def clear_cache(self, older_than_days: int = None):
        """Clear cached articles, optionally only those older than specified days"""
        try:
            deleted_count = asyncio.run(self._manager.clear_cache(older_than_days))
            print(f"Deleted {deleted_count} cached articles")
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about the cache"""
        try:
            stats = asyncio.run(self._manager.get_cache_stats())
            
            # Convert to legacy format
            return {
                'total_articles': int(stats.get('total_articles', 0)),
                'trending_batches': int(stats.get('trending_batches', 0)),
                'featured_batches': int(stats.get('featured_batches', 0)),
                'total_size_mb': int(stats.get('total_size_mb', 0))
            }
            
        except Exception:
            return {
                'total_articles': 0,
                'trending_batches': 0,
                'featured_batches': 0,
                'total_size_mb': 0
            }
    
    def estimate_podcast_duration(self, word_count: int, style: str = "conversational") -> Tuple[int, str]:
        """
        Estimate podcast duration based on word count and style
        
        Args:
            word_count: Number of words in content
            style: Podcast style (affects speaking rate)
            
        Returns:
            Tuple of (duration_seconds, formatted_duration)
        """
        return self._manager.content_processor.estimate_duration(word_count, style)
    
    def batch_suggestion_mode(self, queries: List[str]) -> Dict[str, Optional[str]]:
        """
        Process multiple queries and return best matches
        Useful for batch processing without user interaction
        """
        results = {}
        
        for query in queries:
            try:
                suggestions = self.get_smart_suggestions(query, 5)
                
                if suggestions:
                    best_match = suggestions[0]
                    if best_match.similarity_score > 0.7 and not best_match.is_disambiguation:
                        results[query] = best_match.title
                    else:
                        results[query] = None
                else:
                    results[query] = None
                    
            except Exception:
                results[query] = None
        
        return results
    
    def suggest_related_articles(self, title: str, count: int = 5) -> List[str]:
        """
        Suggest related articles based on categories and links
        """
        try:
            result = asyncio.run(self._manager.wikipedia_source.get_related_articles(title, count))
            return result.data if result.success else []
        except Exception:
            return []


# Convenience function for backward compatibility
def example_usage():
    """Example of how to use the Enhanced WikipediaContentFetcher"""
    fetcher = WikipediaContentFetcher(cache_dir='raw_articles')
    
    print("=== Enhanced Wikipedia Podcast Content Fetcher ===")
    print(f"Cache directory: {fetcher.cache_dir}")
    
    # Show cache stats
    stats = fetcher.get_cache_stats()
    print(f"Cache stats: {stats['total_articles']} articles, {stats['total_size_mb']} MB")
    
    # Test smart fetch
    article = fetcher.smart_fetch_article("frank zappa", interactive=False, target_length="medium")
    
    if article:
        print(f"✅ Success: {article.title}")
        print(f"📊 Word count: {article.word_count}")
        print(f"⭐ Quality score: {article.quality_score:.2f}")
        
        # Show estimated duration
        duration_sec, duration_str = fetcher.estimate_podcast_duration(article.word_count, "conversational")
        print(f"🎙️ Estimated podcast duration: {duration_str}")
    else:
        print("❌ Could not find article")


if __name__ == "__main__":
    example_usage()