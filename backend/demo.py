"""Run the real RiskVision engines against isolated, reproducible sample data.

Usage: python backend/demo.py [--seed-only]
This entry point never opens or modifies the configured PostgreSQL database.
"""
import os
import runpy
import sys
from pathlib import Path

os.environ["RISK_DEMO_MODE"] = "1"

from sqlalchemy import text
from connection import engine

ROOT = Path(__file__).resolve().parent


def upgrade_demo():
    """Repair the v1 fixture schedule once, keeping installed demo data and cases."""
    with engine.begin() as conn:
        version = conn.execute(text("SELECT version FROM demo_ready")).scalar_one()
        if version < 2:
            conn.execute(text("UPDATE covenants SET next_test_date='2026-06-30' "
                              "WHERE testing_frequency='QUARTERLY' AND next_test_date='2026-12-31'"))
            conn.execute(text("UPDATE demo_ready SET version=2"))


def seed_demo():
    with engine.connect() as conn:
        exists = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='demo_ready'"
        )).first()
    if exists:
        upgrade_demo()
        return

    import openpyxl

    statements = [
        """CREATE TABLE IF NOT EXISTS borrowers (
            id INTEGER PRIMARY KEY, borrower_name TEXT, sector TEXT,
            loan_amount REAL, created_at TEXT DEFAULT '2026-05-31T09:00:00')""",
        """CREATE TABLE IF NOT EXISTS borrower_financials (
            borrower_id INTEGER PRIMARY KEY, dpd INTEGER, dscr REAL,
            revenue_decline REAL, cash_flow TEXT, restructured BOOLEAN)""",
        """CREATE TABLE IF NOT EXISTS risk_scores (
            borrower_id INTEGER PRIMARY KEY, score REAL, classification TEXT)""",
        """CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY, borrower_id INTEGER, alert_type TEXT,
            severity TEXT, created_at TEXT DEFAULT '2026-05-31T09:00:00',
            UNIQUE(borrower_id, alert_type))""",
        """CREATE TABLE IF NOT EXISTS risk_history (
            id INTEGER PRIMARY KEY, borrower_id INTEGER, score REAL,
            classification TEXT, created_at TEXT DEFAULT '2026-05-31T09:00:00')""",
        (ROOT / 'migrations/001_create_borrower_metric_observations.sql')
            .read_text().replace('SERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY'),
    ]
    workbook = openpyxl.load_workbook(
        ROOT.parent / 'data/risk_output.xlsx', read_only=True, data_only=True
    )
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))
        for borrower_id, row in enumerate(list(workbook.active.values)[1:], 47):
            name, sector, exposure, dpd, dscr, decline, cash, restructured, score, _, classification, *_ = row
            conn.execute(text('INSERT OR IGNORE INTO borrowers (id, borrower_name, sector, loan_amount) VALUES (:id, :name, :sector, :exposure)'),
                         dict(id=borrower_id, name=name, sector=sector, exposure=exposure))
            conn.execute(text('INSERT OR IGNORE INTO borrower_financials VALUES (:id, :dpd, :dscr, :decline, :cash, :restructured)'),
                         dict(id=borrower_id, dpd=dpd, dscr=dscr, decline=decline, cash=cash, restructured=str(restructured).lower() == 'yes'))
            conn.execute(text('INSERT OR IGNORE INTO risk_scores VALUES (:id, :score, :classification)'),
                         dict(id=borrower_id, score=score, classification=classification))
            # The workbook expresses revenue decline in percentage points.
            conditions = [(score > 60, 'High Risk Borrower', 'HIGH'),
                          (dpd > 30, 'Payment Delay', 'HIGH'),
                          (dscr < 1, 'Liquidity Stress', 'MEDIUM'),
                          (decline > 20, 'Business Deterioration', 'MEDIUM'),
                          (str(cash).lower() == 'negative', 'Negative Cash Flow', 'HIGH')]
            for condition, label, severity in conditions:
                if condition:
                    conn.execute(text('INSERT OR IGNORE INTO alerts (borrower_id, alert_type, severity) VALUES (:id, :label, :severity)'),
                                 dict(id=borrower_id, label=label, severity=severity))
    workbook.close()

    for migration in ['003_create_facility_covenant_tables.py', '004_create_stress_events.py']:
        runpy.run_path(str(ROOT / 'migrations' / migration), run_name='__main__')
    for seed in sorted((ROOT / 'seeds').glob('*.py')):
        runpy.run_path(str(seed), run_name='__main__')
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE demo_ready (version INTEGER)'))
        conn.execute(text('INSERT INTO demo_ready VALUES (1)'))
    print('Sample portfolio ready. All analytics use the existing RiskVision engines.')
    upgrade_demo()


if __name__ == '__main__':
    seed_demo()
    if '--seed-only' not in sys.argv:
        import uvicorn
        uvicorn.run('main:app', host='127.0.0.1', port=8000)
