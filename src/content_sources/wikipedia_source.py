"""
Pure Wikipedia Content Source - NO legacy dependencies
Eliminates all duplication by implementing Wikipedia API calls directly.
"""

import requests
import json
import time
from typing import List, Optional
from pathlib import Path
from datetime import datetime
import re

from .interfaces import ContentSource
from core.models import Article, ContentMetadata, ContentType


class WikipediaContentSource(ContentSource):
    """
    Pure Wikipedia implementation - zero legacy dependencies
    """
    
    def __init__(self):
        self.base_url = 'https://en.wikipedia.org/api/rest_v1'
        self.api_url = 'https://en.wikipedia.org/w/api.php'
        self.headers = {
            'User-Agent': 'WikipediaPodcastBot/1.0',
            'Accept': 'application/json'
        }
        
        # Use the same cache directory for consistency
        self.cache_dir = Path('raw_articles')
        self.cache_dir.mkdir(exist_ok=True)
        
        print("✅ WikipediaContentSource (pure implementation - no legacy)")
    
    def fetch_article(self, identifier: str) -> Optional[Article]:
        """Fetch article using direct Wikipedia API calls - no legacy dependency"""
        
        print(f"Fetching article: {identifier}")
        
        # Check cache first
        cached = self._get_from_cache(identifier)
        if cached:
            print(f"✓ Cached: {identifier} ({cached.word_count} words)")
            return cached
        
        try:
            # Get article content using Wikipedia API
            page_url = f"{self.api_url}?action=query&format=json&titles={identifier}&prop=extracts|pageimages|categories|info&exintro=&explaintext=&exsectionformat=plain&piprop=original&inprop=url"
            
            response = requests.get(page_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get('query', {}).get('pages', {})
            if not pages:
                print(f"❌ No data found for {identifier}")
                return None
            
            page_data = list(pages.values())[0]
            
            if 'missing' in page_data:
                print(f"❌ Article not found: {identifier}")
                return None
            
            title = page_data.get('title', identifier)
            content = page_data.get('extract', '')
            url = page_data.get('fullurl', f"https://en.wikipedia.org/wiki/{identifier}")
            
            # Extract summary (first paragraph)
            summary = content.split('\n')[0] if content else ''
            if len(summary) > 500:
                summary = summary[:500] + '...'
            
            # Get categories
            categories = []
            for cat in page_data.get('categories', []):
                cat_title = cat.get('title', '').replace('Category:', '')
                if cat_title:
                    categories.append(cat_title)
            
            # Create metadata
            metadata = ContentMetadata(
                source="wikipedia",
                language="en",
                categories=categories[:10],  # Limit categories
                quality_score=self._calculate_quality_score(content, categories),
                page_views=1000,  # Default value
                last_modified=datetime.now().isoformat(),
                references=[],
                images=[]
            )
            
            # Create Article
            article = Article(
                id=identifier,
                title=title,
                content=content,
                summary=summary,
                url=url,
                content_type=ContentType.WIKIPEDIA_ARTICLE,
                metadata=metadata
            )
            
            # Set compatibility attributes for interactive menu
            article.word_count = len(content.split()) if content else 0
            article.quality_score = metadata.quality_score
            article.page_views = metadata.page_views
            article.last_modified = metadata.last_modified
            article.categories = metadata.categories
            article.references = metadata.references
            article.images = metadata.images
            
            # Cache the result
            self._save_to_cache(identifier, article)
            
            print(f"✓ Fetched: {title} ({article.word_count} words)")
            return article
            
        except Exception as e:
            print(f"❌ Error fetching {identifier}: {e}")
            return None
    
    def search_articles(self, query: str) -> List[Article]:
        """Search Wikipedia articles"""
        try:
            search_url = f"{self.api_url}?action=query&list=search&srsearch={query}&format=json&srlimit=5"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for result in data.get('query', {}).get('search', []):
                article = self.fetch_article(result['title'])
                if article:
                    articles.append(article)
            
            return articles
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def _calculate_quality_score(self, content: str, categories: list) -> float:
        """Calculate article quality score"""
        score = 0.5  # Base score
        
        # Content length factor
        word_count = len(content.split()) if content else 0
        if word_count > 1000:
            score += 0.3
        elif word_count > 500:
            score += 0.2
        elif word_count > 200:
            score += 0.1
        
        # Categories factor (indicates well-organized article)
        if len(categories) > 5:
            score += 0.2
        elif len(categories) > 2:
            score += 0.1
        
        return min(1.0, score)
    
    def _get_from_cache(self, identifier: str) -> Optional[Article]:
        """Get article from cache"""
        # Use same cache format as legacy system for compatibility
        cache_file = self.cache_dir / f"{identifier.replace('/', '_').replace(' ', '_')}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle both new and legacy cache formats
                if 'metadata' in data:
                    # New format
                    metadata = ContentMetadata(
                        source=data['metadata'].get('source', 'wikipedia'),
                        language=data['metadata'].get('language', 'en'),
                        categories=data['metadata'].get('categories', []),
                        quality_score=data['metadata'].get('quality_score', 0.0),
                        page_views=data['metadata'].get('page_views', 0),
                        last_modified=data['metadata'].get('last_modified', ''),
                        references=data['metadata'].get('references', []),
                        images=data['metadata'].get('images', [])
                    )
                else:
                    # Legacy format compatibility
                    metadata = ContentMetadata(
                        source="wikipedia",
                        language="en",
                        categories=data.get('categories', []),
                        quality_score=data.get('quality_score', 0.0),
                        page_views=data.get('page_views', 0),
                        last_modified=data.get('last_modified', ''),
                        references=data.get('references', []),
                        images=data.get('images', [])
                    )
                
                article = Article(
                    id=data.get('id', identifier),
                    title=data.get('title', identifier),
                    content=data.get('content', ''),
                    summary=data.get('summary', ''),
                    url=data.get('url', ''),
                    content_type=ContentType.WIKIPEDIA_ARTICLE,
                    metadata=metadata
                )
                
                # Set compatibility attributes
                article.word_count = data.get('word_count', 0)
                article.quality_score = data.get('quality_score', 0.0)
                article.page_views = data.get('page_views', 0)
                article.last_modified = data.get('last_modified', '')
                article.categories = data.get('categories', [])
                article.references = data.get('references', [])
                article.images = data.get('images', [])
                
                return article
                
            except Exception as e:
                print(f"⚠️ Cache read error for {identifier}: {e}")
                return None
        
        return None
    
    def _save_to_cache(self, identifier: str, article: Article):
        """Save article to cache using same format as legacy system"""
        try:
            cache_file = self.cache_dir / f"{identifier.replace('/', '_').replace(' ', '_')}.json"
            
            # Use format compatible with legacy system and interactive menu
            data = {
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'summary': article.summary,
                'url': article.url,
                'word_count': article.word_count,
                'quality_score': article.quality_score,
                'page_views': article.page_views,
                'last_modified': article.last_modified,
                'categories': article.categories,
                'references': article.references,
                'images': article.images,
                'cached_timestamp': time.time(),
                'metadata': {
                    'source': article.metadata.source,
                    'language': article.metadata.language,
                    'categories': article.metadata.categories,
                    'quality_score': article.metadata.quality_score,
                    'page_views': article.metadata.page_views,
                    'last_modified': article.metadata.last_modified,
                    'references': article.metadata.references,
                    'images': article.metadata.images
                }
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ Cache write error for {identifier}: {e}")
    
    def list_cached_articles(self):
        """List all cached articles - compatible with interactive menu"""
        cached = []
        
        for file_path in self.cache_dir.glob('*.json'):
            if not file_path.name.startswith(('trending_', 'featured_', 'stats_')):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    cached.append({
                        'title': data.get('title', file_path.stem.replace('_', ' ')),
                        'filename': file_path.name,
                        'word_count': data.get('word_count', 0),
                        'cached_date': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                    })
                    
                except Exception:
                    # Fallback for corrupted files
                    cached.append({
                        'title': file_path.stem.replace('_', ' '),
                        'filename': file_path.name,
                        'word_count': 0,
                        'cached_date': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                    })
        
        return cached
    
    def load_cached_article(self, filename: str):
        """Load specific cached article by filename - for interactive menu compatibility"""
        identifier = filename.replace('.json', '').replace('_', ' ')
        return self._get_from_cache(identifier)
    
    def get_trending_articles(self, count: int = 5):
        """Get trending articles - simplified implementation"""
        trending_topics = ['Python', 'Artificial_intelligence', 'Climate_change', 'Space_exploration', 'Quantum_computing']
        articles = []
        
        for topic in trending_topics[:count]:
            article = self.fetch_article(topic)
            if article:
                articles.append(article)
        
        return articles
    
    def get_featured_articles(self, count: int = 5):
        """Get featured articles - simplified implementation"""
        featured_topics = ['Albert_Einstein', 'Leonardo_da_Vinci', 'Marie_Curie', 'Isaac_Newton', 'Charles_Darwin']
        articles = []
        
        for topic in featured_topics[:count]:
            article = self.fetch_article(topic)
            if article:
                articles.append(article)
        
        return articles

    def get_cache_stats(self):
        """Get cache statistics for pipeline status"""
        try:
            cache_files = list(self.cache_dir.glob('*.json'))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                'total_articles': len([f for f in cache_files if not f.name.startswith(('trending_', 'featured_', 'stats_'))]),
                'trending_batches': len([f for f in cache_files if f.name.startswith('trending_')]),
                'featured_batches': len([f for f in cache_files if f.name.startswith('featured_')]),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'cache_dir': str(self.cache_dir)
            }
            
        except Exception as e:
            return {
                'total_articles': 0,
                'trending_batches': 0, 
                'featured_batches': 0,
                'total_size_mb': 0.0,
                'error': str(e)
            }
