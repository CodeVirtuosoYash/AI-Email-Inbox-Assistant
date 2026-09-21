# Inbox Copilot

An AI email assistant built for a 3-hour hackathon.

**Problem statement:** Managing a busy inbox can become overwhelming. Build an AI email
assistant that helps users summarize conversations, identify important messages, extract
tasks and deadlines, and draft suitable responses.

**Approach:** a local, single-user tool — no login, no external mailbox connection. Point
it at a JSON file of emails (`data/emails.json`), click **Summarize**, and the backend
redacts PII, batches the emails to Gemini for classification, and persists the results to
SQLite so the dashboard is populated on every future visit without re-processing anything
already seen.

---

## Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React 19 + Vite + React Router | Fast dev loop, no server-rendering needed for a local tool |
| Backend | FastAPI + SQLAlchemy 2.0 | Typed, async-capable, minimal boilerplate |
| Database | SQLite | Zero-config, file-based, plenty for a single-user demo |
| LLM | Gemini (`gemini-2.5-flash` by default), free-tier API key | Fast + cheap enough to batch many emails per call |

---

## Repository layout

```
AI-Email-Inbox-Assistant/
├── data/
│   └── emails.json              # the local demo inbox — source of truth for a Summarize run
├── email_assistant_design.md    # full system design: ER diagram, sequence diagrams, API contract
│
├── backend/
│   ├── requirements.txt
│   ├── .env.example             # GEMINI_API_KEY, GEMINI_MODEL, batching/retry tuning, DATABASE_URL
│   ├── demo.py                  # standalone CLI: runs the LLM pipeline without the API/DB
│   └── app/
│       ├── main.py              # FastAPI app, CORS, creates tables on startup
│       ├── config.py            # env-driven settings
│       ├── database.py          # engine, SessionLocal, Base
│       ├── models.py            # SQLAlchemy models (Email, Analysis, Task, Reply, SyncState)
│       ├── schemas.py           # request bodies (PATCH /tasks, POST /replies/regenerate)
│       ├── crud.py              # persistence + response serializers
│       ├── security.py          # redact_pii() — regex PII scrubbing
│       ├── guardrails.py        # prompt-injection pre-scan + output validation/sanitization
│       ├── routers/             # summarize, dashboard, tasks, messages, replies
│       └── services/
│           ├── agent.py         # /summarize orchestration + watermark logic
│           ├── gemini_client.py # batched Gemini calls, schema, retries
│           ├── ingest.py        # loads emails.json → redact → guardrail pre-scan
│           └── rollup.py        # builds the dashboard response shape
│
└── frontend/
    └── src/
        ├── App.jsx              # router — Dashboard is the entry route, no auth
        ├── api/client.js        # fetch wrapper (USE_MOCKS toggle for backend-less dev)
        ├── pages/                # Dashboard, Tasks, Messages, Replies, Calendar
        └── components/           # SummarizeButton, TaskCard, ReplyEditor, LoadingState, ...
```

See [`email_assistant_design.md`](email_assistant_design.md) for the full design: ER diagram,
architecture diagram, sequence diagram, and the Gemini output contract.

---

## How it works

1. **First open:** the dashboard has no data yet — empty stat cards, no "last synced" line,
   nothing in Tasks/Messages/Replies/Calendar. Nothing has been processed.
