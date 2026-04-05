"""
search.py - Search engine query processing.

Handles the print and find commands against the inverted index.

Design decisions:
    - print outputs structured, human-readable data including frequency,
      positions, and TF-IDF score per page, so users can inspect the
      index internals and verify correctness.
    - find performs set intersection for multi-word queries: a page must
      contain ALL query terms to be returned. Results are ranked by the
      sum of TF-IDF scores across all query terms, so pages where the
      terms are most prominent appear first.
    - Word normalisation is applied to queries so lookups are
      case-insensitive, consistent with how the index was built.

Algorithmic trade-offs:
    - Set intersection is O(min(|S1|, |S2|, ...)) per pair, which is
      efficient when postings lists are small. For very large corpora,
      postings could be sorted by document ID for merge-based intersection.
    - TF-IDF summation is a simple but effective ranking signal. More
      advanced approaches (BM25, proximity boosting) could improve
      relevance but add complexity beyond the assignment scope.
"""

from typing import Optional, Dict, List, Tuple
from text_processor import tokenise, normalise_word


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

    def find(self, query: str) -> List[Tuple[str, float]]:
        """
        Find pages containing all search terms, ranked by TF-IDF.

        For multi-word queries, returns only pages where every term
        appears. Results are sorted by the sum of TF-IDF scores across
        all query terms (descending), so the most relevant pages appear first.

        Args:
            query: One or more search terms separated by spaces.

        Returns:
            A list of (url, combined_tfidf_score) tuples sorted by
            relevance, or an empty list if no matches are found.

        Complexity:
            O(T * P) where T is the number of query terms and P is
            the average postings list length, plus O(R log R) for
            sorting R results.
        """
        terms = tokenise(query)

        if not terms:
            print("Error: No valid search terms provided.")
            return []

        # Collect postings for each term
        term_postings = {}
        missing_terms = []

        for term in terms:
            entry = self.indexer.get_entry(term)
            if entry is None:
                missing_terms.append(term)
            else:
                term_postings[term] = entry

        # If any term has no results, intersection is empty
        if missing_terms:
            print(f"No results: the following terms were not found in the index:")
            for term in missing_terms:
                print(f"  - '{term}'")
            return []

        # Find pages that contain ALL terms (set intersection)
        page_sets = [set(postings.keys()) for postings in term_postings.values()]
        matching_pages = page_sets[0]
        for page_set in page_sets[1:]:
            matching_pages = matching_pages.intersection(page_set)

        if not matching_pages:
            print(f"No pages contain all of the search terms: {', '.join(terms)}")
            return []

        # Rank by sum of TF-IDF scores across all query terms
        ranked_results = []
        for url in matching_pages:
            combined_score = sum(
                term_postings[term][url]["tfidf"] for term in terms
            )
            ranked_results.append((url, combined_score))

        # Sort by score descending (highest relevance first)
        ranked_results.sort(key=lambda x: x[1], reverse=True)

        # Display results
        print(f"\nSearch results for '{query}':")
        print(f"  Found {len(ranked_results)} matching page(s):\n")

        for rank, (url, score) in enumerate(ranked_results, start=1):
            print(f"  {rank}. {url}")
            print(f"     Relevance score: {score:.4f}")

            # Show per-term breakdown
            for term in terms:
                stats = term_postings[term][url]
                print(f"     '{term}': frequency={stats['frequency']}, "
                      f"positions={stats['positions']}")
            print()

        return ranked_results