from typing import Any

from type_contracts import CovenantSummary


def calculate_headroom(
    actual_value: float | int,
    threshold_value: float | int,
    threshold_direction: str,
) -> float | None: ...


def classify_headroom(
    headroom_percentage: float | None,
    warning_buffer_pct: float | int = ...,
) -> str: ...


def analyze_covenant(
    covenant_id: int,
) -> dict[str, Any]: ...


def analyze_borrower_covenants(
    borrower_id: int,
) -> dict[str, Any]: ...


def analyze_portfolio_covenants(
) -> list[dict[str, Any]]: ...


def summarize_portfolio_covenants(
) -> CovenantSummary: ...
