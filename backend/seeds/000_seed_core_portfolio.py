import json
import sys
from pathlib import Path

from sqlalchemy import text


# =========================================================
# ALLOW IMPORTS FROM BACKEND DIRECTORY
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
# FIXTURE LOCATION
# =========================================================

FIXTURE_PATH = (
    Path(__file__)
    .resolve()
    .parent
    / "core_portfolio_fixture.json"
)


# =========================================================
# EXPECTED FIXTURE COUNTS
# =========================================================

EXPECTED_COUNTS = {
    "borrowers": 25,
    "borrower_financials": 25,
    "risk_scores": 25,
    "risk_history": 25,
    "alerts": 46,
}


# =========================================================
# LOAD FIXTURE
# =========================================================

def load_fixture():

    if not FIXTURE_PATH.exists():

        raise RuntimeError(
            f"Fixture not found: {FIXTURE_PATH}"
        )

    with FIXTURE_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:

        fixture = json.load(file)

    return fixture


# =========================================================
# VALIDATE FIXTURE
# =========================================================

def validate_fixture(
    fixture,
):

    for (
        table,
        expected_count,
    ) in EXPECTED_COUNTS.items():

        if table not in fixture:

            raise RuntimeError(
                f"Missing fixture table: {table}"
            )

        actual_count = len(
            fixture[table]
        )

        if actual_count != expected_count:

            raise RuntimeError(
                f"{table}: expected "
                f"{expected_count} rows, "
                f"found {actual_count}"
            )


# =========================================================
# SEED CORE PORTFOLIO
# =========================================================

def seed_core_portfolio():

    fixture = load_fixture()

    validate_fixture(
        fixture
    )


    with engine.begin() as conn:

        # =================================================
        # CLEAN EXISTING CORE DATA
        # =================================================
        #
        # Child tables are cleared before borrowers
        # because they reference borrowers through FKs.
        # =================================================

        conn.execute(
            text(
                "DELETE FROM alerts"
            )
        )

        conn.execute(
            text(
                "DELETE FROM risk_history"
            )
        )

        conn.execute(
            text(
                "DELETE FROM risk_scores"
            )
        )

        conn.execute(
            text(
                "DELETE FROM borrower_financials"
            )
        )

        conn.execute(
            text(
                "DELETE FROM borrowers"
            )
        )


        # =================================================
        # BORROWERS
        # =================================================

        conn.execute(
            text("""
                INSERT INTO borrowers (
                    id,
                    borrower_name,
                    sector,
                    loan_amount,
                    created_at
                )

                VALUES (
                    :id,
                    :borrower_name,
                    :sector,
                    :loan_amount,
                    :created_at
                )
            """),
            fixture[
                "borrowers"
            ],
        )


        # =================================================
        # BORROWER FINANCIALS
        # =================================================

        conn.execute(
            text("""
                INSERT INTO borrower_financials (
                    id,
                    borrower_id,
                    dpd,
                    dscr,
                    revenue_decline,
                    cash_flow,
                    restructured,
                    uploaded_at
                )

                VALUES (
                    :id,
                    :borrower_id,
                    :dpd,
                    :dscr,
                    :revenue_decline,
                    :cash_flow,
                    :restructured,
                    :uploaded_at
                )
            """),
            fixture[
                "borrower_financials"
            ],
        )


        # =================================================
        # RISK SCORES
        # =================================================

        conn.execute(
            text("""
                INSERT INTO risk_scores (
                    id,
                    borrower_id,
                    score,
                    classification,
                    generated_at
                )

                VALUES (
                    :id,
                    :borrower_id,
                    :score,
                    :classification,
                    :generated_at
                )
            """),
            fixture[
                "risk_scores"
            ],
        )


        # =================================================
        # RISK HISTORY
        # =================================================

        conn.execute(
            text("""
                INSERT INTO risk_history (
                    id,
                    borrower_id,
                    old_score,
                    new_score,
                    reason,
                    changed_at
                )

                VALUES (
                    :id,
                    :borrower_id,
                    :old_score,
                    :new_score,
                    :reason,
                    :changed_at
                )
            """),
            fixture[
                "risk_history"
            ],
        )


        # =================================================
        # ALERTS
        # =================================================

        conn.execute(
            text("""
                INSERT INTO alerts (
                    id,
                    borrower_id,
                    alert_type,
                    severity,
                    created_at
                )

                VALUES (
                    :id,
                    :borrower_id,
                    :alert_type,
                    :severity,
                    :created_at
                )
            """),
            fixture[
                "alerts"
            ],
        )


        # =================================================
        # RESET POSTGRES ID SEQUENCES
        # =================================================
        #
        # The fixture preserves original IDs, including
        # borrower IDs such as Falcon Realty = 65.
        #
        # Therefore PostgreSQL sequences must be advanced
        # to MAX(id) after inserting explicit IDs.
        # =================================================

        sequence_tables = [
            "borrowers",
            "borrower_financials",
            "risk_scores",
            "risk_history",
            "alerts",
        ]


        for table in sequence_tables:

            conn.execute(
                text(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence(
                            '{table}',
                            'id'
                        ),
                        COALESCE(
                            (
                                SELECT MAX(id)
                                FROM {table}
                            ),
                            1
                        ),
                        true
                    )
                    """
                )
            )


    print()
    print(
        "Core synthetic portfolio fixture loaded."
    )

    print()

    for (
        table,
        expected_count,
    ) in EXPECTED_COUNTS.items():

        print(
            f"{table}: "
            f"{expected_count} rows"
        )


# =========================================================
# RUN DIRECTLY
# =========================================================

if __name__ == "__main__":

    seed_core_portfolio()