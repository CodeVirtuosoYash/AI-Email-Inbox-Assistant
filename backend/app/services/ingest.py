"""Bridges the local demo inbox (data/emails.json) to the LLM stage.

Pipeline: load raw JSON -> redact_pii() on every body -> guardrail pre_scan()
on the redacted body -> wrap as EmailInput, ready for
gemini_client.analyze_emails(). PII redaction is unconditional; nothing
reaches a prompt without going through it first.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

from app.config import EMAIL_FILE
from app.guardrails import pre_scan
from app.security import redact_pii
from app.services.gemini_client import EmailInput


def load_emails_from_file(path: Path = EMAIL_FILE) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def to_email_inputs(raw_emails: Iterable[dict]) -> list[EmailInput]:
    inputs = []
    for e in raw_emails:
        clean_body = redact_pii(e["body"])
        flags = pre_scan(e["subject"], clean_body)
        inputs.append(
            EmailInput(
                source_id=e["source_id"],
                subject=e["subject"],
                body=clean_body,
                received_at=datetime.fromisoformat(e["received_at"]),
                pre_flags=flags,
            )
        )
    return inputs
