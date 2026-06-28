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

## Steps

### 1. Locate or create the plan

Default path: `work_tracker/work_plan.md`. If no plan exists, PAUSE and
confirm before creating one from `references/template-work-plan.md` —
fill only the sections the project has real content for; delete the rest.

### 2. Discovery

PRIMARY SOURCE — the current conversation. In-session decisions, scope
changes, and newly discovered work ONLY exist in the main thread's context.

SECONDARY SOURCES — spawn ONE Explore subagent (skip this when
dispatched from `update-context`; reuse the orchestrator's shared
discovery instead):

> "Discover what's landed or changed in <project-root> since
> <timestamp> that affects the forward plan. Check: `git log
> --since=<ts>` + `git status`; new or status-changed files in
> docs/decisions/; the most recent work_tracker/ entries; file mtimes
> under the source tree. Report a tight bullet list of (a) plan items
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
  is append-only; never rewrite or delete prior rows.
- **Refresh the "As of" dates** in the header and status snapshot.

### 4. Consistency pointers (do not duplicate)

- A plan item whose decision landed should cite the ADR, not restate it.
- Exit criteria and gates must be observable and falsifiable ("smoke
  test green", not "mostly working").
- If reconciliation reveals a decision that was never captured, flag it
  for `update-decisions` — do not bury rationale in the plan.

## Pause-for-confirmation rules

- PAUSE before creating the plan file from the template.
- PAUSE before deleting or restructuring whole sections (phases,
  legends) — marking items and appending rows never needs confirmation.

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
