from __future__ import annotations

import argparse
import cProfile
import io
import json
import platform
import pstats
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, median
from time import perf_counter_ns
from typing import Callable

from backtest_engine import backtest_portfolio, replay_borrower
from portfolio_analytics import analyze_portfolio_concentration
from trajectory_engine import analyze_borrower, analyze_portfolio, analyze_trajectory


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    iterations: int
    min_ms: float
    mean_ms: float
    median_ms: float
    p95_ms: float
    max_ms: float
    operations_per_second: float


# These are intentionally loose regression guardrails rather than production SLAs.
# They are designed to catch catastrophic performance regressions on shared CI runners.
PERFORMANCE_BUDGET_MS = {
    "trajectory_256": 50.0,
    "trajectory_4096": 250.0,
    "borrower_analysis_65": 1500.0,
    "portfolio_analysis_25": 12000.0,
    "borrower_replay_65": 15000.0,
    "portfolio_backtest": 30000.0,
    "portfolio_concentration": 3000.0,
}


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        raise ValueError("Cannot calculate a percentile from an empty sample.")

    if not 0 <= percentile_value <= 100:
        raise ValueError("percentile_value must be between 0 and 100.")

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * (percentile_value / 100.0)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = position - lower_index

    return (
        ordered[lower_index]
        + (ordered[upper_index] - ordered[lower_index]) * fraction
    )


def measure(
    name: str,
    operation: Callable[[], object],
    *,
    iterations: int,
    warmups: int = 1,
) -> BenchmarkResult:
    if iterations <= 0:
        raise ValueError("iterations must be greater than zero.")

    if warmups < 0:
        raise ValueError("warmups cannot be negative.")

    for _ in range(warmups):
        operation()

    durations_ms: list[float] = []

    for _ in range(iterations):
        start = perf_counter_ns()
        operation()
        elapsed_ns = perf_counter_ns() - start
        durations_ms.append(elapsed_ns / 1_000_000.0)

    median_ms = median(durations_ms)

    return BenchmarkResult(
        name=name,
        iterations=iterations,
        min_ms=round(min(durations_ms), 3),
        mean_ms=round(mean(durations_ms), 3),
        median_ms=round(median_ms, 3),
        p95_ms=round(percentile(durations_ms, 95.0), 3),
        max_ms=round(max(durations_ms), 3),
        operations_per_second=(
            round(1000.0 / median_ms, 3)
            if median_ms > 0
            else float("inf")
        ),
    )


def build_trajectory_input(size: int) -> tuple[list[float], list[date]]:
    if size <= 0:
        raise ValueError("size must be greater than zero.")

    start = date(2020, 1, 1)
    values = [100.0 + index * 0.1 for index in range(size)]
    dates = [start + timedelta(days=30 * index) for index in range(size)]
    return values, dates


def build_workloads(quick: bool) -> list[tuple[str, Callable[[], object], int]]:
    values_256, dates_256 = build_trajectory_input(256)
    values_4096, dates_4096 = build_trajectory_input(4096)

    if quick:
        pure_iterations = 20
        db_iterations = 3
        expensive_iterations = 2
    else:
        pure_iterations = 100
        db_iterations = 7
        expensive_iterations = 3

    return [
        (
            "trajectory_256",
            lambda: analyze_trajectory(values_256, dates_256, "UP"),
            pure_iterations,
        ),
        (
            "trajectory_4096",
            lambda: analyze_trajectory(values_4096, dates_4096, "UP"),
            pure_iterations,
        ),
        (
            "borrower_analysis_65",
            lambda: analyze_borrower(65),
            db_iterations,
        ),
        (
            "portfolio_analysis_25",
            analyze_portfolio,
            expensive_iterations,
        ),
        (
            "borrower_replay_65",
            lambda: replay_borrower(65),
            expensive_iterations,
        ),
        (
            "portfolio_backtest",
            backtest_portfolio,
            expensive_iterations,
        ),
        (
            "portfolio_concentration",
            analyze_portfolio_concentration,
            db_iterations,
        ),
    ]


def enforce_budgets(results: list[BenchmarkResult]) -> list[str]:
    failures: list[str] = []

    for result in results:
        budget_ms = PERFORMANCE_BUDGET_MS.get(result.name)

        if budget_ms is None:
            continue

        if result.p95_ms > budget_ms:
            failures.append(
                f"{result.name}: p95 {result.p95_ms:.3f} ms exceeds "
                f"budget {budget_ms:.3f} ms"
            )

    return failures


def render_results(results: list[BenchmarkResult]) -> None:
    print()
    print("RiskVision backend benchmark")
    print("=" * 104)
    print(
        f"{'workload':30} {'iters':>7} {'min ms':>10} {'mean ms':>10} "
        f"{'median ms':>11} {'p95 ms':>10} {'max ms':>10} {'ops/s':>10}"
    )
    print("-" * 104)

    for result in results:
        print(
            f"{result.name:30} "
            f"{result.iterations:7d} "
            f"{result.min_ms:10.3f} "
            f"{result.mean_ms:10.3f} "
            f"{result.median_ms:11.3f} "
            f"{result.p95_ms:10.3f} "
            f"{result.max_ms:10.3f} "
            f"{result.operations_per_second:10.3f}"
        )


def write_json(
    path: Path,
    results: list[BenchmarkResult],
    budget_failures: list[str],
    quick: bool,
) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "quick_mode": quick,
        "budgets_ms": PERFORMANCE_BUDGET_MS,
        "budget_failures": budget_failures,
        "results": [asdict(result) for result in results],
    }

    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(f"\nBenchmark JSON written to {path}")


def print_profile() -> None:
    profiler = cProfile.Profile()
    profiler.enable()
    backtest_portfolio()
    profiler.disable()

    output = io.StringIO()
    stats = pstats.Stats(profiler, stream=output).sort_stats("cumulative")
    stats.print_stats(25)

    print()
    print("cProfile: backtest_portfolio (top 25 by cumulative time)")
    print("=" * 104)
    print(output.getvalue())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark RiskVision trajectory analysis, borrower/portfolio analysis, "
            "historical replay, backtesting and concentration analytics."
        )
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Use fewer repetitions for CI smoke benchmarking.",
    )
    parser.add_argument(
        "--enforce-budgets",
        action="store_true",
        help="Fail if a p95 timing exceeds the loose CI regression budget.",
    )
    parser.add_argument(
        "--json",
        type=Path,
        dest="json_path",
        help="Write machine-readable benchmark results to this path.",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Also cProfile the portfolio backtest and print the hottest call paths.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = [
        measure(
            name,
            operation,
            iterations=iterations,
            warmups=1,
        )
        for name, operation, iterations in build_workloads(args.quick)
    ]

    render_results(results)
    budget_failures = enforce_budgets(results)

    if args.json_path is not None:
        write_json(args.json_path, results, budget_failures, args.quick)

    if args.profile:
        print_profile()

    if args.enforce_budgets and budget_failures:
        print("\nPerformance budget failures:")
        for failure in budget_failures:
            print(f"- {failure}")
        return 1

    if args.enforce_budgets:
        print("\nAll performance regression budgets passed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
