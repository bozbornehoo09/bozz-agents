---
name: update-rules
description: Update per-package architectural rule files to reflect new ADRs or design shifts. Use when a decision changes a package's hard rules. Ends with docs-review.
---

Update the per-package architectural rule files at <project-root>/.claude/rules/
to reflect durable WHAT-decisions from recent work. Rules are per-package
design documents the AI loads as authoritative context whenever it touches
the matching files. Rationale ("why") lives in `docs/decisions/` (ADRs),
not here.

## Steps

### 1. Read the existing rule files

Read every current rule file under `.claude/rules/` to understand existing
scope, descriptions, and constraints.

### 2. Discovery

PRIMARY SOURCE — the current conversation. Decisions and design changes
surface here first; capture them directly.

SECONDARY SOURCES — spawn ONE Explore subagent with this brief:

> "Find what's changed that may require updates to per-package design
> rules in <project-root>/.claude/rules/. Check:
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

### 6. Run docs-review

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
- PAUSE for any change that rewrites a CRITICAL OVERRIDE block.
- PAUSE for any change that removes or weakens a hard rule.
- PAUSE before creating a new rule file.
- PAUSE before deleting a rule file (very rare — the right move is usually
  a superseding ADR plus a citation update, not deletion).
- For additive changes (new hard rule, new out-of-scope clarification, new
  ADR cross-reference), surface the diff and proceed unless ambiguous.

## Style

- Preserve the `glob:` frontmatter and structural conventions
  (CRITICAL OVERRIDE blocks, hard-rule lists, out-of-scope sections).
- Rule files are durable design guidance, not a changelog. No date stamps
  inside.
- Each rule file describes its package: purpose and scope, services owned,
  public contracts, hard rules, out-of-scope clarifications.
- If an edit causes a rule to conflict with itself, surface the conflict
  rather than silently picking a side.
