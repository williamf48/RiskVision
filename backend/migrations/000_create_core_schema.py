import sys
from pathlib import Path

from sqlalchemy import text


# =========================================================
# ALLOW MIGRATION TO IMPORT BACKEND MODULES
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


# =========================================================
# CORE SCHEMA MIGRATION
# =========================================================

def run_migration():

    statements = [

        # =================================================
        # BORROWERS
        # =================================================

        """
        CREATE TABLE IF NOT EXISTS borrowers (

            id SERIAL PRIMARY KEY,

            borrower_name TEXT,

            sector TEXT,

            loan_amount NUMERIC,

            created_at TIMESTAMP
                DEFAULT NOW()
        )
        """,


        # =================================================
        # BORROWER FINANCIALS
        # =================================================

        """
        CREATE TABLE IF NOT EXISTS borrower_financials (

            id SERIAL PRIMARY KEY,

            borrower_id INTEGER
                REFERENCES borrowers(id)
                ON DELETE CASCADE,

            dpd INTEGER,

            dscr NUMERIC,

            revenue_decline NUMERIC,

            cash_flow TEXT,

            restructured BOOLEAN,

            uploaded_at TIMESTAMP
                DEFAULT NOW()
        )
        """,


        # =================================================
        # RISK SCORES
        # =================================================

        """
        CREATE TABLE IF NOT EXISTS risk_scores (

            id SERIAL PRIMARY KEY,

            borrower_id INTEGER
                REFERENCES borrowers(id)
                ON DELETE CASCADE,

            score NUMERIC,

            classification TEXT,

            generated_at TIMESTAMP
                DEFAULT NOW()
        )
        """,


        # =================================================
        # RISK HISTORY
        # =================================================

        """
        CREATE TABLE IF NOT EXISTS risk_history (

            id SERIAL PRIMARY KEY,

            borrower_id INTEGER
                REFERENCES borrowers(id)
                ON DELETE CASCADE,

            old_score NUMERIC,

            new_score NUMERIC,

            reason TEXT,

            changed_at TIMESTAMP
                DEFAULT NOW()
        )
        """,


        # =================================================
        # ALERTS
        # =================================================

        """
        CREATE TABLE IF NOT EXISTS alerts (

            id SERIAL PRIMARY KEY,

            borrower_id INTEGER
                REFERENCES borrowers(id)
                ON DELETE CASCADE,

            alert_type TEXT,

            severity TEXT,

            created_at TIMESTAMP
                DEFAULT NOW()
        )
        """,


        # =================================================
        # INDEXES
        # =================================================

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


    with engine.begin() as conn:

        for statement in statements:

            conn.execute(
                text(statement)
            )


    print(
        "Core RiskVision schema migration complete."
    )


if __name__ == "__main__":

    run_migration()