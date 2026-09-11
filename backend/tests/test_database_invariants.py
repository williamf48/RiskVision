import sys
import unittest
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


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


from connection import engine


class DatabaseInvariantTests(
    unittest.TestCase
):

    # =====================================================
    # HELPERS
    # =====================================================

    def assert_rejected(
        self,
        sql,
        params=None,
    ):

        with engine.connect() as conn:

            transaction = conn.begin()

            try:

                with self.assertRaises(
                    IntegrityError
                ):
                    conn.execute(
                        text(sql),
                        params or {},
                    )

            finally:
                transaction.rollback()


    # =====================================================
    # VALID CONTROL INSERT
    # =====================================================

    def test_valid_borrower_insert_succeeds(self):

        with engine.connect() as conn:

            transaction = conn.begin()

            try:

                borrower_id = conn.execute(
                    text("""
                        INSERT INTO borrowers (
                            borrower_name,
                            sector,
                            loan_amount
                        )
                        VALUES (
                            'Invariant Test Borrower',
                            'Testing',
                            1
                        )
                        RETURNING id
                    """)
                ).scalar_one()

                self.assertIsInstance(
                    borrower_id,
                    int,
                )

            finally:
                transaction.rollback()


    # =====================================================
    # BORROWERS
    # =====================================================

    def test_null_borrower_name_is_rejected(self):

        self.assert_rejected(
            """
            INSERT INTO borrowers (
                borrower_name,
                sector,
                loan_amount
            )
            VALUES (
                NULL,
                'Testing',
                1
            )
            """
        )


    def test_negative_loan_amount_is_rejected(self):

        self.assert_rejected(
            """
            INSERT INTO borrowers (
                borrower_name,
                sector,
                loan_amount
            )
            VALUES (
                'Negative Exposure Test',
                'Testing',
                -1
            )
            """
        )


    def test_duplicate_borrower_name_is_rejected(self):

        self.assert_rejected(
            """
            INSERT INTO borrowers (
                borrower_name,
                sector,
                loan_amount
            )
            VALUES (
                'Falcon Realty Ltd',
                'Testing',
                1
            )
            """
        )


    # =====================================================
    # FINANCIALS
    # =====================================================

    def test_negative_dpd_is_rejected(self):

        self.assert_rejected(
            """
            INSERT INTO borrower_financials (
                borrower_id,
                dpd,
                dscr,
                revenue_decline,
                cash_flow,
                restructured
            )
            VALUES (
                65,
                -1,
                1.5,
                0,
                'Positive',
                FALSE
            )
            """
        )


    # =====================================================
    # RISK SCORES
    # =====================================================

    def test_invalid_risk_classification_is_rejected(self):

        self.assert_rejected(
            """
            INSERT INTO risk_scores (
                borrower_id,
                score,
                classification
            )
            VALUES (
                65,
                10,
                'UNKNOWN'
            )
            """
        )


    def test_negative_risk_score_is_rejected(self):

        self.assert_rejected(
            """
            INSERT INTO risk_scores (
                borrower_id,
                score,
                classification
            )
            VALUES (
                65,
                -1,
                'Low Risk'
            )
            """
        )


    # =====================================================
    # ALERTS
    # =====================================================

    def test_invalid_alert_severity_is_rejected(self):

        self.assert_rejected(
            """
            INSERT INTO alerts (
                borrower_id,
                alert_type,
                severity
            )
            VALUES (
                65,
                'Invariant Test Alert',
                'INVALID'
            )
            """
        )


    def test_invalid_borrower_foreign_key_is_rejected(self):

        self.assert_rejected(
            """
            INSERT INTO alerts (
                borrower_id,
                alert_type,
                severity
            )
            VALUES (
                999999,
                'Foreign Key Test',
                'MEDIUM'
            )
            """
        )


    # =====================================================
    # HISTORICAL OBSERVATIONS
    # =====================================================

    def test_invalid_reporting_frequency_is_rejected(self):

        self.assert_rejected(
            """
            INSERT INTO borrower_metric_observations (
                borrower_id,
                metric_code,
                metric_value,
                observation_date,
                reporting_frequency,
                source,
                data_quality
            )
            VALUES (
                65,
                'DSCR',
                1.5,
                '2099-01-31',
                'INVALID',
                'INVARIANT_TEST',
                'VALID'
            )
            """
        )


    def test_invalid_data_quality_is_rejected(self):

        self.assert_rejected(
            """
            INSERT INTO borrower_metric_observations (
                borrower_id,
                metric_code,
                metric_value,
                observation_date,
                reporting_frequency,
                source,
                data_quality
            )
            VALUES (
                65,
                'DSCR',
                1.5,
                '2099-02-28',
                'MONTHLY',
                'INVARIANT_TEST',
                'INVALID'
            )
            """
        )


    def test_invalid_period_range_is_rejected(self):

        self.assert_rejected(
            """
            INSERT INTO borrower_metric_observations (
                borrower_id,
                metric_code,
                metric_value,
                observation_date,
                period_start,
                period_end,
                reporting_frequency,
                source,
                data_quality
            )
            VALUES (
                65,
                'DSCR',
                1.5,
                '2099-03-31',
                '2099-03-31',
                '2099-03-01',
                'MONTHLY',
                'INVARIANT_TEST',
                'VALID'
            )
            """
        )


    # =====================================================
    # FACILITIES
    # =====================================================

    def test_negative_facility_amount_is_rejected(self):

        self.assert_rejected(
            """
            INSERT INTO facilities (
                borrower_id,
                facility_code,
                facility_name,
                facility_type,
                sanctioned_amount,
                status
            )
            VALUES (
                65,
                'INV-NEGATIVE-AMOUNT',
                'Invariant Test Facility',
                'TERM_LOAN',
                -1,
                'ACTIVE'
            )
            """
        )


    # =====================================================
    # COVENANTS
    # =====================================================

    def test_negative_covenant_warning_buffer_is_rejected(self):

        with engine.connect() as conn:

            facility_id = conn.execute(
                text("""
                    SELECT id
                    FROM facilities
                    ORDER BY id
                    LIMIT 1
                """)
            ).scalar_one()


        self.assert_rejected(
            """
            INSERT INTO covenants (
                facility_id,
                covenant_code,
                covenant_name,
                metric_code,
                threshold_direction,
                threshold_value,
                warning_buffer_pct,
                testing_frequency,
                status
            )
            VALUES (
                :facility_id,
                'INV-NEGATIVE-BUFFER',
                'Invariant Test Covenant',
                'DSCR',
                'MINIMUM',
                1.0,
                -1,
                'QUARTERLY',
                'ACTIVE'
            )
            """,
            {
                "facility_id":
                    facility_id,
            },
        )


if __name__ == "__main__":

    unittest.main(
        verbosity=2
    )
