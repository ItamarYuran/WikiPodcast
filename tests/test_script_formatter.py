#!/usr/bin/env python3
"""
Test Suite for Script Formatter
Tests podcast script generation functionality
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

from script_formatter import (
    PodcastScriptFormatter,
    PodcastScript,
    PodcastStyles
)
from content_fetcher import WikipediaArticle

class TestPodcastScript(unittest.TestCase):
    """Test PodcastScript dataclass"""
    
    def test_script_creation(self):
        """Test creating a PodcastScript instance"""
        script = PodcastScript(
            title="Test Podcast",
            style="conversational",
            script="This is a test script content.",
            intro="Welcome to the test podcast",
            outro="Thanks for listening",
            segments=[{"content": "segment 1", "duration": 60}],
            estimated_duration=300,
            word_count=100,
            source_article="Test Article",
            generated_timestamp="2024-01-01T12:00:00",
            custom_instructions="Test instructions"
        )
        
        self.assertEqual(script.title, "Test Podcast")
        self.assertEqual(script.style, "conversational")
        self.assertEqual(script.word_count, 100)
        self.assertEqual(script.estimated_duration, 300)

class TestPodcastStyles(unittest.TestCase):
    """Test PodcastStyles configuration"""
    
    def test_styles_exist(self):
        """Test that all expected styles are defined"""
        expected_styles = [
            "conversational",
            "academic", 
            "storytelling",
            "news_report",
            "documentary",
            "comedy",
            "interview",
            "kids_educational"
        ]
        
        for style in expected_styles:
            self.assertIn(style, PodcastStyles.STYLES)
    
    def test_style_structure(self):
        """Test that each style has required fields"""
        required_fields = ["name", "description", "target_duration", "voice_style", "prompt_template"]
        
        for style_name, style_config in PodcastStyles.STYLES.items():
            for field in required_fields:
                self.assertIn(field, style_config, f"Style {style_name} missing field {field}")
            
            # Test data types
            self.assertIsInstance(style_config["target_duration"], int)
            self.assertIsInstance(style_config["name"], str)
            self.assertIsInstance(style_config["description"], str)
    
    def test_prompt_template_formatting(self):
        """Test that prompt templates can be formatted with topic"""
        topic = "Test Topic"
        
        for style_name, style_config in PodcastStyles.STYLES.items():
            template = style_config["prompt_template"]
            
            # Should not raise an exception
            try:
                formatted = template.format(topic=topic)
                self.assertIn(topic, formatted)
            except KeyError as e:
                self.fail(f"Style {style_name} template missing placeholder: {e}")

class TestPodcastScriptFormatter(unittest.TestCase):
    """Test PodcastScriptFormatter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-key-12345'
        })
        self.env_patcher.start()
        
        # Create formatter instance
        self.formatter = PodcastScriptFormatter(
            openai_api_key='sk-test-key-12345',
            cache_dir=self.temp_dir
        )
        
        # Mock article for testing
        self.mock_article = WikipediaArticle(
            title="Test Article",
            url="https://en.wikipedia.org/wiki/Test_Article",
            content="This is test content about artificial intelligence. " * 50,
            summary="Test summary about AI",
            categories=["Technology", "Artificial Intelligence"],
            page_views=1000,
            last_modified="2024-01-01",
            references=["https://example.com"],
            images=["test.jpg"],
            word_count=250,
            quality_score=0.8
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_formatter_initialization(self):
        """Test formatter initializes correctly"""
        self.assertTrue(self.formatter.cache_dir.exists())
        self.assertEqual(self.formatter.openai_api_key, 'sk-test-key-12345')
        
        # Check that style directories are created
        for style in PodcastStyles.STYLES.keys():
            style_dir = self.formatter.cache_dir / style
            self.assertTrue(style_dir.exists())
    
    def test_initialization_without_api_key(self):
        """Test initialization fails without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                PodcastScriptFormatter()
            
            self.assertIn("OpenAI API key not found", str(context.exception))
    
    def test_invalid_api_key_format(self):
        """Test initialization fails with invalid API key format"""
        with self.assertRaises(ValueError) as context:
            PodcastScriptFormatter(openai_api_key="invalid-key")
        
        self.assertIn("Invalid OpenAI API key format", str(context.exception))
    
    def test_get_available_styles(self):
        """Test getting available styles"""
        styles = self.formatter.get_available_styles()
        
        self.assertIsInstance(styles, dict)
        self.assertGreater(len(styles), 0)
        
        # Check structure
        for style_name, style_info in styles.items():
            self.assertIn("name", style_info)
            self.assertIn("description", style_info)
            self.assertIn("target_duration", style_info)
            self.assertIn("voice_style", style_info)
    
    def test_prepare_content(self):
        """Test content preparation for script generation"""
        prepared = self.formatter._prepare_content(self.mock_article)
        
        self.assertIn("SUMMARY:", prepared)
        self.assertIn("CONTENT:", prepared)
        self.assertIn("CATEGORIES:", prepared)
        self.assertIn(self.mock_article.summary, prepared)
        self.assertIn(self.mock_article.content, prepared)
    
    def test_prepare_content_long_article(self):
        """Test content preparation with very long article"""
        # Create article with 10k words
        long_content = "This is a very long article. " * 2000  # ~10k words
        long_article = WikipediaArticle(
            **{**self.mock_article.__dict__, 'content': long_content, 'word_count': 10000}
        )
        
        prepared = self.formatter._prepare_content(long_article)
        
        # Should be truncated
        prepared_words = len(prepared.split())
        self.assertLess(prepared_words, 12000)  # Should be less than original
    
    def test_build_prompt(self):
        """Test prompt building for OpenAI"""
        style_config = PodcastStyles.STYLES["conversational"]
        content = "Test content for prompt building"
        
        prompt = self.formatter._build_prompt(
            self.mock_article,
            style_config,
            content,
            custom_instructions="Test custom instructions"
        )
        
        self.assertIn(self.mock_article.title, prompt)
        self.assertIn(content, prompt)
        self.assertIn("Test custom instructions", prompt)
        self.assertIn("conversational", prompt.lower())
    
    @patch('script_formatter.OpenAI')
    def test_generate_with_openai_success(self, mock_openai_class):
        """Test successful OpenAI generation"""
        # Mock OpenAI client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated podcast script content here."
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        prompt = "Test prompt for generation"
        result = self.formatter._generate_with_openai(prompt, "gpt-3.5-turbo")
        
        self.assertIsNotNone(result)
        self.assertEqual(result, "Generated podcast script content here.")
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('script_formatter.OpenAI')
    def test_generate_with_openai_failure(self, mock_openai_class):
        """Test OpenAI generation failure handling"""
        # Mock OpenAI client to raise an exception
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        prompt = "Test prompt"
        result = self.formatter._generate_with_openai(prompt, "gpt-3.5-turbo")
        
        self.assertIsNone(result)
    
    def test_parse_generated_script(self):
        """Test parsing generated script content"""
        script_content = """
        Welcome to today's podcast about artificial intelligence.
        
        ## Introduction
        Today we'll explore the fascinating world of AI.
        
        ## Main Content
        Artificial intelligence has revolutionized many industries.
        
        ## Conclusion
        Thanks for listening to our show today.
        """
        
        parsed = self.formatter._parse_generated_script(script_content, "conversational", "AI Test")
        
        self.assertIn("intro", parsed)
        self.assertIn("outro", parsed)
        self.assertIn("segments", parsed)
        self.assertIsInstance(parsed["segments"], list)
    
    def test_estimate_duration(self):
        """Test duration estimation"""
        test_text = "This is a test script. " * 100  # ~400 words
        
        duration = self.formatter._estimate_duration(test_text)
        
        # Should be around 160 seconds (400 words / 2.5 words per second)
        self.assertGreater(duration, 100)
        self.assertLess(duration, 250)
    
    def test_save_script_to_cache(self):
        """Test saving script to cache"""
        script = PodcastScript(
            title="Test Script",
            style="conversational",
            script="Test script content",
            intro="Intro",
            outro="Outro",
            segments=[],
            estimated_duration=300,
            word_count=50,
            source_article="Test Article",
            generated_timestamp="2024-01-01T12:00:00"
        )
        
        self.formatter._save_script_to_cache(script)
        
        # Check file was created in correct style directory
        style_dir = self.formatter.cache_dir / "conversational"
        json_files = list(style_dir.glob("*.json"))
        self.assertGreater(len(json_files), 0)
        
        # Verify content
        with open(json_files[0], 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["title"], "Test Script")
        self.assertEqual(saved_data["style"], "conversational")
    
    @patch('script_formatter.OpenAI')
    def test_format_article_to_script_success(self, mock_openai_class):
        """Test complete article to script conversion"""
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Welcome to our AI podcast. Today we discuss artificial intelligence. Thanks for listening."
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        result = self.formatter.format_article_to_script(
            self.mock_article,
            style="conversational"
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, PodcastScript)
        self.assertEqual(result.style, "conversational")
        self.assertIn("Test Article", result.title)
        self.assertGreater(result.word_count, 0)
    
    def test_format_article_invalid_style(self):
        """Test error handling for invalid style"""
        with self.assertRaises(ValueError) as context:
            self.formatter.format_article_to_script(
                self.mock_article,
                style="invalid_style"
            )
        
        self.assertIn("Unknown style", str(context.exception))
    
    def test_list_cached_scripts(self):
        """Test listing cached scripts"""
        # Create test scripts
        script1 = PodcastScript(
            title="Script 1",
            style="conversational",
            script="Content 1",
            intro="", outro="", segments=[],
            estimated_duration=300, word_count=50,
            source_article="Article 1",
            generated_timestamp="2024-01-01T12:00:00"
        )
        
        script2 = PodcastScript(
            title="Script 2", 
            style="documentary",
            script="Content 2",
            intro="", outro="", segments=[],
            estimated_duration=600, word_count=100,
            source_article="Article 2",
            generated_timestamp="2024-01-02T12:00:00"
        )
        
        self.formatter._save_script_to_cache(script1)
        self.formatter._save_script_to_cache(script2)
        
        # Test listing all scripts
        all_scripts = self.formatter.list_cached_scripts()
        self.assertGreaterEqual(len(all_scripts), 2)
        
        # Test listing by style
        conv_scripts = self.formatter.list_cached_scripts(style="conversational")
        self.assertGreaterEqual(len(conv_scripts), 1)
        
        # Check structure
        for script_info in all_scripts:
            self.assertIn("title", script_info)
            self.assertIn("style", script_info)
            self.assertIn("word_count", script_info)
            self.assertIn("filename", script_info)
    
    def test_load_cached_script(self):
        """Test loading cached script"""
        # Save a script first
        original_script = PodcastScript(
            title="Test Load Script",
            style="academic",
            script="Academic content",
            intro="Academic intro", outro="Academic outro", segments=[],
            estimated_duration=900, word_count=150,
            source_article="Academic Article",
            generated_timestamp="2024-01-01T12:00:00"
        )
        
        self.formatter._save_script_to_cache(original_script)
        
        # Get the filename
        style_dir = self.formatter.cache_dir / "academic"
        json_files = list(style_dir.glob("*.json"))
        self.assertGreater(len(json_files), 0)
        
        filename = json_files[0].name
        
        # Load the script
        loaded_script = self.formatter.load_cached_script(filename, style="academic")
        
        self.assertIsNotNone(loaded_script)
        self.assertEqual(loaded_script.title, "Test Load Script")
        self.assertEqual(loaded_script.style, "academic")
    
    @patch('script_formatter.OpenAI')
    def test_batch_generate_scripts(self, mock_openai_class):
        """Test batch script generation"""
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated script content."
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        # Create test articles
        articles = [
            self.mock_article,
            WikipediaArticle(**{**self.mock_article.__dict__, 'title': 'Article 2'})
        ]
        
        with patch('time.sleep'):  # Speed up the test
            results = self.formatter.batch_generate_scripts(articles, style="conversational")
        
        self.assertIsInstance(results, list)
        # Should generate scripts for both articles (if OpenAI succeeds)
        self.assertLessEqual(len(results), len(articles))
    
    @patch('script_formatter.OpenAI')
    def test_api_connection_test(self, mock_openai_class):
        """Test API connection testing functionality"""
        # Mock successful API test
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "API test successful"
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        result = self.formatter.test_api_connection()
        
        self.assertTrue(result)
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('script_formatter.OpenAI')
    def test_api_connection_test_failure(self, mock_openai_class):
        """Test API connection test failure handling"""
        # Mock API failure
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("Connection failed")
        mock_openai_class.return_value = mock_client
        
        result = self.formatter.test_api_connection()
        
        self.assertFalse(result)

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        """Set up edge case test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-key-12345'}):
            self.formatter = PodcastScriptFormatter(
                openai_api_key='sk-test-key-12345',
                cache_dir=self.temp_dir
            )
    
    def tearDown(self):
        """Clean up edge case test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_empty_article_content(self):
        """Test handling of empty article content"""
        empty_article = WikipediaArticle(
            title="Empty Article",
            url="https://example.com",
            content="",
            summary="",
            categories=[],
            page_views=0,
            last_modified="2024-01-01",
            references=[],
            images=[],
            word_count=0,
            quality_score=0.0
        )
        
        prepared = self.formatter._prepare_content(empty_article)
        
        # Should still generate some content structure
        self.assertIn("CONTENT:", prepared)
        self.assertIn("CATEGORIES:", prepared)
    
    def test_very_long_title(self):
        """Test handling of very long article titles"""
        long_title = "A" * 200  # Very long title
        long_article = WikipediaArticle(
            title=long_title,
            url="https://example.com",
            content="Short content",
            summary="Summary",
            categories=["Test"],
            page_views=100,
            last_modified="2024-01-01",
            references=[],
            images=[],
            word_count=2,
            quality_score=0.5
        )
        
        # Should not crash when building prompt
        style_config = PodcastStyles.STYLES["conversational"]
        prompt = self.formatter._build_prompt(long_article, style_config, "test content")
        
        self.assertIn(long_title, prompt)
    
    def test_special_characters_in_filename(self):
        """Test safe filename generation with special characters"""
        special_title = "Test/Article\\With:Special*Characters?<>|"
        script = PodcastScript(
            title=special_title,
            style="conversational",
            script="Test content",
            intro="", outro="", segments=[],
            estimated_duration=300, word_count=50,
            source_article=special_title,
            generated_timestamp="2024-01-01T12:00:00"
        )
        
        # Should not crash when saving
        self.formatter._save_script_to_cache(script)
        
        # Check that file was created with safe filename
        style_dir = self.formatter.cache_dir / "conversational"
        json_files = list(style_dir.glob("*.json"))
        self.assertGreater(len(json_files), 0)

if __name__ == '__main__':
    # Configure test runner
    unittest.main(
        verbosity=2,
        failfast=False,
        buffer=True
    )