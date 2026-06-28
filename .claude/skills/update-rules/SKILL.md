---
name: update-rules
description: Update per-package architectural rule files to reflect new ADRs or design shifts. Use when a decision changes a package's hard rules. Ends with docs-review.
---

# Update Rules

Update the per-package architectural rule files to reflect durable
WHAT-decisions from recent work. Rules are per-package design documents
the AI loads as authoritative context whenever it touches the matching
files. Rationale ("why") lives in `docs/decisions/` (ADRs), not here.

## Resolve the canonical source first

Rule files may be authored directly, or **generated** from a tool-neutral
canonical source (so one set of rules serves Claude, Antigravity, and
other tools). **Never hand-edit a generated file — the next regenerate
clobbers your edit.**

1. **Locate the rules.** If a project `context-manifest.yaml` declares a
   `rules` layer `path`, start there; otherwise default to `.claude/rules/`.
2. **Check whether it is generated.** A sibling `GENERATED.md`, or a
   `<!-- GENERATED — do not edit -->` / `# GENERATED — do not edit` header,
   marks the directory as a build output. The marker names both the
   **canonical source** (e.g. `rules/`) and the **regen command** (e.g.
   `scripts/generate-tool-context.sh`).
3. **Edit canonical, then regenerate.**
   - *Generated layout:* edit the canonical source the marker names, then
     run the regen command so every per-tool copy updates in lockstep.
   - *Direct layout (no marker):* the located directory is itself canonical
     — edit it directly.

Below, "the rule files" always means the **canonical** ones resolved here.

## Steps

### 1. Read the existing rule files

Read every current canonical rule file to understand existing scope,
descriptions, and constraints.

### 2. Discovery

PRIMARY SOURCE — the current conversation. Decisions and design changes
surface here first; capture them directly.

SECONDARY SOURCES — spawn ONE Explore subagent with this brief:

> "Find what's changed that may require updates to the per-package design
> rules in <the canonical rules directory resolved above>. Check:
> (a) any new ADRs in docs/decisions/ since the oldest rule file mtime
> (these are the canonical source for durable decisions); (b)
> `git log --since=<that mtime>` + `git status` and file mtimes under
> src/, infrastructure/, docs/; (c) work_tracker/ entries from this
> week and last week. Report a tight bullet list of changes with file
> paths. Under 300 words."

### 3. For each rule file, decide whether anything counts as a *durable* update

Durable means:
- A new component, responsibility, or service the package owns
- A change to what the package does or how it fits into the architecture
- A new or changed public contract / interface the package exposes
- A new constraint or hard rule the AI should treat as fact
- A correction or refinement to an existing rule or description
- A change to the cloud / service mapping or to a port's contract
- A new out-of-scope clarification (with a pointer to where it now lives)

NOT durable (do not add):
- One-off bug fixes or implementation details derivable from code
- Status updates / progress reports — those go in `work_tracker/`
- Speculative future plans not yet committed-to
- The WHY behind a decision — that goes in the ADR; the rule cites the ADR

### 4. Add ADR citations

When a rule changes because of a specific ADR, add or update a citation:
`(see docs/decisions/NNNN-slug.md)`. Citations are one-liners; do not
restate the ADR's content in the rule.

### 5. Handle new packages or concerns

If a brand-new package has emerged with no rule file, PAUSE and propose
creating one (snake_case naming consistent with existing files). Do not
create silently.

### 6. Regenerate (generated layouts only)

If the rules are generated, run the regen command the marker named (e.g.
`scripts/generate-tool-context.sh`) so the per-tool copies reflect the
canonical edits. Confirm its `--check` (or equivalent) is clean before
moving on.

### 7. Run docs-review

After rule updates land, invoke the `docs-review` skill to verify rule
edits did not desync from the ADRs they cite, contradict the
architecture design doc, or break propagation of cross-cutting concerns
(tenancy, self-host capability, two-pass cognition). Read its report
and either:
- **READY** → done.
- **READY-WITH-FIXES** → address the FIX/SUGGEST findings or surface
  them and ask before proceeding.
- **REVISE** → BLOCK findings present; do not consider the rule update
  complete until they are resolved.

## Pause-for-confirmation rules

Default to caution; loosen as trust grows.
- PAUSE if you cannot tell whether the located rules are canonical or
  generated — confirm before editing, never risk editing a build output.
- PAUSE for any change that rewrites a CRITICAL OVERRIDE block.
- PAUSE for any change that removes or weakens a hard rule.
- PAUSE before creating a new rule file.
- PAUSE before deleting a rule file (very rare — the right move is usually
  a superseding ADR plus a citation update, not deletion).
- For additive changes (new hard rule, new out-of-scope clarification, new
  ADR cross-reference), surface the diff and proceed unless ambiguous.

## Style

- Edit the **canonical** source, never a generated copy.
- Preserve the `glob:` frontmatter and structural conventions
  (CRITICAL OVERRIDE blocks, hard-rule lists, out-of-scope sections).
- Rule files are durable design guidance, not a changelog. No date stamps
  inside.
- Each rule file describes its package: purpose and scope, services owned,
  public contracts, hard rules, out-of-scope clarifications.
- If an edit causes a rule to conflict with itself, surface the conflict
  rather than silently picking a side.
