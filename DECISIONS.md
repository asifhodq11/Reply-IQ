# ReplyIQ — DECISIONS.md

> **Purpose:** Running log of everything built, decided, and in-progress.
> Every new AI conversation should read this file first to pick up where we left off.

---

## Current State

- **Phase:** 0 — Foundation
- **Status:** Not started (about to begin)
- **Last completed:** Bible read and confirmed (2026-03-17)
- **Next step:** Present Phase 0 plan, wait for "go ahead", then scaffold project

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

---

## Build Log

| Phase | Item | Status | Date |
|-------|------|--------|------|
| 0 | Read Bible, confirm understanding | ✅ Done | 2026-03-17 |
| 0 | Scaffold project structure | ⬜ Not started | — |

---

## Notes for Next Conversation

If starting a new chat, tell the AI:
1. We are on **Phase 0**
2. Last completed: **Bible confirmed, DECISIONS.md created**
3. Read this file (`DECISIONS.md`) and the Bible (`ReplyIQ_Bible.docx`)
