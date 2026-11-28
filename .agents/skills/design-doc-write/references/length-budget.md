# Specialist Brief: Length Budget

Contents: [Authoritative corpus (in scope)](#authoritative-corpus-in-scope) · [Out of scope corpus (invisible)](#out-of-scope-corpus-invisible) · [The budget](#the-budget) · [What is counted](#what-is-counted) · [Acceptance lines](#acceptance-lines) · [Shrinking order](#shrinking-order) · [What must survive a cut](#what-must-survive-a-cut) · [Check for (in order of importance)](#check-for-in-order-of-importance) · [Anti-hallucination contract](#anti-hallucination-contract) · [Output format](#output-format)

One half of `design-doc-review`'s **audience-and-length** lens; `audience-and-purpose.md`
is the other half. Sentence and word checks make text tighter; this brief limits the size
of the body as a whole, because a doc can pass every line check and still be far longer
than a reviewer will read before the meeting. `authoring-calibration.md` gives the
reasoning behind each number.

## Authoritative corpus (in scope)

The doc under review and the output of `../scripts/measure_doc.py` run on it at its grain.

## Out of scope corpus (invisible)

Everything else. Wording belongs to `tone-rubric.md` and what to move belongs to
`structure-rubric.md`; this brief only decides whether the body must shrink and in what
order to work.

## The budget

The budget covers the body; appendices have no limit.

| Grain | Target | Ceiling |
|---|---|---|
| Mini-design | 600 words | 1,000 words |
| LLD | 1,800 words | 2,500 words |
| HLD | 2,000 words | 2,500 words |

### Glossary

The body count leaves out the Glossary, so it has its own limits.

| Measure | Target | FIX above |
|---|---|---|
| Entries | 15 | 30 |
| Words in one gloss | 40 | — |

Going over the entry count is a prompt to re-audit, not a list of cuts: run the template's
three-part test on every entry and name the ones that fail it. The target is an upper
bound, not a quota; a small glossary is never a finding.

These tables are the source of truth. `measure_doc.py` keeps copies in `BUDGETS` and
`GLOSSARY`; change both together.

## What is counted

**Body words** are the words from the title down to the `## Appendices` heading, leaving
out fenced code blocks, HTML comments and the `## Glossary` section. Table cells are
counted: a table reads faster than prose, but it is still reading.

The Glossary is excluded by its heading wherever it sits, so keeping it in the reading
path costs the body nothing.

## Acceptance lines

A limit the owner cannot ever satisfy turns into a finding that never closes: every round
reports it, the owner declines it, and the verdict stays stuck on something nobody will
act on. The owner can therefore record the decision in the doc, on its own line directly
after the audience notes table:

```markdown
Length accepted: <YYYY-MM-DD> — <what the extra length pays for>.
Glossary size accepted: <YYYY-MM-DD> — <what the extra entries pay for>.
```

- Date and reason are both required. The reason says what the length buys ("the state
  table has to sit beside the rules it enforces"), never "hard to cut", and names no
  person or review step.
- With the line present, the script still prints the overage but treats it as
  information and does not fail on length.
- **Only the owner writes it.** A reviewer or pen-holder may say a doc deserves one and
  ask; it never adds one to clear its own finding.
- **It accepts a size, not growth.** An edit that adds body words to an accepted doc
  reports how many it added.

## Shrinking order

Work down the list and stop once the body is under the ceiling.

1. Move build-level depth to an appendix (`structure-rubric.md` S5).
2. Move settled-choice comparisons after the divider (`structure-rubric.md` S4).
3. Delete repetition (`structure-rubric.md` S3).
4. Move schemas and formal definitions to an appendix (`tone-rubric.md` E2).
5. Tighten wording (`tone-rubric.md` E1). Last, because it saves the least: being
   a thousand words over is a structure problem.

Still over after all five: the doc is really two docs. Split it, or make it an HLD that
links an LLD for the depth, or the owner adds an acceptance line.

## What must survive a cut

Cutting too much is a FIX in its own right. Keep real thresholds, named controls,
measured figures, concrete identifiers, the worked example a derived rule needs, and
every open item with its state. The cold-read gate outranks this budget. **Never** reach
the budget by deleting an open question, a caveat or a risk; that converts a length
problem into a decision-honesty BLOCK.

## Check for (in order of importance)

1. **Body over the ceiling with no acceptance line → FIX.** Name the sections to move
   first, each with its measured word count.
2. **More than 30 glossary entries with no acceptance line → FIX.** Name the entries that
   fail the three-part test and which test each fails.
3. **Body over target → SUGGEST**, naming what would go first.
4. **More than 15 glossary entries → SUGGEST**, same naming rule. A single gloss over 40
   words → SUGGEST on that entry.
5. **Glossary after the divider → FIX.** Move it up; it costs the body nothing.

## Anti-hallucination contract

A length finding has no single line to quote, so it is the family's one exception to the
quote rule (`design-doc-review` contract rule 8). In place of a quote:

- **Cite the script's figure**, the grain it measured, and the budget row exceeded. A
  hand count or estimate is dropped.
- **Each proposed move names the section and its measured word count** from the script's
  per-section table ("4. Failure handling — 610 words"). "Trim section 4 a bit" is
  dropped.
- **A glossary finding names the entries to cut and the test each fails.** A count alone
  is a measurement, not a finding. If the count is over but every entry passes, say so and
  suggest the owner consider an acceptance line.
- **Never flag a doc for being short.** There is no minimum.

## Output format

```
[length] <file> (whole body — measurement finding, contract rule 8) [FIX|SUGGEST]
Measured: <n> words (measure_doc.py --type <grain>) vs <grain> <target|ceiling> <n> (length-budget.md "The budget")
Shrink step: <n> — <section heading> (<n> words): <move or cut, and to where>
```

Empty report is a valid result. Do not invent findings to look thorough.
