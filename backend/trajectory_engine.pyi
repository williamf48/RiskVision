from typing import Any, Sequence

from type_contracts import (
    BorrowerAnalysis,
    DateLike,
    InterventionSummary,
    MetricAnalysis,
)


def get_metric_history(
    borrower_id: int,
    metric_code: str,
    as_of_date: DateLike | None = ...,
) -> Any: ...


def classify_condition(
    current_value: float | int | None,
    bad_direction: str,
    thresholds: dict[str, Any],
) -> dict[str, Any]: ...


def calculate_risk_velocity(
    old_value: float | int,
    new_value: float | int,
    old_date: DateLike,
    new_date: DateLike,
    bad_direction: str,
) -> tuple[
    int | None,
    float | None,
]: ...


def analyze_trajectory(
    values: Sequence[float | int],
    dates: Sequence[DateLike],
    bad_direction: str,
) -> MetricAnalysis: ...


def analyze_metric(
    borrower_id: int,
    metric_code: str,
    as_of_date: DateLike | None = ...,
) -> MetricAnalysis: ...


def build_recommended_investigations(
    metric_results: list[MetricAnalysis],
) -> list[str]: ...


def build_intervention_priority(
    analysis: BorrowerAnalysis,
) -> dict[str, Any]: ...


def analyze_borrower(
    borrower_id: int,
    as_of_date: DateLike | None = ...,
) -> BorrowerAnalysis: ...


def analyze_portfolio(
    as_of_date: DateLike | None = ...,
) -> list[BorrowerAnalysis]: ...


def summarize_portfolio_interventions(
    as_of_date: DateLike | None = ...,
) -> InterventionSummary: ...
