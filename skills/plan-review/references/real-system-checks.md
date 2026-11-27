# Real-system checks

**Passing unit tests and a clean build do not show that a change works.** When
a step changes how a real system behaves, someone looks at that system before
the change ships. This file is the only place that rule is written down; the
skills that plan, review or build steps link here instead of repeating it.

It is shared corpus rather than a specialist brief. `plan-review` hands it to
the `implementation-plan-standard.md`, `testing-discipline.md` and
`sweep.md` (inventory 10) dispatches.

## 1. Find the package's documented method

Before writing or judging a check, look up how this package is actually
verified. For each package a step touches, go through every source in the
table, and note each one you consulted as `file:line@commit`.

| Source | Look at | Usually tells you |
|---|---|---|
| 1. The package README | Sections on testing, running locally, manual verification, staging or preview environments — and any docs pages they link | The procedure itself |
| 2. The pull-request template | `.github/pull_request_template.md`, `.gitlab/merge_request_templates/`, or the repo's own equivalent | What reviewers expect a change to claim |
| 3. CI/CD configuration | Which suites run at which stage, approval gates, soak periods, any documented way to run a stage's checks before merging | The automated gate after merge |
| 4. Contributor and agent docs | `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, the project's skills | Often the only written staging procedure |
| 5. Recently merged pull requests | Roughly the last ten descriptions, not just their commit messages | What people really run, and what reviewers accept |
| 6. The host, for a front end something else loads | The loader's map from environment to URL, and the host's development path | Whether a recipe exists for *this* host — one written for a neighbouring host does not transfer |
| 7. Environment safety rules | Approved test accounts, extra approval for production, alarms a manual override can set off | Limits on how the check may be run |
| 8. Nothing found | — | Write that down plainly ("CI only", "none documented") and raise it with the user as an open item. Do not make up a recipe. |

## 2. What a check names

A `Real-system check:` gives five things, in this order:

1. **Method** — quoted from a section-1 source, with `file:line@commit`.
2. **Where** — the host or environment it runs in.
3. **Look-for** — exactly what is observed: an output, a screen, a row, a log
   line, a metric.
4. **Needs** — whatever running it takes beyond the implementer's own tools
   (a signed-in browser, credentials above read-only, access to a particular
   host), or `none`.
5. **Holds** — the stage or the merge that waits on it.

A check never names a person. Who runs it is settled outside the plan; the
plan says only what running it takes.

**Not yet run.** Record it as `pending: <where>, needs <what>`, giving the
host or stage and the missing requirement — for example `needs the merge`
(it can only run after merge), `needs a signed-in browser`, `needs
credentials above read-only`.

**When the implementer cannot run it:**

- write the `pending:` line, and copy the method, the target environment and
  the plan's look-fors word for word, so whoever does run it has all of it;
- do not leave behind a local-only config edit or a running dev server unless
  the plan says to;
- for a host with no recipe, write only the method you inferred, marked
  `inferred, unverified`, and tell the user the recipe is missing.

A look-for that fails is the implementer's to fix, rebuild and record again.

## 3. Backend steps

Run it in a non-production environment and name both halves: what you call,
and where the result is read back from — a row in a table, a log search, a
metric, an alarm.

## 4. A step nothing shows alone

A step that only adds library code or types names the later step where its
effect first becomes visible: `first observed in <step id>`. That later
step's check then covers both. "N/A" is accepted only together with that
pointer.

## 5. Pull request versus merge

Opening a pull request before the check has run is fine if its description
says so in plain words. Merging — or promoting to production — waits for the
check, unless the user waives it in writing. Record a waiver in the user's own
words, quoted, as `waived: <date>, "<words>"`, either on the step's
`Observed:` line or in the pull request's testing section. A description never
claims a check that did not run.

## Where each skill applies it

| Skill | Where |
|---|---|
| `plan-review` | Three lenses: the hand-off standard (check 9, on each step's field), testing discipline (check 8), and the sweep (inventory 10) |
| `writing-implementation-plans` | Every step's `Real-system check:` field, and the component's `GATES.md` where the project keeps one (`../../writing-implementation-plans/references/plan-tree.md`) |
| `implementing-a-plan` | Runs the check, or records a `pending:` line (section 2) or a `waived:` line (section 5). Build and tests alone never finish a step. |
