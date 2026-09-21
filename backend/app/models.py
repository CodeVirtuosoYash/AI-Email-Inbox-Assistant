"""SQLAlchemy 2.0 models — see email_assistant_design.md §3/§4 for the ER diagram."""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ---- enums -----------------------------------------------------------
class Category(str, PyEnum):
    IMPORTANT_MESSAGE = "important_message"
    TASK = "task"
    MEETING = "meeting"
    EVENT = "event"
    FYI = "fyi"


class Priority(str, PyEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, PyEnum):
    PENDING = "pending"
    DONE = "done"


# ---- tables ----------------------------------------------------------
class SyncState(Base):
    """Single row (id=1). Holds the incremental watermark for the local inbox."""

    __tablename__ = "sync_state"
    id: Mapped[int] = mapped_column(primary_key=True)
    last_summarized_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    emails_processed_total: Mapped[int] = mapped_column(default=0)


class Email(Base):
    __tablename__ = "emails"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    sender: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime, index=True)  # watermark key
    ingested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    analysis: Mapped[Optional["Analysis"]] = relationship(
        back_populates="email", uselist=False, cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="email", cascade="all, delete-orphan"
    )
    reply: Mapped[Optional["Reply"]] = relationship(
        back_populates="email", uselist=False, cascade="all, delete-orphan"
    )


class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[int] = mapped_column(primary_key=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("emails.id"), unique=True)
    summary: Mapped[str] = mapped_column(Text)
    category: Mapped[Category] = mapped_column(Enum(Category), index=True)
    priority: Mapped[Priority] = mapped_column(Enum(Priority))
    priority_reason: Mapped[str] = mapped_column(Text)
    # populated only when category is "meeting" or "event"
    event_when: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    event_where: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    event_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # guardrail metadata carried over from the Gemini batch response (see §5b)
    prompt_injection_suspected: Mapped[bool] = mapped_column(default=False)
    spam_suspected: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    email: Mapped["Email"] = relationship(back_populates="analysis")


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("emails.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    suggested_actions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # list[str]
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    email: Mapped["Email"] = relationship(back_populates="tasks")


class Reply(Base):
    __tablename__ = "replies"
    id: Mapped[int] = mapped_column(primary_key=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("emails.id"), unique=True)
    suggested_reply: Mapped[str] = mapped_column(Text)
    tone: Mapped[str] = mapped_column(String(40), default="friendly")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    email: Mapped["Email"] = relationship(back_populates="reply")
