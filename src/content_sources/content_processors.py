"""
Content Processing Components
Handles content validation, processing, and quality assessment
"""

import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from ..core.models import ProcessingResult
from .interfaces import (
    ContentProcessor, ContentValidator, ContentCache, InteractiveSelector,
    Article, ArticleSuggestion, SearchCriteria, ContentLength
)
from ..utils.filesystem import FileManager
from ..config_management.config_manager import get_cache_config


class WikipediaContentProcessor(ContentProcessor):
    """Content processor for Wikipedia articles"""
    
    def __init__(self):
        """Initialize content processor"""
        pass
    
    async def process_content(self, content: str, target_length: ContentLength) -> ProcessingResult[str]:
        """
        Process and potentially shorten content to target length
        
        Args:
            content: Original content
            target_length: Target content length
            
        Returns:
            ProcessingResult containing processed content
        """
        try:
            if target_length == ContentLength.FULL:
                return ProcessingResult.success(content)
            
            # Apply content length control
            processed_content = self._control_content_length(content, target_length)
            
            return ProcessingResult.success(processed_content)
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error processing content: {str(e)}",
                error_code="PROCESSING_ERROR",
                exception=e
            )
    
    def calculate_quality_score(self, article: Article) -> float:
        """Calculate quality score for an article"""
        score = 0.0
        
        # Content length factor (0.0 - 0.3)
        word_count = article.word_count
        if word_count > 2000:
            score += 0.3
        elif word_count > 1000:
            score += 0.2
        elif word_count > 500:
            score += 0.1
        
        # References factor (0.0 - 0.25)
        ref_count = len(article.references)
        if ref_count > 20:
            score += 0.25
        elif ref_count > 10:
            score += 0.2
        elif ref_count > 5:
            score += 0.15
        elif ref_count > 0:
            score += 0.1
        
        # Categories factor (0.0 - 0.15)
        cat_count = len(article.categories)
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
        
        content_lower = article.content.lower()
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
        paragraphs = article.content.split('\n\n')
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
    
    def estimate_duration(self, word_count: int, style: str = "conversational") -> Tuple[int, str]:
        """
        Estimate podcast duration based on word count and style
        
        Args:
            word_count: Number of words
            style: Speaking style
            
        Returns:
            Tuple of (duration_seconds, formatted_duration)
        """
        # Words per minute by style
        wpm_by_style = {
            "conversational": 160,
            "news_report": 180,
            "academic": 140,
            "storytelling": 150,
            "documentary": 145,
            "comedy": 170,
            "interview": 155,
            "kids_educational": 130
        }
        
        wpm = wpm_by_style.get(style, 150)
        duration_minutes = word_count / wpm
        duration_seconds = int(duration_minutes * 60)
        
        # Format duration
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        formatted = f"{minutes}:{seconds:02d}"
        
        return duration_seconds, formatted
    
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


class WikipediaContentValidator(ContentValidator):
    """Content validator for Wikipedia articles"""
    
    def __init__(self, processor: WikipediaContentProcessor):
        """Initialize validator with content processor"""
        self.processor = processor
    
    def validate_article(self, article: Article, criteria: SearchCriteria) -> ProcessingResult[Article]:
        """
        Validate article meets quality and content criteria
        
        Args:
            article: Article to validate
            criteria: Validation criteria
            
        Returns:
            ProcessingResult with validated article or validation errors
        """
        try:
            errors = []
            warnings = []
            
            # Check minimum content length
            if article.word_count < 300:
                errors.append(f"Article too short: {article.word_count} words (minimum: 300)")
            
            # Check quality score
            if article.quality_score < criteria.quality_threshold:
                errors.append(f"Quality score too low: {article.quality_score:.2f} (minimum: {criteria.quality_threshold})")
            
            # Check page views
            if article.page_views < criteria.min_views:
                warnings.append(f"Low page views: {article.page_views} (minimum: {criteria.min_views})")
            
            # Check for excluded categories
            excluded_found = []
            for excluded in criteria.exclude_categories:
                for category in article.categories:
                    if excluded.lower() in category.lower():
                        excluded_found.append(category)
            
            if excluded_found:
                errors.append(f"Article in excluded categories: {excluded_found}")
            
            # Check for problematic patterns
            problematic_patterns = ['disambiguation', 'list of', 'redirect', 'stub']
            problematic_found = []
            for pattern in problematic_patterns:
                if pattern in article.title.lower():
                    problematic_found.append(pattern)
            
            if problematic_found:
                errors.append(f"Article contains problematic patterns: {problematic_found}")
            
            # If there are errors, validation fails
            if errors:
                return ProcessingResult.failure(
                    f"Article validation failed: {'; '.join(errors)}",
                    error_code="VALIDATION_FAILED",
                    metadata={'errors': errors, 'warnings': warnings}
                )
            
            # If only warnings, validation succeeds but with warnings
            result = ProcessingResult.success(article)
            if warnings:
                result.metadata = {'warnings': warnings}
            
            return result
            
        except Exception as e:
            return ProcessingResult.failure(
                f"Error validating article: {str(e)}",
                error_code="VALIDATION_ERROR",
                exception=e
            )
    
    def is_suitable_for_podcast(self, article: Article, criteria: SearchCriteria) -> bool:
        """
        Check if article is suitable for podcast generation
        
        Args:
            article: Article to check
            criteria: Suitability criteria
            
        Returns:
            True if suitable for podcast
        """
        # Use validation but only check for errors (ignore warnings)
        validation_result = self.validate_article(article, criteria)
        return validation_result.success


