from datetime import date, datetime
from typing import Any, Literal, TypedDict


DateLike = str | date | datetime

Priority = Literal[
    "INSUFFICIENT_DATA",
    "LOW",
    "MEDIUM",
    "HIGH",
    "URGENT",
]

TrajectoryDirection = Literal[
    "INSUFFICIENT_HISTORY",
    "STABLE",
    "IMPROVING",
    "DETERIORATING",
]

Condition = Literal[
    "INSUFFICIENT_DATA",
    "HEALTHY",
    "WATCH",
    "WEAK",
    "CRITICAL",
]

AccelerationDirection = Literal[
    "INSUFFICIENT_HISTORY",
    "STEADY",
    "ACCELERATING",
    "DECELERATING",
]


class MetricAnalysis(TypedDict, total=False):
    borrower_id: int
    metric_code: str
    bad_direction: str

    observations: int

    current_value: float | None
    previous_value: float | None

    absolute_change: float | None
    percentage_change: float | None

    days_since_previous: int | None

    direction: TrajectoryDirection
    persistence: int

    risk_velocity_30d: float | None
    previous_risk_velocity_30d: float | None
    velocity_change_30d: float | None

    acceleration_direction: AccelerationDirection

    condition: Condition
    condition_severity: int | None


class BorrowerAnalysis(TypedDict, total=False):
    borrower_id: int
    borrower_name: str
    as_of_date: str | None

    configured_metrics: int
    metrics_analyzed: int

    deteriorating_signals: int
    improving_signals: int
    stable_signals: int
    insufficient_history_signals: int

    persistent_deterioration_signals: int
    accelerating_deterioration_signals: int
    decelerating_deterioration_signals: int

    critical_condition_signals: int
    weak_condition_signals: int
    watch_condition_signals: int
    healthy_condition_signals: int

    convergence_ratio: float
    convergence_percentage: float

    intervention_priority: Priority
    priority_rank: int

    reason_codes: list[str]
    explanations: list[str]
    recommended_investigations: list[str]

    metric_results: list[MetricAnalysis]

    portfolio_rank: int


class InterventionSummary(TypedDict):
    total_borrowers: int
    urgent: int
    high: int
    medium: int
    low: int
    insufficient_data: int
    actionable_borrowers: int


class CovenantSummary(TypedDict, total=False):
    borrowers_with_covenants: int
    borrowers_breached: int
    borrowers_near_breach: int
    borrowers_tight: int
    borrowers_healthy: int
    borrowers_insufficient_data: int

    total_covenants: int
    breached_covenants: int
    near_breach_covenants: int
    tight_covenants: int
    healthy_covenants: int
    untested_covenants: int

    borrowers_under_covenant_pressure: int


class PortfolioAnalytics(TypedDict, total=False):
    portfolio_summary: dict[str, Any]
    sector_analytics: list[dict[str, Any]]
    borrower_concentration: list[dict[str, Any]]


class ReplayPoint(TypedDict, total=False):
    as_of_date: str

    intervention_priority: Priority
    priority_rank: int

    metrics_analyzed: int
    deteriorating_signals: int
    critical_condition_signals: int
    weak_condition_signals: int

    persistent_deterioration_signals: int
    accelerating_deterioration_signals: int

    convergence_percentage: float
    reason_codes: list[str]


class ReplayResult(TypedDict, total=False):
    borrower_id: int
    borrower_name: str
    replay_points: int
    timeline: list[ReplayPoint]


class BorrowerBacktest(TypedDict, total=False):
    borrower_id: int
    borrower_name: str

    alert_threshold: Priority

    replay_points: int

    stress_event_present: bool
    stress_events: list[dict[str, Any]]

    first_medium_date: str | None
    first_high_date: str | None
    first_urgent_date: str | None
    first_alert_date: str | None

    lead_time_days: int | None

    maximum_priority: Priority
    maximum_priority_date: str | None
    maximum_convergence_percentage: float

    timeline: list[ReplayPoint]


class BacktestSummary(TypedDict, total=False):
    alert_threshold: Priority

    historically_assessable_borrowers: int
    labelled_stress_events: int

    confusion_matrix: dict[str, int]

    precision: float
    recall: float
    specificity: float

    average_lead_time_days: float | None

    borrowers: list[BorrowerBacktest]
