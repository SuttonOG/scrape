"""
query_suggester.py - Query suggestion engine using edit distance.

Provides "did you mean?" suggestions when a search term is not found
in the index, by finding the closest matching indexed words using
Levenshtein distance.

Design decisions:
    - Levenshtein distance is computed using dynamic programming in
      O(m*n) time where m and n are the lengths of the two strings.
    - Suggestions are limited to words within a maximum edit distance
      of 2, which catches most common typos (character swaps, missing
      or extra characters) without returning irrelevant results.
    - Only the top 3 suggestions are returned to avoid overwhelming
      the user.

Alternative approaches considered:
    - BK-trees would allow O(log V) lookup for similar words but add
      implementation complexity. For the vocabulary size of this corpus
      (~2000 words), linear scan is fast enough.
    - Soundex/phonetic matching would handle homophones but is
      English-specific and less general than edit distance.
"""

from typing import List, Tuple, Dict


def levenshtein_distance(word_a: str, word_b: str) -> int:
    """
    Compute the Levenshtein (edit) distance between two strings.

    The edit distance is the minimum number of single-character insertions,
    deletions, or substitutions required to transform one string into another.

    Args:
        word_a: First string.
        word_b: Second string.

    Returns:
        The integer edit distance between the two strings.

    Complexity:
        Time:  O(m * n) where m = len(word_a), n = len(word_b).
        Space: O(min(m, n)) using two-row optimisation.

    Examples:
        >>> levenshtein_distance("kitten", "sitting")
        3
        >>> levenshtein_distance("hello", "hello")
        0
        >>> levenshtein_distance("", "abc")
        3
    """
    # Ensure word_a is the shorter string for space optimisation
    if len(word_a) > len(word_b):
        word_a, word_b = word_b, word_a

    m, n = len(word_a), len(word_b)

    # Two-row DP approach: O(min(m, n)) space instead of O(m * n)
    previous_row = list(range(m + 1))
    current_row = [0] * (m + 1)

    for j in range(1, n + 1):
        current_row[0] = j
        for i in range(1, m + 1):
            cost = 0 if word_a[i - 1] == word_b[j - 1] else 1
            current_row[i] = min(
                current_row[i - 1] + 1,       # insertion
                previous_row[i] + 1,           # deletion
                previous_row[i - 1] + cost,    # substitution
            )
        previous_row, current_row = current_row, previous_row

    return previous_row[m]


def suggest_words(
    query_term: str,
    vocabulary: Dict,
    max_distance: int = 2,
    max_suggestions: int = 3,
) -> List[Tuple[str, int]]:
    """
    Find the closest words in the index vocabulary to a given query term.

    Scans the full vocabulary and returns words within the maximum
    edit distance, sorted by distance (closest first), then alphabetically.

    Args:
        query_term: The misspelled or unrecognised search term.
        vocabulary: The index dictionary (keys are the vocabulary words).
        max_distance: Maximum edit distance to consider (default 2).
        max_suggestions: Maximum number of suggestions to return (default 3).

    Returns:
        A list of (word, distance) tuples sorted by distance then alphabetically.

    Complexity:
        O(V * m * n) where V is vocabulary size, m is the length of the
        query term, and n is the average word length in the vocabulary.
    """
    candidates: List[Tuple[str, int]] = []

    for word in vocabulary:
        # Early termination: if lengths differ by more than max_distance,
        # the edit distance must be at least that much
        if abs(len(word) - len(query_term)) > max_distance:
            continue

        distance = levenshtein_distance(query_term, word)
        if distance <= max_distance:
            candidates.append((word, distance))

    # Sort by distance first, then alphabetically for consistent output
    candidates.sort(key=lambda x: (x[1], x[0]))

    return candidates[:max_suggestions]