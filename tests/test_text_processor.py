"""Tests for the text processing module."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from text_processor import tokenise, normalise_word


class TestTokenise:
    """Tests for the tokenise function."""

    def test_basic_sentence(self):
        """Tokenises a simple sentence into lowercase words."""
        assert tokenise("Good friends and good books") == [
            "good", "friends", "and", "good", "books"
        ]

    def test_strips_punctuation(self):
        """Removes all punctuation from tokens."""
        assert tokenise("Hello, world! How's it going?") == [
            "hello", "world", "how", "s", "it", "going"
        ]

    def test_case_normalisation(self):
        """Converts all tokens to lowercase."""
        assert tokenise("The QUICK Brown FOX") == [
            "the", "quick", "brown", "fox"
        ]

    def test_empty_string(self):
        """Returns empty list for empty input."""
        assert tokenise("") == []

    def test_numbers_only(self):
        """Discards numeric-only tokens."""
        assert tokenise("123 456 789") == []

    def test_symbols_only(self):
        """Discards symbol-only tokens."""
        assert tokenise("@#$ !!! ***") == []

    def test_mixed_content(self):
        """Extracts words from text mixed with numbers and symbols."""
        assert tokenise("Page 1: Hello 2nd world!") == [
            "page", "hello", "nd", "world"
        ]

    def test_preserves_order_and_duplicates(self):
        """Keeps tokens in order and retains duplicates for position tracking."""
        assert tokenise("the cat sat on the mat") == [
            "the", "cat", "sat", "on", "the", "mat"
        ]

    def test_whitespace_variations(self):
        """Handles tabs, newlines, and multiple spaces."""
        assert tokenise("hello\tworld\n  foo   bar") == [
            "hello", "world", "foo", "bar"
        ]


class TestNormaliseWord:
    """Tests for the normalise_word function."""

    def test_lowercase(self):
        """Converts uppercase to lowercase."""
        assert normalise_word("HELLO") == "hello"

    def test_mixed_case(self):
        """Handles mixed case input."""
        assert normalise_word("GoOd") == "good"

    def test_strips_whitespace(self):
        """Strips leading and trailing whitespace."""
        assert normalise_word("  hello  ") == "hello"

    def test_already_normalised(self):
        """Returns unchanged if already normalised."""
        assert normalise_word("hello") == "hello"

    def test_empty_string(self):
        """Handles empty string input."""
        assert normalise_word("") == ""