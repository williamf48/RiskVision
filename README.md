# RiskVision

**Explainable credit deterioration monitoring, covenant analysis and portfolio intervention prioritization.**

RiskVision is a full-stack development prototype for reviewing corporate credit portfolios. It combines financial snapshots with historical metric observations to highlight worsening borrower conditions, explain the signals driving intervention priority and support analyst investigation.

Built by [William Fernandes](https://github.com/williamf48).

## Features

- **Historical deterioration analysis:** current condition, direction, persistence, time-normalized velocity and changes in velocity.
- **Cross-signal convergence:** identifies when multiple financial indicators deteriorate together.
- **Intervention prioritization:** URGENT, HIGH, MEDIUM, LOW and INSUFFICIENT_DATA, with reason codes and recommended investigations.
- **Facility-level covenants:** evaluates minimum and maximum thresholds, headroom and breach pressure.
- **Portfolio intelligence:** exposure, sector concentration, HHI concentration analytics and historical coverage.
- **Historical replay and backtesting:** reconstructs borrower trajectories at observation-date cutoffs and compares alerts with seeded stress events.
- **Analyst interface:** dashboard, portfolio workspace, borrower profiles, interventions, alerts, reports and validation views.
- **Regression checks:** 10 database-dependent tests covering expected development scenarios.

## Technology stack

| Layer | Technologies |
| --- | --- |
| Frontend | React, Vite, React Router, Recharts |
| API | Python, FastAPI |
| Data access | Pandas, SQLAlchemy |
| Database | PostgreSQL |
| Configuration | python-dotenv |
| Verification | Python unittest |

The main data flow is **PostgreSQL → analytical modules → FastAPI JSON endpoints → React workspaces**. Excel processing is handled separately by the legacy import script.

## Analytical approach

The current deterioration engine is transparent, deterministic analytical logic. It does not require a trained ML model.

| Metric | Deterioration direction |
| --- | --- |
| Debt service coverage ratio (DSCR) | Decreasing |
| Bounce rate | Increasing |
| Receivable days | Increasing |
| Debt / EBITDA | Increasing |

Each metric is evaluated against development thresholds and its own history. Changes are normalized to a 30-day interval to make different observation intervals more interpretable. Borrower priority combines condition severity, persistent deterioration, acceleration and signal convergence.

For example, the synthetic Falcon Realty scenario contains:

| Metric | Synthetic sequence |
| --- | --- |
| DSCR | 1.45 → 1.31 → 1.12 → 0.90 |
| Bounce rate | 2.0 → 3.2 → 5.4 → 8.1 |
| Receivable days | 52 → 61 → 75 → 94 |
| Debt / EBITDA | 2.2 → 2.5 → 2.9 → 3.4 |

These are development fixtures, not evidence of real borrower performance. Missing history is explicitly reported as insufficient data.

## Repository guide

| Path | Purpose |
| --- | --- |
| `backend/main.py` | FastAPI routes |
| `backend/connection.py` | Environment-based PostgreSQL connection |
| `backend/trajectory_engine.py` | Historical deterioration and intervention logic |
| `backend/covenant_engine.py` | Covenant headroom and pressure analysis |
| `backend/portfolio_analytics.py` | Exposure and concentration analytics |
| `backend/backtest_engine.py` | Observation-date replay and stress-event comparison |
| `backend/risk_engine_excel.py` | Legacy Excel import and static scoring |
| `backend/migrations/` | Additional observation, covenant and stress-event tables |
| `backend/seeds/` | Synthetic development histories and scenarios |
| `backend/tests/` | Database-dependent regression suite |
| `frontend/` | React application |
| `data/` | Excel workbooks |
| `docs/CURRENT_STATE.md` | Development history and implementation notes |

## Local setup

### Prerequisites

- Python with a virtual environment.
- PostgreSQL.
- Node.js and npm compatible with the Vite version in `frontend/package.json`.
- An existing, populated RiskVision database or an equivalent development fixture.

**Database bootstrap is currently incomplete in this repository.** The committed migrations add tables to an existing schema; they do not create every core table from scratch. Core tables referenced by the application include `borrowers`, `borrower_financials`, `risk_scores`, `risk_history` and `alerts`. The regression suite also expects specific seeded borrower IDs and portfolio contents.

### 1. Clone and install backend dependencies

```bash
git clone https://github.com/williamf48/RiskVision.git
cd RiskVision
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

The backend does not yet include a pinned dependency manifest. Install the packages required by the inspected API and Excel-processing code:

```bash
python -m pip install fastapi uvicorn pandas sqlalchemy psycopg2-binary python-dotenv openpyxl
```

### 2. Configure PostgreSQL

Copy `backend/.env.example` to `backend/.env`, then fill in your local settings:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=risk_platform
DB_USER=postgres
DB_PASSWORD=your_local_database_password
```

Keep `.env` out of version control. Apply the additional migrations and seeds only after the required base schema and borrower fixtures exist. Use a dedicated development database.

The legacy Excel importer has its own hardcoded database configuration and Windows workbook path. It does not currently use the shared environment-based connection. Update those settings before using it; exposed credentials should be removed and rotated wherever they remain valid.

### 3. Start the API

From the repository root, with the virtual environment active:

```bash
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

API: http://127.0.0.1:8000  
Interactive documentation: http://127.0.0.1:8000/docs

### 4. Start the frontend

In a second terminal, from the repository root:

```bash
cd frontend
npm ci
npm run dev
```

Open the URL printed by Vite. Frontend components currently reference `http://127.0.0.1:8000` directly, so use that API address for local development.

## Selected API endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /borrowers` | Borrower directory |
| `GET /borrowers/{borrower_id}` | Borrower financials, assessment and alerts |
| `GET /borrowers/{borrower_id}/deterioration` | Signal-level deterioration analysis |
| `GET /borrowers/{borrower_id}/history` | Historical observations |
| `GET /borrowers/{borrower_id}/covenants` | Covenant analysis |
| `GET /borrowers/{borrower_id}/replay` | Historical replay |
| `GET /borrowers/{borrower_id}/backtest` | Borrower backtest |
| `GET /intervention_watchlist` | Prioritized intervention list |
| `GET /intervention_summary` | Intervention counts |
| `GET /portfolio_analytics` | Portfolio exposure and concentration |
| `GET /backtest_summary` | Portfolio validation summary |

Use the interactive API documentation for query parameters and response schemas.

## Verification

With the expected PostgreSQL fixture and environment configured, run from the repository root:

```bash
python -m unittest discover -s backend/tests -p "test_*.py" -v
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

The regression suite checks synthetic scenario outcomes, historical replay, insufficient-data handling, covenant summaries and backtest consistency. It is not an isolated unit-test suite and cannot run against an empty database. These commands are provided for verification; this README does not assert a passing run in a fresh environment.

## Scope and limitations

- Thresholds and priority rules are MVP defaults, not institutionally validated credit policy.
- The prototype is an analyst-support tool, not a calibrated probability-of-default model or automated lending decision system.
- Synthetic backtests demonstrate implementation behavior, not validated predictive performance.
- Replay filters by `observation_date`. Real-world point-in-time validation also needs reliable data-availability timestamps and revision handling.
- Reproducible database bootstrap, backend dependency pinning, isolated test fixtures and CI remain improvements.
- The API currently has permissive CORS settings and no authentication layer in its route module; deployment requires additional configuration.

## Related projects

- [CreditSentinel V2](https://github.com/williamf48/CreditSentinelV2): ensemble model inference and an interactive credit dashboard.
- [CreditSentinel original](https://github.com/williamf48/Credit-Sentinel.): earlier single-model application.

## License

No license file is currently included in this repository.

