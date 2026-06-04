---
name: update-orientation
description: Update the project orientation file (CLAUDE.md / AGENTS.md) when it drifts from current state. Use when the auto-loaded onboarding context is stale. Ends with docs-review.
---

Update `<project-root>/CLAUDE.md` to reflect changes in
project conventions, the prompt set, the layer structure, or behavioral
rules. CLAUDE.md is the project orientation file — it is loaded into
**every** AI session, so drift here has the highest blast radius of any
single file in the project.

This prompt is **downstream of** every other update prompt: ADRs,
rules, architecture, strategy, skills, and prompts can all change in
ways that should be reflected in CLAUDE.md's orientation.

## Scope

In scope:
- `<project-root>/CLAUDE.md`

Out of scope:
- Everything else. CLAUDE.md is an orientation summary; it does not
  duplicate content owned by other docs. It points to them.

## Steps

### 1. Read CLAUDE.md

Read it end-to-end. CLAUDE.md typically covers:
- Project one-liner and pointer to the canonical design doc
- The context system (layer table + prompt list)
- Behavioral rules (e.g., bulk-edit conventions, sed-vs-Edit guidance)
- Anything else loaded reflexively into every session

### 2. Discovery — drift detection

PRIMARY SOURCE — the current conversation. Convention changes,
behavioral-rule additions, or new prompts/skills surface here first.
Capture directly.

SECONDARY SOURCES — spawn ONE Explore subagent with this brief:

> "Find drift between CLAUDE.md at <project-root>/CLAUDE.md
> and current project state. Specifically check: (a) does the prompt
> list in CLAUDE.md match the actual files in prompts/? (b) does the
> layer table match the directories that exist (docs/decisions/,
> .claude/rules/, work_tracker/, plus any new authoritative
> directories)? (c) do the behavioral rules reference tools or
> conventions that have since changed? (d) any new top-level
> directories under .claude/ (skills/, review-context/, etc.) that
> CLAUDE.md should mention? Report a tight bullet list of mismatches
> with file paths. Under 300 words."

### 3. Categorize the drift

For each mismatch, decide whether CLAUDE.md should change:
- **Yes** — prompt count is wrong, a layer was added, a behavioral
  rule is stale, a referenced path moved
- **No** — the mismatch reflects a *temporary* state (uncommitted
  experimental directory, in-flight work). CLAUDE.md describes
  durable conventions, not temporary state.

### 4. Update CLAUDE.md

Edit directly. CLAUDE.md is short on purpose — every line is loaded
into every session. Do not add prose; bullet lists, tables, and
pointers belong here. Long explanations belong in the doc CLAUDE.md
points to.

### 5. Run docs-review

After updates land, invoke the `docs-review` skill — CLAUDE.md is in
scope for the `internal-consistency` and `temporal-decay` specialists.
A CLAUDE.md that claims facts contradicting the rest of the project
is a load-bearing failure (every session reads it). Read its report
and either:
- **READY** → done.
- **READY-WITH-FIXES** → address the FIX/SUGGEST findings or surface
  them and ask before proceeding.
- **REVISE** → BLOCK findings present; do not consider the CLAUDE.md
  update complete until they are resolved.

## Pause-for-confirmation rules

This file is loaded into every session. Default to maximum caution.

- PAUSE before any change to behavioral rules — these directly
  modify how the AI behaves in every future session.
- PAUSE before any restructuring (adding a new section, removing a
  section, reordering sections).
- PAUSE before changing pointer paths (e.g., the design doc
  reference) — a stale pointer here propagates to every session.
- For numerical updates that reflect mechanical reality (prompt
  count went from N to M, layer count went from X to Y), surface
  the diff and proceed unless ambiguous.

## Style

- Tight. CLAUDE.md is a tax on every session — every line should
  earn its place.
- Bullet points and tables, not prose.
- Pointers, not duplication. CLAUDE.md says "see X for details" and
  X owns the content.
- Behavioral rules are imperative ("use sed for project-wide
  substitutions"), not narrative.
- If a behavioral rule is unfalsifiable ("write good code"), it
  doesn't belong here — promote it to a rule file or strip it.
