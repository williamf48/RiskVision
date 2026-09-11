from __future__ import annotations

from sqlalchemy import inspect, text

from connection import engine


EXPECTED_TABLES = {
    "alerts",
    "borrower_financials",
    "borrower_metric_observations",
    "borrower_stress_events",
    "borrowers",
    "covenant_tests",
    "covenants",
    "facilities",
    "risk_history",
    "risk_scores",
}

EXPECTED_FIXTURE_COUNTS = {
    "borrowers": 25,
    "borrower_financials": 25,
    "risk_scores": 25,
    "risk_history": 25,
    "alerts": 46,
    "borrower_metric_observations": 80,
    "facilities": 6,
    "covenants": 12,
    "covenant_tests": 40,
    "borrower_stress_events": 2,
}


def verify_environment() -> None:
    actual_tables = set(inspect(engine).get_table_names())
    missing = EXPECTED_TABLES - actual_tables

    if missing:
        raise RuntimeError(
            "RiskVision environment is incomplete. Missing tables: "
            + ", ".join(sorted(missing))
        )

    failures: list[str] = []

    with engine.connect() as conn:
        for table, expected in EXPECTED_FIXTURE_COUNTS.items():
            actual = int(
                conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            )
            if actual != expected:
                failures.append(f"{table}: expected {expected}, found {actual}")

    if failures:
        raise RuntimeError(
            "RiskVision fixture verification failed: " + "; ".join(failures)
        )

    print("RiskVision environment verified.")
    print(f"Database: {engine.url.database}")
    print(f"Tables: {len(EXPECTED_TABLES)}")
    print("Synthetic fixture counts match the reproducible development baseline.")


if __name__ == "__main__":
    verify_environment()
