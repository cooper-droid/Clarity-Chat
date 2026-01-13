"""
Web scraper service to fetch content from fiatwm.com
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class WebScraperService:
    """Service for scraping content from fiatwm.com"""

    def __init__(self):
        self.base_url = "https://fiatwm.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def scrape_page(self, url: str) -> Optional[Dict[str, str]]:
        """
        Scrape content from a specific page

        Args:
            url: The URL to scrape

        Returns:
            Dictionary with title and content, or None if failed
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()

            # Get title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else url

            # Get main content
            main_content = soup.find('main') or soup.find('article') or soup.find('body')

            if main_content:
                # Extract text
                text = main_content.get_text(separator='\n', strip=True)
                # Clean up excessive whitespace
                text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()])

                return {
                    'url': url,
                    'title': title_text,
                    'content': text[:5000]  # Limit to first 5000 chars
                }

            return None

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    def search_site(self, query: str) -> List[Dict[str, str]]:
        """
        Search the site for relevant pages

        Args:
            query: Search query

        Returns:
            List of scraped content from relevant pages
        """
        results = []

        # Common pages to check
        common_pages = [
            f"{self.base_url}/",
            f"{self.base_url}/about",
            f"{self.base_url}/services",
            f"{self.base_url}/retirement-planning",
            f"{self.base_url}/tax-planning",
            f"{self.base_url}/wealth-management",
        ]

        for page_url in common_pages:
            content = self.scrape_page(page_url)
            if content and self._is_relevant(content['content'], query):
                results.append(content)

        return results[:3]  # Return top 3 results

    def _is_relevant(self, content: str, query: str) -> bool:
        """
        Check if content is relevant to the query

        Args:
            content: Page content
            query: Search query

        Returns:
            True if content seems relevant
        """
        query_lower = query.lower()
        content_lower = content.lower()

        # Split query into words
        query_words = [w for w in query_lower.split() if len(w) > 3]

        # Check if at least one query word appears in content
        for word in query_words:
            if word in content_lower:
                return True

        return False


# Global instance
web_scraper = WebScraperService()
