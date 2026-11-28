# Review completeness

The one definition of two rules that every review skill which fans out
specialist lenses follows: `code-review`, `docs-review`, `plan-review`,
`skill-review` and `design-doc-review`. Each of them points here instead of
restating the rules; `cross-skill-consistency.md` flags a fan-out skill that
neither points here nor follows them. Both rules exist for the same reason: a
lens that never finished looks, in an aggregated report, exactly like a lens
that found nothing.

## 1. An unfinished lens never passes a review

- **The end line.** Every lens prompt asks the specialist to finish with
  `COUNTS: BLOCK <n> FIX <n> SUGGEST <n>`, an empty report included. The line
  is how the orchestrator tells a report that ended from one that was cut off.
- **Unfinished** means any of: the call still failed after the skill's
  retries; the report has no `COUNTS:` end line; or the report says it could
  not do a read or a check its brief requires. Two notes are not unfinished: a
  point the contract routes to "out of scope — cannot evaluate", and the stated
  limit of a split lens (section 2).
- **Effect.** Name every unfinished lens in the `failed:` field of the report's
  `Specialists run:` line, and return `REVISE` whatever the findings say. A
  pass with an unfinished lens never counts as a pass with no BLOCK, so a loop
  that stops at its first BLOCK-free pass (`writing-implementation-plans`,
  `preparing-code-reviews`, a design-doc pen-holder) keeps going instead.

## 2. A split lens settles the pairs its parts could not judge

A skill's sizing rule splits a lens whose corpus is too large for one
specialist into parts, each a dispatch of the same brief over its own files.
Splitting must not quietly drop the comparisons that cross the cut:

- **Shared side.** Every part also gets, whole, the files the lens judges
  against (for example the decision index and the ADRs it cites, the rule
  files, the register). Count them when sizing each part.
- **Named pairs.** A part that meets a finding whose other side sits in
  another part answers "out of scope — cannot evaluate" and names both files.
- **The pair call.** Once all parts return, one more dispatch of the same lens
  reads each named pair whose two files are both in the corpus, and judges
  those pairs only. Size it like a part, shared side included, and split it the
  same way if it is still too large. Until it returns, the lens is unfinished.
- **Stated limit.** Cross-part pairs that no part named are compared only
  through the shared side. The report says so; that statement does not make
  the lens unfinished.
- **Report.** The `Specialists run:` line lists a split lens's parts and its
  pair call with the number of pairs read, for example
  `internal-consistency (parts: decisions, rules; pair call: 3 pairs)`.
