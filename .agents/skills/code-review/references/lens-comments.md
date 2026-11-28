# Specialist Brief: Comments

You are reviewing what each comment the change adds or edits tells an engineer
who opens this code a year from now, with none of today's context. Scope is
comment meaning, in code and in tests — not code correctness
(`lens-correctness.md`), reuse (`lens-precedents.md`), ADRs
(`lens-decisions.md`), or the register (`lens-overrides.md`).

## Authoritative corpus

- The diff, plus each changed file read in full as of the change's last commit.
- Whatever a comment makes a claim about: the function it describes, the
  caller or contract it mentions, the test it points at, the library behavior
  it relies on (at the version the project pins).
- The plan or spec the change implements, when the orchestrator passes it.
- `../../refining-technical-writing/references/code-comments.md` — the rules
  and severities this lens applies.

## Check for (in order of importance)

The rules and their severities are defined once, in
`../../refining-technical-writing/references/code-comments.md`: rules C1 to C10,
its "Checks per comment" table, and its "Severity" section. Read that file
before reviewing and apply it to every comment the change adds or edits; do
not substitute other rules or severities. In order of importance:

1. A false or misleading comment (C8 "Accurate").
2. A missing comment where a reader would be lost (the "Absent" check).
3. Every other check in that table, in its order. A ticket, document, review
   or chat id offered as the reason is a C1 failure even when a reason sits
   beside it; the replacement states the reason and drops the id.

Each finding gives a replacement comment (or "delete"), not just the problem,
following that file's "Proposing replacements" rules.

## Do not flag (negative scope)

- Whether a guard is reachable or tested (correctness owns that half of C3;
  this lens checks only that the guard states what it rejects and why).
- Comments the change leaves untouched.
- Wording or grammar alone, when the meaning is true, explains why, and reads
  at a glance.
- Generated code and license headers.

## Anti-hallucination contract

- Each finding quotes, at `file:line`, the comment in question (or, when the
  comment is missing, the code that lacks it), and also quotes what the
  comment was checked against, with its own `file:line`. A finding missing
  either quote or either citation is dropped.
- A terms finding (C5, C6) quotes both comments.
- An empty report is correct. Read every changed file before reporting.

## Output format

```
[comments] <file:line> [BLOCK|FIX|SUGGEST]
Rule: C<n> (<check>)
Finding: <one sentence>
Quote: > "<verbatim comment>"
Checked against (<file:line>): > "<verbatim code or source>"
Replacement: <the comment to write, or "delete">
```

Number findings `comments-<n>`.

Empty report is a valid result. Do not invent findings to look thorough.
