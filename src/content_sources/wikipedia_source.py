"""
Wikipedia Content Source
"""

import requests
from typing import List, Optional

from .interfaces import ContentSource, Article

class WikipediaContentSource(ContentSource):
    """
    A content source for fetching articles from Wikipedia.
    """

    def __init__(self, api_url: str = "https://en.wikipedia.org/api/rest_v1/page/summary/"):
        """
        Initializes the WikipediaContentSource.

        Args:
            api_url (str): The URL of the Wikipedia API.
        """
        self.api_url = api_url

    def fetch_article(self, identifier: str) -> Optional[Article]:
        """
        Fetches a single article from Wikipedia.

        Args:
            identifier (str): The title of the article to fetch.

        Returns:
            Optional[Article]: The fetched article, or None if not found.
        """
        try:
            response = requests.get(f"{self.api_url}{identifier}")
            response.raise_for_status()
            data = response.json()
            return Article(
                title=data.get("title", ""),
                content=data.get("extract", ""),
                url=data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                source="wikipedia"
            )
        except requests.RequestException:
            return None

    def search_articles(self, query: str) -> List[Article]:
        """
        Searches for articles on Wikipedia.

        Args:
            query (str): The search query.

        Returns:
            List[Article]: A list of articles that match the query.
        """
        # Note: This is a simplified search that fetches a single article.
        # A more robust implementation would use the Wikipedia search API.
        article = self.fetch_article(query)
        return [article] if article else []
