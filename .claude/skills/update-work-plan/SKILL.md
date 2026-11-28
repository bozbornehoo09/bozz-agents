---
name: update-work-plan
description: Reconcile the forward work plan with reality — mark landed items, promote the next focus, record plan changes with their why. Use at the end of a session or after a decision reshapes the plan. No review hook (the plan is not authoritative); run plan-review before starting a build phase.
---

# Update Work Plan

Update the work plan at <project-root>/work_tracker/work_plan.md (or the
path declared in `context-manifest.yaml`). The work plan is the FORWARD
layer: what's next, in what order, and why — the mirror of the work
tracker, which records what already happened. Rationale lives in ADRs;
the plan only points at it.

## Scope

In scope:
- `work_tracker/work_plan.md` (or the manifest-declared path)

Out of scope:
- the longer-term backlog `work_tracker/backlog.md` →
  `update-backlog`
- the activity log (weekly tracker entries) →
  `update-work-tracker`
- decision rationale → `update-decisions` (the plan only
  points at ADRs)

## Steps

### 1. Locate or create the plan

Default path: `work_tracker/work_plan.md`. If no plan exists, PAUSE and
confirm before creating one from `references/template-work-plan.md` —
fill only the sections the project has real content for; delete the rest.

### 2. Discovery

PRIMARY SOURCE — the current conversation. In-session decisions, scope
changes, and newly discovered work ONLY exist in the main thread's context.

SECONDARY SOURCES — run ONE discovery subagent using the host's subagent or
delegation facility (skip this when
dispatched from `update-context`; reuse the orchestrator's shared
discovery instead):

> "Discover what's landed or changed in <project-root> since
> <timestamp> that affects the forward plan. Check: `git log
> --since=<ts>` + `git status`; new or status-changed files in
> docs/decisions/; the most recent work_tracker/ entries; file mtimes
> under the source tree. Read the plan through its headings and open
> items (context-up's scripts/load_context.py prints them) and grep the
> rest; never read it whole. Report a tight bullet list of (a) plan items
> that appear DONE or IN PROGRESS, (b) new work not in any plan, with
> file paths. Under 300 words."

Timestamp anchor: the plan's own "As of" date. If none, the most recent
work_tracker entry.

### 3. Reconcile the plan

- **Mark landed items** — `[ ]` → `[x]` with a pointer to where the work
  landed (`→ ADR-NNNN`, `→ work_tracker/week_NN`, or a file path). Move
  nothing; the marker and pointer are the record. Before marking,
  confirm the pointer target exists — discovery reports items that
  *appear* done; the pointer check is what makes the marker true.
- **Mark in-flight items** `[~]`, dropped items `[—]` with a one-clause
  reason.
- **Promote the next focus** — when a "Next up" item clears, promote the
  next; keep the list short (3–5 items) and ordered.
- **Add newly discovered work** to the right phase. If it gates the
  current focus, it goes in "Next up"; if it's blocked externally, it
  goes in "Blocked" with what unblocks it.
- **Record every structural change** — additions, reorderings, drops,
  scope reshapes — as a dated row in the "Plan Changes" table. The table
  is append-only; never rewrite or delete prior rows (aged rows leave the
  live file only by verbatim archival in step 5).
- **Refresh the "As of" dates** in the header and status snapshot. Take
  every date from the system clock (`date +%Y-%m-%d`), never from
  reasoning about the calendar.
- **Flag, don't guess.** When an item's phase or priority is ambiguous,
  leave it where it is and name it in the report.
- **Respect deliberate divergence.** If the user has restructured the plan
  on purpose, keep their layout and record the divergence as a Plan
  Changes row instead of forcing the template back.

### 4. Consistency pointers (do not duplicate)

- A plan item whose decision landed should cite the ADR, not restate it.
- Exit criteria and gates must be observable and falsifiable ("smoke
  test green", not "mostly working").
- If reconciliation reveals a decision that was never captured, flag it
  for `update-decisions` — do not bury rationale in the plan.

### 5. Compaction (only when flagged or requested)

When `update-context` reports `compaction due` for the plan and the user
accepted it, or the user asks to compact the plan, run the procedure in
`../update-context/references/compaction.md` after steps 3–4. Typical
candidates: Plan Changes rows past the live horizon, item rows of phases
whose exit criteria are met, and stacked prior status snapshots. Current
phase, "Next up", "Blocked", and the latest snapshot are always KEEP.
Archive to `work_tracker/archive/work_plan-history.md` (beside the
manifest-declared plan path).

## Pause-for-confirmation rules

- PAUSE before creating the plan file from the template.
- PAUSE before deleting or restructuring whole sections (phases,
  legends) — marking items and appending rows never needs confirmation.
- PAUSE on the compaction plan before archiving or compressing anything.

## Style

- Tables and one-line bullets, not prose. Terse.
- Cross-reference ADRs by number, tracker entries by week folder,
  research by path.
- History lives in Plan Changes and the work tracker — the plan body
  always reads as the current truth.

## Review hook

None — the plan is forward-looking and not authoritative, so it is
excluded from `docs-review` scope (like the work tracker). Before a
build phase starts, stress-test the plan with `plan-review` instead.
