# ADR-0003: File-scoped cross-agent review lifecycle with independent finding adjudication

**Status:** Accepted
**Date:** 2026-07-18
**Category:** Tooling

## Context

The review-skill family produces strong evidence-backed findings, but it does
not coordinate a long-running review between independent agent platforms. The
first Prism experiment used one shared append-only `review-loop.md`. It proved
the value of external cross-review, but one global file grew to roughly 1 MB,
global entry allocation collided, historical entries became physically
misordered, and polling timeouts had to be repeatedly negotiated by a human.

The implementer also needs a stronger response contract. External findings are
hypotheses, not authority: immediately editing to match them lets a plausible
but mistaken reviewer steer the code. Verification must be independent of both
the original implementation context and the proposed fold.

## Decision

Adopt a file-scoped cross-agent review lifecycle implemented by three generic
Agent Skills:

- **`cross-review-requester`** owns the implementer/requester lifecycle:
  create the session, pin scope and revisions, publish work timing, poll,
  invoke finding folding, re-request, explicitly close, and archive.
- **`cross-reviewer`** owns the independent reviewer lifecycle: claim a ready
  request, invoke the requested review-family skill, publish evidence and
  timing, and remain available for subsequent rounds.
- **`fold-review-findings`** owns impartial adjudication and implementation:
  verify every external finding in a fresh context, classify it as confirmed,
  rejected, or deferred, edit only confirmed findings, and verify the fold.
  When a confirmed change targets an authoritative content layer, it invokes
  that layer's declared `update-*` owner rather than becoming a second writer.

The requester MUST invoke `fold-review-findings` whenever adaptive polling
observes `REVIEW_COMPLETE`; it MUST NOT directly accept or implement findings.
The folding procedure delegates verification to a fresh reviewer context that
receives the raw finding, pinned artifact, and authoritative sources, but not
the implementer's desired conclusion or proposed fix.

Use one append-only file per review, with a stable review ID and event numbers
local to that file. State is event-derived:

`READY_FOR_REVIEW → REVIEWING → REVIEW_COMPLETE →
ADJUDICATING_FINDINGS → FOLD_COMPLETE → READY_FOR_REVIEW | terminal`.

Both requester and reviewer use the same adaptive polling contract. The actor
that owns the next action publishes an absolute `EXPECTED_BY` plus `GRACE` and
may replace it with a progress event. Polling slows before the expected window
and tightens near it. Inactivity may stop a watcher but never closes or
archives a review.

Only an explicit terminal event permits archival. Preserve the raw transcript
and bind it to a SHA-256 digest; summaries are optional derived lookup aids and
never replace raw review evidence.

The cross-review skills coordinate existing review-family skills rather than
replace them. `code-review`, `plan-review`, `docs-review`, and project-specific
review engines continue to own specialist fan-out, evidence rules, severities,
and verdicts.

## Alternatives considered

- **One global bridge file** — rejected: global numbering, textual EOF anchors,
  and unbounded active context already failed in live use.
- **Two skills (requester + reviewer), with folding inside requester** —
  rejected: lifecycle coordination, independent adjudication, editing, and
  verification are distinct responsibilities; embedding all four makes the
  requester broad and makes impartiality difficult to test.
- **Trust reviewer findings and fold immediately** — rejected: an external
  model can be confidently wrong. Equal-quality verification is required for
  both acceptance and rejection.
- **Summaries replace old raw transcripts** — rejected: summaries are lossy and
  cannot support exact citations or later audit.
- **Close/archive on inactivity** — rejected: expected work may legitimately
  exceed a static timeout, and silence is not a terminal decision.

## Consequences

- **Positive:** concurrent reviews no longer contend for global numbering or
  load unrelated history; each session is independently resumable and
  archivable.
- **Positive:** timing becomes agent-to-agent protocol data, eliminating most
  human polling extensions while retaining prompt response near completion.
- **Positive:** requester bias and reviewer hallucination are checked by a
  separate evidence-first adjudication step.
- **Negative:** three skills and a small state-machine helper add more moving
  parts than a prose-only bridge.
- **Negative:** finding folds incur another independent reasoning pass and can
  increase wall-clock time; this is intentional review integrity cost.
- **Binds:** cross-agent review coordination uses the three-role lifecycle;
  review findings are never folded without independent verification; raw
  archives remain authoritative evidence; authoritative-layer folds preserve
  the owning `update-*` skill's exclusive write path.
- **Revisit when:** the host platforms expose a reliable shared event/queue API
  with equivalent immutable history, or independent adjudication proves unable
  to improve finding accuracy in forward tests.

## References

- Foundational review-family decision: Prism ADR-0015
- Plugin ownership/extraction: Prism ADR-0021
- Protocol and helper: `skills/cross-review-requester/`
- Reviewer role: `skills/cross-reviewer/`
- Finding adjudication: `skills/fold-review-findings/`
