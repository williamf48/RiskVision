import runpy
from pathlib import Path

from sqlalchemy import inspect

from connection import engine


BACKEND_DIR = Path(__file__).resolve().parent
MIGRATIONS_DIR = BACKEND_DIR / "migrations"
SEEDS_DIR = BACKEND_DIR / "seeds"


def ensure_empty_database():
    """
    Bootstrap is intended only for a fresh database.

    Refuse to run against a database that already contains
    tables so existing development or production data cannot
    accidentally be overwritten.
    """

    existing_tables = (
        inspect(engine)
        .get_table_names()
    )

    if existing_tables:
        raise RuntimeError(
            "Database bootstrap aborted because the target "
            "database is not empty. Existing tables: "
            + ", ".join(
                sorted(existing_tables)
            )
        )


def run_python_script(path: Path):

    if not path.exists():
        raise RuntimeError(
            f"Required bootstrap file not found: {path}"
        )

    print()
    print(f">>> Running {path.name}")

    runpy.run_path(
        str(path),
        run_name="__main__",
    )


def run_sql_file(path: Path):

    if not path.exists():
        raise RuntimeError(
            f"Required bootstrap file not found: {path}"
        )

    print()
    print(f">>> Running {path.name}")

    sql = path.read_text(
        encoding="utf-8"
    )

    with engine.begin() as conn:
        conn.exec_driver_sql(sql)

    print(
        f"{path.name} complete."
    )


def bootstrap_database():

    print("=" * 72)
    print("RISKVISION DATABASE BOOTSTRAP")
    print("=" * 72)
    print(
        f"Target database: {engine.url.database}"
    )

    ensure_empty_database()

    # =====================================================
    # CORE PORTFOLIO
    # =====================================================

    run_python_script(
        MIGRATIONS_DIR
        / "000_create_core_schema.py"
    )

    run_python_script(
        SEEDS_DIR
        / "000_seed_core_portfolio.py"
    )

    # =====================================================
    # HISTORICAL OBSERVATIONS
    # =====================================================

    run_sql_file(
        MIGRATIONS_DIR
        / "001_create_borrower_metric_observations.sql"
    )

    run_python_script(
        SEEDS_DIR
        / "001_seed_falcon_history.py"
    )

    run_python_script(
        SEEDS_DIR
        / "002_seed_portfolio_histories.py"
    )

    # =====================================================
    # FACILITIES + COVENANTS
    # =====================================================

    run_python_script(
        MIGRATIONS_DIR
        / "003_create_facility_covenant_tables.py"
    )

    run_python_script(
        SEEDS_DIR
        / "003_seed_facilities_covenants.py"
    )

    # =====================================================
    # STRESS EVENTS
    # =====================================================

    run_python_script(
        MIGRATIONS_DIR
        / "004_create_stress_events.py"
    )

    run_python_script(
        SEEDS_DIR
        / "004_seed_stress_events.py"
    )

    # =====================================================
    # FINAL SCHEMA VERIFICATION
    # =====================================================

    expected_tables = {
        "borrowers",
        "borrower_financials",
        "risk_scores",
        "risk_history",
        "alerts",
        "borrower_metric_observations",
        "facilities",
        "covenants",
        "covenant_tests",
        "borrower_stress_events",
    }

    actual_tables = set(
        inspect(engine)
        .get_table_names()
    )

    missing_tables = (
        expected_tables
        - actual_tables
    )

    if missing_tables:
        raise RuntimeError(
            "Bootstrap incomplete. Missing tables: "
            + ", ".join(
                sorted(missing_tables)
            )
        )

    print()
    print("=" * 72)
    print(
        "RISKVISION DATABASE BOOTSTRAP COMPLETE"
    )
    print("=" * 72)
    print(
        f"Tables created: {len(expected_tables)}"
    )


if __name__ == "__main__":
    bootstrap_database()
