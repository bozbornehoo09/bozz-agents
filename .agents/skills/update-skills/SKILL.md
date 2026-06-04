---
name: update-skills
description: Update the project's AI tooling — skills and specialist briefs — when conventions shift. Use after adding a content domain or refining a review contract. Ends with skill-review.
---

Update the AI tooling under `<project-root>/.claude/skills/`
and `<project-root>/.claude/review-context/` to reflect
changes in project conventions, the corpus the skills review, or the
workflows they support. Skills are meta-tooling — they orchestrate AI
behavior within the project. Like rules, they describe a current state
the AI loads as authoritative; like ADRs, they have structural
conventions worth preserving.

## Scope

In scope:
- `.claude/skills/*/SKILL.md` — skill definitions (YAML frontmatter +
  body).
- `.claude/review-context/*.md` — specialist briefs invoked by skills.

Out of scope:
- `prompts/*.md` — orchestration prompts; updated by hand or via a
  future `/update-prompts` flow.
- `.claude/rules/*.md` — covered by `update-rules`.
- `docs/decisions/*.md` — covered by `update-decisions`.

## Steps

### 1. Read the existing skill set

Read every current `SKILL.md` under `.claude/skills/` and every brief
under `.claude/review-context/` to understand established structure,
specialist conventions, anti-hallucination contracts, output formats, and
which skills invoke which briefs.

### 2. Discovery

PRIMARY SOURCE — the current conversation. Skill changes typically arise
from session-level decisions about how AI tooling should behave.
Capture these directly — a subagent cannot see them.

SECONDARY SOURCES — spawn ONE Explore subagent with this brief:

> "Find what's changed in <project-root> that may require
> updates to AI skills or specialist briefs. Check: (a) new directories
> under docs/ that should be added to docs-review's corpus globs;
> (b) new ADR Status values, rule structural conventions, or other
> doc conventions that briefs reference; (c) git log + status across
> .claude/ since the oldest mtime in .claude/skills/. Report a tight
> bullet list with file paths. Under 300 words."

### 3. For each skill, decide whether anything counts as a *durable* update

Durable means:
- A new corpus directory or glob to add (e.g., `docs/specs/` introduced)
- A new specialist brief to add (a genuinely new lens emerges that the
  existing briefs don't cover)
- A refinement to an anti-hallucination contract based on an observed
  failure mode
- An updated output format reflecting better aggregation discipline
- A change in how the orchestrator coordinates specialists (e.g., the
  status-manifest pattern in `docs-review`)
- A new skill entirely (rare — implies a new repeatable workflow)

NOT durable (do not add):
- One-off prompt tweaks for a single invocation
- Speculative new skills with no concrete trigger
- Stylistic preferences without a reasoning anchor
- Implementation-level details derivable from the existing skill text

### 4. Cross-reference verification

Each `SKILL.md` references its specialist briefs by path. Verify:
- Every brief listed in a `SKILL.md` actually exists in
  `.claude/review-context/`.
- Every brief in `.claude/review-context/` is referenced by at least one
  `SKILL.md`. Orphaned briefs are dead weight — surface for deletion.
- Corpus globs in `SKILL.md` and the briefs it invokes are consistent.
  If `SKILL.md` scopes `docs/strategy/*.md` but a brief lists individual
  files, fix the brief.
- ADR conventions referenced by briefs match current state. If the ADR
  README adds a new Status value (e.g., `Deprecated`), every brief that
  handles status needs the new value reflected.
- Rule conventions referenced by briefs match current state (e.g., if
  rules adopt a new structural anchor, briefs that check structure need
  updating).

### 5. Handle new skills

If the conversation surfaced a new repeatable workflow that fits the
skill pattern (consistent input shape, parallel specialists adding
value, structured output worth standardizing), PAUSE and propose
creating a new skill. Don't create silently.

A new skill is justified when all of:
- The pattern will be re-invoked across many sessions, not once.
- The input shape stabilizes — same question family every time.
- Coordinating multiple specialists adds enough structure to justify
  the file (versus a one-shot subagent prompt).

### 6. Handle new specialist briefs

If a new lens emerges within an existing skill (a failure mode the
current briefs miss), PAUSE and propose adding a brief. The brief must:
- Have a single, sharp scope — no overlap with existing briefs.
- Reference the same anti-hallucination contract as its sibling briefs.
- Use the same output format conventions.
- Be invoked from at least one `SKILL.md`.

### 7. Run skill-review

After skill or brief updates land, invoke the `skill-review` skill to
verify structural integrity (frontmatter, required sections, brief
references intact), anti-hallucination contract quality, scope focus
(single-purpose discipline, no overlap), and cross-skill consistency
(severity vocabulary, verdict labels, output templates). Read its
report and either:
- **READY** → done.
- **READY-WITH-FIXES** → address the FIX/SUGGEST findings or surface
  them and ask before proceeding.
- **REVISE** → BLOCK findings present; do not consider the skill
  update complete until they are resolved.

## Pause-for-confirmation rules

Default to caution; loosen as trust grows.

- PAUSE for any change to a skill's anti-hallucination contract — this
  is load-bearing for review quality and cross-cuts every specialist.
- PAUSE before adding or removing a specialist brief — it changes the
  fan-out shape of a skill.
- PAUSE before deleting a skill — a refactor or merge is usually the
  right move, not a delete.
- PAUSE before deleting a brief unless explicitly orphaned (referenced
  by no `SKILL.md`).
- PAUSE before modifying an output format — downstream aggregation
  depends on it.
- For additive changes (new corpus glob, new check item in a brief, new
  optional output field), surface the diff and proceed unless ambiguous.

## Style

- Preserve YAML frontmatter conventions in `SKILL.md`: `name:` (no
  leading slash), `description:` (one line, used for slash-command
  surfacing).
- Preserve brief structure: `Authoritative corpus`, `Check for (in
  order of importance)`, `Anti-hallucination contract`, `Out of scope`,
  `Output format`, closing line `Empty report is a valid result. Do not
  invent findings to look thorough.`
- Keep anti-hallucination contracts visible and explicit — never bury
  them in prose.
- Skills are tooling, not journals. No date stamps inside.
- Briefs are scoped — keep each brief to a single lens. If two briefs
  drift toward overlapping checks, surface the conflict rather than
  silently letting both flag the same thing.
- If an edit causes a `SKILL.md` to drift from its briefs (e.g.,
  `SKILL.md` lists four briefs but only three exist), surface the
  conflict rather than silently picking a side.

## Coordination with other update flows

- New ADR Status conventions → `update-decisions` lands the ADR
  README change first; THEN run this prompt to propagate the new value
  through brief status-handling sections.
- New `docs/` directory or new authoritative doc class → run this
  prompt to add the directory to the relevant skill's corpus globs.
- New rule structural anchor → `update-rules` lands the rule
  convention; THEN this prompt updates briefs that check structure.

This prompt is downstream of `update-decisions` and
`update-rules`. Run it after either of those when their changes
affect what the skills review.
