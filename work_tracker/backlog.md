# bozz-agents — Backlog

**As of:** 2026-11-27
**Status:** Longer-term parking lot — deferred *tasks* with a trigger but no
scheduled slot. One line each; promote into the work plan when it is time. Not
authoritative; no review hook.
**Maintenance:** Owned by `update-backlog`, dispatched by `/update-context`.
Keep it terse — a backlog that reads like a plan has failed.

---

## Parked tasks

- **Re-home or cross-reference the foundational decisions** — decide whether
  prism ADR-0015 / 0016 / 0021 (the patterns this repo implements) get
  bozz-agents-local ADRs or stay cross-referenced from
  [ADR-0001](../docs/decisions/0001-bozz-agents-maintains-own-context.md).
  Trigger: when a foundational pattern next changes here.
- **Grouped cross-review runs** — a supervisor that launches several reviewers
  for one request and collects their reviews. Rejected for the 2026-11 port as
  host-CLI-specific. Trigger: when two or more reviewer hosts are used routinely.
- **Verify host-specific agent notes** — `docs/agents.md` flags
  `worktree.bgIsolation`, `claude respawn/stop/attach`, plugin-scoped
  `--agent` names and `Read(~/.ssh/**)` deny syntax as unverified. Trigger:
  before relying on them in a cloud session.
- **Render-check the diagram example** — `design-diagrams`' example `.drawio`
  and the macOS draw.io installer have not been run end to end. Trigger: first
  machine with draw.io installed.
