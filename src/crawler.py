"""
crawler.py - Web crawler for quotes.toscrape.com

Responsible for fetching web pages, discovering links,
and respecting the politeness window between requests.

Design decisions:
    - Breadth-first traversal ensures all pages at a given depth are
      visited before going deeper, producing a predictable crawl order.
    - Retry logic with exponential backoff handles transient network
      failures without overwhelming the server.
    - The politeness delay is enforced between ALL requests, including
      retries, to respect the target server.

Complexity:
    - crawl: O(P * (F + L)) where P is the number of pages, F is the
      average page fetch time, and L is the average number of links
      per page.
"""

import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Dict, Optional, Set


class Crawler:
    """Crawls a target website and returns page content."""

    website_url: str = "https://quotes.toscrape.com"
    base_timeout: int = 6       # seconds between requests
    max_retries: int = 3        # retry attempts for failed requests
    request_timeout: int = 10   # HTTP request timeout in seconds

    def __init__(self) -> None:
        self.visited_urls: Set[str] = set()
        self.page_contents: Dict[str, str] = {}

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch a single page and return a BeautifulSoup object.

        Implements retry logic with exponential backoff for transient
        network errors. Each retry respects the politeness delay.

        Args:
            url: The URL to fetch.

        Returns:
            BeautifulSoup object if successful, None after all retries fail.

        Complexity:
            O(1) per successful attempt, up to O(max_retries) total.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(url, timeout=self.request_timeout)
                response.raise_for_status()
                return BeautifulSoup(response.text, "html.parser")

            except requests.RequestException as error:
                print(f"  Attempt {attempt}/{self.max_retries} failed for {url}: {error}")
                if attempt < self.max_retries:
                    wait = self.base_timeout * attempt  # exponential backoff
                    print(f"  Retrying in {wait}s...")
                    time.sleep(wait)

        print(f"  All {self.max_retries} attempts failed for {url}. Skipping.")
        return None

    def extract_text(self, soup: BeautifulSoup) -> str:
        """
        Extract visible text content from a parsed HTML page.

        Removes script, style, and navigation elements to focus on
        meaningful page content.

        Args:
            soup: BeautifulSoup object of the page.

        Returns:
            A string of all visible text on the page.

        Complexity:
            O(n) where n is the number of DOM elements.
        """
        for element in soup(["script", "style"]):
            element.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return text

    def extract_links(self, soup: BeautifulSoup, current_url: str) -> Set[str]:
        """
        Extract all internal links from a parsed HTML page.

        Filters to only include links within the target domain and
        normalises URLs by removing fragments and trailing whitespace.

        Args:
            soup: BeautifulSoup object of the page.
            current_url: The URL of the current page (for resolving relative links).

        Returns:
            A set of absolute URLs found on the page.

        Complexity:
            O(L) where L is the number of anchor tags on the page.
        """
        links: Set[str] = set()
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()

            # Skip empty hrefs, javascript links, and mailto
            if not href or href.startswith(("javascript:", "mailto:")):
                continue

            absolute_url = urljoin(current_url, href)

            # Validate URL structure
            parsed = urlparse(absolute_url)
            if not parsed.scheme or not parsed.netloc:
                continue

            # Only keep links within the target website
            if absolute_url.startswith(self.website_url):
                # Remove URL fragments
                absolute_url = absolute_url.split("#")[0]
                # Remove trailing slash inconsistencies for deduplication
                links.add(absolute_url)

        return links

    def crawl(self) -> Dict[str, str]:
        """
        Crawl the target website using breadth-first search.

        Discovers all internal pages starting from the base URL,
        respecting the politeness delay between requests.

        Returns:
            Dictionary mapping each crawled URL to its text content.

        Complexity:
            O(P * (F + L)) where P = pages, F = fetch time, L = links per page.
        """
        self.visited_urls = set()
        self.page_contents = {}

        queue = [self.website_url + "/"]

        while queue:
            url = queue.pop(0)

            if url in self.visited_urls:
                continue

            # Respect politeness window (skip delay for first request)
            if self.visited_urls:
                print(f"  Waiting {self.base_timeout}s (politeness delay)...")
                time.sleep(self.base_timeout)

            print(f"  Crawling: {url}")
            self.visited_urls.add(url)

            soup = self.fetch_page(url)
            if soup is None:
                continue

            text = self.extract_text(soup)
            if text.strip():
                self.page_contents[url] = text

            links = self.extract_links(soup, url)
            for link in links:
                if link not in self.visited_urls:
                    queue.append(link)

        print(f"  Crawl complete. {len(self.page_contents)} pages collected.")
        return self.page_contents