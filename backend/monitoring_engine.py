"""Evidence-first credit monitoring. Transparent demonstration policy, not a rating model.

This layer deliberately keeps credit signals, evidence completeness, contract tests,
and analyst disposition separate. Observation cutoffs are not bitemporal replay:
the legacy schema has no historical contract versions or publication timestamps.
"""
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
import math

from sqlalchemy import text

from connection import DEMO_MODE, engine
from trajectory_engine import METRIC_CONFIG, analyze_trajectory, classify_condition

POLICY_VERSION = "RV-MON-2.0"
FRESHNESS_DAYS = {"DAILY": 3, "WEEKLY": 10, "MONTHLY": 45,
                  "QUARTERLY": 120, "SEMI_ANNUAL": 210, "ANNUAL": 400}
REVIEW_DAYS = {"URGENT": 1, "HIGH": 3, "WATCH": 7, "DATA_REVIEW": 14, "ROUTINE": 30}
PRIORITY_RANK = {"URGENT": 5, "HIGH": 4, "WATCH": 3, "DATA_REVIEW": 2, "ROUTINE": 1}
METRIC_NAMES = {"DSCR": "Debt-service coverage", "BOUNCE_RATE": "Payment bounce rate",
                "RECEIVABLE_DAYS": "Receivable days", "DEBT_EBITDA": "Debt / EBITDA"}
METRIC_UNITS = {"DSCR": "×", "BOUNCE_RATE": "%", "RECEIVABLE_DAYS": "days", "DEBT_EBITDA": "×"}


