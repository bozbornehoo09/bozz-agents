---
name: context-up
description: Load just enough project context to resume work with confidence — where things stand, what's next, and the specific docs the task at hand needs. Use when the user says "context up", "load context", "pick up where I left off", "what was I working on", "what's the status", or starts a session with a task and no context loaded. Read-only; modifies nothing.
---

# Context Up

Load the minimum context needed to act with full confidence on THIS
session's task — not the whole knowledge base. The project's layered
docs exist precisely so you can navigate to the right ones; loading
everything defeats the layering and burns the context window.

Read-only: this skill never modifies files.

## Procedure

### Step 1 — Resolve the layer map

Read `context-manifest.yaml` at the project root for layer paths. If
absent, use the conventional defaults (`docs/decisions/`,
`docs/strategy/`, `docs/architecture/`, `.claude/rules/`,
`docs/open_questions.md`, `work_tracker/`,
`work_tracker/work_plan.md`, `work_tracker/backlog.md`). The
orientation file (CLAUDE.md / AGENTS.md) is already auto-loaded — do
not re-read it.

### Step 2 — Determine session intent

From the user's message. If they gave a task ("implement X", "design
Y", "should we Z?"), that is the intent. If they only said "context up"
or "where did I leave off", intent is **resume**.

### Step 3 — Core load (always; this is the whole load for "resume")

Read, in full — these are small by convention:

1. The most recent `work_tracker/` daily entry (backward: what just
   happened, what was deferred).
2. The work plan's header, status snapshot, "Next up", and "Blocked"
   sections (forward: what's next and what's stuck).
3. The decisions index (`docs/decisions/README.md`) — titles and
   statuses ONLY. Note any **Proposed** ADRs awaiting sign-off; read a
   Proposed ADR in full only if signing off looks like this session's
   work.

Do NOT read individual Accepted ADRs, the architecture design, strategy
docs, rules, or research at this stage.

### Step 4 — Intent-scoped expansion

Expand by intent. Each row lists what to ADD — nothing else.

| Intent | Add |
|---|---|
| **Resume / status** | Nothing. Core load is complete. |
| **Implement in package X** | The rules file for X (e.g. `.claude/rules/<x>.md`); then ONLY the ADRs and architecture sections that rules file cites. If the work plan names a spec for the item (e.g. an implementation-plan file), read that spec. |
| **Design / architect** | Architecture README + the design sections covering the affected area (navigate by the doc's numbered TOC; do not read the design end-to-end); related ADRs found via the index; relevant `docs/open_questions.md` entries. |
| **Decide an open question** | That question's entry in `docs/open_questions.md` + the research memos and ADRs it links. Other questions stay unread. |
| **Strategy / positioning** | `docs/strategy/` top-level docs. Research memos only if the task cites them. |
| **Review (plan/code/docs)** | Nothing extra — invoke the review skill; it loads its own corpus. |

If the task spans multiple intents, take the union — but each piece
still enters via its row's path (citation-first, never bulk).

## Anti-greed contract

- **Index first, then fetch.** Reach ADRs through the decisions index
  or a citation in a rules/architecture file — never by globbing the
  decisions directory.
- **Citations are the trail.** Read a doc because something you already
  read cites it for this task, not because it exists.
- **Sections, not volumes.** For long docs (architecture design,
  strategy), read the TOC, then only the sections that match the task.
- **Don't preload "might need".** Name it as available instead; load it
  when the task actually touches it.
- **Never load** research memos, superseded ADRs, prior work-tracker
  weeks, or the longer-term backlog (`work_tracker/backlog.md`) unless
  the task is specifically about them — the backlog is a parking lot,
  not part of resuming.

### Step 5 — Report and confirm readiness

Print a tight summary (≤10 lines):

- **Project + phase:** one line.
- **Last session:** 1–2 lines from the latest tracker entry.
- **Next up:** the plan's top unchecked item (or the user's stated task).
- **Blockers / pending:** open blockers, Proposed ADRs awaiting sign-off.
- **Loaded:** the files/sections actually read.
- **Skipped (by design):** the layers deliberately not loaded, e.g.
  "architecture §§1–8, strategy, research — say the word to pull any in."

Then: "Context loaded. Ready to continue."

If, once work starts, a gap appears (an uncited constraint, an
unfamiliar term), fetch the specific doc then — scoped loading means
late binding, not flying blind.
