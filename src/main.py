"""
main.py - Command-line interface for the search engine tool.

Provides an interactive shell with build, load, print, and find commands.
Wraps all operations in error handling so the shell never crashes.
"""

import sys
import os

# Add the src directory to the path so modules can import each other
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler import Crawler
from indexer import Indexer
from search import SearchEngine

# Default path for the index file
INDEX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "data", "index.json")


def main() -> None:
    """Run the interactive search engine shell."""
    print("Search Engine Tool")
    print("Type 'help' for available commands or 'quit' to exit.\n")

    crawler = Crawler()
    indexer = Indexer()
    search_engine = SearchEngine(indexer)
    index_loaded = False

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        parts = user_input.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        try:
            if command == "build":
                print("Crawling website and building index...")
                pages = crawler.crawl()
                if not pages:
                    print("Warning: No pages were crawled. Index not built.")
                    continue
                indexer.build_index(pages)
                indexer.save_index(INDEX_PATH)
                index_loaded = True
                print(f"Index built successfully. {len(pages)} pages crawled.")
                print(f"Index saved to {INDEX_PATH}")

            elif command == "load":
                if indexer.load_index(INDEX_PATH):
                    index_loaded = True
                    print("Index loaded successfully.")
                else:
                    print("Error: No index file found. Run 'build' first.")

            elif command == "print":
                if not index_loaded:
                    print("Error: No index loaded. Run 'build' or 'load' first.")
                elif not args:
                    print("Usage: print <word>")
                else:
                    search_engine.print_word(args.strip())

            elif command == "find":
                if not index_loaded:
                    print("Error: No index loaded. Run 'build' or 'load' first.")
                elif not args:
                    print("Usage: find <search terms>")
                else:
                    search_engine.find(args.strip())

            elif command == "help":
                print("Available commands:")
                print("  build           - Crawl the website and build the index")
                print("  load            - Load a previously saved index")
                print("  print <word>    - Show index entry for a word")
                print("  find <terms>    - Find pages containing all search terms")
                print("  quit            - Exit the search tool")

            elif command in ("quit", "exit"):
                print("Goodbye!")
                break

            else:
                print(f"Unknown command: '{command}'. Type 'help' for available commands.")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            print("The search tool is still running. Please try again.")


if __name__ == "__main__":
    main()