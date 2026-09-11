import sys
import unittest
from pathlib import Path


# =========================================================
# ALLOW TESTS TO IMPORT BACKEND MODULES
# =========================================================

BACKEND_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

sys.path.insert(
    0,
    str(BACKEND_DIR),
)


from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


# =========================================================
# API INTEGRATION TESTS
# =========================================================

class RiskVisionAPITests(
    unittest.TestCase
):

    # -----------------------------------------------------
    # ROOT / HEALTH
    # -----------------------------------------------------

    def test_root_endpoint(self):

        response = client.get("/")

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["message"],
            "RiskVision API Running",
        )

        self.assertIn(
            "version",
            payload,
        )


    # -----------------------------------------------------
    # BORROWER DIRECTORY
    # -----------------------------------------------------

    def test_borrowers_endpoint_returns_list(self):

        response = client.get(
            "/borrowers"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertIsInstance(
            payload,
            list,
        )

        self.assertEqual(
            len(payload),
            25,
        )

        self.assertGreater(
            len(payload),
            0,
        )

        borrower = payload[0]

        required_fields = {
            "id",
            "borrower_name",
            "sector",
            "loan_amount",
            "created_at",
        }

        self.assertTrue(
            required_fields
            .issubset(
                borrower.keys()
            )
        )


    # -----------------------------------------------------
    # SINGLE BORROWER
    # -----------------------------------------------------

    def test_known_borrower_endpoint(self):

        response = client.get(
            "/borrowers/65"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["borrower_id"],
            65,
        )

        self.assertEqual(
            payload["borrower_name"],
            "Falcon Realty Ltd",
        )

        self.assertIn(
            "alerts",
            payload,
        )

        self.assertIsInstance(
            payload["alerts"],
            list,
        )


    def test_unknown_borrower_returns_404(self):

        response = client.get(
            "/borrowers/999999"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        payload = response.json()

        self.assertIn(
            "detail",
            payload,
        )


    # -----------------------------------------------------
    # DETERIORATION
    # -----------------------------------------------------

    def test_borrower_deterioration_endpoint(self):

        response = client.get(
            "/borrowers/65/deterioration"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        required_fields = {
            "borrower_id",
            "borrower_name",
            "intervention_priority",
            "metrics_analyzed",
            "deteriorating_signals",
            "convergence_percentage",
            "metric_results",
        }

        self.assertTrue(
            required_fields
            .issubset(
                payload.keys()
            )
        )

        self.assertEqual(
            payload[
                "intervention_priority"
            ],
            "URGENT",
        )

        self.assertEqual(
            payload[
                "metrics_analyzed"
            ],
            4,
        )


    def test_unknown_deterioration_borrower_returns_404(self):

        response = client.get(
            "/borrowers/999999/deterioration"
        )

        self.assertEqual(
            response.status_code,
            404,
        )


    # -----------------------------------------------------
    # HISTORY
    # -----------------------------------------------------

    def test_borrower_history_endpoint(self):

        response = client.get(
            "/borrowers/65/history"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["borrower_id"],
            65,
        )

        self.assertGreater(
            payload["metric_count"],
            0,
        )

        self.assertGreater(
            payload["observation_count"],
            0,
        )

        self.assertIsInstance(
            payload["metrics"],
            dict,
        )

        self.assertIn(
            "DSCR",
            payload["metrics"],
        )


    def test_unknown_history_borrower_returns_404(self):

        response = client.get(
            "/borrowers/999999/history"
        )

        self.assertEqual(
            response.status_code,
            404,
        )


    # -----------------------------------------------------
    # COVENANTS
    # -----------------------------------------------------

    def test_borrower_covenants_endpoint(self):

        response = client.get(
            "/borrowers/65/covenants"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["borrower_id"],
            65,
        )

        self.assertIn(
            "covenant_pressure_status",
            payload,
        )

        self.assertIn(
            "covenants",
            payload,
        )

        self.assertIsInstance(
            payload["covenants"],
            list,
        )


    def test_unknown_covenant_borrower_returns_404(self):

        response = client.get(
            "/borrowers/999999/covenants"
        )

        self.assertEqual(
            response.status_code,
            404,
        )


    # -----------------------------------------------------
    # INTERVENTION WATCHLIST
    # -----------------------------------------------------

    def test_intervention_watchlist_endpoint(self):

        response = client.get(
            "/intervention_watchlist"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertIsInstance(
            payload,
            list,
        )

        self.assertEqual(
            len(payload),
            25,
        )

        ranks = [
            borrower[
                "portfolio_rank"
            ]
            for borrower
            in payload
        ]

        self.assertEqual(
            ranks,
            list(
                range(
                    1,
                    len(payload) + 1,
                )
            ),
        )


    # -----------------------------------------------------
    # INTERVENTION SUMMARY
    # -----------------------------------------------------

    def test_intervention_summary_endpoint(self):

        response = client.get(
            "/intervention_summary"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        required_fields = {
            "total_borrowers",
            "urgent",
            "high",
            "medium",
            "low",
            "insufficient_data",
            "actionable_borrowers",
        }

        self.assertTrue(
            required_fields
            .issubset(
                payload.keys()
            )
        )

        classified = (
            payload["urgent"]
            + payload["high"]
            + payload["medium"]
            + payload["low"]
            + payload[
                "insufficient_data"
            ]
        )

        self.assertEqual(
            classified,
            payload[
                "total_borrowers"
            ],
        )


    # -----------------------------------------------------
    # COVENANT SUMMARY
    # -----------------------------------------------------

    def test_covenant_summary_endpoint(self):

        response = client.get(
            "/covenant_summary"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload[
                "borrowers_with_covenants"
            ],
            6,
        )

        self.assertEqual(
            payload[
                "total_covenants"
            ],
            12,
        )

        self.assertIn(
            "borrowers_under_covenant_pressure",
            payload,
        )


    # -----------------------------------------------------
    # PORTFOLIO SUMMARY
    # -----------------------------------------------------

    def test_portfolio_summary_endpoint(self):

        response = client.get(
            "/portfolio_summary"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        required_fields = {
            "total_borrowers",
            "total_exposure",
            "high_risk",
            "watchlist",
            "low_risk",
            "total_alerts",
            "high_severity_alerts",
        }

        self.assertTrue(
            required_fields
            .issubset(
                payload.keys()
            )
        )

        self.assertEqual(
            payload["total_borrowers"],
            25,
        )

        self.assertAlmostEqual(
            payload["total_exposure"],
            1056.0,
            places=2,
        )


    # -----------------------------------------------------
    # PORTFOLIO ANALYTICS
    # -----------------------------------------------------

    def test_portfolio_analytics_endpoint(self):

        response = client.get(
            "/portfolio_analytics"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertIn(
            "portfolio_summary",
            payload,
        )

        summary = payload[
            "portfolio_summary"
        ]

        self.assertEqual(
            summary[
                "total_borrowers"
            ],
            25,
        )

        self.assertEqual(
            summary[
                "historically_assessable_borrowers"
            ],
            5,
        )

        self.assertGreaterEqual(
            summary[
                "borrower_exposure_hhi"
            ],
            0,
        )

        self.assertGreaterEqual(
            summary[
                "sector_exposure_hhi"
            ],
            0,
        )


    # -----------------------------------------------------
    # ALERTS
    # -----------------------------------------------------

    def test_alerts_endpoint(self):

        response = client.get(
            "/alerts"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertIsInstance(
            payload,
            list,
        )

        self.assertEqual(
            len(payload),
            46,
        )

        self.assertGreater(
            len(payload),
            0,
        )

        alert = payload[0]

        required_fields = {
            "alert_id",
            "borrower_id",
            "borrower_name",
            "alert_type",
            "severity",
            "created_at",
        }

        self.assertTrue(
            required_fields
            .issubset(
                alert.keys()
            )
        )


    # -----------------------------------------------------
    # HISTORICAL REPLAY
    # -----------------------------------------------------

    def test_replay_endpoint(self):

        response = client.get(
            "/borrowers/65/replay"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["borrower_id"],
            65,
        )

        self.assertGreater(
            payload["replay_points"],
            0,
        )

        timeline = payload[
            "timeline"
        ]

        self.assertIsInstance(
            timeline,
            list,
        )

        dates = [
            point["as_of_date"]
            for point
            in timeline
        ]

        self.assertEqual(
            dates,
            sorted(dates),
        )


    def test_unknown_replay_borrower_returns_404(self):

        response = client.get(
            "/borrowers/999999/replay"
        )

        self.assertEqual(
            response.status_code,
            404,
        )


    # -----------------------------------------------------
    # BORROWER BACKTEST
    # -----------------------------------------------------

    def test_borrower_backtest_endpoint(self):

        response = client.get(
            "/borrowers/65/backtest"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["borrower_id"],
            65,
        )

        self.assertTrue(
            payload[
                "stress_event_present"
            ]
        )

        self.assertEqual(
            payload[
                "maximum_priority"
            ],
            "URGENT",
        )

        self.assertIsNotNone(
            payload[
                "first_alert_date"
            ]
        )

        self.assertGreater(
            payload[
                "lead_time_days"
            ],
            0,
        )


    def test_unknown_backtest_borrower_returns_404(self):

        response = client.get(
            "/borrowers/999999/backtest"
        )

        self.assertEqual(
            response.status_code,
            404,
        )


    # -----------------------------------------------------
    # PORTFOLIO BACKTEST
    # -----------------------------------------------------

    def test_backtest_summary_endpoint(self):

        response = client.get(
            "/backtest_summary"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        required_fields = {
            "alert_threshold",
            "historically_assessable_borrowers",
            "labelled_stress_events",
            "confusion_matrix",
            "precision",
            "recall",
            "specificity",
            "borrowers",
        }

        self.assertTrue(
            required_fields
            .issubset(
                payload.keys()
            )
        )

        matrix = payload[
            "confusion_matrix"
        ]

        classified = (
            matrix["true_positive"]
            + matrix["false_positive"]
            + matrix["true_negative"]
            + matrix["false_negative"]
        )

        self.assertEqual(
            classified,
            payload[
                "historically_assessable_borrowers"
            ],
        )

        self.assertIsInstance(
            payload["borrowers"],
            list,
        )


# =========================================================
# RUN DIRECTLY
# =========================================================

if __name__ == "__main__":

    unittest.main(
        verbosity=2
    )