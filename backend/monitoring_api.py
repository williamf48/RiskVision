from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from connection import engine
from monitoring_engine import build_monitoring, policy
from case_store import CaseConflict, load_cases, load_events, save_case

router = APIRouter(prefix="/monitoring", tags=["Monitoring workspace"])


class CaseUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    expected_version: int = Field(ge=0)
    status: Literal["OPEN", "IN_REVIEW", "ESCALATED", "RESOLVED"]
    owner: str = Field(default="", max_length=80)
    actor: str = Field(min_length=2, max_length=80)
    due_date: date | None = None
    next_action: str = Field(default="", max_length=500)
    note: str = Field(min_length=10, max_length=5000)

    @model_validator(mode="after")
    def require_action(self):
        if self.status in ("IN_REVIEW", "ESCALATED") and (not self.owner or not self.due_date or len(self.next_action) < 5):
            raise ValueError("An active review requires an owner, due date, and next action.")
        if self.status == "RESOLVED" and not self.owner:
            raise ValueError("Record a review owner and a resolution rationale before closing a case.")
        return self


def workspace(as_of=None):
    try:
        result = build_monitoring(as_of)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    saved = load_cases(engine)
    for borrower in result["borrowers"]:
        record = saved.get(borrower["borrower_id"])
        borrower["case"] = record
        borrower["case_overdue"] = bool(record and record["status"] != "RESOLVED" and record["due_date"]
                                          and record["due_date"] < result["as_of"])
    result["summary"]["open_cases"] = sum(r["status"] != "RESOLVED" for r in saved.values())
    result["summary"]["overdue_cases"] = sum(b["case_overdue"] for b in result["borrowers"])
    return result


@router.get("")
def get_workspace(as_of: date | None = None):
    return workspace(as_of)


@router.get("/policy")
def get_policy():
    return policy()


@router.get("/activity")
def get_activity():
    return load_events(engine)


@router.get("/borrowers/{borrower_id}")
def get_monitoring_borrower(borrower_id: int, as_of: date | None = None):
    data = workspace(as_of)
    borrower = next((b for b in data["borrowers"] if b["borrower_id"] == borrower_id), None)
    if not borrower:
        raise HTTPException(404, "Borrower not found")
    return {**borrower, "as_of": data["as_of"], "mode": data["mode"],
            "policy_version": data["policy_version"], "events": load_events(engine, borrower_id)}


@router.put("/borrowers/{borrower_id}/case")
def update_case(borrower_id: int, body: CaseUpdate, as_of: date | None = None):
    data = get_monitoring_borrower(borrower_id, as_of)
    evidence = {key: data[key] for key in ("as_of", "policy_version", "priority", "drivers", "data_issues",
                                         "fresh_metrics", "metrics", "covenants")}
    try:
        result = save_case(engine, borrower_id, body.model_dump(mode="json"), evidence)
    except CaseConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"case": result, "events": load_events(engine, borrower_id)}
