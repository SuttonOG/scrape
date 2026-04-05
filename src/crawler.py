
from bs4 import BeautifulSoup
import requests
# go to website and scrape
from urllib.parse import urljoin
import time


# Create crawler -> fetch page -> extract links -> go to links -> scrape link content  -> add to page_contents
class Crawler:

    # globals
    base_timeout = 6                                # required delay between requests
    website_url = 'https://quotes.toscrape.com'     # no trailing slash for clean joins

    def __init__(self):
        self.visited_urls = set()
        self.page_contents = {}

    def fetch_page(self, url):
        """Fetch a single page and return a BeautifulSoup object."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as error:
            print(f"  Unable to extract page {url}\n  Error code: {error}")
            return None

    def extract_text(self, soup):
        """Extract visible text content from a parsed HTML page."""
        for element in soup(["script", "style"]):
            element.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text

    def extract_links(self, soup, current_url):
        """Extract all internal links from a parsed HTML page."""
        links = set()
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            absolute_url = urljoin(current_url, href)
            if absolute_url.startswith(self.website_url):
                absolute_url = absolute_url.split("#")[0]
                links.add(absolute_url)
        return links

    def crawl(self):
        """
        Crawl the target website using breadth-first search.

        Discovers all internal pages starting from the base URL,
        respecting the politeness delay between requests.

        Returns:
            Dictionary mapping each crawled URL to its text content.
        """
        # Reset state for a fresh crawl
        self.visited_urls = set()
        self.page_contents = {}

        # Queue of URLs to visit (breadth-first)
        queue = [self.website_url + "/"]

        while queue:
            url = queue.pop(0)

            # Skip if already visited
            if url in self.visited_urls:
                continue

            # Respect politeness window (skip delay for the very first request)
            if self.visited_urls:
                print(f"  Waiting {self.base_timeout}s (politeness delay)...")
                time.sleep(self.base_timeout)

            print(f"  Crawling: {url}")
            self.visited_urls.add(url)

            soup = self.fetch_page(url)
            if soup is None:
                continue

            # Extract and store page text
            text = self.extract_text(soup)
            if text:
                self.page_contents[url] = text

            # Discover new links and add unvisited ones to the queue
            links = self.extract_links(soup, url)
            for link in links:
                if link not in self.visited_urls:
                    queue.append(link)

        print(f"  Crawl complete. {len(self.page_contents)} pages collected.")
        return self.page_contents