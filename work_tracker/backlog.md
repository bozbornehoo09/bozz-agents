# bozz-agents — Backlog

**As of:** 2026-06-29
**Status:** Longer-term parking lot — deferred *tasks* with a trigger but no
scheduled slot. One line each; promote into the work plan when it is time. Not
authoritative; no review hook.
**Maintenance:** Owned by `update-backlog`, dispatched by `/update-context`.
Keep it terse — a backlog that reads like a plan has failed.

---

## Parked tasks

- **Publish v0.3.0** — PR #1 (the `update-backlog` skill) and PR #2 (structure
  cleanup) merged 2026-06-28; bump the installed / marketplace plugin to v0.3.0.
- **SUGGEST-level skill cleanups** (deferred from PR #2's `skill-review`) — add a
  `## What this skill is NOT` section to the `update-*` skills; restore the
  canonical closing line to the two `_brief-template.md` files; convert
  `update-open-questions`' `### 7. No docs-review hook` into a `## Review hook`
  section; renest `context-up`'s Step 5 under `## Procedure`. Promote when doing
  a skill-polish pass.
- **Re-home or cross-reference the foundational decisions** — decide whether
  prism ADR-0015 / 0016 / 0021 (the patterns this repo implements) get
  bozz-agents-local ADRs or stay cross-referenced from
  [ADR-0001](../docs/decisions/0001-bozz-agents-maintains-own-context.md).
  Trigger: when a foundational pattern next changes here.
