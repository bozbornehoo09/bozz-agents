---
name: update-orientation
description: Update the project orientation file (CLAUDE.md / AGENTS.md, or its neutral source) when it drifts from current state. Use when the auto-loaded onboarding context is stale. Ends with docs-review.
---

# Update Orientation

Update the project orientation to reflect changes in project
conventions, the skill set, the layer structure, or behavioral rules.
The orientation is loaded into **every** AI session, so drift here has
the highest blast radius of any single file in the project.

This skill is **downstream of** every other update skill: ADRs, rules,
architecture, strategy, and skills can all change in ways that should be
reflected in the orientation.

## Resolve the canonical source first

The orientation may be a single hand-edited file, or **generated** from
a tool-neutral canonical source (so one source produces `CLAUDE.md`,
`.agents/AGENTS.md`, and any other per-tool copy). **Never hand-edit a
generated file — the next regenerate clobbers your edit.**

1. **Locate the orientation.** If a project `context-manifest.yaml`
   declares an `orientation` path (or list of paths), inspect those;
   otherwise prefer a neutral `ORIENTATION.md`, then the orientation file the
   current host loaded (`AGENTS.md`, `CLAUDE.md`, or equivalent).
2. **Check whether it is generated.** A `<!-- GENERATED — do not edit -->`
   / `# GENERATED — do not edit` header marks the file as a build output
   (a generated *directory* is marked by a sibling `GENERATED.md` instead);
   it names both the **canonical source** (e.g. `ORIENTATION.md`) and the
   **regen command** (e.g. `scripts/generate-tool-context.sh`).
3. **Edit canonical, then regenerate.**
   - *Generated layout:* edit the canonical source the marker names, then
     run the regen command so every per-tool copy updates in lockstep.
     Tool-specific framing (install/invoke syntax) lives in the canonical
     source's per-tool fenced blocks — edit the matching block, not the
     generated output.
   - *Direct layout (no marker):* the located file is itself canonical —
     edit it directly.

Below, "the orientation" means the **canonical** source resolved here.

## Scope

In scope:
- The canonical orientation source (and, via regeneration, its per-tool
  copies).

Out of scope:
- Everything else. The orientation is a summary; it does not duplicate
  content owned by other docs. It points to them.

## Steps

### 1. Read the orientation

Read it end-to-end. The orientation typically covers:
- Project one-liner and pointer to the canonical design doc
- The context system (layer table + skill list)
- Behavioral rules (e.g., bulk-edit conventions)
- Anything else loaded reflexively into every session

### 2. Discovery — drift detection

PRIMARY SOURCE — the current conversation. Convention changes,
behavioral-rule additions, or new skills surface here first. Capture
directly.

SECONDARY SOURCES — run ONE discovery subagent using the host's subagent or
delegation facility with this brief:

> "Find drift between the canonical orientation source (resolved above)
> and current project state. Specifically check: (a) does the skill /
> update-* list in the orientation match the skills actually available?
> (b) does the layer table match the directories that exist
> (docs/decisions/, the canonical rules directory, work_tracker/, plus
> any new authoritative directories)? (c) do the behavioral rules
> reference tools or conventions that have since changed? (d) any new
> top-level authoritative directories the orientation should mention?
> Report a tight bullet list of mismatches with file paths. Under 300
> words."

### 3. Categorize the drift

For each mismatch, decide whether the orientation should change:
- **Yes** — a skill/layer count is wrong, a layer was added, a behavioral
  rule is stale, a referenced path moved
- **No** — the mismatch reflects a *temporary* state (uncommitted
  experimental directory, in-flight work). The orientation describes
  durable conventions, not temporary state.

### 4. Update the orientation

Edit the canonical source directly. The orientation is short on purpose —
every line is loaded into every session. Do not add prose; bullet lists,
tables, and pointers belong here. Long explanations belong in the doc the
orientation points to. Keep tool-specific text inside the per-tool fenced
blocks (generated layouts).

### 5. Regenerate (generated layouts only)

If the orientation is generated, run the regen command the marker named
(e.g. `scripts/generate-tool-context.sh`) so every per-tool copy reflects
the canonical edit. Confirm its `--check` (or equivalent) is clean.

### 6. Run docs-review

After updates land, invoke the `docs-review` skill — the orientation is
in scope for the `internal-consistency` and `temporal-decay` specialists.
An orientation that claims facts contradicting the rest of the project is
a load-bearing failure (every session reads it). Read its report and
either:
- **READY** → done.
- **READY-WITH-FIXES** → address the FIX/SUGGEST findings or surface
  them and ask before proceeding.
- **REVISE** → BLOCK findings present; do not consider the orientation
  update complete until they are resolved.

## Pause-for-confirmation rules

This content is loaded into every session. Default to maximum caution.

- PAUSE if you cannot tell whether the located orientation is canonical
  or generated — confirm before editing, never risk editing a build output.
- PAUSE before any change to behavioral rules — these directly modify how
  the AI behaves in every future session.
- PAUSE before any restructuring (adding a new section, removing a
  section, reordering sections).
- PAUSE before changing pointer paths (e.g., the design doc reference) —
  a stale pointer here propagates to every session.
- For numerical updates that reflect mechanical reality (skill count went
  from N to M, layer count went from X to Y), surface the diff and proceed
  unless ambiguous.

## Style

- Edit the **canonical** source, never a generated copy.
- Tight. The orientation is a tax on every session — every line should
  earn its place.
- Bullet points and tables, not prose.
- Pointers, not duplication. The orientation says "see X for details" and
  X owns the content.
- Behavioral rules are imperative ("use sed for project-wide
  substitutions"), not narrative.
- If a behavioral rule is unfalsifiable ("write good code"), it doesn't
  belong here — promote it to a rule file or strip it.
