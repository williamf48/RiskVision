# RiskVision Current State — Professional Monitoring

Updated: 13 October 2026

RiskVision is a working credit-monitoring prototype with a React/Vite interface and a Python/FastAPI backend. Transparent rules combine financial deterioration, contractual covenant breaches and evidence quality into an analyst review queue. The current sample workspace contains 25 synthetic borrowers and ₹1,056 Cr of exposure.

## Implemented workflow

| Workspace | Current behavior |
| --- | --- |
| Monitoring | Ranked borrower queue, credit exceptions, exposure, evidence coverage, search, filters and reporting cutoff |
| Borrower review | Four financial trend charts, priority drivers, evidence dates/sources, covenants and investigation prompts |
| Covenant register | Facility-level thresholds, recomputed actual-versus-limit headroom, breach status and testing deadlines |
| Analyst cases | Saved owner, status, due date, next action and decision rationale |
| Decision history | Before/after case values and the supporting assessment saved with each decision |
| Data quality | Missing, stale, estimated, conflicting, invalid and unscheduled evidence states |
| Policy | Visible demonstration rules and thresholds under policy version `RV-MON-2.0` |
| Portfolio and validation | Exposure/concentration analysis, original trajectory views, historical replay and synthetic stress backtests |
| Exports | Filtered queue CSV and printable borrower review HTML |

## Architecture and persistence

- React, React Router and Recharts provide the interface. Route and chart bundles load as needed.
- FastAPI exposes the original analysis routes plus `/monitoring`, borrower case routes, activity and policy.
- SQLAlchemy connects to PostgreSQL in the normal workspace and to an isolated SQLite database in demo mode.
- `backend/demo.py` bootstraps the synthetic SQLite portfolio. `start_demo.py` launches both services; `START_RISKVISION.bat` supports subsequent Windows runs.
- Analyst cases and assessment snapshots persist in the workspace database. Expected-version checks reject stale edits with HTTP 409.
- Local environment files, installed packages and database files are excluded from version control.

## Monitoring logic

Credit assessment, evidence quality and analyst case status are separate. Closing a case does not clear a breach or remove a financial warning.

Confirmed active covenant breaches trigger urgent review, including a last confirmed breach that later valid evidence has not cleared. Contractual results are recomputed from actual values and thresholds before rounding; equality is at the limit rather than a breach.

Freshness follows reporting cadence and period end. Only eligible observations establish current financial signals. Missing or stale evidence cannot establish healthy credit. Trends need at least three comparable observations; conflicting sources, cadence changes, invalid readings and reporting gaps break the comparable series.

At the default observation cutoff, **31 May 2026**, Falcon Realty and Crest Realty are urgent. Crest's minimum DSCR test is **1.05× against a required 1.10×**. Moving the cutoff forward demonstrates aging evidence without clearing a known unresolved breach.

## Verification

Before publication, all **43 backend tests**, frontend lint and the production frontend build passed. The backend suite covers the original scenario regressions, historical replay, evidence boundaries, covenant calculations, persistent cases and concurrent-edit protection.

