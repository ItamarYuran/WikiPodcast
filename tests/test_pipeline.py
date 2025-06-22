#!/usr/bin/env python3
"""
Test Suite for Pipeline
Tests the main pipeline orchestration functionality
"""

import unittest
import tempfile
import shutil
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pipeline import PodcastPipeline
from content_fetcher import WikipediaArticle
from script_formatter import PodcastScript

class TestPodcastPipeline(unittest.TestCase):
    """Test PodcastPipeline class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock environment variables for API keys
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-key-12345'
        })
        self.env_patcher.start()
        
        # Create pipeline with mocked components
        with patch('pipeline.WikipediaContentFetcher') as mock_fetcher_class, \
             patch('pipeline.PodcastScriptFormatter') as mock_formatter_class, \
             patch('pipeline.ContentProcessor') as mock_processor_class, \
             patch('pipeline.AudioGenerator') as mock_audio_class, \
             patch('pipeline.InteractiveMenus') as mock_menus_class:
            
            # Set up mock instances
            self.mock_fetcher = Mock()
            self.mock_formatter = Mock()
            self.mock_processor = Mock()
            self.mock_audio = Mock()
            self.mock_menus = Mock()
            
            mock_fetcher_class.return_value = self.mock_fetcher
            mock_formatter_class.return_value = self.mock_formatter
            mock_processor_class.return_value = self.mock_processor
            mock_audio_class.return_value = self.mock_audio
            mock_menus_class.return_value = self.mock_menus
            
            self.pipeline = PodcastPipeline(cache_dir=self.temp_dir)
        
        # Mock article for testing
        self.mock_article = WikipediaArticle(
            title="Test Article",
            url="https://en.wikipedia.org/wiki/Test_Article",
            content="This is test content about artificial intelligence. " * 50,
            summary="Test summary about AI",
            categories=["Technology", "AI"],
            page_views=1000,
            last_modified="2024-01-01",
            references=["https://example.com"],
            images=["test.jpg"],
            word_count=250,
            quality_score=0.8
        )
        
        # Mock script for testing
        self.mock_script = PodcastScript(
            title="Test Script",
            style="conversational",
            script="This is a test podcast script",
            intro="Welcome to the podcast",
            outro="Thanks for listening",
            segments=[{"content": "segment 1", "duration": 60}],
            estimated_duration=300,
            word_count=100,
            source_article="Test Article",
            generated_timestamp="2024-01-01T12:00:00"
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_pipeline_initialization(self):
        """Test pipeline initializes correctly"""
        self.assertIsNotNone(self.pipeline.content_fetcher)
        self.assertIsNotNone(self.pipeline.script_formatter)
        self.assertIsNotNone(self.pipeline.content_processor)
        self.assertIsNotNone(self.pipeline.audio_generator)
        self.assertIsNotNone(self.pipeline.interactive_menus)
        
        # Check that components are properly connected
        self.assertEqual(self.pipeline.interactive_menus.pipeline, self.pipeline)
    
    def test_show_status(self):
        """Test pipeline status display"""
        # Mock cache stats
        self.mock_fetcher.get_cache_stats.return_value = {
            'total_articles': 5,
            'total_size_mb': 10.5
        }
        self.mock_formatter.list_cached_scripts.return_value = [
            {'title': 'Script 1', 'style': 'conversational'},
            {'title': 'Script 2', 'style': 'documentary'}
        ]
        
        # Should not raise an exception
        self.pipeline.show_status()
        
        # Verify calls were made
        self.mock_fetcher.get_cache_stats.assert_called_once()
        self.mock_formatter.list_cached_scripts.assert_called_once()
    
    def test_interactive_mode(self):
        """Test entering interactive mode"""
        # Should delegate to interactive menus
        self.pipeline.interactive_mode()
        
        self.mock_menus.run_main_menu.assert_called_once()
    
    def test_fetch_and_generate_trending_success(self):
        """Test successful trending articles processing"""
        # Mock fetcher returning articles
        self.mock_fetcher.get_trending_articles.return_value = [self.mock_article]
        
        # Mock processor returning results
        mock_result = Mock()
        mock_result.title = "Test Article"
        mock_result.script_file = "test_script.json"
        mock_result.word_count = 100
        mock_result.style = "conversational"
        mock_result.estimated_duration = 300
        
        self.mock_processor.fetch_and_generate_trending.return_value = [mock_result]
        
        results = self.pipeline.fetch_and_generate_trending(count=1, style="conversational")
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Test Article")
        
        # Verify calls
        self.mock_processor.fetch_and_generate_trending.assert_called_once_with(
            count=1, style="conversational", target_length="full"
        )
    
    def test_fetch_and_generate_trending_empty(self):
        """Test trending articles when no articles available"""
        # Mock processor returning empty list
        self.mock_processor.fetch_and_generate_trending.return_value = []
        
        results = self.pipeline.fetch_and_generate_trending(count=5)
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)
    
    def test_fetch_and_generate_featured_success(self):
        """Test successful featured articles processing"""
        mock_result = Mock()
        mock_result.title = "Featured Article"
        mock_result.script_file = "featured_script.json"
        
        self.mock_processor.fetch_and_generate_featured.return_value = [mock_result]
        
        results = self.pipeline.fetch_and_generate_featured(count=2, style="documentary")
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        
        self.mock_processor.fetch_and_generate_featured.assert_called_once_with(
            count=2, style="documentary", target_length="full"
        )
    
    def test_generate_single_topic_success(self):
        """Test successful single topic processing"""
        mock_result = Mock()
        mock_result.title = "Single Topic"
        mock_result.script_file = "single_topic.json"
        
        self.mock_processor.generate_single_topic.return_value = mock_result
        
        result = self.pipeline.generate_single_topic("Python programming", style="academic")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.title, "Single Topic")
        
        self.mock_processor.generate_single_topic.assert_called_once_with(
            "Python programming", style="academic", target_length="full"
        )
    
    def test_generate_single_topic_failure(self):
        """Test single topic processing failure"""
        self.mock_processor.generate_single_topic.return_value = None
        
        result = self.pipeline.generate_single_topic("Nonexistent topic")
        
        self.assertIsNone(result)
    
    def test_create_complete_podcast_success(self):
        """Test complete podcast creation (topic to audio)"""
        # Mock successful topic processing
        mock_topic_result = Mock()
        mock_topic_result.title = "Complete Podcast"
        mock_topic_result.script_file = "complete_script.json"
        mock_topic_result.style = "conversational"
        mock_topic_result.estimated_duration = 600
        
        self.mock_processor.generate_single_topic.return_value = mock_topic_result
        
        # Mock successful audio generation
        mock_audio_result = {
            'filename': 'complete_podcast.mp3',
            'duration': 10.5,
            'file_size': 15.2
        }
        
        self.mock_audio.generate_from_script_file.return_value = mock_audio_result
        
        result = self.pipeline.create_complete_podcast("AI topic", style="conversational")
        
        self.assertIsNotNone(result)
        self.assertIn('script_file', result)
        self.assertIn('audio_file', result)
        self.assertIn('duration', result)
        self.assertEqual(result['style'], 'conversational')
        
        # Verify both steps were called
        self.mock_processor.generate_single_topic.assert_called_once()
        self.mock_audio.generate_from_script_file.assert_called_once()
    
    def test_create_complete_podcast_script_failure(self):
        """Test complete podcast creation when script generation fails"""
        # Mock script generation failure
        self.mock_processor.generate_single_topic.return_value = None
        
        result = self.pipeline.create_complete_podcast("Bad topic")
        
        self.assertIsNone(result)
        
        # Audio generation should not be called
        self.mock_audio.generate_from_script_file.assert_not_called()
    
    def test_create_complete_podcast_audio_failure(self):
        """Test complete podcast creation when audio generation fails"""
        # Mock successful script generation
        mock_topic_result = Mock()
        mock_topic_result.title = "Test"
        mock_topic_result.script_file = "test.json"
        mock_topic_result.style = "conversational"
        
        self.mock_processor.generate_single_topic.return_value = mock_topic_result
        
        # Mock audio generation failure
        self.mock_audio.generate_from_script_file.return_value = None
        
        result = self.pipeline.create_complete_podcast("Test topic")
        
        self.assertIsNone(result)
    
    def test_get_pipeline_stats(self):
        """Test getting pipeline statistics"""
        # Mock component stats
        self.mock_fetcher.get_cache_stats.return_value = {
            'total_articles': 10,
            'total_size_mb': 25.5
        }
        
        self.mock_formatter.list_cached_scripts.return_value = [
            {'style': 'conversational', 'word_count': 100},
            {'style': 'documentary', 'word_count': 200},
            {'style': 'conversational', 'word_count': 150}
        ]
        
        stats = self.pipeline.get_pipeline_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('articles', stats)
        self.assertIn('scripts', stats)
        self.assertIn('total_cache_size_mb', stats)
        
        # Verify structure
        self.assertEqual(stats['articles']['count'], 10)
        self.assertEqual(stats['scripts']['count'], 3)
    
    def test_clear_all_caches(self):
        """Test clearing all pipeline caches"""
        # Mock cache clearing methods
        self.mock_fetcher.clear_cache.return_value = 5
        
        # Mock manual script cache clearing (since method doesn't exist)
        with patch.object(self.pipeline, '_clear_script_cache', return_value=3):
            
            result = self.pipeline.clear_all_caches()
            
            self.assertIsInstance(result, dict)
            self.assertIn('articles_cleared', result)
            
            # Verify fetcher cache was cleared
            self.mock_fetcher.clear_cache.assert_called_once()
    
    def test_error_handling_in_status(self):
        """Test error handling in status display"""
        # Mock an exception in one of the status calls
        self.mock_fetcher.get_cache_stats.side_effect = Exception("Cache error")
        
        # Should not raise an exception, should handle gracefully
        try:
            self.pipeline.show_status()
        except Exception as e:
            self.fail(f"show_status raised an exception: {e}")
    
    def test_component_initialization_failure(self):
        """Test handling of component initialization failures"""
        # Test what happens when a component fails to initialize
        with patch('pipeline.WikipediaContentFetcher', side_effect=Exception("Init failed")):
            with self.assertRaises(Exception):
                PodcastPipeline()
    
    def test_custom_cache_directory(self):
        """Test pipeline with custom cache directory"""
        custom_dir = self.temp_dir / "custom_cache"
        
        with patch('pipeline.WikipediaContentFetcher') as mock_fetcher_class, \
             patch('pipeline.PodcastScriptFormatter') as mock_formatter_class, \
             patch('pipeline.ContentProcessor') as mock_processor_class, \
             patch('pipeline.AudioGenerator') as mock_audio_class, \
             patch('pipeline.InteractiveMenus') as mock_menus_class:
            
            pipeline = PodcastPipeline(cache_dir=str(custom_dir))
            
            # Verify components were initialized with correct cache directories
            # (This depends on the actual implementation details)
            self.assertIsNotNone(pipeline.content_fetcher)
            self.assertIsNotNone(pipeline.script_formatter)

class TestPipelineIntegration(unittest.TestCase):
    """Integration tests for pipeline components working together"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Set up environment
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-key-12345'
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('pipeline.WikipediaContentFetcher')
    @patch('pipeline.PodcastScriptFormatter')
    @patch('pipeline.ContentProcessor')
    def test_pipeline_component_interaction(self, mock_processor_class, mock_formatter_class, mock_fetcher_class):
        """Test that pipeline components interact correctly"""
        # Set up mock instances
        mock_fetcher = Mock()
        mock_formatter = Mock()
        mock_processor = Mock()
        
        mock_fetcher_class.return_value = mock_fetcher
        mock_formatter_class.return_value = mock_formatter
        mock_processor_class.return_value = mock_processor
        
        # Create pipeline
        pipeline = PodcastPipeline(cache_dir=self.temp_dir)
        
        # Test that processor receives the correct dependencies
        mock_processor_class.assert_called_once()
        call_kwargs = mock_processor_class.call_args[1]
        
        # Verify that processor gets the fetcher and formatter instances
        self.assertEqual(call_kwargs['content_fetcher'], mock_fetcher)
        self.assertEqual(call_kwargs['script_formatter'], mock_formatter)
    
    def test_pipeline_data_flow(self):
        """Test data flow through pipeline components"""
        with patch('pipeline.WikipediaContentFetcher') as mock_fetcher_class, \
             patch('pipeline.PodcastScriptFormatter') as mock_formatter_class, \
             patch('pipeline.ContentProcessor') as mock_processor_class:
            
            # Create realistic mock data flow
            mock_article = WikipediaArticle(
                title="Data Flow Test",
                url="https://test.com",
                content="Test content",
                summary="Test summary",
                categories=["Test"],
                page_views=100,
                last_modified="2024-01-01",
                references=[],
                images=[],
                word_count=50,
                quality_score=0.7
            )
            
            mock_script = PodcastScript(
                title="Data Flow Script",
                style="conversational",
                script="Generated script content",
                intro="Intro", outro="Outro", segments=[],
                estimated_duration=300, word_count=75,
                source_article="Data Flow Test",
                generated_timestamp="2024-01-01T12:00:00"
            )
            
            # Set up mock returns
            mock_fetcher = Mock()
            mock_formatter = Mock() 
            mock_processor = Mock()
            
            mock_fetcher.fetch_article.return_value = mock_article
            mock_formatter.format_article_to_script.return_value = mock_script
            
            mock_result = Mock()
            mock_result.title = "Data Flow Test"
            mock_result.script_file = "test.json"
            mock_processor.generate_single_topic.return_value = mock_result
            
            mock_fetcher_class.return_value = mock_fetcher
            mock_formatter_class.return_value = mock_formatter
            mock_processor_class.return_value = mock_processor
            
            # Create pipeline and test data flow
            pipeline = PodcastPipeline(cache_dir=self.temp_dir)
            result = pipeline.generate_single_topic("test topic")
            
            # Verify the data flowed through the system
            self.assertIsNotNone(result)
            self.assertEqual(result.title, "Data Flow Test")

