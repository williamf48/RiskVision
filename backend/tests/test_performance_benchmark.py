import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


from performance_benchmark import (
    BenchmarkResult,
    build_trajectory_input,
    enforce_budgets,
    measure,
    percentile,
)


class PerformanceBenchmarkTests(unittest.TestCase):

    def test_percentile_interpolates_ordered_sample(self):
        self.assertAlmostEqual(
            percentile([1.0, 2.0, 3.0, 4.0], 50.0),
            2.5,
        )

    def test_measure_runs_warmups_and_iterations(self):
        calls = 0

        def operation():
            nonlocal calls
            calls += 1
            return calls

        result = measure(
            "unit_test",
            operation,
            iterations=4,
            warmups=2,
        )

        self.assertEqual(calls, 6)
        self.assertEqual(result.iterations, 4)
        self.assertGreaterEqual(result.max_ms, result.min_ms)
        self.assertGreaterEqual(result.p95_ms, result.min_ms)

    def test_budget_failure_is_reported(self):
        result = BenchmarkResult(
            name="trajectory_256",
            iterations=1,
            min_ms=100.0,
            mean_ms=100.0,
            median_ms=100.0,
            p95_ms=100.0,
            max_ms=100.0,
            operations_per_second=10.0,
        )

        failures = enforce_budgets([result])
        self.assertEqual(len(failures), 1)
        self.assertIn("trajectory_256", failures[0])

    def test_synthetic_trajectory_input_is_monotonic(self):
        values, dates = build_trajectory_input(32)

        self.assertEqual(len(values), 32)
        self.assertEqual(len(dates), 32)
        self.assertTrue(all(a < b for a, b in zip(values, values[1:])))
        self.assertTrue(all(a < b for a, b in zip(dates, dates[1:])))


if __name__ == "__main__":
    unittest.main(verbosity=2)
