
from bs4 import BeautifulSoup
import requests
# go to website and scrape
from urllib.parse import urljoin

# Create crawler -> fetch page -> extract links -> go to links -> scrape link content  -> add to page_contents
class Crawler:

    #globals
    base_timeout = 6                                # required delay between the requests
    website_url = 'https://quotes.toscrape.com/'   

    def __init__(self):

        # track pages visited 
        self.visited_urls = set()                       # set to not add twice
        self.page_contents = {}                         # for returning {url:content} after crawling

    def fetch_page(self,url):

        # visit page -> beautifulsoup object
        try:
            response = requests.get(url, timeout = 10)
            response.raise_for_status()             # check it was successful
            
            # if success, return beautifulsoup object
            return BeautifulSoup(response.text, "html.parser")
        
        except requests.RequestException as error:
            # error case print 
            print(f"Unable to extract page {url}\n Error code: {error}")
            return None
        
    def extract_text(self, soup):
        """
        Extract visible text content from a parsed HTML page.

        Args:
            soup: BeautifulSoup object of the page.

        Returns:
            A string of all visible text on the page.
        """
        # Remove script and style elements
        for element in soup(["script", "style"]):
            element.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return text
    
    def extract_links(self, soup, current_url):
        """
        Extract all internal links from a parsed HTML page.

        Args:
            soup: BeautifulSoup object of the page.
            current_url: The URL of the current page (for resolving relative links).

        Returns:
            A set of absolute URLs found on the page.
        """
        links = set()
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            # Resolve relative URLs to absolute
            absolute_url = urljoin(current_url, href)
            # Only keep links within the target website
            if absolute_url.startswith(self.website_url):
                # Remove URL fragments (e.g., #section)
                absolute_url = absolute_url.split("#")[0]
                links.add(absolute_url)
        return links

