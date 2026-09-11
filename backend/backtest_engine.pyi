from typing import Any

from type_contracts import (
    BacktestSummary,
    BorrowerBacktest,
    Priority,
    ReplayResult,
)


def get_borrower(
    borrower_id: int,
) -> dict[str, Any] | None: ...


def get_historically_assessable_borrowers(
) -> list[dict[str, Any]]: ...


def get_replay_dates(
    borrower_id: int,
) -> list[Any]: ...


def get_stress_events(
    borrower_id: int,
) -> list[dict[str, Any]]: ...


def first_priority_date(
    timeline: list[dict[str, Any]],
    minimum_priority: Priority,
) -> str | None: ...


def get_max_priority(
    timeline: list[dict[str, Any]],
) -> Any: ...


def replay_borrower(
    borrower_id: int,
) -> ReplayResult: ...


def backtest_borrower(
    borrower_id: int,
    alert_threshold: Priority = ...,
) -> BorrowerBacktest: ...


def backtest_portfolio(
    alert_threshold: Priority = ...,
) -> BacktestSummary: ...
