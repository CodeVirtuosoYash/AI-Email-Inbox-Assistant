"""Orchestrates one /summarize run — see email_assistant_design.md §1 and §6.

Watermark safety: the watermark only advances past emails that were
*successfully* analyzed. If a batch fails, the watermark is capped just
before the earliest email in that failed batch, so those emails remain
`received_at > watermark` and get retried on the next run — while emails
that succeeded (even ones timestamped after a failure elsewhere) are already
in the DB, so the `email_exists` dedup guard keeps them from being
reprocessed even though the watermark didn't move past them.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app import crud
from app.services.gemini_client import analyze_emails
from app.services.ingest import load_emails_from_file, to_email_inputs
from app.services.rollup import build_rollup


def _new_raw_emails(db: Session, watermark: datetime | None) -> list[dict]:
    raw = load_emails_from_file()
    return [
        e
        for e in raw
        if (watermark is None or datetime.fromisoformat(e["received_at"]) > watermark)
        and not crud.email_exists(db, e["source_id"])
    ]


def _next_watermark(
    watermark: datetime | None,
    results: dict[str, dict],
    failures: list,
    raw_by_id: dict[str, dict],
) -> datetime | None:
    success_ts = [datetime.fromisoformat(raw_by_id[sid]["received_at"]) for sid in results]
    if not success_ts:
        return watermark

    candidate = max(success_ts)
    if failures:
        failure_ts = [
            datetime.fromisoformat(raw_by_id[sid]["received_at"])
            for f in failures
            for sid in f.source_ids
        ]
        earliest_failure = min(failure_ts)
        eligible = [t for t in success_ts if t < earliest_failure]
        candidate = max(eligible) if eligible else watermark

    if watermark is not None:
        return max(candidate, watermark) if candidate is not None else watermark
    return candidate


def _apply_result(db: Session, email, result: dict) -> None:
    crud.save_analysis(db, email, result)

    if result["type"] == "important_message" and result.get("suggested_reply"):
        crud.save_reply(db, email, result["suggested_reply"], result.get("tone") or "friendly")

    for task in result.get("tasks", []):
        crud.save_task(db, email, task)

    if result["type"] in ("meeting", "event"):
        crud.save_event_task(db, email, result)


def summarize(db: Session) -> tuple[dict, list]:
    """Returns (dashboard_rollup, failures) — failures is empty on a clean run."""
    state = crud.get_or_create_sync_state(db)
    watermark = state.last_summarized_at

    new_raw = _new_raw_emails(db, watermark)
    if not new_raw:
        return build_rollup(db), []

    raw_by_id = {e["source_id"]: e for e in new_raw}
    inputs = to_email_inputs(new_raw)  # redact_pii() + guardrail pre_scan() per email
    results, failures = analyze_emails(inputs)

    processed = 0
    for source_id, result in results.items():
        email = crud.insert_email(db, raw_by_id[source_id])
        _apply_result(db, email, result)
        processed += 1

    state.last_summarized_at = _next_watermark(watermark, results, failures, raw_by_id)
    state.last_run_at = datetime.utcnow()
    state.emails_processed_total += processed
    db.commit()

    return build_rollup(db), failures
