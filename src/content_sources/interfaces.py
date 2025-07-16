"""
Simplified Content Source Interfaces
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Article:
    """
    Represents a fetched article with essential information.
    """
    title: str
    content: str
    url: str
    source: str

class ContentSource(ABC):
    """
    A unified interface for all content sources, providing a consistent
    way to fetch, search, and get suggestions for articles.
    """

    @abstractmethod
    def fetch_article(self, identifier: str) -> Optional[Article]:
        """
        Fetches a single article based on a unique identifier (e.g., title, URL).

        Args:
            identifier (str): The unique identifier for the article.

        Returns:
            Optional[Article]: The fetched article, or None if not found.
        """
        pass

    @abstractmethod
    def search_articles(self, query: str) -> List[Article]:
        """
        Searches for articles based on a query string.

        Args:
            query (str): The search query.

        Returns:
            List[Article]: A list of articles that match the query.
        """
        pass
