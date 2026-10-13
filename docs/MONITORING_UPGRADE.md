# RiskVision Professional Monitoring — v2

This update turns the sample-data demonstration into a more realistic credit analyst workflow. It uses deterministic, inspectable rules; it does not imitate a vendor's proprietary model or supply production banking controls.

## Install on William's Windows computer

1. Stop the current RiskVision terminal with **Ctrl+C**.
2. Download and extract **RiskVision-Professional-Update.zip** into Downloads.
3. Open the extracted update folder and double-click **APPLY_UPDATE.bat**.
4. The updater finds an installed RiskVision project in Downloads. It verifies source files and saves a backup before applying changes.
5. Open that original project folder and double-click **START_RISKVISION.bat**. The existing Python and Node packages are reused.
6. The browser opens at `http://127.0.0.1:5173`. Use **Ctrl+F5** if the old page is still visible.

If the original folder was moved, open a terminal inside the extracted update folder and run:

```powershell
python apply_update.py --target "C:\full\path\to\your\project"
```

The target is the folder containing `start_demo.py`, `frontend`, and `backend`. An optional `--check` validates without changing anything. Unexpected local source changes stop the update so they can be merged safely. Installed packages, `.env`, old browser notes, and the demo database are preserved. The isolated fixture's incorrect quarterly schedule is upgraded from December to June once. A local source and demo-database backup is created before applying the update.

For a fresh installation, use **RiskVision-Professional-v2.zip** and the Windows installation instructions in `DEMO_GUIDE.md`.

## What changed

| Real-world workflow | Implementation in RiskVision |
| --- | --- |
| Portfolio review and exception management | Searchable, sector-filtered monitoring queue with priority, exposure, evidence, owner, due date, and case status |
| Facility-level contractual oversight | Covenant register with actual value, contractual threshold, recomputed headroom, test date, evidence quality, and next test date |
| Data quality as part of credit assessment | Separate missing, stale, estimated, conflicting, invalid, and unscheduled evidence states |
| Accountable follow-up | Database-backed case owner, deadline, next action, decision rationale, and case lifecycle |
| Traceable decisions | Append-only application journal of before/after case values and the policy/evidence snapshot saved with each decision |
| Transparent analytics | A readable policy page, reporting cutoffs, financial trend charts, and source/age information |
| Review communication | Filtered CSV queue export and printable borrower credit-review HTML with saved decision history |

Previous browser notes are offered as a draft when opening a borrower with no saved database case. Save the decision to place that note in the new case journal.

## Research references

Official product descriptions were reviewed on 12 October 2026. These sources informed workflow patterns; RiskVision's formulas and policies are its own demonstration defaults.

- **Moody's Lending Suite Monitoring** describes centralized portfolio oversight, standardized reviews, documentation, covenant collection/testing, and early-warning monitoring. This informed the separation of evidence, contracts, and recorded review decisions. https://www.moodys.com/web/en/us/solutions/lending/loan-monitoring.html
- **nCino Commercial Lending / Credit Portfolio Management** describes portfolio reporting, covenant due-date notifications, continuous monitoring, and records of compliance. This informed the visible deadlines, case ownership, and follow-up workflow. https://www.ncino.com/solutions/commercial-lending and https://www.ncino.com/solutions/credit-portfolio-management
- **Allvue Portfolio Intelligence** describes searchable portfolio KPIs, borrower drill-through, financial measures, and covenant headroom monitoring. This informed the monitoring grid and linked borrower/facility analysis. https://www.allvuesystems.com/solutions/portfolio-intelligence/

## Monitoring policy RV-MON-2.0

The monitoring assessment is distinct from the original trajectory-only views. Those views remain available for comparison and historical regression continuity.

- **Urgent:** a confirmed active covenant breach, including a last confirmed breach not cleared by later valid evidence; or at least two critical and two deteriorating fresh indicators.
- **High:** a confirmed covenant within 5% headroom; a fresh critical indicator; or at least three fresh indicators deteriorating.
- **Watch:** a covenant inside its configured warning buffer; at least two deteriorating indicators; or a fresh weak indicator.
- **Data review:** no higher-priority credit trigger, but incomplete or unreliable evidence, missing comparable history, an overdue test, or an absent testing schedule.
- **Routine:** all four configured indicators have current valid values and at least three comparable observations, with no escalation trigger or evidence exception.

