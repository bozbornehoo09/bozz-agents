# Specialist Brief: Mechanism Ledger

Set-mode lens for `design-doc-review`. One specialist builds an inventory of every
mechanism a set of design docs mentions, so that a mechanism nobody reads, or one no doc
specifies, shows up even when no traced scenario reaches it. The dispatcher pins and
exports the set and verifies the result, as `set-mode.md` defines.

## Authoritative corpus (in scope)

- The export directory of the set at the pinned commit, every file read in full.
  Nothing outside the export is needed.

## Out of scope corpus (invisible)

Anything outside the export, including the working tree, docs not in the set, and the
scenario matrix (`scenario-traces.md` owns that).

## Check for (in order of importance)

Build one table covering every writer, data store, index, scheduled job, alarm and
runbook entry the docs mention:

| Mechanism | Kind | State | Writers | Readers | Failure mode | Specified at |
|---|---|---|---|---|---|---|

Each mechanism gets one row, positioned where the set first cites it (by file order, then
line), and later mentions are added to that row's cells; two runs against the same commit
therefore produce identical tables. Under the table, list any attribute that has more
than one writer, as `<attribute> — <writer> (path:line@sha7), <writer> (path:line@sha7)`.
That list is an inventory, not a set of findings.

Findings, listed under the table:

1. **Underspecified.** A mechanism whose `Specified at` is `none`, or with no stated
   failure mode.
2. **Unread.** A mechanism nobody reads; it may be removable. These rows are the best
   source of simplification ideas.

## Anti-hallucination contract

1. Every cell carries a `path:line@<sha7>` citation with the full path from the
   repository root, or reads `none — > "<nearby quote>" — path:line@sha7`, quoting the
   place where the missing fact would have had to be written.
2. Text taken from the set is quoted exactly (`> "…"`).
3. A row with no finding is not a finding; report nothing just to show the run did
   something.
4. The dispatcher verifies each finding row's quotes before it reaches `FINDINGS.md`.

## Do not flag

- Two docs that describe one mechanism in different amounts of detail but do not disagree.
- Style, grammar and formatting.

## Output format

Hand back the contents of `MECHANISM-LEDGER.md`: the table, the multi-writer list, then
each finding as

```
[mechanism-ledger] <path:line@sha7> [SUGGEST]
Mechanism: <name> — <underspecified | unread>
Evidence: > "<nearby quote>" — <path:line@sha7>
```

Empty report is a valid result. Do not invent findings to look thorough.
