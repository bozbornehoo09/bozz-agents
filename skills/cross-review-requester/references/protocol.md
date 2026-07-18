# Cross-review protocol v1

## Identity and storage

- Use one file per review under `.agent-bridge/active/`.
- Name files from kind, human subject, and generated `REVIEW_ID`.
- Number events locally from 1; never allocate a repository-global number.
- Treat header and events as immutable. Corrections are new events.
- Use the helper for creation, append, status, waiting, close, and archive.
- Quote or indent any literal bridge heading or reserved metadata line inside an
  event body; unprefixed protocol-shaped lines are rejected as ambiguous.

## States

```text
READY_FOR_REVIEW
  -> REVIEWING
  -> REVIEW_COMPLETE
  -> ADJUDICATING_FINDINGS
  -> FOLD_COMPLETE
  -> READY_FOR_REVIEW | terminal
```

Progress events may repeat within `REVIEWING`, `WORK_IN_PROGRESS`, or
`ADJUDICATING_FINDINGS`. Terminal statuses are `CLOSED`, `ABANDONED`,
`SUPERSEDED`, and `STOPPED`.

`REVIEW_COMPLETE` always transfers control to the requester, which announces
`FOLD_STARTED` and invokes `fold-review-findings`. Findings are not facts until
that independent adjudication completes.

## Timing

Every event whose actor retains work must contain:

```text
EXPECTED_BY: <absolute RFC3339 UTC timestamp>
GRACE: <ISO-8601 PT duration>
NEXT_UPDATE_BY: <optional earlier RFC3339 update promise>
```

Both roles use the same adaptive watcher:

- deadline = maximum of the inactivity deadline and `EXPECTED_BY + GRACE`;
- poll slowly before the expected window and about every 60 seconds near it;
- replace the timing window when a progress event arrives;
- stop watching on timeout without changing state;
- never archive due to inactivity.

## Anti-hallucination contract

- Pin base/head and complete requested scope.
- `REVIEW_REQUESTED`, `REVIEW`, `RESPONSE`, and `CLOSE` carry the immutable
  revision they request, reviewed, produced, or close.
- Findings use `BLOCK`, `FIX`, or `SUGGEST`.
- Assign stable IDs such as `F1.1`.
- Include exact location and verbatim quote for every finding.
- Cross-reference findings cite and quote both sides.
- A clean report is explicit and valid.
- Verdicts are `READY` (no findings), `READY-WITH-FIXES` (only FIX/SUGGEST), or
  `REVISE` (any BLOCK).

## Folding evidence

Map every finding ID to `CONFIRMED`, `REJECTED`, or `DEFERRED`. The requester
must use a fresh impartial verifier before editing. Record resulting revision,
tests, and exact evidence. Re-request review after any fold.

## Atomicity and archive

The helper locks each review, checks the prior SHA and legal transition, writes
one O_APPEND buffer, fsyncs, and verifies the new status is physically last.
Every read revalidates the complete actor/target, transition, reply, timestamp,
and revision history. Waiters resolve an immediately archived terminal file.
Archive only an explicit terminal state. Move the raw transcript atomically to
`archive/raw/YYYY/MM/`, write its SHA-256 sidecar, and append a rebuildable
catalog record. Derived summaries never replace raw evidence.
