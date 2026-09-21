"""Guardrails around the Gemini call: a pre-scan on the way in, strict
validation/sanitization on the way out. Email bodies are attacker-
controllable text pasted into an LLM prompt — the classic prompt-injection
surface — so neither side trusts the model to police itself.

Pipeline position: security.redact_pii() runs first (unconditionally), then
pre_scan() runs on the redacted body before it goes into a batch prompt,
then validate_and_sanitize() re-checks every result that comes back,
merging in the pre-scan flags regardless of what the model itself reported.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.security import redact_pii

ALLOWED_TYPES = {"important_message", "task", "meeting", "event", "fyi"}
ALLOWED_PRIORITIES = {"high", "medium", "low"}

MAX_SUMMARY_CHARS = 1000
MAX_REASON_CHARS = 500
MAX_REPLY_CHARS = 2000
MAX_TASKS_PER_EMAIL = 20
MAX_TASK_TEXT_CHARS = 500
MAX_ACTIONS_PER_TASK = 10

# Dates outside this window relative to received_at are almost certainly a
# hallucination (or a spam email's own fake urgency), not a real deadline.
_MAX_DATE_SKEW = timedelta(days=730)


class BatchIntegrityError(Exception):
    """Raised when a Gemini batch response doesn't cover the emails it was sent."""


# ---- pre-scan (runs before the prompt is built) ---------------------------

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all|any|the)?\s*(previous|prior|above)\s+instructions", re.I),
    re.compile(r"disregard\s+(all|any|the)?\s*(previous|prior|above)", re.I),
    re.compile(r"system\s+prompt", re.I),
    re.compile(r"\byou\s+are\s+now\b", re.I),
    re.compile(r"\bact\s+as\s+(a|an|my)\b", re.I),
    re.compile(r"pretend\s+(you\s+are|to\s+be)", re.I),
    re.compile(r"reveal\s+(your|the)\s+(instructions|prompt|system)", re.I),
    re.compile(r"print\s+(your|the)\s+(instructions|prompt|system)", re.I),
    re.compile(r"developer\s+mode", re.I),
    re.compile(r"\bjailbreak\b", re.I),
    re.compile(r"do\s+anything\s+now", re.I),
    re.compile(r"<\|.*?\|>"),
    re.compile(r"\[\s*system\s*\]", re.I),
    re.compile(r"new\s+instructions\s*:", re.I),
    re.compile(r"override\s+(your|the)\s+(rules|instructions)", re.I),
]

_ZERO_WIDTH_CHARS = "​‌‍⁠﻿"  # ZWSP, ZWNJ, ZWJ, WORD JOINER, BOM
_ZERO_WIDTH_RE = re.compile("[" + _ZERO_WIDTH_CHARS + "]")

_SPAM_PATTERNS = [
    re.compile(r"\bact\s+now\b", re.I),
    re.compile(r"\bclick\s+here\b", re.I),
    re.compile(r"you('|\s+ha)ve\s+won", re.I),
    re.compile(r"free\s+(cruise|money|gift|prize)", re.I),
    re.compile(r"limited\s+(time|spots)", re.I),
    re.compile(r"congratulations!+", re.I),
]


@dataclass
class PreScanFlags:
    prompt_injection_suspected: bool = False
    spam_suspected: bool = False
    notes: str = ""
    _hits: list[str] = field(default_factory=list, repr=False)


def scan_for_prompt_injection(text: str) -> list[str]:
    hits = [p.pattern for p in _INJECTION_PATTERNS if p.search(text)]
    if _ZERO_WIDTH_RE.search(text):
        hits.append("zero-width/invisible characters")
    return hits


def scan_for_spam(subject: str, body: str) -> list[str]:
    text = f"{subject}\n{body}"
    hits = [p.pattern for p in _SPAM_PATTERNS if p.search(text)]
    if text.count("!") >= 3:
        hits.append("excessive exclamation marks")
    if subject and len(subject) > 8:
        upper_ratio = sum(1 for c in subject if c.isupper()) / len(subject)
        if upper_ratio > 0.6:
            hits.append("mostly-uppercase subject")
    return hits


