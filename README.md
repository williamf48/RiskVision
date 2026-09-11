# RiskVision

RiskVision is an explainable credit-deterioration intelligence prototype for corporate lending portfolios. It combines historical borrower signals, covenant pressure, portfolio concentration, point-in-time replay, and synthetic stress-event backtesting behind a FastAPI/PostgreSQL backend and React/Vite frontend.

> The included portfolio, histories, covenants, and stress-event labels are synthetic development fixtures. Backtest results are engineering validation, not institutional predictive validation.

## Engineering highlights

- Point-in-time historical replay designed to prevent future-data leakage.
- Explainable trajectory analysis: current condition, direction, persistence, 30-day-normalized velocity, acceleration/deceleration, and cross-signal convergence.
- PostgreSQL constraints and regression tests for structural invariants.
- Pydantic API response contracts and mypy-checked analytical interfaces.
- Deterministic clean-database bootstrap and environment verification.
- GitHub Actions CI covering backend tests, typing, database bootstrap, performance guardrails, and frontend production builds.
- Reproducible performance benchmarks with JSON artifacts.

See `docs/ARCHITECTURE.md` for design decisions and `docs/PERFORMANCE.md` for benchmark methodology.

## Repository layout

```text
backend/
  main.py                   FastAPI transport layer
  read_models.py            query-only API projections
  trajectory_engine.py      deterioration analysis
  covenant_engine.py        covenant headroom / pressure
  portfolio_analytics.py    concentration analytics
  backtest_engine.py        historical replay and validation
  migrations/               reproducible schema evolution
  seeds/                    deterministic synthetic fixtures
  tests/                    regression, API, temporal and DB tests
frontend/                    React + Vite dashboard
docs/                       architecture and performance notes
.github/workflows/ci.yml     clean CI pipeline
```

## Prerequisites

- Python 3.13
- Node.js 22
- PostgreSQL 16

Docker is optional; `compose.yaml` provides the development PostgreSQL configuration used below.

## Clean-clone setup

### 1. Clone and select the branch

```bash
git clone https://github.com/williamf48/RiskVision.git
cd RiskVision
git checkout engineering-hardening
```

### 2. Start PostgreSQL

With Docker:

```bash
docker compose up -d postgres
```

This creates a local `risk_platform` database using development-only credentials.

### 3. Configure the backend

Windows PowerShell:

```powershell
Copy-Item backend/.env.example backend/.env
```

macOS/Linux:

```bash
cp backend/.env.example backend/.env
```

Install dependencies and build the deterministic database:

```bash
cd backend
python -m pip install -r requirements.txt
python bootstrap_database.py
python verify_environment.py
```

Expected verification includes 10 tables and the deterministic synthetic fixture counts.

### 4. Run backend checks

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m mypy type_contracts.py api_schemas.py read_models.py trajectory_engine.pyi covenant_engine.pyi portfolio_analytics.pyi backtest_engine.pyi
python performance_benchmark.py --quick --enforce-budgets
```

Start the API:

```bash
uvicorn main:app --reload
```

Swagger UI is available at `http://127.0.0.1:8000/docs`.

### 5. Run the frontend

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

For the production build used by CI:

```bash
npm run build
```

## Continuous integration

Every push to `main` or `engineering-hardening` runs a clean GitHub-hosted environment with PostgreSQL 16. The backend job installs pinned dependencies, compiles Python, bootstraps the database, verifies schema/fixture integrity, runs mypy, executes the test suite, runs performance guardrails, and uploads benchmark JSON. The frontend job performs `npm ci` and a Vite production build.

## Development safety

- Never commit `backend/.env` or database credentials.
- `bootstrap_database.py` refuses to run against a non-empty database.
- Synthetic stress-event labels must remain clearly identified as synthetic.
- Performance budgets are regression alarms, not production latency promises.
