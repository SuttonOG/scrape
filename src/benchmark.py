"""
benchmark.py - Performance benchmarking for the search engine.

Provides timing and analysis tools to measure the performance of
indexing, searching, and storage operations. Results can be displayed
to demonstrate algorithmic efficiency and validate complexity claims.

Design decisions:
    - Uses time.perf_counter() for high-resolution timing rather than
      time.time(), which has lower precision on some platforms.
    - Each benchmark runs multiple iterations and reports min, max,
      mean, and median to account for variance from OS scheduling,
      cache effects, and garbage collection.
    - Results are printed in a formatted table for easy comparison.
"""

import time
import statistics
from typing import Callable, List, Dict, Any, Optional


class BenchmarkResult:
    """Stores the results of a benchmark run."""

    def __init__(self, name: str, times: List[float]) -> None:
        """
        Initialise a benchmark result.

        Args:
            name: Descriptive name of the benchmark.
            times: List of execution times in seconds.
        """
        self.name = name
        self.times = times
        self.iterations = len(times)
        self.min_time = min(times)
        self.max_time = max(times)
        self.mean_time = statistics.mean(times)
        self.median_time = statistics.median(times)
        self.stdev = statistics.stdev(times) if len(times) > 1 else 0.0

    def __str__(self) -> str:
        """Format the result as a readable string."""
        return (
            f"{self.name}:\n"
            f"  Iterations: {self.iterations}\n"
            f"  Min:    {self._format_time(self.min_time)}\n"
            f"  Max:    {self._format_time(self.max_time)}\n"
            f"  Mean:   {self._format_time(self.mean_time)}\n"
            f"  Median: {self._format_time(self.median_time)}\n"
            f"  StDev:  {self._format_time(self.stdev)}"
        )

    @staticmethod
    def _format_time(seconds: float) -> str:
        """
        Format a time value with appropriate units.

        Args:
            seconds: Time in seconds.

        Returns:
            Formatted string with appropriate unit (s, ms, or μs).
        """
        if seconds >= 1.0:
            return f"{seconds:.4f} s"
        elif seconds >= 0.001:
            return f"{seconds * 1000:.4f} ms"
        else:
            return f"{seconds * 1_000_000:.2f} μs"


def run_benchmark(
    name: str,
    func: Callable,
    iterations: int = 100,
    setup: Optional[Callable] = None,
) -> BenchmarkResult:
    """
    Run a function multiple times and collect timing data.

    Args:
        name: Descriptive name for the benchmark.
        func: The function to benchmark (called with no arguments).
        iterations: Number of times to run the function.
        setup: Optional setup function called once before benchmarking.

    Returns:
        A BenchmarkResult with timing statistics.

    Complexity:
        O(iterations * cost_of_func).
    """
    if setup:
        setup()

    times: List[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append(end - start)

    return BenchmarkResult(name, times)


def benchmark_search_engine(indexer, search_engine) -> List[BenchmarkResult]:
    """
    Run a suite of benchmarks on the search engine components.

    Tests index lookup, single-word search, multi-word search,
    phrase search, and query suggestion performance.

    Args:
        indexer: A built Indexer instance.
        search_engine: A SearchEngine instance using the indexer.

    Returns:
        A list of BenchmarkResult objects.
    """
    results: List[BenchmarkResult] = []

    # Benchmark 1: Single word index lookup
    results.append(run_benchmark(
        "Index lookup (single word)",
        lambda: indexer.get_entry("the"),
        iterations=1000,
    ))

    # Benchmark 2: Vocabulary scan (get_vocabulary_size)
    results.append(run_benchmark(
        "Vocabulary size query",
        lambda: indexer.get_vocabulary_size(),
        iterations=1000,
    ))

    # Benchmark 3: Single word find
    results.append(run_benchmark(
        "Find (single word: 'world')",
        lambda: search_engine.find("world"),
        iterations=100,
    ))

    # Benchmark 4: Multi-word AND search
    results.append(run_benchmark(
        "Find (multi-word AND: 'good friends')",
        lambda: search_engine.find("good friends"),
        iterations=100,
    ))

    # Benchmark 5: Phrase search
    results.append(run_benchmark(
        "Find (phrase: '\"the world\"')",
        lambda: search_engine.find('"the world"'),
        iterations=100,
    ))

    # Benchmark 6: Non-existent word (triggers suggestions)
    results.append(run_benchmark(
        "Find (non-existent: 'zzzzz')",
        lambda: search_engine.find("zzzzz"),
        iterations=100,
    ))

    # Benchmark 7: Index build time (on small corpus)
    small_corpus = {
        f"https://example.com/page/{i}": f"word{i} common shared text page content"
        for i in range(50)
    }
    results.append(run_benchmark(
        "Build index (50 pages)",
        lambda: indexer.build_index(small_corpus),
        iterations=20,
    ))

    return results


def print_benchmark_report(results: List[BenchmarkResult]) -> None:
    """
    Print a formatted benchmark report.

    Args:
        results: List of BenchmarkResult objects to display.
    """
    print("\n" + "=" * 60)
    print("  SEARCH ENGINE BENCHMARK REPORT")
    print("=" * 60)

    for result in results:
        print(f"\n{result}")

    print("\n" + "=" * 60)
    print("  Complexity Summary")
    print("=" * 60)
    print("  Index lookup:       O(1) average (hash table)")
    print("  Single-word find:   O(P) where P = postings list length")
    print("  Multi-word find:    O(T*P + R log R) T=terms, R=results")
    print("  Phrase search:      O(T*P*K) K=positions per term")
    print("  Query suggestions:  O(V*m*n) V=vocab, m,n=word lengths")
    print("  Index build:        O(N + V*D) N=total words, V=vocab, D=docs")
    print("=" * 60 + "\n")