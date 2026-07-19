# bozz-agents — Work Plan

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
- This document is not authoritative — rationale lives in ADRs. Before a
  build phase starts, stress-test the plan with `plan-review`.

STATUS MARKERS: [ ] not started   [~] in progress   [x] complete
                [—] dropped (with reason)
-->

**As of:** 2026-07-18
**Scope:** Plugin development and publishing — the skills are the product;
no application build phases.
**Companion docs:** `docs/decisions/` (the why), `docs/concepts.md` (the
design), `work_tracker/` (the when, after the fact). This doc is the
*forward* view; the work tracker is the *backward* one.
**Maintenance:** Owned by `update-work-plan` (dispatched by `update-context`
at session end). No review hook.

---

## 0. Status snapshot (as of 2026-07-18)

**Done.**
- Context bootstrap — manifest, ADR-0001, work_tracker seeded
  → work_tracker week_27 tuesday_6-30
- Skill-family convention hardening (two-round skill-review + fixes,
  incl. prism instance sync) → PR #5 (bozz) merged 2026-07-02
- Host-neutral distribution + Codex plugin packaging (canonical `skills/`,
  generated per-host trees, plugin manifests) → PR #6 merged 2026-07-18,
  ADR-0002
- Manifest-resolved `docs-review` corpus discovery → commit `2364c45`
- File-scoped cross-agent review lifecycle: requester, reviewer, independent
  finding fold, adaptive polling, helper/tests, and generated host trees
  → PR #8 merged 2026-07-18, ADR-0003
- v0.4.0 published with the host-neutral distribution and cross-review
  lifecycle → PR #9 merged 2026-07-18

**In progress.**
- None.

**Not started.**
- No scheduled milestone.

---

## 1. Next up — current focus

The immediate, ordered focus. When one clears, promote the next and log the
landing in the work tracker.

No active milestone is scheduled. Select the next scope before implementation;
longer-term candidates remain in `work_tracker/backlog.md`.

(Companion prism PR #22 tracked in that repo; not verified this session.)

---

## Blocked

None.

---

## Plan Changes

Append-only. One row per meaningful plan change.

| Date | What changed | Why |
|---|---|---|
| 2026-07-03 | Plan created (seeded from template) | First `update-context` sweep to need the FORWARD layer; `context-manifest.yaml` declared the path but the file did not exist |
| 2026-07-18 | PR #5 marked merged; PR #6 (host-neutral distribution + Codex plugin) landed unplanned, recorded as ADR-0002; v0.3.0 promoted to sole next-up | Skill genericization + Codex packaging completed the portability arc, and the merge cleared the PR #5 gate on the version bump |
| 2026-07-18 | ADR-0003 cross-review lifecycle inserted ahead of v0.3.0; publish scope expanded to include its three skills and helper | The live Prism bridge proved independent review but also exposed global-file growth, numbering collisions, static polling, and unverified-fold risks that should be fixed before the next plugin release |
| 2026-07-18 | ADR-0003 lifecycle and docs-review corpus resolution marked complete; planned v0.3.0 replaced by shipped v0.4.0; active queue cleared | PR #8 and PR #9 landed the reviewed lifecycle and release, leaving no user-selected next milestone |
