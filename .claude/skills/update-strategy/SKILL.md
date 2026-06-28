---
name: update-strategy
description: Update strategy and positioning docs to reflect new decisions or research artifacts. Use when positioning shifts or a strategy doc needs reconciling with landed ADRs. Ends with docs-review.
---

# Update Strategy

Update the strategy documents at
`<project-root>/docs/strategy/` to reflect positioning,
competitive analysis, and north-star refinements that surfaced during
recent work. Strategy docs are the WHY-of-the-business layer — what
the project is for in the market, who it serves, what it deliberately does
not do.

This prompt is **parallel to** `update-decisions` (ADRs) — strategy
informs which ADRs get written, and ADRs reflect strategic
constraints, but neither is downstream of the other.

## Scope

In scope:
- `docs/strategy/north_star.md` — north-star trajectory, framing
  decisions, reserved future services
- `docs/strategy/competitive_positioning.md` — where the project wins, where
  it doesn't, where it's vulnerable

Out of scope:
- `docs/strategy/research/**` — preserved source artifacts; immutable
  by convention. Research is read; it is never edited.
- `docs/decisions/*.md` — `update-decisions`
- `docs/architecture/*` — `update-architecture`

## Steps

### 1. Read the current strategy set

Read both in-scope files end-to-end. The strategy docs cite each other
and cite ADRs — preserve cross-references.

### 2. Discovery

PRIMARY SOURCE — the current conversation. Strategy shifts surface
here first (a new vertical considered, a competitive observation, a
revised north-star framing). Capture these directly — a subagent
cannot see them.

SECONDARY SOURCES — spawn ONE Explore subagent with this brief:

> "Find changes in <project-root> that may require
> updates to strategy docs. Check: (a) new research artifacts in
> docs/strategy/research/ since the strategy docs' mtime — these
> often drive positioning revisions; (b) new ADRs in docs/decisions/
> with strategic implications (e.g., a new architectural constraint
> driven by a market wedge); (c) recent work_tracker/ entries
> mentioning competitive analysis, vertical decisions, or
> positioning. Report a tight bullet list with file paths and the
> strategic implication of each. Under 300 words."

### 3. For each in-scope file, decide whether anything counts as a *durable* update

Durable means:
- A new vertical or wedge analyzed (competitive_positioning)
- A revision to where the project does or does not try to win
- A north-star refinement (a new reserved future service, a tightened
  trajectory framing)
- A correction to a positioning claim now contradicted by new research
- A new ADR-driven strategic constraint that should be reflected in
  positioning

NOT durable (do not add):
- Speculative product features without research backing
- Marketing copy or external messaging — strategy docs are internal
- Status updates / progress reports — those go in `work_tracker/`
- The full text of new research — that lives in
  `docs/strategy/research/` as a preserved artifact

### 4. Update the strategy docs

Edit `north_star.md` and `competitive_positioning.md` directly. Cite
research artifacts by path when introducing claims sourced from them:
`per docs/strategy/research/YYYY-MM-DD_<source>_<topic>.md`.

Cite ADRs the same way as elsewhere:
`(see docs/decisions/NNNN-slug.md)`.

### 5. Run docs-review

After updates land, invoke the `docs-review` skill to verify strategy
claims have architectural mechanisms (the
`strategy-architecture-coherence` specialist), that no new claims age
without dating (`temporal-decay`), and that strategy docs don't
contradict ADRs or architecture (`internal-consistency`). Read its
report and either:
- **READY** → done.
- **READY-WITH-FIXES** → address the FIX/SUGGEST findings or surface
  them and ask before proceeding.
- **REVISE** → BLOCK findings present; do not consider the strategy
  update complete until they are resolved.

## Pause-for-confirmation rules

- PAUSE before any change to the north-star trajectory (the long-arc
  framing of what the project is becoming).
- PAUSE before any change to the "what we don't do" / "where the project
  does not try to win" sections — these are deliberate exclusions
  with downstream architectural consequences.
- PAUSE before adding a new reserved future service to north_star.md.
- For additive analysis (new competitor row, new wedge bullet, new
  research citation), surface the diff and proceed unless ambiguous.

## Style

- Strategy docs are internal, written for engineers and AI assistants
  reasoning about positioning. Not marketing copy.
- Be honest about vulnerability — `competitive_positioning.md` has a
  "where the project is genuinely vulnerable" section. Drift toward only
  flattering claims is a degradation.
- Cite research artifacts to ground claims; un-sourced market claims
  are a temporal-decay liability.
- The `research/` subdirectory is immutable — never edit a preserved
  artifact. Corrections go in the synthesized strategy doc, with a
  note flagging the artifact's known errors.
