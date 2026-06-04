---
name: update-open-questions
description: Reconcile the open-questions log: close questions resolved by new ADRs and record newly surfaced ones. Use after decisions land. No review hook (open questions are unresolved by definition).
---

Update the open questions log at
`<project-root>/docs/open_questions.md` to reconcile
resolved questions, add newly-surfaced ones, and keep ranking aligned
with current downstream-unblock priorities. The open questions doc is
the project's running list of decisions the user has not yet committed
to — it is by definition unresolved content.

This prompt is **downstream of** `update-decisions` (when an ADR
lands, its corresponding open question is resolved) and **upstream of**
`update-context` (the orchestrator runs this after ADR work).

## Scope

In scope:
- `docs/open_questions.md`

Out of scope:
- `docs/research/**` — research memos that ground individual open
  questions; immutable per-question artifacts. Updated only by
  authoring new memos, not by editing existing ones.
- ADRs, rules, architecture, strategy — covered by other update
  prompts.

## Steps

### 1. Read the current open questions doc

Read `docs/open_questions.md` end-to-end. Note the structure:
- Status / Last-updated header
- Ranked list of "Decisions the user needs to make"
- Per-question deep-dive sections
- Convention: when a question graduates to an ADR, its section is
  replaced with a one-line pointer to the ADR

### 2. Discovery — three reconciliation passes

PRIMARY SOURCE — the current conversation. New questions surface here;
in-session decisions resolve existing ones. Capture both directly.

SECONDARY SOURCES — spawn ONE Explore subagent with this brief:

> "Find what's changed in <project-root> that affects
> docs/open_questions.md. Three checks: (a) new ADRs in
> docs/decisions/ since the open_questions.md mtime — these may
> resolve open questions and need replacement-with-pointer; (b)
> new research memos in docs/research/ since that mtime — these
> may add detail to existing questions or surface new ones; (c)
> recent work_tracker/ entries mentioning 'Decided X' lines whose
> ADR has not yet landed — these may be in-flight resolutions.
> Report a tight bullet list mapping each finding to: an existing
> question (resolves / refines), a new question to add, or no
> action. Under 300 words."

### 3. Reconcile resolved questions

For each open question that an ADR now answers:
- Replace the question's section with a one-line pointer:
  `→ Resolved by [ADR-NNNN](decisions/NNNN-slug.md) on YYYY-MM-DD`
- Remove the question from the ranked list at the top
- PAUSE before removing — the user may want to see the diff to
  confirm the ADR fully resolves the question (partial resolutions
  stay open with a refined sub-question)

### 4. Add newly-surfaced questions

For each new question:
- Place in the ranked list using the "downstream unblock" criterion —
  questions blocking more downstream work rank higher
- Add a deep-dive section with: problem framing, options considered,
  current research/recommendation status, sub-questions only the user
  can answer
- If a research memo exists at `docs/research/00NN-*.md`, cite it

### 5. Refine ranking

Re-evaluate the ranked list. As decisions land, downstream-unblock
weights shift. Move questions up or down as needed; this is the only
mutation to existing-but-not-resolved questions that is routine.

### 6. Update the header

- Bump the `Last updated` date to today.
- If the document has shifted in scope or audience, update the Status
  line.

### 7. No docs-review hook

`docs/open_questions.md` is explicitly out of scope for `docs-review`
(it is unresolved by definition; it cannot be inconsistent with
anything authoritative). Skip the review step.

## Pause-for-confirmation rules

- PAUSE before removing a question (resolution is final; partial
  resolutions stay open with a refined sub-question).
- PAUSE before adding a new top-level section (the document has a
  deliberate structure — Tier A, Round 3, etc.).
- PAUSE before any change to the ranking that demotes a top-3
  question — the user has a working priority order that should not
  shift silently.
- For additive deep-dive content within an existing question (new
  research finding, new option considered), surface the diff and
  proceed unless ambiguous.

## Style

- Open questions are honest. Do not soften "we don't know" into
  "we're considering options."
- Each question has options *considered* and *rejected* — both belong
  in the deep dive.
- Cite research memos by path; do not restate their content (the memo
  is the authoritative source).
- Resolved questions become one-line pointers, not deletions —
  deletion loses audit trail.
