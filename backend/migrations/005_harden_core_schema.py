import sys
from pathlib import Path

from sqlalchemy import text


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


# =========================================================
# HELPERS
# =========================================================

def constraint_exists(
    connection,
    constraint_name,
):
    return connection.execute(
        text("""
            SELECT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = :constraint_name
            )
        """),
        {
            "constraint_name":
                constraint_name,
        },
    ).scalar_one()


# =========================================================
# MIGRATION
# =========================================================

def run_migration():

    with engine.begin() as conn:

        # =================================================
        # REQUIRED CORE FIELDS
        # =================================================

        not_null_statements = [

            """
            ALTER TABLE borrowers
            ALTER COLUMN borrower_name
            SET NOT NULL
            """,

            """
            ALTER TABLE borrowers
            ALTER COLUMN sector
            SET NOT NULL
            """,

            """
            ALTER TABLE borrowers
            ALTER COLUMN loan_amount
            SET NOT NULL
            """,

            """
            ALTER TABLE borrower_financials
            ALTER COLUMN borrower_id
            SET NOT NULL
            """,

            """
            ALTER TABLE borrower_financials
            ALTER COLUMN dpd
            SET NOT NULL
            """,

            """
            ALTER TABLE borrower_financials
            ALTER COLUMN dscr
            SET NOT NULL
            """,

            """
            ALTER TABLE borrower_financials
            ALTER COLUMN revenue_decline
            SET NOT NULL
            """,

            """
            ALTER TABLE borrower_financials
            ALTER COLUMN cash_flow
            SET NOT NULL
            """,

            """
            ALTER TABLE borrower_financials
            ALTER COLUMN restructured
            SET NOT NULL
            """,

            """
            ALTER TABLE risk_scores
            ALTER COLUMN borrower_id
            SET NOT NULL
            """,

            """
            ALTER TABLE risk_scores
            ALTER COLUMN score
            SET NOT NULL
            """,

            """
            ALTER TABLE risk_scores
            ALTER COLUMN classification
            SET NOT NULL
            """,

            """
            ALTER TABLE alerts
            ALTER COLUMN borrower_id
            SET NOT NULL
            """,

            """
            ALTER TABLE alerts
            ALTER COLUMN alert_type
            SET NOT NULL
            """,

            """
            ALTER TABLE alerts
            ALTER COLUMN severity
            SET NOT NULL
            """,
        ]


        for statement in not_null_statements:
            conn.execute(
                text(statement)
            )


        # =================================================
        # CHECK CONSTRAINTS
        # =================================================

        constraints = [

            (
                "ck_borrowers_name_nonempty",
                """
                ALTER TABLE borrowers
                ADD CONSTRAINT
                    ck_borrowers_name_nonempty
                CHECK (
                    BTRIM(borrower_name) <> ''
                )
                """,
            ),

            (
                "ck_borrowers_sector_nonempty",
                """
                ALTER TABLE borrowers
                ADD CONSTRAINT
                    ck_borrowers_sector_nonempty
                CHECK (
                    BTRIM(sector) <> ''
                )
                """,
            ),

            (
                "ck_borrowers_loan_amount_nonnegative",
                """
                ALTER TABLE borrowers
                ADD CONSTRAINT
                    ck_borrowers_loan_amount_nonnegative
                CHECK (
                    loan_amount >= 0
                )
                """,
            ),

            (
                "ck_financials_dpd_nonnegative",
                """
                ALTER TABLE borrower_financials
                ADD CONSTRAINT
                    ck_financials_dpd_nonnegative
                CHECK (
                    dpd >= 0
                )
                """,
            ),

            (
                "ck_risk_score_nonnegative",
                """
                ALTER TABLE risk_scores
                ADD CONSTRAINT
                    ck_risk_score_nonnegative
                CHECK (
                    score >= 0
                )
                """,
            ),

            (
                "ck_risk_classification",
                """
                ALTER TABLE risk_scores
                ADD CONSTRAINT
                    ck_risk_classification
                CHECK (
                    classification IN (
                        'Low Risk',
                        'Watchlist',
                        'High Risk'
                    )
                )
                """,
            ),

            (
                "ck_alert_type_nonempty",
                """
                ALTER TABLE alerts
                ADD CONSTRAINT
                    ck_alert_type_nonempty
                CHECK (
                    BTRIM(alert_type) <> ''
                )
                """,
            ),

            (
                "ck_alert_severity",
                """
                ALTER TABLE alerts
                ADD CONSTRAINT
                    ck_alert_severity
                CHECK (
                    severity IN (
                        'LOW',
                        'MEDIUM',
                        'HIGH'
                    )
                )
                """,
            ),
        ]


        for (
            constraint_name,
            statement,
        ) in constraints:

            if not constraint_exists(
                conn,
                constraint_name,
            ):
                conn.execute(
                    text(statement)
                )


        # =================================================
        # BORROWER IDENTITY
        # =================================================

        conn.execute(
            text("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                    uq_borrowers_borrower_name

                ON borrowers (
                    borrower_name
                )
            """)
        )


        # =================================================
        # ACCESS-PATH INDEXES
        # =================================================

        indexes = [

            """
            CREATE INDEX IF NOT EXISTS
                ix_borrowers_sector
            ON borrowers (
                sector
            )
            """,

            """
            CREATE INDEX IF NOT EXISTS
                ix_borrower_financials_borrower_id
            ON borrower_financials (
                borrower_id
            )
            """,

            """
            CREATE INDEX IF NOT EXISTS
                ix_risk_scores_borrower_id
            ON risk_scores (
                borrower_id
            )
            """,

            """
            CREATE INDEX IF NOT EXISTS
                ix_risk_history_borrower_id
            ON risk_history (
                borrower_id
            )
            """,

            """
            CREATE INDEX IF NOT EXISTS
                ix_alerts_borrower_id
            ON alerts (
                borrower_id
            )
            """,

            """
            CREATE INDEX IF NOT EXISTS
                ix_alerts_severity
            ON alerts (
                severity
            )
            """,
        ]


        for statement in indexes:
            conn.execute(
                text(statement)
            )


    print(
        "Core database invariant hardening complete."
    )


if __name__ == "__main__":
    run_migration()
