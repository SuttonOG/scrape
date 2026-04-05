"""
indexer.py - Inverted index builder and manager

Responsible for processing crawled page text into an inverted index
storing word frequency, positions, and TF-IDF scores.
"""


class Indexer:
    """Builds and manages an inverted index from crawled pages."""

    def __init__(self):
        self.index = {}       # word -> {url: {frequency, positions}}
        self.page_count = 0   # total number of pages indexed

    def build_index(self, pages):
        """Build the inverted index from a dict of {url: text_content}."""
        raise NotImplementedError("Indexer not yet implemented")

    def save_index(self, filepath):
        """Save the inverted index to a JSON file."""
        raise NotImplementedError("Save not yet implemented")

    def load_index(self, filepath):
        """Load the inverted index from a JSON file. Returns True on success."""
        raise NotImplementedError("Load not yet implemented")