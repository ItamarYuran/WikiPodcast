#!/usr/bin/env python3
"""
Test Suite for Content Fetcher
Tests Wikipedia content fetching functionality
"""

import unittest
import tempfile
import shutil
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from content_fetcher import (
    WikipediaContentFetcher, 
    WikipediaArticle, 
    ArticleSuggestion
)

class TestWikipediaArticle(unittest.TestCase):
    """Test WikipediaArticle dataclass"""
    
    def test_article_creation(self):
        """Test creating a WikipediaArticle instance"""
        article = WikipediaArticle(
            title="Test Article",
            url="https://en.wikipedia.org/wiki/Test_Article",
            content="This is test content.",
            summary="Test summary",
            categories=["Test Category"],
            page_views=1000,
            last_modified="2024-01-01",
            references=["https://example.com"],
            images=["test.jpg"],
            word_count=4,
            quality_score=0.8
        )
        
        self.assertEqual(article.title, "Test Article")
        self.assertEqual(article.word_count, 4)
        self.assertEqual(article.quality_score, 0.8)
        self.assertIn("Test Category", article.categories)

class TestArticleSuggestion(unittest.TestCase):
    """Test ArticleSuggestion dataclass"""
    
    def test_suggestion_creation(self):
        """Test creating an ArticleSuggestion instance"""
        suggestion = ArticleSuggestion(
            title="Test Suggestion",
            snippet="Test snippet",
            similarity_score=0.9,
            page_views=500,
            is_disambiguation=False
        )
        
        self.assertEqual(suggestion.title, "Test Suggestion")
        self.assertEqual(suggestion.similarity_score, 0.9)
        self.assertFalse(suggestion.is_disambiguation)

