"""Decision-relevant boundaries for monitoring and persistent analyst reviews."""
import os
import sys
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("RISK_DEMO_MODE", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine
from pydantic import ValidationError
from monitoring_engine import assess_metric, assess_covenant, covenant_headroom, prioritize, build_monitoring
from case_store import initialize, load_cases, load_events, save_case, CaseConflict
from monitoring_api import CaseUpdate

CUTOFF = date(2026, 5, 31)


def observation(value=1.5, when="2026-05-31", **extra):
    return {"id": 1, "metric_value": value, "observation_date": when, "period_end": when,
            "source": "SYNTHETIC", "reporting_frequency": "MONTHLY", "data_quality": "VALID", **extra}


def contract(**extra):
    return {"covenant_id": 1, "borrower_id": 65, "covenant_name": "Minimum DSCR", "threshold_value": 1.1,
            "threshold_direction": "MINIMUM", "warning_buffer_pct": 15, "testing_frequency": "QUARTERLY",
            "next_test_date": "2026-06-30", "covenant_status": "ACTIVE", "facility_status": "ACTIVE", **extra}


def test_row(actual=1.3, when="2026-05-31", **extra):
    return {"id": 1, "test_date": when, "actual_value": actual, "source": "SYNTHETIC", "data_quality": "VALID", **extra}


class EvidenceTests(unittest.TestCase):
    def test_no_history_is_not_low_risk(self):
        metrics = [assess_metric(c, [], CUTOFF) for c in ("DSCR", "BOUNCE_RATE", "RECEIVABLE_DAYS", "DEBT_EBITDA")]
        self.assertEqual(prioritize(metrics, [])["priority"], "DATA_REVIEW")
        self.assertEqual(prioritize(metrics, [])["credit_state"], "NOT_ASSESSED")

    def test_three_distinct_observations_required(self):
        result = assess_metric("DSCR", [observation(2, "2026-04-30"), observation(1.8)], CUTOFF)
        self.assertFalse(result["trend_assessable"])
        self.assertTrue(result["eligible"])

    def test_duplicate_date_does_not_create_trend_or_zero_day_velocity(self):
        result = assess_metric("DSCR", [observation(2, "2026-04-30"), observation(1.8), observation(1.8, source="SECOND")], CUTOFF)
        self.assertEqual(result["observations"], 2)
        self.assertIsNone(result["velocity_30d"])

    def test_conflicting_sources_are_excluded(self):
        result = assess_metric("DSCR", [observation(.8), observation(1.5, source="SECOND")], CUTOFF)
        self.assertFalse(result["eligible"])
        self.assertEqual(result["freshness"], "CONFLICT")
        self.assertIsNone(result["value"])

    def test_monthly_freshness_boundary(self):
        self.assertTrue(assess_metric("DSCR", [observation(2, "2026-04-16")], CUTOFF)["eligible"])
        self.assertEqual(assess_metric("DSCR", [observation(2, "2026-04-15")], CUTOFF)["freshness"], "STALE")

    def test_quarterly_cadence_has_different_freshness(self):
        result = assess_metric("DSCR", [observation(2, "2026-03-31", reporting_frequency="QUARTERLY")], CUTOFF)
        self.assertTrue(result["eligible"])

    def test_old_period_recently_imported_remains_stale(self):
        result = assess_metric("DSCR", [observation(2, period_end="2025-12-31")], CUTOFF)
        self.assertEqual(result["freshness"], "STALE")

    def test_estimated_critical_value_is_not_a_current_credit_signal(self):
        result = assess_metric("DSCR", [observation(.4, data_quality="ESTIMATED")], CUTOFF)
        self.assertFalse(result["eligible"])
        self.assertEqual(result["condition"], "NOT_ASSESSED")

    def test_future_observation_and_period_are_not_used(self):
        rows = [observation(2), observation(.2, "2026-06-30"), observation(.3, period_end="2026-06-30")]
        result = assess_metric("DSCR", rows, CUTOFF)
        self.assertEqual(result["value"], 2)
        self.assertEqual(result["observations"], 1)

    def test_invalid_numbers_and_impossible_bounce_rates(self):
        for value in (float("nan"), float("inf"), -1, 101):
            with self.subTest(value=value):
                self.assertEqual(assess_metric("BOUNCE_RATE", [observation(value)], CUTOFF)["freshness"], "INVALID")

    def test_mixed_cadence_breaks_comparable_history(self):
        rows = [observation(2, "2026-03-31", reporting_frequency="QUARTERLY"), observation(1.9, "2026-04-30"), observation(1.8)]
        self.assertFalse(assess_metric("DSCR", rows, CUTOFF)["trend_assessable"])

    def test_large_reporting_gap_breaks_continuity(self):
        rows = [observation(2, "2025-10-31"), observation(1.9, "2026-04-30"), observation(1.8)]
        self.assertEqual(assess_metric("DSCR", rows, CUTOFF)["observations"], 2)

    def test_time_normalized_velocity_changes_with_elapsed_days(self):
        monthly = [observation(2, "2026-03-31"), observation(1.8, "2026-04-30"), observation(1.6)]
        result = assess_metric("DSCR", monthly, CUTOFF)
        self.assertTrue(result["trend_assessable"])
        self.assertEqual(result["direction"], "DETERIORATING")
        self.assertAlmostEqual(result["velocity_30d"], (1.8 - 1.6) / 1.8 * 100 * 30 / 31, places=2)


class CovenantTests(unittest.TestCase):
    def test_minimum_and_maximum_headroom(self):
        self.assertAlmostEqual(covenant_headroom(1.3, 1.1, "MINIMUM")["headroom_pct"], 18.18181818)
        self.assertAlmostEqual(covenant_headroom(3.1, 3.5, "MAXIMUM")["headroom_pct"], 11.42857142)

    def test_exact_limit_is_not_a_breach(self):
        self.assertEqual(covenant_headroom(1.1, 1.1, "MINIMUM")["result"], "NEAR_BREACH")
        self.assertEqual(covenant_headroom(3.5, 3.5, "MAXIMUM")["result"], "NEAR_BREACH")

    def test_no_rounding_away_a_small_breach(self):
        self.assertEqual(covenant_headroom(1.099999999, 1.1, "MINIMUM")["result"], "BREACHED")

    def test_zero_threshold_retains_absolute_compliance(self):
        self.assertEqual(covenant_headroom(-1, 0, "MINIMUM")["result"], "BREACHED")
        self.assertEqual(covenant_headroom(1, 0, "MINIMUM")["result"], "COMPLIANT")
        self.assertIsNone(covenant_headroom(1, 0, "MINIMUM")["headroom_pct"])

    def test_negative_debt_ebitda_requires_review_and_cannot_clear_breach(self):
        result = assess_covenant(contract(metric_code="DEBT_EBITDA", threshold_direction="MAXIMUM", threshold_value=3.5),
                                 [test_row(4, "2026-03-31"), test_row(-2)], CUTOFF)
        self.assertEqual(result["freshness"], "INVALID")
        self.assertTrue(result["unresolved_breach"])

    def test_recompute_status_not_imported_label(self):
        result = assess_covenant(contract(), [test_row(.8, test_status="HEALTHY", headroom_percentage=50)], CUTOFF)
        self.assertEqual(result["result"], "BREACHED")

    def test_waived_contract_does_not_trigger_priority(self):
        result = assess_covenant(contract(covenant_status="WAIVED"), [test_row(.8)], CUTOFF)
        self.assertFalse(result["in_scope"])
        self.assertEqual(prioritize([], [result])["breached_covenants"], 0)

    def test_stale_compliance_is_not_current_compliance(self):
        result = assess_covenant(contract(), [test_row(1.8, "2025-01-01")], CUTOFF)
        self.assertFalse(result["confirmed"])
        self.assertEqual(result["freshness"], "STALE")

    def test_confirmed_breach_survives_age_and_estimated_submission(self):
        rows = [test_row(.8, "2025-01-01"), test_row(1.8, data_quality="ESTIMATED", id=2)]
        result = assess_covenant(contract(), rows, CUTOFF)
        self.assertTrue(result["unresolved_breach"])
        self.assertEqual(prioritize([], [result])["priority"], "URGENT")

    def test_later_valid_compliance_resolves_confirmed_breach(self):
        rows = [test_row(.8, "2026-03-31"), test_row(1.8, id=2)]
        self.assertFalse(assess_covenant(contract(), rows, CUTOFF)["unresolved_breach"])

    def test_future_test_cannot_clear_breach(self):
        rows = [test_row(.8), test_row(1.8, "2026-06-30", id=2)]
        self.assertTrue(assess_covenant(contract(), rows, CUTOFF)["unresolved_breach"])

    def test_untested_and_overdue_are_explicit(self):
        result = assess_covenant(contract(next_test_date="2026-05-30"), [], CUTOFF)
        self.assertTrue(result["overdue"])
        self.assertEqual(result["result"], "UNTESTED")

    def test_valid_test_on_due_date_is_not_overdue(self):
        result = assess_covenant(contract(next_test_date="2026-05-30"), [test_row(1.8, "2026-05-30")], CUTOFF)
        self.assertFalse(result["overdue"])

    def test_estimated_test_does_not_complete_an_overdue_test(self):
        result = assess_covenant(contract(next_test_date="2026-05-30"), [test_row(1.8, "2026-05-30", data_quality="ESTIMATED")], CUTOFF)
        self.assertTrue(result["overdue"])


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.db = create_engine("sqlite:///" + self.temp.name + "/cases.sqlite3")
        initialize(self.db)
        self.values = {"expected_version": 0, "status": "IN_REVIEW", "owner": "Analyst", "actor": "William",
                       "due_date": "2026-06-01", "next_action": "Request receivable ageing", "note": "Check ageing against the reported financial statements."}

    def tearDown(self):
        self.db.dispose()
        self.temp.cleanup()

    def test_case_survives_new_database_connection(self):
        save_case(self.db, 65, self.values, {"priority": "URGENT", "as_of": "2026-05-31"})
        self.db.dispose()
        self.assertEqual(load_cases(self.db)[65]["owner"], "Analyst")
        self.assertEqual(load_events(self.db, 65)[0]["evidence"]["priority"], "URGENT")

    def test_stale_write_rejected_without_extra_event(self):
        save_case(self.db, 65, self.values, {"priority": "URGENT"})
        with self.assertRaises(CaseConflict):
            save_case(self.db, 65, self.values, {"priority": "LOW"})
        self.assertEqual(len(load_events(self.db, 65)), 1)
        self.assertEqual(load_cases(self.db)[65]["version"], 1)

    def test_update_preserves_previous_decision_and_evidence(self):
        save_case(self.db, 65, self.values, {"priority": "URGENT"})
        save_case(self.db, 65, {**self.values, "expected_version": 1, "status": "RESOLVED", "note": "Review complete; continue monitoring the active breach."}, {"priority": "URGENT"})
        history = load_events(self.db, 65)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["before"]["status"], "IN_REVIEW")
        self.assertEqual(history[1]["after"]["note"], self.values["note"])
        self.assertEqual(history[0]["evidence"]["priority"], "URGENT")

    def test_schema_requires_owner_due_date_action_and_reason(self):
        for change in ({"owner": " "}, {"due_date": None}, {"next_action": ""}, {"note": "ok"}):
            with self.subTest(change=change), self.assertRaises(ValidationError):
                CaseUpdate(**{**self.values, **change})


class PortfolioTests(unittest.TestCase):
    def test_contract_override_exposure_and_missing_data(self):
        data = build_monitoring("2026-05-31")
        by_id = {b["borrower_id"]: b for b in data["borrowers"]}
        self.assertEqual(by_id[58]["priority"], "URGENT")
        self.assertEqual(by_id[65]["priority"], "URGENT")
        self.assertEqual(by_id[64]["priority"], "DATA_REVIEW")
        self.assertAlmostEqual(data["summary"]["exposure"], 1056)
        self.assertAlmostEqual(data["summary"]["attention_exposure"], 158)
        self.assertEqual(data["summary"]["coverage_pct"], 20)

    def test_later_cutoff_flags_stale_data_without_clearing_known_breaches(self):
        data = build_monitoring("2026-10-12")
        by_id = {b["borrower_id"]: b for b in data["borrowers"]}
        self.assertEqual(data["summary"]["coverage_pct"], 0)
        self.assertEqual(by_id[47]["priority"], "DATA_REVIEW")
        self.assertEqual(by_id[65]["priority"], "URGENT")
        self.assertGreater(data["summary"]["overdue_tests"], 0)


if __name__ == "__main__":
    unittest.main()
