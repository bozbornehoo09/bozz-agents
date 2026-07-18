---
name: cross-review-requester
description: Coordinate the implementer/requester side of a file-based multi-agent review. Use when an agent must open a review, publish exact scope and revisions, wait adaptively for an external reviewer, invoke fold-review-findings on every completed review, re-request after confirmed fixes, and explicitly close/archive the thread.
---

# Cross-review Requester

Own the review lifecycle without treating reviewer findings as fact. Communicate
through one append-only file per review and use the bundled helper for every
state change.

## Inputs

Require:

- project root and bridge root (default `.agent-bridge`);
- review kind: `CODE`, `PLAN`, `DESIGN`, or `DOCS`;
- human-readable subject;
- exact base/head revision or immutable document identity;
- review skill the reviewer must invoke;
- initial acknowledgement ETA and grace;
- complete scope, rules/ADRs to load, and proportionate verification commands.

Read [references/protocol.md](references/protocol.md) completely before opening
or resuming a review.

## Workflow

1. **Inspect before opening.** Confirm the requested artifact exists, resolve
   immutable identities, check the worktree, and preserve unrelated changes.
2. **Create one review file.** Run `scripts/review_bridge.py init`; never append
   by patching an EOF anchor. Put everything the reviewer needs in the first
   request. The file name is generated from kind, subject, and stable review ID.
3. **Wait adaptively.** Capture the SHA returned by `init`/`status`, then run
   `review_bridge.py wait --baseline-sha ...`. Honor the current owner's
   `EXPECTED_BY + GRACE`; use slow polling before the expected window and
   approximately 60-second polling near/after it. A timeout stops the watcher
   but does not close or archive the review.
4. **Handle every hit.** Re-read parsed state after every detected change:
   - `REVIEWING` / progress: record the new SHA and resume adaptive polling.
   - `REVIEW_COMPLETE`: **immediately append `FOLD_STARTED` with the requester’s
     fold ETA/grace, then invoke `$fold-review-findings`. Do not directly accept,
     reject, or implement any finding.** This call is mandatory even for a
     clean review; the folding skill may return a no-findings confirmation.
   - terminal status: stop.
5. **Publish dispositions.** After the folding skill returns, append `RESPONSE`
   with one stable finding ID per `CONFIRMED`, `REJECTED`, or `DEFERRED`
   disposition, exact evidence, changed revision, and checks run.
6. **Continue or close.** If code/docs changed, append a new
   `REVIEW_REQUESTED` pinned to the new head and resume adaptive polling. If the
   fold confirms a clean final verdict and the gate policy is satisfied, append
   `CLOSE` with outcome and final revision, then run `archive`.

Post `WORK_UPDATE` or `FOLD_PROGRESS` before an ETA expires. The update must
carry a replacement `EXPECTED_BY`, `GRACE`, and, for longer work,
`NEXT_UPDATE_BY`.

## Finding discipline

- Treat the external review as evidence to investigate, not authority.
- Never mark a finding fixed before independent adjudication.
- Require the folding report to cite the pinned diff and governing source.
- Require every `REJECTED` disposition in the folding report to carry evidence
  equal in quality to the original finding.
- Require every `DEFERRED` disposition to be policy-permitted and name its
  durable destination, owner, and return trigger.
- Preserve the reviewer’s original words in the transcript.

## Helper commands

Resolve the helper relative to this skill directory. Typical operations:

```bash
python3 scripts/review_bridge.py init ...
python3 scripts/review_bridge.py status --file <active-review>
python3 scripts/review_bridge.py wait --file <active-review> --baseline-sha <sha>
python3 scripts/review_bridge.py append ...
python3 scripts/review_bridge.py archive --file <closed-review>
```

Use a body file or stdin for multiline content; do not interpolate untrusted
review text into shell arguments.

## Stop conditions

Stop only on explicit `CLOSED`, `ABANDONED`, `SUPERSEDED`, or `STOPPED`, or
when adaptive waiting times out. Inactivity alone never changes review state.

## Pause-for-confirmation rules

Pause without changing or archiving review state when the immutable scope cannot
be resolved, the requested review skill is unavailable, a fold needs authority
beyond the original request, or gate policy does not determine whether a review
may close. A watcher timeout is resumable and does not itself require a product
decision.

## Style

Keep bridge events concise and audit-ready. Use stable IDs, absolute UTC times,
exact revisions, exact commands and results, and direct evidence. Do not restate
the full transcript or hide decisions in narrative progress updates.

## What this skill is NOT

- Not the independent reviewer; use `cross-reviewer`.
- Not the adjudicator/implementer of findings; always call
  `fold-review-findings` after `REVIEW_COMPLETE`.
- Not a replacement for `code-review`, `plan-review`, or `docs-review`; it
  coordinates them across agents.
