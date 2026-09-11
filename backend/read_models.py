from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import text

from connection import engine


JsonRecord = dict[str, Any]


def list_borrowers() -> list[JsonRecord]:
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

    return pd.read_sql(query, engine).to_dict(orient="records")


def get_borrower_identity(borrower_id: int) -> JsonRecord | None:
    query = text("""
        SELECT id, borrower_name
        FROM borrowers
        WHERE id = :borrower_id
    """)

    with engine.connect() as conn:
        row = conn.execute(
            query,
            {"borrower_id": borrower_id},
        ).mappings().one_or_none()

    return dict(row) if row is not None else None


def get_borrower_detail(borrower_id: int) -> JsonRecord | None:
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
        params={"borrower_id": borrower_id},
    )

    if borrower_df.empty:
        return None

    alerts_query = text("""
        SELECT
            alerts.id AS alert_id,
            alerts.alert_type,
            alerts.severity,
            alerts.created_at
        FROM alerts
        WHERE alerts.borrower_id = :borrower_id
        ORDER BY alerts.created_at DESC, alerts.id DESC
    """)

    alerts_df = pd.read_sql(
        alerts_query,
        engine,
        params={"borrower_id": borrower_id},
    )

    borrower = borrower_df.iloc[0].to_dict()
    borrower["alerts"] = alerts_df.to_dict(orient="records")
    return borrower


def get_borrower_history_payload(borrower_id: int) -> JsonRecord | None:
    borrower = get_borrower_identity(borrower_id)
    if borrower is None:
        return None

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
        ORDER BY metric_code, observation_date
    """)

    history_df = pd.read_sql(
        history_query,
        engine,
        params={"borrower_id": borrower_id},
    )

    metrics: dict[str, list[JsonRecord]] = {}

    for _, row in history_df.iterrows():
        metric_code = str(row["metric_code"])
        metrics.setdefault(metric_code, [])

        period_start = (
            pd.Timestamp(row["period_start"]).strftime("%Y-%m-%d")
            if pd.notna(row["period_start"])
            else None
        )
        period_end = (
            pd.Timestamp(row["period_end"]).strftime("%Y-%m-%d")
            if pd.notna(row["period_end"])
            else None
        )

        metrics[metric_code].append(
            {
                "date": pd.Timestamp(row["observation_date"]).strftime("%Y-%m-%d"),
                "value": float(row["metric_value"]),
                "period_start": period_start,
                "period_end": period_end,
                "reporting_frequency": row["reporting_frequency"],
                "source": row["source"],
                "data_quality": row["data_quality"],
            }
        )

    return {
        "borrower_id": borrower["id"],
        "borrower_name": borrower["borrower_name"],
        "metric_count": len(metrics),
        "observation_count": int(len(history_df)),
        "metrics": metrics,
    }


def list_risk_scores() -> list[JsonRecord]:
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
    return pd.read_sql(query, engine).to_dict(orient="records")


def list_alerts(severity: str | None = None) -> list[JsonRecord]:
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
    """
    params: dict[str, Any] = {}

    if severity is not None:
        query += " WHERE alerts.severity = %(severity)s"
        params["severity"] = severity

    query += " ORDER BY alerts.created_at DESC, alerts.id DESC"

    return pd.read_sql(query, engine, params=params).to_dict(orient="records")


def get_portfolio_summary() -> JsonRecord:
    query = text("""
        SELECT
            (SELECT COUNT(*) FROM borrowers) AS total_borrowers,
            (SELECT COALESCE(SUM(loan_amount), 0) FROM borrowers) AS total_exposure,
            (SELECT COUNT(*) FROM risk_scores WHERE classification = 'High Risk') AS high_risk,
            (SELECT COUNT(*) FROM risk_scores WHERE classification = 'Watchlist') AS watchlist,
            (SELECT COUNT(*) FROM risk_scores WHERE classification = 'Low Risk') AS low_risk,
            (SELECT COUNT(*) FROM alerts) AS total_alerts,
            (SELECT COUNT(*) FROM alerts WHERE severity = 'HIGH') AS high_severity_alerts
    """)

    with engine.connect() as conn:
        row = conn.execute(query).mappings().one()

    return {
        "total_borrowers": int(row["total_borrowers"]),
        "total_exposure": float(row["total_exposure"]),
        "high_risk": int(row["high_risk"]),
        "watchlist": int(row["watchlist"]),
        "low_risk": int(row["low_risk"]),
        "total_alerts": int(row["total_alerts"]),
        "high_severity_alerts": int(row["high_severity_alerts"]),
    }


def list_legacy_watchlist() -> list[JsonRecord]:
    query = """
        SELECT
            borrowers.id AS borrower_id,
            borrowers.borrower_name,
            risk_scores.score,
            risk_scores.classification
        FROM borrowers
        JOIN risk_scores
            ON borrowers.id = risk_scores.borrower_id
        WHERE risk_scores.classification IN ('Watchlist', 'High Risk')
        ORDER BY risk_scores.score DESC, borrowers.id
    """
    return pd.read_sql(query, engine).to_dict(orient="records")


def list_top_risk_accounts(limit: int = 10) -> list[JsonRecord]:
    query = text("""
        SELECT
            borrowers.id AS borrower_id,
            borrowers.borrower_name,
            risk_scores.score,
            risk_scores.classification
        FROM borrowers
        JOIN risk_scores
            ON borrowers.id = risk_scores.borrower_id
        ORDER BY risk_scores.score DESC, borrowers.id
        LIMIT :limit
    """)

    return pd.read_sql(
        query,
        engine,
        params={"limit": limit},
    ).to_dict(orient="records")
