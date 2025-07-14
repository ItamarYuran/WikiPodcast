# src/content_sources/__init__.py
from .manager import ContentSourceManager, create_content_source_manager
from .compatibility_layer import WikipediaContentFetcher
from .interfaces import Article, SearchCriteria, ContentLength

__all__ = [
    'ContentSourceManager', 'create_content_source_manager',
    'WikipediaContentFetcher', 'Article', 'SearchCriteria', 'ContentLength'
]