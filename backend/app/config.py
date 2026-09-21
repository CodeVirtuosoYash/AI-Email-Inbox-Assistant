"""Settings for the LLM pipeline: Gemini access, batching limits, retries.

Everything here is overridable via env vars (see ../.env.example) so the
pipeline can be tuned without touching code — e.g. a stricter free-tier
rate limit on the day of the demo just means a smaller
GEMINI_MAX_EMAILS_PER_BATCH, not a code change.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


# ---- Gemini access -----------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# gemini-2.5-flash is the current free-tier flash model on Google AI Studio
# API keys (no billing account required) — good default for a hackathon demo.
# Model availability changes over time; swap via env if yours differs (run
# genai.list_models() against your key to check).
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# ---- Batching ------------------------------------------------------------
# Real constraint in practice is the model's *output* token budget (one JSON
# result comes back per email), not the much larger input context — so we
# cap by BOTH a conservative input-token estimate and a hard email count.
GEMINI_MAX_INPUT_TOKENS_PER_BATCH = _env_int("GEMINI_MAX_INPUT_TOKENS_PER_BATCH", 20_000)
GEMINI_MAX_OUTPUT_TOKENS_PER_BATCH = _env_int("GEMINI_MAX_OUTPUT_TOKENS_PER_BATCH", 8_192)
GEMINI_EST_OUTPUT_TOKENS_PER_EMAIL = _env_int("GEMINI_EST_OUTPUT_TOKENS_PER_EMAIL", 220)
GEMINI_MAX_EMAILS_PER_BATCH = max(
    1, GEMINI_MAX_OUTPUT_TOKENS_PER_BATCH // GEMINI_EST_OUTPUT_TOKENS_PER_EMAIL
)

# ---- Resilience ------------------------------------------------------------
GEMINI_MAX_RETRIES = _env_int("GEMINI_MAX_RETRIES", 3)
GEMINI_RETRY_BASE_DELAY_SECONDS = _env_int("GEMINI_RETRY_BASE_DELAY_SECONDS", 2)

# ---- Local data -----------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
EMAIL_FILE = Path(os.environ.get("EMAIL_FILE") or (_THIS_DIR / ".." / ".." / "data" / "emails.json"))

# ---- Database & API ---------------------------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./inbox_copilot.db")

# Single-user local tool (no auth) — wildcard is fine; comma-separate to restrict.
_cors = os.environ.get("CORS_ORIGINS", "*")
CORS_ORIGINS = ["*"] if _cors.strip() == "*" else [o.strip() for o in _cors.split(",") if o.strip()]