Closing a case records an analyst decision; it does not erase a credit signal or covenant breach. Status, owner, rationale, deadline and next action are saved server-side. Simultaneous edits use an expected version: a stale edit receives HTTP 409 and cannot overwrite a newer decision.

### Evidence policy

Freshness is measured from period end, falling back to observation date. Demo limits in calendar days: daily 3, weekly 10, monthly 45, quarterly 120, semiannual 210, annual 400. Values at the freshness boundary are eligible; older values are stale. Event-based readings require an explicit schedule.

Only current VALID observations drive current condition and trend signals. At least three comparable observations are required for a trend. Equal duplicate observations are deduplicated. Conflicting sources, a cadence change, an invalid reading, or an excessively large gap break the comparable series. Future observations and future periods are excluded. Negative debt/EBITDA needs manual interpretation and does not establish healthy leverage.

Undated legacy financial snapshots remain visible for reference; they do not establish current monitoring priority.

### Covenant policy

Minimum headroom = actual minus threshold. Maximum headroom = threshold minus actual. Relative headroom is absolute headroom divided by the absolute threshold, expressed as a percentage. Threshold zero retains absolute testing and has no percentage headroom. Classification happens before rounding. Exact equality is at the limit, not a breach.

Negative headroom is breached, 0–under 5% is near the limit, and 5%–under the covenant warning buffer is tight. Waived/expired contracts and inactive facilities do not create active credit triggers. Stale compliant results cannot establish current compliance. A later estimated or conflicting submission cannot clear a last valid breach.

The fixture's latest covenant tests are March 2026, so the next quarterly test is June 2026. This corrects the original December fixture date.

### Dates and scope

The demo opens at the dataset's last observation date, **31 May 2026**, to make demonstrations reproducible. The date picker changes the observation cutoff, not the computer clock. Case deadlines are evaluated against this displayed cutoff. Case journal timestamps are the actual save time.

A cutoff is **not a full historical reconstruction**: contract versions, publication times and undated snapshots are not archived. The historical validation page remains a separate original-engine demonstration and uses synthetic stress labels.

## Two-minute walkthrough

- **0–20 seconds:** Monitoring overview: 25 synthetic borrowers, ₹1,056 Cr exposure, 3 credit exceptions, 2 urgent borrowers, and 20% current indicator coverage.
- **20–45 seconds:** Open Falcon. Explain declining coverage, worsening payment behavior and the confirmed covenant breach. Show the date and source for the evidence.
- **45–70 seconds:** Open the covenant register. Compare actuals with contractual thresholds and explain why negative headroom overrides a softer trajectory signal.
- **70–100 seconds:** Open a case, set owner and due date, add a next action and rationale, save, and inspect decision history. Export the review.
- **100–120 seconds:** Show Orion's missing evidence and the policy page. State clearly that this is a rules-based prototype using synthetic data.

At the default cutoff, the combined policy identifies Falcon and Crest as urgent and Nova as watch. That is different from the original trajectory-only model, which has one urgent borrower. The difference is intentional and explained by covenant overrides and the new policy.

## Validation and production boundaries

The release is verified with regression and boundary tests, a production frontend build, linting, API checks, and a browser walkthrough including desktop/mobile layouts, exports, persisted reviews, cutoff propagation, and filters. Test code is in `backend/tests/test_monitoring.py` and the existing regression suite.

Production adoption still requires authenticated identities and role-based access, approved and calibrated lender policies, production data connectors, controlled covenant amendments/waivers, document ingestion, institution-specific escalation SLAs, durable tamper-resistant audit infrastructure, and independently validated models. The local journal has user-entered actor labels and is not a tamper-proof regulatory audit system. No emails, borrower messages, or automated lending actions are sent.
