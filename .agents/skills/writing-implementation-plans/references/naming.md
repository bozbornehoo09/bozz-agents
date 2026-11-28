# Naming plan artifacts

## Contents

- [Purpose and adoption](#purpose-and-adoption)
- [Anatomy of an id](#anatomy-of-an-id)
- [Kinds, by family](#kinds-by-family)
- [Choosing the words](#choosing-the-words)
- [Lifecycle](#lifecycle)
- [Where ids appear](#where-ids-appear)
- [Checking an id](#checking-an-id)
- [Migrating old ids](#migrating-old-ids)

## Purpose and adoption

This is the only definition of how plans, steps, pull requests, tests and
gates are named. An id should tell a reader both *what sort of thing* it is
and *which one*, with no lookup.

Each project chooses whether to adopt it. One that does keeps a names table in
its plans index (`plan-tree.md`). One that does not simply skips
`implementation-plan-standard.md` check 10.

## Anatomy of an id

```
<FAMILY>_<kind>[.<modifier>]_<COMPONENT>.<DETAIL>
```

Lowercase segments classify; uppercase segments identify.

- **FAMILY** is one of `PLAN`, `PR`, `TEST`, `GATE`.
- **kind** and the optional **modifier** come from the fixed list in the next
  section, spelled exactly as given there.
- **COMPONENT** is a name from the project's names table. Only an
  integration test may join several, with `+`.
- **DETAIL** says which item of that kind, for that component. The plan id
  itself is the one id without a DETAIL (or a kind): `PLAN_<COMPONENT>`.

A worked set for an invented invoicing system:

| Id | Reads as |
|---|---|
| `PLAN_INVOICE-EXPORTER` | the plan for the invoice exporter |
| `PLAN_step_INVOICE-EXPORTER.ADD-DEAD-LETTER-QUEUE` | one of its steps |
| `PLAN_step.away_WEBHOOK-DISPATCHER.REGISTER-EXPORT-EVENT` | a step whose code lives in another team's repository |
| `PR_INVOICE-EXPORTER.DEAD-LETTER-QUEUE` | the pull request that ships it |
| `TEST_load_INVOICE-EXPORTER.BURST-RETURNS-429` | a load test, named for what must hold |
| `TEST_integration_INVOICE-EXPORTER+WEBHOOK-DISPATCHER.EXPORT-EVENT-DELIVERED` | an integration test across two components |
| `TEST_e2e.manual_BILLING-PORTAL.SHOWS-EXPORT-PROGRESS` | an end-to-end check a person has to carry out |
| `GATE_ask_WEBHOOK-DISPATCHER.RATE-LIMIT-EXEMPTS-EXPORTS` | an answer another team owes |

## Kinds, by family

The list is closed. If something fits none of these, raise it with the user
before inventing a new prefix.

**`PLAN` — the plan and its steps**

- `PLAN_` — the plan for one component; one `PLAN.md`.
- `PLAN_step_` — one step, which `implementing-a-plan` turns into one commit.
- `PLAN_step.away_` — a step whose code sits in a repository another team
  owns.
- `PLAN_manual_` — a step done by hand rather than by an agent (a setting in
  a console, a sign-off).
- `PLAN_precheck_` — something the implementer reads or checks before
  writing code; added at closure under `## Implementer checks`.

**`PR` — pull requests**

- `PR_` — one pull request: the steps it ships, in the packages it touches.
- `PR_away_` — a pull request in a repository another team owns.

**`TEST` — evidence**

- `TEST_component_` — one component on its own (its own stores and queues
  count as part of it): a unit or package test, or checking it in a real
  environment.
- `TEST_integration_` — two or more components, or one component and an
  outside system, working together in one environment.
- `TEST_e2e_` — a whole path a user or caller takes, in a real host.
- `TEST_load_` — behavior at volume or at limits.
- `.manual` after any of the four kinds (`TEST_e2e.manual_`, …) — a person
  has to perform or watch it. An agent running something by hand does not
  make it manual.

**`GATE` — what must be settled before something can proceed**

- `GATE_claim_` — something the plan assumes that can only be confirmed by
  looking; its row names the `TEST_` id that will confirm it.
- `GATE_ask_` — an answer owed by another team or person.
- `GATE_risk_` — a risk the user accepted in writing, with their words quoted
  where the gate is defined.
- `GATE_blocker_` — any other gap that holds up several steps or tests.

## Choosing the words

- **COMPONENT** names are created once per project, as rows in the names
  table, with columns name · purpose and users · plan folder · packages. Say what
  the thing is in one to four words (`INVOICE-EXPORTER`, `BILLING-PORTAL`) —
  never an abbreviation like `IE`. Outside systems a plan touches get rows
  too, so their `away` items have a name to use.
- **DETAIL**, one to six words, depends on the kind: a step names what it
  changes (`ADD-DEAD-LETTER-QUEUE`); a pull request, what it ships; a test,
  the thing that must be true (`BURST-RETURNS-429`); a gate, its claim or
  question; a manual step, the action.
- Words use only `A–Z` and `0–9` and are joined by `-`. The characters `_`,
  `.` and `+` are separators and appear nowhere else.

## Lifecycle

- Once any commit mentions an id, it is fixed. If the scope changes, mint a
  new id and add the old one to the names table's `Retired` list
  (COMPONENT · old id · new id or `none` · reason). Retired ids are never
  reused.
- Steps run in the order their headings appear in the plan; ids carry no
  sequence numbers.
- Ids that come from outside — issue-tracker tickets, a hosting service's
  pull-request numbers — are never renamed.
- **Accepted exceptions.** A name longer than the word limit that was already
  committed when the project adopted this rule stays as it is and goes on the
  names table's `Accepted exceptions` list (name or id · first commit and
  date · reason). Any newer over-long name is fixed: in place if it has not
  been committed yet, otherwise by minting a new id and retiring the old one.

## Where ids appear

| Location | What it carries |
|---|---|
| A plan | Its title, step headings, `PRs:` line and `## Implementer checks` rows |
| A component README | Its `PLAN_` id (`plan-tree.md`) |
| A component's `GATES.md` | A row for each of its test and gate ids |
| A step's commit subject | That step's id (`implementing-a-plan`) |
| A branch name | The `PR_` id itself — git allows `_`, `.` and capitals |
| A published pull request | No id in the title or description, which are written for outside reviewers; the branch name links it back to the plan |
| Anything else (briefs, `first observed in` pointers, …) | The full id, never abbreviated |

## Checking an id

Let `W` stand for one word, `[A-Z0-9]+`, and `D` for a DETAIL, `W(-W){0,5}`.
Let `X` stand for one COMPONENT name:
`([A-Z0-9]+(-[A-Z0-9]+){0,3}|<exception name>|...)`, where the alternatives
after the first are every name on the `Accepted exceptions` list.

A valid id matches the extended regex for its family:

```
plan               ^PLAN_X$
plan items         ^PLAN_(step(\.away)?|manual|precheck)_X\.D$
pull requests      ^PR(_away)?_X\.D$
integration tests  ^TEST_integration(\.manual)?_X(\+X)*\.D$
other tests        ^TEST_(component|e2e|load)(\.manual)?_X\.D$
gates              ^GATE_(claim|ask|risk|blocker)_X\.D$
```

Beyond the pattern:

- an id that is itself on the `Accepted exceptions` list counts as valid;
- every COMPONENT name used must exist in the names table;
- no other id in the tree, live or retired, may be identical.

## Migrating old ids

A project that already has ids like `S1` or `STEP-3` converts them once, at a
time when nobody else is editing the affected files.

1. Put every component in the names table.
2. Add a `Retired` row for each old id with its new id. Key the row by
   COMPONENT *and* old id, since `S1` may exist in every plan.
3. For each row, run `git grep -n -w '<old id>'` across the live files — every
   `PLAN.md`, `GATES.md` and README. Review records and history keep the old
   ids. An old id found outside its own component's folder with nothing to
   say which plan it means is ambiguous: mark that row `resolve by hand` and
   let the user choose.
4. Rename the unambiguous rows, one commit per component folder. Settle the
   by-hand rows. Re-run the step-3 search and paste its empty output into the
   body of the final migration commit.
