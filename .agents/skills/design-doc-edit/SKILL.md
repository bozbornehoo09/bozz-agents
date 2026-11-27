---
name: design-doc-edit
description: Revise an EXISTING human-review design doc (HLD, LLD, or mini-design) in place so it stays legible to a cold reader, then gate the changed doc through design-doc-review (tone and structure, cold read, audience and length, verified claims) and fold the findings before handing back a diff. Reads and refreshes the doc's audience notes, keeps open questions open, holds the body to its length budget, and follows a safe procedure for restructures. Use when the user asks to edit, revise, tighten, shorten or restructure a design doc, HLD or LLD, or to apply review feedback to one. Runs the review once per edit batch, not per edit. To draft a new doc use design-doc-write; for a read-only review use design-doc-review.
---

# Design Doc Edit

Change an **existing** design doc so it stays readable without context and keeps to the
same rubrics it was written against. The skill edits the file in place, then runs
`design-doc-review` on the result **once the batch of edits is complete**, folds what the
review finds, and hands back a diff.

Same two governors as `design-doc-write`: the rubrics in
`../design-doc-write/references/` guide the writing, and `design-doc-review` decides when
the doc is done. This skill runs that review and folds; it carries no checks of its own.

## Scope

**In scope:** edits to one existing human-review design doc, or a coordinated
restructure across a set of them. That covers requested changes, applying review or
reader feedback, tightening, restructuring, and refreshing the audience notes.

**Out of scope:**

- A doc that does not exist yet: `design-doc-write`.
- A review with no edits (the doc is shared, or someone else owns it):
  `design-doc-review`.
- Machine-facing references and dense combined specs; these rules do not apply.
- Settling open questions. An edit that would close one keeps it open unless the user
  decided it in this session.

**References.** The shared references are owned by `design-doc-write`; resolve them at
`../design-doc-write/references/` relative to this file, with the script at
`../design-doc-write/scripts/measure_doc.py` and the invented examples under
`../design-doc-write/references/examples/`. If that path does not resolve, look for
`design-doc-write/` elsewhere under the same skills root; if it is not installed, say it
is required and stop. Do the same for `../design-doc-review/`. Before editing, read
`tone-rubric.md`, `structure-rubric.md`, `design-doc-template.md`,
`shared-authoring-rules.md` and `authoring-calibration.md`. This skill owns one reference,
`references/restructuring.md`, read only for a restructure (step 5). Figures use
`../design-diagrams/` when installed.

## Steps

### 1. Resolve the doc and check nobody else is editing it

Find the exact file and confirm it is a human-review design doc. Read all of it; you
cannot keep it coherent otherwise. Note the grain from its title and depth so the edits
match it: an HLD stays conceptual, an LLD carries contracts and schemas.

Load the project conventions (`shared-authoring-rules.md`, "Project conventions").

**Check for concurrent editing before the first change.** Run
`git log -3 --format='%h %ar %s' -- <doc>` and `git status --short -- <doc>`. If the log shows a
recent commit that is not yours, or the status shows changes that are not yours, another
session or the owner is in the file: stop and ask. A clean status can also hide an open, unsaved editor buffer,
so if the owner edits this doc by hand, ask them to save and close it first. While the
batch runs:

- **Re-read the target text immediately before each edit**, never relying on an earlier
  read, so you never overwrite a change the owner just made.
- **Apply edits one at a time**, not in parallel, so no two edits race on one file.
- **Leave the owner's own wording alone.** In a sweep over text the owner wrote by hand,
  do not rewrite or reinterpret their passages in place; propose changes in the diff and
  let them decide. If their in-progress edit has left an obvious break (a half-typed
  word), repair it only where the intent is unmistakable, and show the repair.

### 2. Read the audience notes first

The six-row table in the final appendix (`audience-and-purpose.md`) states who the doc is
for, what they know, and what it asks of them; it governs every edit. Three cases:

- **Present and accurate**: edit to it. The stated prior knowledge decides whether an
  added explanation is needed or is padding.
- **Present but outdated** (the readers, the ask or the expected questions have changed):
  update it in this batch and say so in the diff.
- **Missing**, or placed at the top of an older doc: add it, or move it, as the final
  appendix after the `## Appendices` divider. Fill it from the source and the user; ask
  rather than guess the readers or the ask.

### 3. Apply the edits

Make the requested changes against `tone-rubric.md` and `structure-rubric.md`, then run
these passes over everything you touched, in this order:

| Pass | On the edit side |
|---|---|
| A. Answer first | Every touched block leads with its point and with the people served before mechanism. On a restructure, recheck the whole pyramid |
| B. Audience | The step-2 reconciliation |
| C. Data | Figures you added or changed have a unit, a baseline and a source |
| D. Sentences and words | `tone-rubric.md` E1 on all changed prose |
| E. Structure | Headings you added, moved or renamed still match their siblings' form |
| F. Proofread | The changed lines |

