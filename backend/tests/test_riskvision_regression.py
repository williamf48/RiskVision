import sys
import unittest
from pathlib import Path


# =========================================================
# ALLOW TESTS DIRECTORY TO IMPORT BACKEND MODULES
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


from trajectory_engine import (
    analyze_borrower,
    summarize_portfolio_interventions,
)

from covenant_engine import (
    analyze_borrower_covenants,
    summarize_portfolio_covenants,
)

from portfolio_analytics import (
    analyze_portfolio_concentration,
)

from backtest_engine import (
    backtest_borrower,
    backtest_portfolio,
)


# =========================================================
# REGRESSION TEST SUITE
# =========================================================

class RiskVisionRegressionTests(
    unittest.TestCase
):

    # -----------------------------------------------------
    # CURRENT TRAJECTORY
    # -----------------------------------------------------

    def test_falcon_current_state(self):

        result = analyze_borrower(
            65
        )

        self.assertEqual(
            result[
                "intervention_priority"
            ],
            "URGENT",
        )

        self.assertEqual(
            result[
                "deteriorating_signals"
            ],
            4,
        )

        self.assertEqual(
            result[
                "metrics_analyzed"
            ],
            4,
        )

        self.assertEqual(
            result[
                "convergence_percentage"
            ],
            100.0,
        )


    # -----------------------------------------------------
    # POINT-IN-TIME REPLAY
    # -----------------------------------------------------

    def test_falcon_historical_replay(self):

        result = analyze_borrower(
            65,
            as_of_date="2026-02-28",
        )

        self.assertEqual(
            result[
                "as_of_date"
            ],
            "2026-02-28",
        )

        self.assertEqual(
            result[
                "intervention_priority"
            ],
            "HIGH",
        )

        self.assertEqual(
            result[
                "deteriorating_signals"
            ],
            3,
        )

        self.assertEqual(
            result[
                "metrics_analyzed"
            ],
            3,
        )


    # -----------------------------------------------------
    # NO FUTURE DATA LEAKAGE
    # -----------------------------------------------------

    def test_replay_has_less_or_equal_history_than_current(self):

        historical = analyze_borrower(
            65,
            as_of_date="2026-02-28",
        )

        current = analyze_borrower(
            65
        )


        historical_observations = sum(
            metric[
                "observations"
            ]
            for metric
            in historical[
                "metric_results"
            ]
        )


        current_observations = sum(
            metric[
                "observations"
            ]
            for metric
            in current[
                "metric_results"
            ]
        )


        self.assertLessEqual(
            historical_observations,
            current_observations,
        )


    # -----------------------------------------------------
    # INSUFFICIENT TRAJECTORY DATA
    # -----------------------------------------------------

    def test_orion_has_no_false_trajectory_priority(self):

        result = analyze_borrower(
            64
        )

        self.assertEqual(
            result[
                "intervention_priority"
            ],
            "INSUFFICIENT_DATA",
        )

        self.assertEqual(
            result[
                "metrics_analyzed"
            ],
            0,
        )


    # -----------------------------------------------------
    # PORTFOLIO INTERVENTION COUNTS
    # -----------------------------------------------------

    def test_intervention_summary(self):

        result = (
            summarize_portfolio_interventions()
        )

        self.assertEqual(
            result[
                "total_borrowers"
            ],
            25,
        )

        self.assertEqual(
            result[
                "urgent"
            ],
            1,
        )

        self.assertEqual(
            result[
                "high"
            ],
            1,
        )

        self.assertEqual(
            result[
                "medium"
            ],
            2,
        )

        self.assertEqual(
            result[
                "low"
            ],
            1,
        )

        self.assertEqual(
            result[
                "insufficient_data"
            ],
            20,
        )

        self.assertEqual(
            result[
                "actionable_borrowers"
            ],
            4,
        )


    # -----------------------------------------------------
    # COVENANT INSUFFICIENT DATA
    # -----------------------------------------------------

    def test_orion_covenants_remain_insufficient(self):

        result = (
            analyze_borrower_covenants(
                64
            )
        )

        self.assertEqual(
            result[
                "covenant_pressure_status"
            ],
            "INSUFFICIENT_DATA",
        )

        self.assertGreater(
            result[
                "untested_covenants"
            ],
            0,
        )


    # -----------------------------------------------------
    # COVENANT SUMMARY
    # -----------------------------------------------------

    def test_covenant_summary(self):

        result = (
            summarize_portfolio_covenants()
        )

        self.assertEqual(
            result[
                "borrowers_with_covenants"
            ],
            6,
        )

        self.assertEqual(
            result[
                "borrowers_breached"
            ],
            2,
        )

        self.assertEqual(
            result[
                "borrowers_under_covenant_pressure"
            ],
            3,
        )

        self.assertEqual(
            result[
                "total_covenants"
            ],
            12,
        )


    # -----------------------------------------------------
    # PORTFOLIO ANALYTICS
    # -----------------------------------------------------

    def test_portfolio_analytics(self):

        result = (
            analyze_portfolio_concentration()
        )

        summary = (
            result[
                "portfolio_summary"
            ]
        )

        self.assertEqual(
            summary[
                "total_borrowers"
            ],
            25,
        )

        self.assertAlmostEqual(
            summary[
                "total_exposure"
            ],
            1056.0,
            places=2,
        )

        self.assertEqual(
            summary[
                "historically_assessable_borrowers"
            ],
            5,
        )

        self.assertAlmostEqual(
            summary[
                "history_coverage_percentage"
            ],
            20.0,
            places=2,
        )

        self.assertAlmostEqual(
            summary[
                "actionable_exposure"
            ],
            180.0,
            places=2,
        )


    # -----------------------------------------------------
    # FALCON BACKTEST
    # -----------------------------------------------------

    def test_falcon_backtest(self):

        result = backtest_borrower(
            65
        )

        self.assertTrue(
            result[
                "stress_event_present"
            ]
        )

        self.assertEqual(
            result[
                "maximum_priority"
            ],
            "URGENT",
        )

        self.assertIsNotNone(
            result[
                "first_alert_date"
            ]
        )

        self.assertIsNotNone(
            result[
                "lead_time_days"
            ]
        )

        self.assertGreater(
            result[
                "lead_time_days"
            ],
            0,
        )


    # -----------------------------------------------------
    # PORTFOLIO BACKTEST INTERNAL CONSISTENCY
    # -----------------------------------------------------

    def test_backtest_confusion_matrix_is_consistent(self):

        result = (
            backtest_portfolio()
        )

        matrix = (
            result[
                "confusion_matrix"
            ]
        )

        classified = (
            matrix[
                "true_positive"
            ]
            +
            matrix[
                "false_positive"
            ]
            +
            matrix[
                "true_negative"
            ]
            +
            matrix[
                "false_negative"
            ]
        )


        self.assertEqual(
            classified,
            result[
                "historically_assessable_borrowers"
            ],
        )


# =========================================================
# RUN TESTS
# =========================================================

if __name__ == "__main__":

    unittest.main(
        verbosity=2
    )