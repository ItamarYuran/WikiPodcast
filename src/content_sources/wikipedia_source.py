"""
Wikipedia Content Source Implementation
Main Wikipedia API interface with smart search and suggestions
"""

import asyncio
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from ..core.models import ProcessingResult
from ..utils.http_client import HTTPClient, create_wikipedia_client
from ..utils.async_utils import AsyncBatch, AsyncRetry, create_retry_handler
from ..config_management.config_manager import get_content_source_config
from .interfaces import (
    ContentSource, TrendingContentSource, FeaturedContentSource, 
    CategoryContentSource, HistoricalContentSource, SuggestionProvider,
    Article, ArticleSuggestion, SearchCriteria, ContentLength
)


class WikipediaContentSource(
    ContentSource, 
    TrendingContentSource, 
    FeaturedContentSource,
    CategoryContentSource,
    HistoricalContentSource,
    SuggestionProvider
):
    """
    Wikipedia content source with comprehensive search and suggestion capabilities
    """
    
    def __init__(self, language: str = 'en', http_client: Optional[HTTPClient] = None):
        """
        Initialize Wikipedia content source
        
        Args:
            language: Wikipedia language code
            http_client: Optional HTTP client (will create default if not provided)
        """
        self.language = language
        self.config = get_content_source_config()
        self.http_client = http_client or create_wikipedia_client()
        self.retry_handler = create_retry_handler(max_attempts=3)
        
        # API endpoints
        self.base_url = f'https://{language}.wikipedia.org/api/rest_v1'
        self.api_url = f'https://{language}.wikipedia.org/w/api.php'
        
        # Memory cache for current session
        self._memory_cache: Dict[str, Article] = {}
        self._suggestion_cache: Dict[str, List[ArticleSuggestion]] = {}
    
    def supports_source(self, identifier: str) -> bool:
        """Check if this source can handle the identifier"""
        # Support Wikipedia URLs, titles, or general text
        if isinstance(identifier, str):
            return True  # Wikipedia can attempt to find articles for any text
        return False
    
    async def fetch_article(self, title: str, criteria: SearchCriteria) -> ProcessingResult[Article]:
        """
        Fetch a Wikipedia article by title with smart fallback
        
        Args:
            title: Article title
            criteria: Search criteria
            
        Returns:
            ProcessingResult containing Article or error information
        """
        try:
            # Check memory cache first
            cache_key = f"{title}_{criteria.include_references}_{criteria.target_length.value}"
            if cache_key in self._memory_cache:
                return ProcessingResult.success(self._memory_cache[cache_key])
            
            # Try exact title variations first
            exact_match = await self._try_exact_variations(title)
            if exact_match:
                article = await self._fetch_article_content(exact_match, criteria)
                if article.success:
                    self._memory_cache[cache_key] = article.data
                    return article
            
            # If no exact match, try smart suggestions
            suggestions_result = await self.get_smart_suggestions(title, max_results=5)
            if not suggestions_result.success or not suggestions_result.data:
                return ProcessingResult.failure(
                    f"No articles found for '{title}'",
                    error_code="ARTICLE_NOT_FOUND"
                )
            
            # Use best suggestion if confidence is high
            best_suggestion = suggestions_result.data[0]
            if best_suggestion.similarity_score > 0.7:
                article = await self._fetch_article_content(best_suggestion.title, criteria)
                if article.success:
                    self._memory_cache[cache_key] = article.data
                    return article
            
            return ProcessingResult.failure(
                f"No suitable articles found for '{title}'. Best match: '{best_suggestion.title}' (confidence: {best_suggestion.similarity_score:.2f})",
                error_code="LOW_CONFIDENCE_MATCH",
                metadata={'suggestions': suggestions_result.data}
            )
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error fetching article '{title}': {str(e)}",
                error_code="FETCH_ERROR",
                exception=e
            )
    
    async def search_articles(self, criteria: SearchCriteria) -> ProcessingResult[List[Article]]:
        """
        Search for articles matching criteria
        
        Args:
            criteria: Search criteria
            
        Returns:
            ProcessingResult containing list of Articles
        """
        try:
            # Get search results from Wikipedia API
            search_params = {
                'action': 'query',
                'list': 'search',
                'srsearch': criteria.query,
                'srlimit': criteria.max_results * 2,  # Get extra to account for filtering
                'srprop': 'snippet|titlesnippet|size',
                'format': 'json'
            }
            
            response = await self.http_client.get(self.api_url, params=search_params)
            
            if not response.success:
                return ProcessingResult.failure(
                    f"Search API request failed: {response.error}",
                    error_code="API_ERROR"
                )
            
            data = response.json
            if not data or 'query' not in data or 'search' not in data['query']:
                return ProcessingResult.failure(
                    "Invalid search response from Wikipedia API",
                    error_code="INVALID_RESPONSE"
                )
            
            search_results = data['query']['search']
            
            # Fetch full articles for the search results
            batch_processor = AsyncBatch(batch_size=5, max_concurrent=3, rate_limit=2.0)
            
            async def fetch_single_article(result):
                return await self._fetch_article_content(result['title'], criteria)
            
            batch_result = await batch_processor.process_batch(
                search_results[:criteria.max_results],
                fetch_single_article
            )
            
            # Extract successful articles
            articles = [result.data for result in batch_result.successful if result.success]
            
            return ProcessingResult.success(articles)
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error searching articles: {str(e)}",
                error_code="SEARCH_ERROR",
                exception=e
            )
    
    async def get_suggestions(self, query: str, max_results: int = 10) -> ProcessingResult[List[ArticleSuggestion]]:
        """Get article suggestions for a query"""
        return await self.get_smart_suggestions(query, max_results)
    
    async def get_trending_articles(self, criteria: SearchCriteria) -> ProcessingResult[List[Article]]:
        """
        Get currently trending Wikipedia articles
        
        Args:
            criteria: Filtering criteria
            
        Returns:
            ProcessingResult containing trending articles
        """
        try:
            # Get most viewed pages from recent period
            trending_titles = await self._get_most_viewed_pages()
            
            if not trending_titles:
                return ProcessingResult.failure(
                    "No trending articles found",
                    error_code="NO_TRENDING_DATA"
                )
            
            # Fetch articles for trending titles
            batch_processor = AsyncBatch(batch_size=5, max_concurrent=3, rate_limit=2.0)
            
            async def fetch_trending_article(title):
                return await self._fetch_article_content(title, criteria)
            
            # Process in batches to avoid overwhelming the API
            batch_result = await batch_processor.process_batch(
                trending_titles[:criteria.max_results * 2],  # Get extra for filtering
                fetch_trending_article
            )
            
            # Filter and sort results
            articles = [result.data for result in batch_result.successful if result.success]
            filtered_articles = self._filter_articles(articles, criteria)
            
            return ProcessingResult.success(filtered_articles[:criteria.max_results])
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error fetching trending articles: {str(e)}",
                error_code="TRENDING_ERROR",
                exception=e
            )
    
    async def get_featured_articles(self, criteria: SearchCriteria) -> ProcessingResult[List[Article]]:
        """
        Get Wikipedia's featured articles
        
        Args:
            criteria: Filtering criteria
            
        Returns:
            ProcessingResult containing featured articles
        """
        try:
            # Get featured articles from category
            featured_params = {
                'action': 'query',
                'list': 'categorymembers',
                'cmtitle': 'Category:Featured articles',
                'cmlimit': criteria.max_results * 2,
                'format': 'json'
            }
            
            response = await self.http_client.get(self.api_url, params=featured_params)
            
            if not response.success:
                return ProcessingResult.failure(
                    f"Featured articles API request failed: {response.error}",
                    error_code="API_ERROR"
                )
            
            data = response.json
            if not data or 'query' not in data:
                return ProcessingResult.failure(
                    "Invalid featured articles response",
                    error_code="INVALID_RESPONSE"
                )
            
            featured_titles = [page['title'] for page in data['query']['categorymembers']]
            
            # Randomize to get variety
            import random
            random.shuffle(featured_titles)
            
            # Fetch full articles
            batch_processor = AsyncBatch(batch_size=3, max_concurrent=2, rate_limit=1.0)
            
            async def fetch_featured_article(title):
                return await self._fetch_article_content(title, criteria)
            
            batch_result = await batch_processor.process_batch(
                featured_titles[:criteria.max_results],
                fetch_featured_article
            )
            
            articles = [result.data for result in batch_result.successful if result.success]
            
            return ProcessingResult.success(articles)
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error fetching featured articles: {str(e)}",
                error_code="FEATURED_ERROR",
                exception=e
            )
    
    async def get_articles_by_category(self, category: str, criteria: SearchCriteria) -> ProcessingResult[List[Article]]:
        """
        Get articles from a specific category
        
        Args:
            category: Category name
            criteria: Filtering criteria
            
        Returns:
            ProcessingResult containing articles from category
        """
        try:
            category_params = {
                'action': 'query',
                'list': 'categorymembers',
                'cmtitle': f'Category:{category}',
                'cmlimit': criteria.max_results * 2,
                'format': 'json'
            }
            
            response = await self.http_client.get(self.api_url, params=category_params)
            
            if not response.success:
                return ProcessingResult.failure(
                    f"Category API request failed: {response.error}",
                    error_code="API_ERROR"
                )
            
            data = response.json
            if not data or 'query' not in data:
                return ProcessingResult.failure(
                    f"Invalid category response for '{category}'",
                    error_code="INVALID_RESPONSE"
                )
            
            category_titles = [page['title'] for page in data['query']['categorymembers']]
            
            # Fetch articles
            batch_processor = AsyncBatch(batch_size=5, max_concurrent=3, rate_limit=2.0)
            
            async def fetch_category_article(title):
                return await self._fetch_article_content(title, criteria)
            
            batch_result = await batch_processor.process_batch(
                category_titles[:criteria.max_results],
                fetch_category_article
            )
            
            articles = [result.data for result in batch_result.successful if result.success]
            filtered_articles = self._filter_articles(articles, criteria)
            
            return ProcessingResult.success(filtered_articles)
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error fetching articles from category '{category}': {str(e)}",
                error_code="CATEGORY_ERROR",
                exception=e
            )
    
    async def get_available_categories(self) -> ProcessingResult[List[str]]:
        """Get list of available categories (top-level categories)"""
        try:
            # Get main categories
            categories_params = {
                'action': 'query',
                'list': 'categorymembers',
                'cmtitle': 'Category:Main topic classifications',
                'cmlimit': 50,
                'format': 'json'
            }
            
            response = await self.http_client.get(self.api_url, params=categories_params)
            
            if not response.success:
                return ProcessingResult.failure(
                    f"Categories API request failed: {response.error}",
                    error_code="API_ERROR"
                )
            
            data = response.json
            if not data or 'query' not in data:
                return ProcessingResult.failure(
                    "Invalid categories response",
                    error_code="INVALID_RESPONSE"
                )
            
            # Extract category names (remove "Category:" prefix)
            categories = [
                page['title'].replace('Category:', '') 
                for page in data['query']['categorymembers']
                if page['title'].startswith('Category:')
            ]
            
            return ProcessingResult.success(categories)
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error fetching categories: {str(e)}",
                error_code="CATEGORIES_ERROR",
                exception=e
            )
    
    async def get_on_this_day(self, date: Optional[datetime] = None, criteria: SearchCriteria = None) -> ProcessingResult[List[Article]]:
        """
        Get articles related to events on this day in history
        
        Args:
            date: Specific date (defaults to today)
            criteria: Optional filtering criteria
            
        Returns:
            ProcessingResult containing historical articles
        """
        if date is None:
            date = datetime.now()
        
        if criteria is None:
            criteria = SearchCriteria(query="", max_results=10)
        
        try:
            # Use Wikipedia's "On this day" API
            url = f"{self.base_url}/feed/onthisday/all/{date.month:02d}/{date.day:02d}"
            response = await self.http_client.get(url)
            
            if not response.success:
                return ProcessingResult.failure(
                    f"On this day API request failed: {response.error}",
                    error_code="API_ERROR"
                )
            
            data = response.json
            if not data:
                return ProcessingResult.failure(
                    "Invalid 'on this day' response",
                    error_code="INVALID_RESPONSE"
                )
            
            # Extract article titles from events, births, and deaths
            titles = []
            for section in ['events', 'births', 'deaths']:
                if section in data:
                    for item in data[section][:3]:  # Limit to prevent too many requests
                        for page in item.get('pages', []):
                            titles.append(page['titles']['normalized'])
            
            # Fetch articles
            batch_processor = AsyncBatch(batch_size=3, max_concurrent=2, rate_limit=1.0)
            
            async def fetch_historical_article(title):
                return await self._fetch_article_content(title, criteria)
            
            batch_result = await batch_processor.process_batch(
                titles[:criteria.max_results],
                fetch_historical_article
            )
            
            articles = [result.data for result in batch_result.successful if result.success]
            
            return ProcessingResult.success(articles)
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error fetching 'on this day' articles: {str(e)}",
                error_code="HISTORICAL_ERROR",
                exception=e
            )
    
    async def get_smart_suggestions(self, query: str, max_results: int = 10) -> ProcessingResult[List[ArticleSuggestion]]:
        """
        Get intelligent article suggestions using multiple strategies
        
        Args:
            query: Search query
            max_results: Maximum suggestions to return
            
        Returns:
            ProcessingResult containing ranked suggestions
        """
        # Check cache first
        cache_key = f"{query}_{max_results}"
        if cache_key in self._suggestion_cache:
            return ProcessingResult.success(self._suggestion_cache[cache_key])
        
        try:
            suggestions = []
            
            # Strategy 1: OpenSearch API (prefix matching)
            opensearch_suggestions = await self._get_opensearch_suggestions(query, max_results)
            suggestions.extend(opensearch_suggestions)
            
            # Strategy 2: Full-text search
            search_suggestions = await self._get_search_suggestions(query, max_results)
            suggestions.extend(search_suggestions)
            
            # Strategy 3: Fuzzy matching for common domains
            fuzzy_suggestions = await self._get_fuzzy_suggestions(query, max_results // 2)
            suggestions.extend(fuzzy_suggestions)
            
            # Remove duplicates and rank
            unique_suggestions = self._deduplicate_suggestions(suggestions)
            ranked_suggestions = self._rank_suggestions(query, unique_suggestions, max_results)
            
            # Cache the results
            self._suggestion_cache[cache_key] = ranked_suggestions
            
            return ProcessingResult.success(ranked_suggestions)
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error getting suggestions for '{query}': {str(e)}",
                error_code="SUGGESTIONS_ERROR",
                exception=e
            )
    
    async def get_related_articles(self, article_title: str, max_results: int = 5) -> ProcessingResult[List[str]]:
        """
        Get articles related to the given article
        
        Args:
            article_title: Source article title
            max_results: Maximum related articles to return
            
        Returns:
            ProcessingResult containing related article titles
        """
        try:
            # Get categories of the source article
            categories = await self._get_categories(article_title)
            
            related_titles = set()
            
            # Find articles in same categories (limit to avoid too many requests)
            for category in categories[:3]:
                try:
                    category_params = {
                        'action': 'query',
                        'list': 'categorymembers',
                        'cmtitle': f'Category:{category}',
                        'cmlimit': 10,
                        'format': 'json'
                    }
                    
                    response = await self.http_client.get(self.api_url, params=category_params)
                    
                    if response.success and response.json:
                        for page in response.json['query']['categorymembers']:
                            if page['title'] != article_title:  # Exclude source article
                                related_titles.add(page['title'])
                    
                    # Rate limiting
                    await asyncio.sleep(0.1)
                    
                except Exception:
                    continue
            
            return ProcessingResult.success(list(related_titles)[:max_results])
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error finding related articles for '{article_title}': {str(e)}",
                error_code="RELATED_ERROR",
                exception=e
            )
    
    def calculate_similarity(self, query: str, title: str) -> float:
        """Calculate similarity score between query and title"""
        query_lower = query.lower().strip()
        title_lower = title.lower().strip()
        
        # Exact match
        if query_lower == title_lower:
            return 1.0
        
        # Check if query is contained in title
        if query_lower in title_lower:
            return 0.9
        
        # Check if title is contained in query
        if title_lower in query_lower:
            return 0.8
        
        # Use sequence matching
        import difflib
        sequence_match = difflib.SequenceMatcher(None, query_lower, title_lower).ratio()
        
        # Boost score for common prefixes/suffixes
        if title_lower.startswith(query_lower) or query_lower.startswith(title_lower):
            sequence_match += 0.2
        
        # Word-based similarity
        query_words = set(query_lower.split())
        title_words = set(title_lower.split())
        
        if query_words and title_words:
            word_overlap = len(query_words.intersection(title_words)) / len(query_words.union(title_words))
            sequence_match = max(sequence_match, word_overlap)
        
        return min(sequence_match, 1.0)
    
    # Private helper methods
    
    async def _try_exact_variations(self, query: str) -> Optional[str]:
        """Try various exact title variations"""
        def title_case_names(text):
            return ' '.join(word.capitalize() for word in text.split())
        
        variations = [
            query,
            query.strip(),
            query.title(),
            title_case_names(query),
            query.lower(),
            query.upper(),
            query.capitalize(),
            query.replace('_', ' '),
            query.replace(' ', '_'),
            query.replace('-', ' '),
            query.replace(' ', '-'),
            title_case_names(query).replace(' ', '_'),
            query.title().replace(' ', '_'),
        ]
        
        # Add common disambiguation patterns
        if not any(word in query.lower() for word in ['(disambiguation)', '(band)', '(musician)', '(album)']):
            base_title = title_case_names(query)
            variations.extend([
                f"{base_title} (musician)",
                f"{base_title} (band)",
                f"{base_title} (composer)",
                f"{base_title} (artist)",
                f"{base_title} (album)",
                f"{base_title} (song)",
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for var in variations:
            if var not in seen:
                seen.add(var)
                unique_variations.append(var)
        
        # Test each variation
        for variation in unique_variations:
            try:
                page_info = await self._get_page_info(variation.replace(' ', '_'))
                if page_info and 'missing' not in page_info:
                    return page_info['title']
            except Exception:
                continue
        
        return None
    
    async def _fetch_article_content(self, title: str, criteria: SearchCriteria) -> ProcessingResult[Article]:
        """Fetch complete article content"""
        try:
            # Get page info and content in parallel
            async def get_page_info():
                return await self._get_page_info(title.replace(' ', '_'))
            
            async def get_page_content():
                return await self._get_page_content(title.replace(' ', '_'))
            
            page_info, content = await asyncio.gather(
                get_page_info(),
                get_page_content(),
                return_exceptions=True
            )
            
            if isinstance(page_info, Exception) or isinstance(content, Exception):
                error_msg = str(page_info if isinstance(page_info, Exception) else content)
                return ProcessingResult.failure(
                    f"Error fetching article content: {error_msg}",
                    error_code="CONTENT_ERROR"
                )
            
            if not page_info or not content:
                return ProcessingResult.failure(
                    f"Article content not found for '{title}'",
                    error_code="CONTENT_NOT_FOUND"
                )
            
            # Get additional metadata
            page_views = await self._get_page_views(title.replace(' ', '_'))
            categories = await self._get_categories(title.replace(' ', '_'))
            references = await self._get_references(title.replace(' ', '_')) if criteria.include_references else []
            images = await self._get_images(title.replace(' ', '_'))
            
            # Process content length if needed
            if criteria.target_length != ContentLength.FULL:
                content = self._control_content_length(content, criteria.target_length)
            
            # Create article object
            article = Article(
                title=page_info.get('title', title),
                url=f"https://{self.language}.wikipedia.org/wiki/{title.replace(' ', '_')}",
                content=content,
                summary=page_info.get('extract', ''),
                categories=categories,
                page_views=page_views,
                last_modified=page_info.get('timestamp', ''),
                references=references,
                images=images,
                word_count=len(content.split()),
                quality_score=self._calculate_quality_score(content, references, categories)
            )
            
            return ProcessingResult.success(article)
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error fetching article '{title}': {str(e)}",
                error_code="FETCH_ERROR",
                exception=e
            )
    
    async def _get_page_info(self, title: str) -> Optional[Dict]:
        """Get basic page information and handle redirects"""
        async def fetch_page_info():
            params = {
                'action': 'query',
                'titles': title,
                'prop': 'extracts|info',
                'exintro': True,
                'explaintext': True,
                'exsectionformat': 'plain',
                'inprop': 'url',
                'redirects': True,
                'format': 'json'
            }
            
            response = await self.http_client.get(self.api_url, params=params)
            
            if not response.success:
                return None
            
            data = response.json
            if not data or 'query' not in data:
                return None
            
            pages = data['query']['pages']
            page_id = list(pages.keys())[0]
            
            if page_id == '-1':  # Page not found
                return None
            
            page_data = pages[page_id]
            if 'missing' in page_data:
                return None
            
            return page_data
        
        return await self.retry_handler.execute(fetch_page_info)
    
    async def _get_page_content(self, title: str) -> Optional[str]:
        """Get full page content"""
        async def fetch_content():
            params = {
                'action': 'query',
                'titles': title,
                'prop': 'extracts',
                'explaintext': True,
                'exsectionformat': 'plain',
                'format': 'json'
            }
            
            response = await self.http_client.get(self.api_url, params=params)
            
            if not response.success:
                return None
            
            data = response.json
            if not data or 'query' not in data:
                return None
            
            pages = data['query']['pages']
            page_id = list(pages.keys())[0]
            
            if page_id == '-1':
                return None
            
            content = pages[page_id].get('extract', '')
            
            # Clean up the content
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = re.sub(r'==+.*?==+', '', content)
            
            return content.strip()
        
        return await self.retry_handler.execute(fetch_content)
    
    async def _get_page_views(self, title: str, days: int = 7) -> int:
        """Get recent page view statistics"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{self.language}.wikipedia/all-access/user/{title}/daily/{start_date.strftime('%Y%m%d')}/{end_date.strftime('%Y%m%d')}"
            
            response = await self.http_client.get(url)
            
            if not response.success:
                return 0
            
            data = response.json
            if not data or 'items' not in data:
                return 0
            
            return sum(item['views'] for item in data['items'])
            
        except Exception:
            return 0
    
    async def _get_categories(self, title: str) -> List[str]:
        """Get article categories"""
        try:
            params = {
                'action': 'query',
                'titles': title,
                'prop': 'categories',
                'cllimit': 50,
                'format': 'json'
            }
            
            response = await self.http_client.get(self.api_url, params=params)
            
            if not response.success:
                return []
            
            data = response.json
            if not data or 'query' not in data:
                return []
            
            pages = data['query']['pages']
            page_id = list(pages.keys())[0]
            
            if page_id == '-1':
                return []
            
            categories = pages[page_id].get('categories', [])
            return [cat['title'].replace('Category:', '') for cat in categories]
            
        except Exception:
            return []
    
    async def _get_references(self, title: str) -> List[str]:
        """Get article references/external links"""
        try:
            params = {
                'action': 'query',
                'titles': title,
                'prop': 'extlinks',
                'ellimit': 20,
                'format': 'json'
            }
            
            response = await self.http_client.get(self.api_url, params=params)
            
            if not response.success:
                return []
            
            data = response.json
            if not data or 'query' not in data:
                return []
            
            pages = data['query']['pages']
            page_id = list(pages.keys())[0]
            
            if page_id == '-1':
                return []
            
            links = pages[page_id].get('extlinks', [])
            return [link['*'] for link in links]
            
        except Exception:
            return []
    
    async def _get_images(self, title: str) -> List[str]:
        """Get article images"""
        try:
            params = {
                'action': 'query',
                'titles': title,
                'prop': 'images',
                'imlimit': 5,
                'format': 'json'
            }
            
            response = await self.http_client.get(self.api_url, params=params)
            
            if not response.success:
                return []
            
            data = response.json
            if not data or 'query' not in data:
                return []
            
            pages = data['query']['pages']
            page_id = list(pages.keys())[0]
            
            if page_id == '-1':
                return []
            
            images = pages[page_id].get('images', [])
            return [img['title'] for img in images if not img['title'].endswith('.svg')]
            
        except Exception:
            return []
    
    async def _get_most_viewed_pages(self, days: int = 1) -> List[str]:
        """Get most viewed pages from recent period"""
        try:
            date = (datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')
            url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/{self.language}.wikipedia/all-access/{date}"
            
            response = await self.http_client.get(url)
            
            if not response.success:
                return []
            
            data = response.json
            if not data or 'items' not in data or not data['items']:
                return []
            
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
    
    async def _get_opensearch_suggestions(self, query: str, limit: int) -> List[ArticleSuggestion]:
        """Get suggestions using OpenSearch API"""
        try:
            params = {
                'action': 'opensearch',
                'search': query,
                'limit': limit,
                'format': 'json',
                'redirects': 'resolve'
            }
            
            response = await self.http_client.get(self.api_url, params=params)
            
            if not response.success:
                return []
            
            data = response.json
            if len(data) < 4:
                return []
            
            titles = data[1]
            descriptions = data[2]
            
            suggestions = []
            for i, title in enumerate(titles):
                snippet = descriptions[i] if i < len(descriptions) else ""
                similarity = self.calculate_similarity(query, title)
                
                suggestions.append(ArticleSuggestion(
                    title=title,
                    snippet=snippet,
                    similarity_score=similarity,
                    page_views=0,
                    is_disambiguation='disambiguation' in title.lower()
                ))
            
            return suggestions
            
        except Exception:
            return []
    
    async def _get_search_suggestions(self, query: str, limit: int) -> List[ArticleSuggestion]:
        """Get suggestions using full-text search"""
        try:
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'srlimit': limit,
                'srinfo': 'suggestion',
                'srprop': 'snippet|titlesnippet|size',
                'format': 'json'
            }
            
            response = await self.http_client.get(self.api_url, params=params)
            
            if not response.success:
                return []
            
            data = response.json
            if not data or 'query' not in data:
                return []
            
            search_results = data['query']['search']
            
            suggestions = []
            for result in search_results:
                title = result['title']
                snippet = re.sub(r'<.*?>', '', result.get('snippet', ''))
                similarity = self.calculate_similarity(query, title)
                
                suggestions.append(ArticleSuggestion(
                    title=title,
                    snippet=snippet,
                    similarity_score=similarity,
                    page_views=0,
                    is_disambiguation='disambiguation' in title.lower()
                ))
            
            return suggestions
            
        except Exception:
            return []
    
    async def _get_fuzzy_suggestions(self, query: str, limit: int) -> List[ArticleSuggestion]:
        """Get fuzzy matching suggestions for typos and variations"""
        suggestions = []
        
        # Context-aware suggestions for music-related terms
        if any(word in query.lower() for word in ['music', 'band', 'song', 'album', 'guitar', 'rock', 'jazz']):
            music_variations = [
                f"{query} band",
                f"{query} musician", 
                f"{query} composer",
                f"{query} singer"
            ]
            
            for variation in music_variations:
                try:
                    opensearch = await self._get_opensearch_suggestions(variation, 2)
                    suggestions.extend(opensearch)
                except Exception:
                    continue
        
        return suggestions[:limit]
    
    def _deduplicate_suggestions(self, suggestions: List[ArticleSuggestion]) -> List[ArticleSuggestion]:
        """Remove duplicate suggestions"""
        seen_titles = set()
        unique_suggestions = []
        
        for suggestion in suggestions:
            if suggestion.title not in seen_titles:
                seen_titles.add(suggestion.title)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions
    
    def _rank_suggestions(self, query: str, suggestions: List[ArticleSuggestion], limit: int) -> List[ArticleSuggestion]:
        """Rank suggestions by relevance"""
        def ranking_key(suggestion):
            score = suggestion.similarity_score
            
            # Penalize disambiguation pages
            if suggestion.is_disambiguation:
                score -= 0.3
            
            # Boost exact matches
            if suggestion.title.lower() == query.lower():
                score += 0.5
            
            # Boost if query appears early in title
            if query.lower() in suggestion.title.lower()[:len(query) + 5]:
                score += 0.1
            
            return score
        
        suggestions.sort(key=ranking_key, reverse=True)
        return suggestions[:limit]
    
    def _filter_articles(self, articles: List[Article], criteria: SearchCriteria) -> List[Article]:
        """Filter articles based on criteria"""
        filtered = []
        
        for article in articles:
            # Check minimum views
            if article.page_views < criteria.min_views:
                continue
            
            # Check excluded categories
            if any(excluded.lower() in cat.lower() for excluded in criteria.exclude_categories for cat in article.categories):
                continue
            
            # Check content quality
            if article.word_count < 300:  # Too short
                continue
            
            if article.quality_score < criteria.quality_threshold:
                continue
            
            # Check for problematic content patterns
            problematic_patterns = ['disambiguation', 'list of', 'category:', 'redirect', 'stub']
            if any(pattern in article.title.lower() for pattern in problematic_patterns):
                continue
            
            filtered.append(article)
        
        # Sort by quality score and views
        filtered.sort(key=lambda x: (x.quality_score, x.page_views), reverse=True)
        
        return filtered
    
    def _control_content_length(self, content: str, target_length: ContentLength) -> str:
        """Control article content length for target podcast duration"""
        length_targets = {
            ContentLength.SHORT: 875,   # ~5 minutes
            ContentLength.MEDIUM: 1750, # ~10 minutes
            ContentLength.LONG: 2625,   # ~15 minutes
            ContentLength.FULL: None    # No limit
        }
        
        target_words = length_targets.get(target_length)
        if not target_words:
            return content
        
        words = content.split()
        current_word_count = len(words)
        
        if current_word_count <= target_words:
            return content
        
        # Smart content reduction based on target length
        if target_length == ContentLength.SHORT:
            return self._create_short_summary(content, target_words)
        elif target_length == ContentLength.MEDIUM:
            return self._create_medium_summary(content, target_words)
        elif target_length == ContentLength.LONG:
            return self._create_long_summary(content, target_words)
        
        return content
    
    def _create_short_summary(self, content: str, target_words: int) -> str:
        """Create a short summary focusing on key points"""
        sentences = content.split('. ')
        
        # Take first 30% (introduction) and key sentences
        intro_sentences = sentences[:int(len(sentences) * 0.3)]
        
        # Find sentences with key indicators
        key_indicators = [
            'important', 'significant', 'notable', 'famous', 'known for',
            'discovered', 'invented', 'created', 'founded', 'established',
            'major', 'primary', 'main', 'key', 'central', 'crucial'
        ]
        
        key_sentences = [
            sentence for sentence in sentences
            if any(indicator in sentence.lower() for indicator in key_indicators)
        ]
        
        # Combine and deduplicate
        combined_sentences = intro_sentences + key_sentences[:10]
        seen = set()
        unique_sentences = []
        for sentence in combined_sentences:
            if sentence not in seen:
                seen.add(sentence)
                unique_sentences.append(sentence)
        
        result = '. '.join(unique_sentences)
        
        # Trim to target if still too long
        words = result.split()
        if len(words) > target_words:
            result = ' '.join(words[:target_words])
            last_period = result.rfind('.')
            if last_period > len(result) * 0.8:
                result = result[:last_period + 1]
        
        return result + "\n\n[Content condensed to highlight key points and main facts]"
    
    def _create_medium_summary(self, content: str, target_words: int) -> str:
        """Create a medium-length summary with main sections"""
        sentences = content.split('. ')
        total_sentences = len(sentences)
        
        # Take sections: intro (25%), middle (50%), conclusion (25%)
        intro_end = int(total_sentences * 0.25)
        middle_start = int(total_sentences * 0.25)
        middle_end = int(total_sentences * 0.75)
        
        intro_sentences = sentences[:intro_end]
        middle_sentences = sentences[middle_start:middle_end:2]  # Every other sentence
        conclusion_sentences = sentences[int(total_sentences * 0.75):]
        
        combined_sentences = intro_sentences + middle_sentences + conclusion_sentences
        result = '. '.join(combined_sentences)
        
        # Trim to target if needed
        words = result.split()
        if len(words) > target_words:
            result = ' '.join(words[:target_words])
            last_period = result.rfind('.')
            if last_period > len(result) * 0.8:
                result = result[:last_period + 1]
        
        return result + "\n\n[Content condensed to include main sections and key developments]"
    
    def _create_long_summary(self, content: str, target_words: int) -> str:
        """Create a comprehensive but condensed version"""
        sentences = content.split('. ')
        total_sentences = len(sentences)
        
        intro_end = int(total_sentences * 0.2)
        conclusion_start = int(total_sentences * 0.8)
        
        intro_sentences = sentences[:intro_end]
        middle_sentences = sentences[intro_end:conclusion_start:3]  # Every 3rd sentence
        conclusion_sentences = sentences[conclusion_start:]
        
        combined_sentences = intro_sentences + middle_sentences + conclusion_sentences
        result = '. '.join(combined_sentences)
        
        # Trim to target if needed
        words = result.split()
        if len(words) > target_words:
            result = ' '.join(words[:target_words])
            last_period = result.rfind('.')
            if last_period > len(result) * 0.9:
                result = result[:last_period + 1]
        
        return result + "\n\n[Content condensed while maintaining comprehensive coverage]"
    
    def _calculate_quality_score(self, content: str, references: List[str], categories: List[str]) -> float:
        """Calculate quality score for the article"""
        score = 0.0
        
        # Content length factor (0.0 - 0.3)
        word_count = len(content.split())
        if word_count > 2000:
            score += 0.3
        elif word_count > 1000:
            score += 0.2
        elif word_count > 500:
            score += 0.1
        
        # References factor (0.0 - 0.25)
        ref_count = len(references)
        if ref_count > 20:
            score += 0.25
        elif ref_count > 10:
            score += 0.2
        elif ref_count > 5:
            score += 0.15
        elif ref_count > 0:
            score += 0.1
        
        # Categories factor (0.0 - 0.15)
        cat_count = len(categories)
        if cat_count > 10:
            score += 0.15
        elif cat_count > 5:
            score += 0.1
        elif cat_count > 0:
            score += 0.05
        
        # Content quality indicators (0.0 - 0.2)
        quality_indicators = [
            'born', 'died', 'established', 'founded', 'created', 'developed',
            'published', 'released', 'invented', 'discovered', 'awarded',
            'graduated', 'studied', 'worked', 'career', 'known for', 'famous'
        ]
        
        content_lower = content.lower()
        indicator_count = sum(1 for indicator in quality_indicators if indicator in content_lower)
        
        if indicator_count > 10:
            score += 0.2
        elif indicator_count > 5:
            score += 0.15
        elif indicator_count > 2:
            score += 0.1
        elif indicator_count > 0:
            score += 0.05
        
        # Structural quality (0.0 - 0.1)
        paragraphs = content.split('\n\n')
        if len(paragraphs) > 5:
            score += 0.1
        elif len(paragraphs) > 2:
            score += 0.05
        
        # Penalty for low-quality indicators
        low_quality_markers = [
            'stub', 'disambiguation', 'redirect', 'may refer to',
            'this article needs', 'citation needed', 'unreliable source'
        ]
        
        for marker in low_quality_markers:
            if marker in content_lower:
                score -= 0.1
        
        return max(0.0, min(1.0, score))