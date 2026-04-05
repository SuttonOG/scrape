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