def day(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def finite(value):
    try:
        return value is not None and math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def policy():
    return {
        "version": POLICY_VERSION,
        "description": "Demonstration policy. Calibrate and approve for each lender before operational use.",
        "freshness_days": FRESHNESS_DAYS,
        "review_days": REVIEW_DAYS,
        "minimum_trend_observations": 3,
        "sector_limit_pct": 25,
        "metrics": [{"code": code, "name": METRIC_NAMES[code], "unit": METRIC_UNITS[code], **config}
                    for code, config in METRIC_CONFIG.items()],
        "rules": [
            {"priority": "URGENT", "rule": "A confirmed active covenant breach, or at least two critical and two deteriorating fresh indicators."},
            {"priority": "HIGH", "rule": "A confirmed covenant within 5% headroom, a critical fresh indicator, or at least three deteriorating fresh indicators."},
            {"priority": "WATCH", "rule": "A covenant inside its warning buffer, at least two deteriorating indicators, or a weak fresh indicator."},
            {"priority": "DATA_REVIEW", "rule": "No higher-priority credit trigger, but missing, stale, estimated, conflicting, or incomplete evidence or an overdue covenant test."},
            {"priority": "ROUTINE", "rule": "All four indicators have fresh valid values and three comparable observations, with no credit trigger or covenant evidence exception."},
        ],
        "limitations": [
            "Priority is an analyst triage category, not a probability of default or regulatory classification.",
            "Credit state is independent of case state. Closing a review does not remove an active breach.",
            "Observation cutoffs do not reconstruct historical contract terms or information publication times.",
            "Undated legacy financial snapshots are displayed separately and do not drive this monitoring policy.",
            "Facility registers are partial. Borrower exposure is summed once per borrower; no facility double counting.",
        ],
    }


def assess_metric(code, observations, as_of):
    """Never promote a stale/estimated/conflicting current value into a fresh signal."""
    result = {"code": code, "name": METRIC_NAMES[code], "unit": METRIC_UNITS[code],
              "value": None, "observed_at": None, "period_end": None, "source": None,
              "frequency": None, "age_days": None, "freshness": "MISSING", "condition": "NOT_ASSESSED",
              "direction": "INSUFFICIENT_DATA", "observations": 0, "trend_assessable": False,
              "velocity_30d": None, "change": None, "persistence": None,
              "acceleration": "NOT_ASSESSED", "history": [], "eligible": False}
    rows = [r for r in observations if day(r["observation_date"]) <= as_of
            and (not r.get("period_end") or day(r["period_end"]) <= as_of)]
    if not rows:
        return result
    grouped = defaultdict(list)
    for row in rows:
        grouped[day(row["observation_date"])].append(row)
    latest_date = max(grouped)
    latest_group = grouped[latest_date]
    latest = max(latest_group, key=lambda r: r.get("id", 0))
    frequency = latest["reporting_frequency"]
    age = (as_of - day(latest.get("period_end") or latest["observation_date"])).days
    result.update(value=float(latest["metric_value"]) if finite(latest["metric_value"]) else None,
                  observed_at=latest_date.isoformat(), period_end=str(latest.get("period_end") or latest_date)[:10],
                  source=", ".join(sorted({r["source"] for r in latest_group})), frequency=frequency, age_days=age)

    def valid_value(r):
        value = r["metric_value"]
        if not finite(value):
            return False
        value = float(value)
        return not ((code == "BOUNCE_RATE" and not 0 <= value <= 100)
                    or (code in ("RECEIVABLE_DAYS", "DEBT_EBITDA") and value < 0))

    def consistent(group):
        return (all(valid_value(r) for r in group)
                and len({float(r["metric_value"]) for r in group}) == 1
                and len({(r["reporting_frequency"], str(r.get("period_end"))) for r in group}) == 1)

    if not all(valid_value(r) for r in latest_group):
        freshness = "INVALID"
    elif not consistent(latest_group):
        freshness = "CONFLICT"
        result["value"] = None
    elif any(r["data_quality"] != "VALID" for r in latest_group):
        freshness = "STALE" if any(r["data_quality"] == "STALE" for r in latest_group) else "ESTIMATED"
    elif frequency not in FRESHNESS_DAYS:
        freshness = "UNSCHEDULED"
    elif age > FRESHNESS_DAYS[frequency]:
        freshness = "STALE"
    else:
        freshness = "VALID"
    result["freshness"] = freshness
    # Deduplicate equal same-date observations; conflicting sources never become zero-day trends.
    # Cadence changes require a new comparable series. Older invalid dates break continuity.
    comparable = []
    for observed in sorted(grouped):
        group = grouped[observed]
        r = max(group, key=lambda item: item.get("id", 0))
        if (not consistent(group) or any(x["data_quality"] != "VALID" for x in group)
                or r["reporting_frequency"] != frequency):
            comparable = []
            continue
        if comparable and (observed - day(comparable[-1]["observation_date"])).days > FRESHNESS_DAYS.get(frequency, 0):
            comparable = []
        comparable.append(r)
    result["history"] = [{"date": str(r["observation_date"])[:10], "value": float(r["metric_value"])}
                         for r in comparable]
    result["observations"] = len(comparable)
    result["eligible"] = freshness == "VALID"
    if not result["eligible"]:
        return result
    config = METRIC_CONFIG[code]
    result["condition"] = classify_condition(result["value"], config["bad_direction"], config["condition_thresholds"])["condition"]
    if len(comparable) >= 3:
        trend = analyze_trajectory([float(r["metric_value"]) for r in comparable],
                                   [r["observation_date"] for r in comparable], config["bad_direction"])
        result.update(direction=trend["direction"], velocity_30d=trend.get("risk_velocity_30d"),
                      change=round(result["value"] - float(comparable[-2]["metric_value"]), 4),
                      persistence=trend.get("persistence"), acceleration=trend.get("acceleration_direction", "NOT_ASSESSED"),
                      trend_assessable=True)
    return result


def covenant_headroom(actual, threshold, direction, buffer=15):
    """Classify before display rounding. Exactly at a contractual limit is not breached."""
    if not finite(actual) or not finite(threshold) or not finite(buffer) or float(buffer) < 0:
        raise ValueError("Covenant values must be finite and the warning buffer non-negative")
    if direction not in ("MINIMUM", "MAXIMUM"):
        raise ValueError("Unknown covenant direction")
    actual, threshold = Decimal(str(actual)), Decimal(str(threshold))
    absolute = actual - threshold if direction == "MINIMUM" else threshold - actual
    percentage = absolute / abs(threshold) * 100 if threshold != 0 else None
    if absolute < 0:
        status = "BREACHED"
    elif absolute == 0 or (percentage is not None and percentage < 5):
        status = "NEAR_BREACH"
    elif percentage is not None and percentage < Decimal(str(buffer)):
        status = "TIGHT"
    else:
        status = "COMPLIANT"
    return {"headroom_absolute": float(absolute), "headroom_pct": float(percentage) if percentage is not None else None,
            "result": status}


def assess_covenant(covenant, tests, as_of):
    result = dict(covenant)
    for key in ("threshold_value", "warning_buffer_pct", "outstanding_amount", "sanctioned_amount"):
        result[key] = float(result[key]) if finite(result.get(key)) else None
    result["next_test_date"] = str(result["next_test_date"])[:10] if result.get("next_test_date") else None
    result.update(actual=None, test_date=None, source=None, quality=None, age_days=None,
                  headroom_absolute=None, headroom_pct=None, result="UNTESTED", freshness="MISSING", confirmed=False)
    tests = [r for r in tests if day(r["test_date"]) <= as_of]
    if tests:
        test_day = max(day(r["test_date"]) for r in tests)
        latest_group = [r for r in tests if day(r["test_date"]) == test_day]
        test = max(latest_group, key=lambda r: r["id"])
        age = (as_of - test_day).days
        result.update(actual=float(test["actual_value"]) if finite(test["actual_value"]) else None,
                      test_date=test_day.isoformat(), source=test["source"], quality=test["data_quality"], age_days=age)
        conflict = len({Decimal(str(r["actual_value"])) for r in latest_group if finite(r["actual_value"])}) > 1
        if covenant.get("metric_code") == "DEBT_EBITDA" and finite(test["actual_value"]) and float(test["actual_value"]) < 0:
            result.update(result="UNVERIFIED", freshness="INVALID")
        elif conflict:
            result.update(result="UNVERIFIED", freshness="CONFLICT", actual=None)
        elif any(r["data_quality"] != "VALID" for r in latest_group):
            result.update(result="UNVERIFIED", freshness=test["data_quality"] if test["data_quality"] != "VALID" else "ESTIMATED")
        else:
            try:
                result.update(covenant_headroom(test["actual_value"], covenant["threshold_value"],
                                               covenant["threshold_direction"], covenant["warning_buffer_pct"]))
                result["freshness"] = "STALE" if age > FRESHNESS_DAYS.get(covenant["testing_frequency"], 0) else "VALID"
                # An old confirmed breach remains an exception until a subsequent valid test resolves it.
                result["confirmed"] = result["freshness"] == "VALID" or result["result"] == "BREACHED"
            except ValueError:
                result.update(result="UNVERIFIED", freshness="INVALID")
    # Estimated/conflicting subsequent submissions cannot clear a confirmed breach.
    result["unresolved_breach"] = False
    result["last_valid_test_date"] = None
    for test_day in sorted({day(t["test_date"]) for t in tests}, reverse=True):
        group = [t for t in tests if day(t["test_date"]) == test_day]
        if any(t["data_quality"] != "VALID" or not finite(t["actual_value"]) for t in group):
            continue
        if covenant.get("metric_code") == "DEBT_EBITDA" and any(float(t["actual_value"]) < 0 for t in group):
            continue
        if len({Decimal(str(t["actual_value"])) for t in group}) != 1:
            continue
        try:
            confirmed = covenant_headroom(group[0]["actual_value"], covenant["threshold_value"],
                                         covenant["threshold_direction"], covenant["warning_buffer_pct"])
        except ValueError:
            continue
        result["last_valid_test_date"] = test_day.isoformat()
        result["unresolved_breach"] = confirmed["result"] == "BREACHED"
        break
    due = day(result["next_test_date"])
    tested_on = day(result["last_valid_test_date"])
    active = result["covenant_status"] == "ACTIVE" and result["facility_status"] == "ACTIVE"
    result["in_scope"] = active
    result["overdue"] = bool(active and due and due < as_of and (not tested_on or tested_on < due))
    result["days_to_test"] = (due - as_of).days if due else None
    if not active:
        result["confirmed"] = False
    return result


def prioritize(metrics, covenants):
    fresh = [m for m in metrics if m["eligible"]]
    critical = sum(m["condition"] == "CRITICAL" for m in fresh)
    weak = sum(m["condition"] == "WEAK" for m in fresh)
    worsening = sum(m["direction"] == "DETERIORATING" for m in fresh)
    confirmed = [c for c in covenants if c["in_scope"] and c["confirmed"]]
    breached = [c for c in covenants if c["in_scope"] and
                ((c["confirmed"] and c["result"] == "BREACHED") or c.get("unresolved_breach"))]
    near = [c for c in confirmed if c["result"] == "NEAR_BREACH"]
    tight = [c for c in confirmed if c["result"] == "TIGHT"]
    issues = []
    for m in metrics:
        if not m["eligible"]:
            issues.append(f"{m['name']}: {m['freshness'].lower().replace('_', ' ')} evidence")
        elif not m["trend_assessable"]:
            issues.append(f"{m['name']}: fewer than three comparable observations")
    for c in covenants:
        if c["in_scope"] and c["freshness"] != "VALID":
            issues.append(f"{c['covenant_name']}: {c['freshness'].lower()} test evidence")
        if c["overdue"]:
            issues.append(f"{c['covenant_name']}: scheduled test overdue")
        if c["in_scope"] and not c.get("next_test_date"):
            issues.append(f"{c['covenant_name']}: next test not scheduled")
    drivers = []
    if breached:
        priority = "URGENT"
        drivers.append(f"{len(breached)} confirmed covenant breach{'es' if len(breached) != 1 else ''}")
        if worsening:
            drivers.append(f"{worsening} fresh indicators deteriorating together")
    elif critical >= 2 and worsening >= 2:
        priority = "URGENT"
        drivers.append(f"{critical} critical indicators with {worsening} deteriorating trends")
    elif near or critical or worsening >= 3:
        priority = "HIGH"
        if near:
            drivers.append(f"{len(near)} covenant(s) within 5% headroom")
        if critical:
            drivers.append(f"{critical} fresh indicator(s) at critical levels")
        if worsening >= 3:
            drivers.append(f"{worsening} indicators deteriorating together")
    elif tight or worsening >= 2 or weak:
        priority = "WATCH"
        if tight:
            drivers.append(f"{len(tight)} covenant(s) inside the warning buffer")
        if worsening >= 2:
            drivers.append(f"{worsening} indicators deteriorating together")
        if weak:
            drivers.append(f"{weak} fresh indicator(s) at weak levels")
    elif issues:
        priority = "DATA_REVIEW"
        drivers.append("Current risk cannot be cleared with the available evidence")
    else:
        priority = "ROUTINE"
        drivers.append("No escalation trigger in the available, current evidence")
    return {"priority": priority, "rank": PRIORITY_RANK[priority], "drivers": drivers,
            "credit_state": "NOT_ASSESSED" if priority == "DATA_REVIEW" else priority,
            "data_issues": issues, "fresh_metrics": len(fresh), "deteriorating_metrics": worsening,
            "critical_metrics": critical, "breached_covenants": len(breached),
            "coverage": "COMPLETE" if not issues else "PARTIAL" if fresh or confirmed else "MISSING"}


def build_monitoring(as_of=None, db=None):
    db = db or engine
    with db.connect() as conn:
        def query(sql):
            return [dict(r) for r in conn.execute(text(sql)).mappings()]
        borrowers = query("SELECT id, borrower_name, sector, loan_amount FROM borrowers ORDER BY id")
        observations = query("SELECT * FROM borrower_metric_observations ORDER BY observation_date, id")
        contracts = query("""SELECT c.id AS covenant_id, c.facility_id, c.covenant_name, c.covenant_code,
            c.metric_code, c.threshold_direction, c.threshold_value, c.warning_buffer_pct,
            c.testing_frequency, c.next_test_date, c.status AS covenant_status,
            f.borrower_id, f.facility_code, f.facility_name, f.facility_type, f.currency,
            f.status AS facility_status, f.outstanding_amount, f.sanctioned_amount
            FROM covenants c JOIN facilities f ON f.id = c.facility_id ORDER BY c.id""")
        tests = query("SELECT * FROM covenant_tests ORDER BY test_date, id")
    today = date.today()
    latest_date = max([day(o["observation_date"]) for o in observations
                       if day(o["observation_date"]) <= today] or [today])
    as_of = day(as_of) if as_of else latest_date if DEMO_MODE else today
    if as_of > today:
        raise ValueError("The observation cutoff cannot be in the future")
    obs_by = defaultdict(list)
    for row in observations:
        obs_by[(row["borrower_id"], row["metric_code"])].append(row)
    tests_by = defaultdict(list)
    for row in tests:
        tests_by[row["covenant_id"]].append(row)
    contracts_by = defaultdict(list)
    for c in contracts:
        contracts_by[c["borrower_id"]].append(assess_covenant(c, tests_by[c["covenant_id"]], as_of))
    result = []
    sectors = defaultdict(lambda: {"exposure": 0, "borrowers": 0})
    for b in borrowers:
        metrics = [assess_metric(code, obs_by[(b["id"], code)], as_of) for code in METRIC_CONFIG]
        covenants = contracts_by[b["id"]]
        assessment = prioritize(metrics, covenants)
        exposure = float(b["loan_amount"] or 0)
        result.append({"borrower_id": b["id"], "borrower_name": b["borrower_name"],
                       "sector": b["sector"] or "Unspecified", "exposure": exposure,
                       "metrics": metrics, "covenants": covenants, **assessment,
                       "suggested_due_date": (as_of + timedelta(days=REVIEW_DAYS[assessment["priority"]])).isoformat(),
                       "next_action": ("Confirm breach, check waiver documentation, and escalate to the credit reviewer."
                                       if assessment["breached_covenants"] else
                                       "Request current statements and verify missing or outdated observations."
                                       if assessment["priority"] == "DATA_REVIEW" else
                                       "Review cash conversion, payment behavior, and debt-service capacity."
                                       if assessment["priority"] != "ROUTINE" else
                                       "Continue scheduled monitoring and collect the next reporting period.")})
        sectors[b["sector"] or "Unspecified"]["exposure"] += exposure
        sectors[b["sector"] or "Unspecified"]["borrowers"] += 1
    result.sort(key=lambda b: (-b["rank"], -b["exposure"], b["borrower_id"]))
    total = sum(b["exposure"] for b in result)
    active = [c for rows in contracts_by.values() for c in rows if c["in_scope"]]
    attention = [b for b in result if b["priority"] in ("URGENT", "HIGH", "WATCH")]
    return {"as_of": as_of.isoformat(), "latest_observation": latest_date.isoformat(),
            "mode": "synthetic" if DEMO_MODE else "connected", "policy_version": POLICY_VERSION,
            "borrowers": result,
            "summary": {"borrowers": len(result), "exposure": total, "attention_count": len(attention),
                        "attention_exposure": sum(b["exposure"] for b in attention),
                        "urgent": sum(b["priority"] == "URGENT" for b in result),
                        "coverage_pct": round(sum(b["fresh_metrics"] for b in result) / (len(result) * 4) * 100, 1) if result else 0,
                        "complete_borrowers": sum(b["coverage"] == "COMPLETE" for b in result),
                        "data_exceptions": sum(bool(b["data_issues"]) for b in result),
                        "covenants": len(active), "breaches": sum(c["unresolved_breach"] for c in active),
                        "overdue_tests": sum(c["overdue"] for c in active),
                        "counts": {p: sum(b["priority"] == p for b in result) for p in REVIEW_DAYS}},
            "sectors": [{"sector": sector, **values,
                         "share_pct": round(values["exposure"] / total * 100, 1) if total else 0,
                         "over_limit": values["exposure"] > total * .25 if total else False}
                        for sector, values in sorted(sectors.items(), key=lambda item: -item[1]["exposure"])]}
