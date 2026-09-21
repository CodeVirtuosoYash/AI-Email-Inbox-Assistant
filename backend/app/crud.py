"""Persistence helpers + response serializers.

Serializers return plain dicts that flatten Email fields (subject, sender,
received_at) onto Analysis/Task rows — that's the shape the frontend expects
(see frontend/src/mocks/summarizeResponse.json), not something any single
ORM model represents on its own.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Analysis, Category, Email, Priority, Reply, SyncState, Task, TaskStatus

SYNC_STATE_ID = 1


# ---- sync state / watermark --------------------------------------------

def get_or_create_sync_state(db: Session) -> SyncState:
    state = db.get(SyncState, SYNC_STATE_ID)
    if state is None:
        state = SyncState(id=SYNC_STATE_ID)
        db.add(state)
        db.flush()
    return state


# ---- emails ---------------------------------------------------------------

def email_exists(db: Session, source_id: str) -> bool:
    return db.scalar(select(Email.id).where(Email.source_id == source_id)) is not None


def insert_email(db: Session, raw: dict) -> Email:
    email = Email(
        source_id=raw["source_id"],
        sender=raw["sender"],
        subject=raw["subject"],
        body=raw["body"],
        received_at=datetime.fromisoformat(raw["received_at"]),
    )
    db.add(email)
    db.flush()  # assigns email.id without committing the transaction
    return email


# ---- analyses / tasks / replies -------------------------------------------

def _parse_flexible_date(value: str) -> date | None:
    """LLM dates may come back as a bare date or a full datetime; either way
    we only ever store the date part (Task.due_date is a Date column, and
    the frontend calendar keys strictly on "YYYY-MM-DD")."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def save_analysis(db: Session, email: Email, result: dict) -> Analysis:
    event_details = result.get("event_details") or {}
    flags = result.get("flags") or {}
    analysis = Analysis(
        email_id=email.id,
        summary=result["summary"],
        category=Category(result["type"]),
        priority=Priority(result["priority"]),
        priority_reason=result["priority_reason"],
        event_when=event_details.get("when") or None,
        event_where=event_details.get("where") or None,
        event_notes=event_details.get("notes") or None,
        prompt_injection_suspected=bool(flags.get("prompt_injection_suspected")),
        spam_suspected=bool(flags.get("spam_suspected")),
    )
    db.add(analysis)
    db.flush()
    return analysis


def save_reply(db: Session, email: Email, suggested_reply: str, tone: str) -> Reply:
    reply = Reply(email_id=email.id, suggested_reply=suggested_reply, tone=tone or "friendly")
    db.add(reply)
    db.flush()
    return reply


def save_task(db: Session, email: Email, task: dict) -> Task:
    row = Task(
        email_id=email.id,
        text=task["text"],
        due_date=_parse_flexible_date(task.get("due_date") or ""),
        suggested_actions=task.get("suggested_actions") or [],
    )
    db.add(row)
    db.flush()
    return row


def save_event_task(db: Session, email: Email, result: dict) -> Task:
    """Meetings/events have deadlines too — synthesize a Task row so they
    surface on the Tasks/Calendar pages the same way action items do."""
    event_details = result.get("event_details") or {}
    label = "Meeting" if result["type"] == "meeting" else "Event"
    actions = []
    if event_details.get("where"):
        actions.append(f"Location: {event_details['where']}")
    if event_details.get("notes"):
        actions.append(event_details["notes"])
    row = Task(
        email_id=email.id,
        text=f"{label}: {email.subject}",
        due_date=_parse_flexible_date(event_details.get("when") or ""),
        suggested_actions=actions,
    )
    db.add(row)
    db.flush()
    return row


# ---- serializers (Email fields flattened onto the response dict) ----------

def task_to_dict(task: Task) -> dict:
    return {
        "id": task.id,
        "email_id": task.email_id,
        "text": task.text,
        "due_date": task.due_date,
        "suggested_actions": task.suggested_actions or [],
        "status": task.status,
        "email_subject": task.email.subject,
        "email_sender": task.email.sender,
    }


