# ADR-0006: Cross-review content pins, stale-baseline reviews and relayed reviewers

**Status:** Accepted
**Date:** 2026-11-27
**Category:** Review lifecycle
**Extends:** [ADR-0003](0003-file-scoped-cross-agent-review-lifecycle.md) (does not supersede it)

## Context

ADR-0003 pins a review's scope to commits. Two cases fell through it.

- **Uncommitted or doc-set reviews.** A review of working-tree files or a set of
  docs had no stable identity, so a reviewer could review bytes that changed
  under it and the requester could fold findings against the wrong version.
- **Reviewers that cannot run the helper.** A browser chat model or another tool
  with no file access cannot append its own events to the review file. ADR-0003
  assumed that every REVIEWER event is written by an independent agent.

## Decision

1. **Content fingerprints.** `review_bridge.py fingerprint` produces a
   `files-sha256:` identity for a set of files; `--expect` exits 4 when the bytes
   have moved. A request may pin scope by commit or by fingerprint.
2. **Stale-baseline reviews.** The reviewer re-checks the pin before reviewing
   and again before appending. If it moved, the review's first line is
   `BASELINE: STALE` and it carries no findings. The requester re-pins and
   re-requests; a stale review can never close a thread.
3. **Relayed out-of-band reviewers.** When the reviewer cannot write to the
   file, the requester posts its events on its behalf, marked `RELAYED:`, quoting
   the reviewer's output verbatim with its SHA-256. The independent fold
   (`fold-review-findings`) is still mandatory, and the relay marker keeps the
   provenance visible.

## Alternatives considered

- **Require commits for every review.** Rejected: doc reviews and pre-commit
  reviews are common and committing just to review adds noise.
- **Forbid reviewers without file access.** Rejected: browser models are a cheap,
  genuinely independent second opinion; the relay keeps them auditable.

## Consequences

- **Positive:** reviews of uncommitted work are pinned; relayed reviews are
  usable and labelled.
- **Negative:** a relayed event is written by the requester, so independence
  rests on the verbatim quote and hash plus the mandatory fold, not on who wrote
  the event.
- **Binds:** a relayed event MUST carry `RELAYED:`, the verbatim output and its
  SHA-256; a `BASELINE: STALE` review MUST NOT support closing.

## References

- `skills/cross-review-requester/` (incl. `references/protocol.md`,
  `references/out-of-band-reviewer.md`, `scripts/review_bridge.py`),
  `skills/cross-reviewer/`, `skills/fold-review-findings/`
- Tests: `tests/test_review_bridge.py`
