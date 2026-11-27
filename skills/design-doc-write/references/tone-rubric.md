# Specialist Brief: Tone Rubric

Contents: [Authoritative corpus (in scope)](#authoritative-corpus-in-scope) · [Out of scope corpus (invisible)](#out-of-scope-corpus-invisible) · [Check for (in order of importance)](#check-for-in-order-of-importance) · [Severity](#severity) · [Anti-hallucination contract](#anti-hallucination-contract) · [What this rubric does NOT flag](#what-this-rubric-does-not-flag) · [Output format](#output-format)

The wording half of `design-doc-review`'s **tone** lens for one human-review design doc,
whether someone else wrote it or a pen-holder is checking its own draft. The ordering
half is `structure-rubric.md`. Run both as one lens: every finding is tagged `[tone]`,
and severity, contract and output format come from this file only.

Each defect belongs to exactly one check in the family. When a check below names another
check as owner of a case, report the case there, not here.

## Authoritative corpus (in scope)

- The doc under review, at the path the dispatcher gives, read in full including its
  appendices.
- `design-doc-template.md` (alongside this file), as the reference shape.
- `../../refining-technical-writing/references/general-rules.md`, for the headings that
  check E1 names, and only those.

## Out of scope corpus (invisible)

Linked sibling docs, the code and contracts the doc describes, and the source material.
Two checks have a half that needs evidence outside the doc: decision status against the
source (check A) and names against the artifact (check F). Do not judge those halves
from memory and do not drop them; the dispatcher sends them to the `verify` lens as
enumerated claims (`design-doc-review` Orchestration step 4).

## Check for (in order of importance)

### A. Decision honesty

Docs fail this more than any other rule. Give it its own read of Open items, every
Status line, and every sentence that states a design choice.

- **BLOCK** an undecided question worded as decided. Every reviewer is misled by it.
- **BLOCK** a recommendation worded as a decision. Recommending is fine when it says
  "recommended".
- **BLOCK** a genuine choice between options presented as the only path. Show the options
  and which way the author leans.
- **BLOCK** a fabricated resolution: "settled on <date>", "agreed by <person>". A settled
  call is recorded as the choice, what it beat, and why.
- **Commitment state is explicit.** Each capability is one of: *decided and being built*;
  *allowed by the interface but not planned*; *rejected*, with the reason. **BLOCK** an
  unplanned capability written up as committed work.
- **FIX** a person or team named as the one who will resolve an open item. The tracker
  holds ownership so the doc does not go stale when people move. Exempt: an ownership
  section the project explicitly requires.

### B. History — BLOCK anywhere in the doc

The doc describes the design as it is now. Narrating how it got there is a BLOCK in the
body, a parenthesis, a caption, or an appendix:

- dates of reversals ("switched on 2026-03-02"), former states ("used to be the default",
  "can now change"), earlier drafts ("the previous version proposed…").
- A one-line reason is allowed when it carries no time reference: "(404 rather than 403,
  so callers cannot probe which ids exist)" is fine; adding "changed last sprint" makes it
  a BLOCK. The test: does any word only make sense against an older version of the doc?

### C. How the doc was made — BLOCK anywhere in the doc

No trace of the process that produced the doc: reviews, reviewers, panels, personas,
lenses, rounds, sessions, folds, prompts, or the author's working files. Acceptance lines
are included. Test: is the sentence about the design, or about producing the doc? Keep
the design fact and drop the provenance; renaming the process does not help. A process
mention carrying a date is reported once, here, not again under B. Words such as
*session* or *prompt* that refer to the design (a user's login session, a model prompt
the system builds) are not findings.

### D. Settled decisions carry their reasons

A reviewer's first question about any choice is "why not the other option?". Where the
reasons go is `structure-rubric.md` S4; this check is only that they exist.

- **FIX** a major settled choice with no alternative and no reason anywhere in the doc.
  Major: it shapes the architecture, a contract or the data model, and a reader would
  push back on it.
- A minor choice needs a single "X over Y because Z". Do not demand a table for it, and
  do not flag obvious or externally imposed choices.

### E. Wording checks specific to design docs

1. **General writing rules.** Apply these headings of
   `../../refining-technical-writing/references/general-rules.md` at the severities they
   state: "Sentence length", "Splitting a long sentence", "Plain statements", "Fewer
   words", "Concrete words", "Active voice", "No names", and the "Numbers and evidence"
   section. Do not restate
   them here. Two design-doc readings: build or CI status ("compiles", "tests pass") is
   process trace, so **FIX** it by stating what the system does; and reasoning chains
   ("because… so… therefore") stay as prose, so **SUGGEST** rejoining one that was
   chopped into bullets.
