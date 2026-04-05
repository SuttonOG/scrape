"""Tests for the web crawler module."""

import sys
import os
import pytest
from unittest.mock import patch, Mock
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from crawler import Crawler


@pytest.fixture
def crawler():
    """Create a fresh Crawler instance for each test."""
    return Crawler()


@pytest.fixture
def sample_html():
    """Sample HTML page resembling quotes.toscrape.com."""
    return """
    <html>
    <head><title>Quotes to Scrape</title>
    <style>.header { color: red; }</style>
    <script>var x = 1;</script>
    </head>
    <body>
        <div class="quote">
            <span class="text">"The world as we have created it is a process of our thinking."</span>
            <small class="author">Albert Einstein</small>
        </div>
        <div class="quote">
            <span class="text">"Good friends, good books, and a sleepy conscience."</span>
            <small class="author">Mark Twain</small>
        </div>
        <nav>
            <a href="/page/2/">Next</a>
            <a href="/author/Albert-Einstein/">Albert Einstein</a>
            <a href="https://external-site.com/spam">External</a>
        </nav>
    </body>
    </html>
    """


class TestFetchPage:
    """Tests for the fetch_page method."""

    @patch("crawler.requests.get")
    def test_successful_fetch(self, mock_get, crawler):
        """fetch_page returns a BeautifulSoup object on success."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><p>Hello</p></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = crawler.fetch_page("https://quotes.toscrape.com/")
        assert result is not None
        assert isinstance(result, BeautifulSoup)
        assert result.find("p").text == "Hello"

    @patch("crawler.requests.get")
    def test_fetch_timeout(self, mock_get, crawler):
        """fetch_page returns None on a timeout."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        result = crawler.fetch_page("https://quotes.toscrape.com/")
        assert result is None

    @patch("crawler.requests.get")
    def test_fetch_connection_error(self, mock_get, crawler):
        """fetch_page returns None on a connection error."""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")

        result = crawler.fetch_page("https://quotes.toscrape.com/")
        assert result is None

    @patch("crawler.requests.get")
    def test_fetch_http_error(self, mock_get, crawler):
        """fetch_page returns None on a 404 or other HTTP error."""
        import requests
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
        mock_get.return_value = mock_response

        result = crawler.fetch_page("https://quotes.toscrape.com/bad-page")
        assert result is None

    @patch("crawler.requests.get")
    def test_fetch_sets_timeout(self, mock_get, crawler):
        """fetch_page passes a timeout to requests.get."""
        mock_response = Mock()
        mock_response.text = "<html></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        crawler.fetch_page("https://quotes.toscrape.com/")
        mock_get.assert_called_once_with("https://quotes.toscrape.com/", timeout=10)


class TestExtractText:
    """Tests for the extract_text method."""

    def test_extracts_visible_text(self, crawler, sample_html):
        """extract_text returns visible text from the page."""
        soup = BeautifulSoup(sample_html, "html.parser")
        text = crawler.extract_text(soup)

        assert "Albert Einstein" in text
        assert "Good friends" in text
        assert "Mark Twain" in text

    def test_removes_script_tags(self, crawler, sample_html):
        """extract_text strips JavaScript content."""
        soup = BeautifulSoup(sample_html, "html.parser")
        text = crawler.extract_text(soup)

        assert "var x = 1" not in text

    def test_removes_style_tags(self, crawler, sample_html):
        """extract_text strips CSS content."""
        soup = BeautifulSoup(sample_html, "html.parser")
        text = crawler.extract_text(soup)

        assert "color: red" not in text

    def test_empty_page(self, crawler):
        """extract_text handles an empty page body."""
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        text = crawler.extract_text(soup)

        assert text == ""