class TestPipelineErrorScenarios(unittest.TestCase):
    """Test error scenarios and edge cases in pipeline"""
    
    def setUp(self):
        """Set up error scenario test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-key-12345'
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up error scenario test fixtures"""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_missing_api_key_handling(self):
        """Test pipeline behavior when API key is missing"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('pipeline.PodcastScriptFormatter', side_effect=ValueError("API key missing")):
                with self.assertRaises(ValueError):
                    PodcastPipeline()
    
    def test_network_error_handling(self):
        """Test pipeline behavior during network errors"""
        with patch('pipeline.WikipediaContentFetcher') as mock_fetcher_class, \
             patch('pipeline.PodcastScriptFormatter') as mock_formatter_class, \
             patch('pipeline.ContentProcessor') as mock_processor_class:
            
            # Mock network error in fetcher
            mock_fetcher = Mock()
            mock_fetcher.get_trending_articles.side_effect = Exception("Network error")
            mock_fetcher_class.return_value = mock_fetcher
            
            mock_formatter_class.return_value = Mock()
            
            # Mock processor to handle the error gracefully
            mock_processor = Mock()
            mock_processor.fetch_and_generate_trending.return_value = []
            mock_processor_class.return_value = mock_processor
            
            pipeline = PodcastPipeline(cache_dir=self.temp_dir)
            
            # Should return empty list, not crash
            result = pipeline.fetch_and_generate_trending(count=5)
            self.assertEqual(result, [])
    
    def test_partial_component_failure(self):
        """Test pipeline when some components fail but others work"""
        with patch('pipeline.WikipediaContentFetcher') as mock_fetcher_class, \
             patch('pipeline.PodcastScriptFormatter') as mock_formatter_class, \
             patch('pipeline.ContentProcessor') as mock_processor_class, \
             patch('pipeline.AudioGenerator') as mock_audio_class:
            
            # Set up working components
            mock_fetcher_class.return_value = Mock()
            mock_formatter_class.return_value = Mock()
            mock_processor_class.return_value = Mock()
            
            # Mock audio generator failure
            mock_audio_class.side_effect = Exception("Audio system unavailable")
            
            # Pipeline should still initialize other components
            pipeline = PodcastPipeline(cache_dir=self.temp_dir)
            
            # Content fetching should still work
            self.assertIsNotNone(pipeline.content_fetcher)
            self.assertIsNotNone(pipeline.script_formatter)
    
    def test_invalid_cache_directory(self):
        """Test pipeline with invalid cache directory"""
        # Try to use a file as a directory (should fail)
        invalid_path = Path(self.temp_dir) / "not_a_directory.txt"
        invalid_path.write_text("This is a file, not a directory")
        
        with patch('pipeline.WikipediaContentFetcher') as mock_fetcher_class:
            # The fetcher should handle this gracefully or raise a clear error
            mock_fetcher_class.side_effect = Exception("Invalid cache directory")
            
            with self.assertRaises(Exception):
                PodcastPipeline(cache_dir=str(invalid_path))

class TestPipelinePerformance(unittest.TestCase):
    """Test pipeline performance characteristics"""
    
    def setUp(self):
        """Set up performance test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-key-12345'
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up performance test fixtures"""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_pipeline_initialization_time(self):
        """Test that pipeline initializes in reasonable time"""
        import time
        
        with patch('pipeline.WikipediaContentFetcher') as mock_fetcher_class, \
             patch('pipeline.PodcastScriptFormatter') as mock_formatter_class, \
             patch('pipeline.ContentProcessor') as mock_processor_class, \
             patch('pipeline.AudioGenerator') as mock_audio_class, \
             patch('pipeline.InteractiveMenus') as mock_menus_class:
            
            # Mock quick initialization
            mock_fetcher_class.return_value = Mock()
            mock_formatter_class.return_value = Mock()
            mock_processor_class.return_value = Mock()
            mock_audio_class.return_value = Mock()
            mock_menus_class.return_value = Mock()
            
            start_time = time.time()
            pipeline = PodcastPipeline(cache_dir=self.temp_dir)
            end_time = time.time()
            
            # Should initialize quickly (under 1 second for mocked components)
            initialization_time = end_time - start_time
            self.assertLess(initialization_time, 1.0)
            self.assertIsNotNone(pipeline)
    
    def test_memory_usage_patterns(self):
        """Test that pipeline doesn't hold excessive references"""
        with patch('pipeline.WikipediaContentFetcher') as mock_fetcher_class, \
             patch('pipeline.PodcastScriptFormatter') as mock_formatter_class, \
             patch('pipeline.ContentProcessor') as mock_processor_class:
            
            mock_fetcher_class.return_value = Mock()
            mock_formatter_class.return_value = Mock()
            mock_processor_class.return_value = Mock()
            
            pipeline = PodcastPipeline(cache_dir=self.temp_dir)
            
            # Test that pipeline can be deleted cleanly
            pipeline_id = id(pipeline)
            del pipeline
            
            # If there were circular references, this would be problematic
            # This is a basic test - more sophisticated memory testing would
            # require additional tools

if __name__ == '__main__':
    # Configure test runner
    unittest.main(
        verbosity=2,
        failfast=False,
        buffer=True
    )