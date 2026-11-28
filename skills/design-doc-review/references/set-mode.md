# Whole-set mode (`set`): dispatcher procedure

When handed several doc paths that together describe one system (an HLD, its LLDs,
schema notes), run two set lenses in place of the four per-doc lenses. This file is
the dispatcher's procedure, and its single definition; each lens's method lives in its brief.

| Lens | Brief | Who runs it | Records produced |
|---|---|---|---|
| `scenario-traces` | `scenario-traces.md` | MATRIX (one specialist), then TRACE (one specialist per batch of at most ten cases; batches for different entry lanes run in parallel), then VERIFY (a fresh read-only verifier, step 6) | `SCENARIO-MATRIX.md`, `traces/`, `FINDINGS.md`, `COVERAGE.md` |
| `mechanism-ledger` | `mechanism-ledger.md` | one specialist | `MECHANISM-LEDGER.md` |

Specialists hand back file contents; you write the files, in a run folder the user
chooses. With no folder named, write them to a temporary directory and show
`FINDINGS.md` in the reply. Name each run `<date>-set-<n>` so a later run never replaces
a record someone has referred to. Launching, back-off and retries follow `../SKILL.md`
Orchestration step 5; step 2 below takes the place of that step's corpus
sizing. Contract rule 6 reads
"outside the set" here. The set is never edited; changes go through `design-doc-edit` and
its own review.

1. **Timing.** Run once per design stage, after each doc's own review loop has converged
   (`flattened-execution.md` step 5). What it finds feeds a fresh per-doc loop.
   Do not run it while fixes are being folded.
2. **Pin and size.** If any doc in the set is untracked by git, it cannot be pinned: stop
   and ask. Docs with uncommitted changes (`git status --porcelain -- <paths>`) are read
   as last committed and named in the matrix header. Note `git rev-parse HEAD`, then
   export the set with `git archive <sha> <paths> | tar -x -C <tmp>/set@<sha7>`, along
   with any project audience file the cold-read gate would pick up for these docs.
   Estimate tokens as `wc -w` × 1.33 per file; when the total passes roughly one third of
   a specialist's context window, stop and ask the user which docs can be left out
   (replaced drafts, plan notes for finished work). Never cut files short. TRACE repeats
   the check with the approved matrix included. Asking in this way replaces the verdict,
   just as STALE does.
3. **Start MATRIX and the ledger together.** Each receives the export directory, each
   file's size, the list of docs read as last committed, and its brief. Budget about ten
   cases per specialist and one read of the set each; never start a specialist for a
   single case.
4. **Approve the matrix** before any tracing; show it to the user, who may approve it but
   does not have to. First re-read, byte for byte in the export, every citation used to
   prune a pair and three or more axis-value citations. Approve only if each axis value
   has a citation, every empty coverage cell has a reason, the UNDERSPECIFIED count and
   the case count and expected cost are stated, and that check passed. A matrix that
   fails goes back once with the mismatches listed; failing again means stop and ask.
5. **Trace in rounds.** Sort traceable cases into their entry lanes; inside each lane,
   order them by score (high to low, then by id) and split into batches of no more than
   ten. In each round, every lane with remaining cases sends one batch, all in parallel.
   If the ten-batch cap leaves fewer batches than lanes, the lanes whose next case has the
   highest score go first, then lane order from the axis table. No case appears in two
   batches. Real token use is several times the expected cost, since every turn re-sends
   the context. After each round, re-read three or more step quotes from every batch; a
   batch that fails is rerun, and the rerun uses up one of the ten batches.
6. **Verify each round** before the next. Give a fresh read-only verifier this step, the
   export directory and the list of claims (not `verify-against-artifact.md`: here the
   artifacts are the docs at the pinned commit, and every claim says a quote really is at
   its cited line). Send: for a CONFLICT, the quote from each side plus the `Protects:`
   quote when present; for a GAP, each step's quote, the nearby quote at the step missing
   a fact, and the `Protects:` quote when present; for an UNDERSPECIFIED case scoring 2 or
   more (matrix cases straight after approval, neighbours in their own round), the nearby
   quote and any anchor quote; for a ledger finding row, its nearby quote. When
   `Protects:` or the anchor is `none`, nothing is sent for it; the case still counts if
   its remaining claims pass, and is filed as a SUGGEST. The tracer alone decides that
   something is missing; for a CONFLICT you read both verified quotes and confirm they
   really cannot both hold. A finding stands only when all of its claims pass; anything
   else goes into `COVERAGE.md` as dropped, with the reason.
7. **Queue neighbours.** For neighbours of verified findings only, give them `X-nn` ids,
   remove duplicates as the brief's case rules say, and queue each under the entry lane
   its own values name, without another approval. UNDERSPECIFIED neighbours are verified
   in the same round and never queued. When two consecutive rounds trace neighbours along
   one axis and none yields a verified finding, stop queuing neighbours along that axis.
8. **Stop** after two consecutive rounds that produce neither a new verified finding nor
   a new kind of finding (its result type together with the attribute or mechanism
   involved; `SUGGEST:` notes are ignored); or when nothing is left to trace; or once ten
   batches have run.
9. **Report.** `FINDINGS.md` uses `../SKILL.md`'s Output template with these changes: `Set:` (the
   paths and the commit) replaces `Doc:` and names the heading; there is no `Measured:`
   line; and `Specialists run:` reads `scenario-traces, mechanism-ledger`, adding
   `cold-read (partner)` if a partner read ran. It holds every verified result: GAPs,
   CONFLICTs, UNDERSPECIFIED cases with score 2 or more, and ledger findings. Each entry
   carries `Why it matters:`, `Protects:`, `Steps:`, `Evidence:` and
   `Case: <id> (<axis values>) · traces/<id>.md · verified`. Severity: an entry that
   quotes what it protects (a requirement or decision) and gives numbered steps is a
   BLOCK for a CONFLICT and a FIX for a GAP or UNDERSPECIFIED case; with either missing,
   it is a SUGGEST. Ledger findings are always SUGGESTs. Verdict: REVISE if any BLOCK;
   READY-WITH-FIXES if no BLOCK and at least one FIX; READY otherwise. BLOCKs and FIXes
   stay open until fixed; this review lists them for the user, and `update-work-plan`
   tracks them if the project has a work-plan layer. `COVERAGE.md` records what the run
   did, which matters most when it found nothing: new verified findings per round and
   axis value; every UNDERSPECIFIED case and its score; each neighbour and the case it
   came from; each dropped finding and why; the cases still untraced; why the run
   stopped, and how many batches it used.

**Partner read (optional).** If the caller says a partner team will receive some of the
docs, run the cold-read gate as written on each of those docs, with two readers playing
the partner in the caller's own words. Its findings go in `FINDINGS.md` tagged
`[cold-read]`, keep the severity the gate gave them, and are checked through
`../SKILL.md` Orchestration steps 6 and 7, not step 6 above. A FAIL or INCOMPLETE gate counts as a
BLOCK.