class TestExtractLinks:
    """Tests for the extract_links method."""

    def test_finds_internal_links(self, crawler, sample_html):
        """extract_links returns links within the target domain."""
        soup = BeautifulSoup(sample_html, "html.parser")
        links = crawler.extract_links(soup, "https://quotes.toscrape.com/")

        assert "https://quotes.toscrape.com/page/2/" in links
        assert "https://quotes.toscrape.com/author/Albert-Einstein/" in links

    def test_excludes_external_links(self, crawler, sample_html):
        """extract_links filters out links to other domains."""
        soup = BeautifulSoup(sample_html, "html.parser")
        links = crawler.extract_links(soup, "https://quotes.toscrape.com/")

        assert "https://external-site.com/spam" not in links

    def test_resolves_relative_urls(self, crawler):
        """extract_links converts relative URLs to absolute."""
        html = '<html><body><a href="/page/3/">Page 3</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = crawler.extract_links(soup, "https://quotes.toscrape.com/page/2/")

        assert "https://quotes.toscrape.com/page/3/" in links

    def test_strips_url_fragments(self, crawler):
        """extract_links removes # fragments from URLs."""
        html = '<html><body><a href="/page/2/#top">Top</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = crawler.extract_links(soup, "https://quotes.toscrape.com/")

        assert "https://quotes.toscrape.com/page/2/" in links

    def test_no_links(self, crawler):
        """extract_links returns empty set when page has no links."""
        html = "<html><body><p>No links here</p></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        links = crawler.extract_links(soup, "https://quotes.toscrape.com/")

        assert links == set()

    def test_ignores_anchors_without_href(self, crawler):
        """extract_links skips anchor tags that have no href attribute."""
        html = '<html><body><a name="top">Top</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = crawler.extract_links(soup, "https://quotes.toscrape.com/")

        assert links == set()



class TestCrawl:
    """Tests for the full crawl method."""

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get")
    def test_crawl_collects_pages(self, mock_get, mock_sleep, crawler):
        """crawl returns a dict of URL to text content."""
        # Page 1 has a link to page 2
        page1_html = """
        <html><body>
            <p>Page one content</p>
            <a href="/page/2/">Next</a>
        </body></html>
        """
        # Page 2 has no further links
        page2_html = """
        <html><body>
            <p>Page two content</p>
        </body></html>
        """

        def side_effect(url, timeout=10):
            mock_resp = Mock()
            mock_resp.raise_for_status = Mock()
            if "page/2" in url:
                mock_resp.text = page2_html
            else:
                mock_resp.text = page1_html
            return mock_resp

        mock_get.side_effect = side_effect

        pages = crawler.crawl()

        assert len(pages) == 2
        assert any("Page one content" in text for text in pages.values())
        assert any("Page two content" in text for text in pages.values())

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get")
    def test_crawl_does_not_revisit_pages(self, mock_get, mock_sleep, crawler):
        """crawl only visits each URL once."""
        # Two pages that link to each other (circular)
        page1_html = """
        <html><body>
            <p>Page one</p>
            <a href="/page/2/">Next</a>
        </body></html>
        """
        page2_html = """
        <html><body>
            <p>Page two</p>
            <a href="/">Back to start</a>
        </body></html>
        """

        def side_effect(url, timeout=10):
            mock_resp = Mock()
            mock_resp.raise_for_status = Mock()
            if "page/2" in url:
                mock_resp.text = page2_html
            else:
                mock_resp.text = page1_html
            return mock_resp

        mock_get.side_effect = side_effect

        crawler.crawl()

        # Should have exactly 2 calls, not infinite
        assert mock_get.call_count == 2

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get")
    def test_crawl_respects_politeness_delay(self, mock_get, mock_sleep, crawler):
        """crawl waits between requests but not before the first one."""
        page1_html = """
        <html><body>
            <p>Page one</p>
            <a href="/page/2/">Next</a>
        </body></html>
        """
        page2_html = "<html><body><p>Page two</p></body></html>"

        def side_effect(url, timeout=10):
            mock_resp = Mock()
            mock_resp.raise_for_status = Mock()
            if "page/2" in url:
                mock_resp.text = page2_html
            else:
                mock_resp.text = page1_html
            return mock_resp

        mock_get.side_effect = side_effect

        crawler.crawl()

        # Sleep should be called once (before page 2, not before page 1)
        mock_sleep.assert_called_once_with(crawler.base_timeout)

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get")
    def test_crawl_skips_failed_pages(self, mock_get, mock_sleep, crawler):
        """crawl continues if a page fails to fetch."""
        import requests as req

        def side_effect(url, timeout=10):
            if "page/2" in url:
                raise req.exceptions.ConnectionError("Failed")
            mock_resp = Mock()
            mock_resp.raise_for_status = Mock()
            mock_resp.text = """
            <html><body>
                <p>Good page</p>
                <a href="/page/2/">Broken link</a>
            </body></html>
            """
            return mock_resp

        mock_get.side_effect = side_effect

        pages = crawler.crawl()

        # Only the successful page should be in results
        assert len(pages) == 1

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get")
    def test_crawl_resets_state(self, mock_get, mock_sleep, crawler):
        """Calling crawl twice starts fresh each time."""
        html = "<html><body><p>Hello</p></body></html>"
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.text = html
        mock_get.return_value = mock_resp

        pages1 = crawler.crawl()
        pages2 = crawler.crawl()

        # Both crawls should return the same result
        assert len(pages1) == len(pages2)

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get")
    def test_crawl_ignores_external_links(self, mock_get, mock_sleep, crawler):
        """crawl does not follow links to other domains."""
        html = """
        <html><body>
            <p>Content</p>
            <a href="https://evil.com/hack">External</a>
        </body></html>
        """
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.text = html
        mock_get.return_value = mock_resp

        crawler.crawl()

        # Should only fetch the base URL, never the external link
        assert mock_get.call_count == 1


