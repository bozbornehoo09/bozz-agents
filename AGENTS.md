# bozz-agents — agent orientation

This repository is a portable set of **Agent Skills** for managing and reviewing
a project's authoritative knowledge. It is a developer tool, not an application:
there is no build, no runtime, no service. The deliverables are the `SKILL.md`
files under `skills/`.

## What lives here

- `skills/update-*/` — the **context-management** skills. `update-context` is the
  end-of-session orchestrator; the eight narrow `update-<layer>` skills each own
  one authoritative content layer (decisions, strategy, architecture, rules,
  AI tooling, open questions, orientation, work tracker).
- `skills/{docs,skill,plan,code}-review/` — the **review** family. Each
  orchestrates the specialist briefs bundled in its own `references/` directory,
  fans them out in parallel, and returns `BLOCK`/`FIX`/`SUGGEST` findings with a
  `READY` / `READY-WITH-FIXES` / `REVISE` verdict.

## Conventions (keep these stable)

- Skills are authored to the open Agent Skills spec: a folder + `SKILL.md` with
  required `name` (lowercase-kebab, matching the folder) and `description`
  frontmatter. Keep each `SKILL.md` under ~500 lines; push detail into
  `references/`.
- Severity vocabulary is **BLOCK / FIX / SUGGEST**; verdicts are
  **READY / READY-WITH-FIXES / REVISE**. Do not introduce a second vocabulary —
  `cross-skill-consistency.md` exists to catch exactly that.
- Every review specialist operates under the anti-hallucination contract:
  a finding without a verbatim quote and a `file:line` citation is dropped.

## Working in this repo

- Editing a skill or brief? Run `skill-review` afterward.
- Editing these docs (`README.md`, `AGENTS.md`, `docs/**`)? Keep them consistent
  with the skills they describe.
- The `plan-review` and `code-review` briefs under their `references/` are the
  **Prism** worked example — project-specific by design. Don't genericize them;
  they demonstrate how a consumer writes their own domain briefs.

For Codex-specific install/usage, see `codex/README.md`.
