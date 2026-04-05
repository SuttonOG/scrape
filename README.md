# Search Engine Tool

A command-line search engine that crawls [quotes.toscrape.com](https://quotes.toscrape.com/), builds an inverted index with TF-IDF scoring, and supports ranked single-word, multi-word, and phrase searches with query suggestions.

Built as part of COMP3011 Web Services and Web Data coursework at the University of Leeds.

## Architecture Overview
```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│   Crawler    │────▶│   Indexer   │────▶│  SearchEngine   │
│              │     │             │     │                 │
│ - BFS crawl  │     │ - Tokenise  │     │ - print (lookup)│
│ - Politeness │     │ - Inverted  │     │ - find (AND)    │
│ - Retry/     │     │   index     │     │ - Phrase search │
│   backoff    │     │ - TF-IDF    │     │ - TF-IDF rank   │
│ - Link       │     │ - Save/Load │     │ - Suggestions   │
│   discovery  │     │   (JSON)    │     │                 │
└─────────────┘     └─────────────┘     └─────────────────┘
        │                                        │
        │           ┌─────────────────┐          │
        │           │ text_processor  │          │
        └──────────▶│                 │◀─────────┘
                    │ - tokenise()    │
                    │ - normalise()   │
                    └─────────────────┘
```

## Features

- **Web Crawler**: Breadth-first crawl with 6-second politeness delay, retry with exponential backoff, and URL deduplication.
- **Inverted Index**: Stores word frequency, positions, TF (term frequency), and TF-IDF scores per word per page.
- **Search**: Single-word, multi-word AND queries, and exact phrase search (using stored word positions), all ranked by TF-IDF relevance.
- **Query Suggestions**: Levenshtein distance-based "did you mean?" suggestions for misspelled terms.
- **Persistence**: Save and load the full index (including TF-IDF scores) as JSON.
- **Benchmarking**: Built-in performance benchmarks with statistical analysis.

## Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd search-engine

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage
```bash
python src/main.py
```

### Commands

| Command | Description | Example |
|---|---|---|
| `build` | Crawl the website and build the inverted index | `> build` |
| `load` | Load a previously saved index from disk | `> load` |
| `print <word>` | Display the full index entry for a word | `> print nonsense` |
| `find <terms>` | Find pages containing all search terms (AND) | `> find good friends` |
| `find "<phrase>"` | Find pages with an exact adjacent phrase | `> find "the world"` |
| `benchmark` | Run performance benchmarks on the index | `> benchmark` |
| `help` | Show available commands | `> help` |
| `quit` | Exit the search tool | `> quit` |

### Example Session
```
Search Engine Tool
Type 'help' for available commands or 'quit' to exit.

> build
  Crawling: https://quotes.toscrape.com/
  Waiting 6s (politeness delay)...
  Crawling: https://quotes.toscrape.com/page/2/
  ...
  Crawl complete. 60 pages collected.
  Index built: 1847 unique words across 60 pages.
  Index saved to data/index.json

> print world
  Index entry for 'world':
    Appears in 5 page(s):

    URL:       https://quotes.toscrape.com/
    Frequency: 2
    Positions: [4, 18]
    TF:        0.012346
    TF-IDF:    0.029851

> find good friends
  Search results for 'good friends' (AND search):
    Found 2 matching page(s):

    1. https://quotes.toscrape.com/page/2/
       Relevance score: 0.0842
       'good': frequency=3, positions=[5, 12, 30]
       'friends': frequency=1, positions=[6]

> find "the world"
  Search results for '"the world"' (phrase search):
    Found 3 matching page(s):
    ...

> quit
Goodbye!
```

## Data Structures

### Inverted Index

The core data structure is an inverted index mapping each word to its occurrences across all crawled pages:
```json
{
  "metadata": {
    "page_count": 60,
    "vocabulary_size": 1847,
    "page_word_counts": { "url": 150 }
  },
  "index": {
    "world": {
      "https://quotes.toscrape.com/": {
        "frequency": 2,
        "positions": [4, 18],
        "tf": 0.012346,
        "tfidf": 0.029851
      }
    }
  }
}
```

### Why TF-IDF?

TF-IDF (Term Frequency–Inverse Document Frequency) balances two signals:
- **TF**: How often a word appears in a specific page (higher = more relevant to that page).
- **IDF**: How rare the word is across all pages (higher = more discriminating).

Words like "the" appear everywhere (high TF, low IDF → low TF-IDF), while distinctive words like "conscience" appear rarely (moderate TF, high IDF → high TF-IDF). This produces more meaningful search rankings than raw frequency alone.

### Phrase Search

Phrase search uses the stored word positions to verify adjacency. For a query `"good friends"`, we find all pages containing both words, then check that there exists a position `p` where `"good"` is at position `p` and `"friends"` is at position `p+1`. This is O(P) where P is the number of positions of the first term.

## Algorithm Complexity

| Operation | Time Complexity | Notes |
|---|---|---|
| Index lookup | O(1) average | Hash table (Python dict) |
| Build index | O(N + V×D) | N=total words, V=vocab, D=docs |
| Single-word find | O(P) | P=postings list length |
| Multi-word find | O(T×P + R log R) | T=terms, R=results |
| Phrase search | O(T×P×K) | K=positions per term |
| Query suggestions | O(V×m×n) | V=vocab, m,n=word lengths |
| Save/load index | O(S) | S=serialised index size |

## Testing
```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=src --cov-report=term-missing

# Run a specific test file
pytest tests/test_crawler.py -v

# Run a specific test class
pytest tests/test_search.py::TestPhraseSearch -v
```

### Test Coverage Summary

| Module | Coverage |
|---|---|
| `crawler.py` | 95%+ |
| `indexer.py` | 95%+ |
| `search.py` | 95%+ |
| `text_processor.py` | 100% |
| `query_suggester.py` | 100% |
| `benchmark.py` | 90%+ |

## Project Structure
```
search-engine/
├── src/
│   ├── crawler.py          # BFS web crawler with politeness and retry
│   ├── indexer.py           # Inverted index with TF-IDF scoring
│   ├── search.py            # Query processing, phrase search, ranking
│   ├── text_processor.py    # Tokenisation and normalisation
│   ├── query_suggester.py   # Levenshtein distance suggestions
│   ├── benchmark.py         # Performance benchmarking suite
│   └── main.py              # CLI shell interface
├── tests/
│   ├── test_crawler.py      # Crawler unit tests (mocked HTTP)
│   ├── test_indexer.py       # Indexer and TF-IDF tests
│   ├── test_search.py        # Search, phrase, and suggestion tests
│   ├── test_text_processor.py # Tokenisation tests
│   ├── test_query_suggester.py # Levenshtein and suggestion tests
│   └── test_benchmark.py     # Benchmark module tests
├── data/
│   └── index.json            # Compiled inverted index (generated)
├── requirements.txt
├── pytest.ini
└── README.md
```

## Dependencies

- **requests** — HTTP library for fetching web pages
- **beautifulsoup4** — HTML parsing and content extraction
- **pytest** — Testing framework
- **pytest-cov** — Test coverage reporting

## References

- Manning, Raghavan & Schütze (2008). *Introduction to Information Retrieval*. Cambridge University Press. — TF-IDF theory and inverted index design.
- Levenshtein, V. I. (1966). "Binary codes capable of correcting deletions, insertions, and reversals." — Edit distance algorithm.
- Python `requests` library: https://docs.python-requests.org/
- BeautifulSoup documentation: https://www.crummy.com/software/BeautifulSoup/bs4/doc/