2. **Tables for same-shaped facts.**
   - **FIX** a paragraph of more than about four sentences listing things of one shape
     (fields, options, states): make it a table or list.
   - **FIX** data compared across two or more dimensions (option by cost by risk) written
     as prose or bullets: make it a table. A one-dimensional list can stay a list.
   - **FIX** a body section that opens with a multi-line schema or interface definition.
     Put the definition in an appendix as a typed code block; the body gets a field table
     (`Field | Direction | Required | Meaning`) and a pointer.
3. **Say what it is before how it works.** After the experience it serves, the doc and
   each major section state what the thing is ("X is a Y that does Z") before any
   mechanism. **FIX** a section that never says, or says only after the mechanism. (A
   section that leads with mechanism instead of experience is `structure-rubric.md` S2; a
   doc opening that does is `audience-and-purpose.md`'s.)
4. **Explain at first use.** Each in-scope term and abbreviation is explained where it
   first appears; the Glossary backs up the load-bearing ones. **FIX** a term explained
   somewhere, but used earlier than that. A term explained nowhere is the cold-read
   gate's; glossary size is `length-budget.md`'s.
5. **One concrete case.** **FIX** a roll-up, reduction or derived-value rule given only
   in the abstract: add one example with real inputs and the result ("two deliveries
   succeeded and one is retrying, so the batch shows `PARTIAL`; when the third succeeds
   it shows `DELIVERED`"). **SUGGEST** a short walkthrough where a flow is only described
   abstractly.
6. **Leftover formal machinery.** **FIX** a formal property that only guards wording the
   doc no longer contains ("first match wins" over rows that can no longer overlap). Cut
   it; do not add prose defending it.
7. **Parallel sibling headings.** **FIX** a group of three or more sibling headings in
   mixed grammatical forms (some noun phrases, some sentences, some imperatives).

### F. Naming

Names outlive the doc, so name things for what they are.

- **FIX** a name tied to the one consumer an entity happens to serve today, when it is
  not limited to that consumer.
- **FIX** a name taken from the team or repository that builds a thing instead of the
  capability it provides.
- **FIX** a display name the artifact does not use for that thing.
- **FIX** a heading or phase named after a side detail instead of what it delivers.
- **SUGGEST** an internal distinction for a word used in two senses, where renaming it
  would break a published contract.

In review, judge only names the doc itself contradicts; names checked against the
artifact go to `verify` as naming claims. A pen-holder with the code open applies both.

## Severity

- **BLOCK**: the doc would mislead a reviewer. Checks A, B and C, plus
  `structure-rubric.md`'s S2 and S8 BLOCKs.
- **FIX**: a concrete rule broken in a way that hurts reviewing and has a mechanical fix.
- **SUGGEST**: clearer or shorter, no rule broken.

## Anti-hallucination contract

The family contract holds: each finding has a `> "verbatim quote"` and `file:line`; an
empty report is right for a clean doc; the dispatcher drops findings that break this.
For this rubric also:

1. **Decision honesty inside the doc needs both places.** In review this lens covers a
   choice called settled in one place and open in another (quote both), or a
   settled-sounding claim the doc never actually settles. Whether the source still lists
   it as open is `verify`'s.
2. **Missing reasons (D) is a claim of absence.** Quote the bare decision and the text
   around it, and only report after reading the whole doc, appendices included.
3. **Leftover machinery (E6) quotes both** the property and the text that makes it moot.
4. **A process mention (C) quotes enough** to show it is about producing the doc, not a
   same-named design concept.
5. **A word-level finding is checked against its sentence.** A word-list or script hit is
   only a candidate.

## What this rubric does NOT flag

- Dense prose or long sentences inside a clearly marked appendix. Disorganised appendices
  are still `structure-rubric.md` S8's.
- Whether the design is right. That is the human design review.
- Terms explained nowhere (the cold-read gate), glossary size (`length-budget.md`), or the
  opening paragraph (`audience-and-purpose.md`).
- Spelling and grammar that break none of the checks above.

## Output format

```
[tone] <file:line> [BLOCK|FIX|SUGGEST]
Check: <id and name, e.g. "A decision-honesty", "E2 tables", "S4 solution-first">
Finding: <one sentence naming the broken rule>
Quote: > "<verbatim doc text>"
Rewrite: <replacement text that meets the rule>
```

Pen-holders (`design-doc-write`, `design-doc-edit`) may apply the rewrite.
`design-doc-review` only reports it.

Empty report is a valid result. Do not invent findings to look thorough.
