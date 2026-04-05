"""Tests for the benchmarking module."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from benchmark import BenchmarkResult, run_benchmark, benchmark_search_engine
from indexer import Indexer
from search import SearchEngine


class TestBenchmarkResult:
    """Tests for the BenchmarkResult class."""

    def test_basic_statistics(self):
        """Computes min, max, mean, and median correctly."""
        result = BenchmarkResult("test", [0.1, 0.2, 0.3, 0.4, 0.5])
        assert result.min_time == 0.1
        assert result.max_time == 0.5
        assert result.mean_time == 0.3
        assert result.median_time == 0.3
        assert result.iterations == 5

    def test_single_iteration(self):
        """Handles a single timing measurement."""
        result = BenchmarkResult("test", [0.05])
        assert result.min_time == 0.05
        assert result.max_time == 0.05
        assert result.stdev == 0.0

    def test_stdev_calculated(self):
        """Standard deviation is computed for multiple iterations."""
        result = BenchmarkResult("test", [0.1, 0.2, 0.3])
        assert result.stdev > 0

    def test_format_seconds(self):
        """Times >= 1s are formatted in seconds."""
        assert "s" in BenchmarkResult._format_time(1.5)

    def test_format_milliseconds(self):
        """Times between 1ms and 1s are formatted in milliseconds."""
        formatted = BenchmarkResult._format_time(0.015)
        assert "ms" in formatted

    def test_format_microseconds(self):
        """Times < 1ms are formatted in microseconds."""
        formatted = BenchmarkResult._format_time(0.000050)
        assert "μs" in formatted

    def test_str_representation(self):
        """String output contains all key fields."""
        result = BenchmarkResult("My Benchmark", [0.1, 0.2])
        output = str(result)
        assert "My Benchmark" in output
        assert "Min:" in output
        assert "Max:" in output
        assert "Mean:" in output
        assert "Median:" in output


class TestRunBenchmark:
    """Tests for the run_benchmark function."""

    def test_runs_correct_iterations(self):
        """Function is called the specified number of times."""
        call_count = {"n": 0}

        def counter():
            call_count["n"] += 1

        result = run_benchmark("counter", counter, iterations=10)
        assert call_count["n"] == 10
        assert result.iterations == 10

    def test_returns_benchmark_result(self):
        """Returns a BenchmarkResult object."""
        result = run_benchmark("noop", lambda: None, iterations=5)
        assert isinstance(result, BenchmarkResult)

    def test_times_are_positive(self):
        """All measured times are non-negative."""
        result = run_benchmark("noop", lambda: None, iterations=10)
        for t in result.times:
            assert t >= 0

    def test_setup_called_once(self):
        """Setup function is called exactly once before benchmarking."""
        setup_count = {"n": 0}

        def setup():
            setup_count["n"] += 1

        run_benchmark("test", lambda: None, iterations=5, setup=setup)
        assert setup_count["n"] == 1


class TestBenchmarkSearchEngine:
    """Tests for the full benchmark suite."""

    def test_returns_results_list(self):
        """benchmark_search_engine returns a list of BenchmarkResult objects."""
        indexer = Indexer()
        indexer.build_index({
            "https://example.com/1": "the world is a fine place",
            "https://example.com/2": "good friends and good books",
        })
        search_engine = SearchEngine(indexer)

        results = benchmark_search_engine(indexer, search_engine)

        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, BenchmarkResult) for r in results)

    def test_all_benchmarks_have_times(self):
        """Every benchmark result has at least one timing measurement."""
        indexer = Indexer()
        indexer.build_index({
            "https://example.com/1": "the world is a fine place",
            "https://example.com/2": "good friends and good books",
        })
        search_engine = SearchEngine(indexer)

        results = benchmark_search_engine(indexer, search_engine)

        for result in results:
            assert len(result.times) > 0
            assert result.min_time >= 0