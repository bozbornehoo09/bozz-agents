# {Project} — Work Plan

<!--
PURPOSE: The forward view — what's next, in what order, and why. The work
tracker records what happened (backward); this plan says what's coming
(forward). It is the first thing to read when deciding what to work on.

PRINCIPLES:
- Keep "Next up" current — a stale plan is worse than no plan.
- Plans change; record the change, don't erase it. When items are added,
  reordered, or dropped, add a dated row to "Plan Changes" with the why.
- Completed work leaves a pointer, not a narrative: cross-reference the
  work_tracker entry or ADR where it landed.
- This document is not authoritative — rationale lives in ADRs, constraints
  live in rules. Before a build phase starts, stress-test the plan with
  `plan-review`.

STATUS MARKERS (item-level, used in Status columns and checklists):
  [ ] not started   [~] in progress   [x] complete   [—] dropped (with reason)
-->

**As of:** {YYYY-MM-DD}
**Scope:** {What this plan covers — build work, design questions, research.}
**Companion docs:** {decisions dir} (the why), {rules dir} (the per-package
what), {architecture dir} (the design), {work tracker dir} (the when, after
the fact). This doc is the *forward* view; the work tracker is the *backward* one.
**Maintenance:** Owned by `update-work-plan` (dispatched by `update-context`
at session end). No review hook; run `plan-review` before starting a build phase.

---

## 0. Status snapshot (as of {YYYY-MM-DD})

**Done.**
- {Landed item — one line, with pointer: → ADR-NNNN / work_tracker week_NN}

**Not started.**
- {Major outstanding area — one line}

---

## 1. Next up — current focus

The immediate, ordered focus. When one clears, promote the next and log the
landing in the work tracker.

1. **{[~] Item}** — {what it unblocks, what gates it}
2. **{[ ] Item}** — {…}

---

## 2. Phases overview

| Phase | Theme | Priority | Exit criteria |
|---|---|---|---|
| **Phase 0** | {theme} | P0 | {observable, falsifiable exit condition} |
| **Phase 1** | {theme} | P0 | {…} |

<!-- Optional legends — keep if the project sizes work; delete otherwise. -->

**Priority tiers:** P0 {meaning} · P1 {meaning} · P2 {meaning} · P3 {deferred}.

**LOE (t-shirt, one dev's calendar days):** XS ≤0.5 · S 1–2 · M 3–5 · L 1–2wk
· XL >2wk. Inflate 1.5–2× for the first task in a new technology area.

---

## Phase {N} — {Theme} ({priority})

{One paragraph: the goal of this phase and why it's sequenced here.}

| # | Item | Status | LOE | Depends on | Notes |
|---|---|---|---|---|---|
| {N.1} | **{Item}** | [ ] / [~] / [x] → {ADR/tracker ref} / [—] {reason} | {S} | {N.0} | {constraints, pointers} |

**Critical path:** {N.1 → N.2 → …}
**Estimated wall time:** {range, with assumptions}

<!-- Repeat per phase. Later phases may be bundled pointers, not itemized. -->

---

## Blocked

Items that cannot proceed, with what unblocks them. External dependencies
(third-party access, approvals, sign-offs) go here even when mid-phase.

- [ ] {Item} — blocked on: {what needs to happen, who/what it's waiting on, date raised}

---

## Recommended ordering

<!-- Optional: week-by-week or milestone sequence with explicit gates. -->

1. **{Week/Milestone 1}.** {…}
2. **{Week/Milestone 2}.** {…} **← Gate: {condition that must be true to proceed}**

**Risk note:** {known slip risks and the de-scope order if slipping — what
gets deferred first, what is never split.}

---

## Plan Changes

Append-only. One row per meaningful plan change — additions, reorderings,
drops, scope reshapes. The plan is a living document, not a contract; this
table is its history.

| Date | What changed | Why |
|---|---|---|
| {YYYY-MM-DD} | {e.g., "Dropped X approach, switched to Y"} | {e.g., "licensing verification refuted assumption Z — see research memo"} |
