"""Builds the dashboard roll-up — same shape for GET /dashboard and the
POST /summarize response (see frontend/src/mocks/summarizeResponse.json).
Called with no data processed yet (fresh DB), it returns the empty-state
shape the Dashboard page already knows how to render.
"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app import crud


def build_rollup(db: Session) -> dict:
    state = crud.get_or_create_sync_state(db)
    today = date.today()
    tomorrow = today + timedelta(days=1)

    return {
        "last_summarized_at": state.last_summarized_at,
        "emails_processed": state.emails_processed_total,
        "todays_tasks": crud.get_tasks_due_on(db, today),
        "tomorrows_tasks": crud.get_tasks_due_on(db, tomorrow),
        "important": crud.get_important_messages(db),
        "all_analyses": crud.get_analyses(db),
        "counts": crud.counts(db),
    }
