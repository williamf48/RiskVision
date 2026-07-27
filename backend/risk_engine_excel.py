# =========================================================
# RISK ENGINE + EXCEL PROCESSOR + POSTGRESQL INTEGRATION
# =========================================================

import pandas as pd

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# =========================================================
# DATABASE CONNECTION
# =========================================================

DATABASE_URL = "postgresql://postgres:william4256@localhost:5432/risk_platform"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

db = SessionLocal()

print("✅ Database Connected Successfully")

# =========================================================
# LOAD EXCEL FILE
# =========================================================

file_path = r"C:\Users\William\Documents\Risk Software\Book3.xlsx"

df = pd.read_excel(file_path)

print("✅ Excel File Loaded Successfully")

print("\nExcel Columns:")
print(df.columns)

# =========================================================
# CREATE EMPTY LISTS
# =========================================================

risk_scores = []
classifications = []
triggered_rules_list = []

# =========================================================
# PROCESS EACH BORROWER
# =========================================================

for index, row in df.iterrows():

    try:

        risk = 0

        triggered_rules = []

        # =========================================================
        # PARAMETER 1 — DPD
        # =========================================================

        if row["DPD"] > 30:
            risk += 30
            triggered_rules.append("DPD > 30")

        # =========================================================
        # PARAMETER 2 — DSCR
        # =========================================================

        if row["DSCR"] < 1:
            risk += 25
            triggered_rules.append("DSCR < 1")

        # =========================================================
        # PARAMETER 3 — REVENUE DECLINE
        # =========================================================

        if row["Revenue Decline %"] > 20:
            risk += 20
            triggered_rules.append("Revenue Decline > 20%")

        # =========================================================
        # PARAMETER 4 — CASH FLOW
        # =========================================================

        if str(row["Cash Flow"]).strip().lower() == "negative":
            risk += 20
            triggered_rules.append("Negative Cash Flow")

        # =========================================================
        # PARAMETER 5 — RESTRUCTURED
        # =========================================================

        if str(row["Restructured"]).strip().lower() == "yes":
            risk += 25
            triggered_rules.append("Loan Restructured")

        # =========================================================
        # CLASSIFICATION LOGIC
        # =========================================================

        if risk <= 30:
            classification = "Low Risk"

        elif risk <= 60:
            classification = "Watchlist"

        else:
            classification = "High Risk"

        # =========================================================
        # ALERT LOGIC
        # =========================================================

        if risk > 60:
            alert_status = "ALERT"
        else:
            alert_status = "NORMAL"

        # =========================================================
        # STORE RESULTS
        # =========================================================

        risk_scores.append(risk)
        classifications.append(classification)

        triggered_rules_text = ", ".join(triggered_rules)

        triggered_rules_list.append(triggered_rules_text)

        # =========================================================
        # INSERT INTO borrowers
        # =========================================================

        borrower_query = text("""
            INSERT INTO borrowers
            (borrower_name, sector, loan_amount)
            VALUES
            (:name, :sector, :loan_amount)
            RETURNING id
        """)

        borrower_result = db.execute(
            borrower_query,
            {
                "name": row["Borrower"],
                "sector": row["Sector"],
                "loan_amount": float(row["Exposure (Cr)"])
            }
        )

        borrower_id = borrower_result.fetchone()[0]

        # =========================================================
        # INSERT INTO borrower_financials
        # =========================================================

        financial_query = text("""
            INSERT INTO borrower_financials
            (
                borrower_id,
                dpd,
                dscr,
                revenue_decline,
                cash_flow,
                restructured
            )
            VALUES
            (
                :borrower_id,
                :dpd,
                :dscr,
                :revenue_decline,
                :cash_flow,
                :restructured
            )
        """)

        db.execute(
            financial_query,
            {
                "borrower_id": borrower_id,
                "dpd": int(row["DPD"]),
                "dscr": float(row["DSCR"]),
                "revenue_decline": float(row["Revenue Decline %"]),
                "cash_flow": str(row["Cash Flow"]),
                "restructured": (
                    True
                    if str(row["Restructured"]).strip().lower() == "yes"
                    else False
                )
            }
        )

        # =========================================================
        # INSERT INTO risk_scores
        # =========================================================

        score_query = text("""
            INSERT INTO risk_scores
            (
                borrower_id,
                score,
                classification
            )
            VALUES
            (
                :borrower_id,
                :score,
                :classification
            )
        """)

        db.execute(
            score_query,
            {
                "borrower_id": borrower_id,
                "score": risk,
                "classification": classification
            }
        )

        # =========================================================
        # INSERT INTO alerts
        # =========================================================

        for rule in triggered_rules:

            if "DPD" in rule:
                alert_type = "Payment Delay"
                severity = "HIGH"

            elif "DSCR" in rule:
                alert_type = "Liquidity Stress"
                severity = "MEDIUM"

            elif "Revenue" in rule:
                alert_type = "Business Deterioration"
                severity = "MEDIUM"

            elif "Negative Cash Flow" in rule:
                alert_type = "Negative Cash Flow"
                severity = "HIGH"

            elif "Restructured" in rule:
                alert_type = "High Risk Borrower"
                severity = "HIGH"

            else:
                continue

            alert_query = text("""
                INSERT INTO alerts
                (
                    borrower_id,
                    alert_type,
                    severity
                )
                VALUES
                (
                    :borrower_id,
                    :alert_type,
                    :severity
                )
            """)

            db.execute(
                alert_query,
                {
                    "borrower_id": borrower_id,
                    "alert_type": alert_type,
                    "severity": severity
                }
            )

        # =========================================================
        # INSERT INTO risk_history
        # =========================================================

        history_query = text("""
            INSERT INTO risk_history
            (
                borrower_id,
                old_score,
                new_score,
                reason
            )
            VALUES
            (
                :borrower_id,
                :old_score,
                :new_score,
                :reason
            )
        """)

        db.execute(
            history_query,
            {
                "borrower_id": borrower_id,
                "old_score": 0,
                "new_score": risk,
                "reason": triggered_rules_text
            }
        )

        print(f"✅ Processed Borrower: {row['Borrower']}")

    except Exception as e:

        print(f"\n❌ ERROR PROCESSING ROW {index}")
        print("Error:", e)

# =========================================================
# COMMIT DATABASE TRANSACTIONS
# =========================================================

db.commit()

print("\n✅ Database Updated Successfully")

# =========================================================
# ADD RESULTS TO DATAFRAME
# =========================================================

df["Risk Score"] = risk_scores
df["Classification"] = classifications
df["Triggered Rules"] = triggered_rules_list

# =========================================================
# SAVE OUTPUT FILE
# =========================================================

output_file = r"C:\Users\William\Documents\Risk Software\risk_output.xlsx"

df.to_excel(output_file, index=False)

# =========================================================
# FINAL OUTPUT
# =========================================================

print("\n===================================")
print("RISK ASSESSMENT COMPLETED")
print("===================================")

print(f"\n✅ Output File Saved As:\n{output_file}")

print("\n===================================")
print("FINAL RESULTS")
print("===================================\n")

print(df)

print("\n✅ End of Processing")