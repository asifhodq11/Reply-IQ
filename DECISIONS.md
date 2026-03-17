# ReplyIQ — DECISIONS.md

> **Purpose:** Running log of everything built, decided, and in-progress.
> Every new AI conversation should read this file first to pick up where we left off.

---

## Current State

- **Phase:** 1 — App Factory
- **Status:** ✅ COMPLETE
- **Last completed:** Built app factory, rigid config.py, errors, logger, and health check (2026-03-17)
- **Next step:** Begin Phase 2 — Database Migrations (5 files, RLS, indexes)

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
| 2 | DB Migrations (tables, RLS policies, indexes) | ⬜ Not started | — |

---

## Notes for Next Conversation

If starting a new chat, tell the AI:
1. We are ready for **Phase 2 — Migrations**
2. Last completed: **Phase 1 — App Factory (fully complete)**
3. Read this file (`DECISIONS.md`) and the Bible (`ReplyIQ_Bible.docx`)
