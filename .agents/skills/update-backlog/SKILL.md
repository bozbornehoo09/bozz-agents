---
name: update-backlog
description: Reconcile the longer-term backlog — promote tasks into the work plan when they're scheduled, park newly-deferred tasks, drop ones that landed. Use at the end of a session or when a task is wanted but deferred past the current plan. No review hook (the backlog is not authoritative); keep it terse — it is a parking lot, not a plan.
---

# Update Backlog

Update the backlog at `<project-root>/work_tracker/backlog.md` (or the
path declared in `context-manifest.yaml`). The backlog is the
longer-term member of the FORWARD family: a terse parking lot for
deferred *tasks* the project will want but has not yet scheduled into a
phase — one line each, promoted into the work plan when it is time.
It is the sibling of `work_tracker/work_plan.md`: the work plan holds
the current phase + the near-term backlog (§1); this file holds
everything wanted-but-not-yet-scheduled.

## What belongs here (and what does not)

In scope — deferred **tasks**: work we expect to do, with a trigger
that will schedule it, but no phase yet.

Out of scope — route these elsewhere, never park them here:
- Deferred **decisions** → `docs/open_questions.md` (`update-open-questions`).
- Committed milestones / itemized phase work → the phase tables in
  `work_tracker/work_plan.md` (`update-work-plan`).
- The **near-term** backlog (next phase, scheduled) → work plan §1.

The test for "backlog vs work plan §1": if it has a trigger but no
phase, it is backlog; once it is scheduled into the current or next
phase, it is promoted out.

## Steps

### 1. Locate or create the backlog

Default path: `work_tracker/backlog.md`. If none exists, PAUSE and
confirm before creating one — a short header (`As of`, a one-line
note that it is not authoritative / no review hook) plus the parked
items, terse.

### 2. Discovery

PRIMARY SOURCE — the current conversation. Tasks get deferred, and
deferred tasks get scheduled, in the main thread; capture both directly.

SECONDARY SOURCES — spawn ONE Explore subagent (skip this when
dispatched from `update-context`; reuse the orchestrator's shared
discovery instead):

> "Discover what's changed in <project-root> since <timestamp> that
> affects the longer-term backlog. Check: `git log --since=<ts>` +
> `git status`; new/status-changed ADRs in docs/decisions/; the work
> plan's §1 and phase tables; the most recent work_tracker/ entries.
> Report a tight bullet list of (a) backlog items that now appear
> SCHEDULED (named in a phase) or LANDED (built), (b) longer-term
> tasks newly deferred that are not yet parked, with file paths.
> Under 300 words."

Timestamp anchor: the backlog's own "As of" date. If none, the most
recent work_tracker entry.

### 3. Reconcile the backlog

- **Promote scheduled items** — when an item gets a phase, remove it
  from the backlog and hand the promotion to `update-work-plan`, which
  owns writing it into the plan (§1 or the right phase table) and
  recording the Plan Changes row. In a sweep, `update-context` runs
  `update-work-plan` alongside this skill; standalone, invoke
  `update-work-plan` (or PAUSE and flag the promotion) rather than
  editing `work_plan.md` from here — this skill owns only `backlog.md`.
  The backlog keeps no audit trail of its own — the trail is the work
  plan's Plan Changes plus the work tracker.
- **Park newly-deferred tasks** — one line each: the task, the
  **trigger** that will schedule it (a phase, an ADR, a design-doc
  threshold), and a pointer to where it is grounded. No prose.
- **Drop landed items** — if a parked task was built anyway, remove the
  line. Confirm the landing before dropping (discovery reports items
  that *appear* done). Its record lives in the tracker, not here.
- **Refresh the "As of" date** in the header.

### 4. Keep it terse (anti-bloat)

The backlog earns its keep only by staying short. One line per item.
If an item has grown a paragraph of rationale, the rationale belongs in
an ADR or the design doc — cite it and cut the prose. A backlog that
reads like a plan has failed; promote or drop instead of elaborating.

## Pause-for-confirmation rules

- PAUSE before creating the backlog file.
- PAUSE before dropping an item as no-longer-wanted (vs landed/promoted)
  — that is a scope call the user owns.
- Parking a new item and removing a promoted/landed item from the
  backlog never need confirmation — apply directly and report what
  moved. Writing into the work plan is `update-work-plan`'s job; hand it
  off rather than editing `work_plan.md` from this skill.

## Style

- One line per item. Terse. Group related items under a short heading
  if the list grows (e.g. "Future services", "Scale-out swaps").
- Every item names its **promotion trigger** and cites its source
  (ADR by number, design/strategy section by §).
- Do not restate rationale — the ADR or design doc owns it.

## Review hook

None — the backlog is forward-looking and not authoritative, so it is
excluded from `docs-review` scope (like the work plan and work tracker).
There is nothing to stress-test: a parked task is a pointer, not a
commitment.
