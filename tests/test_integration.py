"""
Integration tests for the search engine tool.

Tests the full pipeline from crawling through to search,
using mocked HTTP responses to avoid hitting the live website.
These tests verify that all components work together correctly.
"""

import sys
import os
import json
import pytest
from unittest.mock import patch, Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from crawler import Crawler
from indexer import Indexer
from search import SearchEngine


# Realistic HTML pages resembling quotes.toscrape.com
MOCK_PAGES = {
    "https://quotes.toscrape.com/": """
    <html>
    <head><title>Quotes to Scrape</title></head>
    <body>
        <div class="quote">
            <span class="text">"The world as we have created it is a process
            of our thinking. It cannot be changed without changing our thinking."</span>
            <small class="author">Albert Einstein</small>
            <div class="tags">
                <a class="tag" href="/tag/change/page/1/">change</a>
                <a class="tag" href="/tag/thinking/page/1/">thinking</a>
            </div>
        </div>
        <div class="quote">
            <span class="text">"It is our choices, Harry, that show what we
            truly are, far more than our abilities."</span>
            <small class="author">J.K. Rowling</small>
        </div>
        <nav>
            <ul class="pager">
                <li class="next"><a href="/page/2/">Next</a></li>
            </ul>
        </nav>
    </body>
    </html>
    """,
    "https://quotes.toscrape.com/page/2/": """
    <html>
    <head><title>Quotes to Scrape</title></head>
    <body>
        <div class="quote">
            <span class="text">"There are only two ways to live your life.
            One is as though nothing is a miracle. The other is as though
            everything is a miracle."</span>
            <small class="author">Albert Einstein</small>
        </div>
        <div class="quote">
            <span class="text">"Good friends, good books, and a sleepy
            conscience: this is the ideal life."</span>
            <small class="author">Mark Twain</small>
        </div>
        <nav>
            <ul class="pager">
                <li class="previous"><a href="/">Previous</a></li>
            </ul>
        </nav>
    </body>
    </html>
    """,
}


def mock_get(url, timeout=10):
    """Mock requests.get to return pre-defined HTML pages."""
    mock_resp = Mock()
    mock_resp.raise_for_status = Mock()

    # Normalise URL for lookup
    if url in MOCK_PAGES:
        mock_resp.text = MOCK_PAGES[url]
    else:
        # Return empty page for unknown URLs (tag pages etc.)
        mock_resp.text = "<html><body><p>Empty page</p></body></html>"

    return mock_resp


class TestFullPipeline:
    """End-to-end tests for the complete search engine pipeline."""

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get", side_effect=mock_get)
    def test_crawl_build_and_search(self, mock_req, mock_sleep):
        """Full pipeline: crawl -> build index -> search returns results."""
        crawler = Crawler()
        indexer = Indexer()
        search_engine = SearchEngine(indexer)

        # Crawl
        pages = crawler.crawl()
        assert len(pages) >= 2

        # Build index
        indexer.build_index(pages)
        assert indexer.get_vocabulary_size() > 0
        assert indexer.page_count >= 2

        # Search for a word present on both pages
        results = search_engine.find("einstein")
        assert len(results) >= 1

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get", side_effect=mock_get)
    def test_save_load_preserves_search(self, mock_req, mock_sleep, tmp_path):
        """Index produces identical search results after save/load cycle."""
        crawler = Crawler()
        indexer = Indexer()
        search_engine = SearchEngine(indexer)

        pages = crawler.crawl()
        indexer.build_index(pages)

        # Search before save
        results_before = search_engine.find("thinking")

        # Save and load into a fresh indexer
        filepath = str(tmp_path / "index.json")
        indexer.save_index(filepath)

        new_indexer = Indexer()
        new_indexer.load_index(filepath)
        new_search = SearchEngine(new_indexer)

        # Search after load
        results_after = new_search.find("thinking")

        assert len(results_before) == len(results_after)
        urls_before = [url for url, _ in results_before]
        urls_after = [url for url, _ in results_after]
        assert set(urls_before) == set(urls_after)

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get", side_effect=mock_get)
    def test_multiword_search_accuracy(self, mock_req, mock_sleep):
        """Multi-word AND search returns only pages with all terms."""
        crawler = Crawler()
        indexer = Indexer()
        search_engine = SearchEngine(indexer)

        pages = crawler.crawl()
        indexer.build_index(pages)

        results = search_engine.find("good friends")
        urls = [url for url, _ in results]

        # "good friends" only appears on page 2
        for url in urls:
            entry_good = indexer.get_entry("good")
            entry_friends = indexer.get_entry("friends")
            assert url in entry_good
            assert url in entry_friends

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get", side_effect=mock_get)
    def test_phrase_search_accuracy(self, mock_req, mock_sleep):
        """Phrase search only returns pages with adjacent terms."""
        crawler = Crawler()
        indexer = Indexer()
        search_engine = SearchEngine(indexer)

        pages = crawler.crawl()
        indexer.build_index(pages)

        # "good friends" should appear as adjacent words on page 2
        phrase_results = search_engine.find('"good friends"')
        and_results = search_engine.find("good friends")

        phrase_urls = {url for url, _ in phrase_results}
        and_urls = {url for url, _ in and_results}

        # Phrase results must be a subset of AND results
        assert phrase_urls.issubset(and_urls)

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get", side_effect=mock_get)
    def test_print_after_build(self, mock_req, mock_sleep):
        """print_word returns correct data after building index."""
        crawler = Crawler()
        indexer = Indexer()
        search_engine = SearchEngine(indexer)

        pages = crawler.crawl()
        indexer.build_index(pages)

        entry = search_engine.print_word("miracle")
        assert entry is not None
        for url, stats in entry.items():
            assert stats["frequency"] > 0
            assert len(stats["positions"]) == stats["frequency"]
            assert stats["tf"] > 0

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get", side_effect=mock_get)
    def test_case_insensitive_end_to_end(self, mock_req, mock_sleep):
        """Case insensitivity works through the entire pipeline."""
        crawler = Crawler()
        indexer = Indexer()
        search_engine = SearchEngine(indexer)

        pages = crawler.crawl()
        indexer.build_index(pages)

        # "Einstein" appears in HTML with capital E
        results_lower = search_engine.find("einstein")
        results_upper = search_engine.find("EINSTEIN")

        urls_lower = {url for url, _ in results_lower}
        urls_upper = {url for url, _ in results_upper}
        assert urls_lower == urls_upper

    @patch("crawler.time.sleep")
    @patch("crawler.requests.get", side_effect=mock_get)
    def test_query_suggestions_end_to_end(self, mock_req, mock_sleep, capsys):
        """Misspelled words trigger suggestions from the real vocabulary."""
        crawler = Crawler()
        indexer = Indexer()
        search_engine = SearchEngine(indexer)

        pages = crawler.crawl()
        indexer.build_index(pages)

        # "einsten" is a typo for "einstein"
        search_engine.find("einsten")
        captured = capsys.readouterr()
        assert "Did you mean" in captured.out