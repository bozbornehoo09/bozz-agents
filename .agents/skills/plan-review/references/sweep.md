# Specialist Brief: Completeness Sweep

Your dispatch names **one inventory** from the list below. Take the frozen
plan one step at a time and, for each step, confirm every item of that
inventory against the code as it stands at the plan's pinned heads. Each step
gets a row in your table, including steps where the answer is `n/a`.

The full-pass lenses — plan quality, simplicity, test integrity, safety — are
not yours here. You are counting, not judging the design.

## Authoritative corpus

- The plan and the pinned heads the dispatch gives (`repo @ commit`).
- Those repositories **at those commits and no other**. Read files with
  `git -C <repo> show <commit>:<path>`, or from a `git archive` snapshot of
  the commit if the dispatch names one. Searching is for finding a file; read
  the whole file before you cite it.
- Inventory 8 only: the plans index — the top README of the plans tree
  (`../../writing-implementation-plans/references/plan-tree.md`) — and the
  plan and README of every other plan the index lists as sharing an interface
  or a file with this one.
- Inventory 10 only: `real-system-checks.md` (this folder) and, at the pinned
  head, each section-1 source for every package the plan changes.

## Check for — the inventories

| # | Inventory | For each item, confirm |
|---|---|---|
| 1 | Reads and writes | The store, the key, the fields, the condition, the consistency level. |
| 2 | Payload and wire fields | Each field a step sends or receives: its name, type, encoding and validation. |
| 3 | Permissions and access | Each call a step adds: the identity it runs as, the permission it needs, the resource, and any trust or account boundary it crosses. |
| 4 | State | Each transition, the condition guarding it, and whether it is idempotent under a retry or a duplicate delivery. |
| 5 | Failure handling | Retry policy, timeouts, how a rollback works, and which recovery action runs first. |
| 6 | Environment and configuration | Each environment variable, config value and per-environment constant: where it is set and what it is in every environment. |
| 7 | Tests and observability | The test that proves the step, and the alarm, metric or log line that shows it working after deploy. |
| 8 | Shared files across plans | Each interface in the plans index that this plan touches, checked from both ends: both plans use the same field, key, queue and order, and no file is edited by two plans toward different results. No plans index → one `n/a` row saying so. |
| 9 | Hand-offs between steps | Each value, resource or state an earlier step creates and a later step reads, alters or removes: same name, shape and order — and the later step's precondition still holds both after the earlier step and after that step is rolled back. |
| 10 | Real-system checks | That `real-system-checks.md` section 1 was worked through for every package the step changes (sources listed and cited), the host or environment the check runs in, and — for a step nothing shows alone — its `first observed in` pointer. |

## What a gap is

A gap is an item the step relies on without stating it, or states in a way
the pinned code (or the neighbouring plan) contradicts. Use the severity
criteria in your dispatch, with two rules on top:

- A BLOCK gap spells out the bad end state as numbered steps. Without that
  sequence it is a FIX.
- Inventory 10: a step with no check and no `first observed in` pointer is a
  BLOCK, as `implementation-plan-standard.md` check 9 sets out.

When closing the gap would add a mechanism or a behavior, write
`adds a mechanism` in the row — closure declines those.

## Do not flag (negative scope)

- The nine inventories you were not given.
- Whether the design is right.
- Anything the plan sets aside with an honest out-of-scope note.

## Anti-hallucination contract

- Every row quotes the plan verbatim with `file:line`.
- An `OK` row also quotes the code (or other plan) it checked against. A gap
  row quotes the code or other-plan text that disagrees. Cite either as
  `path:line @ commit`.
- An `n/a` row quotes the step text showing the inventory does not apply.
- Code at any commit you were not given does not exist for you: write "out of
  scope — cannot evaluate".
- Read the entire plan before the first row.

## Output format

```
## Sweep: <inventory number> — <inventory name>
| step | item | result | evidence |
| <step id> | <item> | OK | > "<plan text>" (<file:line>); > "<code text>" (<path:line @ commit>) |
| <step id> | <item> | n/a | > "<step text>" (<file:line>) |
| <step id> | <item> | GAP: <BLOCK|FIX|SUGGEST> | plan > "<text>" (<file:line>) ≠ code > "<text>" (<path:line @ commit>) — <what differs>[; adds a mechanism] |
```

A table of nothing but `OK` and `n/a` rows is this brief's empty report.

Empty report is a valid result. Do not invent findings to look thorough.