Route new facts per `shared-authoring-rules.md` ("Route each fact"). On the edit side
that means in particular:

- A reversed choice is described only as it now stands; the reversal itself belongs in an
  ADR or decision log, never the doc (`tone-rubric.md` B).
- Each fact keeps one home; point to it rather than restate it, including in figure
  captions.
- When asked to tighten a section, start with what readers see first (the heading, the
  lead sentence, the main table) before the nested detail. A heavy heading over polished
  detail still reads as heavy.

### 4. Keep the body within budget

Measure before the first edit and again after the batch:
`python3 -I ../design-doc-write/scripts/measure_doc.py <doc> --type <grain>`.

- **The batch must not push the body over its ceiling.** If the doc is already over, or
  the batch takes it over, work the shrinking order in `length-budget.md` in the same
  batch, moving depth after the divider rather than shipping a longer body. A batch that
  grows an already-too-long body and moves nothing out is incomplete.
- **A valid length acceptance line** means the owner has already accepted the size: the
  script passes, report the figure, and do not start cutting. It accepts a size, not
  growth, so report how many body words the batch added. Only the owner adds or changes
  that line; never write one to clear your own finding.

### 5. Restructures

If the batch reorders sections, moves detail to appendices, rebuilds the doc
solution-first, renumbers, or does any of these across several docs, follow
`references/restructuring.md` before step 7. It covers in-place editing, an
interruption-safe order of work, copy-before-delete, the conservation check, the
cross-reference sweep and multi-doc reconciliation, locked conventions, and the fidelity
check.

### 6. Figures

When an edit changes the design's structure (a new interaction, flow, lifecycle or
fan-out), check `../design-diagrams/references/when-to-diagram.md`: the change may now need
a figure, or may have made an existing one wrong. Either way it is a `../design-diagrams/`
task; put only the caption and a one-line pointer in the doc. A prose-only edit needs no
figure check.

### 7. Review the batch and fold the findings

Once the batch is coherent (the user says it is done, or a natural stopping point), run
`design-doc-review` **flattened**, as
`../design-doc-review/references/flattened-execution.md` defines: measure, run all four
lenses from this level with the cold readers as your own direct subagents, verify
findings before folding, fold, rerun, and stop at its loop limit. On the edit side:

- **Fold every BLOCK and FIX into the doc.** When a cold reader stumbles over a term
  whose explanation this batch cut, put the explanation back; do not delete the term.
- Open questions get closed by accident during edits more than at any other time. As you fold, keep
  every open question worded as open and every recommendation marked "recommended".

### 8. Hand back

Report as in Output format, with the diff.

## Pause-for-confirmation rules

- **Stop before the first edit** if step 1 finds someone else editing the doc.
- **Stop and ask** before changing whether an open item is open or settled, unless the
  user decided it in this session, and before guessing the readers or the ask.
- **Stop and ask** when folding a finding would require inventing a fact, or when the
  user's requested change conflicts with a rubric BLOCK (for example, it would add
  history to the doc); explain the conflict and offer the compliant version.
- **Stop before touching a locked project convention** unless told to.
- Otherwise do not stop between edits in a batch; the review runs at the end, not after
  each edit.

## Style

- The rubrics are the standard, not taste.
- Smallest edit that does the job; leave untouched text untouched.
- The doc states the current design only. No history, no trace of how it was produced.
- Point to sections and docs by title, not bare number.
- Commit, when asked, by explicit path, never `git add -A`.

## Output format

```
Doc: <path> (<HLD | LLD | mini-design>)
Diff: <unified diff, or a summary with the diff attached>
Verdict: <READY | READY-WITH-FIXES | REVISE>  (design-doc-review, pass <n> of <n>)
Measured: body <before> -> <after> words vs <grain> ceiling <n>; glossary <before> -> <after> entries
Audience notes: <unchanged | refreshed: what changed | added>
Open items changed: <items whose open/settled state the batch changed, for confirmation, or "none">
Folded after the last pass (unreviewed): <list, or "none">
Surviving findings (REVISE only): <list; the limit that stopped the loop; whether the approach should change>
```

## What this skill is NOT

- **Not `design-doc-write`.** That creates a doc; this revises one that exists.
- **Not `design-doc-review`.** That reports without editing; this skill runs it as its
  gate. For a review with no changes, run `design-doc-review` directly.
- **Not `docs-review`.** That checks the project's authoritative context layers (ADRs,
  rules, architecture, strategy) against each other. A design doc is a proposal for human
  reviewers, not one of those layers unless the manifest declares it.
- **Not a decision-maker.** It never closes an open question to tidy the doc. A contested
  call can go to `../deciding-calls-by-debate/`; the doc then records the outcome.
- **Not a figure tool.** `../design-diagrams/` draws; this skill places the caption.
- **Not a per-edit linter.** The review runs once per coherent batch.
- **Not a general editor.** Prose that is not a design doc is
  `../refining-technical-writing/`.
