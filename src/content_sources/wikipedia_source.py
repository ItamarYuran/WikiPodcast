"""
Wikipedia Content Source
"""
import requests
from typing import List, Optional
import sys
from pathlib import Path

# Add src to path to import legacy components
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

from .interfaces import ContentSource, Article

class WikipediaContentSource(ContentSource):
    """
    A content source for fetching articles from Wikipedia.
    Now delegates to the working legacy WikipediaContentFetcher.
    """
    
    def __init__(self, api_url: str = "https://en.wikipedia.org/api/rest_v1/page/summary/"):
        """
        Initializes the WikipediaContentSource.
        
        Args:
            api_url (str): The URL of the Wikipedia API.
        """
        self.api_url = api_url
        
        # Initialize the working legacy fetcher
        try:
            from content_fetcher import WikipediaContentFetcher
            self.fetcher = WikipediaContentFetcher(cache_dir='raw_articles')
            print("✅ WikipediaContentSource using legacy fetcher")
        except ImportError as e:
            print(f"⚠️  Could not import legacy fetcher: {e}")
            self.fetcher = None
    
    def fetch_article(self, identifier: str) -> Optional[Article]:
        """
        Fetches a single article from Wikipedia.
        Delegates to the working legacy fetcher.
        """
        if self.fetcher:
            # Use legacy fetcher
            legacy_article = self.fetcher.fetch_article(identifier)
            if legacy_article:
                # Convert to new Article format
                return Article(
                    title=legacy_article.title,
                    content=legacy_article.content,
                    url=legacy_article.url,
                    source="wikipedia"
                )
        
        # Fallback to original simple implementation
        try:
            response = requests.get(f"{self.api_url}{identifier}")
            response.raise_for_status()
            data = response.json()
            return Article(
                title=data.get("title", ""),
                content=data.get("extract", ""),
                url=data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                source="wikipedia"
            )
        except requests.RequestException:
            return None
    
    def search_articles(self, query: str) -> List[Article]:
        """
        Searches for articles on Wikipedia.
        Delegates to the working legacy fetcher.
        """
        if self.fetcher:
            # Use legacy fetcher
            legacy_article = self.fetcher.fetch_article(query)
            if legacy_article:
                return [Article(
                    title=legacy_article.title,
                    content=legacy_article.content,
                    url=legacy_article.url,
                    source="wikipedia"
                )]
        
        # Fallback to original simple implementation
        article = self.fetch_article(query)
        return [article] if article else []
    
    def get_cache_stats(self):
        """Get cache statistics from the legacy fetcher"""
        if hasattr(self, 'fetcher') and self.fetcher and hasattr(self.fetcher, 'get_cache_stats'):
            return self.fetcher.get_cache_stats()
        return {
            'total_articles': 0,
            'trending_batches': 0,
            'featured_batches': 0,
            'total_size_mb': 0.0
        }
    
    def list_cached_articles(self):
        """List cached articles from the legacy fetcher"""
        if hasattr(self, 'fetcher') and self.fetcher and hasattr(self.fetcher, 'list_cached_articles'):
            return self.fetcher.list_cached_articles()
        return []
    
    def load_cached_article(self, filename: str):
        """Load cached article from the legacy fetcher"""
        if hasattr(self, 'fetcher') and self.fetcher and hasattr(self.fetcher, 'load_cached_article'):
            return self.fetcher.load_cached_article(filename)
        return None
    
    def get_trending_articles(self, count: int = 5):
        """Get trending articles from the legacy fetcher"""
        if hasattr(self, 'fetcher') and self.fetcher and hasattr(self.fetcher, 'get_trending_articles'):
            return self.fetcher.get_trending_articles(count)
        return []
    
    def get_featured_articles(self, count: int = 3):
        """Get featured articles from the legacy fetcher"""
        if hasattr(self, 'fetcher') and self.fetcher and hasattr(self.fetcher, 'get_featured_articles'):
            return self.fetcher.get_featured_articles(count)
        return []