---
name: cross-reviewer
description: Conduct the reviewer side of a file-based multi-agent review. Use when an active cross-review file is READY_FOR_REVIEW and an independent agent must claim it, publish review ETA/grace, invoke the requested review skill against the pinned scope, append evidence-backed findings, and poll adaptively for folds or re-review requests.
---

# Cross-reviewer

Review exactly the pinned request, publish evidence through its append-only
file, and remain available for fold responses and subsequent rounds.

## Inputs

Require an exact active review file or discover unclaimed files under
`.agent-bridge/active/`. Read the file’s `Protocol` section and
[the canonical protocol reference](../cross-review-requester/references/protocol.md)
completely before acting.

## Workflow

1. **Verify and claim.** Run the sibling `scripts/review_bridge.py status`,
   confirm `READY_FOR_REVIEW`, resolve the pinned base/head/scope, and append
   `REVIEW_STARTED` with a realistic `EXPECTED_BY`, `GRACE`, and optional
   `NEXT_UPDATE_BY`. Claiming prevents duplicate reviewers.
   - **Independence check first:** compare your own agent/thread identity with
     the header's `REQUESTER`. If they are the same thread, disclose the
     self-review and pause for explicit user approval before claiming.
   - **Baseline check:** confirm the pinned revision resolves to the bytes you
     will read — `git rev-parse` for commits, or
     `review_bridge.py fingerprint --repo-root <root> <paths> --expect <revision>`
     for a `files-sha256:` identity (exit 4 = moved).
2. **Invoke the requested review engine.** Use the header’s `REVIEW_SKILL`
   (`code-review`, `plan-review`, `docs-review`, or a project-specific review
   skill). Follow that skill completely. Review surrounding context only to
   understand the requested scope.
3. **Publish progress before expiry.** For long work, append
   `REVIEW_PROGRESS` with a replacement ETA/grace before the prior ETA expires.
4. **Append the review.** Re-run the baseline check immediately before
   appending. If the bytes moved at either check, discard findings for that
   baseline and append `REVIEW` with first body line `BASELINE: STALE`, the
   observed mismatch, and no findings — never review mixed versions.
   Otherwise use `REVIEW` / `REVIEW_COMPLETE`. Give every finding
   a stable ID (`F<round>.<sequence>`), severity `BLOCK|FIX|SUGGEST`, an
   `OBSERVED` or `HYPOTHESIS` label, exact location and quote, and governing
   cross-reference evidence. Explicitly say when there are no findings, and
   list what you checked and cleared under `NON-FINDINGS`. Include
   verification commands and the review engine's verdict: REVISE if any
   BLOCK; READY-WITH-FIXES if no BLOCK and at least one FIX; READY otherwise.
5. **Wait adaptively.** Capture the returned SHA and run
   `review_bridge.py wait --baseline-sha ...`. Both reviewer and requester use
   the same algorithm: slow polling before the owner’s expected window,
   approximately 60 seconds near/after it, and deadline extension through
   `EXPECTED_BY + GRACE`.
6. **Handle each hit.** Re-read state:
   - `ADJUDICATING_FINDINGS`: accept the requester’s fold ETA and keep waiting.
   - `FOLD_COMPLETE`: inspect dispositions; keep waiting for either a new
     request or explicit close.
   - `READY_FOR_REVIEW`: verify the new immutable head and begin the next round.
   - terminal status: stop.

Do not close a thread because waiting timed out. Report the timeout and leave
the active file resumable.

## Anti-hallucination contract

- Rebuild context from the pinned artifact and authoritative sources.
- Do not accept the requester’s implementation narrative as proof.
- Do not modify the reviewed artifact.
- Do not negotiate findings outside the transcript.
- Every finding requires an exact `file:line` citation and verbatim quote;
  cross-reference findings cite and quote both sides.
- Separate observations from inferences and reproduce behavioral claims.
- An empty report is correct; never invent findings to appear thorough.
- Preserve scope discipline; adjacent code is context, not a target unless the
  requested change causes a demonstrable contradiction there.
- Label uncertainty `HYPOTHESIS` and name the missing evidence; never present
  an inaccessible live-system claim as a confirmed failure.
- Do not re-flag the request's known-open items unless their stated
  disposition is unsound or contradicted by the artifact.

## Severity

- **BLOCK** — unsound or unsafe behavior, data loss, security exposure, or a
  contradiction that prevents approval. For code, name the concrete failing
  behavior.
- **FIX** — a concrete correction required before approval that leaves the
  overall approach intact. For code, name the concrete failing behavior.
- **SUGGEST** — optional; current behavior is sound and approval does not
  depend on it. A design SUGGEST may say the approach is sound but another is
  better.

Do not elevate style, naming, or preference without functional impact, and do
not report pre-existing issues the requested change did not touch.

## Helper

`scripts/review_bridge.py` is a thin launcher for the requester skill’s
canonical helper, ensuring identical transition, locking, archive, and adaptive
polling behavior on both sides.

## Pause-for-confirmation rules

Pause and publish a resumable progress event when the pinned artifact cannot be
resolved, the requested review skill is unavailable, the request contradicts
its stated scope, completing it would require new authority, or your identity
matches the requester's thread (self-review). Do not silently
substitute a review engine, broaden scope, close the thread, or modify artifacts.

## Style

Write compact evidence-first review events. Use stable finding IDs, severity in
BLOCK → FIX → SUGGEST order, exact `file:line` citations with verbatim quotes,
explicit command results, and one canonical verdict. Separate observed facts
from inferences.

## What this skill is NOT

- Not the requester or implementer.
- Not the finding folder; the requester invokes `fold-review-findings`.
- Not permission to broaden the requested artifact or make repository changes.
