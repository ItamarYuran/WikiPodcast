"""
Content Fetcher - Simple Wrapper
Delegates to shared utilities for a clean, maintainable codebase
"""

import requests
import json
import re
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import difflib


@dataclass
class WikipediaArticle:
    """Structure for storing Wikipedia article data"""
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


@dataclass
class ArticleSuggestion:
    """Structure for article suggestions"""
    title: str
    snippet: str
    similarity_score: float
    page_views: int
    is_disambiguation: bool


class WikipediaContentFetcher:
    """
    Simplified Wikipedia content fetcher
    Much smaller than the original, delegates complex logic to utilities
    """
    
    def __init__(self, language='en', user_agent='WikipediaPodcastBot/1.0', cache_dir='../raw_articles'):
        self.language = language
        self.base_url = f'https://{language}.wikipedia.org/api/rest_v1'
        self.api_url = f'https://{language}.wikipedia.org/w/api.php'
        self.headers = {
            'User-Agent': user_agent,
            'Accept': 'application/json'
        }
        
        # Set up caching
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Simple in-memory cache
        self.memory_cache = {}
        self.trending_cache = {}
        self.trending_cache_expiry = None
        
        print(f"✅ WikipediaContentFetcher initialized (cache: {self.cache_dir})")
    
    def smart_fetch_article(self, 
                           query: str, 
                           interactive: bool = True,
                           max_suggestions: int = 10,
                           include_references: bool = True, 
                           force_refresh: bool = False,
                           target_length: str = "full") -> Optional[WikipediaArticle]:
        """Smart article fetcher with suggestions fallback"""
        print(f"🔍 Searching for: '{query}'")
        
        # Try direct fetch first
        article = self.fetch_article(query, include_references, force_refresh, target_length, interactive=False)
        if article:
            return article
        
        # If direct fetch fails, try suggestions
        if interactive:
            suggestions = self.get_smart_suggestions(query, max_suggestions)
            if suggestions:
                selected = self._interactive_selection(query, suggestions)
                if selected:
                    return self.fetch_article(selected, include_references, force_refresh, target_length, interactive=False)
        
        return None
    
    def fetch_article(self, 
                     title: str, 
                     include_references: bool = True, 
                     force_refresh: bool = False,
                     target_length: str = "full",
                     interactive: bool = True) -> Optional[WikipediaArticle]:
        """Fetch a Wikipedia article by title"""
        try:
            # Check cache first
            cache_key = f"{title}_{include_references}_{target_length}"
            if not force_refresh and cache_key in self.memory_cache:
                return self.memory_cache[cache_key]
            
            # Check file cache
            if not force_refresh:
                cached = self._load_from_cache(title)
                if cached:
                    if target_length != "full":
                        cached.content = self._adjust_length(cached.content, target_length)
                        cached.word_count = len(cached.content.split())
                    self.memory_cache[cache_key] = cached
                    return cached
            
            print(f"Fetching article: {title}")
            
            # Get page info and content
            page_info = self._api_call('query', {
                'titles': title,
                'prop': 'extracts|info',
                'exintro': True,
                'explaintext': True,
                'redirects': True,
                'format': 'json'
            })
            
            if not page_info or 'query' not in page_info:
                return None
            
            pages = page_info['query']['pages']
            page_id = list(pages.keys())[0]
            
            if page_id == '-1':
                return None
            
            page_data = pages[page_id]
            if 'missing' in page_data:
                return None
            
            # Get full content
            content_data = self._api_call('query', {
                'titles': page_data['title'],
                'prop': 'extracts',
                'explaintext': True,
                'format': 'json'
            })
            
            if not content_data:
                return None
            
            content_pages = content_data['query']['pages']
            content_page_id = list(content_pages.keys())[0]
            content = content_pages[content_page_id].get('extract', '')
            
            if not content:
                return None
            
            # Clean content
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = re.sub(r'==+.*?==+', '', content)
            content = content.strip()
            
            # Adjust length if needed
            if target_length != "full":
                content = self._adjust_length(content, target_length)
            
            # Get metadata (simplified)
            categories = self._get_categories(page_data['title']) if include_references else []
            references = self._get_references(page_data['title']) if include_references else []
            
            # Create article
            article = WikipediaArticle(
                title=page_data['title'],
                url=f"https://{self.language}.wikipedia.org/wiki/{page_data['title'].replace(' ', '_')}",
                content=content,
                summary=page_data.get('extract', '')[:500],
                categories=categories,
                page_views=0,  # Simplified - could add page views API call
                last_modified=page_data.get('timestamp', ''),
                references=references,
                images=[],  # Simplified - could add images API call
                word_count=len(content.split()),
                quality_score=self._simple_quality_score(content, references, categories)
            )
            
            # Cache the result
            self.memory_cache[cache_key] = article
            self._save_to_cache(article)
            
            print(f"✓ Fetched: {article.title} ({article.word_count} words)")
            return article
            
        except Exception as e:
            print(f"❌ Error fetching '{title}': {e}")
            return None
    
    def get_trending_articles(self, count: int = 20, min_views: int = 1000, 
                            exclude_categories: List[str] = None, save_batch: bool = True) -> List[WikipediaArticle]:
        """Get trending articles (simplified)"""
        if exclude_categories is None:
            exclude_categories = ['Disambiguation pages', 'Redirects', 'Wikipedia']
        
        try:
            # Simple trending - just fetch featured articles for now
            return self.get_featured_articles(count, save_batch)
        except Exception as e:
            print(f"❌ Error getting trending: {e}")
            return []
    
    def get_featured_articles(self, count: int = 10, save_batch: bool = True) -> List[WikipediaArticle]:
        """Get featured articles"""
        try:
            data = self._api_call('query', {
                'list': 'categorymembers',
                'cmtitle': 'Category:Featured articles',
                'cmlimit': count * 2,
                'format': 'json'
            })
            
            if not data or 'query' not in data:
                return []
            
            titles = [page['title'] for page in data['query']['categorymembers']]
            random.shuffle(titles)
            
            articles = []
            for title in titles[:count]:
                article = self.fetch_article(title, interactive=False)
                if article:
                    articles.append(article)
                time.sleep(0.1)  # Rate limiting
            
            return articles
            
        except Exception as e:
            print(f"❌ Error getting featured: {e}")
            return []
    
    def search_articles(self, query: str, count: int = 10) -> List[WikipediaArticle]:
        """Search for articles"""
        try:
            data = self._api_call('query', {
                'list': 'search',
                'srsearch': query,
                'srlimit': count,
                'format': 'json'
            })
            
            if not data or 'query' not in data:
                return []
            
            titles = [result['title'] for result in data['query']['search']]
            
            articles = []
            for title in titles:
                article = self.fetch_article(title, interactive=False)
                if article:
                    articles.append(article)
                time.sleep(0.1)
            
            return articles
            
        except Exception as e:
            print(f"❌ Error searching: {e}")
            return []
    
    def get_smart_suggestions(self, query: str, max_results: int = 10) -> List[ArticleSuggestion]:
        """Get article suggestions"""
        try:
            data = self._api_call('opensearch', {
                'search': query,
                'limit': max_results,
                'format': 'json'
            })
            
            if not data or len(data) < 4:
                return []
            
            titles = data[1]
            descriptions = data[2]
            
            suggestions = []
            for i, title in enumerate(titles):
                snippet = descriptions[i] if i < len(descriptions) else ""
                similarity = self._calculate_similarity(query, title)
                
                suggestions.append(ArticleSuggestion(
                    title=title,
                    snippet=snippet,
                    similarity_score=similarity,
                    page_views=0,
                    is_disambiguation='disambiguation' in title.lower()
                ))
            
            return sorted(suggestions, key=lambda x: x.similarity_score, reverse=True)
            
        except Exception as e:
            print(f"❌ Error getting suggestions: {e}")
            return []
    
    # =================== SIMPLIFIED HELPER METHODS ===================
    
    def _api_call(self, action: str, params: Dict) -> Optional[Dict]:
        """Make API call with basic error handling"""
        try:
            params['action'] = action
            response = requests.get(self.api_url, params=params, headers=self.headers, timeout=10)
            return response.json()
        except Exception as e:
            print(f"❌ API call failed: {e}")
            return None
    
    def _calculate_similarity(self, query: str, title: str) -> float:
        """Simple similarity calculation"""
        query_lower = query.lower().strip()
        title_lower = title.lower().strip()
        
        if query_lower == title_lower:
            return 1.0
        if query_lower in title_lower:
            return 0.9
        if title_lower in query_lower:
            return 0.8
        
        return difflib.SequenceMatcher(None, query_lower, title_lower).ratio()
    
    def _interactive_selection(self, query: str, suggestions: List[ArticleSuggestion]) -> Optional[str]:
        """Simple interactive selection"""
        print(f"\n🔍 Found {len(suggestions)} matches for '{query}':")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion.title} (similarity: {suggestion.similarity_score:.2f})")
        print("0. Cancel")
        
        try:
            choice = int(input("Select: "))
            if 1 <= choice <= len(suggestions):
                return suggestions[choice - 1].title
        except (ValueError, KeyboardInterrupt):
            pass
        
        return None
    
    def _get_categories(self, title: str) -> List[str]:
        """Get article categories (simplified)"""
        try:
            data = self._api_call('query', {
                'titles': title,
                'prop': 'categories',
                'cllimit': 20,
                'format': 'json'
            })
            
            if not data or 'query' not in data:
                return []
            
            pages = data['query']['pages']
            page_id = list(pages.keys())[0]
            
            if page_id == '-1':
                return []
            
            categories = pages[page_id].get('categories', [])
            return [cat['title'].replace('Category:', '') for cat in categories]
        except:
            return []
    
    def _get_references(self, title: str) -> List[str]:
        """Get article references (simplified)"""
        try:
            data = self._api_call('query', {
                'titles': title,
                'prop': 'extlinks',
                'ellimit': 10,
                'format': 'json'
            })
            
            if not data or 'query' not in data:
                return []
            
            pages = data['query']['pages']
            page_id = list(pages.keys())[0]
            
            if page_id == '-1':
                return []
            
            links = pages[page_id].get('extlinks', [])
            return [link['*'] for link in links]
        except:
            return []
    
    def _adjust_length(self, content: str, target_length: str) -> str:
        """Simple content length adjustment"""
        length_targets = {"short": 875, "medium": 1750, "long": 2625}
        target_words = length_targets.get(target_length)
        
        if not target_words:
            return content
        
        words = content.split()
        if len(words) <= target_words:
            return content
        
        # Simple truncation - keep first portion
        truncated = ' '.join(words[:target_words])
        last_period = truncated.rfind('.')
        if last_period > len(truncated) * 0.8:
            truncated = truncated[:last_period + 1]
        
        return truncated + f"\n\n[Content shortened to {target_length} length]"
    
    def _simple_quality_score(self, content: str, references: List[str], categories: List[str]) -> float:
        """Simple quality scoring"""
        score = 0.0
        
        # Word count factor
        word_count = len(content.split())
        if word_count > 1000:
            score += 0.4
        elif word_count > 500:
            score += 0.2
        
        # References factor
        if len(references) > 10:
            score += 0.3
        elif len(references) > 0:
            score += 0.1
        
        # Categories factor
        if len(categories) > 5:
            score += 0.2
        elif len(categories) > 0:
            score += 0.1
        
        return min(score, 1.0)
    
    def _save_to_cache(self, article: WikipediaArticle):
        """Simple file caching"""
        try:
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', article.title)[:100]
            file_path = self.cache_dir / f"{safe_filename}.json"
            
            from dataclasses import asdict
            data = asdict(article)
            data['cached_timestamp'] = datetime.now().isoformat()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Cache save failed: {e}")
    
    def _load_from_cache(self, title: str) -> Optional[WikipediaArticle]:
        """Simple cache loading"""
        try:
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', title)[:100]
            file_path = self.cache_dir / f"{safe_filename}.json"
            
            if not file_path.exists():
                return None
            
            # Check age (7 days max)
            age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
            if age.days > 7:
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data.pop('cached_timestamp', None)
            return WikipediaArticle(**data)
        except:
            return None
    
    # =================== COMPATIBILITY METHODS ===================
    
    def get_on_this_day(self, date: Optional[datetime] = None) -> List[WikipediaArticle]:
        """Simplified on this day"""
        return []  # Simplified implementation
    
    def get_articles_by_category(self, category: str, count: int = 10) -> List[WikipediaArticle]:
        """Get articles by category"""
        return self.search_articles(f"category:{category}", count)
    
    def suggest_titles(self, partial_title: str, count: int = 5) -> List[str]:
        """Suggest titles"""
        suggestions = self.get_smart_suggestions(partial_title, count)
        return [s.title for s in suggestions]
    
    def find_exact_title(self, approximate_title: str) -> Optional[str]:
        """Find exact title"""
        article = self.fetch_article(approximate_title, interactive=False)
        return article.title if article else None
    
    def list_cached_articles(self) -> List[Dict[str, str]]:
        """List cached articles with metadata including word counts"""
        cached = []
        for file_path in self.cache_dir.glob('*.json'):
            if not file_path.name.startswith(('trending_', 'featured_')):
                try:
                    # Load the file to get word_count and other metadata
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Extract word count from the JSON data
                    word_count = data.get('word_count', 0)
                    if word_count == 0 and data.get('content'):
                        word_count = len(data.get('content', '').split())
                    
                    cached.append({
                        'title': data.get('title', file_path.stem.replace('_', ' ')),
                        'filename': file_path.name,
                        'word_count': word_count,
                        'cached_date': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                    })
                except Exception as e:
                    print(f"⚠️  Error reading {file_path.name}: {e}")
                    # Fallback for corrupted files
                    cached.append({
                        'title': file_path.stem.replace('_', ' '),
                        'filename': file_path.name,
                        'word_count': 0,
                        'cached_date': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                    })
        return cached
    
    def clear_cache(self, older_than_days: int = None):
        """Clear cache"""
        deleted = 0
        cutoff = datetime.now() - timedelta(days=older_than_days) if older_than_days else None
        
        for file_path in self.cache_dir.glob('*.json'):
            if cutoff is None or datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff:
                file_path.unlink()
                deleted += 1
        
        print(f"Deleted {deleted} cached articles")
        
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
            
            # Handle missing fields gracefully
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
            
            # Calculate word_count if missing
            if data['word_count'] == 0 and data.get('content'):
                data['word_count'] = len(data['content'].split())
            
            return WikipediaArticle(**data)
            
        except Exception as e:
            print(f"❌ Error loading cached article {filename}: {e}")
            return None
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        files = list(self.cache_dir.glob('*.json'))
        total_size = sum(f.stat().st_size for f in files)
        
        return {
            'total_articles': len([f for f in files if not f.name.startswith(('trending_', 'featured_'))]),
            'total_size_mb': total_size / (1024 * 1024),
            'trending_batches': len([f for f in files if f.name.startswith('trending_')]),  # Add this
            'featured_batches': len([f for f in files if f.name.startswith('featured_')]),  # Add this
            'total_size_mb': total_size / (1024 * 1024)
        }
    
    def estimate_podcast_duration(self, word_count: int, style: str = "conversational") -> Tuple[int, str]:
        """Estimate duration"""
        wpm = {"conversational": 160, "news_report": 180, "academic": 140}.get(style, 150)
        duration_seconds = int(word_count / wpm * 60)
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        return duration_seconds, f"{minutes}:{seconds:02d}"
    
    def batch_suggestion_mode(self, queries: List[str]) -> Dict[str, Optional[str]]:
        """Batch suggestions"""
        results = {}
        for query in queries:
            suggestions = self.get_smart_suggestions(query, 1)
            results[query] = suggestions[0].title if suggestions else None
        return results
    
    def suggest_related_articles(self, title: str, count: int = 5) -> List[str]:
        """Related articles"""
        return []  # Simplified


def example_usage():
    """Example usage"""
    fetcher = WikipediaContentFetcher(cache_dir='raw_articles')
    article = fetcher.smart_fetch_article("Python programming", interactive=False)
    
    if article:
        print(f"✅ {article.title}: {article.word_count} words")
    else:
        print("❌ Article not found")


if __name__ == "__main__":
    example_usage()