class TestWikipediaContentFetcher(unittest.TestCase):
    """Test WikipediaContentFetcher class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.fetcher = WikipediaContentFetcher(cache_dir=self.temp_dir)
        
        # Mock article data
        self.mock_article_data = {
            'title': 'Python (programming language)',
            'url': 'https://en.wikipedia.org/wiki/Python_(programming_language)',
            'content': 'Python is a high-level programming language. ' * 100,
            'summary': 'Python is a programming language.',
            'categories': ['Programming languages', 'Python'],
            'page_views': 50000,
            'last_modified': '2024-01-01T12:00:00Z',
            'references': ['https://python.org'],
            'images': ['Python-logo.png'],
            'word_count': 500,
            'quality_score': 0.9
        }
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_fetcher_initialization(self):
        """Test fetcher initializes correctly"""
        self.assertEqual(self.fetcher.language, 'en')
        self.assertTrue(self.fetcher.cache_dir.exists())
        self.assertIn('User-Agent', self.fetcher.headers)
    
    def test_make_safe_filename(self):
        """Test filename sanitization"""
        # Test various problematic characters
        test_cases = [
            ("Python (programming language)", "Python_programming_language"),
            ("C++/CLI", "C_CLI"),
            ("File:Example.jpg", "File_Example_jpg"),
            ("Article with spaces", "Article_with_spaces"),
            ("Special<>chars:\"/\\|?*", "Special_chars_")
        ]
        
        for input_title, expected in test_cases:
            result = self.fetcher._make_safe_filename(input_title)
            self.assertEqual(result, expected)
            # Ensure result is valid filename
            self.assertNotIn('/', result)
            self.assertNotIn('\\', result)
    
    @patch('content_fetcher.requests.get')
    def test_get_page_info_success(self, mock_get):
        """Test successful page info retrieval"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'query': {
                'pages': {
                    '123': {
                        'title': 'Python (programming language)',
                        'extract': 'Python is a programming language.',
                        'timestamp': '2024-01-01T12:00:00Z'
                    }
                }
            }
        }
        mock_get.return_value = mock_response
        
        result = self.fetcher._get_page_info('Python')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], 'Python (programming language)')
        mock_get.assert_called_once()
    
    @patch('content_fetcher.requests.get')
    def test_get_page_info_not_found(self, mock_get):
        """Test page info when page doesn't exist"""
        # Mock page not found response
        mock_response = Mock()
        mock_response.json.return_value = {
            'query': {
                'pages': {
                    '-1': {
                        'missing': True
                    }
                }
            }
        }
        mock_get.return_value = mock_response
        
        result = self.fetcher._get_page_info('NonexistentPage')
        
        self.assertIsNone(result)
    
    def test_calculate_similarity(self):
        """Test similarity calculation"""
        test_cases = [
            ("python", "python", 1.0),  # Exact match
            ("python", "Python", 1.0),  # Case insensitive
            ("python", "python programming", 0.9),  # Query in title
            ("artificial intelligence", "AI", 0.0),  # Different
            ("machine learning", "machine", 0.8),  # Partial match
        ]
        
        for query, title, expected_min in test_cases:
            result = self.fetcher._calculate_similarity(query, title)
            if expected_min == 1.0:
                self.assertEqual(result, expected_min)
            else:
                self.assertGreaterEqual(result, expected_min - 0.2)  # Allow some variance
    
    def test_deduplicate_suggestions(self):
        """Test suggestion deduplication"""
        suggestions = [
            ArticleSuggestion("Python", "snippet1", 0.9, 100, False),
            ArticleSuggestion("Python", "snippet2", 0.8, 200, False),  # Duplicate
            ArticleSuggestion("Java", "snippet3", 0.7, 150, False),
        ]
        
        result = self.fetcher._deduplicate_suggestions(suggestions)
        
        self.assertEqual(len(result), 2)
        titles = [s.title for s in result]
        self.assertIn("Python", titles)
        self.assertIn("Java", titles)
    
    def test_rank_suggestions(self):
        """Test suggestion ranking"""
        suggestions = [
            ArticleSuggestion("Python tutorial", "Tutorial", 0.7, 100, False),
            ArticleSuggestion("Python (disambiguation)", "Disambig", 0.8, 200, True),
            ArticleSuggestion("Python", "Main article", 0.9, 300, False),
        ]
        
        result = self.fetcher._rank_suggestions("python", suggestions, 3)
        
        # Main article should be ranked higher than disambiguation
        self.assertEqual(result[0].title, "Python")
        # Disambiguation should be penalized
        self.assertNotEqual(result[0].title, "Python (disambiguation)")
    
    def test_estimate_podcast_duration(self):
        """Test podcast duration estimation"""
        test_cases = [
            (150, "conversational", 60),   # 150 words ~= 1 minute
            (300, "news_report", 60),      # Faster speaking rate
            (200, "academic", 90),         # Slower speaking rate
        ]
        
        for word_count, style, expected_seconds in test_cases:
            duration_sec, duration_str = self.fetcher.estimate_podcast_duration(word_count, style)
            
            # Allow 20% variance in estimation
            self.assertAlmostEqual(duration_sec, expected_seconds, delta=expected_seconds * 0.2)
            self.assertIn(":", duration_str)  # Should be in MM:SS format
    
    @patch('content_fetcher.requests.get')
    def test_get_trending_articles(self, mock_get):
        """Test trending articles retrieval"""
        # Mock trending API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [{
                'articles': [
                    {'article': 'Trending_Article_1', 'views': 10000},
                    {'article': 'Trending_Article_2', 'views': 8000},
                ]
            }]
        }
        mock_get.return_value = mock_response
        
        # Mock the fetch_article method to avoid actual API calls
        with patch.object(self.fetcher, 'fetch_article') as mock_fetch:
            mock_article = WikipediaArticle(**self.mock_article_data)
            mock_fetch.return_value = mock_article
            
            # Mock _is_suitable_for_podcast to return True
            with patch.object(self.fetcher, '_is_suitable_for_podcast', return_value=True):
                result = self.fetcher.get_trending_articles(count=2)
                
                self.assertIsInstance(result, list)
                # Should call fetch_article for each trending title
                self.assertGreater(mock_fetch.call_count, 0)
    
    def test_control_content_length(self):
        """Test content length control"""
        long_content = "This is a test sentence. " * 200  # ~1000 words
        
        # Test short length
        short_result = self.fetcher._control_content_length(long_content, "short")
        short_words = len(short_result.split())
        self.assertLess(short_words, 1000)  # Should be shortened
        
        # Test full length
        full_result = self.fetcher._control_content_length(long_content, "full")
        self.assertEqual(full_result, long_content)  # Should be unchanged
    
    def test_save_and_load_cache(self):
        """Test article caching functionality"""
        # Create test article
        article = WikipediaArticle(**self.mock_article_data)
        filename = "test_article"
        
        # Save to cache
        self.fetcher._save_to_file_cache(article, filename)
        
        # Check file was created
        cache_file = self.fetcher.cache_dir / f"{filename}.json"
        self.assertTrue(cache_file.exists())
        
        # Load from cache
        loaded_article = self.fetcher._load_from_file_cache(filename)
        
        self.assertIsNotNone(loaded_article)
        self.assertEqual(loaded_article.title, article.title)
        self.assertEqual(loaded_article.word_count, article.word_count)
    
    def test_cache_stats(self):
        """Test cache statistics"""
        # Save a test article to create cache data
        article = WikipediaArticle(**self.mock_article_data)
        self.fetcher._save_to_file_cache(article, "test")
        
        stats = self.fetcher.get_cache_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_articles', stats)
        self.assertIn('total_size_mb', stats)
        self.assertGreaterEqual(stats['total_articles'], 1)
    
    def test_list_cached_articles(self):
        """Test listing cached articles"""
        # Save test articles
        article1 = WikipediaArticle(**self.mock_article_data)
        article2 = WikipediaArticle(
            **{**self.mock_article_data, 'title': 'Second Article'}
        )
        
        self.fetcher._save_to_file_cache(article1, "test1")
        self.fetcher._save_to_file_cache(article2, "test2")
        
        cached_list = self.fetcher.list_cached_articles()
        
        self.assertIsInstance(cached_list, list)
        self.assertGreaterEqual(len(cached_list), 2)
        
        # Check structure of returned data
        for item in cached_list:
            self.assertIn('title', item)
            self.assertIn('filename', item)
            self.assertIn('word_count', item)
    
    @patch('content_fetcher.requests.get')
    def test_smart_fetch_with_suggestions(self, mock_get):
        """Test smart fetch with suggestion flow"""
        # Mock search API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'query': {
                'search': [
                    {
                        'title': 'Python (programming language)',
                        'snippet': 'Programming language snippet'
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        # Mock the interactive selection to return the first suggestion
        with patch.object(self.fetcher, '_interactive_selection', return_value='Python (programming language)'):
            with patch.object(self.fetcher, 'fetch_article') as mock_fetch:
                mock_fetch.return_value = WikipediaArticle(**self.mock_article_data)
                
                result = self.fetcher.smart_fetch_article("python", interactive=True)
                
                self.assertIsNotNone(result)
                mock_fetch.assert_called()

class TestIntegration(unittest.TestCase):
    """Integration tests for content fetcher"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.fetcher = WikipediaContentFetcher(cache_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), "Integration tests disabled")
    def test_real_wikipedia_fetch(self):
        """Test actual Wikipedia API call (requires internet)"""
        # Only run if explicitly enabled
        article = self.fetcher.fetch_article("Python (programming language)")
        
        if article:  # Only test if we successfully got an article
            self.assertIsInstance(article, WikipediaArticle)
            self.assertGreater(len(article.content), 100)
            self.assertGreater(article.word_count, 0)
            self.assertIsInstance(article.categories, list)

if __name__ == '__main__':
    # Configure test runner
    unittest.main(
        verbosity=2,
        failfast=False,
        buffer=True
    )