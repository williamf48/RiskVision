# RiskVision Architecture and Engineering Decisions

## Purpose

RiskVision is a full-stack credit deterioration intelligence prototype. The engineering goal is not to automate lending decisions; it is to reconstruct borrower state from historical observations, explain deterioration signals, rank analyst intervention priority, and validate that behavior with point-in-time replay.

The repository deliberately separates domain analysis, data access, API contracts, persistence, validation, and presentation so each layer can be tested independently.

## System map

```text
React / Vite frontend
        |
        v
FastAPI transport layer (main.py)
        |
        +----------------------+----------------------+---------------------+
        |                      |                      |                     |
        v                      v                      v                     v
read_models.py        trajectory_engine.py   covenant_engine.py   portfolio_analytics.py
        |                      |                      |                     |
        +----------------------+----------------------+---------------------+
                               |
                               v
                        PostgreSQL / SQLAlchemy
                               |
                +--------------+---------------+
                |                              |
                v                              v
       historical observations       facilities / covenants
                |
                v
          backtest_engine.py
                |
                v
      replay + lead-time validation
```

## Layer responsibilities

### API transport

`main.py` owns HTTP routing, HTTP status semantics, CORS, and response contracts. It should not contain deterioration algorithms.

### Read models

`read_models.py` centralizes query-only projections used by API surfaces. This keeps SQL retrieval concerns separate from domain calculations and gives query behavior its own testable boundary.

### Deterioration engine

`trajectory_engine.py` calculates current condition, direction, persistence, time-normalized velocity, acceleration/deceleration, cross-signal convergence, recommended investigations, and intervention priority.

The engine distinguishes **current condition** from **trajectory deterioration**. A borrower can therefore have a weak current metric without a worsening trajectory, or a currently acceptable metric with a rapidly deteriorating trajectory.

### Covenant engine

`covenant_engine.py` evaluates covenant headroom and pressure independently from trajectory scoring. This avoids conflating contractual threshold status with behavioral deterioration.

### Portfolio analytics

`portfolio_analytics.py` aggregates exposure, concentration, historical coverage, actionability, and covenant pressure. Portfolio-level outputs are derived from borrower-level results rather than maintained as a second source of truth.

### Historical replay and backtesting

`backtest_engine.py` reconstructs borrower state at historical observation dates. The replay path passes `as_of_date` into the deterioration engine so observations after the replay date are excluded.

Synthetic stress-event labels are used only for development validation. They must not be represented as institutional predictive validation.

## Key design decisions

### 1. Point-in-time correctness over convenience

Historical replay filters observations by `observation_date <= as_of_date`. Tests assert that replay never has more history than the current state. This prevents future-data leakage.

### 2. Explainable heuristics before opaque scoring

Intervention priority is derived from explicit signals such as deterioration count, persistence, acceleration, condition severity, and convergence. The current implementation is transparent and auditable; it is not a probability of default model.

### 3. Database invariants are structural, not speculative policy

PostgreSQL constraints enforce facts such as non-negative exposure/DPD, allowed classifications, required identifiers, valid alert severities, unique borrower identity, and foreign-key integrity. The database deliberately does not impose questionable financial assumptions such as forcing DSCR to be non-negative.

### 4. Typed boundaries without rewriting stable algorithms

`TypedDict`/`Literal` contracts and `.pyi` interfaces provide static contracts around established analytical modules. Pydantic models enforce important API responses at runtime. Mypy runs in CI.

### 5. Reproducibility is part of correctness

A clean database can be built from migrations and deterministic synthetic fixtures with `bootstrap_database.py`. `verify_environment.py` checks both schema presence and fixture counts. CI performs this bootstrap from scratch before running tests.

### 6. Performance checks are guardrails, not SLAs

`performance_benchmark.py` measures core analytical workloads and stores machine-readable results. CI budgets are intentionally loose regression detectors because GitHub-hosted runners are noisy and the synthetic portfolio is small.

## Correctness strategy

The test suite covers four levels:

1. Pure trajectory edge cases: zero history, equal values, date anomalies, zero denominators, persistence and acceleration.
2. Temporal invariants: point-in-time cutoff behavior, replay ordering, valid priorities and portfolio consistency.
3. Database invariants: invalid writes must be rejected by PostgreSQL.
4. API contracts: successful paths, 404 behavior, Pydantic response binding and portfolio endpoints.

CI also performs Python compilation, static typing, clean PostgreSQL bootstrap, environment verification, performance benchmarking, and the frontend production build.

## Known limitations

- Synthetic borrower histories and stress-event labels are development fixtures, not real-world validation data.
- Current scale is intentionally small (25 borrowers, five historically assessable borrowers).
- The FastAPI module still contains some legacy SQL-backed endpoints; new query-only projections should move through `read_models.py` rather than adding more SQL to the transport layer.
- Authentication, tenant isolation, enterprise RBAC, production observability, secrets management, and production deployment automation are outside the current resume prototype scope.

## Extension rules

When adding a new feature:

1. Put analytical logic in a domain module, not an endpoint.
2. Put query-only projections in `read_models.py` or a dedicated repository module.
3. Define an explicit typed/Pydantic boundary when the result crosses the API.
4. Add failure-mode and temporal tests before changing intervention logic.
5. Add a migration for structural database changes; never mutate the development database manually as the only source of truth.
6. If the change affects hot analytical paths, add or update a benchmark.
