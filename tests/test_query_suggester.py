"""Tests for the query suggestion module."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from query_suggester import levenshtein_distance, suggest_words


class TestLevenshteinDistance:
    """Tests for the Levenshtein distance function."""

    def test_identical_strings(self):
        """Distance between identical strings is 0."""
        assert levenshtein_distance("hello", "hello") == 0

    def test_empty_strings(self):
        """Distance between two empty strings is 0."""
        assert levenshtein_distance("", "") == 0

    def test_one_empty_string(self):
        """Distance from empty to a word is the word length."""
        assert levenshtein_distance("", "abc") == 3
        assert levenshtein_distance("abc", "") == 3

    def test_single_insertion(self):
        """One character difference by insertion."""
        assert levenshtein_distance("cat", "cats") == 1

    def test_single_deletion(self):
        """One character difference by deletion."""
        assert levenshtein_distance("cats", "cat") == 1

    def test_single_substitution(self):
        """One character difference by substitution."""
        assert levenshtein_distance("cat", "car") == 1

    def test_multiple_edits(self):
        """Multiple edits required."""
        assert levenshtein_distance("kitten", "sitting") == 3

    def test_completely_different(self):
        """Totally different strings."""
        assert levenshtein_distance("abc", "xyz") == 3

    def test_symmetric(self):
        """Distance is the same regardless of argument order."""
        assert levenshtein_distance("hello", "hallo") == levenshtein_distance("hallo", "hello")

    def test_case_sensitive(self):
        """Function is case-sensitive (normalisation is caller's job)."""
        assert levenshtein_distance("Hello", "hello") == 1


class TestSuggestWords:
    """Tests for the suggest_words function."""

    def test_exact_match_returns_zero_distance(self):
        """An exact match has distance 0."""
        vocab = {"hello": {}, "world": {}, "help": {}}
        suggestions = suggest_words("hello", vocab)
        assert suggestions[0] == ("hello", 0)

    def test_close_typo(self):
        """Finds words within edit distance of 1."""
        vocab = {"friends": {}, "fiends": {}, "fences": {}}
        suggestions = suggest_words("frends", vocab)
        words = [w for w, d in suggestions]
        assert "friends" in words

    def test_respects_max_distance(self):
        """Only returns words within max_distance."""
        vocab = {"hello": {}, "world": {}, "help": {}}
        suggestions = suggest_words("xxxxx", vocab, max_distance=1)
        assert suggestions == []

    def test_respects_max_suggestions(self):
        """Returns at most max_suggestions results."""
        vocab = {f"word{i}": {} for i in range(100)}
        suggestions = suggest_words("word", vocab, max_distance=5, max_suggestions=3)
        assert len(suggestions) <= 3

    def test_sorted_by_distance_then_alpha(self):
        """Results are sorted by distance first, then alphabetically."""
        vocab = {"cat": {}, "car": {}, "bat": {}, "cap": {}}
        suggestions = suggest_words("cat", vocab, max_distance=2)

        distances = [d for w, d in suggestions]
        assert distances == sorted(distances)

        # Within same distance, should be alphabetical
        same_dist = [(w, d) for w, d in suggestions if d == 1]
        words_at_dist_1 = [w for w, d in same_dist]
        assert words_at_dist_1 == sorted(words_at_dist_1)

    def test_empty_vocabulary(self):
        """Returns empty list for empty vocabulary."""
        suggestions = suggest_words("hello", {})
        assert suggestions == []

    def test_length_filter_optimisation(self):
        """Words with length difference > max_distance are skipped."""
        vocab = {"a": {}, "abcdefghij": {}, "cat": {}}
        suggestions = suggest_words("ca", vocab, max_distance=1)
        words = [w for w, d in suggestions]
        # "abcdefghij" is too different in length to be within distance 1
        assert "abcdefghij" not in words