import sys
from pathlib import Path

from sqlalchemy import text


# =========================================================
# ALLOW SEED TO IMPORT BACKEND MODULES
# =========================================================

BACKEND_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

if str(BACKEND_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(BACKEND_DIR),
    )


from connection import engine

from covenant_engine import (
    calculate_headroom,
    classify_headroom,
)


# =========================================================
# DEVELOPMENT BORROWERS
# =========================================================

TARGET_BORROWERS = [

    47,  # Alpha Manufacturing
    48,  # Beta Logistics
    55,  # Nova Energy
    58,  # Crest Realty
    64,  # Orion Power Projects
    65,  # Falcon Realty

]


# =========================================================
# COVENANT DEFINITIONS
# =========================================================

COVENANT_DEFINITIONS = [

    {
        "covenant_code":
            "DSCR_MIN",

        "covenant_name":
            "Minimum DSCR",

        "metric_code":
            "DSCR",

        "threshold_direction":
            "MINIMUM",

        "threshold_value":
            1.10,

        "warning_buffer_pct":
            15.0,

        "testing_frequency":
            "QUARTERLY",
    },

    {
        "covenant_code":
            "DEBT_EBITDA_MAX",

        "covenant_name":
            "Maximum Debt / EBITDA",

        "metric_code":
            "DEBT_EBITDA",

        "threshold_direction":
            "MAXIMUM",

        "threshold_value":
            3.50,

        "warning_buffer_pct":
            15.0,

        "testing_frequency":
            "QUARTERLY",
    },

]


# =========================================================
# SEED
# =========================================================