class FileBasedContentCache(ContentCache):
    """File-based content cache implementation"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize file-based cache
        
        Args:
            cache_dir: Cache directory path (uses config default if None)
        """
        config = get_cache_config()
        self.cache_dir = cache_dir or config.articles_cache
        self.file_manager = FileManager(self.cache_dir)
        self.config = config
    
    async def get_cached_article(self, key: str) -> Optional[Article]:
        """
        Get article from cache
        
        Args:
            key: Cache key (usually article title)
            
        Returns:
            Cached article or None if not found/expired
        """
        try:
            safe_key = self._make_safe_filename(key)
            file_path = f"{safe_key}.json"
            
            # Check if file exists
            file_info = self.file_manager.get_file_info(file_path)
            if not file_info.exists:
                return None
            
            # Check if file is expired
            if self._is_cache_expired(file_info.modified):
                return None
            
            # Load and parse article data
            article_data = self.file_manager.read_json(file_path)
            
            # Remove metadata fields that aren't part of Article
            article_data.pop('cached_timestamp', None)
            article_data.pop('cache_version', None)
            
            return Article(**article_data)
            
        except Exception:
            return None
    
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
        try:
            safe_key = self._make_safe_filename(key)
            file_path = f"{safe_key}.json"
            
            # Convert article to dict and add metadata
            from dataclasses import asdict
            article_data = asdict(article)
            article_data['cached_timestamp'] = datetime.now().isoformat()
            article_data['cache_version'] = '2.0'
            article_data['ttl_hours'] = ttl_hours
            
            # Save to file
            self.file_manager.write_json(file_path, article_data)
            
            return True
            
        except Exception:
            return False
    
    async def cache_batch(self, articles: List[Article], prefix: str = "") -> int:
        """
        Cache multiple articles
        
        Args:
            articles: Articles to cache
            prefix: Optional prefix for cache keys
            
        Returns:
            Number of articles successfully cached
        """
        cached_count = 0
        
        for article in articles:
            cache_key = f"{prefix}{article.title}" if prefix else article.title
            if await self.cache_article(cache_key, article):
                cached_count += 1
        
        return cached_count
    
    async def get_cache_stats(self) -> Dict[str, Union[int, float]]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            # Get all JSON files in cache directory (excluding batch files)
            cache_files = self.file_manager.list_files(".", "*.json")
            article_files = [
                f for f in cache_files 
                if not f.name.startswith(('trending_', 'featured_'))
            ]
            
            trending_files = [f for f in cache_files if f.name.startswith('trending_')]
            featured_files = [f for f in cache_files if f.name.startswith('featured_')]
            
            # Calculate total size
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                'total_articles': len(article_files),
                'trending_batches': len(trending_files),
                'featured_batches': len(featured_files),
                'total_size_mb': total_size / (1024 * 1024),
                'cache_directory': str(self.file_manager.base_path)
            }
            
        except Exception:
            return {
                'total_articles': 0,
                'trending_batches': 0,
                'featured_batches': 0,
                'total_size_mb': 0.0,
                'cache_directory': str(self.file_manager.base_path)
            }
    
    async def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear cached articles
        
        Args:
            older_than_days: Only clear items older than this many days
            
        Returns:
            Number of items cleared
        """
        try:
            cache_files = self.file_manager.list_files(".", "*.json")
            
            if older_than_days is None:
                # Clear all cache files
                deleted_count = 0
                for file_path in cache_files:
                    if self.file_manager.delete_file(file_path):
                        deleted_count += 1
                return deleted_count
            else:
                # Clear only old files
                cutoff_date = datetime.now() - timedelta(days=older_than_days)
                deleted_count = 0
                
                for file_path in cache_files:
                    file_info = self.file_manager.get_file_info(file_path)
                    if file_info.exists and file_info.modified < cutoff_date:
                        if self.file_manager.delete_file(file_path):
                            deleted_count += 1
                
                return deleted_count
                
        except Exception:
            return 0
    
    def _make_safe_filename(self, title: str) -> str:
        """Convert article title to safe filename"""
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        safe_title = re.sub(r'[^\w\s-]', '', safe_title)
        safe_title = re.sub(r'\s+', '_', safe_title)
        return safe_title[:100]  # Limit length
    
    def _is_cache_expired(self, file_modified: datetime) -> bool:
        """Check if cached file is expired"""
        cache_age = datetime.now() - file_modified
        return cache_age.total_seconds() > (self.config.default_ttl_hours * 3600)


class ConsoleInteractiveSelector(InteractiveSelector):
    """Console-based interactive article selector"""
    
    async def select_from_suggestions(self, query: str, suggestions: List[ArticleSuggestion]) -> Optional[str]:
        """
        Allow user to interactively select from suggestions
        
        Args:
            query: Original search query
            suggestions: List of article suggestions
            
        Returns:
            Selected article title or None if cancelled
        """
        if not suggestions:
            print(f"❌ No suggestions found for '{query}'")
            return None
        
        # Display suggestions
        self.display_suggestions(query, suggestions)
        
        # Get user selection
        while True:
            try:
                choice = input(f"Select article (0-{len(suggestions)}): ").strip()
                
                if choice == '0':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(suggestions):
                    selected = suggestions[choice_num - 1]
                    print(f"✅ Selected: {selected.title}")
                    return selected.title
                else:
                    print(f"Please enter a number between 0 and {len(suggestions)}")
            
            except ValueError:
                print("Please enter a valid number")
            except KeyboardInterrupt:
                print("\n❌ Cancelled")
                return None
    
    def display_suggestions(self, query: str, suggestions: List[ArticleSuggestion]) -> None:
        """
        Display suggestions to user
        
        Args:
            query: Original search query
            suggestions: List of suggestions to display
        """
        print(f"\n🔍 Found {len(suggestions)} possible matches for '{query}':")
        print("=" * 60)
        
        for i, suggestion in enumerate(suggestions, 1):
            similarity_bar = "█" * int(suggestion.similarity_score * 10) + "░" * (10 - int(suggestion.similarity_score * 10))
            disambiguation_marker = " [DISAMBIGUATION]" if suggestion.is_disambiguation else ""
            
            print(f"{i:2}. {suggestion.title}{disambiguation_marker}")
            print(f"    Match: {similarity_bar} ({suggestion.similarity_score:.2f})")
            if suggestion.snippet:
                snippet_clean = suggestion.snippet[:100] + "..." if len(suggestion.snippet) > 100 else suggestion.snippet
                print(f"    Info: {snippet_clean}")
            print()
        
        print("0. ❌ None of these / Cancel")
        print("=" * 60)


# Convenience factory functions
def create_content_processor() -> WikipediaContentProcessor:
    """Create Wikipedia content processor"""
    return WikipediaContentProcessor()


def create_content_validator(processor: Optional[WikipediaContentProcessor] = None) -> WikipediaContentValidator:
    """Create Wikipedia content validator"""
    if processor is None:
        processor = create_content_processor()
    return WikipediaContentValidator(processor)


def create_file_cache(cache_dir: Optional[str] = None) -> FileBasedContentCache:
    """Create file-based content cache"""
    return FileBasedContentCache(cache_dir)


def create_console_selector() -> ConsoleInteractiveSelector:
    """Create console-based interactive selector"""
    return ConsoleInteractiveSelector()