from typing import Any

from pydantic import BaseModel, ConfigDict

from type_contracts import Priority


class FlexibleModel(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )


class RootResponse(FlexibleModel):
    message: str
    version: str | int | float


class BorrowerDeteriorationResponse(
    FlexibleModel
):
    borrower_id: int
    borrower_name: str

    intervention_priority: Priority

    metrics_analyzed: int
    deteriorating_signals: int

    convergence_percentage: float

    metric_results: list[
        dict[str, Any]
    ]


class InterventionSummaryResponse(
    FlexibleModel
):
    total_borrowers: int

    urgent: int
    high: int
    medium: int
    low: int

    insufficient_data: int

    actionable_borrowers: int


class CovenantSummaryResponse(
    FlexibleModel
):
    borrowers_with_covenants: int
    borrowers_breached: int

    total_covenants: int

    borrowers_under_covenant_pressure: int


class PortfolioSummaryResponse(
    FlexibleModel
):
    total_borrowers: int
    total_exposure: float

    high_risk: int
    watchlist: int
    low_risk: int

    total_alerts: int
    high_severity_alerts: int


class PortfolioAnalyticsResponse(
    FlexibleModel
):
    portfolio_summary: dict[
        str,
        Any,
    ]


class ReplayResponse(FlexibleModel):
    borrower_id: int
    borrower_name: str

    replay_points: int

    timeline: list[
        dict[str, Any]
    ]


class BorrowerBacktestResponse(
    FlexibleModel
):
    borrower_id: int
    borrower_name: str

    stress_event_present: bool

    maximum_priority: Priority

    timeline: list[
        dict[str, Any]
    ]


class BacktestSummaryResponse(
    FlexibleModel
):
    alert_threshold: Priority

    historically_assessable_borrowers: int
    labelled_stress_events: int

    confusion_matrix: dict[
        str,
        int,
    ]

    precision: float
    recall: float
    specificity: float

    borrowers: list[
        dict[str, Any]
    ]
