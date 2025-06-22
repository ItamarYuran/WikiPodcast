"""
Test Suite for Wikipedia Podcast Pipeline
Contains unit tests, integration tests, and test utilities
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path for imports
src_dir = Path(__file__).parent.parent / 'src'
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Test configuration
TEST_CONFIG = {
    'temp_dir_prefix': 'wikipedia_podcast_test_',
    'mock_api_key': 'sk-test-key-12345',
    'test_timeout': 30,  # seconds
    'integration_tests_enabled': os.getenv('RUN_INTEGRATION_TESTS', '').lower() == '1'
}

# Mock data for testing
MOCK_ARTICLE_DATA = {
    'title': 'Test Article',
    'url': 'https://en.wikipedia.org/wiki/Test_Article',
    'content': 'This is test content about artificial intelligence. ' * 50,
    'summary': 'Test summary about AI',
    'categories': ['Technology', 'Artificial Intelligence'],
    'page_views': 1000,
    'last_modified': '2024-01-01T12:00:00Z',
    'references': ['https://example.com'],
    'images': ['test.jpg'],
    'word_count': 250,
    'quality_score': 0.8
}

MOCK_SCRIPT_DATA = {
    'title': 'Test Podcast Script',
    'style': 'conversational',
    'script': 'This is a test podcast script content.',
    'intro': 'Welcome to our test podcast',
    'outro': 'Thanks for listening to our test',
    'segments': [
        {'content': 'Segment 1 content', 'estimated_duration': 60},
        {'content': 'Segment 2 content', 'estimated_duration': 90}
    ],
    'estimated_duration': 300,
    'word_count': 100,
    'source_article': 'Test Article',
    'generated_timestamp': '2024-01-01T12:00:00'
}

def get_test_data_path():
    """Get path to test data directory"""
    return Path(__file__).parent / 'data'

def ensure_test_data_dir():
    """Ensure test data directory exists"""
    data_dir = get_test_data_path()
    data_dir.mkdir(exist_ok=True)
    return data_dir