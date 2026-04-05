"""
search.py - Search engine query processing.

Handles the print and find commands against the inverted index.
The print command displays the full index entry for a single word.
The find command (Step 8) will support multi-word queries with TF-IDF ranking.

Design decisions:
    - print outputs structured, human-readable data including frequency,
      positions, and TF-IDF score per page, so users can inspect the
      index internals and verify correctness.
    - Word normalisation is applied to queries so lookups are
      case-insensitive, consistent with how the index was built.
"""

from typing import Optional, Dict
from text_processor import normalise_word


class SearchEngine:
    """Processes search queries against the inverted index."""

    def __init__(self, indexer) -> None:
        """
        Initialise the search engine with a reference to the indexer.

        Args:
            indexer: An Indexer instance containing the inverted index.
        """
        self.indexer = indexer

    def print_word(self, word: str) -> Optional[Dict[str, Dict]]:
        """
        Print the inverted index entry for a given word.

        Displays frequency, positions, TF, and TF-IDF score for
        every page the word appears on. Also returns the entry
        dict for programmatic use and testability.

        Args:
            word: The word to look up (case-insensitive).

        Returns:
            The index entry dict if the word exists, None otherwise.

        Complexity:
            O(1) for the lookup, O(P) for display where P is the
            number of pages containing the word.
        """
        normalised = normalise_word(word)

        if not normalised:
            print("Error: No word provided.")
            return None

        entry = self.indexer.get_entry(normalised)

        if entry is None:
            print(f"Word '{normalised}' not found in the index.")
            return None

        print(f"\nIndex entry for '{normalised}':")
        print(f"  Appears in {len(entry)} page(s):\n")

        for url, stats in entry.items():
            print(f"  URL:       {url}")
            print(f"  Frequency: {stats['frequency']}")
            print(f"  Positions: {stats['positions']}")
            print(f"  TF:        {stats['tf']}")
            print(f"  TF-IDF:    {stats['tfidf']}")
            print()

        return entry

    def find(self, query: str) -> None:
        """Find pages containing all search terms in the query."""
        # TODO: Implement in Step 8
        raise NotImplementedError("Find not yet implemented")