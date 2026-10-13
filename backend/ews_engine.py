from connection import engine, SessionLocal
from sqlalchemy import text
import pandas as pd

# ============================================
# DATABASE CONNECTION
# ============================================




db = SessionLocal()

print("✅ EWS Engine Connected to Database")


# ============================================
# LOAD DATA FROM DATABASE
# ============================================

query = """
SELECT
    borrowers.id,
    borrowers.borrower_name,
    borrower_financials.dpd,
    borrower_financials.dscr,
    borrower_financials.revenue_decline,
    borrower_financials.cash_flow,
    risk_scores.score,
    risk_scores.classification

FROM borrowers

JOIN borrower_financials
ON borrowers.id = borrower_financials.borrower_id

JOIN risk_scores
ON borrowers.id = risk_scores.borrower_id
"""

df = pd.read_sql(query, engine)

print("\n✅ Borrower Data Loaded\n")

print(df)


# ============================================
# PROCESS EWS ALERTS
# ============================================

for index, row in df.iterrows():

    borrower_id = row["id"]

    alerts = []

    # ============================================
    # HIGH RISK ALERT
    # ============================================

    if row["score"] > 60:
        alerts.append(("High Risk Borrower", "HIGH"))

    # ============================================
    # PAYMENT DELAY ALERT
    # ============================================

    if row["dpd"] > 30:
        alerts.append(("Payment Delay", "HIGH"))

    # ============================================
    # LIQUIDITY STRESS
    # ============================================

    if row["dscr"] < 1:
        alerts.append(("Liquidity Stress", "MEDIUM"))

    # ============================================
    # BUSINESS DETERIORATION
    # ============================================

    if row["revenue_decline"] > 20:
        alerts.append(("Business Deterioration", "MEDIUM"))

    # ============================================
    # NEGATIVE CASH FLOW
    # ============================================

    if str(row["cash_flow"]).strip().lower() == "negative":
        alerts.append(("Negative Cash Flow", "HIGH"))

    # ============================================
    # INSERT ALERTS INTO DATABASE
    # ============================================

    for alert_type, severity in alerts:

        alert_query = text("""
        INSERT INTO alerts
        (borrower_id, alert_type, severity)
        VALUES
        (:borrower_id, :alert_type, :severity)
        """)

        db.execute(
            alert_query,
            {
                "borrower_id": borrower_id,
                "alert_type": alert_type,
                "severity": severity
            }
        )

        print(f"✅ Alert Generated: {alert_type}")

# ============================================
# COMMIT ALERTS
# ============================================

db.commit()

print("\n✅ All Alerts Generated Successfully")