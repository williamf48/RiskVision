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

SYNTHETIC_EVENTS = [

    {
        "borrower_name":
            "Falcon Realty Ltd",

        "event_type":
            "PAYMENT_STRESS",

        "event_date":
            "2026-06-30",

        "severity":
            "SEVERE",

        "source":
            "SYNTHETIC_BACKTEST",

        "notes":
            "Synthetic development event used to validate historical replay and lead-time measurement.",
    },


    {
        "borrower_name":
            "Crest Realty Pvt Ltd",

        "event_type":
            "COVENANT_STRESS",

        "event_date":
            "2026-07-31",

        "severity":
            "HIGH",

        "source":
            "SYNTHETIC_BACKTEST",

        "notes":
            "Synthetic development event used to validate historical replay and lead-time measurement.",
    },
]


def seed_events():

    borrower_query = text("""
        SELECT
            id,
            borrower_name

        FROM borrowers
    """)


    insert_query = text("""
        INSERT INTO borrower_stress_events (

            borrower_id,
            event_type,
            event_date,
            severity,
            source,
            notes

        )

        VALUES (

            :borrower_id,
            :event_type,
            :event_date,
            :severity,
            :source,
            :notes

        )

        ON CONFLICT (
            borrower_id,
            event_type,
            event_date,
            source
        )

        DO NOTHING
    """)


    with engine.begin() as conn:

        borrowers = conn.execute(
            borrower_query
        ).mappings().all()


        borrower_map = {

            borrower[
                "borrower_name"
            ]:
                borrower[
                    "id"
                ]

            for borrower
            in borrowers
        }


        for event in SYNTHETIC_EVENTS:

            borrower_name = (
                event[
                    "borrower_name"
                ]
            )


            borrower_id = (
                borrower_map.get(
                    borrower_name
                )
            )


            if borrower_id is None:

                raise RuntimeError(
                    f"Borrower not found: "
                    f"{borrower_name}"
                )


            conn.execute(

                insert_query,

                {
                    "borrower_id":
                        borrower_id,

                    "event_type":
                        event[
                            "event_type"
                        ],

                    "event_date":
                        event[
                            "event_date"
                        ],

                    "severity":
                        event[
                            "severity"
                        ],

                    "source":
                        event[
                            "source"
                        ],

                    "notes":
                        event[
                            "notes"
                        ],
                },
            )


            print(
                f"{borrower_name}: "
                f"{event['event_type']} "
                f"on {event['event_date']} ready."
            )


    print()
    print(
        "Synthetic stress-event labels ready."
    )


if __name__ == "__main__":
    seed_events()