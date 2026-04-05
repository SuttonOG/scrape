"""
main.py - Command-line interface for the search engine tool

Provides an interactive shell with build, load, print, and find commands.
"""

import sys
import os

# Add the src directory to the path so modules can import each other
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler import Crawler
from indexer import Indexer
from search import SearchEngine


def main():
    """Run the interactive search engine shell."""
    print("Search Engine Tool")
    print("Type 'help' for available commands or 'quit' to exit.\n")

    crawler = Crawler()
    indexer = Indexer()
    search_engine = SearchEngine(indexer)

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        # Split the input into command and arguments
        parts = user_input.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "build":
            print("Crawling website and building index...")
            pages = crawler.crawl()
            indexer.build_index(pages)
            indexer.save_index("data/index.json")
            print(f"Index built successfully. {len(pages)} pages crawled.")
            print("Index saved to data/index.json")

        elif command == "load":
            if indexer.load_index("data/index.json"):
                print("Index loaded successfully.")
            else:
                print("Error: No index file found. Run 'build' first.")

        elif command == "print":
            if not args:
                print("Usage: print <word>")
            else:
                search_engine.print_word(args.strip())

        elif command == "find":
            if not args:
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


if __name__ == "__main__":
    main()