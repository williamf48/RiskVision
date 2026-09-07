# RiskVision Current State

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
## Portfolio Data Integrity Cleanup � 7 September 2026

A database integrity audit identified that the 25-borrower mock portfolio had been imported twice.

The obsolete import used borrower IDs 22�46. The canonical import used IDs 47�71.

Evidence for selecting IDs 47�71 as canonical:

- 25/25 risk scores match the current scoring methodology.
- The later records contain populated sector and loan-amount data.
- The canonical batch contains all 46 active alerts.
- Each canonical borrower has one financial record and one risk-history record.
- Only 9/25 scores in the obsolete batch matched the current methodology.

A full PostgreSQL backup was created before cleanup.

The obsolete IDs 22�46 and their associated risk scores, financial rows and risk-history rows were removed transactionally.

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

