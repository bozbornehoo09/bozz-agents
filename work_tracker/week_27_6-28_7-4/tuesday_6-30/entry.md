# Tuesday 2026-06-30 — Context bootstrap landed

## Landed
- **bozz-agents PR #3 merged** (`1a8ae1e`) — the repo now maintains its own
  context (→ ADR-0001): `context-manifest.yaml`, `docs/decisions/`, the
  `AGENTS.md` "Context system" section, `work_tracker/`, and a seeded
  `backlog.md`. All three PRs from this arc are now on master: #1 (`update-backlog`
  skill), #2 (skill-family structure cleanup), #3 (context bootstrap).

## Up next
- **Publish v0.3.0** — the *installed* plugin is still cached at v0.2.0, so the
  merged skills (incl. `update-backlog`) haven't reached consumers yet; bump the
  marketplace / installed version. Parked in `work_tracker/backlog.md`.
- Deferred SUGGEST-level skill cleanups remain in the backlog.
