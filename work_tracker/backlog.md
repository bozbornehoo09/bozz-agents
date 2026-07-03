# bozz-agents — Backlog

**As of:** 2026-07-03
**Status:** Longer-term parking lot — deferred *tasks* with a trigger but no
scheduled slot. One line each; promote into the work plan when it is time. Not
authoritative; no review hook.
**Maintenance:** Owned by `update-backlog`, dispatched by `/update-context`.
Keep it terse — a backlog that reads like a plan has failed.

---

## Parked tasks

- **Publish v0.3.0** — PRs #1–#2 merged 2026-06-28; scope now also includes
  PR #5 (skill-family convention hardening). Bump the installed / marketplace
  plugin once PR #5 merges. Promoted to the work plan's next-up.
- **Re-home or cross-reference the foundational decisions** — decide whether
  prism ADR-0015 / 0016 / 0021 (the patterns this repo implements) get
  bozz-agents-local ADRs or stay cross-referenced from
  [ADR-0001](../docs/decisions/0001-bozz-agents-maintains-own-context.md).
  Trigger: when a foundational pattern next changes here.
