"""Persistent single-workspace case journal with optimistic concurrency control.

Actor labels are user-entered; this is not authenticated, tamper-proof audit storage.
No outbound notifications or automated credit decisions are performed.
"""
from datetime import datetime, timezone
import json

from sqlalchemy import Column, Integer, MetaData, Table, Text, select, update
from sqlalchemy.exc import IntegrityError

metadata = MetaData()
cases = Table("monitoring_cases", metadata,
              Column("borrower_id", Integer, primary_key=True), Column("version", Integer, nullable=False),
              Column("status", Text, nullable=False), Column("owner", Text, nullable=False),
              Column("due_date", Text), Column("next_action", Text, nullable=False),
              Column("note", Text, nullable=False), Column("updated_at", Text, nullable=False))
events = Table("monitoring_case_events", metadata,
               Column("id", Integer, primary_key=True), Column("borrower_id", Integer, nullable=False),
               Column("version", Integer, nullable=False), Column("actor", Text, nullable=False),
               Column("recorded_at", Text, nullable=False), Column("before_json", Text, nullable=False),
               Column("after_json", Text, nullable=False), Column("evidence_json", Text, nullable=False))


class CaseConflict(Exception):
    pass


def initialize(db):
    metadata.create_all(db)


def load_cases(db):
    with db.connect() as conn:
        return {r["borrower_id"]: dict(r) for r in conn.execute(select(cases)).mappings()}


def load_events(db, borrower_id=None, limit=100):
    query = select(events)
    if borrower_id is not None:
        query = query.where(events.c.borrower_id == borrower_id)
    with db.connect() as conn:
        rows = conn.execute(query.order_by(events.c.id.desc()).limit(limit)).mappings()
        return [{"id": r["id"], "borrower_id": r["borrower_id"], "version": r["version"],
                 "actor": r["actor"], "recorded_at": r["recorded_at"],
                 "before": json.loads(r["before_json"]), "after": json.loads(r["after_json"]),
                 "evidence": json.loads(r["evidence_json"])} for r in rows]


def save_case(db, borrower_id, values, evidence):
    expected = values["expected_version"]
    now = datetime.now(timezone.utc).isoformat()
    row = {"borrower_id": borrower_id, "version": expected + 1,
           **{key: values[key] for key in ("status", "owner", "due_date", "next_action", "note")}, "updated_at": now}
    try:
        with db.begin() as conn:
            current = conn.execute(select(cases).where(cases.c.borrower_id == borrower_id)).mappings().first()
            before = dict(current) if current else {}
            if (current and current["version"] != expected) or (not current and expected != 0):
                raise CaseConflict("This case changed in another window. Reload the case before saving.")
            if current:
                result = conn.execute(update(cases).where(cases.c.borrower_id == borrower_id,
                                                         cases.c.version == expected).values(**row))
                if result.rowcount != 1:
                    raise CaseConflict("This case changed in another window. Reload the case before saving.")
            else:
                conn.execute(cases.insert().values(**row))
            conn.execute(events.insert().values(borrower_id=borrower_id, version=row["version"],
                         actor=values["actor"], recorded_at=now, before_json=json.dumps(before),
                         after_json=json.dumps(row), evidence_json=json.dumps(evidence, allow_nan=False)))
    except IntegrityError as exc:
        raise CaseConflict("Another review was saved first. Reload the case before saving.") from exc
    return row