def analysis_to_dict(analysis: Analysis) -> dict:
    out = {
        "id": analysis.id,
        "email_id": analysis.email_id,
        "summary": analysis.summary,
        "category": analysis.category,
        "priority": analysis.priority,
        "priority_reason": analysis.priority_reason,
        "email_subject": analysis.email.subject,
        "email_sender": analysis.email.sender,
        "email_received_at": analysis.email.received_at,
        "flags": {
            "prompt_injection_suspected": analysis.prompt_injection_suspected,
            "spam_suspected": analysis.spam_suspected,
        },
    }
    if analysis.category in (Category.MEETING, Category.EVENT):
        out["event_details"] = {
            "when": analysis.event_when,
            "where": analysis.event_where,
            "notes": analysis.event_notes,
        }
    reply = analysis.email.reply
    if reply is not None:
        out["suggested_reply"] = reply.suggested_reply
        out["tone"] = reply.tone
    return out


def reply_to_dict(reply: Reply) -> dict:
    return {
        # keyed by email_id, not Reply.id — matches how the frontend calls
        # POST /replies/{id}/regenerate with emailId (see ReplyEditor.jsx)
        "id": reply.email_id,
        "email_id": reply.email_id,
        "email_subject": reply.email.subject,
        "email_sender": reply.email.sender,
        "suggested_reply": reply.suggested_reply,
        "tone": reply.tone,
    }


# ---- queries ---------------------------------------------------------------

def get_tasks(db: Session) -> list[dict]:
    tasks = db.scalars(select(Task).order_by(Task.due_date.is_(None), Task.due_date, Task.id)).all()
    return [task_to_dict(t) for t in tasks]


def get_task(db: Session, task_id: int) -> Task | None:
    return db.get(Task, task_id)


def update_task_status(db: Session, task_id: int, status: str) -> Task | None:
    task = db.get(Task, task_id)
    if task is None:
        return None
    task.status = TaskStatus(status)
    db.flush()
    return task


def get_tasks_due_on(db: Session, day: date) -> list[dict]:
    tasks = db.scalars(
        select(Task).where(Task.due_date == day, Task.status == TaskStatus.PENDING).order_by(Task.id)
    ).all()
    return [task_to_dict(t) for t in tasks]


def get_analyses(db: Session) -> list[dict]:
    analyses = db.scalars(select(Analysis).order_by(Analysis.id)).all()
    return [analysis_to_dict(a) for a in analyses]


def get_important_messages(db: Session) -> list[dict]:
    priority_rank = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
    analyses = db.scalars(
        select(Analysis).where(Analysis.category == Category.IMPORTANT_MESSAGE)
    ).all()
    ordered = sorted(analyses, key=lambda a: priority_rank.get(a.priority, 3))
    return [analysis_to_dict(a) for a in ordered]


def get_replies(db: Session) -> list[dict]:
    replies = db.scalars(select(Reply).order_by(Reply.id)).all()
    return [reply_to_dict(r) for r in replies]


def get_reply_by_email_id(db: Session, email_id: int) -> Reply | None:
    return db.scalar(select(Reply).where(Reply.email_id == email_id))


def get_email(db: Session, email_id: int) -> Email | None:
    return db.get(Email, email_id)


def upsert_reply(db: Session, email: Email, suggested_reply: str, tone: str) -> Reply:
    existing = get_reply_by_email_id(db, email.id)
    if existing is not None:
        existing.suggested_reply = suggested_reply
        existing.tone = tone
        db.flush()
        return existing
    return save_reply(db, email, suggested_reply, tone)


def counts(db: Session) -> dict:
    categories = db.scalars(select(Analysis.category)).all()
    pending_tasks = db.scalar(
        select(func.count()).select_from(Task).where(Task.status == TaskStatus.PENDING)
    )
    return {
        "messages": sum(1 for c in categories if c == Category.IMPORTANT_MESSAGE),
        "tasks": pending_tasks or 0,
        "fyi": sum(1 for c in categories if c == Category.FYI),
    }
