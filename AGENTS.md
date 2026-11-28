# bozz-agents — agent orientation

This repository is a portable set of **Agent Skills** for managing and reviewing
a project's authoritative knowledge. It is a developer tool, not an application:
there is no application runtime or service. The deliverables are the canonical
skill packages under `skills/` (including references and helper scripts), the
agent definitions under `agents/`, their generated discovery trees and Codex
roles, and thin per-host plugin/marketplace manifests.

## What lives here

- `skills/update-*/` — the **context-management** skills. `update-context` is the
  end-of-session orchestrator; the ten narrow `update-<layer>` skills each own
  one content layer (decisions, strategy, architecture, rules, AI tooling,
  open questions, work plan, backlog, orientation, work tracker).
- `skills/context-up/` — the **session-start** bookend: a read-only loader whose
  load is one capped script call (`scripts/load_context.py`: work plan next-up,
  decisions in force, latest tracker entries, repository state), then headings
  and grep at need under an anti-greed contract (index-first, fetch-only-cited).
- `skills/{docs,skill,plan,code,design-doc}-review/` — the **review** family.
  Each fans out its bundled specialist briefs; `plan-review` and `code-review`
  ship built-in generic lenses and also run consumer-supplied briefs made from
  `_brief-template.md` (ADR-0004). All use `BLOCK`/`FIX`/`SUGGEST` findings and
  a `READY` / `READY-WITH-FIXES` / `REVISE` verdict.
- `skills/{writing-implementation-plans,implementing-a-plan,preparing-code-reviews,deciding-calls-by-debate}/`
  — the **plan → build → PR** family: plan to a closed `plan-review` pass, build
  one step per commit, prepare one pull request, and settle reversible design
  calls by debate when the owner is away.
- `skills/{design-doc-write,design-doc-edit,refining-technical-writing,design-diagrams}/`
  — the **writing** family: design docs, prose and code comments, diagrams.
- `agents/` — the **manager/worker agents** (manager, architect, implementer,
  review-specialist, cold-reader, cold-reader-deep, artifact-verifier) and their
  shared contract and shell deny lists in `agents/shared/` (ADR-0005; see
  `docs/agents.md`). `codex/agents/*.toml` are generated from them. Session
  roles hand off at a size cap through the self-gated hook in `hooks/`
  (`agents/shared/scripts/ctxcap.sh`); the manager hands off to its own
  successor (`manager-handoff.zsh`); rules read only on a trigger live in
  `agents/shared/reference/` (ADR-0007). Script tests: `tests/test_agents_scripts.py`.
- `skills/{cross-review-requester,cross-reviewer,fold-review-findings}/` — the
  file-scoped **cross-agent review lifecycle**. The requester and reviewer both
  use ETA/grace-aware polling; every completed review passes through an
  independent finding-adjudication fold before edits (ADR-0003).

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
- Severity rule, stated identically everywhere: REVISE if any BLOCK;
  READY-WITH-FIXES if no BLOCK and at least one FIX; READY otherwise.
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
- Cross-review findings are hypotheses, not instructions. The requester always
  invokes `fold-review-findings` after `REVIEW_COMPLETE`; only independently
  confirmed findings may change the reviewed artifact (ADR-0003).
- Edit the canonical `skills/` tree only. The per-host discovery directories
  (`.claude/skills/`, `.agents/skills/`) are generated from it by
  `scripts/generate-tool-skills.sh` and carry GENERATED markers — never
  hand-edit them; regenerate instead. Per-host packaging is a thin manifest
  pointing at canonical `skills/`, never a fork (see ADR-0002). Likewise
  `codex/agents/*.toml` are generated by `agents/shared/build_codex_roles.py`;
  a new agent must also be listed in `.claude-plugin/plugin.json` `agents`.
- Installers download third-party tools pinned to a release at least two weeks
  old, with a checksum where upstream publishes one; never vendor them.

## Working in this repo

- Editing a skill or brief? Run `skill-review` afterward.
- Run the tests before committing: `python3 -I -m unittest discover -s tests`
  plus the per-skill script tests listed in `.github/workflows/validate-skills.yml`.
- Editing these docs (`README.md`, `AGENTS.md`, `docs/**`)? Keep them consistent
  with the skills they describe.
- `plan-review` and `code-review` carry **architecture-neutral** built-in
  lenses only. Anything specific to one architecture belongs in a consumer brief
  made from `_brief-template.md`, never in a built-in lens. The Prism project's
  real design briefs live in the Prism repo, not here (see
  `docs/prism-case-study.md`).

For Codex-specific install/usage, see `codex/README.md`.
