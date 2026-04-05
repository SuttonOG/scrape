"""Tests for the indexer module."""

import sys
import os
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from indexer import Indexer


@pytest.fixture
def indexer():
    """Create a fresh Indexer instance for each test."""
    return Indexer()


@pytest.fixture
def sample_pages():
    """Sample crawled pages for testing."""
    return {
        "https://quotes.toscrape.com/": (
            "The world as we have created it is a process of our thinking"
        ),
        "https://quotes.toscrape.com/page/2/": (
            "Good friends good books and a sleepy conscience"
        ),
        "https://quotes.toscrape.com/page/3/": (
            "The world is a fine place and worth the fighting for"
        ),
    }


@pytest.fixture
def built_indexer(indexer, sample_pages):
    """Return an indexer with a pre-built index."""
    indexer.build_index(sample_pages)
    return indexer


class TestBuildIndex:
    """Tests for the build_index method."""

    def test_indexes_all_words(self, built_indexer):
        """Every word from every page appears in the index."""
        assert "world" in built_indexer.index
        assert "good" in built_indexer.index
        assert "friends" in built_indexer.index
        assert "conscience" in built_indexer.index

    def test_case_insensitive(self, indexer):
        """Words are normalised to lowercase during indexing."""
        indexer.build_index({
            "https://example.com/": "Hello HELLO hello"
        })
        assert "hello" in indexer.index
        assert "Hello" not in indexer.index
        assert "HELLO" not in indexer.index

    def test_correct_frequency(self, built_indexer):
        """Word frequency is counted correctly per page."""
        # "good" appears twice on page 2
        page2 = "https://quotes.toscrape.com/page/2/"
        assert built_indexer.index["good"][page2]["frequency"] == 2

    def test_correct_positions(self, built_indexer):
        """Word positions are recorded correctly."""
        # "good" at positions 0 and 2 in "good friends good books and a sleepy conscience"
        page2 = "https://quotes.toscrape.com/page/2/"
        positions = built_indexer.index["good"][page2]["positions"]
        assert positions == [0, 2]

    def test_word_appears_in_multiple_pages(self, built_indexer):
        """Words shared across pages have entries for each page."""
        # "the" appears on page 1 and page 3
        assert len(built_indexer.index["the"]) >= 2

    def test_page_count(self, built_indexer):
        """page_count reflects the number of pages indexed."""
        assert built_indexer.page_count == 3

    def test_page_word_counts(self, built_indexer):
        """page_word_counts stores the total word count per page."""
        page2 = "https://quotes.toscrape.com/page/2/"
        # "good friends good books and a sleepy conscience" = 8 words
        assert built_indexer.page_word_counts[page2] == 8

    def test_empty_pages(self, indexer):
        """Building an index from empty input produces an empty index."""
        indexer.build_index({})
        assert indexer.index == {}
        assert indexer.page_count == 0

    def test_rebuild_resets_index(self, built_indexer):
        """Calling build_index again replaces the old index entirely."""
        built_indexer.build_index({
            "https://example.com/": "only one word here"
        })
        assert built_indexer.page_count == 1
        assert "conscience" not in built_indexer.index

    def test_punctuation_stripped(self, indexer):
        """Punctuation is removed during tokenisation."""
        indexer.build_index({
            "https://example.com/": 'Hello, world! "Quoted text."'
        })
        assert "hello" in indexer.index
        assert "world" in indexer.index
        assert "hello," not in indexer.index
        assert '"quoted' not in indexer.index


class TestTFIDF:
    """Tests for the TF-IDF computation."""

    def test_tf_calculated(self, built_indexer):
        """TF is frequency / total words in document."""
        page2 = "https://quotes.toscrape.com/page/2/"
        # "good" appears 2 times in 8 words -> tf = 0.25
        tf = built_indexer.index["good"][page2]["tf"]
        assert tf == pytest.approx(0.25)

    def test_tfidf_higher_for_rare_words(self, built_indexer):
        """Rare words should have higher TF-IDF than common words."""
        page2 = "https://quotes.toscrape.com/page/2/"
        # "conscience" only appears on page 2 (rare)
        # "a" appears on multiple pages (common)
        tfidf_rare = built_indexer.index["conscience"][page2]["tfidf"]
        tfidf_common = built_indexer.index["a"][page2]["tfidf"]
        assert tfidf_rare > tfidf_common

    def test_tfidf_zero_for_universal_words(self, indexer):
        """Words appearing in every document get IDF of 0, so TF-IDF is 0."""
        indexer.build_index({
            "https://example.com/1": "hello world",
            "https://example.com/2": "hello there",
        })
        # "hello" appears in both documents -> IDF = log(2/2) = 0
        assert indexer.index["hello"]["https://example.com/1"]["tfidf"] == 0.0

    def test_idf_increases_with_rarity(self, indexer):
        """IDF component increases as a word appears in fewer documents."""
        indexer.build_index({
            "https://example.com/1": "alpha beta gamma",
            "https://example.com/2": "alpha beta",
            "https://example.com/3": "alpha",
        })
        # alpha in 3 docs, beta in 2, gamma in 1
        tfidf_alpha = indexer.index["alpha"]["https://example.com/1"]["tfidf"]
        tfidf_beta = indexer.index["beta"]["https://example.com/1"]["tfidf"]
        tfidf_gamma = indexer.index["gamma"]["https://example.com/1"]["tfidf"]

        assert tfidf_gamma > tfidf_beta > tfidf_alpha


