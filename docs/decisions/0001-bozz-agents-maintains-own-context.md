# ADR-0001: bozz-agents maintains its own context

**Status:** Accepted
**Date:** 2026-06-29

## Context

bozz-agents ships the context-management (`update-*`) and review skills, but
until now did not apply them to itself. Its own design decisions — the
review-skill family pattern, the discover-and-dispatch orchestrator, the
canonical `skills/` tree with per-tool generation — were recorded only in the
**prism** project's ADRs (prism ADR-0015, ADR-0016, ADR-0021), from which this
repo was extracted. As bozz-agents evolves on its own (new skills like
`update-backlog`, contract refinements, the generation pipeline), there was no
local authoritative record of *why*, and no mechanism keeping `AGENTS.md`, the
skills, and the docs coherent as they drift.

## Decision

bozz-agents declares its own authoritative content layers in a root
`context-manifest.yaml` and runs the `update-*` / review skills on itself
(dogfooding). The layers:

- **decisions** → `docs/decisions/`; **architecture** → `docs/concepts.md`;
  **ai-tooling** → `skills/` (canonical; the per-tool `.claude/` / `.agents/`
  copies are generated); **open-questions** → `docs/open_questions.md`;
  **work-plan / backlog / work-tracker** → `work_tracker/`;
  **orientation** → `AGENTS.md`.
- The `rules` and `strategy` layers are **omitted**: this is a developer-tool
  repo with no application packages — conventions live in `AGENTS.md`,
  positioning in `README.md`.
- `plan-review` / `code-review` stay skeletons (no architecture briefs of their
  own); `docs-review` and `skill-review` are the load-bearing reviewers here.

## Consequences

- **+** Dogfooding surfaces skill bugs and rough edges before users hit them;
  the repo doubles as a worked example of its own pattern.
- **+** Decisions, orientation, and skills stay coherent via the same skills the
  project ships — drift is caught by `docs-review` / `skill-review`.
- **−** A second context to keep current (mild maintenance overhead).
- **−** Two homes for the foundational decisions: the originals stay in prism's
  ADRs (immutable there); this repo cross-references rather than duplicating
  them, and records *new* repo-specific decisions here going forward.
