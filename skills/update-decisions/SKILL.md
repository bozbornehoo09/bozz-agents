---
name: update-decisions
description: Capture WHY-rationale as immutable Architecture Decision Records (ADRs). Use after a decision is made that genuinely binds future work; writes a new numbered ADR and supersedes rather than edits. Ends with docs-review.
---

# Update Decisions

Update the Architecture Decision Records (ADRs) at <project-root>/docs/decisions/
to capture WHY-rationale for decisions made in recent work. ADRs are
*immutable* — never edit an accepted ADR's Decision or Alternatives. When
something changes, write a NEW ADR that supersedes the old one.

## Scope

In scope:
- `docs/decisions/*.md` — the ADR files
- `docs/decisions/README.md` — the status index

Out of scope:
- open-questions reconciliation → `update-open-questions`
- propagating decisions into the architecture design →
  `update-architecture`
- propagating decisions into rule files → `update-rules`
- the work plan → `update-work-plan`

## Steps

### 1. Read the existing ADRs

Read `docs/decisions/README.md` (the index) and the most recent ADRs to
understand what is already captured and the next available number.

### 2. Discovery

PRIMARY SOURCE — the current conversation. Decisions and rationale surface
here first and ONLY exist in the main thread's context. Capture these
directly; do not delegate this part.

SECONDARY SOURCES — spawn ONE Explore subagent with this brief and use only
its summarized report (do not re-read raw output into main context):

> "Find decisions made in <project-root> that are missing
> ADRs. Check: (a) recent commits and uncommitted changes via
> `git log --since=<last ADR mtime>` + `git status` for evidence of
> implementation choices; (b) work_tracker/ entries from this week and
> last week, looking for `Decided X` lines that have no ADR-NNNN
> reference; (c) .claude/rules/*.md files, looking for CRITICAL OVERRIDE
> blocks or hard rules with no `(see docs/decisions/...)` citation. Report
> a tight bullet list of candidate decisions with one-line context for
> each. Under 300 words."

### 3. Decide which candidates warrant an ADR

For each candidate (from your conversation OR the subagent's report),
decide:
- YES if alternatives were genuinely considered AND it binds future work
- YES if a future engineer would reasonably ask "why did we do this?"
- NO if it's a code style choice, one-off bug fix, or derivation from an
  existing ADR

### 4. Draft each ADR using this template

```
# ADR-NNNN: <Title — short noun phrase>

**Status:** Proposed | Accepted | Superseded by ADR-MMMM | Deprecated
**Date:** YYYY-MM-DD
**Category:** Process | Infrastructure | Language/Stack | Architecture | Ground Truth | Tooling | ML | UI
**Supersedes:** ADR-XXXX (if applicable)

## Context
<The situation that forced a decision. Constraints, prior state, what
triggered the question.>

## Decision
<What we chose. Concrete and specific. Note explicit scope when relevant
(e.g., "for THIS package only").>

## Alternatives considered
- **<Alternative A>** — why rejected
- **<Alternative B>** — why rejected

## Consequences
- **Positive:** what this enables
- **Negative:** what this costs or makes harder
- **Binds:** what future decisions are now constrained by this
- **Revisit when:** (optional) trigger for reopening this decision

## References
- Related rules: .claude/rules/<file>.md
- Related design: docs/architecture/<design-doc>#<section>
- Related: ADR-NNNN, ADR-MMMM
```

### 5. File naming and numbering

`NNNN-kebab-case-title.md`, zero-padded. Numbers assigned in commit order,
never reused. Sequential — do NOT group by topic.

### 6. Update the index

After writing/updating ADRs, update `docs/decisions/README.md` with one line
per ADR: `- [ADR-NNNN](NNNN-slug.md) — Title — Status`.

### 7. Handle supersedence

If a new ADR supersedes an existing one:
- Set the old ADR's Status to "Superseded by ADR-NNNN"
- Do NOT change anything else in the old ADR (immutability)
- Cross-link both ways

### 8. Run docs-review

After the ADR (and any supersedence updates) land, invoke the
`docs-review` skill to verify no inconsistencies were introduced —
particularly that the new ADR doesn't contradict prior Accepted ADRs,
that the README index reflects the new ADR with correct status, and
that any rule files claiming to cite this ADR's domain are still
accurate. Read its report and either:
- **READY** → done.
- **READY-WITH-FIXES** → address the FIX/SUGGEST findings or surface
  them and ask before proceeding.
- **REVISE** → BLOCK findings present; do not consider the ADR work
  complete until they are resolved.

## Pause-for-confirmation rules

Default to caution.
- PAUSE before writing any new ADR — show the full draft for approval.
- PAUSE before marking an existing ADR as Superseded.
- PAUSE before changing any ADR's status from Proposed to Accepted (or back).
- Deletion of an ADR is essentially never correct — supersede instead.
  PAUSE with strong objection if asked to delete.

## Style

- Plain language; ADRs are read by humans first, AI second.
- Be honest in Alternatives: include the option that was almost chosen,
  not just straw men.
- Be honest in Consequences: include the negatives. ADRs that only list
  positives are propaganda, not records.
- Keep ADRs short — one screen is the target. If you need more, the
  decision is probably actually two decisions.
