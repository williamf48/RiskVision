# RiskVision Performance Benchmarking

RiskVision includes a reproducible backend benchmark harness in `backend/performance_benchmark.py`.

The goal is not to claim production latency from a synthetic development portfolio. The benchmark provides a repeatable way to detect large regressions, compare code changes, and identify expensive call paths before the project is submitted or deployed.

## Workloads

The harness measures both CPU-only trajectory logic and database-backed end-to-end operations:

| Workload | What it measures |
| --- | --- |
| `trajectory_256` | Trajectory analysis over 256 synthetic observations |
| `trajectory_4096` | Scaling of the trajectory algorithm over 4,096 observations |
| `borrower_analysis_65` | Current deterioration analysis for Falcon Realty |
| `portfolio_analysis_25` | Current intervention analysis across the 25-borrower synthetic portfolio |
| `borrower_replay_65` | Point-in-time historical replay for Falcon Realty |
| `portfolio_backtest` | Historical replay/backtest across historically assessable borrowers |
| `portfolio_concentration` | Portfolio exposure and sector concentration analytics |

Each workload records minimum, mean, median, p95 and maximum latency plus median-derived operations per second.

## Run locally

From `backend/`:

```powershell
python performance_benchmark.py
```

For a shorter CI-equivalent run:

```powershell
python performance_benchmark.py --quick --enforce-budgets --json benchmark_results.json
```

To inspect hot call paths in the historical replay/backtest:

```powershell
python performance_benchmark.py --profile
```

The profiler uses Python's built-in `cProfile` and reports the 25 highest cumulative-time call paths.

## CI regression budgets

CI runs the quick benchmark after the complete backend test suite and stores `benchmark_results.json` as a workflow artifact.

The thresholds in `PERFORMANCE_BUDGET_MS` are intentionally loose. They are regression guardrails, not service-level objectives, because GitHub-hosted runners have variable CPU and I/O performance.

A budget failure means a workload's p95 latency exceeded its guardrail and the change should be investigated. The benchmark artifact preserves the measurements from each CI run for comparison.

## Interpreting results

Use median latency for normal comparisons and p95 for regression detection. Database-backed timings include PostgreSQL access, pandas conversion and application logic, so they are useful as end-to-end engineering measurements but should not be presented as production latency claims.

The synthetic portfolio is intentionally small. If RiskVision is expanded to materially larger datasets, add benchmark datasets at realistic portfolio sizes before tightening budgets.
