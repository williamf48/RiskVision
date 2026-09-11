import sys
import unittest
from datetime import date
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


from trajectory_engine import (
    PRIORITY_RANK,
    analyze_borrower,
    analyze_portfolio,
    get_metric_history,
    summarize_portfolio_interventions,
)

from backtest_engine import (
    backtest_portfolio,
    get_historically_assessable_borrowers,
    replay_borrower,
)


# =========================================================
# TEMPORAL CORRECTNESS + SYSTEM INVARIANTS
# =========================================================

class TemporalInvariantTests(
    unittest.TestCase
):

    # -----------------------------------------------------
    # AS-OF DATE BEFORE ANY HISTORY
    # -----------------------------------------------------

    def test_as_of_date_before_history_is_insufficient(self):

        result = analyze_borrower(
            65,
            as_of_date="2025-01-01",
        )

        self.assertEqual(
            result["metrics_analyzed"],
            0,
        )

        self.assertEqual(
            result["intervention_priority"],
            "INSUFFICIENT_DATA",
        )


    # -----------------------------------------------------
    # FUTURE CUTOFF MUST MATCH CURRENT ANALYSIS
    # -----------------------------------------------------

    def test_future_as_of_date_matches_current_state(self):

        current = analyze_borrower(
            65
        )

        future = analyze_borrower(
            65,
            as_of_date="2099-12-31",
        )


        comparable_fields = [
            "intervention_priority",
            "priority_rank",
            "metrics_analyzed",
            "deteriorating_signals",
            "improving_signals",
            "stable_signals",
            "persistent_deterioration_signals",
            "accelerating_deterioration_signals",
            "critical_condition_signals",
            "convergence_percentage",
        ]


        for field in comparable_fields:

            self.assertEqual(
                current[field],
                future[field],
                msg=(
                    f"Mismatch for field: "
                    f"{field}"
                ),
            )


    # -----------------------------------------------------
    # DATABASE-LEVEL LOOK-AHEAD PROTECTION
    # -----------------------------------------------------

    def test_metric_history_respects_cutoff_date(self):

        cutoff = date(
            2026,
            2,
            28,
        )


        df = get_metric_history(
            borrower_id=65,
            metric_code="DSCR",
            as_of_date=cutoff,
        )


        for observation_date in (
            df["observation_date"]
            .tolist()
        ):

            self.assertLessEqual(
                observation_date,
                cutoff,
            )


    # -----------------------------------------------------
    # HISTORY CANNOT SHRINK AS TIME MOVES FORWARD
    # -----------------------------------------------------

    def test_metric_history_is_monotonic_over_time(self):

        dates = [
            "2025-09-30",
            "2025-12-31",
            "2026-03-31",
            "2026-05-31",
        ]


        counts = []


        for cutoff in dates:

            df = get_metric_history(
                borrower_id=65,
                metric_code="DSCR",
                as_of_date=cutoff,
            )

            counts.append(
                len(df)
            )


        self.assertEqual(
            counts,
            sorted(counts),
        )


    # -----------------------------------------------------
    # REPLAY DATES MUST BE CHRONOLOGICAL
    # -----------------------------------------------------

    def test_replay_timeline_is_sorted(self):

        replay = replay_borrower(
            65
        )


        dates = [

            point["as_of_date"]

            for point
            in replay["timeline"]
        ]


        self.assertEqual(
            dates,
            sorted(dates),
        )


    # -----------------------------------------------------
    # PRIORITY VALUES MUST ALWAYS BE VALID
    # -----------------------------------------------------

    def test_replay_priorities_are_valid(self):

        replay = replay_borrower(
            65
        )


        valid_priorities = set(
            PRIORITY_RANK.keys()
        )


        for point in replay["timeline"]:

            self.assertIn(
                point[
                    "intervention_priority"
                ],
                valid_priorities,
            )


    # -----------------------------------------------------
    # CONVERGENCE MUST ALWAYS BE BETWEEN 0 AND 100
    # -----------------------------------------------------

    def test_convergence_percentage_is_bounded(self):

        borrowers = (
            get_historically_assessable_borrowers()
        )


        for borrower in borrowers:

            result = analyze_borrower(
                int(
                    borrower["id"]
                )
            )


            self.assertGreaterEqual(
                result[
                    "convergence_percentage"
                ],
                0.0,
            )


            self.assertLessEqual(
                result[
                    "convergence_percentage"
                ],
                100.0,
            )


    # -----------------------------------------------------
    # SIGNAL DIRECTIONS MUST PARTITION ANALYZED METRICS
    # -----------------------------------------------------

    def test_direction_counts_match_metrics_analyzed(self):

        borrowers = (
            get_historically_assessable_borrowers()
        )


        for borrower in borrowers:

            result = analyze_borrower(
                int(
                    borrower["id"]
                )
            )


            direction_total = (

                result[
                    "deteriorating_signals"
                ]

                +

                result[
                    "improving_signals"
                ]

                +

                result[
                    "stable_signals"
                ]
            )


            self.assertEqual(
                direction_total,
                result[
                    "metrics_analyzed"
                ],
                msg=(
                    f"Direction invariant failed "
                    f"for borrower "
                    f"{borrower['id']}"
                ),
            )


    # -----------------------------------------------------
    # CONDITION COUNTS MUST PARTITION ANALYZED METRICS
    # -----------------------------------------------------

    def test_condition_counts_match_metrics_analyzed(self):

        borrowers = (
            get_historically_assessable_borrowers()
        )


        for borrower in borrowers:

            result = analyze_borrower(
                int(
                    borrower["id"]
                )
            )


            condition_total = (

                result[
                    "critical_condition_signals"
                ]

                +

                result[
                    "weak_condition_signals"
                ]

                +

                result[
                    "watch_condition_signals"
                ]

                +

                result[
                    "healthy_condition_signals"
                ]
            )


            self.assertEqual(
                condition_total,
                result[
                    "metrics_analyzed"
                ],
                msg=(
                    f"Condition invariant failed "
                    f"for borrower "
                    f"{borrower['id']}"
                ),
            )


    # -----------------------------------------------------
    # CONVERGENCE FORMULA MUST BE INTERNALLY CONSISTENT
    # -----------------------------------------------------

    def test_convergence_matches_signal_ratio(self):

        borrowers = (
            get_historically_assessable_borrowers()
        )


        for borrower in borrowers:

            result = analyze_borrower(
                int(
                    borrower["id"]
                )
            )


            metrics_analyzed = (
                result[
                    "metrics_analyzed"
                ]
            )


            if metrics_analyzed == 0:
                continue


            expected = round(

                100
                *
                result[
                    "deteriorating_signals"
                ]
                /
                metrics_analyzed,

                2,
            )


            self.assertEqual(
                result[
                    "convergence_percentage"
                ],
                expected,
            )


    # -----------------------------------------------------
    # PORTFOLIO PRIORITY COUNTS MUST SUM TO TOTAL
    # -----------------------------------------------------

    def test_portfolio_priority_counts_sum_to_total(self):

        summary = (
            summarize_portfolio_interventions()
        )


        classified = (

            summary["urgent"]

            +

            summary["high"]

            +

            summary["medium"]

            +

            summary["low"]

            +

            summary["insufficient_data"]
        )


        self.assertEqual(
            classified,
            summary[
                "total_borrowers"
            ],
        )


    # -----------------------------------------------------
    # ACTIONABLE COUNT MUST MATCH URGENT + HIGH + MEDIUM
    # -----------------------------------------------------

    def test_actionable_count_is_consistent(self):

        summary = (
            summarize_portfolio_interventions()
        )


        expected_actionable = (

            summary["urgent"]

            +

            summary["high"]

            +

            summary["medium"]
        )


        self.assertEqual(
            summary[
                "actionable_borrowers"
            ],
            expected_actionable,
        )


    # -----------------------------------------------------
    # PORTFOLIO RANKS MUST BE CONTIGUOUS
    # -----------------------------------------------------

    def test_portfolio_ranks_are_contiguous(self):

        portfolio = (
            analyze_portfolio()
        )


        ranks = [

            borrower[
                "portfolio_rank"
            ]

            for borrower
            in portfolio
        ]


        self.assertEqual(
            ranks,
            list(
                range(
                    1,
                    len(portfolio) + 1,
                )
            ),
        )


    # -----------------------------------------------------
    # BACKTEST CONFUSION MATRIX MUST COVER ALL BORROWERS
    # -----------------------------------------------------

    def test_backtest_matrix_covers_all_assessable_borrowers(self):

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


    # -----------------------------------------------------
    # LABELLED EVENTS MUST EQUAL TP + FN
    # -----------------------------------------------------

    def test_labelled_events_match_positive_outcomes(self):

        result = (
            backtest_portfolio()
        )


        matrix = (
            result[
                "confusion_matrix"
            ]
        )


        positive_outcomes = (

            matrix[
                "true_positive"
            ]

            +

            matrix[
                "false_negative"
            ]
        )


        self.assertEqual(
            positive_outcomes,
            result[
                "labelled_stress_events"
            ],
        )


    # -----------------------------------------------------
    # LEAD TIME MUST NEVER BE NEGATIVE FOR DETECTED EVENTS
    # -----------------------------------------------------

    def test_detected_event_lead_times_are_nonnegative(self):

        result = (
            backtest_portfolio()
        )


        for borrower in (
            result[
                "borrowers"
            ]
        ):

            lead_time = (
                borrower[
                    "lead_time_days"
                ]
            )


            if lead_time is None:
                continue


            self.assertGreaterEqual(
                lead_time,
                0,
                msg=(
                    f"Negative lead time for "
                    f"{borrower['borrower_name']}"
                ),
            )


# =========================================================
# RUN DIRECTLY
# =========================================================

if __name__ == "__main__":

    unittest.main(
        verbosity=2
    )