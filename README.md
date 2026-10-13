# RiskVision

**Explainable credit deterioration monitoring, covenant analysis and portfolio intervention prioritization.**

RiskVision is a full-stack development prototype for reviewing corporate credit portfolios. It combines financial snapshots with historical metric observations to highlight worsening borrower conditions, explain the signals driving intervention priority and support analyst investigation.

Built by [William Fernandes](https://github.com/williamf48).

## Run the professional monitoring demo

The demo launches the API and interface together with **25 synthetic borrowers**. It creates an isolated SQLite workspace, so a fresh demo installation does not need PostgreSQL. Python 3.12 and Node.js 24 were used for verification.

On Windows, open PowerShell in the cloned project folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd frontend
npm.cmd ci
cd ..
.\.venv\Scripts\python.exe start_demo.py
```

For subsequent runs, double-click `START_RISKVISION.bat`. On macOS/Linux, install the same dependencies and run `.venv/bin/python start_demo.py`. The interface opens at http://127.0.0.1:5173; keep the terminal open while using it.

See [the demo guide](docs/DEMO_GUIDE.md) for complete setup instructions and [the current state](docs/CURRENT_STATE.md) for the implemented workflows and remaining limitations.

## Features

- **Historical deterioration analysis:** current condition, direction, persistence, time-normalized velocity and changes in velocity.
- **Cross-signal convergence:** identifies when multiple financial indicators deteriorate together.
- **Intervention prioritization:** URGENT, HIGH, MEDIUM, LOW and INSUFFICIENT_DATA, with reason codes and recommended investigations.
- **Facility-level covenants:** evaluates minimum and maximum thresholds, headroom and breach pressure.
- **Portfolio intelligence:** exposure, sector concentration, HHI concentration analytics and historical coverage.
- **Historical replay and backtesting:** reconstructs borrower trajectories at observation-date cutoffs and compares alerts with seeded stress events.
- **Analyst interface:** monitoring queue, case workspace, covenant register, data-quality matrix, borrower profiles, portfolio analytics, reports and validation views.
- **Evidence-aware monitoring:** separate credit exceptions from missing or unreliable data, with frequency-aware freshness and contractual breach overrides.
- **Persistent analyst cases:** owners, due dates, actions, decision history, saved evidence snapshots, and concurrent-edit protection.
- **Policy transparency:** readable priority rules, thresholds, and monitoring scope.
- **Verification:** 43 backend regression, evidence-boundary and case-workflow tests, plus frontend lint and production build checks.

## Technology stack

| Layer | Technologies |
| --- | --- |
| Frontend | React, Vite, React Router, Recharts |
| API | Python, FastAPI |
| Data access | Pandas, SQLAlchemy |
| Database | PostgreSQL; isolated SQLite in demo mode |
| Configuration | python-dotenv |
| Verification | Python unittest |

The main data flow is **PostgreSQL or demo SQLite → analytical modules → FastAPI JSON endpoints → React workspaces**. Case decisions and their supporting assessments persist in the selected workspace database. Excel processing is handled separately by the legacy import script.

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
| `backend/monitoring_engine.py` | Evidence quality, covenant overrides and combined triage policy |
| `backend/case_store.py` | Persistent versioned cases and decision history |
| `backend/monitoring_api.py` | Monitoring and case endpoints |
| `backend/connection.py` | Environment-based PostgreSQL connection or isolated demo SQLite |
| `backend/trajectory_engine.py` | Historical deterioration and intervention logic |
| `backend/covenant_engine.py` | Covenant headroom and pressure analysis |
| `backend/portfolio_analytics.py` | Exposure and concentration analytics |
| `backend/backtest_engine.py` | Observation-date replay and stress-event comparison |
| `backend/risk_engine_excel.py` | Legacy Excel import and static scoring |
| `backend/migrations/` | Additional observation, covenant and stress-event tables |
| `backend/seeds/` | Synthetic development histories and scenarios |
| `backend/tests/` | Scenario regression, evidence boundaries and case-workflow checks |
| `frontend/` | React application |
| `data/` | Excel workbooks |
| `docs/CURRENT_STATE.md` | Current architecture, implemented workflows and limitations |

## Recording-ready sample workspace

For the polished UI and a reproducible sample portfolio, see [the demo guide](docs/DEMO_GUIDE.md). After installing dependencies, run `python start_demo.py` in your virtual environment to launch both services. The isolated SQLite demo runs the existing analytical engines with the committed synthetic fixtures. PostgreSQL remains the default for normal API startup.

The v2 monitoring workspace adds evidence-aware triage, a covenant register, a data-quality matrix, and database-backed analyst cases. Each saved decision retains its rationale and assessment snapshot. Actor labels are user-entered; the journal is not an authenticated, tamper-proof audit system. Existing browser notes can be brought into a new case. See [the professional monitoring upgrade](docs/MONITORING_UPGRADE.md) for research references, policy details, the Windows updater, and a two-minute walkthrough.

![Professional monitoring workspace](docs/professional-monitoring.png)

## PostgreSQL workspace setup

Use this setup for an existing PostgreSQL workspace. For a fresh sample installation, use the demo instructions above.

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

Install the pinned backend dependencies:

```bash
python -m pip install -r backend/requirements.txt
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

The legacy Excel importer and alert script now use the shared environment-based connection. The importer defaults to `data/Book3.xlsx`; set `RISKVISION_WORKBOOK` for another file. Historical commits may still contain previously committed local credentials; change any password that is still in use.

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

Open the URL printed by Vite. The shared API client defaults to `http://127.0.0.1:8000`. Set `VITE_API_BASE_URL` in `frontend/.env.local` to change it.

## Selected API endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Service health and workspace mode |
| `GET /monitoring?as_of=2026-05-31` | Evidence-aware portfolio queue and summary |
| `GET /monitoring/policy` | Monitoring rules and thresholds |
| `GET /monitoring/borrowers/{borrower_id}` | Borrower assessment, saved case and decision history |
| `PUT /monitoring/borrowers/{borrower_id}/case` | Save a versioned analyst decision and supporting evidence |
| `GET /monitoring/activity` | Recent recorded case decisions |
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

Seed the isolated sample portfolio and run all 43 backend tests from the repository root:

```bash
python backend/demo.py --seed-only
RISK_DEMO_MODE=1 python -m unittest discover -s backend/tests -p "test_*.py" -v
```

Use the virtual environment's Python. The [demo guide](docs/DEMO_GUIDE.md#verification-commands) includes the equivalent PowerShell commands. With the expected PostgreSQL fixture and environment configured, the same suite can also run against that dedicated development database:

```bash
RISK_DEMO_MODE=0 python -m unittest discover -s backend/tests -p "test_*.py" -v
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

The suite checks synthetic scenario outcomes, historical replay, evidence freshness and quality, covenant threshold boundaries, breach overrides, persisted decisions, conflicting edits and backtest consistency. Portfolio integration tests require the seeded fixture. The 43 tests, frontend lint and production build passed before this update was published; these checks do not validate a production lender's credit policy.

## Scope and limitations

- Thresholds and priority rules are MVP defaults, not institutionally validated credit policy.
- The prototype is an analyst-support tool, not a calibrated probability-of-default model or automated lending decision system.
- Synthetic backtests demonstrate implementation behavior, not validated predictive performance.
- Replay filters by `observation_date`. Real-world point-in-time validation also needs reliable data-availability timestamps and revision handling.
- Complete PostgreSQL bootstrap, authenticated identities, institution-specific policies and CI remain improvements. The isolated SQLite bootstrap, database-backed case persistence and pinned backend manifest are included.
- Default CORS origins are `http://127.0.0.1:5173` and `http://localhost:5173`; `RISKVISION_ALLOWED_ORIGINS` configures a different trusted origin list. The API has no authentication layer, so production deployment requires access controls.

## Related projects

- [CreditSentinel V2](https://github.com/williamf48/CreditSentinelV2): ensemble model inference and an interactive credit dashboard.
- [CreditSentinel original](https://github.com/williamf48/Credit-Sentinel.): earlier single-model application.

## License

No license file is currently included in this repository.

