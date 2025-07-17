"""
Wikipedia Content Source
"""
import requests
from typing import List, Optional
import sys
from pathlib import Path
import json
from datetime import datetime
from pathlib import Path
from .interfaces import ContentSource
from core.models import Article

# Add src to path to import legacy components
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

from .interfaces import ContentSource
from core.models import Article

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
        Fetches a single article from Wikipedia with complete metadata.
        Delegates to the working legacy fetcher and preserves all metadata.
        """
        if self.fetcher:
            # Use legacy fetcher to get rich article data
            legacy_article = self.fetcher.fetch_article(identifier)
            if legacy_article:
                # Create ContentMetadata with all the rich data from legacy article
                from core.models import ContentMetadata, ContentType
                
                metadata = ContentMetadata(
                    source="wikipedia",
                    language="en",
                    categories=getattr(legacy_article, 'categories', []),
                    quality_score=getattr(legacy_article, 'quality_score', 0.0),
                    page_views=getattr(legacy_article, 'page_views', 0),
                    last_modified=getattr(legacy_article, 'last_modified', None),
                    references=getattr(legacy_article, 'references', []),
                    images=getattr(legacy_article, 'images', [])
                )
                
                # Create Article object with complete metadata (NO id parameter)
                article = Article(
                    id=legacy_article.title.replace(' ', '_'),
                    title=legacy_article.title,
                    content=legacy_article.content,
                    summary=getattr(legacy_article, 'summary', ''),
                    url=getattr(legacy_article, 'url', ''),
                    content_type=ContentType.WIKIPEDIA_ARTICLE,
                    metadata=metadata
                )
                
                # Set metadata as direct attributes for interactive menu compatibility
                article.word_count = getattr(legacy_article, 'word_count', len(legacy_article.content.split()))
                article.quality_score = getattr(legacy_article, 'quality_score', 0.0)
                article.page_views = getattr(legacy_article, 'page_views', 0)
                article.references = getattr(legacy_article, 'references', [])
                article.images = getattr(legacy_article, 'images', [])
                article.last_modified = getattr(legacy_article, 'last_modified', '')
                article.categories = getattr(legacy_article, 'categories', [])
                
                return article
        
        # Fallback to original simple implementation (without rich metadata)
        try:
            import requests
            response = requests.get(f"{self.api_url}{identifier}")
            response.raise_for_status()
            data = response.json()
            
            # Create basic article without rich metadata (NO id parameter)
            article = Article(
                id=data.get("title", "unknown").replace(' ', '_'),
                title=data.get("title", ""),
                content=data.get("extract", ""),
                url=data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                content_type=ContentType.WIKIPEDIA_ARTICLE,
                metadata=ContentMetadata(source="wikipedia", language="en")
            )
            
            # Set basic attributes
            article.word_count = len(article.content.split()) if article.content else 0
            article.quality_score = 0.0  # No quality data from simple API
            article.page_views = 0  # No view data from simple API
            article.references = []
            article.images = []
            article.last_modified = ''
            article.categories = []
            
            return article
            
        except Exception as e:
            print(f"❌ Fallback fetch failed: {e}")
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
        """
        List all cached articles with complete metadata for the interactive menu.
        This is the authoritative implementation that replaces all others.
        """
        try:
            cached = []
            
            # Use the legacy fetcher's cache directory for consistency
            if hasattr(self, 'fetcher') and self.fetcher and hasattr(self.fetcher, 'cache_dir'):
                cache_dir = self.fetcher.cache_dir
            else:
                # Fallback to common cache directories
                from pathlib import Path
                possible_dirs = [Path('raw_articles'), Path('../raw_articles')]
                cache_dir = None
                for dir_path in possible_dirs:
                    if dir_path.exists():
                        cache_dir = dir_path
                        break
                
                if not cache_dir:
                    return []
            
            # Look for JSON files in the cache directory
            for file_path in cache_dir.glob('*.json'):
                # Skip system files and temporary files
                if file_path.name.startswith(('trending_', 'featured_', 'stats_', 'temp_', '.')):
                    continue
                    
                try:
                    # Load the file to get metadata
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Extract and enhance metadata
                    title = data.get('title', file_path.stem.replace('_', ' '))
                    word_count = data.get('word_count', 0)
                    
                    # Calculate word count if missing
                    if word_count == 0 and data.get('content'):
                        word_count = len(data.get('content', '').split())
                    
                    # Get cached date from file modification time
                    cached_date = datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                    
                    # Create complete metadata record
                    article_metadata = {
                        'title': title,
                        'filename': file_path.name,
                        'word_count': word_count,
                        'quality_score': data.get('quality_score', 0.0),
                        'page_views': data.get('page_views', 'Not available'),
                        'cached_date': cached_date,
                        'last_modified': data.get('last_modified', cached_date),
                        'references': data.get('references', []),
                        'images': data.get('images', []),
                        'url': data.get('url', ''),
                        'summary': data.get('summary', '')
                    }
                    
                    cached.append(article_metadata)
                    
                except json.JSONDecodeError as e:
                    # Handle corrupted JSON files
                    print(f"⚠️ Corrupted JSON file {file_path.name}: {e}")
                    cached.append({
                        'title': f"Corrupted: {file_path.stem.replace('_', ' ')}",
                        'filename': file_path.name,
                        'word_count': 0,
                        'quality_score': 0.0,
                        'page_views': 'Not available',
                        'cached_date': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                        'last_modified': '',
                        'references': [],
                        'images': [],
                        'url': '',
                        'summary': 'File corrupted'
                    })
                    
                except Exception as e:
                    # Handle other file reading errors
                    print(f"⚠️ Could not read {file_path.name}: {e}")
                    cached.append({
                        'title': file_path.stem.replace('_', ' '),
                        'filename': file_path.name,
                        'word_count': 0,
                        'quality_score': 0.0,
                        'page_views': 'Not available',
                        'cached_date': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                        'last_modified': '',
                        'references': [],
                        'images': [],
                        'url': '',
                        'summary': 'Read error'
                    })
            
            # Sort by cached date (newest first)
            return sorted(cached, key=lambda x: x['cached_date'], reverse=True)
            
        except Exception as e:
            print(f"❌ Error listing cached articles: {e}")
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