def pre_scan(subject: str, redacted_body: str) -> PreScanFlags:
    """Runs on the already-redacted body, before it enters a batch prompt.
    A hit does not drop the email — it still needs triage — it just forces
    the flag true in the final result no matter what the model reports."""
    injection_hits = scan_for_prompt_injection(redacted_body)
    spam_hits = scan_for_spam(subject, redacted_body)

    notes = []
    if injection_hits:
        notes.append("injection cues: " + ", ".join(injection_hits[:3]))
    if spam_hits:
        notes.append("spam cues: " + ", ".join(spam_hits[:3]))

    return PreScanFlags(
        prompt_injection_suspected=bool(injection_hits),
        spam_suspected=bool(spam_hits),
        notes="; ".join(notes),
        _hits=injection_hits + spam_hits,
    )


# ---- post-validation (runs on every batch response) ------------------------

def _looks_like_plausible_date(value: str, received_at: datetime) -> bool:
    if not value:
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return abs(parsed - received_at) <= _MAX_DATE_SKEW


def validate_and_sanitize(
    result: dict,
    source_id: str,
    received_at: datetime,
    pre_flags: PreScanFlags,
) -> dict:
    """Never trust a Gemini response just because response_schema was set —
    re-check enums, cap lengths, sanity-bound dates, and merge in the
    pre-scan guardrail flags (which the model's own self-report can't
    override, only add to)."""
    out: dict = {"source_id": source_id}

    out["type"] = result.get("type") if result.get("type") in ALLOWED_TYPES else "fyi"
    out["priority"] = (
        result.get("priority") if result.get("priority") in ALLOWED_PRIORITIES else "medium"
    )
    out["summary"] = str(result.get("summary") or "")[:MAX_SUMMARY_CHARS]
    out["priority_reason"] = str(result.get("priority_reason") or "")[:MAX_REASON_CHARS]

    # Defensive: even though the input was redacted, re-scrub the reply in
    # case the model echoes back something sensitive verbatim or invents PII.
    reply = str(result.get("suggested_reply") or "")[:MAX_REPLY_CHARS]
    out["suggested_reply"] = redact_pii(reply)
    out["tone"] = str(result.get("tone") or "")[:40]

    tasks = []
    for t in (result.get("tasks") or [])[:MAX_TASKS_PER_EMAIL]:
        if not isinstance(t, dict):
            continue
        due = t.get("due_date") or ""
        if not _looks_like_plausible_date(due, received_at):
            due = ""
        tasks.append(
            {
                "text": str(t.get("text") or "")[:MAX_TASK_TEXT_CHARS],
                "due_date": due,
                "suggested_actions": [
                    str(a)[:200] for a in (t.get("suggested_actions") or [])[:MAX_ACTIONS_PER_TASK]
                ],
            }
        )
    out["tasks"] = tasks

    event = result.get("event_details") or {}
    when = event.get("when") or ""
    out["event_details"] = {
        "when": when if _looks_like_plausible_date(when, received_at) else "",
        "where": str(event.get("where") or "")[:255],
        "notes": str(event.get("notes") or "")[:MAX_REASON_CHARS],
    }

    model_flags = result.get("flags") or {}
    out["flags"] = {
        # OR, never AND/override: pre-scan hits always win, the model can
        # only add more suspicion, never clear a flag the pre-scan raised.
        "prompt_injection_suspected": bool(
            pre_flags.prompt_injection_suspected or model_flags.get("prompt_injection_suspected")
        ),
        "spam_suspected": bool(pre_flags.spam_suspected or model_flags.get("spam_suspected")),
        "notes": pre_flags.notes or str(model_flags.get("notes") or "")[:MAX_REASON_CHARS],
    }

    return out


def check_batch_coverage(returned_ids: set[str], expected_ids: set[str]) -> None:
    """Every email sent in a batch must come back exactly once. A model that
    drops, merges, or hallucinates an id is a correctness/integrity failure,
    not something to silently paper over."""
    missing = expected_ids - returned_ids
    if missing:
        raise BatchIntegrityError(f"Gemini batch response missing results for: {sorted(missing)}")
