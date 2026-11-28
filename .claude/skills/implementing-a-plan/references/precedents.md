# PRECEDENTS.md — the precedent record

This file is the one definition of `PRECEDENTS.md`. `implementing-a-plan`
writes it (step 4.2); `preparing-code-reviews` reads it for the PR
description and for the review loop's precedent checkouts. Other files point
here rather than restating the format.

The point of the record: for every choice a reviewer might ask "why this way?",
show that the change does what existing code already does — or, where it does
not, which line of the plan decided that.

## When a row is needed

A step makes a non-obvious choice when a competent reader could reasonably
have done it another way. Typical cases:

- wiring: how a component is registered, injected or started;
- build or packaging configuration: a dependency, a plugin, an artifact
  layout, a script entry;
- the shape of an error: its type, code, message or mapping;
- a name: a module, class, key, metric or route;
- a handler or middleware chain: what runs, in which order.

A change the plan spells out to the character and that has only one sensible
form needs no row.

## Where to look

1. **This repository first**, at the commit the step builds on: the same
   module, then shared modules, then the rest. Cite each hit as
   `<path>:<line>@<short sha>`.
2. **Comparable public repositories, only those the user names.** For a
   public URL the user gave, a read-only shallow clone into a temporary
   directory is fine:
   ```bash
   git clone --depth 1 <public url> <tmp>/<name>
   git -C <tmp>/<name> rev-parse --short HEAD     # the commit you cite
   ```
   Never clone from a private or internal host, never supply credentials, and
   never clone a repository the user did not name. Run nothing from a clone;
   read it only.

Open and read every precedent before citing it.

## Format

The file lives in the working folder — the folder that holds the plan, where
`ASK-<step id>.md` files also go — and is never part of a step's commit. One
header line lists the clones, then one table row per choice:

```
Checkouts: <public url> @ <sha> -> <local dir>; ...   (or: Checkouts: none)

| step | choice | ours | precedents | verdict |
|---|---|---|---|---|
| PLAN_step_EXPORT-CLIENT.ADD-RETRY-BACKOFF | retry backoff on the export client | src/export/client.py:42 | src/billing/client.py:57@3f9c2ab; webhook-dispatcher lib/http.py:88@b71e0d4 | matches |
| PLAN_step_EXPORT-CLIENT.MAP-REJECTED-ERROR | error code for a rejected export | src/export/errors.py:12 | src/orders/errors.py:30@3f9c2ab | differs: PLAN.md:118 |
| PLAN_step_EXPORT-CLIENT.EMIT-LAG-METRIC | metric name `export.batch.lag` | src/export/metrics.py:9 | — | no precedent: searched src/**/metrics.py and webhook-dispatcher; no lag metric exists |
```

Verdicts, exactly one per row:

- `matches` — ours makes the same choice as the precedents cited.
- `differs: <plan file:line>` — ours departs from the precedents, and that
  plan line decides the departure. A `differs` without a plan line is a
  deviation: stop under `../SKILL.md` step 5.
- `no precedent: <where you searched; why none applies>` — nothing comparable
  was found.

These verdicts line up with `../../code-review/references/lens-precedents.md`:
`matches` is its OK, a `differs` with a plan line is its plan-decided
departure, and `no precedent` is its "no precedent found in <where you
searched>".

## Keeping it current

When a later step or a review fold removes a choice, delete its row. When a
cited line moves, update the cite. A row whose precedent no longer shows the
claimed choice is fixed or removed before the branch is handed on.
