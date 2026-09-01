from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from connection import engine
import pandas as pd

# ============================================
# FASTAPI INITIALIZATION
# ============================================

app = FastAPI()

# ============================================
# CORS CONFIGURATION
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# HOME ROUTE
# ============================================

@app.get("/")
def home():

    return {
        "message": "Risk Platform Running"
    }

# ============================================
# GET ALL BORROWERS
# ============================================

@app.get("/borrowers")
def get_borrowers():

    query = """
    SELECT * FROM borrowers
    """

    df = pd.read_sql(query, engine)

    return df.to_dict(orient="records")

# ============================================
# GET RISK SCORES
# ============================================

@app.get("/risk_scores")
def get_risk_scores():

    query = """
    SELECT
        borrowers.borrower_name,
        risk_scores.score,
        risk_scores.classification

    FROM borrowers

    JOIN risk_scores
    ON borrowers.id = risk_scores.borrower_id
    """

    df = pd.read_sql(query, engine)

    return df.to_dict(orient="records")

# ============================================
# GET ALERTS
# ============================================

@app.get("/alerts")
def get_alerts():

    query = """
    SELECT
        borrowers.borrower_name,
        alerts.alert_type,
        alerts.severity,
        alerts.created_at

    FROM alerts

    JOIN borrowers
    ON borrowers.id = alerts.borrower_id
    """

    df = pd.read_sql(query, engine)

    return df.to_dict(orient="records")

# ============================================
# PORTFOLIO SUMMARY API
# ============================================

@app.get("/portfolio_summary")
def portfolio_summary():

    total_borrowers_query = """
    SELECT COUNT(*) AS total_borrowers
    FROM borrowers
    """

    high_risk_query = """
    SELECT COUNT(*) AS high_risk
    FROM risk_scores
    WHERE classification = 'High Risk'
    """

    watchlist_query = """
    SELECT COUNT(*) AS watchlist
    FROM risk_scores
    WHERE classification = 'Watchlist'
    """

    low_risk_query = """
    SELECT COUNT(*) AS low_risk
    FROM risk_scores
    WHERE classification = 'Low Risk'
    """

    alerts_query = """
    SELECT COUNT(*) AS total_alerts
    FROM alerts
    """

    high_alerts_query = """
    SELECT COUNT(*) AS high_alerts
    FROM alerts
    WHERE severity = 'HIGH'
    """

    total_borrowers = pd.read_sql(total_borrowers_query, engine)

    high_risk = pd.read_sql(high_risk_query, engine)

    watchlist = pd.read_sql(watchlist_query, engine)

    low_risk = pd.read_sql(low_risk_query, engine)

    total_alerts = pd.read_sql(alerts_query, engine)

    high_alerts = pd.read_sql(high_alerts_query, engine)

    return {

        "total_borrowers":
            int(total_borrowers.iloc[0]["total_borrowers"]),

        "high_risk":
            int(high_risk.iloc[0]["high_risk"]),

        "watchlist":
            int(watchlist.iloc[0]["watchlist"]),

        "low_risk":
            int(low_risk.iloc[0]["low_risk"]),

        "total_alerts":
            int(total_alerts.iloc[0]["total_alerts"]),

        "high_severity_alerts":
            int(high_alerts.iloc[0]["high_alerts"])
    }

# ============================================
# WATCHLIST API
# ============================================

@app.get("/watchlist")
def watchlist():

    query = """
    SELECT
        borrowers.borrower_name,
        risk_scores.score,
        risk_scores.classification

    FROM borrowers

    JOIN risk_scores
    ON borrowers.id = risk_scores.borrower_id

    WHERE risk_scores.classification = 'Watchlist'
       OR risk_scores.classification = 'High Risk'
    """

    df = pd.read_sql(query, engine)

    return df.to_dict(orient="records")

# ============================================
# TOP RISK ACCOUNTS API
# ============================================

@app.get("/top_risk_accounts")
def top_risk_accounts():

    query = """
    SELECT
        borrowers.borrower_name,
        risk_scores.score,
        risk_scores.classification

    FROM borrowers

    JOIN risk_scores
    ON borrowers.id = risk_scores.borrower_id

    ORDER BY risk_scores.score DESC
    LIMIT 10
    """

    df = pd.read_sql(query, engine)

    return df.to_dict(orient="records")

# ============================================
# HIGH SEVERITY ALERTS API
# ============================================

@app.get("/high_alerts")
def high_alerts():

    query = """
    SELECT
        borrowers.borrower_name,
        alerts.alert_type,
        alerts.severity,
        alerts.created_at

    FROM alerts

    JOIN borrowers
    ON borrowers.id = alerts.borrower_id

    WHERE alerts.severity = 'HIGH'
    """

    df = pd.read_sql(query, engine)

    return df.to_dict(orient="records")