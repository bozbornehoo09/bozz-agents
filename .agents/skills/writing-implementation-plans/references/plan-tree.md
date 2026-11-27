# Plan tree layout

Consult this to decide where a plan, its review records and its READMEs go,
and how a plan's status is recorded. The layout groups plans by the design
they serve and puts a short README in every folder, so nobody has to open a
plan just to learn what a folder holds.

## The plans root

Take the first of these that applies:

1. A path the user names for this plan.
2. The `path` of a `context-manifest.yaml` layer with
   `id: implementation-plans`, if the manifest has one.
3. An `implementation-plans/` folder beside the manifest's `work-plan` layer
   (by default `work_tracker/implementation-plans/`).

If the root does not exist yet, PAUSE and confirm before creating it.

## Where a plan goes

```
<plans-root>/<design-slug>/<component>/PLAN.md
```

| Part | Derived from | Example |
|---|---|---|
| `<design-slug>` | The design doc's file name: extension dropped, any `-design` / `-hld` / `-lld`-style suffix dropped, kebab-cased. With no design doc, the requirement's title, kebab-cased. | `invoice-export-design.md` → `invoice-export` |
| `<component>` | The design section (or part of the requirement) the plan's steps change, kebab-cased. | `retry-queue` |

- A plan that would change two components, or serve two designs, is split
  along its steps into two plans.
- The exception is a sequence whose cross-design order *is* the deliverable
  (a release backfill, a staged migration). It gets its own top-level folder,
  `<plans-root>/<sequence>/`, laid out like a component folder.

**Flat layout.** If the tree would be overhead for a small project, keep
`<plans-root>/<PLAN id>.md` files instead and say so in the plans index. The
README rules below then apply only to the index: each plan gets one index row
holding its status and its **plan-review line**, which in this layout stands in
for the component README's. Review records go in `<plans-root>/reviews/`, and
`../../plan-review/references/implementation-plan-standard.md` check 8 is
judged against the flat layout.

## Review records

Each `plan-review` run on a plan is saved as its own file in
`<component>/reviews/`:

```
<YYYY-MM-DD>-<PLAN id>-<kind>-<n>.md
```

`<kind>` is `pass` for a full pass, `sweep` for the closure sweep
(`closure.md`), or `closure` for a diff-only closing review. Each record is the
`plan-review` report as returned; its `Plan:` line, directly under the
`# Plan Review:` heading, gives the plan's path and the commit that was
reviewed.

## A README at every level

With the plan's first commit, add any README missing between its folder and
the root, and update whichever rows and order or interface lines the plan
affects.

| README | Holds |
|---|---|
| `<plans-root>/README.md` — the plans index | A row per design or sequence folder (link, design served); the interfaces between folders; release and test order; and, if the project uses `naming.md`, the names table with its `Retired` and `Accepted exceptions` lists. |
| `<design-slug>/README.md` | A row per component (folder, design section, pull requests and packages, status); interfaces between components and with other folders; shared prerequisites. |
| `<component>/README.md` — 15 lines at most | The `PLAN` id and a one-sentence description of the component; the design lines it serves; links to `PLAN.md` and `GATES.md`; the **plan-review line** (below); its pull requests (the plan's `PRs:` line); its status; what it consumes and what it provides. |

**`<component>/GATES.md`** is optional, for plans with real-system checks or
external questions still open. It is one table with a row per `TEST_` and
`GATE_` id (`naming.md`) and these columns: id · what must be true (with
citation) · what settles it (a test, an answer, a quoted decision) · what
running it needs, and where · the step, stage or merge it holds · status.
Steps refer to these ids; `../../plan-review/references/real-system-checks.md`
defines what a check must name.

If another active plan is also changing a README, ask the user (or that
plan's author) before you edit it, rather than racing them.

## Status and the plan-review line

A component README's status (in flat layout, the plan's index row) is
`draft` until closure finishes (`closure.md` step 6), and `passed` after. A
short note may follow it.

The **plan-review line** has the form

```
plan-review: <path to the final review record> — <verdict>
```

It lives in the component README, or in flat layout in the plan's row of
the plans index. `implementing-a-plan` reads this line as its gate.

READMEs summarize and link. Step text exists only in `PLAN.md`, and nothing
in a README may contradict its `PLAN.md` or the latest review record.
