"""Standalone runnable demo for the LLM pipeline — works before the rest of
the backend (FastAPI, SQLAlchemy, routers) exists. Run from the backend/
directory (or anywhere, via `python backend/demo.py`):

    python demo.py            # redact + guardrail pre-scan + batch + call Gemini
    python demo.py --dry-run  # skip the Gemini call, just show redaction/batching

Requires GEMINI_API_KEY in backend/.env (copy from .env.example) unless
--dry-run is passed.
"""
from __future__ import annotations

import argparse

from app.services.gemini_client import analyze_emails, build_batches
from app.services.ingest import load_emails_from_file, to_email_inputs


def _print_batches(batches: list) -> None:
    print(f"\n{len(batches)} batch(es) planned:")
    for i, batch in enumerate(batches, start=1):
        ids = ", ".join(e.source_id for e in batch)
        flagged = [e.source_id for e in batch if e.pre_flags.prompt_injection_suspected]
        print(f"  batch {i}: {len(batch)} email(s) -> {ids}")
        if flagged:
            print(f"    guardrail pre-scan flagged possible prompt injection: {flagged}")


def _print_result(source_id: str, result: dict) -> None:
    print(f"\n[{source_id}] type={result['type']} priority={result['priority']}")
    print(f"  summary: {result['summary']}")
    print(f"  reason:  {result['priority_reason']}")
    if result["flags"]["prompt_injection_suspected"] or result["flags"]["spam_suspected"]:
        print(f"  flags:   {result['flags']}")
    if result["type"] == "important_message" and result.get("suggested_reply"):
        preview = result["suggested_reply"][:120]
        print(f"  reply ({result.get('tone', '')}): {preview}...")
    for t in result.get("tasks", []):
        print(f"  task: {t['text']} (due {t['due_date'] or 'no deadline'})")
    if result["type"] in ("meeting", "event"):
        ev = result.get("event_details", {})
        print(f"  when: {ev.get('when') or '?'}  where: {ev.get('where') or '?'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the inbox-copilot LLM pipeline standalone.")
    parser.add_argument("--dry-run", action="store_true", help="skip the Gemini call")
    args = parser.parse_args()

    raw = load_emails_from_file()
    print(f"Loaded {len(raw)} emails from data/emails.json")

    inputs = to_email_inputs(raw)  # redact_pii() + guardrail pre_scan() per email, per app/security.py + app/guardrails.py

    batches = build_batches(inputs)
    _print_batches(batches)

    if args.dry_run:
        print("\n--dry-run: skipping Gemini call.")
        return

    results, failures = analyze_emails(inputs)

    for e in inputs:
        if e.source_id in results:
            _print_result(e.source_id, results[e.source_id])

    if failures:
        print(f"\n{len(failures)} batch(es) failed:")
        for f in failures:
            print(f"  {f.source_ids}: {f.error}")

    print(f"\nDone: {len(results)}/{len(inputs)} emails analyzed.")


if __name__ == "__main__":
    main()
