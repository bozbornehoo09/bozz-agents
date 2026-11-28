---
name: fold-review-findings
description: Independently adjudicate and fold findings from a completed external review. Use when cross-review-requester detects REVIEW_COMPLETE and must verify each finding with fresh impartial evidence, classify it as CONFIRMED, REJECTED, or DEFERRED, implement only confirmed fixes, run proportionate checks, and return a fold report for the bridge response.
---

# Fold Review Findings

Treat review findings as hypotheses. Verify first, edit second.

Read [references/adjudication-contract.md](references/adjudication-contract.md)
completely before working.

## Inputs

Require:

- active review file and completed review event;
- pinned base/head or immutable document identity;
- repository status and unrelated user changes;
- every stable finding ID and its original evidence;
- gate policy and permitted deferral destinations.

If the review event is clean, verify the event targets the current pinned head
and return `NO_FINDINGS_CONFIRMED`; do not invent work.

If the review's first body line is `BASELINE: STALE`, adjudicate nothing:
confirm the mismatch (re-run the pin check), return `NO_CHANGES` with
`Stale baseline — re-pin and re-request`, and never let it support `CLOSE`.

A relayed out-of-band review (first body line `RELAYED:`) is folded exactly
like any other; the relay's verbatim quote of the reviewer's output is the
finding text.

## Workflow

1. **Freeze the evidence.** Capture the reviewed revision, complete diff, file
   state, and finding text before editing.
2. **Run impartial verification.** For any non-empty findings, delegate one
   bounded batch to a fresh independent reviewer context. Give it the raw
   finding, pinned artifact, and authoritative sources—but not the
   implementer’s planned response, desired conclusion, or proposed fix.
   Explicitly prohibit recursive delegation and bind the verifier to the
   anti-hallucination contract below. Before delegating, do the cheap
   mechanical check yourself: open each cited `file:line` in the pinned bytes.
   A quote that appears nowhere in the cited file is `REJECTED` with the line's
   actual text (or the fact that the line or file does not exist) as the
   counter-evidence; still record it in the report.
3. **Adjudicate.** Re-read the verifier’s citations yourself. Classify every
   finding:
   - `CONFIRMED` — reproduced or directly proven against exact sources;
   - `REJECTED` — disproven with equally exact evidence;
   - `DEFERRED` — valid but explicitly allowed outside this gate, with owner,
     durable destination, and trigger.
4. **Fold only confirmed findings.** Preserve unrelated changes. Keep edits
   inside reviewed scope unless a confirmed cross-reference requires both
   sides. Do not edit merely to appease wording. If a confirmed finding changes
   an authoritative content layer with a declared owning `update-*` skill,
   invoke that owner to make the edit; adjudication does not bypass the
   project's single-writer contract.
   - **Sibling instances.** For a confirmed defect, search the reviewed scope
     yourself for other instances of the same problem and fix every hit in
     this fold; name the search and its hits in the report. Never fix one
     instance of a demonstrated multi-file problem.
   - **Recorded decisions win.** Before applying a fix, check it against the
     Accepted ADRs and other recorded decisions it touches. A fix that would
     reverse or reinterpret one is not foldable here: return `BLOCKED` naming
     the decision and the question for the user (a new ADR goes through
     `update-decisions`).
5. **Verify the fold.** Run focused reproductions first, then proportionate
   tests/static checks. Confirm each original finding is resolved in the new
   diff and that rejected/deferred items were not silently changed.
6. **Return a fold report.** Use the template below. The requester appends it
   as `RESPONSE`, then either re-requests review at the new head or closes.

The parent requester owns repository integration and bridge writes. This skill
does not archive or close the review.

## Anti-hallucination contract

- Every verifier disposition requires exact `file:line` citations and verbatim
  quotes from the pinned artifact or authoritative source.
- Cross-reference claims require citations and verbatim quotes from both sides.
- Separate observed bytes or reproduction results from inferred consequences.
- Report conflicting or unavailable evidence as `UNRESOLVED`; never guess to
  force a disposition.
- The parent re-reads the cited evidence before accepting the disposition. A
  disposition that does not meet this contract cannot be folded.

## Output

```markdown
# Fold report: <review id / event>

Reviewed revision: <sha>
Resulting revision: <sha or unchanged>

## Dispositions
- F1.1 — CONFIRMED
  Evidence: <exact path:line + quote / reproduction>
  Fold: <files changed and why>
  Verification: <command/result>
- F1.2 — REJECTED
  Evidence: <exact counter-evidence>
- F1.3 — DEFERRED
  Destination: <durable path/id>
  Trigger: <when it returns>

Sibling search: <command/pattern and hits, per confirmed finding>
Re-adjudicate next round: <REJECTED BLOCK/FIX ids, or none>

Fold outcome: FOLDED | NO_CHANGES | BLOCKED
```

## Stop conditions

Stop and return `BLOCKED` when evidence conflicts, a finding requires new
authority, the pinned revision changed, or safe verification is impossible.
Never guess merely to keep the review loop moving.

## Pause-for-confirmation rules

Pause before editing when the reviewed revision moved, evidence conflicts, the
fix would broaden authorized scope or change a recorded decision, safe
verification is unavailable, or a deferral is not explicitly permitted by gate
policy. Return a `BLOCKED` fold
report that names the missing decision or evidence; do not change bridge state
or invent a disposition.

## Style

Keep the fold report finding-oriented and auditable. Preserve stable finding
IDs, cite exact evidence, distinguish verifier evidence from parent judgment,
name each changed file and check, and use the smallest coherent patch. Avoid
general cleanup or narrative agreement with the original review.

## What this skill is NOT

- Not a rubber stamp for the external reviewer.
- Not a second full review of unrelated code.
- Not authorization to defer BLOCK findings or broaden product scope.
- Not the bridge lifecycle owner.
