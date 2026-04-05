"""
search.py - Search engine query processing

Responsible for handling print and find commands against
the inverted index, including multi-word queries and ranking.
"""


class SearchEngine:
    """Processes search queries against the inverted index."""

    def __init__(self, indexer):
        self.indexer = indexer

    def print_word(self, word):
        """Print the inverted index entry for a given word."""
        raise NotImplementedError("Print not yet implemented")

    def find(self, query):
        """Find pages containing all search terms in the query."""
        raise NotImplementedError("Find not yet implemented")