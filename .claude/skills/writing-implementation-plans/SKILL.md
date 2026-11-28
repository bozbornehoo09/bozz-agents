---
name: writing-implementation-plans
description: Turn a design (or a requirement) into a hand-off plan so exact that the implementer agent building it decides nothing of consequence, gate it with plan-review until one full pass has no BLOCK, then close it with a completeness sweep and a review of only the closing edits. Use for requests like "draft the plan for this design", "make this buildable by an agent", "prepare a plan for implementing-a-plan", or when a work-plan item needs a plan before it can be built. Reviewing a plan someone else wrote is plan-review; building a passed plan is implementing-a-plan.
---

# Writing Implementation Plans

Three skills share the plan lifecycle. This one writes the plan;
`plan-review` decides whether it passes; `implementing-a-plan` builds it.

The rules the plan must meet are defined elsewhere, and this skill does not
repeat them. All three files are in `../plan-review/references/` — if that
folder is missing, tell the user `plan-review` has to be installed next to
this skill, and stop.

| File | What it sets |
|---|---|
| `implementation-plan-standard.md` | The authoring bar. The plan meets every check on it, check 7's section and count line included. |
| `real-system-checks.md` | What each step's `Real-system check:` must contain. |
| `simplicity.md` | What counts as a mechanism, a second writer, and the mechanism count. Use its definitions unchanged. |

## Scope

In scope:
- The plan file, the READMEs around it and, optionally, its `GATES.md`, laid
  out per `references/plan-tree.md`.
- The review records from each `plan-review` run, and folding their findings
  back into the plan.

Out of scope:
- The design itself — design docs, ADRs, rule files. This skill never edits
  them and never settles a design question (step 3). New decisions go through
  `update-decisions`; design edits through the `update-*` skill that owns that
  layer.
- Building the plan → `implementing-a-plan`.
- Roadmaps and work-plan items nobody will build from directly →
  `update-work-plan`.

## Inputs

- What the plan serves: design docs and ADRs, or — with no design — the
  requirement or work-plan item. Find design and decision files through the
  `architecture`, `decisions` and `rules` layers of `context-manifest.yaml`.
- The target package and where it lives.
- Where the plan goes: the user's path, otherwise `references/plan-tree.md`.

## Steps

1. **Read the design end to end.** Note, each with `file:line`:
   - the lines the plan will implement (every step cites one);
   - for every stored value the plan touches, which component the design or
     an ADR makes its writer;
   - every mechanism the design specifies for the components under change —
     the "design" half of the mechanism count.

   When there is no design, record requirement lines instead, and read
   "requirement line" wherever these steps say "design line".

2. **Read the code.** In the target package:
   - read the README and the build file, and run `git ls-files`;
   - copy the build and test commands exactly as the build file or task
     runner defines them (a command the README mentions but the build file
     does not define is recorded as such, not used — `plan-review` check 5
     rejects it);
   - work through `real-system-checks.md` section 1 to find how this package
     is verified, recording each source you read;
   - pick one to three pattern files to copy from: among files doing the same
     kind of work, the ones changed most recently (`git log`);
   - open every file and symbol the plan will mention; anything not there yet
     is marked new;
   - write down the pinned heads (`repo @ commit`) you read all of this at.

3. **Separate details from design calls — before drafting.**

   | Kind | Examples | What to do |
   |---|---|---|
   | Implementation detail | Naming; how files are arranged within a component the design already has; a test fixture; an edge case inside a designed step | Make the call yourself and state it in the step. |
   | Design call | Anything a design reviewer would expect to weigh in on — a limit, a schedule, how keys are laid out, what a contract looks like — plus whatever `simplicity.md` checks 1–3 would flag with no design line behind it | Leave the design as it is and escalate: ask the user, or, when nobody is available, settle it with `deciding-calls-by-debate` and flag the result for the user to confirm. |

   Drafting waits until every call has an answer. The answer is recorded in
   the design or an ADR by that layer's owner, and the plan cites the line.
   An approved answer that departs from the design is recorded instead as a
   row under `## Plan Changes`, citing where it was decided. Until all calls
   are answered, report the blocked output.

