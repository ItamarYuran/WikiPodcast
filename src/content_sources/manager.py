"""
Content Source Manager
"""

from typing import List, Optional

from .interfaces import ContentSource
from core.models import Article
from .wikipedia_source import WikipediaContentSource

class ContentSourceManager:
    """
    Manages all content sources and provides a unified interface for fetching content.
    """

    def __init__(self):
        """
        Initializes the ContentSourceManager and registers the available content sources.
        """
        self.sources = {
            "wikipedia": WikipediaContentSource()
        }

    def get_source(self, name: str) -> Optional[ContentSource]:
        """
        Gets a content source by name.

        Args:
            name (str): The name of the content source.

        Returns:
            Optional[ContentSource]: The content source, or None if not found.
        """
        return self.sources.get(name)

    def fetch_article(self, identifier: str, source_name: str = "wikipedia") -> Optional[Article]:
        """
        Fetches an article from a specified content source.

        Args:
            identifier (str): The identifier of the article to fetch.
            source_name (str): The name of the content source to use.

        Returns:
            Optional[Article]: The fetched article, or None if not found.
        """
        source = self.get_source(source_name)
        if source:
            return source.fetch_article(identifier)
        return None

    def search_articles(self, query: str, source_name: str = "wikipedia") -> List[Article]:
        """
        Searches for articles from a specified content source.

        Args:
            query (str): The search query.
            source_name (str): The name of the content source to use.

        Returns:
            List[Article]: A list of articles that match the query.
        """
        source = self.get_source(source_name)
        if source:
            return source.search_articles(query)
        return []
