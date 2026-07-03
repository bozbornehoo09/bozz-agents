# bozz-agents — agent orientation

This repository is a portable set of **Agent Skills** for managing and reviewing
a project's authoritative knowledge. It is a developer tool, not an application:
there is no build, no runtime, no service. The deliverables are the `SKILL.md`
files under `skills/`.

## What lives here

- `skills/update-*/` — the **context-management** skills. `update-context` is the
  end-of-session orchestrator; the ten narrow `update-<layer>` skills each own
  one content layer (decisions, strategy, architecture, rules, AI tooling,
  open questions, work plan, backlog, orientation, work tracker).
- `skills/context-up/` — the **session-start** bookend: a read-only loader that
  resolves the layer map, loads the temporal core (latest tracker entry, work
  plan next-up), and expands by task intent under an anti-greed contract
  (index-first, fetch-only-cited).
- `skills/{docs,skill,plan,code}-review/` — the **review** family. Each
  orchestrates the specialist briefs bundled in its own `references/` directory,
  fans them out in parallel, and returns `BLOCK`/`FIX`/`SUGGEST` findings with a
  `READY` / `READY-WITH-FIXES` / `REVISE` verdict.

## Context system

This repo **dogfoods its own skills**: it declares its authoritative content
layers in `context-manifest.yaml` and runs the `update-*` / review skills on
itself *(see `docs/decisions/0001-bozz-agents-maintains-own-context.md`)*. The
layers are `docs/decisions/` (ADRs), `docs/concepts.md` (design), `skills/` (the
AI tooling), `docs/open_questions.md`, `work_tracker/` (work plan, backlog,
activity log), and this `AGENTS.md` (orientation). The `rules` and `strategy`
layers are intentionally omitted — this is a tool repo, so conventions live
below and positioning lives in `README.md`. End a working session with
`/update-context`.

## Conventions (keep these stable)

- Skills are authored to the open Agent Skills spec: a folder + `SKILL.md` with
  required `name` (lowercase-kebab, matching the folder) and `description`
  frontmatter. Keep each `SKILL.md` under ~500 lines; push detail into
  `references/`.
- Severity vocabulary is **BLOCK / FIX / SUGGEST**; verdicts are
  **READY / READY-WITH-FIXES / REVISE**. Do not introduce a second vocabulary —
  `cross-skill-consistency.md` exists to catch exactly that.
- Skill structure follows two family shapes (enforced by `skill-review`'s
  `structural-integrity` brief): review skills carry Corpus / Specialists /
  Orchestration / Output template / What-this-skill-is-NOT; authoring skills
  carry Scope / Steps / Pause-for-confirmation rules / Style, plus Output
  format when they emit a structured report.
- Specialist findings use the per-finding line
  `[lens] file:line [BLOCK|FIX|SUGGEST]`; review output headings are
  `# <Skill Name>: <subject>`.
- Every review specialist operates under the anti-hallucination contract:
  a finding without a verbatim quote and a `file:line` citation is dropped.

## Working in this repo

- Editing a skill or brief? Run `skill-review` afterward.
- Editing these docs (`README.md`, `AGENTS.md`, `docs/**`)? Keep them consistent
  with the skills they describe.
- `plan-review` and `code-review` are **skeletons**: generic machinery plus a
  `_brief-template.md`. They carry no real specialist briefs — a consumer adds
  briefs for their own architecture. The Prism project's real design briefs live
  in the Prism repo, not here (see `docs/prism-case-study.md`).

For Codex-specific install/usage, see `codex/README.md`.
