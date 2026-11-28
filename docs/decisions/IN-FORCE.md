# Decisions in force — bozz-agents

Map last changed: 2026-11-27

## In force

### Context and layers
- bozz-agents declares its own layers in `context-manifest.yaml` and runs its own update and review skills on itself (ADR-0001).
- `context-up` loads through one capped script call, and update skills read layers by that load, headings and grep rather than whole files (ADR-0007).

### Packaging
- `skills/` is the only canonical tree; `.claude/skills/` and `.agents/skills/` are generated and never hand-edited, and per-host packaging is a thin manifest (ADR-0002).
- Codex agent roles are generated from the canonical agent files, never hand-written (ADR-0005, under ADR-0002's rule).

### Review
- Review skills use BLOCK / FIX / SUGGEST and READY / READY-WITH-FIXES / REVISE; `plan-review` and `code-review` ship built-in generic lenses, and project briefs run alongside them (ADR-0004).
- Cross-agent reviews are file-scoped, and every completed review passes an independent fold before edits (ADR-0003); scope may be pinned by content fingerprint, a stale-baseline review closes nothing, and relayed reviewers are marked `RELAYED:` (ADR-0006).

### Agents
- The plugin ships manager, architect, implementer and four read-only reviewer roles, listed explicitly in `plugin.json`; session roles never decide design calls; the shell guard is opt-in (ADR-0005).
- Session roles hand off at a size cap through a self-gated plugin hook, the manager hands off to its own successor, prompts keep rare rules in reference files, and each role lists only the subagents it dispatches (ADR-0007).

### Third-party tools
- Installers download pinned releases at least two weeks old and check checksums where upstream publishes them; nothing is vendored (ADR-0004).

## Unclear
