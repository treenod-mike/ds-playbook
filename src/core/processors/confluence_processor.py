"""
Confluence API processor for downloading and converting pages
"""
import logging
import time
import requests
from typing import Dict, Optional, Any
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth

from src.shared.config import Config


logger = logging.getLogger("playbook_nexus.confluence")


class ConfluenceProcessor:
    """Process Confluence pages via REST API"""

    def __init__(
        self,
        base_url: str = None,
        email: str = None,
        api_token: str = None,
        max_retries: int = None
    ):
        """
        Initialize Confluence processor

        Args:
            base_url: Confluence base URL
            email: User email for authentication
            api_token: API token for authentication
            max_retries: Maximum number of retries on failure
        """
        self.base_url = (base_url or Config.CONFLUENCE_URL).rstrip('/')
        self.email = email or Config.CONFLUENCE_EMAIL
        self.api_token = api_token or Config.CONFLUENCE_API_TOKEN
        self.max_retries = max_retries or Config.CONFLUENCE_MAX_RETRIES
        self.rate_limit_delay = Config.CONFLUENCE_RATE_LIMIT_DELAY

        if not all([self.base_url, self.email, self.api_token]):
            raise ValueError("Confluence credentials not properly configured")

        self.auth = HTTPBasicAuth(self.email, self.api_token)
        self.session = requests.Session()
        self.session.auth = self.auth

    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a Confluence page by ID with retry logic

        Args:
            page_id: Confluence page ID

        Returns:
            Page data dictionary or None if failed
        """
        url = f"{self.base_url}/rest/api/content/{page_id}"
        params = {
            "expand": "body.storage,version,space,ancestors"
        }

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed for page {page_id}: {e}"
                )
                if attempt < self.max_retries - 1:
                    # Exponential backoff with rate limit delay
                    wait_time = (2 ** attempt) * self.rate_limit_delay
                    logger.debug(f"Waiting {wait_time:.2f}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch page {page_id} after {self.max_retries} attempts")
                    return None

            except Exception as e:
                logger.error(f"Unexpected error fetching page {page_id}: {e}")
                return None

        return None

    def extract_text_from_html(self, html: str) -> str:
        """
        Extract clean text from Confluence HTML (basic version)

        Args:
            html: HTML content

        Returns:
            Clean text content
        """
        if not html:
            return ""

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Remove script and style elements
            for element in soup(['script', 'style', 'meta', 'link']):
                element.decompose()

            # Get text
            text = soup.get_text(separator='\n', strip=True)

            # Clean up excessive whitespace
            lines = [line.strip() for line in text.split('\n')]
            lines = [line for line in lines if line]
            text = '\n'.join(lines)

            return text

        except Exception as e:
            logger.error(f"Failed to extract text from HTML: {e}")
            return ""

    def process_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """
        Process a Confluence page and extract relevant information

        Args:
            page_id: Confluence page ID

        Returns:
            Processed page data or None if failed
        """
        page_data = self.get_page(page_id)

        if not page_data:
            return None

        try:
            # Extract basic metadata
            title = page_data.get('title', '')
            page_url = f"{self.base_url}/pages/viewpage.action?pageId={page_id}"

            # Extract space information
            space = page_data.get('space', {})
            space_key = space.get('key', '')
            space_name = space.get('name', '')

            # Extract version information
            version = page_data.get('version', {})
            version_number = version.get('number', 0)
            last_updated = version.get('when', '')

            # Extract and convert HTML content to text
            body = page_data.get('body', {})
            storage = body.get('storage', {})
            html_content = storage.get('value', '')
            text_content = self.extract_text_from_html(html_content)

            # Extract parent/ancestor information
            ancestors = page_data.get('ancestors', [])
            parent_id = ancestors[-1].get('id', '') if ancestors else ''
            parent_title = ancestors[-1].get('title', '') if ancestors else ''

            # Build path from ancestors
            path_parts = [ancestor.get('title', '') for ancestor in ancestors]
            path = ' > '.join(path_parts) if path_parts else ''

            return {
                'page_id': page_id,
                'title': title,
                'content': text_content,
                'html_content': html_content,
                'url': page_url,
                'space_key': space_key,
                'space_name': space_name,
                'version': version_number,
                'last_updated': last_updated,
                'parent_id': parent_id,
                'parent_title': parent_title,
                'path': path,
            }

        except Exception as e:
            logger.error(f"Failed to process page {page_id}: {e}")
            return None

    def test_connection(self) -> bool:
        """
        Test Confluence API connection

        Returns:
            True if connection successful, False otherwise
        """
        try:
            url = f"{self.base_url}/rest/api/content"
            params = {"limit": 1}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            logger.info("Confluence API connection successful")
            return True

        except Exception as e:
            logger.error(f"Confluence API connection failed: {e}")
            return False
