"""
search.py - Search engine query processing.

Handles the print and find commands against the inverted index.

Features:
    - print: displays the full index entry for a single word.
    - find: multi-word AND queries ranked by TF-IDF.
    - Phrase search: detects quoted phrases and uses word positions
      to find exact adjacent matches.
    - Query suggestions: offers "did you mean?" corrections for
      misspelled terms using Levenshtein distance.

Design decisions:
    - Set intersection is used for multi-word AND queries.
    - Phrase matching uses stored word positions: for a phrase of
      length K, we check that positions exist where each successive
      word is at position + 1 from the previous word. This is O(P)
      where P is the length of the shortest postings list.
    - TF-IDF summation ranks results by relevance.

Algorithmic trade-offs:
    - Position-based phrase search is accurate but requires storing
      all positions in the index, increasing storage. The trade-off
      is worthwhile because it enables exact phrase matching without
      re-scanning page content.
"""

from typing import Optional, Dict, List, Tuple, Set
from text_processor import tokenise, normalise_word
from query_suggester import suggest_words


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
            self._show_suggestions(normalised)
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

    def _show_suggestions(self, term: str) -> None:
        """
        Display query suggestions for a term not found in the index.

        Args:
            term: The normalised term that was not found.
        """
        suggestions = suggest_words(term, self.indexer.index)
        if suggestions:
            print("  Did you mean:")
            for word, distance in suggestions:
                print(f"    - {word}")

    def _check_phrase_match(
        self, terms: List[str], url: str, term_postings: Dict
    ) -> bool:
        """
        Check if the given terms appear as an exact adjacent phrase on a page.

        Uses stored word positions to verify that each term appears at
        consecutive positions (i.e., position[i+1] == position[i] + 1).

        Args:
            terms: Ordered list of search terms forming the phrase.
            url: The URL of the page to check.
            term_postings: Dictionary mapping each term to its index entry.

        Returns:
            True if the terms appear as an adjacent phrase on the page.

        Complexity:
            O(P) where P is the number of positions of the first term.
        """
        # Get positions of the first term on this page
        first_positions = term_postings[terms[0]][url]["positions"]

        for start_pos in first_positions:
            match = True
            for offset, term in enumerate(terms[1:], start=1):
                positions = term_postings[term][url]["positions"]
                if (start_pos + offset) not in positions:
                    match = False
                    break
            if match:
                return True

        return False

    def find(self, query: str) -> List[Tuple[str, float]]:
        """
        Find pages containing all search terms, ranked by TF-IDF.

        Supports two modes:
            - Phrase search: wrap terms in quotes, e.g. find "good friends"
              Only returns pages where the words appear adjacent and in order.
            - AND search: without quotes, e.g. find good friends
              Returns pages containing all terms anywhere on the page.

        Results are sorted by the sum of TF-IDF scores across all query
        terms (descending), so the most relevant pages appear first.

        Args:
            query: One or more search terms, optionally in quotes for phrase search.

        Returns:
            A list of (url, combined_tfidf_score) tuples sorted by
            relevance, or an empty list if no matches are found.

        Complexity:
            O(T * P) for term lookup and intersection, plus O(R * T * K)
            for phrase checking where K is average positions per term,
            plus O(R log R) for sorting R results.
        """
        # Detect phrase search (query wrapped in quotes)
        is_phrase = (
            len(query) >= 2
            and query[0] == '"'
            and query[-1] == '"'
        )

        if is_phrase:
            raw_query = query[1:-1]  # strip surrounding quotes
        else:
            raw_query = query

        terms = tokenise(raw_query)

        if not terms:
            print("Error: No valid search terms provided.")
            return []

        # Collect postings for each term
        term_postings: Dict[str, Dict] = {}
        missing_terms: List[str] = []

        for term in terms:
            entry = self.indexer.get_entry(term)
            if entry is None:
                missing_terms.append(term)
            else:
                term_postings[term] = entry

        # If any term is missing, show suggestions and return empty
        if missing_terms:
            print("No results: the following terms were not found in the index:")
            for term in missing_terms:
                print(f"  - '{term}'")
                self._show_suggestions(term)
            return []

        # Find pages that contain ALL terms (set intersection)
        page_sets = [set(postings.keys()) for postings in term_postings.values()]
        matching_pages: Set[str] = page_sets[0]
        for page_set in page_sets[1:]:
            matching_pages = matching_pages.intersection(page_set)

        if not matching_pages:
            print(f"No pages contain all of the search terms: {', '.join(terms)}")
            return []

        # For phrase search, filter to only pages with adjacent positions
        if is_phrase and len(terms) > 1:
            phrase_matches = set()
            for url in matching_pages:
                if self._check_phrase_match(terms, url, term_postings):
                    phrase_matches.add(url)
            matching_pages = phrase_matches

            if not matching_pages:
                print(f"No pages contain the exact phrase: \"{' '.join(terms)}\"")
                # Fall back to showing AND results as a hint
                print("  Tip: Remove quotes to search for pages containing all terms separately.")
                return []

        # Rank by sum of TF-IDF scores across all query terms
        ranked_results: List[Tuple[str, float]] = []
        for url in matching_pages:
            combined_score = sum(
                term_postings[term][url]["tfidf"] for term in terms
            )
            ranked_results.append((url, combined_score))

        ranked_results.sort(key=lambda x: x[1], reverse=True)

        # Display results
        mode = "phrase" if is_phrase else "AND"
        print(f"\nSearch results for '{query}' ({mode} search):")
        print(f"  Found {len(ranked_results)} matching page(s):\n")

        for rank, (url, score) in enumerate(ranked_results, start=1):
            print(f"  {rank}. {url}")
            print(f"     Relevance score: {score:.4f}")

            for term in terms:
                stats = term_postings[term][url]
                print(f"     '{term}': frequency={stats['frequency']}, "
                      f"positions={stats['positions']}")
            print()

        return ranked_results