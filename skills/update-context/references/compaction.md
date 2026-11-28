# Compaction — keeping the temporal layers readable

Contents: [Scope](#scope) · [Governing rule](#the-governing-rule-content-driven-never-size-driven) · [Verbs](#the-three-verbs) · [Keep-test](#the-keep-test-apply-first-to-every-block) · [Reasons](#consolidation-reasons-a-candidate-must-match-one-name-it-in-the-plan) · [Backstops](#backstops--verify-before-proposing-any-cut) · [Never](#never) · [Procedure](#procedure-run-by-the-owning-skill) · [Archive format](#archive-file-format) · [Plan format](#plan-format-print-then-pause)

The temporal layers only ever grow: the work plan's Plan Changes table gains a
row per change, landed items keep their `[x]` lines, and resolved open
questions leave one-line pointers. Past a point, the live file is mostly
history and the next session pays to read it. Compaction moves *aged history*
out of the live file **verbatim** into a sibling archive file, and tightens
bloated entries, without ever changing what the file says is true now.

This is the one definition of compaction. `update-context` flags when it is
due; the layer's own `update-*` skill performs it, so compaction never becomes
a second writer for a layer.

## Scope

Compaction applies only to the **non-authoritative temporal layers**:

| Layer | Owner that compacts | Typical candidates |
|---|---|---|
| Work plan | `update-work-plan` | old Plan Changes rows; `[x]` / `[—]` rows of phases whose exit criteria are met; stacked status snapshots |
| Open questions | `update-open-questions` | old `→ Resolved by ADR-NNNN` pointer stubs |
| Backlog | `update-backlog` | nothing to archive (landed or promoted lines are already removed); only MEGA-ENTRY tightening |

Never compacted:

- **ADRs** — immutable; supersede, never trim.
- **Authoritative layers** (architecture, strategy, rules, orientation, skills) —
  their owners rewrite them as current truth and `docs-review` checks them.
- **The work tracker** — it is the narrative backstop that compaction relies on.
  It is already sharded by week and day, and `context-up` reads only the newest
  entry, so it does not bloat the live view.
- **Cross-review transcripts and archives** (`.agent-bridge/**`) — append-only
  evidence owned by the cross-review helper.
- Any `archive/` file this procedure already wrote.

## The governing rule: content-driven, never size-driven

There is no size target. A long file with nothing consolidatable stays as it
is; a short file with a superseded snapshot gets that snapshot archived. Size
and marker counts only tell you where to look. Every ARCHIVE or COMPRESS
action must name a positive reason the content is safe to move.

## The three verbs

- **KEEP** — leave the block exactly as written. The default.
- **COMPRESS** — rewrite in place, shorter, keeping every fact, decision,
  status, meaning-changing caveat, and open item. Drop a *detail* only after
  confirming that exact detail survives in a cited ADR or tracker entry;
  assumed-preserved is not preserved — when you cannot point at where it
  survives, rephrase tighter and keep it.
- **ARCHIVE** — move the block verbatim to the archive file and leave a
  one-line pointer in the live file.

A block is the smallest independently meaningful unit: a bullet, a table row,
a dated sub-heading section, or a titled paragraph.

## The keep-test (apply first, to every block)

KEEP the block, whatever its size, if any of these hold:

1. It states a **current** status, decision pointer, blocker, open question,
   or to-do.
2. It is the latest status snapshot, the current phase, "Next up", or
   "Blocked".
3. It is **the only home** of a fact — no ADR, tracker entry, or code holds it.
4. It records a **deliberate user divergence** from the template.
5. Moving it would lose information not recoverable from git, the tracker, and
   the ADRs.

Only blocks that fail all five are candidates.

## Consolidation reasons (a candidate must match one; name it in the plan)

- **AGED-HISTORY** — a Plan Changes row, or a completed phase's item rows, older
  than the live horizon (default: the newest 15 Plan Changes rows and the
  current plus previous phase stay live). → ARCHIVE.
- **SUPERSEDED-SNAPSHOT** — a status snapshot or section explicitly marked
  prior, earlier, or superseded, kept only for trace. → ARCHIVE. Do not add,
  remove, or rewrite supersession pointers; that is a fold, not compaction.
- **RESOLVED-POINTER** — an open-questions `→ Resolved by ADR-NNNN` stub older
  than the live horizon (default: the newest 10 stay). → ARCHIVE; the ADR is
  the durable record.
- **REDUNDANT-WITH-ADR** — an entry that restates an ADR's rationale. →
  COMPRESS to a one-liner plus the ADR pointer.
- **MEGA-ENTRY** — one bullet or cell over ~800 characters packing several
  facts plus inline correction narrative. → COMPRESS. Re-run guard: never
  re-compress an entry already under the threshold; a second run must find
  nothing to do.

A candidate that matches none of these cleanly is KEPT. A project can move the
horizons by recording its own values in the live file's header comment.

## Backstops — verify before proposing any cut

- **git-tracked:** `git ls-files --error-unmatch <file>`. An untracked file may
  still be ARCHIVED (moved, not deleted) but never COMPRESSED.
- **tracker coverage:** the archived date range has tracker entries. A stretch
  of history found nowhere else fails keep-test 5 — KEEP it.
- **compress survival:** for each detail a COMPRESS would drop, cite where it
  survives.

## Never

- Never delete. Archive is the only removal, and git is the final backstop.
- Never change meaning: no resolving, reconciling, re-ranking, re-dating, or
  marking items done. If two entries contradict, both survive; reconciling them
  is the owning skill's normal reconcile step.
- Never reorder or restructure surviving sections beyond what compression
  requires.
- Never run unattended. Compaction is propose-then-apply.

## Procedure (run by the owning skill)

1. **Shortlist** cheaply: scan headings and table rows for Plan Changes rows
   past the horizon, completed phases, snapshot markers (`prior`, `earlier`,
   `superseded`, `retained for trace`), resolved-pointer stubs, and entries over
   ~800 characters. Everything else is KEEP without a close read.
2. **Classify** each shortlisted block: keep-test first, then a consolidation
   reason, else KEEP.
3. **Propose** the plan and PAUSE (format below). Write nothing before approval.
4. **Apply**, per file: create the archive file if absent; append ARCHIVE blocks
   verbatim under a dated heading; replace each moved span with one pointer
   line; then rewrite COMPRESS blocks in place.
5. **Verify**: every current status, open item, and the latest snapshot is
   still present; every archived block appears verbatim in the archive file;
   each COMPRESS block still carries every fact it had.
6. **Report** before → after line counts, counts per verb, the archive file
   written, and the three verification results.

Take every date from the system clock (`date +%Y-%m-%d`), never from reasoning
about the calendar.

## Archive file format

Path: beside the live file, `archive/<live-file-stem>-history.md` (so
`work_tracker/work_plan.md` archives to `work_tracker/archive/work_plan-history.md`).
Create it with this header once:

```markdown
# Archived history — <live file name>

Moved out of the live file by compaction to keep it readable. Nothing here is
current state. Substance is also in git history, the work tracker, and the
ADRs. Newest first.
```

Each run adds a `## Archived YYYY-MM-DD` section with the moved blocks verbatim,
newest run first. A moved table keeps its header row. The live file gets one
pointer line where the span was, for example:

`*Plan Changes before 2026-03-01 archived to [archive/work_plan-history.md](archive/work_plan-history.md).*`

`context-up` and the review skills never read `archive/` as current state.

## Plan format (print, then PAUSE)

```text
Compaction plan: <file> (<lines> lines -> ~<lines> lines)
ARCHIVE
- <block label / dated header> — <reason> -> archive/<stem>-history.md
COMPRESS
- <block label> — <reason>; drops <what>, survives in <ADR / tracker entry>
KEEP (confirmed untouched): current phase, Next up, Blocked, latest snapshot, <...>
Downgraded (untracked file): <blocks, or none>
Apply this plan? (y / adjust / n)
```
