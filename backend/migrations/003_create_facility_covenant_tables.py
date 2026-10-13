import sys
from pathlib import Path

from sqlalchemy import text


# =========================================================
# ALLOW MIGRATION TO IMPORT BACKEND MODULES
# =========================================================

BACKEND_DIR = Path(__file__).resolve().parent.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_DIR),
    )


from connection import engine
def run_migration():

    statements = [

        # =================================================
        # FACILITIES
        # =================================================

        """
        CREATE TABLE IF NOT EXISTS facilities (

            id SERIAL PRIMARY KEY,

            borrower_id INTEGER NOT NULL,

            facility_code TEXT NOT NULL,

            facility_name TEXT NOT NULL,

            facility_type TEXT NOT NULL,

            sanctioned_amount NUMERIC(18, 2) NOT NULL,

            outstanding_amount NUMERIC(18, 2),

            currency TEXT NOT NULL DEFAULT 'INR',

            interest_rate NUMERIC(8, 4),

            maturity_date DATE,

            security_type TEXT,

            status TEXT NOT NULL DEFAULT 'ACTIVE',

            created_at TIMESTAMP NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_facilities_borrower
                FOREIGN KEY (borrower_id)
                REFERENCES borrowers(id)
                ON DELETE CASCADE,

            CONSTRAINT uq_facility_code_per_borrower
                UNIQUE (
                    borrower_id,
                    facility_code
                ),

            CONSTRAINT ck_facility_sanctioned_amount
                CHECK (
                    sanctioned_amount >= 0
                ),

            CONSTRAINT ck_facility_outstanding_amount
                CHECK (
                    outstanding_amount IS NULL
                    OR outstanding_amount >= 0
                ),

            CONSTRAINT ck_facility_status
                CHECK (
                    status IN (
                        'ACTIVE',
                        'CLOSED',
                        'RESTRUCTURED',
                        'DEFAULTED'
                    )
                )
        )
        """,


        # =================================================
        # COVENANT DEFINITIONS
        # =================================================

        """
        CREATE TABLE IF NOT EXISTS covenants (

            id SERIAL PRIMARY KEY,

            facility_id INTEGER NOT NULL,

            covenant_code TEXT NOT NULL,

            covenant_name TEXT NOT NULL,

            metric_code TEXT NOT NULL,

            threshold_direction TEXT NOT NULL,

            threshold_value NUMERIC(18, 6) NOT NULL,

            warning_buffer_pct NUMERIC(8, 4)
                NOT NULL DEFAULT 15,

            testing_frequency TEXT NOT NULL,

            next_test_date DATE,

            status TEXT NOT NULL DEFAULT 'ACTIVE',

            created_at TIMESTAMP NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_covenants_facility
                FOREIGN KEY (facility_id)
                REFERENCES facilities(id)
                ON DELETE CASCADE,

            CONSTRAINT uq_covenant_code_per_facility
                UNIQUE (
                    facility_id,
                    covenant_code
                ),

            CONSTRAINT ck_covenant_direction
                CHECK (
                    threshold_direction IN (
                        'MINIMUM',
                        'MAXIMUM'
                    )
                ),

            CONSTRAINT ck_covenant_warning_buffer
                CHECK (
                    warning_buffer_pct >= 0
                ),

            CONSTRAINT ck_covenant_frequency
                CHECK (
                    testing_frequency IN (
                        'MONTHLY',
                        'QUARTERLY',
                        'SEMI_ANNUAL',
                        'ANNUAL'
                    )
                ),

            CONSTRAINT ck_covenant_status
                CHECK (
                    status IN (
                        'ACTIVE',
                        'WAIVED',
                        'EXPIRED'
                    )
                )
        )
        """,


        # =================================================
        # COVENANT TEST RESULTS
        # =================================================

        """
        CREATE TABLE IF NOT EXISTS covenant_tests (

            id SERIAL PRIMARY KEY,

            covenant_id INTEGER NOT NULL,

            test_date DATE NOT NULL,

            actual_value NUMERIC(18, 6) NOT NULL,

            headroom_absolute NUMERIC(18, 6),

            headroom_percentage NUMERIC(12, 4),

            test_status TEXT NOT NULL,

            source TEXT NOT NULL,

            data_quality TEXT NOT NULL
                DEFAULT 'VALID',

            analyst_note TEXT,

            created_at TIMESTAMP NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_covenant_tests_covenant
                FOREIGN KEY (covenant_id)
                REFERENCES covenants(id)
                ON DELETE CASCADE,

            CONSTRAINT uq_covenant_test
                UNIQUE (
                    covenant_id,
                    test_date,
                    source
                ),

            CONSTRAINT ck_covenant_test_status
                CHECK (
                    test_status IN (
                        'HEALTHY',
                        'TIGHT',
                        'NEAR_BREACH',
                        'BREACHED'
                    )
                ),

            CONSTRAINT ck_covenant_test_quality
                CHECK (
                    data_quality IN (
                        'VALID',
                        'ESTIMATED',
                        'STALE'
                    )
                )
        )
        """,


        # =================================================
        # INDEXES
        # =================================================

        """
        CREATE INDEX IF NOT EXISTS
            ix_facilities_borrower_id
        ON facilities (
            borrower_id
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_facilities_status
        ON facilities (
            status
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_covenants_facility_id
        ON covenants (
            facility_id
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_covenants_metric_code
        ON covenants (
            metric_code
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_covenants_next_test_date
        ON covenants (
            next_test_date
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_covenant_tests_covenant_id
        ON covenant_tests (
            covenant_id
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_covenant_tests_test_date
        ON covenant_tests (
            test_date
        )
        """,

        """
        CREATE INDEX IF NOT EXISTS
            ix_covenant_tests_status
        ON covenant_tests (
            test_status
        )
        """,
    ]


    with engine.begin() as connection:

        for statement in statements:

            connection.execute(
                text(statement.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY")
                     if engine.dialect.name == "sqlite" else statement)
            )


    print(
        "Facility and covenant schema migration complete."
    )


if __name__ == "__main__":

    run_migration()