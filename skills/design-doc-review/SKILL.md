---
name: design-doc-review
description: Review an EXISTING human-review design doc (HLD, LLD, or mini-design) read-only and report findings without editing it. Four lenses run in parallel - tone and structure, a cold read by fresh-context readers, audience and length, and claims verified against the code and source material - and the report ranks BLOCK / FIX / SUGGEST findings under a READY / READY-WITH-FIXES / REVISE verdict. Use when the user says "review this design doc", "is this HLD ready for review", "cold-read this LLD", or "check this before I share it"; design-doc-write and design-doc-edit also run it as their acceptance gate. Given a set of doc paths, reviews them as one system by tracing scenarios across the set. To write a doc use design-doc-write; to change one use design-doc-edit.
---

# Design Doc Review

Reviews an **existing** design doc written for human reviewers, and changes nothing.
`design-doc-write` creates docs and `design-doc-edit` revises them; this skill only reads.
It works like the rest of the review family (`docs-review`, `skill-review`,
`plan-review`, `code-review`): specialists run in parallel under one anti-hallucination
contract, findings are `BLOCK` / `FIX` / `SUGGEST`, and the verdict is `READY`,
`READY-WITH-FIXES` or `REVISE`.

It **never edits**. It runs in two situations with the same checks: **on its own**, for a
doc someone wrote (a colleague's, or yours before sharing), and **as the acceptance
gate** the two pen-holders run on their own output. The four lenses live here so that
"reviewed" means one thing in both situations.

The lens that justifies a separate skill is **verify**: a doc can read cleanly and pass
a cold read while asserting things the code contradicts, and the cold read does not test
correctness by design.

## Corpus

- **In scope:** the one design doc under review, read in full. Confirm it is a
  human-review doc (HLD, LLD or mini-design) and note its grain. One doc per run, except
  in set mode.
- **Read, not reviewed:** the code, schemas, config and source material (ADRs, work plan,
  open-questions log) the verify lens needs to check the doc's claims.
- **Out of scope:** sibling docs the doc links to. Linking is a valid hand-off; those
  docs are not reviewed here.
- **Machine-facing references and dense combined specs** are dense on purpose. Run only
  the cold-read and verify lenses on them and say the other two were skipped and why, or
  stop if the user only wanted a tone review.

**References.** The shared rubrics belong to `design-doc-write`; read them from
`../design-doc-write/references/` relative to this file, with the measurement script at
`../design-doc-write/scripts/measure_doc.py`. When the relative path is missing, search
the same skills root for a `design-doc-write/` folder; if it is not installed, tell
the user it is required and stop. This skill owns `references/verify-against-artifact.md`,
`references/scenario-traces.md`, `references/mechanism-ledger.md`,
`references/set-mode.md` and `references/flattened-execution.md`. For figures, the
verify lens also reads `../design-diagrams/references/when-to-diagram.md` and
`diagram-conventions.md` when installed: a figure showing wiring the artifact
contradicts is a BLOCK. Two figure problems are SUGGESTs: a design whose structure needs
a picture but has none, and a figure that argues the case instead of showing the shape.

## Specialists

All four run on every human-review doc. Set mode replaces them with its own two (see
Whole-set mode).

| Lens | Brief(s) | Covers |
|---|---|---|
| `tone` | `../design-doc-write/references/tone-rubric.md` + `structure-rubric.md` | Decision honesty, history, how-the-doc-was-made, wording, naming; answer first, start from the people served, one home per fact, solution first, appendices |
| `cold-read` | `../design-doc-write/references/zero-context-gate.md` | The reader panel, the summary check, the gap filters. Run by the dispatcher, not a specialist |
| `audience-and-length` | `../design-doc-write/references/audience-and-purpose.md` + `length-budget.md` | Opening paragraph and audience notes first, then body and glossary budgets and acceptance lines |
| `verify` | `references/verify-against-artifact.md` | Every claim on the dispatcher's list, checked against the artifacts |

Findings are tagged by brief: `[tone]`, `[cold-read]`, `[audience]`, `[length]`,
`[verify]`.

## Anti-hallucination contract (binding on every specialist)

The orchestrator **drops** any finding that breaks these:

1. Every finding includes a verbatim quote, `> "exact text from the doc"`. Paraphrase is
   invalid.
2. Every finding cites `file:line`.
3. Cross-reference and claim-against-artifact findings quote both sides verbatim: the
   doc (`file:line`) and the artifact checked (`path:line`).
4. "Missing" or "unexplained" findings quote the text around the gap.
5. An empty report is correct for a clean doc. Do not invent findings.
6. Out-of-scope corpus is invisible: linked sibling docs, and the template except as the
   reference shape.
7. Read the whole doc before reporting.
8. **Measurement findings are the one exception to rules 1 and 2.** A length finding has
   no single line to quote, so it cites the number `measure_doc.py` reported, the grain
   measured, and the `length-budget.md` row exceeded; each section it proposes moving is
   named with its word count from the script's per-section table. A hand-counted or
   estimated figure is dropped like any unsourced finding.

## Orchestration

1. **Resolve the doc.** Find the exact file, confirm it is a human-review doc, note the
   grain (from the title, or ask), and read all of it.
2. **Record the doc's identity; do not snapshot it.** Hash the file
   (`shasum -a 256 <doc>`) before dispatch and again after every lens has returned. All
   lenses and readers read the **real path**, so they see identical bytes and cite real
   line numbers. If the hashes differ, the doc changed mid-review: report **STALE** with
   both hashes, discard the round, and rerun. `zero-context-gate.md` step 1 applies the
   same hash to the readers.
3. **Measure.** Run `measure_doc.py <doc> --type <grain> --json` once and hand the result
   to the audience-and-length lens.
4. **List the claims for verify.** Sweep the doc for every claim kind in
   `references/verify-against-artifact.md` "What counts as a claim", including the three
   kinds the other lenses route there (decision status, naming, cross-doc structure). The
   verify lens checks exactly this list, so make it complete.
5. **Fan out in one parallel batch** through the host's subagent or delegation facility:
   one subagent per lens that runs, plus one reader per seat the cold-read panel needs.
   Each lens subagent gets the doc's real path and the hash, its brief path(s), this
   contract, the doc's audience notes (or the fact that they are missing), and the
   instruction to end with the line `COUNTS: BLOCK <n> FIX <n> SUGGEST <n>`, an empty
   report too. Verify also gets the claim list, plus the figure references when the doc
   has figures; give it a fresh context, separate from whoever wrote the doc.
   - **Launch the cold readers yourself**, as direct children of this run, per
     `zero-context-gate.md`. Do not route them through a specialist: many hosts do not let
     a subagent start its own subagents. Each reader is cast from the doc's **Readers**
     row verbatim.
   - **Size each dispatch.** If a lens's files exceed about a third of a subagent's
     context window (bytes ÷ 4 ≈ tokens), split it into parts by file group, each part
     naming its files, and finish it with a pair call, as
     `../skill-review/references/review-completeness.md` section 2 says.
   - **Failures.** On rate-limit or overload errors, re-send the failed calls at half the
     parallelism, halving again while the errors continue, down to one at a time; a call
     that still fails counts as failed. Order within the fan-out never changes the
     result. Other failures get one retry on the same model tier. Cold readers follow the
     gate's own retry rules.
   - **No subagents at all:** run the three specialist lenses in this context, say so in
     the report, and run the cold read via `../design-doc-write/references/user-mediated-gate.md`.
6. **Check BLOCKs.** Re-read each cited doc line byte for byte; for a verify BLOCK, also
   re-read the artifact quote at its `path:line` byte for byte. Drop any with a fabricated
   or paraphrased quote on either side, silently.
7. **Spot-check FIX and SUGGEST**: at least three per severity. Drop mismatches.
8. **Aggregate** by severity, then lens. Merge a line raised by two lenses into one
   finding carrying both tags. Name any lens that failed or came back unfinished in the
   `failed:` field of `Specialists run:`.
9. **Verdict.**
   - REVISE if any BLOCK; READY-WITH-FIXES if no BLOCK and at least one FIX; READY
     otherwise.
   - A cold-read gate that FAILED or is INCOMPLETE counts as a BLOCK (see Severity).
   - An unfinished lens (failed, no `COUNTS:` line, or a required read or check not
     done) makes it REVISE (`review-completeness.md` section 1). Cold readers are judged
     by the gate's own rules instead.
   - **STALE pre-empts a verdict.** Report it, discard the round, rerun; never map it to
     `REVISE`, which would judge a doc this round did not actually review.
   - A reader whose tool log shows it opened another file is **CONTAMINATED**, not STALE:
     discard that reading alone and replace the reader; the gate stays INCOMPLETE until
     the replacement returns.

**Flattened execution.** When a pen-holder runs this review as its gate, it follows
`references/flattened-execution.md`, the single definition of that path.

### Whole-set mode (`set`)

When handed several doc paths that together describe one system, run `scenario-traces`
(`references/scenario-traces.md`) and `mechanism-ledger` (`references/mechanism-ledger.md`)
in place of the four per-doc lenses. `references/set-mode.md` is the dispatcher's
procedure for this mode: pinning, sizing, matrix approval, batching, verification,
stopping, and the report and verdict.

## Severity

- **BLOCK**: something that sends a reviewer the wrong way. An important claim the code
  or records disprove; an open question written as settled, or a recommendation written as a
  decision; history in the doc (`tone-rubric.md` B); any trace of the process that
  produced the doc (`tone-rubric.md` C); a cold-read FAIL or INCOMPLETE gate; a section with no discoverable
  purpose (`structure-rubric.md` S2); a superseded design in an appendix (S8).
- **FIX**: a concrete, mechanically fixable problem. An uncited fact verify cannot
  confirm; a sentence over 30 words; a prose wall that should be a table; bold for
  emphasis; a repeated fact; comparisons as bullets; a buried point; a missing opening or
  unstated ask; a percentage with no baseline; filler, buried verbs, vague qualifiers; a
  passive hiding who acts; mixed sibling headings; a body over its ceiling with no
  acceptance line.
- **SUGGEST**: clearer or tighter, no rule broken; a body over target but under the
  ceiling; a true fact that would benefit from a citation.
- **Not a finding**: a body over the ceiling that carries a valid length acceptance line
  (`length-budget.md`). Report the measurement as information; raising it every round
  would make a finding the owner has already answered impossible to close.

## Output template

The block below shows the format only; the doc and findings are invented.

```
# Design Doc Review: docs/design/webhook-delivery-hld.md

Doc: docs/design/webhook-delivery-hld.md (HLD)
Specialists run: tone (tone-rubric + structure-rubric), cold-read (2 readers), audience-and-length (audience-and-purpose + length-budget), verify (14 claims); failed: none
Measured: body 2,910 words vs HLD ceiling 2,500 (over by 410); median sentence 13; 3.8% over 30 words
Cold-read gate: PASS (readers: 2, personas: platform engineer, security reviewer)

## BLOCK
- [verify] docs/design/webhook-delivery-hld.md:73
  Claim: > "each delivery record stores the response body for replay"
  Artifact: services/delivery/schema.sql:39-42 > "CREATE TABLE delivery_attempts ( id BIGINT PRIMARY KEY, status_code INT NOT NULL, latency_ms INT NOT NULL );" — no body column.
  A data-shape claim the schema contradicts.

## FIX
- [tone] docs/design/webhook-delivery-hld.md:120
  > "**Decision:** partitions are keyed by endpoint."
  E1 ("Plain statements"): bold used for emphasis. Rewrite: "Partitions are keyed by endpoint."

- [length] docs/design/webhook-delivery-hld.md (whole body — measurement finding, contract rule 8)
  Measured: body 2,910 words (measure_doc.py --type HLD) vs HLD ceiling 2,500 (length-budget.md "The budget"). Over by 410.
  Shrink step 1: "4. Failure handling" (610 words) is build-level depth; move it to an appendix with a one-line pointer.

## SUGGEST
- [verify] docs/design/webhook-delivery-hld.md:44
  > "a replay is available for 14 days"
  Artifact: infra/delivery/retention.tf:12 > "replay_retention_days = 14" — confirms 14 days.
  True but uncited; add the source.

Verdict: REVISE
```

## What this skill is NOT

- **Not `design-doc-write` or `design-doc-edit`.** It never changes the doc. To apply its
  findings, hand them to `design-doc-edit`.
- **Not `docs-review`.** `docs-review` checks the project's authoritative context layers
  (ADRs, rules, architecture, strategy) against each other for consistency, coherence,
  decisiveness and decay. This skill reviews one human-facing design doc for legibility,
  tone, size and factual accuracy. A design doc is reviewed here even when it cites an ADR;
  the ADR set itself is `docs-review`'s.
- **Not `plan-review` or `code-review`.** Those check an implementation plan or a diff
  against the architecture.
- **Not `skill-review`** (skills and their briefs) or `../refining-technical-writing/`
  (prose that is not a design doc).
- **Not a design decider.** It flags an open question written as settled; it does not
  settle it.
- **Not a doc-set consistency checker.** Set mode reports only contradictions that a
  traced scenario runs into.
