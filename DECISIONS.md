# ReplyIQ — DECISIONS.md

> **Purpose:** Running log of everything built, decided, and in-progress.
> Every new AI conversation should read this file first to pick up where we left off.

---

## Current State

- **Phase:** 2 — Database Migrations
- **Status:** ✅ COMPLETE
- **Last completed:** All 5 migrations run, health endpoint verified showing database ok (2026-03-17)
- **Next step:** Begin Phase 3 — Authentication

---

## Operational Rules (Always Active)

1. **Bible is law** — `ReplyIQ_Bible.docx` is the single source of truth. Do not guess.
2. **One phase at a time** — Complete current phase fully before touching the next.
3. **Explain before code** — List files, explain in plain English, flag risks, then wait for "go ahead".
4. **No TODOs** — Either write it or state it's out of scope for this phase.
5. **DECISIONS.md stays updated** — Every build step and decision is logged here.
6. **Efficiency rules** — Minimize AI quota usage. No unnecessary browser automation. Be concise.

---

## AI Efficiency Rules

- Avoid opening the browser unless absolutely required for visual verification.
- Batch file operations where possible instead of individual calls.
- Keep tool calls minimal — read only what's needed, don't re-read known files.
- Use terminal commands efficiently (combine checks, limit output).

---

## Decisions Log

| # | Date | Decision | Reasoning |
|---|------|----------|-----------|
| 1 | 2026-03-17 | Bible read and all 4 confirmations verified | Starting point for Phase 0 |
| 2 | 2026-03-17 | DECISIONS.md created as persistent context file | Enables continuity across AI conversations |
| 3 | 2026-03-17 | 14 env keys confirmed as-is | Verified against Bible |
| 4 | 2026-03-17 | Python 3.12 target (safer compatibility) | User has 3.14 installed but 3.12 has wider package support (added .python-version file) |
| 5 | 2026-03-17 | `config.py` enforces immediate crash if keys missing | User explicitly requested `os.environ['KEY']` over `.get()` to prevent silent failures |
| 6 | 2026-03-17 | Key names differ slightly from Bible | Code uses SUPABASE_SERVICE_ROLE_KEY and STRIPE_PRICE_ID_STARTER. Bible says SUPABASE_SERVICE_KEY and STRIPE_STARTER_PRICE_ID. Code is internally consistent — no change made. |
| 9 | 2026-03-17 | Health endpoint updated | Queries users table directly instead of RPC function because tables now exist after Phase 2 |
| 10 | 2026-03-17 | Environment shows as 'unknown' in health response | Cosmetic only, not a bug, fix later |

---

## Build Log

| Phase | Item | Status | Date |
|-------|------|--------|------|
| 0 | Foundation structure, configs, empty files | ✅ Done | 2026-03-17 |
| 1 | `config.py` (Dev, Test, Prod) | ✅ Done | 2026-03-17 |
| 1 | `extensions.py` (Limiter, ONE Supabase client, CORS, Talisman) | ✅ Done | 2026-03-17 |
| 1 | `errors.py` (`build_error` + locked codes) | ✅ Done | 2026-03-17 |
| 1 | `logger.py` (Strict JSON logging `log_event()`) | ✅ Done | 2026-03-17 |
| 1 | Empty route blueprints defined & registered | ✅ Done | 2026-03-17 |
| 1 | `/health` route (DB ping using shared client) | ✅ Done | 2026-03-17 |
| 1 | `__init__.py` App Factory | ✅ Done | 2026-03-17 |
| 2 | `001_create_users.sql` | ✅ Done | 2026-03-17 |
| 2 | `002_create_reviews.sql` | ✅ Done | 2026-03-17 |
| 2 | `003_create_replies.sql` | ✅ Done | 2026-03-17 |
| 2 | `004_create_approval_tokens.sql` | ✅ Done | 2026-03-17 |
| 2 | `005_create_poller_log.sql` | ✅ Done | 2026-03-17 |
| 2 | Health endpoint fixed | ✅ Done | 2026-03-17 |
| 3 | Authentication | ⬜ Not started | — |

---

## Notes for Next Conversation

If starting a new chat, tell the AI:
1. Ready for Phase 3 — Authentication
2. Last completed: Phase 2 fully verified
3. Read DECISIONS.md and ReplyIQ_Bible.docx
4. Phase 3 builds: user_model.py, decorators.py, auth_schema.py, auth.py routes, and 8 auth tests
5. Before writing tests, run the 5 migrations on the TEST Supabase project too
6. Also run the same 5 SQL files against the test Supabase project before Phase 3 tests can run
7. FIRST TASK of Phase 3 before writing any new code: Fix health endpoint — "environment" shows as "unknown" instead of "development". Fix: use os.environ.get('FLASK_ENV', 'unknown') in health.py to read the environment correctly. Restart server and confirm health shows "environment": "development" before proceeding.
