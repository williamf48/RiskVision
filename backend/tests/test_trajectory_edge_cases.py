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
    METRIC_CONFIG,
    analyze_metric,
    analyze_trajectory,
    calculate_risk_velocity,
    classify_condition,
)


# =========================================================
# TRAJECTORY ENGINE EDGE-CASE TESTS
# =========================================================

class TrajectoryEdgeCaseTests(
    unittest.TestCase
):

    # -----------------------------------------------------
    # CURRENT-CONDITION CLASSIFICATION
    # -----------------------------------------------------

    def test_none_current_value_is_insufficient_data(self):

        result = classify_condition(
            current_value=None,
            bad_direction="DOWN",
            thresholds=METRIC_CONFIG[
                "DSCR"
            ][
                "condition_thresholds"
            ],
        )

        self.assertEqual(
            result["condition"],
            "INSUFFICIENT_DATA",
        )

        self.assertIsNone(
            result[
                "condition_severity"
            ]
        )


    def test_down_direction_metric_can_be_critical(self):

        result = classify_condition(
            current_value=0.90,
            bad_direction="DOWN",
            thresholds=METRIC_CONFIG[
                "DSCR"
            ][
                "condition_thresholds"
            ],
        )

        self.assertEqual(
            result["condition"],
            "CRITICAL",
        )

        self.assertEqual(
            result[
                "condition_severity"
            ],
            3,
        )


    def test_up_direction_metric_can_be_critical(self):

        result = classify_condition(
            current_value=9.0,
            bad_direction="UP",
            thresholds=METRIC_CONFIG[
                "BOUNCE_RATE"
            ][
                "condition_thresholds"
            ],
        )

        self.assertEqual(
            result["condition"],
            "CRITICAL",
        )

        self.assertEqual(
            result[
                "condition_severity"
            ],
            3,
        )


    # -----------------------------------------------------
    # ZERO / ONE OBSERVATION
    # -----------------------------------------------------

    def test_zero_observations_return_insufficient_history(self):

        result = analyze_trajectory(
            values=[],
            dates=[],
            bad_direction="UP",
        )

        self.assertEqual(
            result["direction"],
            "INSUFFICIENT_HISTORY",
        )

        self.assertIsNone(
            result["current_value"]
        )

        self.assertIsNone(
            result["previous_value"]
        )

        self.assertEqual(
            result["persistence"],
            0,
        )

        self.assertIsNone(
            result["risk_velocity_30d"]
        )


    def test_one_observation_returns_insufficient_history(self):

        result = analyze_trajectory(
            values=[5.0],
            dates=["2026-01-31"],
            bad_direction="UP",
        )

        self.assertEqual(
            result["direction"],
            "INSUFFICIENT_HISTORY",
        )

        self.assertEqual(
            result["current_value"],
            5.0,
        )

        self.assertIsNone(
            result["previous_value"]
        )

        self.assertEqual(
            result["persistence"],
            0,
        )


    # -----------------------------------------------------
    # DIRECTION-AWARE DETERIORATION
    # -----------------------------------------------------

    def test_up_is_deteriorating_when_up_is_bad(self):

        result = analyze_trajectory(
            values=[
                2.0,
                3.0,
            ],
            dates=[
                "2026-01-01",
                "2026-01-31",
            ],
            bad_direction="UP",
        )

        self.assertEqual(
            result["direction"],
            "DETERIORATING",
        )

        self.assertEqual(
            result["absolute_change"],
            1.0,
        )

        self.assertEqual(
            result["percentage_change"],
            50.0,
        )

        self.assertEqual(
            result["days_since_previous"],
            30,
        )

        self.assertEqual(
            result["risk_velocity_30d"],
            50.0,
        )


    def test_down_is_deteriorating_when_down_is_bad(self):

        result = analyze_trajectory(
            values=[
                1.5,
                1.2,
            ],
            dates=[
                "2026-01-01",
                "2026-01-31",
            ],
            bad_direction="DOWN",
        )

        self.assertEqual(
            result["direction"],
            "DETERIORATING",
        )

        self.assertEqual(
            result["absolute_change"],
            -0.3,
        )

        self.assertEqual(
            result["percentage_change"],
            -20.0,
        )

        # Falling DSCR is converted into
        # positive risk deterioration velocity.
        self.assertEqual(
            result["risk_velocity_30d"],
            20.0,
        )


    def test_up_metric_can_improve(self):

        result = analyze_trajectory(
            values=[
                5.0,
                4.0,
            ],
            dates=[
                "2026-01-01",
                "2026-01-31",
            ],
            bad_direction="UP",
        )

        self.assertEqual(
            result["direction"],
            "IMPROVING",
        )

        self.assertEqual(
            result["risk_velocity_30d"],
            -20.0,
        )


    # -----------------------------------------------------
    # STABLE TRAJECTORY
    # -----------------------------------------------------

    def test_equal_values_are_stable(self):

        result = analyze_trajectory(
            values=[
                5.0,
                5.0,
            ],
            dates=[
                "2026-01-01",
                "2026-01-31",
            ],
            bad_direction="UP",
        )

        self.assertEqual(
            result["direction"],
            "STABLE",
        )

        self.assertEqual(
            result["absolute_change"],
            0.0,
        )

        self.assertEqual(
            result["percentage_change"],
            0.0,
        )

        self.assertEqual(
            result["risk_velocity_30d"],
            0.0,
        )

        self.assertEqual(
            result["persistence"],
            0,
        )


    # -----------------------------------------------------
    # PERSISTENCE
    # -----------------------------------------------------

    def test_persistence_counts_consecutive_deterioration(self):

        result = analyze_trajectory(
            values=[
                2.0,
                3.0,
                4.0,
                5.0,
            ],
            dates=[
                "2026-01-01",
                "2026-01-31",
                "2026-03-02",
                "2026-04-01",
            ],
            bad_direction="UP",
        )

        self.assertEqual(
            result["direction"],
            "DETERIORATING",
        )

        self.assertEqual(
            result["persistence"],
            3,
        )


    def test_persistence_resets_after_non_deteriorating_move(self):

        result = analyze_trajectory(
            values=[
                2.0,
                3.0,
                2.5,
            ],
            dates=[
                "2026-01-01",
                "2026-01-31",
                "2026-03-02",
            ],
            bad_direction="UP",
        )

        self.assertEqual(
            result["direction"],
            "IMPROVING",
        )

        self.assertEqual(
            result["persistence"],
            0,
        )


    # -----------------------------------------------------
    # ACCELERATION / DECELERATION
    # -----------------------------------------------------

    def test_deterioration_can_accelerate(self):

        result = analyze_trajectory(
            values=[
                2.0,
                3.0,
                5.0,
            ],
            dates=[
                "2026-01-01",
                "2026-01-31",
                "2026-03-02",
            ],
            bad_direction="UP",
        )

        self.assertEqual(
            result[
                "acceleration_direction"
            ],
            "ACCELERATING",
        )

        self.assertGreater(
            result[
                "velocity_change_30d"
            ],
            0,
        )


    def test_deterioration_can_decelerate(self):

        result = analyze_trajectory(
            values=[
                2.0,
                4.0,
                5.0,
            ],
            dates=[
                "2026-01-01",
                "2026-01-31",
                "2026-03-02",
            ],
            bad_direction="UP",
        )

        self.assertEqual(
            result[
                "acceleration_direction"
            ],
            "DECELERATING",
        )

        self.assertLess(
            result[
                "velocity_change_30d"
            ],
            0,
        )


    # -----------------------------------------------------
    # ZERO BASE VALUE
    # -----------------------------------------------------

    def test_zero_old_value_does_not_divide_by_zero(self):

        days, velocity = (
            calculate_risk_velocity(
                old_value=0,
                new_value=5,
                old_date="2026-01-01",
                new_date="2026-01-31",
                bad_direction="UP",
            )
        )

        self.assertEqual(
            days,
            30,
        )

        self.assertIsNone(
            velocity
        )


    def test_trajectory_with_zero_previous_value_has_no_percentage_change(self):

        result = analyze_trajectory(
            values=[
                0.0,
                2.0,
            ],
            dates=[
                "2026-01-01",
                "2026-01-31",
            ],
            bad_direction="UP",
        )

        self.assertEqual(
            result["direction"],
            "DETERIORATING",
        )

        self.assertIsNone(
            result["percentage_change"]
        )

        self.assertIsNone(
            result["risk_velocity_30d"]
        )


    # -----------------------------------------------------
    # INVALID / NON-POSITIVE TIME INTERVALS
    # -----------------------------------------------------

    def test_same_day_velocity_is_not_calculated(self):

        days, velocity = (
            calculate_risk_velocity(
                old_value=2,
                new_value=3,
                old_date="2026-01-01",
                new_date="2026-01-01",
                bad_direction="UP",
            )
        )

        self.assertIsNone(
            days
        )

        self.assertIsNone(
            velocity
        )


    def test_reverse_date_velocity_is_not_calculated(self):

        days, velocity = (
            calculate_risk_velocity(
                old_value=2,
                new_value=3,
                old_date="2026-02-01",
                new_date="2026-01-01",
                bad_direction="UP",
            )
        )

        self.assertIsNone(
            days
        )

        self.assertIsNone(
            velocity
        )


    # -----------------------------------------------------
    # INVALID METRIC CODE
    # -----------------------------------------------------

    def test_unknown_metric_code_raises_value_error(self):

        with self.assertRaises(
            ValueError
        ):

            analyze_metric(
                borrower_id=65,
                metric_code=
                    "NOT_A_REAL_METRIC",
            )


# =========================================================
# RUN DIRECTLY
# =========================================================

if __name__ == "__main__":

    unittest.main(
        verbosity=2
    )