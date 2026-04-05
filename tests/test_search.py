"""Tests for the search module."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from indexer import Indexer
from search import SearchEngine


@pytest.fixture
def indexer():
    """Create an indexer with a pre-built index."""
    idx = Indexer()
    idx.build_index({
        "https://quotes.toscrape.com/": (
            "The world as we have created it is a process of our thinking"
        ),
        "https://quotes.toscrape.com/page/2/": (
            "Good friends good books and a sleepy conscience"
        ),
        "https://quotes.toscrape.com/page/3/": (
            "The world is a fine place and worth the fighting for"
        ),
    })
    return idx


@pytest.fixture
def search_engine(indexer):
    """Create a SearchEngine with a pre-built index."""
    return SearchEngine(indexer)


class TestPrintWord:
    """Tests for the print_word method."""

    def test_existing_word_returns_entry(self, search_engine):
        """print_word returns the index entry for a word that exists."""
        result = search_engine.print_word("good")
        assert result is not None
        assert isinstance(result, dict)

    def test_existing_word_has_correct_pages(self, search_engine):
        """Returned entry contains the correct page URLs."""
        result = search_engine.print_word("good")
        assert "https://quotes.toscrape.com/page/2/" in result

    def test_existing_word_has_stats(self, search_engine):
        """Each page entry contains frequency, positions, tf, and tfidf."""
        result = search_engine.print_word("good")
        for url, stats in result.items():
            assert "frequency" in stats
            assert "positions" in stats
            assert "tf" in stats
            assert "tfidf" in stats

    def test_nonexistent_word_returns_none(self, search_engine):
        """print_word returns None for a word not in the index."""
        result = search_engine.print_word("zzzznotaword")
        assert result is None

    def test_case_insensitive_lookup(self, search_engine):
        """print_word normalises input to lowercase."""
        result_lower = search_engine.print_word("good")
        result_upper = search_engine.print_word("GOOD")
        result_mixed = search_engine.print_word("GoOd")

        assert result_lower == result_upper == result_mixed

    def test_empty_word_returns_none(self, search_engine):
        """print_word returns None for empty input."""
        result = search_engine.print_word("")
        assert result is None

    def test_whitespace_word_returns_none(self, search_engine):
        """print_word returns None for whitespace-only input."""
        result = search_engine.print_word("   ")
        assert result is None

    def test_output_formatting(self, search_engine, capsys):
        """print_word outputs readable formatted text."""
        search_engine.print_word("good")
        captured = capsys.readouterr()

        assert "Index entry for 'good'" in captured.out
        assert "URL:" in captured.out
        assert "Frequency:" in captured.out
        assert "Positions:" in captured.out
        assert "TF-IDF:" in captured.out

    def test_not_found_message(self, search_engine, capsys):
        """print_word displays a clear message for missing words."""
        search_engine.print_word("zzzznotaword")
        captured = capsys.readouterr()

        assert "not found" in captured.out







class TestFind:
    """Tests for the find method."""

    def test_single_word_returns_results(self, search_engine):
        """find returns matching pages for a single word."""
        results = search_engine.find("world")
        assert len(results) >= 1
        # Results are (url, score) tuples
        urls = [url for url, score in results]
        assert any("quotes.toscrape.com" in url for url in urls)

    def test_single_word_returns_tuples(self, search_engine):
        """find returns a list of (url, score) tuples."""
        results = search_engine.find("world")
        for item in results:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], str)
            assert isinstance(item[1], float)

    def test_multi_word_intersection(self, search_engine):
        """find with multiple words returns only pages containing ALL terms."""
        results = search_engine.find("good friends")
        urls = [url for url, score in results]

        # Page 2 has both "good" and "friends"
        assert "https://quotes.toscrape.com/page/2/" in urls

        # Page 1 and 3 don't have "friends"
        assert "https://quotes.toscrape.com/" not in urls
        assert "https://quotes.toscrape.com/page/3/" not in urls

    def test_results_ranked_by_tfidf(self, search_engine):
        """Results are sorted by combined TF-IDF score descending."""
        results = search_engine.find("the")
        scores = [score for url, score in results]
        assert scores == sorted(scores, reverse=True)

    def test_nonexistent_word_returns_empty(self, search_engine):
        """find returns empty list when a term is not in the index."""
        results = search_engine.find("zzzznotaword")
        assert results == []

    def test_no_common_pages_returns_empty(self, search_engine):
        """find returns empty list when no page has all terms."""
        # "conscience" is only on page 2, "fighting" is only on page 3
        results = search_engine.find("conscience fighting")
        assert results == []

    def test_case_insensitive_query(self, search_engine):
        """find normalises query terms to lowercase."""
        results_lower = search_engine.find("good")
        results_upper = search_engine.find("GOOD")
        results_mixed = search_engine.find("GoOd")

        urls_lower = [url for url, _ in results_lower]
        urls_upper = [url for url, _ in results_upper]
        urls_mixed = [url for url, _ in results_mixed]

        assert urls_lower == urls_upper == urls_mixed

    def test_empty_query_returns_empty(self, search_engine):
        """find returns empty list for an empty query string."""
        results = search_engine.find("")
        assert results == []

    def test_symbols_only_query_returns_empty(self, search_engine):
        """find returns empty list when query has no valid tokens."""
        results = search_engine.find("!!! @#$ 123")
        assert results == []

    def test_duplicate_terms_handled(self, search_engine):
        """find handles repeated terms in the query gracefully."""
        results = search_engine.find("good good")
        assert len(results) >= 1

    def test_missing_term_message(self, search_engine, capsys):
        """find displays which terms were not found."""
        search_engine.find("zzzznotaword")
        captured = capsys.readouterr()
        assert "not found" in captured.out
        assert "zzzznotaword" in captured.out

    def test_output_shows_ranking(self, search_engine, capsys):
        """find output includes rank numbers and relevance scores."""
        search_engine.find("world")
        captured = capsys.readouterr()
        assert "1." in captured.out
        assert "Relevance score:" in captured.out

    def test_output_shows_per_term_breakdown(self, search_engine, capsys):
        """find output shows frequency and positions for each term."""
        search_engine.find("good friends")
        captured = capsys.readouterr()
        assert "frequency=" in captured.out
        assert "positions=" in captured.out