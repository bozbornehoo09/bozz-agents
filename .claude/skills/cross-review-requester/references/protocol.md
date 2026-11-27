# Cross-review protocol v1

Contents: [Identity and storage](#identity-and-storage) · [States](#states) · [Timing](#timing) · [Artifact identity](#artifact-identity-and-stale-baselines) · [Anti-hallucination contract](#anti-hallucination-contract) · [Independence](#independence) · [Folding evidence](#folding-evidence) · [Out-of-band reviewers](#out-of-band-reviewers) · [Atomicity and archive](#atomicity-and-archive)

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

## Artifact identity and stale baselines

- A pinned revision is a git commit or range for committed work. For
  uncommitted work or a document set, pin content instead:
  `review_bridge.py fingerprint --repo-root <root> <path>...` prints a
  `files-sha256:<digest>` identity over every named file (a directory expands
  to its non-hidden files). Use that value as `--head` / `--revision`, and list
  the fingerprinted paths in the request body.
- The reviewer re-verifies the pinned identity **before reviewing and again
  immediately before appending `REVIEW`** (`git rev-parse` for commits;
  `fingerprint --expect <identity>` for content, which exits 4 on mismatch).
- If the bytes moved, the reviewer must not review mixed versions. It appends
  `REVIEW` against the pinned revision with first body line
  `BASELINE: STALE`, the observed mismatch, and no findings. The fold treats a
  stale review as "re-pin and re-request"; it never supports `CLOSE`.

## Anti-hallucination contract

- Pin base/head and complete requested scope.
- `REVIEW_REQUESTED`, `REVIEW`, `RESPONSE`, and `CLOSE` carry the immutable
  revision they request, reviewed, produced, or close.
- Findings use `BLOCK`, `FIX`, or `SUGGEST`.
- Assign stable IDs such as `F1.1`.
- Include exact location and verbatim quote for every finding.
- Cross-reference findings cite and quote both sides.
- Label each finding `OBSERVED` (the cited bytes or a reproduction show it) or
  `HYPOTHESIS` (a concern the reviewer could not fully verify, with the missing
  evidence named). These are reviewer confidence labels, not fold
  dispositions.
- A clean report is explicit and valid; a `NON-FINDINGS` list records what was
  checked and cleared.
- Known-open items listed in the request are not re-flagged unless their stated
  disposition is unsound or contradicted by the artifact.
- Verdicts follow the review family's rule: REVISE if any BLOCK;
  READY-WITH-FIXES if no BLOCK and at least one FIX; READY otherwise.

## Independence

The header names `REQUESTER` and `REVIEWER`. A reviewer whose own agent/thread
identity matches the requester's discloses the self-review and pauses for
explicit user approval before claiming. Sharing a model family is allowed;
sharing the implementing thread is not.

## Folding evidence

Map every finding ID to `CONFIRMED`, `REJECTED`, or `DEFERRED`. The requester
must use a fresh impartial verifier before editing. Record resulting revision,
tests, and exact evidence. Re-request review after any fold. A re-request
names every `REJECTED` BLOCK or FIX in its requested focus, with the
counter-evidence, so the reviewer adjudicates the disagreement again instead
of it disappearing.

## Out-of-band reviewers

A reviewer that cannot run the helper (a browser chat model, another machine)
joins through the requester's relay: see
`references/out-of-band-reviewer.md`. The lifecycle, transcript, and mandatory
fold are unchanged; relayed events say so in their first body line.

## Atomicity and archive

The helper locks each review, checks the prior SHA and legal transition, writes
one O_APPEND buffer, fsyncs, and verifies the new status is physically last.
Every read revalidates the complete actor/target, transition, reply, timestamp,
and revision history. Waiters resolve an immediately archived terminal file.
Archive only an explicit terminal state. Move the raw transcript atomically to
`archive/raw/YYYY/MM/`, write its SHA-256 sidecar, and append a rebuildable
catalog record. Derived summaries never replace raw evidence.