class TestSaveAndLoad:
    """Tests for save_index and load_index methods."""

    def test_save_creates_file(self, built_indexer, tmp_path):
        """save_index creates a JSON file at the given path."""
        filepath = str(tmp_path / "index.json")
        built_indexer.save_index(filepath)
        assert os.path.exists(filepath)

    def test_save_valid_json(self, built_indexer, tmp_path):
        """Saved file contains valid JSON."""
        filepath = str(tmp_path / "index.json")
        built_indexer.save_index(filepath)

        with open(filepath, "r") as f:
            data = json.load(f)

        assert "index" in data
        assert "metadata" in data

    def test_save_creates_directories(self, built_indexer, tmp_path):
        """save_index creates parent directories if they don't exist."""
        filepath = str(tmp_path / "nested" / "dir" / "index.json")
        built_indexer.save_index(filepath)
        assert os.path.exists(filepath)

    def test_load_restores_index(self, built_indexer, tmp_path):
        """load_index restores the full index from a saved file."""
        filepath = str(tmp_path / "index.json")
        built_indexer.save_index(filepath)

        new_indexer = Indexer()
        result = new_indexer.load_index(filepath)

        assert result is True
        assert new_indexer.page_count == built_indexer.page_count
        assert new_indexer.get_vocabulary_size() == built_indexer.get_vocabulary_size()
        assert "good" in new_indexer.index

    def test_load_restores_tfidf(self, built_indexer, tmp_path):
        """TF-IDF scores survive save/load cycle."""
        filepath = str(tmp_path / "index.json")
        built_indexer.save_index(filepath)

        new_indexer = Indexer()
        new_indexer.load_index(filepath)

        page2 = "https://quotes.toscrape.com/page/2/"
        original_tfidf = built_indexer.index["good"][page2]["tfidf"]
        loaded_tfidf = new_indexer.index["good"][page2]["tfidf"]
        assert loaded_tfidf == pytest.approx(original_tfidf)

    def test_load_nonexistent_file(self, indexer):
        """load_index returns False when file doesn't exist."""
        result = indexer.load_index("/tmp/nonexistent_file.json")
        assert result is False

    def test_load_corrupted_file(self, indexer, tmp_path):
        """load_index returns False for corrupted JSON."""
        filepath = str(tmp_path / "bad.json")
        with open(filepath, "w") as f:
            f.write("{corrupted json content")

        result = indexer.load_index(filepath)
        assert result is False

    def test_load_missing_keys(self, indexer, tmp_path):
        """load_index returns False when JSON is missing required keys."""
        filepath = str(tmp_path / "incomplete.json")
        with open(filepath, "w") as f:
            json.dump({"some": "data"}, f)

        result = indexer.load_index(filepath)
        assert result is False


class TestGetEntry:
    """Tests for the get_entry method."""

    def test_existing_word(self, built_indexer):
        """get_entry returns postings dict for an indexed word."""
        entry = built_indexer.get_entry("good")
        assert entry is not None
        assert isinstance(entry, dict)

    def test_nonexistent_word(self, built_indexer):
        """get_entry returns None for a word not in the index."""
        entry = built_indexer.get_entry("zzzznotaword")
        assert entry is None

    def test_entry_contains_expected_fields(self, built_indexer):
        """Each posting in the entry has frequency, positions, tf, and tfidf."""
        entry = built_indexer.get_entry("good")
        for url, stats in entry.items():
            assert "frequency" in stats
            assert "positions" in stats
            assert "tf" in stats
            assert "tfidf" in stats


class TestGetVocabularySize:
    """Tests for the get_vocabulary_size method."""

    def test_returns_word_count(self, built_indexer):
        """Returns the number of unique words in the index."""
        size = built_indexer.get_vocabulary_size()
        assert size > 0
        assert size == len(built_indexer.index)

    def test_empty_index(self, indexer):
        """Returns 0 for an empty index."""
        assert indexer.get_vocabulary_size() == 0