2. **Click Summarize:** the backend reads `data/emails.json`, keeps only emails newer than
   the stored watermark (`last_summarized_at`) that aren't already in the database, and:
   - **redacts PII** from each body (emails, phone numbers, SSNs, card numbers, account
     numbers, password/PIN/API-key phrases) before anything reaches an LLM prompt,
   - runs a **prompt-injection / spam pre-scan** on the redacted text,
   - **batches** as many redacted emails as fit into one Gemini call (bounded by an
     input-token estimate and the model's output-token budget), instead of one call per email,
   - asks Gemini to classify each email as `important_message`, `task`, `meeting`, `event`,
     or `fyi`, with a summary, priority + reason, and (for messages) a drafted reply, or
     (for tasks/meetings/events) due dates, suggested actions, and when/where details,
   - **re-validates every result in code** — enums coerced to safe defaults, dates
     sanity-bounded, lengths capped, guardrail flags merged (pre-scan flags always win),
   - saves everything to SQLite and advances the watermark.
3. **Every visit after that** reads straight from SQLite — the dashboard, tasks, messages,
   and replies are already there, with a "last synced" timestamp. Clicking Summarize again
   only processes emails added to `data/emails.json` since the last run.

---

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# then edit .env and set GEMINI_API_KEY (free key: https://aistudio.google.com/apikey)
python -m uvicorn app.main:app --reload --port 8000
```

First launch creates `backend/inbox_copilot.db` and all tables automatically — no migration
step needed.

You can exercise the LLM pipeline on its own, without the API or a database, via:

```bash
python demo.py --dry-run   # shows PII redaction + batching plan, no API call
python demo.py             # runs it for real against Gemini
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the printed URL (usually `http://localhost:5173`). The API client talks to
`http://localhost:8000` by default (`frontend/.env.example` → `VITE_API_BASE_URL`).

`frontend/src/api/client.js` has a `USE_MOCKS` flag at the top — `true` runs entirely
against bundled mock data (useful for frontend work with no backend running), `false`
calls the real FastAPI backend above.

---

## API

| Method | Route | Purpose |
|---|---|---|
| POST | `/summarize` | Process only new emails since the last run; returns the dashboard roll-up |
| GET | `/dashboard` | Today/tomorrow tasks, summaries, counts, last-synced timestamp |
| GET | `/tasks` | All extracted tasks |
| PATCH | `/tasks/{id}` | Mark a task done/pending |
| GET | `/messages` | Every analyzed email, any category |
| GET | `/replies` | Emails with a drafted reply |
| POST | `/replies/{email_id}/regenerate` | Re-draft a reply in a different tone |
| GET | `/health` | Liveness check |

Full request/response shapes and the Gemini JSON contract are in
[`email_assistant_design.md`](email_assistant_design.md) §5–§7.

---

## Data model

- **Email** — one row per source email (`source_id` unique, dedup guard).
- **Analysis** — 1:1 with Email. Category, priority + reason, summary, and (for
  meeting/event) when/where/notes, plus guardrail flags (`prompt_injection_suspected`,
  `spam_suspected`).
- **Task** — 1:N with Email. Text, due date, suggested actions, pending/done status.
  Meetings/events also synthesize a Task row so their deadlines show up on the
  Tasks/Calendar pages.
- **Reply** — 0..1 with Email. Suggested reply text + tone.
- **SyncState** — single row holding the watermark (`last_summarized_at`), last run
  time, and cumulative emails-processed count.

## Demo data

`data/emails.json` has 18 sample emails spanning Aug 9–11, 2026: a mix of tasks (with and
without real deadlines), important messages needing replies, meetings/events, plain FYIs, a
spam/promotional email, and emails containing a phone number and an email address (to
exercise PII redaction). Append new entries with a later `received_at` and click Summarize
again to demo incremental processing — only the new ones get analyzed.

---

## Security notes

- The Gemini key lives only in the backend (`backend/.env`, gitignored) — it's never sent
  to or used from the browser.
- Every email body is regex-redacted for PII **before** it's placed in any LLM prompt.
- A pre-scan flags likely prompt-injection attempts in email content (emails are
  attacker-controllable text pasted into a prompt) independently of whatever the model
  itself reports, and every batch response is re-validated in code rather than trusted
  outright.
- **`backend/.env` must never be committed.** It's in `.gitignore`, but a real key was
  committed early in this project's history before that mattered and had to be rotated
  after Google auto-revoked it — double-check `git status` before committing anything under
  `backend/`.

---

## Rubric coverage

| Category | Where it shows up |
|---|---|
| Data modeling | ER diagram + normalized SQLAlchemy models (design doc §3/§4) |
| Architecture / code flow | Layered diagram + sequence diagram (design doc §2/§6) |
| Prompt / LLM engineering | Schema-forced JSON output, batching, explicit model-limitation rules (design doc §5) |
| Security / PII | Backend-only key, `redact_pii`, prompt-injection guardrails (design doc §5b) |
| Tech reasoning | Flash model for latency/free-tier cost, batching for call-count, SQLite zero-config |
| Business value | Watermark-based incremental processing — no redundant LLM spend on re-reads |
