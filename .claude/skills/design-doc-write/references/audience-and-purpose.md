# Specialist Brief: Audience and Purpose

Contents: [Authoritative corpus (in scope)](#authoritative-corpus-in-scope) · [Out of scope corpus (invisible)](#out-of-scope-corpus-invisible) · [The opening](#the-opening) · [The audience notes](#the-audience-notes) · [Filling rules (for pen-holders)](#filling-rules-for-pen-holders) · [Check for (in order of importance)](#check-for-in-order-of-importance) · [Anti-hallucination contract](#anti-hallucination-contract) · [Output format](#output-format)

One half of `design-doc-review`'s **audience-and-length** lens; `length-budget.md` is the
other half. Pen-holders follow the same rules when they write. The brief covers two
things a doc settles before any prose, and they live at opposite ends of the file:

- **The purpose** is the opening paragraph, directly under the title and Status line.
- **The audience notes** are a six-row table in the final appendix, after the
  `## Appendices` divider. They are working notes for authors and reviewers, not design.

They are written first and filed last. `authoring-calibration.md` gives the reasons.

## Authoritative corpus (in scope)

The single doc under review, read end to end: the opening, the body (to compare against
the notes), and the audience notes appendix.

## Out of scope corpus (invisible)

Everything outside that file. The project audience file (`audience-model.md`) feeds the
cold-read gate, not this lens.

## The opening

Unlabelled prose of no more than four sentences, in this order:

1. what the people the design serves will be able to do once it ships;
2. what this doc covers, and in a few words what it leaves to others (the
   `**Not covered here:**` line carries the links);
3. the ask, when the readers have to decide something.

Example: "Integrators will get every webhook within five minutes of the event, even
through a short endpoint outage. This doc covers the delivery queue, the retry schedule,
and what happens to an endpoint that stays down. We need approval of the retry ceiling
listed under Open items."

## The audience notes

```markdown
## Appendix — Audience notes

| Field | Answer |
|---|---|
| **Readers** | <roles, main reader first> |
| **Prior knowledge** | <HIGH / MEDIUM / LOW on the problem and on the people served; the gaps that matter> |
| **Takeaway** | <the single sentence a reader should leave with> |
| **Stakes** | <what gets easier for them, or what goes wrong without this> |
| **Ask** | <approve / choose between options / comment / no action — and by when> |
| **Expected questions** | <three to five, each with where the doc answers it> |
```

Exactly these six rows, in this order. Up to two acceptance lines may follow the table
(`length-budget.md` defines them); they are not rows.

The Glossary does not belong in this appendix. It stays above the divider because the
cold reader needs it; filed below, its terms count as unexplained.

## Filling rules (for pen-holders)

- **Do not guess the readers.** When neither the source nor the user names them, ask.
  A doc aimed at an imagined reader is aimed at no one, and the review then checks it
  against the wrong person.
- **Ask about the ask.** A doc seeking approval and a doc seeking comments are shaped
  differently, so this row matters most.
- **`unknown — <what would settle it>` counts as filled.** A made-up answer does not.
- **Name roles.** "Stakeholders" is not a reader.
- **Every expected question gets a location**: a section, an appendix, or "raised in the
  review meeting". A question with nowhere to go gets a home or is marked out of scope.
- **Six rows only.** Design content that drifts into the notes belongs in the body.

## Check for (in order of importance)

1. **No audience notes → FIX.** `measure_doc.py` reports it. The cold-read gate then uses
   the default reader from `audience-model.md`.
2. **A row left empty or as a placeholder → FIX.** Quote the cell.
3. **The opening is missing, still a placeholder, or a labelled field such as
   `**Purpose:**` → FIX.** The opening paragraph is the purpose.
4. **The Ask row names a request the opening never makes → FIX.**
5. **The opening starts with mechanism instead of what the served people gain → FIX.**
6. **The opening is longer than four sentences → SUGGEST**, proposing the cut.
7. **The notes and the body disagree → FIX**: the body explains far more or far less than
   the stated prior knowledge implies, or an expected question is not answered where the
   row says.
8. **The notes sit in the reading path** (above the divider, or at the top) **→ FIX.**
   Move them to the final appendix.

## Anti-hallucination contract

- Every finding quotes the cell or the opening sentence with `file:line`. A missing row
  quotes the table around the gap.
- A notes-versus-body finding quotes both the row and the body passage (or the section
  where the answer should have been).
- The choice of readers and the ambition of the answers are the owner's. Do not flag them.

## Output format

```
[audience] <file:line> [BLOCK|FIX|SUGGEST]
Check: <number and name>
Finding: <one sentence>
Quote: > "<verbatim text>"
Rewrite: <the fix>
```

Empty report is a valid result. Do not invent findings to look thorough.
