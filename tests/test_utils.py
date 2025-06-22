#!/usr/bin/env python3
"""
Test Utilities and Helper Functions
Common utilities used across test files
"""

import unittest
import tempfile
import shutil
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch
from dataclasses import asdict

# Import test configuration
from . import TEST_CONFIG, MOCK_ARTICLE_DATA, MOCK_SCRIPT_DATA

# Import application modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from content_fetcher import WikipediaArticle
from script_formatter import PodcastScript

class BaseTestCase(unittest.TestCase):
    """Base test case with common setup and utilities"""
    
    def setUp(self):
        """Set up common test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix=TEST_CONFIG['temp_dir_prefix']))
        
        # Set up mock environment
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': TEST_CONFIG['mock_api_key']
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up common test fixtures"""
        self.env_patcher.stop()
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_mock_article(self, **kwargs):
        """Create a mock WikipediaArticle with optional overrides"""
        data = {**MOCK_ARTICLE_DATA, **kwargs}
        return WikipediaArticle(**data)
    
    def create_mock_script(self, **kwargs):
        """Create a mock PodcastScript with optional overrides"""
        data = {**MOCK_SCRIPT_DATA, **kwargs}
        return PodcastScript(**data)
    
    def save_test_article(self, article, filename):
        """Save a test article to temporary directory"""
        file_path = self.temp_dir / f"{filename}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(article), f, indent=2)
        
        return file_path
    
    def save_test_script(self, script, style_dir, filename):
        """Save a test script to temporary directory"""
        style_path = self.temp_dir / style_dir
        style_path.mkdir(exist_ok=True)
        
        file_path = style_path / f"{filename}.json"
        
        script_data = asdict(script)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, indent=2)
        
        return file_path
    
    def assertFileExists(self, file_path):
        """Assert that a file exists"""
        self.assertTrue(Path(file_path).exists(), f"File does not exist: {file_path}")
    
    def assertFileNotExists(self, file_path):
        """Assert that a file does not exist"""
        self.assertFalse(Path(file_path).exists(), f"File should not exist: {file_path}")
    
    def assertDirExists(self, dir_path):
        """Assert that a directory exists"""
        self.assertTrue(Path(dir_path).is_dir(), f"Directory does not exist: {dir_path}")
    
    def assertJSONFileContains(self, file_path, expected_data):
        """Assert that a JSON file contains expected data"""
        self.assertFileExists(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            actual_data = json.load(f)
        
        for key, expected_value in expected_data.items():
            self.assertIn(key, actual_data, f"Key '{key}' not found in JSON file")
            self.assertEqual(actual_data[key], expected_value, 
                           f"Value mismatch for key '{key}'")

class MockAPIResponses:
    """Mock API responses for testing"""
    
    @staticmethod
    def wikipedia_page_info(title="Test Article"):
        """Mock Wikipedia page info response"""
        return {
            'query': {
                'pages': {
                    '123': {
                        'title': title,
                        'extract': f'This is a summary of {title}.',
                        'timestamp': '2024-01-01T12:00:00Z'
                    }
                }
            }
        }
    
    @staticmethod
    def wikipedia_page_content(title="Test Article"):
        """Mock Wikipedia page content response"""
        return {
            'query': {
                'pages': {
                    '123': {
                        'extract': f'This is the full content of {title}. ' * 100
                    }
                }
            }
        }
    
    @staticmethod
    def wikipedia_search_results(query="test"):
        """Mock Wikipedia search results"""
        return {
            'query': {
                'search': [
                    {
                        'title': f'{query.title()} Article',
                        'snippet': f'This is a snippet about {query}'
                    },
                    {
                        'title': f'{query.title()} (disambiguation)',
                        'snippet': f'Disambiguation page for {query}'
                    }
                ]
            }
        }
    
    @staticmethod
    def wikipedia_trending():
        """Mock Wikipedia trending articles response"""
        return {
            'items': [{
                'articles': [
                    {'article': 'Trending_Article_1', 'views': 10000},
                    {'article': 'Trending_Article_2', 'views': 8000},
                    {'article': 'Trending_Article_3', 'views': 6000}
                ]
            }]
        }
    
    @staticmethod
    def openai_chat_completion(content="Generated script content here."):
        """Mock OpenAI chat completion response"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = content
        return mock_response

class TestDataGenerator:
    """Generates test data for various scenarios"""
    
    @staticmethod
    def create_long_article(word_count=5000):
        """Create an article with specific word count"""
        base_sentence = "This is a test sentence for a long article. "
        words_per_sentence = len(base_sentence.split())
        sentences_needed = word_count // words_per_sentence
        
        content = base_sentence * sentences_needed
        
        return WikipediaArticle(
            title="Long Test Article",
            url="https://en.wikipedia.org/wiki/Long_Test_Article",
            content=content,
            summary="This is a very long test article.",
            categories=["Test", "Long Articles"],
            page_views=5000,
            last_modified="2024-01-01",
            references=["https://example.com"],
            images=["long_test.jpg"],
            word_count=word_count,
            quality_score=0.8
        )
    
    @staticmethod
    def create_article_with_special_chars():
        """Create an article with special characters in title"""
        return WikipediaArticle(
            title="Article/With\\Special:Characters*<>|?\"",
            url="https://en.wikipedia.org/wiki/Special_Chars",
            content="This article has special characters in its title.",
            summary="Special character test",
            categories=["Test", "Special Characters"],
            page_views=100,
            last_modified="2024-01-01",
            references=[],
            images=[],
            word_count=10,
            quality_score=0.5
        )
    
    @staticmethod
    def create_multiple_articles(count=5):
        """Create multiple test articles"""
        articles = []
        for i in range(count):
            article = WikipediaArticle(
                title=f"Test Article {i+1}",
                url=f"https://en.wikipedia.org/wiki/Test_Article_{i+1}",
                content=f"This is test content for article {i+1}. " * 50,
                summary=f"Summary for test article {i+1}",
                categories=[f"Category {i+1}", "Test"],
                page_views=1000 * (i+1),
                last_modified="2024-01-01",
                references=[f"https://example.com/ref{i+1}"],
                images=[f"test{i+1}.jpg"],
                word_count=50 + (i * 10),
                quality_score=0.5 + (i * 0.1)
            )
            articles.append(article)
        
        return articles

class APITestMixin:
    """Mixin for testing API interactions"""
    
    def setUp_api_mocks(self):
        """Set up common API mocks"""
        # Wikipedia API mocks
        self.wikipedia_get_patcher = patch('requests.get')
        self.mock_wikipedia_get = self.wikipedia_get_patcher.start()
        
        # OpenAI API mocks
        self.openai_patcher = patch('openai.OpenAI')
        self.mock_openai_class = self.openai_patcher.start()
        self.mock_openai_client = Mock()
        self.mock_openai_class.return_value = self.mock_openai_client
        
        return self.mock_wikipedia_get, self.mock_openai_client
    
    def tearDown_api_mocks(self):
        """Clean up API mocks"""
        self.wikipedia_get_patcher.stop()
        self.openai_patcher.stop()
    
    def setup_wikipedia_success_response(self, title="Test Article"):
        """Set up successful Wikipedia API response"""
        mock_response = Mock()
        mock_response.json.return_value = MockAPIResponses.wikipedia_page_info(title)
        mock_response.raise_for_status.return_value = None
        self.mock_wikipedia_get.return_value = mock_response
    
    def setup_wikipedia_not_found_response(self):
        """Set up Wikipedia API not found response"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'query': {
                'pages': {
                    '-1': {'missing': True}
                }
            }
        }
        self.mock_wikipedia_get.return_value = mock_response
    
    def setup_openai_success_response(self, content="Generated content"):
        """Set up successful OpenAI API response"""
        mock_response = MockAPIResponses.openai_chat_completion(content)
        self.mock_openai_client.chat.completions.create.return_value = mock_response

