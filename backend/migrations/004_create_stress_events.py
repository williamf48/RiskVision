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


def run_migration():

    statements = [

        """
        CREATE TABLE IF NOT EXISTS borrower_stress_events (

            id SERIAL PRIMARY KEY,

            borrower_id INTEGER NOT NULL
                REFERENCES borrowers(id)
                ON DELETE CASCADE,

            event_type TEXT NOT NULL,

            event_date DATE NOT NULL,

            severity TEXT NOT NULL,

            source TEXT NOT NULL,

            notes TEXT,

            created_at TIMESTAMP NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT borrower_stress_event_unique
            UNIQUE (
                borrower_id,
                event_type,
                event_date,
                source
            )
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_borrower_stress_events_borrower_date

        ON borrower_stress_events (
            borrower_id,
            event_date
        )
        """,
    ]


    with engine.begin() as conn:

        for statement in statements:

            conn.execute(
                text(statement)
            )


    print(
        "Borrower stress-event schema migration complete."
    )


if __name__ == "__main__":
    run_migration()