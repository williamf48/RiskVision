import sys
from pathlib import Path

from sqlalchemy import text


# =========================================================
# ALLOW IMPORTS FROM BACKEND DIRECTORY
# =========================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from connection import engine


# =========================================================
# SYNTHETIC DEVELOPMENT HISTORIES
# =========================================================
#
# These histories are intentionally synthetic.
# They exist only to test portfolio-level intervention
# prioritization across different deterioration patterns.
#
# Expected outcomes:
#
# Crest Realty Pvt Ltd
# -> HIGH
#
# Nova Energy Ltd
# -> MEDIUM
#
# Alpha Manufacturing Ltd
# -> LOW
#
# Beta Logistics Pvt Ltd
# -> MEDIUM / mixed trajectory
#
# Falcon Realty Ltd already exists as URGENT.
#
# Orion Power Projects Ltd intentionally remains without
# history so it continues to test INSUFFICIENT_DATA.
# =========================================================


BORROWER_HISTORIES = {


    # =====================================================
    # CREST REALTY
    #
    # Expected:
    # HIGH
    #
    # 3 / 4 signals deteriorating
    # 75% convergence
    # one critical signal
    # multiple weak signals
    # persistent deterioration
    # =====================================================

    "Crest Realty Pvt Ltd": {

        "DSCR": [
            (1.45, "2025-06-30", "2025-04-01", "2025-06-30", "QUARTERLY"),
            (1.28, "2025-09-30", "2025-07-01", "2025-09-30", "QUARTERLY"),
            (1.12, "2025-12-31", "2025-10-01", "2025-12-31", "QUARTERLY"),
            (1.05, "2026-03-31", "2026-01-01", "2026-03-31", "QUARTERLY"),
        ],

        "BOUNCE_RATE": [
            (1.8, "2026-02-28", "2026-02-01", "2026-02-28", "MONTHLY"),
            (2.4, "2026-03-31", "2026-03-01", "2026-03-31", "MONTHLY"),
            (4.8, "2026-04-30", "2026-04-01", "2026-04-30", "MONTHLY"),
            (8.5, "2026-05-31", "2026-05-01", "2026-05-31", "MONTHLY"),
        ],

        "RECEIVABLE_DAYS": [
            (50, "2025-06-30", "2025-04-01", "2025-06-30", "QUARTERLY"),
            (58, "2025-09-30", "2025-07-01", "2025-09-30", "QUARTERLY"),
            (68, "2025-12-31", "2025-10-01", "2025-12-31", "QUARTERLY"),
            (72, "2026-03-31", "2026-01-01", "2026-03-31", "QUARTERLY"),
        ],

        "DEBT_EBITDA": [
            (2.2, "2025-06-30", "2025-04-01", "2025-06-30", "QUARTERLY"),
            (2.3, "2025-09-30", "2025-07-01", "2025-09-30", "QUARTERLY"),
            (2.3, "2025-12-31", "2025-10-01", "2025-12-31", "QUARTERLY"),
            (2.3, "2026-03-31", "2026-01-01", "2026-03-31", "QUARTERLY"),
        ],
    },


    # =====================================================
    # NOVA ENERGY
    #
    # Expected:
    # MEDIUM
    #
    # 2 deteriorating
    # 2 improving
    # 50% convergence
    # emerging rather than broad deterioration
    # =====================================================

    "Nova Energy Ltd": {

        "DSCR": [
            (1.55, "2025-06-30", "2025-04-01", "2025-06-30", "QUARTERLY"),
            (1.45, "2025-09-30", "2025-07-01", "2025-09-30", "QUARTERLY"),
            (1.35, "2025-12-31", "2025-10-01", "2025-12-31", "QUARTERLY"),
            (1.25, "2026-03-31", "2026-01-01", "2026-03-31", "QUARTERLY"),
        ],

        "BOUNCE_RATE": [
            (1.0, "2026-02-28", "2026-02-01", "2026-02-28", "MONTHLY"),
            (1.5, "2026-03-31", "2026-03-01", "2026-03-31", "MONTHLY"),
            (1.8, "2026-04-30", "2026-04-01", "2026-04-30", "MONTHLY"),
            (2.4, "2026-05-31", "2026-05-01", "2026-05-31", "MONTHLY"),
        ],

        "RECEIVABLE_DAYS": [
            (42, "2025-06-30", "2025-04-01", "2025-06-30", "QUARTERLY"),
            (40, "2025-09-30", "2025-07-01", "2025-09-30", "QUARTERLY"),
            (38, "2025-12-31", "2025-10-01", "2025-12-31", "QUARTERLY"),
            (36, "2026-03-31", "2026-01-01", "2026-03-31", "QUARTERLY"),
        ],

        "DEBT_EBITDA": [
            (2.1, "2025-06-30", "2025-04-01", "2025-06-30", "QUARTERLY"),
            (2.0, "2025-09-30", "2025-07-01", "2025-09-30", "QUARTERLY"),
            (1.9, "2025-12-31", "2025-10-01", "2025-12-31", "QUARTERLY"),
            (1.8, "2026-03-31", "2026-01-01", "2026-03-31", "QUARTERLY"),
        ],
    },


    # =====================================================
    # ALPHA MANUFACTURING
    #
    # Expected:
    # LOW
    #
    # all signals improving
    # all latest conditions healthy
    # =====================================================

    "Alpha Manufacturing Ltd": {

        "DSCR": [
            (1.70, "2025-06-30", "2025-04-01", "2025-06-30", "QUARTERLY"),
            (1.85, "2025-09-30", "2025-07-01", "2025-09-30", "QUARTERLY"),
            (2.00, "2025-12-31", "2025-10-01", "2025-12-31", "QUARTERLY"),
            (2.10, "2026-03-31", "2026-01-01", "2026-03-31", "QUARTERLY"),
        ],

        "BOUNCE_RATE": [
            (2.0, "2026-02-28", "2026-02-01", "2026-02-28", "MONTHLY"),
            (1.7, "2026-03-31", "2026-03-01", "2026-03-31", "MONTHLY"),
            (1.3, "2026-04-30", "2026-04-01", "2026-04-30", "MONTHLY"),
            (1.0, "2026-05-31", "2026-05-01", "2026-05-31", "MONTHLY"),
        ],

        "RECEIVABLE_DAYS": [
            (44, "2025-06-30", "2025-04-01", "2025-06-30", "QUARTERLY"),
            (42, "2025-09-30", "2025-07-01", "2025-09-30", "QUARTERLY"),
            (40, "2025-12-31", "2025-10-01", "2025-12-31", "QUARTERLY"),
            (38, "2026-03-31", "2026-01-01", "2026-03-31", "QUARTERLY"),
        ],

        "DEBT_EBITDA": [
            (2.0, "2025-06-30", "2025-04-01", "2025-06-30", "QUARTERLY"),
            (1.9, "2025-09-30", "2025-07-01", "2025-09-30", "QUARTERLY"),
            (1.7, "2025-12-31", "2025-10-01", "2025-12-31", "QUARTERLY"),
            (1.5, "2026-03-31", "2026-01-01", "2026-03-31", "QUARTERLY"),
        ],
    },


    # =====================================================
    # BETA LOGISTICS
    #
    # Expected:
    # MEDIUM
    #
    # DSCR deteriorating
    # other signals improving
    # mixed trajectory
    # =====================================================

    "Beta Logistics Pvt Ltd": {

        "DSCR": [
            (2.40, "2025-06-30", "2025-04-01", "2025-06-30", "QUARTERLY"),
            (2.20, "2025-09-30", "2025-07-01", "2025-09-30", "QUARTERLY"),
            (2.05, "2025-12-31", "2025-10-01", "2025-12-31", "QUARTERLY"),
            (1.95, "2026-03-31", "2026-01-01", "2026-03-31", "QUARTERLY"),
        ],

        "BOUNCE_RATE": [
            (4.0, "2026-02-28", "2026-02-01", "2026-02-28", "MONTHLY"),
            (3.2, "2026-03-31", "2026-03-01", "2026-03-31", "MONTHLY"),
            (2.5, "2026-04-30", "2026-04-01", "2026-04-30", "MONTHLY"),
            (1.8, "2026-05-31", "2026-05-01", "2026-05-31", "MONTHLY"),
        ],

        "RECEIVABLE_DAYS": [
            (65, "2025-06-30", "2025-04-01", "2025-06-30", "QUARTERLY"),
            (58, "2025-09-30", "2025-07-01", "2025-09-30", "QUARTERLY"),
            (52, "2025-12-31", "2025-10-01", "2025-12-31", "QUARTERLY"),
            (45, "2026-03-31", "2026-01-01", "2026-03-31", "QUARTERLY"),
        ],

        "DEBT_EBITDA": [
            (3.2, "2025-06-30", "2025-04-01", "2025-06-30", "QUARTERLY"),
            (2.8, "2025-09-30", "2025-07-01", "2025-09-30", "QUARTERLY"),
            (2.4, "2025-12-31", "2025-10-01", "2025-12-31", "QUARTERLY"),
            (2.1, "2026-03-31", "2026-01-01", "2026-03-31", "QUARTERLY"),
        ],
    },
}


