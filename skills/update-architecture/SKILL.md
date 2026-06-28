---
name: update-architecture
description: Update the architecture design and diagrams to synthesize new ADRs — new services, ports, principles. Use after architecture-affecting decisions land. Ends with docs-review.
---

# Update Architecture

Update the architecture design documents at
`<project-root>/docs/architecture/` to reflect ADR-driven
and in-session changes to the system design. The architecture doc is the
synthesized view that applies decisions in `docs/decisions/` and is cited
by the rule files in `.claude/rules/`.

This prompt is **downstream of** `update-decisions` (ADRs land first
because they decide) and **upstream of** `update-rules` (rule files
cite both ADRs and architecture sections). Run it after a new ADR lands
or after a session introduces a new service, port, principle, or
cross-cutting concern that the design doc should describe.

## Scope

In scope:
- `docs/architecture/architecture_design.md` — canonical design doc
- `docs/architecture/README.md` — overview and index of architecture docs
- `docs/architecture/architecture_diagram.mermaid` — visual system diagram

Out of scope:
- ADRs — `update-decisions`
- Rule files — `update-rules`
- Strategy docs (`docs/strategy/`) — separate prompt if added
- CLAUDE.md — separate prompt if added

## Steps

### 1. Read the current architecture set

Read all three in-scope files end-to-end. The design doc has a numbered
section structure (§1 principles, §2 services, §10 ports, §14 north star,
etc.) — preserve numbering across edits.

### 2. Discovery

PRIMARY SOURCE — the current conversation. Architectural changes surface
here first (a new service decision, a new port, a renumbering). Capture
these directly — a subagent cannot see them.

SECONDARY SOURCES — spawn ONE Explore subagent with this brief and use
only its summarized report:

> "Find architectural changes in <project-root> that may
> require updates to docs/architecture/. Check: (a) new ADRs in
> docs/decisions/ since the design doc's mtime — these are the
> canonical drivers of architectural change; (b) new rule files or
> CRITICAL OVERRIDE blocks in .claude/rules/ that imply a
> not-yet-documented service or port; (c) git log + status across
> src/ and infrastructure/ for evidence of new components; (d) the
> most recent work_tracker/ entries for explicit `Decided X` lines
> with architectural implications. Report a tight bullet list with
> file paths and the architectural concern each implies. Under 300
> words."

### 3. For each in-scope file, decide whether anything counts as a *durable* update

Durable means:
- A new service, port, or component reflected in an Accepted ADR
- A change to the principles section (§1) — almost always implies an ADR
- A new cross-cutting concern (e.g., §2.7 reserved future services, §14
  north star) introduced via strategy or ADR
- A renumbering or section reorganization
- A change to the visual diagram reflecting a structural change
- A correction or refinement to an existing description that brings it
  in line with current ADRs

NOT durable (do not add):
- Status updates, progress reports, or session narrative — those go in
  `work_tracker/`
- Speculative future architecture not yet committed via ADR
- The WHY behind a decision — that lives in the ADR; the design doc
  describes what currently is
- Implementation-level details derivable from code

### 4. Update the design doc

Edit `architecture_design.md` directly. Preserve section
numbering — when adding a new sub-section, slot it into the existing
numbering rather than renumbering the document. If renumbering is
necessary (rare), update every cross-reference (rules cite by section
number).

Add ADR citations inline where the change is driven by a specific ADR:
`(see docs/decisions/NNNN-slug.md)`. Citations are one-liners; do not
restate the ADR's content.

### 5. Update the diagram

If the change adds, removes, or repositions a service or port, update
`architecture_diagram.mermaid` in lockstep. PAUSE before any mermaid
edit — visual layout is a judgment call worth confirming.

### 6. Update the architecture README

If the design doc gains a new top-level section or the README's overview
of the architecture doc set is now stale, update `README.md`. Otherwise
leave it.

### 7. Run docs-review

After updates land, invoke the `docs-review` skill to verify no
consistency, coherence, decisional-clarity, or temporal-decay issues were
introduced. Read its report and either:
- **READY** → done.
- **READY-WITH-FIXES** → address the FIX/SUGGEST findings (or surface
  them and ask before proceeding).
- **REVISE** → BLOCK findings present; do not consider the architecture
  update complete until they are resolved.

## Pause-for-confirmation rules

Default to caution.

- PAUSE before adding a new top-level section (§) — changes the overall
  structure of the design doc.
- PAUSE before removing content from the design doc — content may be
  load-bearing for rules that cite it.
- PAUSE before any mermaid diagram edit.
- PAUSE before renumbering (almost never the right move; ripples
  through every citation).
- For additive sub-sections (new bullet under an existing §) and
  in-line citation additions, surface the diff and proceed unless
  ambiguous.

## Style

- The design doc describes what currently *is*. WHY-rationale lives in
  ADRs; the design doc cites ADRs but does not restate them.
- Numbered sections are stable identifiers — rules cite by section
  number. Do not renumber.
- Keep ADR citations inline and one-line: `(see docs/decisions/NNNN-slug.md)`.
- The mermaid diagram is the visual source of truth — when service
  topology changes, the diagram must change too.
- If an edit causes the design doc to conflict with an Accepted ADR,
  the ADR wins; surface the conflict rather than silently editing the
  doc to disagree with its source.

## Coordination with other update flows

- New ADR landed → run this prompt to propagate the architectural
  change into the design doc, then run `update-rules` if the rules
  need ADR citations or new constraints.
- This prompt always ends with `docs-review` — do not skip step 7.
