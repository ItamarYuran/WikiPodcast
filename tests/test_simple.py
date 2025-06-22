#!/usr/bin/env python3
"""
Simple Working Test
Tests basic functionality without complex imports
"""

import unittest
import tempfile
import shutil
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestBasicImports(unittest.TestCase):
    """Test that we can import our modules"""
    
    def test_import_content_fetcher(self):
        """Test importing content_fetcher module"""
        try:
            import content_fetcher
            self.assertTrue(hasattr(content_fetcher, 'WikipediaContentFetcher'))
        except ImportError as e:
            self.fail(f"Could not import content_fetcher: {e}")
    
    def test_import_script_formatter(self):
        """Test importing script_formatter module"""
        try:
            import script_formatter
            self.assertTrue(hasattr(script_formatter, 'PodcastScriptFormatter'))
        except ImportError as e:
            self.fail(f"Could not import script_formatter: {e}")
    
    def test_import_pipeline(self):
        """Test importing pipeline module"""
        try:
            import pipeline
            self.assertTrue(hasattr(pipeline, 'PodcastPipeline'))
        except ImportError as e:
            self.fail(f"Could not import pipeline: {e}")

class TestContentFetcherBasic(unittest.TestCase):
    """Basic content fetcher tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_safe_filename_basic(self):
        """Test basic safe filename creation"""
        try:
            from content_fetcher import WikipediaContentFetcher
            fetcher = WikipediaContentFetcher(cache_dir=self.temp_dir)
            
            # Test basic case
            result = fetcher._make_safe_filename("Test Article")
            self.assertEqual(result, "Test_Article")
            
            # Test with some special characters
            result = fetcher._make_safe_filename("Test/Article")
            self.assertEqual(result, "Test_Article")
            
        except Exception as e:
            self.fail(f"Safe filename test failed: {e}")
    
    def test_fetcher_initialization(self):
        """Test fetcher can be initialized"""
        try:
            from content_fetcher import WikipediaContentFetcher
            fetcher = WikipediaContentFetcher(cache_dir=self.temp_dir)
            
            self.assertEqual(fetcher.language, 'en')
            self.assertTrue(fetcher.cache_dir.exists())
            
        except Exception as e:
            self.fail(f"Fetcher initialization failed: {e}")

class TestScriptFormatterBasic(unittest.TestCase):
    """Basic script formatter tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock environment
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-key-12345'
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_formatter_with_api_key(self):
        """Test formatter initialization with API key"""
        try:
            from script_formatter import PodcastScriptFormatter
            
            formatter = PodcastScriptFormatter(
                openai_api_key='sk-test-key-12345',
                cache_dir=self.temp_dir
            )
            
            self.assertTrue(formatter.cache_dir.exists())
            self.assertEqual(formatter.openai_api_key, 'sk-test-key-12345')
            
        except Exception as e:
            self.fail(f"Formatter initialization failed: {e}")
    
    def test_get_available_styles(self):
        """Test getting available styles"""
        try:
            from script_formatter import PodcastScriptFormatter
            
            formatter = PodcastScriptFormatter(
                openai_api_key='sk-test-key-12345',
                cache_dir=self.temp_dir
            )
            
            styles = formatter.get_available_styles()
            self.assertIsInstance(styles, dict)
            self.assertIn('conversational', styles)
            
        except Exception as e:
            self.fail(f"Get styles test failed: {e}")

if __name__ == '__main__':
    unittest.main(verbosity=2)