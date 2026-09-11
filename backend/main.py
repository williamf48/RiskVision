from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
from backtest_engine import backtest_borrower, backtest_portfolio, replay_borrower
from covenant_engine import (
    analyze_borrower_covenants,
    analyze_portfolio_covenants,
    summarize_portfolio_covenants,
)
from portfolio_analytics import analyze_portfolio_concentration
from read_models import (
    get_borrower_detail as load_borrower_detail,
    get_borrower_history_payload,
    get_borrower_identity,
    get_portfolio_summary,
    list_alerts,
    list_borrowers,
    list_legacy_watchlist,
    list_risk_scores,
    list_top_risk_accounts,
)
from trajectory_engine import (
    analyze_borrower,
    analyze_portfolio,
    summarize_portfolio_interventions,
)


app = FastAPI(
    title="RiskVision API",
    description=(
        "Credit deterioration, intervention, covenant, portfolio analytics "
        "and historical validation API"
    ),
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _require_borrower_identity(borrower_id: int) -> dict[str, Any]:
    borrower = get_borrower_identity(borrower_id)
    if borrower is None:
        raise HTTPException(status_code=404, detail="Borrower not found")
    return borrower


@app.get("/", response_model=RootResponse)
def home() -> dict[str, str]:
    return {
        "message": "RiskVision API Running",
        "version": "0.4.0",
    }


@app.get("/borrowers")
def get_borrowers() -> list[dict[str, Any]]:
    return list_borrowers()


@app.get("/borrowers/{borrower_id}")
def get_borrower_detail(borrower_id: int) -> dict[str, Any]:
    borrower = load_borrower_detail(borrower_id)
    if borrower is None:
        raise HTTPException(status_code=404, detail="Borrower not found")
    return borrower


@app.get(
    "/borrowers/{borrower_id}/deterioration",
    response_model=BorrowerDeteriorationResponse,
)
def get_borrower_deterioration(borrower_id: int) -> dict[str, Any]:
    borrower = _require_borrower_identity(borrower_id)
    result = analyze_borrower(borrower_id=borrower_id)
    result["borrower_name"] = borrower["borrower_name"]
    return result


@app.get("/borrowers/{borrower_id}/history")
def get_borrower_history(borrower_id: int) -> dict[str, Any]:
    payload = get_borrower_history_payload(borrower_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Borrower not found")
    return payload


@app.get("/borrowers/{borrower_id}/covenants")
def get_borrower_covenants(borrower_id: int) -> dict[str, Any]:
    borrower = _require_borrower_identity(borrower_id)
    result = analyze_borrower_covenants(borrower_id)
    result["borrower_name"] = borrower["borrower_name"]
    return result


@app.get("/borrowers/{borrower_id}/replay", response_model=ReplayResponse)
def borrower_replay(borrower_id: int) -> dict[str, Any]:
    try:
        return replay_borrower(borrower_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get(
    "/borrowers/{borrower_id}/backtest",
    response_model=BorrowerBacktestResponse,
)
def borrower_backtest(borrower_id: int) -> dict[str, Any]:
    try:
        return backtest_borrower(borrower_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/backtest_summary", response_model=BacktestSummaryResponse)
def backtest_summary() -> dict[str, Any]:
    return backtest_portfolio()


@app.get("/intervention_watchlist")
def intervention_watchlist() -> list[dict[str, Any]]:
    return analyze_portfolio()


@app.get("/intervention_summary", response_model=InterventionSummaryResponse)
def intervention_summary() -> dict[str, Any]:
    return summarize_portfolio_interventions()


@app.get("/covenant_watchlist")
def covenant_watchlist() -> list[dict[str, Any]]:
    return analyze_portfolio_covenants()


@app.get("/covenant_summary", response_model=CovenantSummaryResponse)
def covenant_summary() -> dict[str, Any]:
    return summarize_portfolio_covenants()


@app.get("/portfolio_analytics", response_model=PortfolioAnalyticsResponse)
def portfolio_analytics() -> dict[str, Any]:
    return analyze_portfolio_concentration()


@app.get("/risk_scores")
def get_risk_scores() -> list[dict[str, Any]]:
    return list_risk_scores()


@app.get("/alerts")
def get_alerts() -> list[dict[str, Any]]:
    return list_alerts()


@app.get("/portfolio_summary", response_model=PortfolioSummaryResponse)
def portfolio_summary() -> dict[str, Any]:
    return get_portfolio_summary()


@app.get("/watchlist")
def watchlist() -> list[dict[str, Any]]:
    return list_legacy_watchlist()


@app.get("/top_risk_accounts")
def top_risk_accounts() -> list[dict[str, Any]]:
    return list_top_risk_accounts(limit=10)


@app.get("/high_alerts")
def high_alerts() -> list[dict[str, Any]]:
    return list_alerts(severity="HIGH")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
