---
name: design-doc-write
description: Draft a NEW human-review design doc (HLD, LLD, or mini-design) that an engineer with no project context can follow, then gate it through design-doc-review (tone and structure, cold read, audience and length, verified claims) and fold the findings before handing it back. Use when the user says "draft a design doc", "write an HLD/LLD", "start a design doc for X", or "turn these notes into a reviewable design doc". Holds the pen and stops once, for outline approval. To revise an existing doc use design-doc-edit; for a read-only review use design-doc-review.
---

# Design Doc Write

Write a **new** design doc for people who will read and review it cold: an engineer from
a neighbouring team, a security reviewer, a new hire, a partner team. The skill writes
the file, runs `design-doc-review` on its own draft, folds what the review finds, and
then hands the doc back.

Two things set the bar:

1. **The template and rubrics** in this skill's `references/` guide the writing.
2. **`design-doc-review` decides whether the draft is done.** Its four lenses live in one
   place so that "reviewed" means the same for a doc this skill wrote and one a person
   wrote. This skill runs that review and folds the results; it does not carry its own
   copy of the checks.

## Scope

**In scope:** one new human-review design doc at one of three grains.

| Grain | Carries |
|---|---|
| **HLD** (high-level design) | Components, flows, the decisions that shape them, open gates |
| **LLD** (low-level design) | Contracts, schemas, state and failure modes for one part of an HLD |
| **Mini-design** | One small change: problem, solution, the one or two calls worth recording |

Word budgets per grain are in `references/length-budget.md`.

**Out of scope:**

- Changing a doc that already exists: `design-doc-edit`.
- Machine-facing references, combined specs and private notes. They are meant to be
  dense and these rules would fight them. When it is unclear who the doc is for, ask.
- Settling open design questions. The doc records them as open.

**Where the doc goes.** If the project's `context-manifest.yaml` declares a layer with
`id: design-docs`, write under its `path`. Otherwise use the path the user gives. With
neither, ask; do not invent a docs directory. Docs are local markdown files.

## References

This skill owns the family's shared references. `design-doc-edit` and
`design-doc-review` read them from `../design-doc-write/references/`. Resolve every path
relative to this `SKILL.md`.

| File | Used at | Holds |
|---|---|---|
| `references/design-doc-template.md` | Step 5 | The skeleton for all three grains |
| `references/shared-authoring-rules.md` | Steps 1, 4 | Holding the pen, project conventions, routing facts (shared with `design-doc-edit`) |
| `references/audience-and-purpose.md` | Step 2 | The opening paragraph and the six-row audience notes |
| `references/audience-model.md` | Step 2 | The default reader, and how a project declares its readers and known terms |
| `references/tone-rubric.md` | Step 8 | Decision honesty, history, how-it-was-made, wording, naming |
| `references/structure-rubric.md` | Steps 3, 8 | Answer first, start from the people served, one home per fact, solution first, appendices |
| `references/length-budget.md` | Step 8 | Body and glossary budgets, acceptance lines, the shrinking order |
| `references/zero-context-gate.md` | Review | The cold-read panel, run inside `design-doc-review` |
| `references/user-mediated-gate.md` | Review | The cold read when the host has no subagents |
| `references/authoring-calibration.md` | When a number looks arbitrary | The reasoning behind budgets and placements |
| `references/examples/` | Step 8 | Two invented examples: an HLD and a mini-design |
| `scripts/measure_doc.py` | Steps 8, 9 | Mechanical measurement; reports, never judges |

```bash
python3 -I <skill-dir>/scripts/measure_doc.py <doc.md> [--type HLD|LLD|mini] [--json]
```

**Siblings.** The review needs `../design-doc-review/`. If that path does not resolve,
look for `design-doc-review/` elsewhere under the same skills root; if it is not
installed, tell the user it is required and stop. Figures use `../design-diagrams/` when
installed. Final prose polish can use `../refining-technical-writing/`. A contested call
the owner cannot make now can go to `../deciding-calls-by-debate/`.

## Steps

### 1. Gather the source material

