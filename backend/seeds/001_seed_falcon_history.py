import sys
from pathlib import Path

from sqlalchemy import text


# Allow this script to import files from the backend folder
BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from connection import engine

BORROWER_NAME = "Falcon Realty Ltd"


observations = [

    # =====================================================
    # DSCR — QUARTERLY
    # Lower = deterioration
    # =====================================================

    ("DSCR", 1.45, "2025-06-30", "2025-04-01", "2025-06-30", "QUARTERLY"),
    ("DSCR", 1.31, "2025-09-30", "2025-07-01", "2025-09-30", "QUARTERLY"),
    ("DSCR", 1.12, "2025-12-31", "2025-10-01", "2025-12-31", "QUARTERLY"),
    ("DSCR", 0.90, "2026-03-31", "2026-01-01", "2026-03-31", "QUARTERLY"),

    # =====================================================
    # BOUNCE RATE — MONTHLY
    # Higher = deterioration
    # =====================================================

    ("BOUNCE_RATE", 2.0, "2026-02-28", "2026-02-01", "2026-02-28", "MONTHLY"),
    ("BOUNCE_RATE", 3.2, "2026-03-31", "2026-03-01", "2026-03-31", "MONTHLY"),
    ("BOUNCE_RATE", 5.4, "2026-04-30", "2026-04-01", "2026-04-30", "MONTHLY"),
    ("BOUNCE_RATE", 8.1, "2026-05-31", "2026-05-01", "2026-05-31", "MONTHLY"),

    # =====================================================
    # RECEIVABLE DAYS — QUARTERLY
    # Higher = deterioration
    # =====================================================

    ("RECEIVABLE_DAYS", 52, "2025-06-30", "2025-04-01", "2025-06-30", "QUARTERLY"),
    ("RECEIVABLE_DAYS", 61, "2025-09-30", "2025-07-01", "2025-09-30", "QUARTERLY"),
    ("RECEIVABLE_DAYS", 75, "2025-12-31", "2025-10-01", "2025-12-31", "QUARTERLY"),
    ("RECEIVABLE_DAYS", 94, "2026-03-31", "2026-01-01", "2026-03-31", "QUARTERLY"),

    # =====================================================
    # DEBT / EBITDA — QUARTERLY
    # Higher = deterioration
    # =====================================================

    ("DEBT_EBITDA", 2.2, "2025-06-30", "2025-04-01", "2025-06-30", "QUARTERLY"),
    ("DEBT_EBITDA", 2.5, "2025-09-30", "2025-07-01", "2025-09-30", "QUARTERLY"),
    ("DEBT_EBITDA", 2.9, "2025-12-31", "2025-10-01", "2025-12-31", "QUARTERLY"),
    ("DEBT_EBITDA", 3.4, "2026-03-31", "2026-01-01", "2026-03-31", "QUARTERLY"),
]


with engine.begin() as conn:

    borrower_id = conn.execute(
        text("""
            SELECT id
            FROM borrowers
            WHERE borrower_name = :borrower_name
        """),
        {
            "borrower_name": BORROWER_NAME
        },
    ).scalar_one_or_none()

    if borrower_id is None:
        raise RuntimeError(
            f"Borrower not found: {BORROWER_NAME}"
        )

    insert_query = text("""
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

    rows = [
        {
            "borrower_id": borrower_id,
            "metric_code": metric_code,
            "metric_value": metric_value,
            "observation_date": observation_date,
            "period_start": period_start,
            "period_end": period_end,
            "reporting_frequency": reporting_frequency,
        }
        for (
            metric_code,
            metric_value,
            observation_date,
            period_start,
            period_end,
            reporting_frequency,
        ) in observations
    ]

    conn.execute(
        insert_query,
        rows,
    )


print(
    f"Falcon Realty synthetic history ready: "
    f"{len(observations)} observations."
)