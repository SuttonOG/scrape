"""
text_processor.py - Text tokenisation and normalisation utilities.

Provides functions for cleaning, tokenising, and normalising raw text
extracted from web pages, preparing it for indexing.

Design decisions:
    - Lowercase normalisation: the assignment specifies case-insensitive search.
    - Punctuation stripping: we use regex word-boundary matching to extract
      only alphabetic tokens, discarding numbers and symbols.
    - Stopword filtering is intentionally NOT applied. While it would reduce
      index size, it would prevent users from searching for common words
      and phrases like "to be or not to be". This is a deliberate trade-off
      favouring recall over index compactness.
"""

import re
from typing import List


def tokenise(text: str) -> List[str]:
    """
    Convert raw text into a list of normalised word tokens.

    Applies lowercase normalisation and extracts only alphabetic tokens,
    preserving word order and duplicates for position tracking.

    Args:
        text: Raw text string extracted from a web page.

    Returns:
        A list of lowercase alphabetic tokens in their original order.

    Complexity:
        O(n) where n is the length of the input text.

    Examples:
        >>> tokenise("Good friends, good books!")
        ['good', 'friends', 'good', 'books']
        >>> tokenise("")
        []
        >>> tokenise("123 @#$ !!!")
        []
    """
    return re.findall(r"[a-z]+", text.lower())


def normalise_word(word: str) -> str:
    """
    Normalise a single word for index lookup.

    Strips whitespace and converts to lowercase to ensure
    case-insensitive matching as required by the specification.

    Args:
        word: A raw word string (e.g., from user query input).

    Returns:
        The lowercase, stripped version of the word.

    Complexity:
        O(k) where k is the length of the word.

    Examples:
        >>> normalise_word("Good")
        'good'
        >>> normalise_word("  HELLO  ")
        'hello'
    """
    return word.strip().lower()