4. **Draft.**
   - Put the plan and its READMEs where `references/plan-tree.md` says.
   - If the project uses `references/naming.md`, give the plan, steps, pull
     requests, tests and gates ids by it; a new component goes into the names
     table first.
   - Read the project's overrides register, located as
     `../code-review/references/register.md` defines, whenever one is found,
     and write no step that prescribes what an entry rejects.
   - Every number or guard the plan sets comes with its reason, phrased so a
     code comment could carry it (the constraint behind it) — never just a
     link to the design.
   - Each step is a single commit for `implementing-a-plan`, builds on its
     own and passes its own tests. Its "Done when" is what the step's
     `Real-system check:` will show.

   Cover at least the following. The field names marked † are read by other
   skills and are kept exactly; order and the rest of the layout are yours.

   ```
   # <PLAN id or title> — <topic>

   Hand-off: implementer agent †
   Package: <name> (<dir>)
   Pinned heads: <repo> @ <commit>[, ...] †      every file:line below is at these
   Serves:
   - <design or ADR file:line> — "<verbatim line>"
   Build: `<command>` — <build file:line>
   Test: `<command>` — <build file:line>
   Copy from: <path> — <what to copy: style, test layout, wiring>
   PRs: <PR id or name> ships <step ids> in <packages> †
   mechanism count: design N / plan N †

   ## What this plan does not add †
   - <mechanism considered> — unneeded because <design file:line>     (or: None considered.)

   ## Steps
   ### <step id> — <title>
   - Implements: <design file:line> — "<verbatim line>"
   - Files: <path> (new) | <path> (edit)
   - Change: <signatures, data shapes, control flow, every edge case>
   - Tests: <named case: input → expected>
   - Real-system check: <method, file:line@commit> · <host/env> · <look-for> · <needs, or none> · <holds: stage or merge> †
     (or: first observed in <step id>)
   - Done when: <what the real-system check shows>
   - Leave alone: <files and behavior the step must not change>

   ## Plan Changes        (only when the user approved a departure from the design)
   ## Implementer checks † (written at closure; always the last section)
   ```

5. **Review with `plan-review` until a full pass has no BLOCK.** Tell it the
   plan is an implementer hand-off, and hand it the design docs and ADRs the
   plan cites so its simplicity lens has them. Before each pass, commit the
   plan by explicit path so the pass reviews a commit; save each report as a
   review record (`references/plan-tree.md`). Every BLOCK and FIX is a
   hypothesis until you re-read its cited lines
   (`../fold-review-findings/SKILL.md`: verify first, edit second); for each one
   that holds:
   - **Real defect** — a bad end state the plan can reach, a choice left to
     the implementer, the plan disagreeing with its design or with the code:
     fold the fix into the plan.
   - **Needs a design call** — send it to step 3; do not decide it in the plan.
   - **You think it is wrong** — it stays in each new report until it is
     folded or the plan records it as a departure the user approved (a
     `## Plan Changes` row, which `plan-review` honours). Raise it through
     step 3. Never park it in a separate file.

   Only a full pass can end this loop. When the first full pass has no BLOCK,
   move straight to closure (`references/closure.md`); its FIXes are triaged
   there rather than folded here. If one BLOCK survives two rounds of folding,
   or comes back after its step-3 answer, stop and report the blocked output.

6. **Commit for the implementer.** Check every quoted design line against its
   `file:line` once more. Update the component README's status and its
   plan-review line (flat layout: the plan's plans-index row) from closure's
   final record (`references/plan-tree.md`).
   Then commit the plan, the sweep record, the review records and the READMEs
   together, by explicit path, so the gate in `implementing-a-plan` step 1
   passes. Any later edit to the plan follows the after-done rule in
   `references/closure.md`; a change to a README alone needs no new review.

## Pause-for-confirmation rules

- PAUSE before creating the plans root or the plans index if neither exists.
- PAUSE on every design call (step 3): ask the user — or, when no one is
  available, use `deciding-calls-by-debate` and mark the result for the user
  to confirm.
- PAUSE before restarting a full review once closure has begun
  (`references/closure.md`, "Restart triggers").
- Never edit a design doc, ADR or rule file; hand the change to the
  `update-*` skill that owns it.

## Style

- Write for an implementer that takes every word literally: exact paths,
  exact commands, exact signatures, every test case listed. Never "etc." or
  "as appropriate".
- Design lines are quoted word for word with `file:line`, never paraphrased.
- Prose gives the *why*, in words a code comment could carry. The *what* of a
  step is written once, in `PLAN.md`; READMEs summarize and link to it.

## Anti-hallucination contract

- Every file, symbol, command and design line in the plan was opened or run
  during this session, and every design line is quoted verbatim with
  `file:line`. Anything not seen is marked `unverified`, and the plan is not
  handed off while any `unverified` mark remains.
- The build and test commands are copied from the package's own build file
  or task runner, and the plan cites the line each came from.
- The plan is never reported as passed without both its sweep record and a
  final review record (`references/closure.md` step 6) that has no BLOCK and
  covers the committed plan text.
- An answer to a design call goes into the plan only together with a citation
  of where it was decided: an ADR, a design line, or the user's words quoted.

## Output format

Passed:

```
Plan: <path> @ <commit>
plan-review: <final record path> — <READY | READY-WITH-FIXES>, full pass N, then closure (<sweep record path>); implementer checks: K
mechanism count: design N / plan N
Next: implementing-a-plan
```

Blocked (nothing handed off):

```
Plan: <path> (draft — not handed off)
Blocked on: <design call: the question> | <unverified item> | <finding that will not fold> | closure reopened
```

## What this skill is NOT

- Not `plan-review`, which only reads and reports; this skill uses it as the
  gate.
- Not `implementing-a-plan`, which builds a passed plan one commit per step.
- Not a design document. A design is written for human reviewers; this plan
  is written for an implementer agent.
- Not where design questions get decided — those are escalated, never settled
  inside the plan.
- Not for roadmaps or work-plan items nobody will build from directly.