The professional-monitoring update also has a previously completed desktop/mobile browser walkthrough covering navigation, filters, cutoff changes, saved decisions and exports. See [the demo guide](DEMO_GUIDE.md#verification-commands) to reproduce the automated checks.

## Current boundaries

The dataset is synthetic and the monitoring policy is a development policy. RiskVision does not implement a trained default-prediction model, authenticated users, role-based permissions or a tamper-proof regulatory audit system. Actor names are entered by the analyst. Historical cutoffs filter observations; they do not reconstruct historical contracts or publication timestamps.

The sample SQLite bootstrap is complete. Normal PostgreSQL startup still expects an existing populated base schema; this branch does not provide the complete PostgreSQL bootstrap or CI pipeline. Default CORS is restricted to the two local development origins and can be configured with `RISKVISION_ALLOWED_ORIGINS`.

See [the professional monitoring upgrade](MONITORING_UPGRADE.md) for the detailed policy, workflow research and production requirements.

## Earlier development record

The notes below retain the earlier implementation history. Their dated behavior and backlog describe those earlier stages; the current implementation is summarized above.

Date: 1 September 2026

## Technology Stack

Frontend:
- React
- Vite
- Recharts

Backend:
- FastAPI
- Python
- Pandas
- SQLAlchemy

Database:
- PostgreSQL
- Database: risk_platform

---

## Current Architecture

PostgreSQL
    ↓
SQL queries
    ↓
Pandas / SQLAlchemy
    ↓
FastAPI endpoints
    ↓
JSON
    ↓
React fetch()
    ↓
Dashboard components

---

## Working Backend Endpoints

### /borrowers

Status:
Working

Source:
PostgreSQL

Returns:
- id
- borrower_name
- sector
- loan_amount
- created_at

Frontend usage:
Not currently used by React.

---

### /risk_scores

Status:
Working

Source:
PostgreSQL

Returns:
- borrower_name
- score
- classification

Frontend usage:
Not currently used directly.

---

### /portfolio_summary

Status:
Working

Source:
PostgreSQL

Currently returns:
- total_borrowers
- high_risk
- watchlist
- low_risk
- total_alerts
- high_severity_alerts

Frontend usage:
Not currently used.

Known issue:
total_exposure is not implemented.

---

### /alerts

Status:
Working

Source:
PostgreSQL

Frontend:
AlertsPanel.jsx

Returns:
- borrower_name
- alert_type
- severity
- created_at

Current limitations:
- no alert_id returned
- no borrower_id returned
- no alert lifecycle/status
- no explicit ordering
- no deduplication logic in endpoint

---

### /watchlist

Status:
Working

Source:
PostgreSQL

Frontend:
WatchlistTable.jsx

Current selection logic:

classification = Watchlist
OR
classification = High Risk

Current limitations:
- endpoint includes both Watchlist and High Risk borrowers
- no explicit ordering
- no borrower_id returned
- based entirely on static risk classification

---

### /top_risk_accounts

Status:
Working

Source:
PostgreSQL

Frontend:
TopRiskAccounts.jsx

Current logic:

ORDER BY risk_scores.score DESC
LIMIT 10

Current limitation:
Ranks borrowers only by current static risk score.

---

### /high_alerts

Status:
Working

Source:
PostgreSQL

Filter:
severity = HIGH

Frontend usage:
Not currently used.

---

## Current Portfolio Data

Total borrower records:
51

Borrowers with valid risk scores:
50

Borrower IDs:
- 51 IDs present
- 51 unique IDs
- 0 NULL IDs

Risk score table:
- 50 rows
- 50 unique borrower IDs
- 0 duplicate risk score rows
- 0 NULL classifications

---

## Known Data Issues

### ABC Ltd

Borrower ID:
1

Problem:
Exists in borrowers table but has no corresponding risk_scores record.

Result:
Portfolio contains 51 borrowers but only 50 classified borrowers.

---

### Duplicate Atlas Telecom Ltd

Two borrower records exist:

- ID 42
- ID 67

Both currently have:

Risk Score:
120

Classification:
High Risk

---

### Duplicate Fusion Telecom Pvt Ltd

Two borrower records exist:

ID 37:
- score 65
- High Risk

ID 62:
- score 45
- Watchlist

This demonstrates that borrower_name cannot safely be used as the unique borrower identity.

---

## Current Risk Scoring Methodology

RiskVision currently uses five binary rules.

### DPD

DPD > 30

+30 points

### DSCR

DSCR < 1

+25 points

### Revenue Decline

Revenue Decline > 20%

+20 points

### Cash Flow

Negative Cash Flow

+20 points

### Restructuring

Loan Restructured

+25 points

Maximum possible score:

120

---

## Current Classification

0–30:
Low Risk

31–60:
Watchlist

61+:
High Risk

---

## Current Scoring Limitations

The methodology is static and binary.

Examples:

DPD 31 days and DPD 100 days:
same +30 score.

DSCR 0.99 and DSCR 0.40:
same +25 score.

Revenue decline 21% and 60%:
same +20 score.

There is currently no:

- historical trajectory
- trend analysis
- velocity
- acceleration
- persistence
- volatility
- cross-signal convergence
- risk migration
- deterioration score
- intervention priority

---

## Frontend Status

### Live PostgreSQL-backed components

Top Risk Accounts:
Live through /top_risk_accounts

Risk Alerts:
Live through /alerts

Watchlist Monitoring:
Live through /watchlist

### Incomplete / Mock components

Total Exposure:
Placeholder only.

No value currently calculated or displayed.

Borrower Risk Distribution:
Hardcoded inside RiskChart.jsx.

Current hardcoded values include:
- ABC Infra
- Zenith
- Nova
- Delta

The chart does not represent the live PostgreSQL portfolio.

---

## Security Finding

DATABASE_URL including PostgreSQL credentials is currently hardcoded in main.py.

This must be moved to environment variables before repository sharing or production deployment.

---

## Major Architectural Finding

The current RiskVision pipeline is:

Borrower financial data
    ↓
risk_engine_excel.py
    ↓
five threshold rules
    ↓
static risk score
    ↓
Low / Watchlist / High
    ↓
risk_scores table
    ↓
FastAPI
    ↓
React

This is the legacy RiskVision intelligence layer.

The September development objective is to evolve this into a historical Borrower Deterioration Intelligence Engine.
## Portfolio Data Integrity Cleanup — 7 September 2026

A database integrity audit identified that the 25-borrower mock portfolio had been imported twice.

The obsolete import used borrower IDs 22–46. The canonical import used IDs 47–71.

Evidence for selecting IDs 47–71 as canonical:

- 25/25 risk scores match the current scoring methodology.
- The later records contain populated sector and loan-amount data.
- The canonical batch contains all 46 active alerts.
- Each canonical borrower has one financial record and one risk-history record.
- Only 9/25 scores in the obsolete batch matched the current methodology.

A full PostgreSQL backup was created before cleanup.

The obsolete IDs 22–46 and their associated risk scores, financial rows and risk-history rows were removed transactionally.

A legacy prototype borrower, ABC Ltd (ID 1), was also removed after confirming it had no financials, risk score, alerts or risk history.

Final integrity state:

- Borrowers: 25
- Unique borrower IDs: 25
- Financial rows: 25
- Risk scores: 25
- Unique scored borrowers: 25
- Risk-history rows: 25
- Alerts: 46
- Null classifications: 0
- Duplicate borrower names: 0
- Borrowers without risk scores: 0

The API layer now preserves borrower_id throughout borrower-level responses and alert_id throughout alert-level responses.

A new GET /borrowers/{borrower_id} endpoint provides live borrower detail, financial metrics, risk assessment and alerts.

The React borrower drill-down now uses the real PostgreSQL borrower_id rather than list position.


## Historical Deterioration Intelligence Foundation — 8 September 2026

RiskVision now has a dedicated historical metric-observation layer separate from the legacy borrower_financials snapshot table.

Created:
- borrower_metric_observations table
- SQL migration for reproducible schema creation
- synthetic history seed for Falcon Realty Ltd
- generic trajectory_engine.py

Historical observation fields include:
- borrower_id
- metric_code
- metric_value
- observation_date
- period_start
- period_end
- reporting_frequency
- source
- data_quality
- created_at

The architecture supports different reporting frequencies, including monthly, quarterly and annual observations.

Database protections include:
- unique borrower/metric/date/source observations
- reporting-period range validation
- controlled reporting-frequency values
- controlled data-quality values

Falcon Realty Ltd was seeded with 16 synthetic observations across four signals:

DSCR:
1.45 -> 1.31 -> 1.12 -> 0.90

BOUNCE_RATE:
2.0 -> 3.2 -> 5.4 -> 8.1

RECEIVABLE_DAYS:
52 -> 61 -> 75 -> 94

DEBT_EBITDA:
2.2 -> 2.5 -> 2.9 -> 3.4

The seed is idempotent: rerunning it leaves the observation count at 16.

The trajectory engine now:
- loads historical observations from PostgreSQL
- understands whether UP or DOWN represents deterioration for each configured metric
- calculates current value
- previous value
- absolute change
- percentage change
- direction
- persistence

Falcon Realty borrower-level analysis currently produces:

- Metrics analyzed: 4
- Deteriorating signals: 4
- Improving signals: 0
- Stable signals: 0
- Persistent deterioration signals: 4
- Cross-signal convergence: 100%

This is the first implementation of RiskVision's trajectory-based and cross-signal deterioration intelligence layer.


## Current Condition + Trajectory Intelligence — 8 September 2026

RiskVision's deterioration engine now combines current-condition severity with historical trajectory analysis.

Current-condition severity was added using clearly labeled MVP/default development thresholds. These thresholds are not institutionally validated and are intended to be configurable later by lender, industry, geography and underwriting policy.

Configured development metrics:

- DSCR
- BOUNCE_RATE
- RECEIVABLE_DAYS
- DEBT_EBITDA

Each signal now returns:

- current value
- current condition
- condition severity
- previous value
- latest absolute change
- latest percentage change
- deterioration direction
- persistence
- days since previous observation
- risk velocity normalized to 30 days
- previous normalized risk velocity
- velocity change
- acceleration/deceleration interpretation
- number of historical observations

Current-condition states:

- HEALTHY = severity 0
- WATCH = severity 1
- WEAK = severity 2
- CRITICAL = severity 3

Falcon Realty Ltd currently demonstrates:

Current condition:
- Critical signals: 3
- Weak signals: 1
- Watch signals: 0
- Healthy signals: 0

Trajectory:
- Deteriorating signals: 4
- Persistent deterioration signals: 4
- Accelerating deterioration signals: 3
- Decelerating deterioration signals: 1
- Cross-signal convergence: 100%

Falcon metric examples:
- DSCR: 0.90, CRITICAL, deteriorating, 6.55% risk velocity / 30d, accelerating
- BOUNCE_RATE: 8.10, CRITICAL, deteriorating, 48.39% risk velocity / 30d, decelerating
- RECEIVABLE_DAYS: 94, CRITICAL, deteriorating, 8.44% risk velocity / 30d, accelerating
- DEBT_EBITDA: 3.40, WEAK, deteriorating, 5.75% risk velocity / 30d, accelerating

The borrower deterioration API automatically exposes these fields through:

GET /borrowers/{borrower_id}/deterioration

The borrower profile UI now displays:

- current condition counts
- trajectory counts
- cross-signal convergence
- signal-level condition
- latest percentage change
- normalized risk velocity
- deterioration direction
- acceleration/deceleration
- persistence

Regression behavior was verified:

- Falcon Realty Ltd (ID 65): full deterioration intelligence displayed
- Orion Power Projects Ltd (ID 64): correctly displays insufficient historical data instead of interpreting missing history as healthy
- nonexistent borrowers return HTTP 404

RiskVision now has a PID-inspired analytical structure:

- P-like: current-condition severity
- I-like: persistence
- D-like: time-normalized deterioration velocity
- additional derivative proxy: change in velocity
- additional layer: cross-signal convergence


## Portfolio Intervention Intelligence - 9 September 2026

RiskVision now performs portfolio-level borrower deterioration prioritization using the historical deterioration engine.

New portfolio capabilities:
- Borrower-level intervention priority: URGENT, HIGH, MEDIUM, LOW, INSUFFICIENT_DATA
- Explainable reason codes and human-readable priority explanations
- Recommended analyst investigations
- Portfolio-wide intervention ranking
- Portfolio intervention summary
- Dashboard migration from legacy static risk-score views to deterioration-based prioritization

Synthetic portfolio validation set:
- Falcon Realty Ltd -> URGENT
- Crest Realty Pvt Ltd -> HIGH
- Nova Energy Ltd -> MEDIUM
- Beta Logistics Pvt Ltd -> MEDIUM
- Alpha Manufacturing Ltd -> LOW
- Orion Power Projects Ltd -> INSUFFICIENT_DATA

Current portfolio summary:
- Total borrowers: 25
- Historically assessable: 5
- Actionable borrowers: 4
- URGENT: 1
- HIGH: 1
- MEDIUM: 2
- LOW: 1
- INSUFFICIENT_DATA: 20

New API endpoints:
- GET /intervention_watchlist
- GET /intervention_summary

The main dashboard now displays:
- Total Exposure
- Intervention Priority Distribution
- Top Intervention Accounts
- Priority Drivers
- Intervention Watchlist

The intervention watchlist ranks borrowers using intervention priority, current critical-condition signals, cross-signal convergence, accelerating deterioration and persistent deterioration.

Regression checks:
- Falcon Realty Ltd retains full URGENT deterioration and intervention analysis.
- Orion Power Projects Ltd correctly remains INSUFFICIENT_DATA with no false priority assignment.

The current implementation uses transparent MVP heuristic logic and synthetic development thresholds. It is not a probability of default, automated lending decision, or institutionally validated credit-policy framework.

## Interactive Risk Intelligence Workspace - 11 September 2026

RiskVision was upgraded from a primarily dashboard-based interface into an interactive multi-workspace credit deterioration application.

Application navigation now includes:
- Dashboard
- Portfolio Intelligence
- Borrower Directory
- Intervention Centre
- Alerts
- Reports

New frontend routing:
- / -> executive dashboard
- /portfolio -> portfolio intelligence workspace
- /borrowers -> searchable borrower directory
- /borrower/:id -> borrower intelligence workspace
- /interventions -> intervention review centre
- /alerts -> alert investigation workspace
- /reports -> reporting workspace

Executive dashboard improvements:
- clickable Total Exposure KPI
- clickable Borrower count
- clickable Actionable Borrowers KPI
- clickable Urgent borrower KPI
- Historical Coverage KPI
- Intervention Priority Distribution
- Highest Intervention Priorities
- Emerging Risk Drivers
- quick links into analyst workflows

Portfolio Intelligence improvements:
- borrower search
- priority filtering
- sector filtering
- historical coverage filtering
- exposure and sector context
- expandable borrower rows
- explainable Why Flagged details
- recommended investigations
- direct borrower drill-down

Borrower Directory improvements:
- borrower search
- sector filtering
- intervention-priority visibility
- historical-coverage visibility
- direct borrower drill-down

Borrower workspace was redesigned into interactive tabs:
- Overview
- Deterioration
- History
- Alerts

Borrower Overview now displays:
- exposure
- current legacy risk classification
- intervention priority
- historical observation coverage
- borrower information
- latest financial snapshot
- intervention summary

Deterioration workspace displays:
- explainable intervention drivers
- recommended analyst investigations
- current signal condition
- latest percentage change
- 30-day-normalized deterioration velocity
- trajectory direction
- acceleration/deceleration
- persistence

New historical intelligence API:
- GET /borrowers/{borrower_id}/history

The historical API returns grouped borrower observations including:
- metric code
- observation date
- value
- reporting frequency
- reporting period
- source
- data quality

Borrower History workspace now supports interactive analysis of:
- DSCR
- Bounce Rate
- Receivable Days
- Debt / EBITDA

Historical charts include:
- selectable metric views
- line-chart trajectory visualization
- observation dates
- hover tooltips
- reporting frequency
- source
- data quality
- underlying observation table

Validated historical examples:
- Falcon Realty Ltd: 4 metrics and 16 observations
- Orion Power Projects Ltd: 0 observations and a clean no-history state

Intervention Centre improvements:
- borrower search
- priority filtering
- sector filtering
- portfolio rank
- exposure context
- critical signal count
- deteriorating signal count
- persistent deterioration
- accelerating deterioration
- convergence
- expandable Why Flagged rationale
- recommended analyst investigations
- direct borrower drill-down

Alerts workspace improvements:
- borrower search
- severity filtering
- alert-type filtering
- expandable alert details
- borrower links
- direct borrower drill-down

Data-quality behavior:
- insufficient historical data remains explicitly separated from low risk
- Orion Power Projects Ltd correctly remains INSUFFICIENT_DATA despite its legacy High Risk classification
- borrowers with missing trajectory history do not receive false deterioration priorities

Validation:
- frontend production build completed successfully with Vite
- 598 modules transformed
- no frontend compilation errors
- Vite reported only a non-blocking bundle-size warning

The current deterioration and intervention framework remains transparent MVP heuristic logic using synthetic development thresholds. It is not a probability-of-default model, automated lending decision, or institutionally validated credit-policy framework.

## Covenant and Portfolio Analytics Intelligence - 11 September 2026

RiskVision was extended from borrower deterioration monitoring into a broader credit intelligence workspace covering covenant pressure, portfolio concentration and live reporting.

### Covenant intelligence
- Added facilities, covenants and covenant_tests data architecture.
- Added database migration: backend/migrations/003_create_facility_covenant_tables.py.
- Added synthetic facility and covenant seed data: backend/seeds/003_seed_facilities_covenants.py.
- Added backend covenant engine supporting borrower-level and portfolio-level covenant monitoring.
- Covenant states: BREACHED, NEAR_BREACH, TIGHT, HEALTHY and INSUFFICIENT_DATA.
- Added borrower covenant analysis including threshold, actual value, headroom, testing frequency, last/next test dates and facility information.
- Added GET /borrowers/{borrower_id}/covenants.
- Added GET /covenant_watchlist.
- Added GET /covenant_summary.

Current synthetic covenant validation:
- Falcon Realty Ltd -> BREACHED.
- Crest Realty Pvt Ltd -> BREACHED.
- Nova Energy Ltd -> TIGHT.
- Alpha Manufacturing Ltd -> HEALTHY.
- Beta Logistics Pvt Ltd -> HEALTHY.
- Orion Power Projects Ltd -> INSUFFICIENT_DATA.
- Borrowers with covenants: 6.
- Borrowers under covenant pressure: 3.
- Total covenants: 12.
- Breached covenants: 2.
- Near-breach covenants: 1.
- Tight covenants: 1.
- Healthy covenants: 6.
- Untested covenants: 2.

### Borrower workspace
- Added Covenants as a fifth borrower intelligence tab alongside Overview, Deterioration, History and Alerts.
- Borrower covenant views show covenant status, facility details, threshold requirements, actual values, headroom and testing schedule.
- Insufficient historical covenant data remains explicitly separated from healthy compliance.

### Portfolio covenant pressure
- Added interactive Covenant Pressure panel to the Portfolio workspace.
- Added covenant-state filtering and borrower-level drill-down.
- Portfolio covenant monitoring now displays breached, near-breach, tight, healthy and untested counts.

### Portfolio concentration analytics
- Added backend/portfolio_analytics.py.
- Added GET /portfolio_analytics.
- Added sector exposure aggregation and portfolio exposure shares.
- Added actionable exposure analysis.
- Added historical-data coverage by sector.
- Added covenant-pressure concentration by sector.
- Added largest-borrower and top-five borrower exposure concentration.
- Added borrower and sector Herfindahl-Hirschman concentration indices.

Current synthetic portfolio analytics:
- Total borrowers: 25.
- Total exposure: INR 1,056 Cr.
- Sectors represented: 18.
- Historically assessable borrowers: 5.
- Historical coverage: 20.0%.
- Actionable exposure: INR 180 Cr.
- Actionable exposure share: 17.05%.
- Largest borrower exposure share: 8.33%.
- Top-five borrower exposure share: 35.13%.
- Borrower exposure HHI: 489.42.
- Sector exposure HHI: 789.95.

### Interactive portfolio analytics UI
- Added Portfolio Analytics panel.
- Added sector exposure visualization.
- Added Sector Analysis and Largest Exposures interactive views.
- Added sorting by exposure, actionable borrowers, historical coverage and covenant pressure.
- Added borrower drill-down links from portfolio analytics.

### Reporting workspace
- Replaced the Reports placeholder with a live portfolio reporting workspace.
- Reports now combine portfolio summary, intervention summary, covenant summary, intervention watchlist and covenant watchlist.
- Added Intervention CSV export.
- Added full JSON report export.

### Regression validation
- Deterioration engine retains 1 URGENT, 1 HIGH, 2 MEDIUM, 1 LOW and 20 INSUFFICIENT_DATA borrowers.
- Actionable borrowers remain 4 and historically assessable borrowers remain 5.
- Covenant portfolio summary and portfolio concentration analytics passed direct backend regression checks.

Important limitation:
- Current covenant thresholds, facilities, historical observations and portfolio results use synthetic development data.
- Intervention priorities and covenant-pressure classifications use transparent MVP heuristic logic and are not institutionally validated credit-policy decisions or probability-of-default estimates.

## Historical Replay and Backtesting - 11 September 2026

RiskVision now includes point-in-time historical replay and a synthetic backtesting framework for validating deterioration-engine behaviour over time.

### Point-in-time deterioration replay
- Extended the trajectory engine with optional as_of_date analysis.
- Historical analysis only uses observations available on or before the replay date.
- Current production-style calls remain backward compatible when no as_of_date is supplied.
- Added point-in-time borrower and portfolio analysis without changing the existing trajectory mathematics.
- Historical replay explicitly prevents future observations from leaking into earlier analysis states.

### Borrower replay
- Added automatic replay across each borrower's historical observation dates.
- Replay records intervention priority, analyzed signals, deterioration, critical-condition count, persistence, acceleration and cross-signal convergence at every historical point.
- Falcon Realty historical replay demonstrates migration from insufficient history through MEDIUM and HIGH to URGENT intervention priority as additional deterioration evidence becomes available.

### Synthetic stress-event framework
- Added borrower_stress_events schema for labelled outcome events.
- Added migration: backend/migrations/004_create_stress_events.py.
- Added synthetic event seed data: backend/seeds/004_seed_stress_events.py.
- Synthetic stress-event labels are explicitly separated from real institutional validation data.

### Historical backtesting engine
- Added backend/backtest_engine.py.
- Added borrower-level and portfolio-level replay backtesting.
- Added first MEDIUM, HIGH and URGENT intervention dates.
- Added first alert date and maximum historical intervention priority.
- Added lead-time calculation relative to labelled stress events.
- Added historical maximum cross-signal convergence tracking.
- Added portfolio confusion-matrix framework with true positives, false positives, true negatives and false negatives.
- Added precision, recall and specificity calculations for development validation.
- Current synthetic validation set contains 5 historically assessable borrowers and 2 synthetic stress-event labels.
- Synthetic backtesting metrics are development validation only and are not presented as predictive-performance claims.

### Historical validation API
- Added GET /borrowers/{borrower_id}/replay.
- Added GET /borrowers/{borrower_id}/backtest.
- Added GET /backtest_summary.
- FastAPI version advanced to include historical validation capabilities.

### Automated regression testing
- Added backend/tests/test_riskvision_regression.py.
- Added 10 automated regression tests covering current deterioration state, historical replay, look-ahead protection, insufficient-data handling, intervention summary, covenant intelligence, portfolio analytics and backtesting consistency.
- Final regression run: 10 tests passed.

### Validation and Replay workspace
- Added an interactive Validation workspace to the React application.
- Added borrower selection across historically assessable accounts.
- Added intervention-priority migration visualization.
- Added historical replay table with deterioration, critical-condition, persistence, acceleration and convergence information.
- Added first MEDIUM, HIGH and URGENT escalation dates.
- Added labelled stress-event and lead-time display.
- Added prominent SYNTHETIC VALIDATION disclosure to prevent development results from being interpreted as institutional predictive validation.

### Final pre-resume validation
- Backend regression suite passed all 10 tests.
- Frontend production build completed successfully.
- Existing dashboard, borrower, intervention, covenant, portfolio analytics, alerts and reporting functionality remains integrated.

Important limitation:
- Historical borrower observations, covenant data and labelled stress events in the current validation environment are synthetic development data.
- Backtesting results demonstrate system behaviour, temporal replay and engineering correctness; they do not establish real-world predictive accuracy or institutionally validated credit performance.