class TestEdgeCases:
    """Tests for edge case handling in the crawler."""

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get")
    def test_retry_on_failure(self, mock_get, mock_sleep, crawler):
        """fetch_page retries on transient errors before giving up."""
        import requests as req
        mock_get.side_effect = [
            req.exceptions.ConnectionError("Fail 1"),
            req.exceptions.ConnectionError("Fail 2"),
            req.exceptions.ConnectionError("Fail 3"),
        ]

        result = crawler.fetch_page("https://quotes.toscrape.com/")

        assert result is None
        assert mock_get.call_count == 3

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get")
    def test_retry_succeeds_on_second_attempt(self, mock_get, mock_sleep, crawler):
        """fetch_page returns successfully after a transient failure."""
        import requests as req

        success_response = Mock()
        success_response.text = "<html><body><p>Success</p></body></html>"
        success_response.raise_for_status = Mock()

        mock_get.side_effect = [
            req.exceptions.ConnectionError("Fail 1"),
            success_response,
        ]

        result = crawler.fetch_page("https://quotes.toscrape.com/")

        assert result is not None
        assert result.find("p").text == "Success"
        assert mock_get.call_count == 2

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get")
    def test_retry_backoff_timing(self, mock_get, mock_sleep, crawler):
        """Retry delays increase with each attempt (exponential backoff)."""
        import requests as req
        mock_get.side_effect = [
            req.exceptions.ConnectionError("Fail 1"),
            req.exceptions.ConnectionError("Fail 2"),
            req.exceptions.ConnectionError("Fail 3"),
        ]

        crawler.fetch_page("https://quotes.toscrape.com/")

        # First retry: base_timeout * 1, second retry: base_timeout * 2
        calls = mock_sleep.call_args_list
        assert calls[0][0][0] == crawler.base_timeout * 1
        assert calls[1][0][0] == crawler.base_timeout * 2

    def test_extract_links_skips_javascript(self, crawler):
        """extract_links ignores javascript: links."""
        html = '<html><body><a href="javascript:void(0)">Click</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = crawler.extract_links(soup, "https://quotes.toscrape.com/")

        assert links == set()

    def test_extract_links_skips_mailto(self, crawler):
        """extract_links ignores mailto: links."""
        html = '<html><body><a href="mailto:test@example.com">Email</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = crawler.extract_links(soup, "https://quotes.toscrape.com/")

        assert links == set()

    def test_extract_links_skips_empty_href(self, crawler):
        """extract_links ignores empty href attributes."""
        html = '<html><body><a href="">Empty</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = crawler.extract_links(soup, "https://quotes.toscrape.com/")

        assert links == set()

    def test_extract_text_empty_after_stripping(self, crawler):
        """Pages with only scripts/styles produce empty text."""
        html = """
        <html><body>
            <script>var x = 1;</script>
            <style>.foo { color: red; }</style>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        text = crawler.extract_text(soup)

        assert text.strip() == ""

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get")
    def test_crawl_skips_empty_text_pages(self, mock_get, mock_sleep, crawler):
        """Pages with no meaningful text are not included in results."""
        html = """
        <html><body>
            <script>var x = 1;</script>
        </body></html>
        """
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.text = html
        mock_get.return_value = mock_resp

        pages = crawler.crawl()

        assert len(pages) == 0