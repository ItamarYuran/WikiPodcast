import requests
import json
import re
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import time
import random
from pathlib import Path


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


class WikipediaContentFetcher:
    """
    Advanced Wikipedia content fetcher with trending discovery capabilities
    """
    
    def __init__(self, language='en', user_agent='WikipediaPodcastBot/1.0', cache_dir='../raw_articles'):
        self.language = language
        self.base_url = f'https://{language}.wikipedia.org/api/rest_v1'
        self.api_url = f'https://{language}.wikipedia.org/w/api.php'
        self.headers = {
            'User-Agent': user_agent,
            'Accept': 'application/json'
        }
        
        # Set up file caching
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for organization
        (self.cache_dir / 'articles').mkdir(exist_ok=True)
        (self.cache_dir / 'trending').mkdir(exist_ok=True)
        (self.cache_dir / 'featured').mkdir(exist_ok=True)
        (self.cache_dir / 'metadata').mkdir(exist_ok=True)
        
        # In-memory cache for current session
        self.memory_cache = {}
        self.trending_cache = {}
        self.trending_cache_expiry = None
    
    def fetch_article(self, title: str, include_references: bool = True, force_refresh: bool = False) -> Optional[WikipediaArticle]:
        """
        Fetch a specific Wikipedia article by title
        
        Args:
            title: Wikipedia article title
            include_references: Whether to fetch reference links
            force_refresh: Force re-fetch even if cached
            
        Returns:
            WikipediaArticle object or None if not found
        """
        try:
            # Clean title for URL and filename
            clean_title = title.replace(' ', '_')
            safe_filename = self._make_safe_filename(title)
            
            # Check file cache first (unless force refresh)
            if not force_refresh:
                cached_article = self._load_from_file_cache(safe_filename)
                if cached_article:
                    return cached_article
            
            # Check memory cache
            cache_key = f"{clean_title}_{include_references}"
            if not force_refresh and cache_key in self.memory_cache:
                return self.memory_cache[cache_key]
            
            print(f"Fetching article: {title}")
            
            # First try the exact title
            page_info = self._get_page_info(clean_title)
            content = None
            
            # If not found, try with search to find the correct title
            if not page_info:
                print(f"Exact match not found, searching for: {title}")
                search_results = self.search_articles(title, count=1)
                if search_results:
                    print(f"Found similar article: {search_results[0].title}")
                    return search_results[0]  # Return the first search result
                else:
                    print(f"No articles found matching: {title}")
                    return None
            
            content = self._get_page_content(clean_title)
            if not content:
                return None
            
            # Get additional metadata
            page_views = self._get_page_views(clean_title)
            categories = self._get_categories(clean_title)
            references = self._get_references(clean_title) if include_references else []
            images = self._get_images(clean_title)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(content, references, categories)
            
            article = WikipediaArticle(
                title=page_info['title'],
                url=f"https://{self.language}.wikipedia.org/wiki/{clean_title}",
                content=content,
                summary=page_info.get('extract', ''),
                categories=categories,
                page_views=page_views,
                last_modified=page_info.get('timestamp', ''),
                references=references,
                images=images,
                word_count=len(content.split()),
                quality_score=quality_score
            )
            
            # Cache the result in both memory and file
            self.memory_cache[cache_key] = article
            self._save_to_file_cache(article, safe_filename)
            
            print(f"✓ Cached article: {title} ({article.word_count} words, quality: {article.quality_score:.2f})")
            
            return article
            
        except Exception as e:
            print(f"Error fetching article '{title}': {str(e)}")
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
            exclude_categories: Categories to exclude (e.g., ['Disambiguation pages'])
            save_batch: Whether to save the trending batch to file
            
        Returns:
            List of trending WikipediaArticle objects
        """
        if exclude_categories is None:
            exclude_categories = [
                'Disambiguation pages',
                'Redirects',
                'Wikipedia',
                'Articles with dead external links'
            ]
        
        # Check cache first (trending data expires after 1 hour)
        if (self.trending_cache_expiry and 
            datetime.now() < self.trending_cache_expiry and 
            'trending' in self.trending_cache):
            cached_articles = self.trending_cache['trending']
            return self._filter_and_limit_articles(cached_articles, count, min_views, exclude_categories)
        
        try:
            print("Fetching trending articles...")
            trending_titles = self._get_most_viewed_pages()
            articles = []
            
            for i, title in enumerate(trending_titles[:count * 2], 1):  # Fetch extra to account for filtering
                print(f"Processing trending article {i}/{min(count*2, len(trending_titles))}: {title}")
                article = self.fetch_article(title)
                if article and self._is_suitable_for_podcast(article, min_views, exclude_categories):
                    articles.append(article)
                
                # Rate limiting
                time.sleep(0.1)
                
                if len(articles) >= count:
                    break
            
            # Cache the results
            self.trending_cache['trending'] = articles
            self.trending_cache_expiry = datetime.now() + timedelta(hours=1)
            
            # Save trending batch if requested
            if save_batch and articles:
                self._save_trending_batch(articles)
            
            print(f"✓ Found {len(articles)} trending articles")
            return articles
            
        except Exception as e:
            print(f"Error fetching trending articles: {str(e)}")
            return []
    
    def get_featured_articles(self, count: int = 10, save_batch: bool = True) -> List[WikipediaArticle]:
        """
        Get Wikipedia's featured articles (highest quality content)
        
        Args:
            count: Number of articles to return
            save_batch: Whether to save the featured batch to file
        
        Returns:
            List of featured WikipediaArticle objects
        """
        try:
            print("Fetching featured articles...")
            # Get featured articles from Wikipedia's featured content
            response = requests.get(
                self.api_url,
                params={
                    'action': 'query',
                    'list': 'categorymembers',
                    'cmtitle': 'Category:Featured articles',
                    'cmlimit': count * 2,
                    'format': 'json'
                },
                headers=self.headers
            )
            
            data = response.json()
            featured_titles = [page['title'] for page in data['query']['categorymembers']]
            
            # Randomize to get variety
            random.shuffle(featured_titles)
            
            articles = []
            for i, title in enumerate(featured_titles[:count], 1):
                print(f"Processing featured article {i}/{count}: {title}")
                article = self.fetch_article(title)
                if article:
                    articles.append(article)
                time.sleep(0.1)
            
            # Save featured batch if requested
            if save_batch and articles:
                self._save_featured_batch(articles)
            
            print(f"✓ Found {len(articles)} featured articles")
            return articles
            
        except Exception as e:
            print(f"Error fetching featured articles: {str(e)}")
            return []
    
    def get_articles_by_category(self, category: str, count: int = 10) -> List[WikipediaArticle]:
        """
        Get articles from a specific Wikipedia category
        
        Args:
            category: Category name (e.g., "History", "Science", "Technology")
            count: Number of articles to return
            
        Returns:
            List of WikipediaArticle objects from the category
        """
        try:
            response = requests.get(
                self.api_url,
                params={
                    'action': 'query',
                    'list': 'categorymembers',
                    'cmtitle': f'Category:{category}',
                    'cmlimit': count * 2,
                    'format': 'json'
                },
                headers=self.headers
            )
            
            data = response.json()
            titles = [page['title'] for page in data['query']['categorymembers']]
            
            articles = []
            for title in titles[:count]:
                article = self.fetch_article(title)
                if article and article.word_count > 500:  # Ensure substantial content
                    articles.append(article)
                time.sleep(0.1)
            
            return articles
            
        except Exception as e:
            print(f"Error fetching articles from category '{category}': {str(e)}")
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
            response = requests.get(
                self.api_url,
                params={
                    'action': 'query',
                    'list': 'search',
                    'srsearch': query,
                    'srlimit': count,
                    'format': 'json'
                },
                headers=self.headers
            )
            
            data = response.json()
            titles = [result['title'] for result in data['query']['search']]
            
            articles = []
            for title in titles:
                article = self.fetch_article(title)
                if article:
                    articles.append(article)
                time.sleep(0.1)
            
            return articles
            
        except Exception as e:
            print(f"Error searching articles for '{query}': {str(e)}")
            return []
    
    def get_on_this_day(self, date: Optional[datetime] = None) -> List[WikipediaArticle]:
        """
        Get articles related to events that happened on this day in history
        
        Args:
            date: Specific date to check (defaults to today)
            
        Returns:
            List of historical event WikipediaArticle objects
        """
        if date is None:
            date = datetime.now()
        
        try:
            response = requests.get(
                f"{self.base_url}/feed/onthisday/all/{date.month:02d}/{date.day:02d}",
                headers=self.headers
            )
            
            data = response.json()
            articles = []
            
            # Get events and births/deaths
            for section in ['events', 'births', 'deaths']:
                if section in data:
                    for item in data[section][:5]:  # Limit to prevent too many requests
                        for page in item.get('pages', []):
                            article = self.fetch_article(page['titles']['normalized'])
                            if article:
                                articles.append(article)
                            time.sleep(0.1)
            
            return articles
            
        except Exception as e:
            print(f"Error fetching 'on this day' articles: {str(e)}")
            return []
    
    # Private helper methods
    
    def _get_page_info(self, title: str) -> Optional[Dict]:
        """Get basic page information"""
        try:
            response = requests.get(
                self.api_url,
                params={
                    'action': 'query',
                    'titles': title,
                    'prop': 'extracts|info',
                    'exintro': True,
                    'explaintext': True,
                    'exsectionformat': 'plain',
                    'inprop': 'url',
                    'format': 'json'
                },
                headers=self.headers
            )
            
            data = response.json()
            pages = data['query']['pages']
            page_id = list(pages.keys())[0]
            
            if page_id == '-1':  # Page not found
                return None
                
            return pages[page_id]
            
        except Exception:
            return None
    
    def _get_page_content(self, title: str) -> Optional[str]:
        """Get full page content"""
        try:
            response = requests.get(
                self.api_url,
                params={
                    'action': 'query',
                    'titles': title,
                    'prop': 'extracts',
                    'explaintext': True,
                    'exsectionformat': 'plain',
                    'format': 'json'
                },
                headers=self.headers
            )
            
            data = response.json()
            pages = data['query']['pages']
            page_id = list(pages.keys())[0]
            
            if page_id == '-1':
                return None
                
            content = pages[page_id].get('extract', '')
            
            # Clean up the content
            content = re.sub(r'\n\s*\n', '\n\n', content)  # Remove excessive newlines
            content = re.sub(r'==+.*?==+', '', content)    # Remove section headers
            
            return content.strip()
            
        except Exception:
            return None
    
    def _get_page_views(self, title: str, days: int = 7) -> int:
        """Get recent page view statistics"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{self.language}.wikipedia/all-access/user/{title}/daily/{start_date.strftime('%Y%m%d')}/{end_date.strftime('%Y%m%d')}"
            
            response = requests.get(url, headers=self.headers)
            data = response.json()
            
            total_views = sum(item['views'] for item in data.get('items', []))
            return total_views
            
        except Exception:
            return 0
    
    def _get_categories(self, title: str) -> List[str]:
        """Get article categories"""
        try:
            response = requests.get(
                self.api_url,
                params={
                    'action': 'query',
                    'titles': title,
                    'prop': 'categories',
                    'cllimit': 50,
                    'format': 'json'
                },
                headers=self.headers
            )
            
            data = response.json()
            pages = data['query']['pages']
            page_id = list(pages.keys())[0]
            
            if page_id == '-1':
                return []
                
            categories = pages[page_id].get('categories', [])
            return [cat['title'].replace('Category:', '') for cat in categories]
            
        except Exception:
            return []
    
    def _get_references(self, title: str) -> List[str]:
        """Get article references/external links"""
        try:
            response = requests.get(
                self.api_url,
                params={
                    'action': 'query',
                    'titles': title,
                    'prop': 'extlinks',
                    'ellimit': 20,
                    'format': 'json'
                },
                headers=self.headers
            )
            
            data = response.json()
            pages = data['query']['pages']
            page_id = list(pages.keys())[0]
            
            if page_id == '-1':
                return []
                
            links = pages[page_id].get('extlinks', [])
            return [link['*'] for link in links]
            
        except Exception:
            return []
    
    def _get_images(self, title: str) -> List[str]:
        """Get article images"""
        try:
            response = requests.get(
                self.api_url,
                params={
                    'action': 'query',
                    'titles': title,
                    'prop': 'images',
                    'imlimit': 5,
                    'format': 'json'
                },
                headers=self.headers
            )
            
            data = response.json()
            pages = data['query']['pages']
            page_id = list(pages.keys())[0]
            
            if page_id == '-1':
                return []
                
            images = pages[page_id].get('images', [])
            return [img['title'] for img in images if not img['title'].endswith('.svg')]
            
        except Exception:
            return []
    
    def _get_most_viewed_pages(self, days: int = 1) -> List[str]:
        """Get most viewed pages from recent period"""
        try:
            date = (datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')
            url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/{self.language}.wikipedia/all-access/{date}"
            
            response = requests.get(url, headers=self.headers)
            data = response.json()
            
            articles = data['items'][0]['articles']
            
            # Filter out special pages
            filtered_articles = []
            for article in articles:
                title = article['article']
                if not any(prefix in title.lower() for prefix in ['main_page', 'special:', 'file:', 'category:', 'template:']):
                    filtered_articles.append(title.replace('_', ' '))
            
            return filtered_articles
            
        except Exception:
            return []
    
    def _calculate_quality_score(self, content: str, references: List[str], categories: List[str]) -> float:
        """Calculate a quality score for the article (0-1)"""
        score = 0.0
        
        # Content quality indicators
        word_count = len(content.split())
        if word_count > 2000:
            score += 0.3
        elif word_count > 1000:
            score += 0.2
        elif word_count > 500:
            score += 0.1
        
        # References indicate reliability
        ref_count = len(references)
        if ref_count > 10:
            score += 0.3
        elif ref_count > 5:
            score += 0.2
        elif ref_count > 0:
            score += 0.1
        
        # Categories indicate structure
        cat_count = len(categories)
        if cat_count > 5:
            score += 0.2
        elif cat_count > 2:
            score += 0.1
        
        # Content structure indicators
        if '.' in content and len(content.split('.')) > 10:
            score += 0.1  # Well-structured sentences
        
        if any(word in content.lower() for word in ['however', 'therefore', 'furthermore', 'moreover']):
            score += 0.1  # Analytical writing
        
        return min(score, 1.0)
    
    def _is_suitable_for_podcast(self, article: WikipediaArticle, min_views: int, exclude_categories: List[str]) -> bool:
        """Check if article is suitable for podcast generation"""
        # Check minimum views
        if article.page_views < min_views:
            return False
        
        # Check excluded categories
        for excluded in exclude_categories:
            if any(excluded.lower() in cat.lower() for cat in article.categories):
                return False
        
        # Check content quality
        if article.word_count < 300:  # Too short
            return False
        
        if article.quality_score < 0.3:  # Too low quality
            return False
        
        # Check for problematic content patterns
        problematic_patterns = [
            'disambiguation',
            'list of',
            'category:',
            'redirect',
            'stub'
        ]
        
        if any(pattern in article.title.lower() for pattern in problematic_patterns):
            return False
        
        return True
    
    def _filter_and_limit_articles(self, articles: List[WikipediaArticle], count: int, min_views: int, exclude_categories: List[str]) -> List[WikipediaArticle]:
        """Filter and limit articles based on criteria"""
        filtered = [
            article for article in articles
            if self._is_suitable_for_podcast(article, min_views, exclude_categories)
        ]
        
        # Sort by quality score and views
        filtered.sort(key=lambda x: (x.quality_score, x.page_views), reverse=True)
        
    def suggest_titles(self, partial_title: str, count: int = 5) -> List[str]:
        """
        Suggest Wikipedia article titles based on partial input
        
        Args:
            partial_title: Partial or approximate title
            count: Number of suggestions to return
            
        Returns:
            List of suggested titles
        """
        try:
            response = requests.get(
                self.api_url,
                params={
                    'action': 'opensearch',
                    'search': partial_title,
                    'limit': count,
                    'format': 'json'
                },
                headers=self.headers
            )
            
            data = response.json()
            # OpenSearch returns [query, [titles], [descriptions], [urls]]
            if len(data) >= 2:
                return data[1]  # Return the titles list
            return []
            
        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return []
    
    def find_exact_title(self, approximate_title: str) -> Optional[str]:
        """
        Find the exact Wikipedia title for an approximate search
        
        Args:
            approximate_title: The title you're looking for
            
        Returns:
            Exact Wikipedia title if found, None otherwise
        """
        # Try common variations
        variations = [
            approximate_title,
            approximate_title.title(),  # Title Case
            approximate_title.lower(),   # lowercase
            approximate_title.replace('_', ' '),  # Replace underscores
            approximate_title.replace(' ', '_'),  # Replace spaces
        ]
        
        for variation in variations:
            try:
                clean_title = variation.replace(' ', '_')
                page_info = self._get_page_info(clean_title)
                if page_info:
                    return page_info['title']
            except:
                continue
        
        return None
    
    def list_cached_articles(self) -> List[Dict[str, str]]:
        """List all cached articles with basic info"""
        cached_articles = []
        articles_dir = self.cache_dir / 'articles'
        
        for file_path in articles_dir.glob('*.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cached_articles.append({
                        'title': data.get('title', 'Unknown'),
                        'filename': file_path.name,
                        'word_count': data.get('word_count', 0),
                        'quality_score': data.get('quality_score', 0.0),
                        'cached_date': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                    })
            except Exception:
                continue
        
        return sorted(cached_articles, key=lambda x: x['cached_date'], reverse=True)
    
    def load_cached_article(self, filename: str) -> Optional[WikipediaArticle]:
        """Load a specific cached article by filename"""
        return self._load_from_file_cache(filename.replace('.json', ''))
    
    def clear_cache(self, older_than_days: int = None):
        """Clear cached articles, optionally only those older than specified days"""
        articles_dir = self.cache_dir / 'articles'
        cutoff_date = datetime.now() - timedelta(days=older_than_days) if older_than_days else None
        
        deleted_count = 0
        for file_path in articles_dir.glob('*.json'):
            if cutoff_date is None or datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff_date:
                file_path.unlink()
                deleted_count += 1
        
        print(f"Deleted {deleted_count} cached articles")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about the cache"""
        articles_dir = self.cache_dir / 'articles'
        trending_dir = self.cache_dir / 'trending'
        featured_dir = self.cache_dir / 'featured'
        
        return {
            'total_articles': len(list(articles_dir.glob('*.json'))),
            'trending_batches': len(list(trending_dir.glob('*.json'))),
            'featured_batches': len(list(featured_dir.glob('*.json'))),
            'total_size_mb': sum(f.stat().st_size for f in self.cache_dir.rglob('*.json')) / (1024 * 1024)
        }
    
    def suggest_titles(self, partial_title: str, count: int = 5) -> List[str]:
        """
        Suggest Wikipedia article titles based on partial input
        
        Args:
            partial_title: Partial or approximate title
            count: Number of suggestions to return
            
        Returns:
            List of suggested titles
        """
        try:
            response = requests.get(
                self.api_url,
                params={
                    'action': 'opensearch',
                    'search': partial_title,
                    'limit': count,
                    'format': 'json'
                },
                headers=self.headers
            )
            
            data = response.json()
            # OpenSearch returns [query, [titles], [descriptions], [urls]]
            if len(data) >= 2:
                return data[1]  # Return the titles list
            return []
            
        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return []
    
    def find_exact_title(self, approximate_title: str) -> Optional[str]:
        """
        Find the exact Wikipedia title for an approximate search
        
        Args:
            approximate_title: The title you're looking for
            
        Returns:
            Exact Wikipedia title if found, None otherwise
        """
        # Try common variations
        variations = [
            approximate_title,
            approximate_title.title(),  # Title Case
            approximate_title.lower(),   # lowercase
            approximate_title.replace('_', ' '),  # Replace underscores
            approximate_title.replace(' ', '_'),  # Replace spaces
        ]
        
        for variation in variations:
            try:
                clean_title = variation.replace(' ', '_')
                page_info = self._get_page_info(clean_title)
                if page_info:
                    return page_info['title']
            except:
                continue
        
        return None
    
    # Private helper methods for file operations
    
    def _make_safe_filename(self, title: str) -> str:
        """Convert article title to safe filename"""
        # Remove or replace problematic characters
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        safe_title = re.sub(r'[^\w\s-]', '', safe_title)
        safe_title = re.sub(r'\s+', '_', safe_title)
        return safe_title[:100]  # Limit length
    
    def _save_to_file_cache(self, article: WikipediaArticle, filename: str):
        """Save article to file cache"""
        try:
            file_path = self.cache_dir / 'articles' / f"{filename}.json"
            
            # Convert dataclass to dict and add metadata
            article_data = asdict(article)
            article_data['cached_timestamp'] = datetime.now().isoformat()
            article_data['cache_version'] = '1.0'
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Warning: Could not save article to cache: {e}")
    
    def _load_from_file_cache(self, filename: str) -> Optional[WikipediaArticle]:
        """Load article from file cache"""
        try:
            file_path = self.cache_dir / 'articles' / f"{filename}.json"
            
            if not file_path.exists():
                return None
            
            # Check if file is too old (optional - you can adjust this)
            file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_age.days > 7:  # Cache expires after 7 days
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Remove metadata fields that aren't part of WikipediaArticle
            data.pop('cached_timestamp', None)
            data.pop('cache_version', None)
            
            # Create WikipediaArticle from the data
            return WikipediaArticle(**data)
            
        except Exception as e:
            print(f"Warning: Could not load article from cache: {e}")
            return None
    
    def _save_trending_batch(self, articles: List[WikipediaArticle]):
        """Save a batch of trending articles"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            file_path = self.cache_dir / 'trending' / f"trending_{timestamp}.json"
            
            batch_data = {
                'timestamp': datetime.now().isoformat(),
                'count': len(articles),
                'articles': [asdict(article) for article in articles]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(batch_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Warning: Could not save trending batch: {e}")
    
    def _save_featured_batch(self, articles: List[WikipediaArticle]):
        """Save a batch of featured articles"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            file_path = self.cache_dir / 'featured' / f"featured_{timestamp}.json"
            
            batch_data = {
                'timestamp': datetime.now().isoformat(),
                'count': len(articles),
                'articles': [asdict(article) for article in articles]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(batch_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Warning: Could not save featured batch: {e}")


# Example usage and testing functions
def example_usage():
    """Example of how to use the WikipediaContentFetcher"""
    
    # Initialize fetcher
    fetcher = WikipediaContentFetcher()
    
    print("=== Wikipedia Podcast Content Fetcher ===")
    print(f"Cache directory: {fetcher.cache_dir}")
    
    # Show cache stats
    stats = fetcher.get_cache_stats()
    print(f"Cache stats: {stats['total_articles']} articles, {stats['total_size_mb']:.2f} MB")
    
    # Fetch specific article
    print("\n=== Fetching specific article ===")
    article = fetcher.fetch_article("Artificial Intelligence")
    if article:
        print(f"Title: {article.title}")
        print(f"Word count: {article.word_count}")
        print(f"Quality score: {article.quality_score:.2f}")
        print(f"Page views (7 days): {article.page_views}")
        print(f"Categories: {', '.join(article.categories[:5])}")
        print(f"Summary: {article.summary[:200]}...")
    
    print("\n=== Getting trending articles ===")
    trending = fetcher.get_trending_articles(count=5)
    for i, article in enumerate(trending, 1):
        print(f"{i}. {article.title} (Views: {article.page_views}, Quality: {article.quality_score:.2f})")
    
    print("\n=== Getting featured articles ===")
    featured = fetcher.get_featured_articles(count=3)
    for i, article in enumerate(featured, 1):
        print(f"{i}. {article.title} (Quality: {article.quality_score:.2f})")
    
    print("\n=== Listing cached articles ===")
    cached = fetcher.list_cached_articles()
    for article in cached[:5]:  # Show first 5
        print(f"- {article['title']} (cached: {article['cached_date']}, {article['word_count']} words)")
    
    print(f"\n=== Final cache stats ===")
    final_stats = fetcher.get_cache_stats()
    print(f"Total articles cached: {final_stats['total_articles']}")
    print(f"Cache size: {final_stats['total_size_mb']:.2f} MB")
    print(f"Cache location: {fetcher.cache_dir.absolute()}")


if __name__ == "__main__":
    example_usage()