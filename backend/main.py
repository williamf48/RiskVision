from api_schemas import (
    BacktestSummaryResponse,
    BorrowerBacktestResponse,
    BorrowerDeteriorationResponse,
    CovenantSummaryResponse,
    InterventionSummaryResponse,
    PortfolioAnalyticsResponse,
    PortfolioSummaryResponse,
    ReplayResponse,
    RootResponse,
)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

import pandas as pd

from connection import engine

from trajectory_engine import (
    analyze_borrower,
    analyze_portfolio,
    summarize_portfolio_interventions,
)

from covenant_engine import (
    analyze_borrower_covenants,
    analyze_portfolio_covenants,
    summarize_portfolio_covenants,
)

from portfolio_analytics import (
    analyze_portfolio_concentration,
)

from backtest_engine import (
    replay_borrower,
    backtest_borrower,
    backtest_portfolio,
)


# =========================================================
# FASTAPI INITIALIZATION
# =========================================================

app = FastAPI(
    title="RiskVision API",
    description=(
        "Credit deterioration, intervention, covenant, "
        "portfolio analytics and historical validation API"
    ),
    version="0.4.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# HOME
# =========================================================

@app.get("/", response_model=RootResponse)
def home():

    return {
        "message": "RiskVision API Running",
        "version": "0.4.0",
    }


# =========================================================
# GET ALL BORROWERS
# =========================================================

@app.get("/borrowers")
def get_borrowers():

    query = """
        SELECT
            id,
            borrower_name,
            sector,
            loan_amount,
            created_at

        FROM borrowers

        ORDER BY id
    """


    df = pd.read_sql(
        query,
        engine,
    )


    return df.to_dict(
        orient="records"
    )


# =========================================================
# GET ONE BORROWER
# =========================================================

@app.get("/borrowers/{borrower_id}")
def get_borrower_detail(
    borrower_id: int,
):

    borrower_query = text("""
        SELECT
            borrowers.id AS borrower_id,
            borrowers.borrower_name,
            borrowers.sector,
            borrowers.loan_amount,

            borrower_financials.dpd,
            borrower_financials.dscr,
            borrower_financials.revenue_decline,
            borrower_financials.cash_flow,
            borrower_financials.restructured,

            risk_scores.score,
            risk_scores.classification

        FROM borrowers

        LEFT JOIN borrower_financials
            ON borrowers.id = borrower_financials.borrower_id

        LEFT JOIN risk_scores
            ON borrowers.id = risk_scores.borrower_id

        WHERE borrowers.id = :borrower_id
    """)


    borrower_df = pd.read_sql(
        borrower_query,
        engine,
        params={
            "borrower_id": borrower_id
        },
    )


    if borrower_df.empty:

        raise HTTPException(
            status_code=404,
            detail="Borrower not found",
        )


    # -----------------------------------------------------
    # BORROWER ALERTS
    # -----------------------------------------------------

    alert_query = text("""
        SELECT
            alerts.id AS alert_id,
            alerts.alert_type,
            alerts.severity,
            alerts.created_at

        FROM alerts

        WHERE alerts.borrower_id = :borrower_id

        ORDER BY
            alerts.created_at DESC,
            alerts.id DESC
    """)


    alerts_df = pd.read_sql(
        alert_query,
        engine,
        params={
            "borrower_id": borrower_id
        },
    )


    borrower = (
        borrower_df
        .iloc[0]
        .to_dict()
    )


    borrower["alerts"] = (
        alerts_df.to_dict(
            orient="records"
        )
    )


    return borrower


# =========================================================
# BORROWER DETERIORATION INTELLIGENCE
# =========================================================

@app.get("/borrowers/{borrower_id}/deterioration", response_model=BorrowerDeteriorationResponse)
def get_borrower_deterioration(
    borrower_id: int,
):

    borrower_query = text("""
        SELECT
            id,
            borrower_name

        FROM borrowers

        WHERE id = :borrower_id
    """)


    with engine.connect() as conn:

        borrower = conn.execute(
            borrower_query,
            {
                "borrower_id": borrower_id
            },
        ).mappings().one_or_none()


    if borrower is None:

        raise HTTPException(
            status_code=404,
            detail="Borrower not found",
        )


    result = analyze_borrower(
        borrower_id=borrower_id
    )


    result["borrower_name"] = (
        borrower[
            "borrower_name"
        ]
    )


    return result


# =========================================================
# BORROWER HISTORICAL SIGNALS
# =========================================================

@app.get("/borrowers/{borrower_id}/history")
def get_borrower_history(
    borrower_id: int,
):

    borrower_query = text("""
        SELECT
            id,
            borrower_name

        FROM borrowers

        WHERE id = :borrower_id
    """)


    with engine.connect() as conn:

        borrower = conn.execute(
            borrower_query,
            {
                "borrower_id": borrower_id
            },
        ).mappings().one_or_none()


    if borrower is None:

        raise HTTPException(
            status_code=404,
            detail="Borrower not found",
        )


    history_query = text("""
        SELECT
            metric_code,
            metric_value,
            observation_date,
            period_start,
            period_end,
            reporting_frequency,
            source,
            data_quality

        FROM borrower_metric_observations

        WHERE borrower_id = :borrower_id

        ORDER BY
            metric_code,
            observation_date
    """)


    history_df = pd.read_sql(
        history_query,
        engine,
        params={
            "borrower_id": borrower_id
        },
    )


    metrics = {}


    for _, row in history_df.iterrows():

        metric_code = (
            row[
                "metric_code"
            ]
        )


        if metric_code not in metrics:

            metrics[
                metric_code
            ] = []


        observation_date = (
            pd.Timestamp(
                row[
                    "observation_date"
                ]
            )
            .strftime(
                "%Y-%m-%d"
            )
        )


        period_start = None

        if pd.notna(
            row[
                "period_start"
            ]
        ):

            period_start = (
                pd.Timestamp(
                    row[
                        "period_start"
                    ]
                )
                .strftime(
                    "%Y-%m-%d"
                )
            )


        period_end = None

        if pd.notna(
            row[
                "period_end"
            ]
        ):

            period_end = (
                pd.Timestamp(
                    row[
                        "period_end"
                    ]
                )
                .strftime(
                    "%Y-%m-%d"
                )
            )


        metrics[
            metric_code
        ].append({

            "date":
                observation_date,

            "value":
                float(
                    row[
                        "metric_value"
                    ]
                ),

            "period_start":
                period_start,

            "period_end":
                period_end,

            "reporting_frequency":
                row[
                    "reporting_frequency"
                ],

            "source":
                row[
                    "source"
                ],

            "data_quality":
                row[
                    "data_quality"
                ],
        })


    return {

        "borrower_id":
            borrower[
                "id"
            ],

        "borrower_name":
            borrower[
                "borrower_name"
            ],

        "metric_count":
            len(
                metrics
            ),

        "observation_count":
            int(
                len(
                    history_df
                )
            ),

        "metrics":
            metrics,
    }


# =========================================================
# BORROWER COVENANT INTELLIGENCE
# =========================================================

@app.get("/borrowers/{borrower_id}/covenants")
def get_borrower_covenants(
    borrower_id: int,
):

    borrower_query = text("""
        SELECT
            id,
            borrower_name

        FROM borrowers

        WHERE id = :borrower_id
    """)


    with engine.connect() as conn:

        borrower = conn.execute(
            borrower_query,
            {
                "borrower_id": borrower_id
            },
        ).mappings().one_or_none()


    if borrower is None:

        raise HTTPException(
            status_code=404,
            detail="Borrower not found",
        )


    result = (
        analyze_borrower_covenants(
            borrower_id
        )
    )


    result["borrower_name"] = (
        borrower[
            "borrower_name"
        ]
    )


    return result


# =========================================================
# HISTORICAL BORROWER REPLAY
# =========================================================

@app.get("/borrowers/{borrower_id}/replay", response_model=ReplayResponse)
def borrower_replay(
    borrower_id: int,
):
    """
    Reconstruct borrower deterioration intelligence
    across historical observation dates.

    Each replay point only uses information that was
    available on or before that date.
    """

    try:

        return replay_borrower(
            borrower_id
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# =========================================================
# BORROWER BACKTEST
# =========================================================

@app.get("/borrowers/{borrower_id}/backtest", response_model=BorrowerBacktestResponse)
def borrower_backtest(
    borrower_id: int,
):
    """
    Evaluate historical intervention-priority migration
    and lead time relative to labelled stress events.

    Current stress-event labels are synthetic
    development data.
    """

    try:

        return backtest_borrower(
            borrower_id
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# =========================================================
# PORTFOLIO BACKTEST SUMMARY
# =========================================================

@app.get("/backtest_summary", response_model=BacktestSummaryResponse)
def backtest_summary():
    """
    Return portfolio-level historical replay and
    synthetic backtesting results.

    This is development validation and must not be
    interpreted as institutional predictive validation.
    """

    return backtest_portfolio()


# =========================================================
# INTERVENTION WATCHLIST
# =========================================================

@app.get("/intervention_watchlist")
def intervention_watchlist():
    """
    Return entire portfolio ranked by explainable
    borrower intervention priority.
    """

    return analyze_portfolio()


# =========================================================
# INTERVENTION SUMMARY
# =========================================================

@app.get("/intervention_summary", response_model=InterventionSummaryResponse)
def intervention_summary():
    """
    Return portfolio-level intervention priority counts.
    """

    return (
        summarize_portfolio_interventions()
    )


# =========================================================
# PORTFOLIO COVENANT WATCHLIST
# =========================================================

@app.get("/covenant_watchlist")
def covenant_watchlist():
    """
    Return borrowers ranked by covenant-pressure status.
    """

    return (
        analyze_portfolio_covenants()
    )


# =========================================================
# PORTFOLIO COVENANT SUMMARY
# =========================================================

@app.get("/covenant_summary", response_model=CovenantSummaryResponse)
def covenant_summary():
    """
    Return portfolio-level covenant pressure counts.
    """

    return (
        summarize_portfolio_covenants()
    )


# =========================================================
# PORTFOLIO CONCENTRATION ANALYTICS
# =========================================================

@app.get("/portfolio_analytics", response_model=PortfolioAnalyticsResponse)
def portfolio_analytics():
    """
    Return portfolio exposure concentration,
    sector analytics,
    intervention concentration,
    historical coverage,
    borrower concentration,
    and covenant-pressure concentration.
    """

    return (
        analyze_portfolio_concentration()
    )


# =========================================================
# GET RISK SCORES
# =========================================================

@app.get("/risk_scores")
def get_risk_scores():

    query = """
        SELECT
            borrowers.id AS borrower_id,
            borrowers.borrower_name,
            risk_scores.score,
            risk_scores.classification

        FROM borrowers

        JOIN risk_scores
            ON borrowers.id = risk_scores.borrower_id

        ORDER BY borrowers.id
    """


    df = pd.read_sql(
        query,
        engine,
    )


    return df.to_dict(
        orient="records"
    )


# =========================================================
# GET ALL ALERTS
# =========================================================

@app.get("/alerts")
def get_alerts():

    query = """
        SELECT
            alerts.id AS alert_id,
            borrowers.id AS borrower_id,
            borrowers.borrower_name,
            alerts.alert_type,
            alerts.severity,
            alerts.created_at

        FROM alerts

        JOIN borrowers
            ON borrowers.id = alerts.borrower_id

        ORDER BY
            alerts.created_at DESC,
            alerts.id DESC
    """


    df = pd.read_sql(
        query,
        engine,
    )


    return df.to_dict(
        orient="records"
    )


# =========================================================
# PORTFOLIO SUMMARY
# =========================================================

@app.get("/portfolio_summary", response_model=PortfolioSummaryResponse)
def portfolio_summary():

    total_borrowers_query = """
        SELECT
            COUNT(*) AS total_borrowers

        FROM borrowers
    """


    total_exposure_query = """
        SELECT
            COALESCE(
                SUM(loan_amount),
                0
            ) AS total_exposure

        FROM borrowers
    """


    high_risk_query = """
        SELECT
            COUNT(*) AS high_risk

        FROM risk_scores

        WHERE classification = 'High Risk'
    """


    watchlist_query = """
        SELECT
            COUNT(*) AS watchlist

        FROM risk_scores

        WHERE classification = 'Watchlist'
    """


    low_risk_query = """
        SELECT
            COUNT(*) AS low_risk

        FROM risk_scores

        WHERE classification = 'Low Risk'
    """


    alerts_query = """
        SELECT
            COUNT(*) AS total_alerts

        FROM alerts
    """


    high_alerts_query = """
        SELECT
            COUNT(*) AS high_alerts

        FROM alerts

        WHERE severity = 'HIGH'
    """


    total_borrowers = pd.read_sql(
        total_borrowers_query,
        engine,
    )


    total_exposure = pd.read_sql(
        total_exposure_query,
        engine,
    )


    high_risk = pd.read_sql(
        high_risk_query,
        engine,
    )


    watchlist = pd.read_sql(
        watchlist_query,
        engine,
    )


    low_risk = pd.read_sql(
        low_risk_query,
        engine,
    )


    total_alerts = pd.read_sql(
        alerts_query,
        engine,
    )


    high_alerts = pd.read_sql(
        high_alerts_query,
        engine,
    )


    return {

        "total_borrowers":
            int(
                total_borrowers
                .iloc[0][
                    "total_borrowers"
                ]
            ),

        "total_exposure":
            float(
                total_exposure
                .iloc[0][
                    "total_exposure"
                ]
            ),

        "high_risk":
            int(
                high_risk
                .iloc[0][
                    "high_risk"
                ]
            ),

        "watchlist":
            int(
                watchlist
                .iloc[0][
                    "watchlist"
                ]
            ),

        "low_risk":
            int(
                low_risk
                .iloc[0][
                    "low_risk"
                ]
            ),

        "total_alerts":
            int(
                total_alerts
                .iloc[0][
                    "total_alerts"
                ]
            ),

        "high_severity_alerts":
            int(
                high_alerts
                .iloc[0][
                    "high_alerts"
                ]
            ),
    }


# =========================================================
# LEGACY SCORE-BASED WATCHLIST
# =========================================================

@app.get("/watchlist")
def watchlist():

    query = """
        SELECT
            borrowers.id AS borrower_id,
            borrowers.borrower_name,
            risk_scores.score,
            risk_scores.classification

        FROM borrowers

        JOIN risk_scores
            ON borrowers.id = risk_scores.borrower_id

        WHERE
            risk_scores.classification = 'Watchlist'

            OR

            risk_scores.classification = 'High Risk'

        ORDER BY
            risk_scores.score DESC,
            borrowers.id
    """


    df = pd.read_sql(
        query,
        engine,
    )


    return df.to_dict(
        orient="records"
    )


# =========================================================
# TOP RISK ACCOUNTS
# =========================================================

@app.get("/top_risk_accounts")
def top_risk_accounts():

    query = """
        SELECT
            borrowers.id AS borrower_id,
            borrowers.borrower_name,
            risk_scores.score,
            risk_scores.classification

        FROM borrowers

        JOIN risk_scores
            ON borrowers.id = risk_scores.borrower_id

        ORDER BY
            risk_scores.score DESC,
            borrowers.id

        LIMIT 10
    """


    df = pd.read_sql(
        query,
        engine,
    )


    return df.to_dict(
        orient="records"
    )


# =========================================================
# HIGH-SEVERITY ALERTS
# =========================================================

@app.get("/high_alerts")
def high_alerts():

    query = """
        SELECT
            alerts.id AS alert_id,
            borrowers.id AS borrower_id,
            borrowers.borrower_name,
            alerts.alert_type,
            alerts.severity,
            alerts.created_at

        FROM alerts

        JOIN borrowers
            ON borrowers.id = alerts.borrower_id

        WHERE alerts.severity = 'HIGH'

        ORDER BY
            alerts.created_at DESC,
            alerts.id DESC
    """


    df = pd.read_sql(
        query,
        engine,
    )


    return df.to_dict(
        orient="records"
    )


# =========================================================
# RUN DIRECTLY
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
    