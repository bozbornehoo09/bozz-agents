# Authoring Calibration — the reasoning behind the numbers and placements

For pen-holders (`design-doc-write`, `design-doc-edit`) only. Review lenses do not get
this file, so the briefs they read can stay limited to checks.

## The length numbers

The one premise: **a reviewer should be able to read the body in a single sitting before
the review, in about ten minutes.** At a typical reading speed of roughly 250 words a
minute for technical prose, that is about 2,500 words, which is the HLD and LLD ceiling.
Everything else is a default a project can tune:

- **Targets below the ceiling.** An LLD covers one part and pushes depth into appendices,
  so its target is the lowest of the two full grains. An HLD gets a little more for
  context. A mini-design is a few minutes' read.
- **Words, not pages.** Markdown has no pages; word counts survive any renderer.
- **Glossary numbers.** A careful glossary for one design usually lands between 8 and 15
  entries, with glosses of 15 to 25 words. The target (15), the FIX threshold (30) and
  the per-gloss limit (40 words, about twice the usual) follow from that.

To change a number, edit the table in `length-budget.md` and the matching constants in
`../scripts/measure_doc.py` (`BUDGETS`, `GLOSSARY`) together. Nothing checks that they
agree.

## Why the glossary is budgeted by entry count

Glossaries grow one reasonable entry at a time. Each addition looks harmless ("someone
might not know this"), no single removal looks obviously right, and per-entry review
never sees the total. Counting entries is the one measure that sees the total, and that
is its only job: crossing the number triggers a re-audit, and the three-part test in the
template decides what goes.

There is no total word cap for the glossary. Glosses are similar in length, so a word cap
would track the entry count and one of the two limits would always be redundant. Wordiness
belongs to a single gloss, so the per-gloss limit handles it.

The glossary is left out of the body count because readers look things up in it rather
than read it through. Anything excluded from a budget without a budget of its own grows
unchecked, so it has its own row.

## Why the audience notes go last

At the top, six rows of the author's analysis stand between the reader and the point,
which breaks the answer-first rule the rest of the family enforces. Reviewers need the
purpose and the design, not the analysis behind them.

They stay **in the doc** rather than in a chat log or a side file so they last: whoever
opens the doc next, weeks later, inherits the decision about who it is for instead of
guessing again. Filed after the divider, they cost the body nothing.

They also make "enough context" testable. In general it is a matter of taste; against a
stated "readers have LOW prior knowledge of the delivery pipeline" it can be checked.

## Where the notes are used

| Step | Uses |
|---|---|
| Building the pyramid (`design-doc-write` step 3) | **Takeaway** is the top; **Expected questions** suggest the groups |
| The opening | **Ask** is the request the opening must state |
| How much background to carry | **Prior knowledge**: HIGH trims background, LOW earns a section |
| The cold-read gate | **Readers** sets each reader's persona |
| `design-doc-review` | Checks the notes are filled and match the body |
| The outline checkpoint | Shown to the user so the audience is confirmed, not assumed |

## Why the gate hashes the file instead of copying it

Reviewing a snapshot hides the case where the doc changes during the review: the panel
reports cleanly on text that no longer exists. Hashing the live file before and after
makes that case visible. Handing readers the path, not pasted text, also gives every
citation a true line number and guarantees all readers saw the same bytes.

Restricting a subagent to one file is rarely possible. What is needed is "this one file,
chosen at dispatch time", which few hosts can express, and any directory allowlist
includes the sibling docs that would contaminate the read. A tool log that the dispatcher
inspects works on every host.