def skip_if_no_internet():
    """Decorator to skip tests if no internet connection"""
    def decorator(test_func):
        def wrapper(*args, **kwargs):
            try:
                import requests
                requests.get('https://www.google.com', timeout=5)
                return test_func(*args, **kwargs)
            except:
                import unittest
                raise unittest.SkipTest("No internet connection available")
        return wrapper
    return decorator

def skip_if_no_integration_flag():
    """Decorator to skip tests if integration flag not set"""
    def decorator(test_func):
        def wrapper(*args, **kwargs):
            if not TEST_CONFIG['integration_tests_enabled']:
                import unittest
                raise unittest.SkipTest("Integration tests disabled (set RUN_INTEGRATION_TESTS=1)")
            return test_func(*args, **kwargs)
        return wrapper
    return decorator

# Test utilities for assertions
def assert_valid_wikipedia_article(test_case, article):
    """Assert that an object is a valid WikipediaArticle"""
    test_case.assertIsInstance(article, WikipediaArticle)
    test_case.assertIsInstance(article.title, str)
    test_case.assertGreater(len(article.title), 0)
    test_case.assertIsInstance(article.word_count, int)
    test_case.assertGreaterEqual(article.word_count, 0)
    test_case.assertIsInstance(article.quality_score, (int, float))
    test_case.assertGreaterEqual(article.quality_score, 0)
    test_case.assertLessEqual(article.quality_score, 1)

def assert_valid_podcast_script(test_case, script):
    """Assert that an object is a valid PodcastScript"""
    test_case.assertIsInstance(script, PodcastScript)
    test_case.assertIsInstance(script.title, str)
    test_case.assertGreater(len(script.title), 0)
    test_case.assertIsInstance(script.style, str)
    test_case.assertIn(script.style, ['conversational', 'academic', 'storytelling', 'news_report', 'documentary', 'comedy', 'interview', 'kids_educational'])
    test_case.assertIsInstance(script.word_count, int)
    test_case.assertGreater(script.word_count, 0)
    test_case.assertIsInstance(script.estimated_duration, int)
    test_case.assertGreater(script.estimated_duration, 0)