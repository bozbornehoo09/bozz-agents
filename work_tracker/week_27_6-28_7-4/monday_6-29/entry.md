# Monday 2026-06-29 — Bootstrap bozz-agents' own context system

## Decisions
- bozz-agents now maintains its own context layers and dogfoods the `update-*` /
  review skills on itself. → ADR-0001

## Implemented
- `context-manifest.yaml` (root) — declares this repo's layers (decisions;
  architecture → `docs/concepts.md`; ai-tooling → `skills/`; open-questions;
  work-plan / backlog / work-tracker; orientation → `AGENTS.md`; `rules` and
  `strategy` omitted — tool repo).
- `docs/decisions/` — index `README.md` + `0001-bozz-agents-maintains-own-context.md`.
- `AGENTS.md` — new "Context system" section.
- `work_tracker/` — this entry + seeded `backlog.md`.

## Also this session (cross-repo)
- **bozz-agents** PR #1 — `update-backlog` skill + wiring (v0.2.0 → v0.3.0) —
  **merged**; PR #2 — skill-family structure cleanup (FIX-level drift from a
  `skill-review` pass) — **merged**. (Both landed 2026-06-28.)
- **prism** PR #17 — backlog content domain + the work-plan slim-down — **merged**;
  PR #18 — the session-log conflict it caused, resolved (mergeable).

## Up next
- Publish v0.3.0 (PR #1 + #2 merged; bump the installed / marketplace plugin).
  Deferred skill-polish items are parked in `work_tracker/backlog.md`.
