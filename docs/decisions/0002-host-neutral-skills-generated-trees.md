# ADR-0002: Host-neutral skills, generated per-host trees, packaging by manifest

**Status:** Accepted
**Date:** 2026-07-18
**Category:** Infrastructure

## Context

bozz-agents targets multiple agent hosts (Claude Code, Codex, and others).
Each host discovers skills from its own directory (`.claude/skills/`,
`.agents/skills/`) and, increasingly, installs via its own plugin mechanism.
The skills also historically hardcoded Claude Code's layout in their prose —
`CLAUDE.md`, `.claude/rules/`, the named Explore subagent. Left unmanaged, this
pushes toward per-host *forks* of the skill content: divergent copies that
drift and multiply maintenance. A decision was needed on where the source of
truth lives and how each host is served from it. Until now the rationale lived
only in `concepts.md` prose and (upstream) in prism's ADRs — never recorded
here as a local, immutable decision.

## Decision

One canonical, host-neutral `skills/` tree is the single source of truth.

- **Neutral prose.** Skill content resolves context paths from
  `context-manifest.yaml` first, then neutral conventions (`ORIENTATION.md`,
  `rules/`, `skills/`) with host-specific fallbacks, and delegates subagent
  work to "the host's subagent facility" rather than naming a host-specific
  agent.
- **Generated discovery trees.** Per-host discovery dirs (`.claude/skills/`,
  `.agents/skills/`) are generated from canonical by
  `scripts/generate-tool-skills.sh`; CI regenerates on push, the trees carry
  GENERATED markers, and they are never hand-edited.
- **Packaging by manifest.** Per-host packaging is a thin manifest pointing at
  canonical `skills/` — `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`,
  and their marketplace files.

Adding a new host = add a manifest (and, if the host needs a discovery dir, a
generation target). Never fork the skill content.

## Alternatives considered

- **Hand-maintain a separate skill tree per host** — author `.claude/skills/`
  and `.agents/skills/` as first-class copies. Rejected: N copies drift, every
  edit is N× work, and the copies silently diverge from canonical intent.
- **Single tree, but keep host-specific prose in the canonical skills** (leave
  `CLAUDE.md`/Explore references inline, let other hosts cope). Rejected: bakes
  one host's vocabulary into the shared source, making every other host a
  second-class reader and the "portable" claim false.
- **Discovery dirs only, no packaging** (tell users to symlink/copy
  `.agents/skills/`). Rejected: works, but a worse install UX than each host's
  native plugin flow; manifests are cheap and additive.

## Consequences

- **Positive:** one place to edit; hosts stay in sync by construction; the
  portability claim in `concepts.md` is enforced by structure, not discipline.
  New hosts are cheap (a manifest).
- **Positive:** generated trees are reproducible and CI-verified; hand-edits to
  them are caught/overwritten rather than silently kept.
- **Negative:** a generation pipeline to maintain, plus a rule contributors
  must learn — edit canonical `skills/`, never the generated dirs.
- **Binds:** future host integrations MUST point packaging at canonical
  `skills/` and MUST NOT fork skill content; canonical prose MUST stay
  host-neutral (manifest-first path resolution, no host-specific agent names).
- **Revisit when:** a host diverges enough that generation can't bridge it —
  i.e., it needs semantically different skill *content*, not just a different
  directory or manifest.

## References

- Design: `docs/concepts.md` ("Why this is portable")
- Related: [ADR-0001](0001-bozz-agents-maintains-own-context.md) — names the
  canonical-tree-with-per-tool-generation pattern in passing; this ADR
  formalizes it.
- Generation: `scripts/generate-tool-skills.sh`;
  `.github/workflows/generate-tool-skills.yml`, `validate-skills.yml`
- Packaging: `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`,
  `.agents/plugins/marketplace.json`
- Origin patterns: prism ADR-0015 / ADR-0016 / ADR-0021 (extracted from)