Load the project conventions (`references/shared-authoring-rules.md`, "Project
conventions"). Then collect what the doc has to be faithful to; invent nothing:

- What the doc is about. Ask if it is unclear.
- **The grain**: HLD, LLD or mini-design. Ask if not stated; it sets the depth.
- Every source the user points to: notes, issues, a parent HLD, ADRs, a prototype, code.
  Read them.
- **What is decided and what is not.** List open questions (they go to Open items, worded
  as open) and the settled choices worth recording with alternatives and reasons.

If the material is thin, say so and write an **honest stub**: what is known, the rest
marked "design pending", and stop. Never pad the skeleton with invented detail.

### 2. Fill in the audience notes before outlining

Fill the six-row table from `references/audience-and-purpose.md` **now**. It goes in the
doc's final appendix, after the `## Appendices` divider: working notes kept in the file
so the next author inherits them, but outside the reading path. Resolve the reader with
`references/audience-model.md`: the project's declared readers if any, else the default.

**Do not guess the readers or the ask.** If neither the source nor the user says, ask.
`unknown — <what would settle it>` is an acceptable answer; a guess is a defect.

### 3. Build the pyramid before writing prose

Outline the doc as a pyramid (`references/structure-rubric.md` S1):

1. **The answer**: the **Takeaway** row plus the **Ask**. It becomes the opening.
2. **Three to five groups of support**, each summed up in one line that makes a claim.
   "Retry background" is a topic; "Retries are capped so a dead endpoint cannot crowd out
   healthy ones" is a claim.
3. **An order inside each group**: by time, by structure, or by importance. The
   **Expected questions** row hints at the order readers will want.

The headings come straight from the pyramid. If the material refuses to group, because
everything seems to belong at the top, it is two docs; say so before drafting.

### 4. Decide where each fact goes

Apply `references/shared-authoring-rules.md` ("Route each fact"): currency, then depth,
then home. History and process detail stay out; build-level depth goes after the
divider; each fact has one owning section.

### 5. Start from the template

Copy the skeleton in `references/design-doc-template.md`. Delete every `<!-- -->` comment
and placeholder from the real doc; the comments are instructions, not content. Keep the
section order and drop sections that do not apply. Name things per
`references/tone-rubric.md` check F.

### 6. Decide whether a figure is needed

Add a figure when the design has a shape prose handles badly, such as a branch, a
request and its reply, parallel work, state several parts share, fan-out, a lifecycle, or
related entities. A
straight two-party flow does not need one. The full test is
`../design-diagrams/references/when-to-diagram.md`. When a figure is warranted, hand it
to `../design-diagrams/` if installed and put only a caption and a one-line pointer in
the doc; otherwise list it as a recommended figure at step 7.

### 7. Confirm the outline

Show the user the title and Status, all six audience rows, the opening paragraph, the
pyramid (the answer and the groups with their one-line claims, in order), the section
list, the glossary terms, the open items, and any recommended figure. **Stop for
approval** (see Pause-for-confirmation rules).

### 8. Draft the body

Read the example in `references/examples/` that matches the grain for pacing and shape;
copy its form, not its content. Check the budget in `references/length-budget.md` before
starting and put depth after the divider as you write, not in a cleanup pass afterwards.

Write against `references/tone-rubric.md` and `references/structure-rubric.md`, in this
order:

| Pass | Settles |
|---|---|
| A. Answer first | Every block leads with its point; the opening states the purpose and the ask |
| B. Audience | The draft matches the step-2 notes |
| C. Data | Every figure has a unit, a baseline and a source |
| D. Sentences and words | `tone-rubric.md` E1 |
| E. Structure | Tables for same-shaped facts, parallel headings, appendix pointers |
| F. Proofread | One read of the finished draft, start to finish |

Pass A goes first because it rewrites sentences that pass D would otherwise polish.

### 9. Review the draft and fold the findings

Run `design-doc-review` **flattened**, as `../design-doc-review/references/flattened-execution.md`
describes: measure first, run all four lenses from this level, verify findings before
folding, fold, rerun, and stop at the loop limit set there. On the write side:

- Cast the cold readers from the doc's own **Readers** row, verbatim.
- **Fold every BLOCK and FIX into the doc.** This skill holds the pen, so it applies the
  rewrites a read-only review would only suggest.
- Fold as an author, not a patcher: a fix that satisfies one lens but breaks the step-3
  pyramid is a trade-off to resolve, not a fold.

### 10. Hand back

Report as in Output format.

## Pause-for-confirmation rules

- **Stop once, at step 7**, for outline approval. The audience and the pyramid are the
  two things cheapest to correct before any prose exists, so show them plainly.
- After approval, draft and review without further stops, unless the sources contradict
  each other in a way that blocks the draft, or folding a finding would mean inventing a
  fact or closing an open question. Then stop and ask.
- Stop before writing outside the resolved docs location, and before overwriting an
  existing file (that is `design-doc-edit`'s job).

## Style

- The rubrics are the standard, not personal taste.
- Open questions read as open. A recommendation says "recommended"; it is not written as
  a decision.
- The doc describes the current design only: no history and no account of how the doc
  was produced.
- Point to other sections and docs by title, not by bare section number.
- Prose for reasoning, tables for comparisons, one worked example for any derived rule.

## Output format

```
Doc: <path> (<HLD | LLD | mini-design>)
Verdict: <READY | READY-WITH-FIXES | REVISE>  (design-doc-review, pass <n> of <n>)
Measured: body <n> words vs <grain> target <n> / ceiling <n>; glossary <n> entries
Owns: <the concept this doc is the home for>
Links out to: <docs it hands concerns to, or "none">
Open items: <count> — <one line each>
Folded after the last pass (unreviewed): <list, or "none">
Surviving findings (REVISE only): <list; the limit that stopped the loop; whether the approach should change>
Conventions recorded: <owner corrections added to the project conventions file, or "none">
```

## What this skill is NOT

- **Not `design-doc-edit`.** That changes an existing doc in place; this creates one.
- **Not `design-doc-review`.** That is the read-only review this skill runs as its gate.
  To review a doc someone else wrote, run `design-doc-review` directly.
- **Not `docs-review`.** That checks the project's authoritative context layers (ADRs,
  rules, architecture, strategy) against each other. A design doc is a proposal for human
  reviewers and is not one of those layers unless the project's manifest says so.
- **Not a decision-maker.** It never settles an open question to fill the skeleton. For a
  contested call, `../deciding-calls-by-debate/` can decide or park it; the doc then
  records the outcome with its alternatives.
- **Not a figure tool.** It decides a figure is needed and writes the caption;
  `../design-diagrams/` draws it.
- **Not an implementation plan.** Turning an accepted design into ordered build steps is
  `../writing-implementation-plans/`, reviewed by `../plan-review/`.
- **Not a general editor.** Polishing technical prose that is not a design doc is
  `../refining-technical-writing/`.