# =========================================================
# INSERT QUERY
# =========================================================

INSERT_QUERY = text("""
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
        :borrower_id,
        :metric_code,
        :metric_value,
        :observation_date,
        :period_start,
        :period_end,
        :reporting_frequency,
        'SYNTHETIC',
        'VALID'
    )

    ON CONFLICT (
        borrower_id,
        metric_code,
        observation_date,
        source
    )

    DO NOTHING
""")


# =========================================================
# SEED
# =========================================================

with engine.begin() as conn:

    total_attempted = 0

    for (
        borrower_name,
        metric_histories,
    ) in BORROWER_HISTORIES.items():

        borrower_id = conn.execute(
            text("""
                SELECT id
                FROM borrowers
                WHERE borrower_name = :borrower_name
            """),
            {
                "borrower_name":
                    borrower_name
            },
        ).scalar_one_or_none()


        if borrower_id is None:

            raise RuntimeError(
                f"Borrower not found: "
                f"{borrower_name}"
            )


        rows = []


        for (
            metric_code,
            observations,
        ) in metric_histories.items():

            for observation in observations:

                (
                    metric_value,
                    observation_date,
                    period_start,
                    period_end,
                    reporting_frequency,
                ) = observation


                rows.append({

                    "borrower_id":
                        borrower_id,

                    "metric_code":
                        metric_code,

                    "metric_value":
                        metric_value,

                    "observation_date":
                        observation_date,

                    "period_start":
                        period_start,

                    "period_end":
                        period_end,

                    "reporting_frequency":
                        reporting_frequency,
                })


        conn.execute(
            INSERT_QUERY,
            rows,
        )


        total_attempted += len(
            rows
        )


        print(
            f"{borrower_name}: "
            f"{len(rows)} observations ready."
        )


print()

print(
    "Portfolio synthetic histories ready."
)

print(
    "Attempted observations:",
    total_attempted
)