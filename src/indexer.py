"""
indexer.py - Inverted index builder and manager.

Builds an inverted index from crawled page content, storing per-word,
per-document statistics including term frequency, word positions,
and TF-IDF scores for relevance ranking.

Index structure:
    {
        "word": {
            "url": {
                "frequency": int,       # raw count of occurrences
                "positions": [int],     # 0-based word positions in page
                "tf": float,            # term frequency (count / total words)
                "tfidf": float          # TF-IDF score (computed after full build)
            }
        }
    }

Design decisions:
    - Positions are stored to enable future phrase/proximity search.
    - TF-IDF is pre-computed at build time rather than at query time.
      This trades slightly higher build cost for O(1) score lookup
      during search, which is the more frequent operation.
    - The full index (including metadata) is serialised as a single
      JSON file for simplicity and portability.

Complexity:
    - build_index: O(N) where N is total word count across all pages.
    - TF-IDF computation: O(V * D) where V is vocabulary size and
      D is number of documents, though in practice each word only
      appears in a subset of documents.
"""

import json
import math
import os
from typing import Dict, List, Optional
from text_processor import tokenise


class Indexer:
    """Builds and manages an inverted index from crawled pages."""

    def __init__(self) -> None:
        self.index: Dict[str, Dict[str, Dict]] = {}
        self.page_count: int = 0
        self.page_word_counts: Dict[str, int] = {}  # url -> total word count

    def build_index(self, pages: Dict[str, str]) -> None:
        """
        Build the inverted index from crawled pages.

        Tokenises each page, records word frequency and positions,
        then computes TF-IDF scores across the entire corpus.

        Args:
            pages: Dictionary mapping URL to raw text content.

        Complexity:
            O(N + V*D) where N = total words, V = vocabulary size,
            D = number of documents.
        """
        # Reset index for a clean build
        self.index = {}
        self.page_count = len(pages)
        self.page_word_counts = {}

        # Pass 1: Build raw frequency and position data
        for url, text in pages.items():
            tokens = tokenise(text)
            self.page_word_counts[url] = len(tokens)

            for position, word in enumerate(tokens):
                if word not in self.index:
                    self.index[word] = {}

                if url not in self.index[word]:
                    self.index[word][url] = {
                        "frequency": 0,
                        "positions": [],
                        "tf": 0.0,
                        "tfidf": 0.0,
                    }

                self.index[word][url]["frequency"] += 1
                self.index[word][url]["positions"].append(position)

        # Pass 2: Compute TF and TF-IDF scores
        self._compute_tfidf()

        print(f"  Index built: {len(self.index)} unique words across {self.page_count} pages.")

    def _compute_tfidf(self) -> None:
        """
        Compute TF-IDF scores for every word-document pair in the index.

        Uses the standard formula:
            TF(t,d)  = count(t in d) / total_words(d)
            IDF(t)   = log(N / df(t))
            TF-IDF   = TF * IDF

        where N is total document count and df(t) is the number of
        documents containing term t.

        Complexity:
            O(V * D) where V is vocabulary size, D is average documents
            per term.
        """
        for word, postings in self.index.items():
            # Document frequency: how many documents contain this word
            df = len(postings)
            idf = math.log(self.page_count / df) if df > 0 else 0.0

            for url, stats in postings.items():
                total_words = self.page_word_counts.get(url, 1)
                tf = stats["frequency"] / total_words
                stats["tf"] = round(tf, 6)
                stats["tfidf"] = round(tf * idf, 6)

    def save_index(self, filepath: str) -> None:
        """
        Save the inverted index and metadata to a JSON file.

        Args:
            filepath: Path to the output JSON file.

        Raises:
            IOError: If the file cannot be written.
        """
        # Ensure the directory exists
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)

        data = {
            "metadata": {
                "page_count": self.page_count,
                "vocabulary_size": len(self.index),
                "page_word_counts": self.page_word_counts,
            },
            "index": self.index,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_index(self, filepath: str) -> bool:
        """
        Load the inverted index and metadata from a JSON file.

        Args:
            filepath: Path to the JSON index file.

        Returns:
            True if the index was loaded successfully, False otherwise.
        """
        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.index = data["index"]
            self.page_count = data["metadata"]["page_count"]
            self.page_word_counts = data["metadata"]["page_word_counts"]

            print(f"  Index loaded: {len(self.index)} words, {self.page_count} pages.")
            return True

        except (json.JSONDecodeError, KeyError) as e:
            print(f"  Error loading index: {e}")
            return False

    def get_entry(self, word: str) -> Optional[Dict[str, Dict]]:
        """
        Retrieve the index entry for a given word.

        Args:
            word: The word to look up (should be pre-normalised).

        Returns:
            Dictionary of {url: stats} if the word exists, None otherwise.

        Complexity:
            O(1) average case (hash table lookup).
        """
        return self.index.get(word, None)

    def get_vocabulary_size(self) -> int:
        """Return the number of unique words in the index."""
        return len(self.index)