def seed():

    with engine.begin() as conn:

        for borrower_id in TARGET_BORROWERS:

            borrower = conn.execute(
                text("""
                    SELECT
                        id,
                        borrower_name,
                        loan_amount

                    FROM borrowers

                    WHERE id = :borrower_id
                """),
                {
                    "borrower_id":
                        borrower_id
                },
            ).mappings().one_or_none()


            if borrower is None:

                print(
                    f"Borrower {borrower_id} not found. Skipping."
                )

                continue


            loan_amount = float(
                borrower[
                    "loan_amount"
                ]
                or 0
            )


            outstanding_amount = round(
                loan_amount * 0.85,
                2,
            )


            # =============================================
            # FACILITY
            # =============================================

            facility_code = (
                f"TL-{borrower_id}-01"
            )


            facility = conn.execute(
                text("""
                    INSERT INTO facilities (

                        borrower_id,
                        facility_code,
                        facility_name,
                        facility_type,
                        sanctioned_amount,
                        outstanding_amount,
                        currency,
                        interest_rate,
                        maturity_date,
                        security_type,
                        status

                    )

                    VALUES (

                        :borrower_id,
                        :facility_code,
                        :facility_name,
                        'TERM_LOAN',
                        :sanctioned_amount,
                        :outstanding_amount,
                        'INR',
                        11.50,
                        '2029-03-31',
                        'SECURED',
                        'ACTIVE'

                    )

                    ON CONFLICT (
                        borrower_id,
                        facility_code
                    )

                    DO UPDATE SET

                        facility_name =
                            EXCLUDED.facility_name,

                        sanctioned_amount =
                            EXCLUDED.sanctioned_amount,

                        outstanding_amount =
                            EXCLUDED.outstanding_amount,

                        updated_at =
                            CURRENT_TIMESTAMP

                    RETURNING id
                """),
                {
                    "borrower_id":
                        borrower_id,

                    "facility_code":
                        facility_code,

                    "facility_name":
                        (
                            f"{borrower['borrower_name']} "
                            f"Term Loan"
                        ),

                    "sanctioned_amount":
                        loan_amount,

                    "outstanding_amount":
                        outstanding_amount,
                },
            ).scalar_one()


            # =============================================
            # COVENANTS
            # =============================================

            for definition in (
                COVENANT_DEFINITIONS
            ):

                covenant_id = conn.execute(
                    text("""
                        INSERT INTO covenants (

                            facility_id,
                            covenant_code,
                            covenant_name,
                            metric_code,
                            threshold_direction,
                            threshold_value,
                            warning_buffer_pct,
                            testing_frequency,
                            next_test_date,
                            status

                        )

                        VALUES (

                            :facility_id,
                            :covenant_code,
                            :covenant_name,
                            :metric_code,
                            :threshold_direction,
                            :threshold_value,
                            :warning_buffer_pct,
                            :testing_frequency,
                            '2026-06-30',
                            'ACTIVE'

                        )

                        ON CONFLICT (
                            facility_id,
                            covenant_code
                        )

                        DO UPDATE SET

                            covenant_name =
                                EXCLUDED.covenant_name,

                            metric_code =
                                EXCLUDED.metric_code,

                            threshold_direction =
                                EXCLUDED.threshold_direction,

                            threshold_value =
                                EXCLUDED.threshold_value,

                            warning_buffer_pct =
                                EXCLUDED.warning_buffer_pct,

                            testing_frequency =
                                EXCLUDED.testing_frequency,

                            next_test_date =
                                EXCLUDED.next_test_date,

                            updated_at =
                                CURRENT_TIMESTAMP

                        RETURNING id
                    """),
                    {
                        "facility_id":
                            facility,

                        **definition,
                    },
                ).scalar_one()


                # =========================================
                # HISTORICAL OBSERVATIONS
                # =========================================

                observations = conn.execute(
                    text("""
                        SELECT
                            metric_value,
                            observation_date,
                            data_quality

                        FROM borrower_metric_observations

                        WHERE
                            borrower_id = :borrower_id

                            AND metric_code = :metric_code

                        ORDER BY
                            observation_date
                    """),
                    {
                        "borrower_id":
                            borrower_id,

                        "metric_code":
                            definition[
                                "metric_code"
                            ],
                    },
                ).mappings().all()


                for observation in observations:

                    actual_value = float(
                        observation[
                            "metric_value"
                        ]
                    )


                    (
                        headroom_absolute,
                        headroom_percentage,
                    ) = calculate_headroom(

                        actual_value,

                        definition[
                            "threshold_value"
                        ],

                        definition[
                            "threshold_direction"
                        ],

                    )


                    test_status = (
                        classify_headroom(

                            headroom_percentage,

                            definition[
                                "warning_buffer_pct"
                            ],

                        )
                    )


                    conn.execute(
                        text("""
                            INSERT INTO covenant_tests (

                                covenant_id,
                                test_date,
                                actual_value,
                                headroom_absolute,
                                headroom_percentage,
                                test_status,
                                source,
                                data_quality

                            )

                            VALUES (

                                :covenant_id,
                                :test_date,
                                :actual_value,
                                :headroom_absolute,
                                :headroom_percentage,
                                :test_status,
                                'SYNTHETIC_COVENANT_TEST',
                                :data_quality

                            )

                            ON CONFLICT (
                                covenant_id,
                                test_date,
                                source
                            )

                            DO UPDATE SET

                                actual_value =
                                    EXCLUDED.actual_value,

                                headroom_absolute =
                                    EXCLUDED.headroom_absolute,

                                headroom_percentage =
                                    EXCLUDED.headroom_percentage,

                                test_status =
                                    EXCLUDED.test_status,

                                data_quality =
                                    EXCLUDED.data_quality
                        """),
                        {
                            "covenant_id":
                                covenant_id,

                            "test_date":
                                observation[
                                    "observation_date"
                                ],

                            "actual_value":
                                actual_value,

                            "headroom_absolute":
                                headroom_absolute,

                            "headroom_percentage":
                                headroom_percentage,

                            "test_status":
                                test_status,

                            "data_quality":
                                observation[
                                    "data_quality"
                                ],
                        },
                    )


            print(
                f"{borrower['borrower_name']}: "
                f"facility + covenants ready."
            )


    print(
        "\nFacility and covenant synthetic data ready."
    )


if __name__ == "__main__":

    seed()
