# ADR-0005: Ship manager/worker agent definitions alongside the skills

**Status:** Accepted
**Date:** 2026-11-27
**Category:** Infrastructure

## Context

Skills describe *what* a step does; they do not say *who* runs it or how
several sessions coordinate. The maintainer's working model is a manager the
owner talks to, which briefs worker sessions (architect, implementer) and
read-only reviewer subagents (review specialist, cold readers, artifact
verifier), tracks their state, batches the owner's decisions, and never lets a
worker settle a design call. That model depends on agent definitions with
specific model tiers and tool limits, a shared worker contract, and a guard
against destructive shell commands. bozz-agents shipped skills only.

## Decision

1. **The plugin ships agent definitions** in `agents/`: `manager`, `architect`,
   `implementer` (session roles), and `review-specialist`, `cold-reader`,
   `cold-reader-deep`, `artifact-verifier` (read-only subagent roles). They are
   listed explicitly in `.claude-plugin/plugin.json` `agents`, because that key
   replaces the default directory scan and `agents/shared/` must not load as
   agents.
2. **Shared role material lives once** in `agents/shared/`: the worker contract,
   owner-talk and owner-override rules, and the shell deny lists.
3. **Codex roles are generated, not authored.** `agents/shared/build_codex_roles.py`
   writes `codex/agents/*.toml` for the subagent roles from the canonical `.md`
   files; the session roles run on Codex from an explicit prompt
   (`docs/agents.md`). This follows ADR-0002's generate-don't-fork rule.
4. **The shell guard is opt-in.** The deny lists, the PreToolUse hook and a
   settings snippet ship; nothing enables the hook for every session that has the
   plugin installed.
5. **Model tiers are pinned per role** to Claude's opus / sonnet / haiku aliases;
   no role uses a usage-billed tier.

## Alternatives considered

- **Leave agents to each user's own config.** Rejected: the skills reference
  roles (a cold reader, a review specialist) whose behaviour depends on tool
  limits; unshipped, every user rebuilds them differently.
- **Enable the shell guard by default.** Rejected: a plugin-wide hook changes
  every session's behaviour, including sessions unrelated to this workflow.
- **Hand-write the Codex roles.** Rejected by ADR-0002: two copies drift.

## Consequences

- **Positive:** the manager/worker workflow installs with the plugin, locally or
  in a cloud session, and the skills' role references resolve.
- **Negative:** agent files, the generator and the deny lists are new surface,
  with their own tests (`tests/test_agents*.py`).
- **Binds:** new agents MUST be added to `plugin.json` `agents`; Codex role files
  MUST be regenerated, never hand-edited; session roles never decide design
  calls (they escalate or use `deciding-calls-by-debate`).
- **Revisit when:** Codex supports session-level role definitions, or Claude
  Code changes how plugin agents restrict tools.

## References

- `agents/`, `agents/shared/`, `codex/agents/`, `docs/agents.md`
- Tests: `tests/test_agents.py`, `tests/test_agents_shell_deny.py`
- Related: [ADR-0002](0002-host-neutral-skills-generated-trees.md),
  [ADR-0004](0004-built-in-lenses-and-plan-build-family.md)
