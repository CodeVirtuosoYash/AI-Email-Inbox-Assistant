"""Regex-based PII scrubbing.

Runs on every email body BEFORE it is ever assembled into a Gemini prompt —
this is unconditional and happens regardless of what the guardrail pre-scan
(app/guardrails.py) finds. Order matters: patterns that are strict subsets
of a looser one (e.g. a 10-digit phone number inside a 16-digit card number)
are matched first so they can't be partially eaten by a later pattern.
"""
from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

# SSN-shaped (123-45-6789) before the looser card/phone patterns below.
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# 13-19 digits, optionally grouped with spaces/dashes — covers most card PANs.
_CARD_RE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")

_ACCOUNT_RE = re.compile(
    r"\b(?:account|acct)\s*(?:#|no\.?|number)?\s*[:#]?\s*\d{4,}\b", re.IGNORECASE
)

# "password is X", "pwd: X", "pin X", "api key: X", "otp is X" — redact the
# label + the token that follows it, since the token itself is the secret.
_SECRET_RE = re.compile(
    r"\b(?:password|passwd|pwd|pin|otp|api[_ ]?key|secret|token)\b\s*(?:is|:)?\s*[:\-]?\s*\S+",
    re.IGNORECASE,
)

# North American / loosely international phone shapes, plus the bare
# "555-0142" local-exchange format. Runs last so it doesn't eat digits that
# CARD_RE should have claimed first.
_PHONE_RE = re.compile(
    r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b"
    r"|\b\d{3}[-.\s]\d{4}\b"
)

_PATTERNS = (
    (_EMAIL_RE, "[REDACTED_EMAIL]"),
    (_SSN_RE, "[REDACTED_SSN]"),
    (_CARD_RE, "[REDACTED_CARD]"),
    (_ACCOUNT_RE, "[REDACTED_ACCOUNT]"),
    (_SECRET_RE, "[REDACTED_SECRET]"),
    (_PHONE_RE, "[REDACTED_PHONE]"),
)


def redact_pii(text: str) -> str:
    """Replace emails, phone numbers, SSNs, card-shaped digit runs, account
    numbers, and password/PIN/API-key phrases with [REDACTED_*] placeholders."""
    if not text:
        return text
    redacted = text
    for pattern, replacement in _PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted
