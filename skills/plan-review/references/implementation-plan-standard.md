# Specialist Brief: Implementation-Plan Standard

## Contents

- [Your question](#your-question)
- [Authoritative corpus](#authoritative-corpus)
- [Check for](#check-for)
- [Check details](#check-details)
- [Do not flag (negative scope)](#do-not-flag-negative-scope)
- [Anti-hallucination contract](#anti-hallucination-contract)
- [Output format](#output-format)

## Your question

The plan under review will be handed to an implementer agent that builds what
it reads and nothing more — and that agent may be a smaller model than the one
that wrote the plan. Ask one thing: **is any decision with consequences still
open for that agent?** You judge how complete and how precise the hand-off is,
and whether the plan sits where the project keeps its plans.

Other lenses own the rest: general plan quality (`plan-hygiene.md`), test
integrity (`testing-discipline.md`), production safety
(`production-safety.md`), extra machinery (`simplicity.md`), and fit with the
architecture (the project's own briefs).

The same list doubles as the **authoring bar**. `writing-implementation-plans`
drafts against it, and anyone else preparing work for an implementer agent
should too.

## Authoritative corpus

Always:

- The plan text.
- Every file the plan names as a target or as a pattern to copy — open each to
  confirm it exists and fits.
- The target package's README, its build file (`package.json`,
  `pyproject.toml`, `Makefile`, `build.gradle`, `Cargo.toml` or the
  equivalent), and a `git ls-files` listing of the package.

Per check:

| Check | Extra files |
|---|---|
| 8 | `../../writing-implementation-plans/references/plan-tree.md`, plus the README of the plan's folder and of every folder above it up to the plans root. |
| 9 | `real-system-checks.md` (this folder), and the section-1 sources for each changed package. |
| 10 | `../../writing-implementation-plans/references/naming.md` and the names table in the plans index, including its `Retired` and `Accepted exceptions` lists. |

## Check for

Ordered by importance. "Details" points to the section below where a check
needs more than one line.

| # | The gap | Severity |
|---|---|---|
| 1 | A step's target is vague ("the webhook handler") or is a path that is neither in the `git ls-files` listing nor marked new. | FIX |
| 2 | The change leaves the implementer to settle something the plan never mentions: a signature, a data shape, the control flow, or an edge case such as empty input, a duplicate, a retry or a partial failure. | BLOCK if the answer changes behavior; else FIX |
| 3 | No existing file — one to three of them, in the same package — is named as the pattern to copy for style, tests and wiring. | FIX |
| 4 | Tests are promised in general ("add coverage") rather than listed as named cases, each with its input and expected result. | FIX |
| 5 | A build or test command cannot be run as written, or is not defined in the package's build file or task runner (`package.json` scripts, a `Makefile`, `pyproject.toml`, or the local equivalent); a command found only in a README fails this check. | FIX |
| 6 | A step has no condition that tells the implementer it is finished, or does not say which files and behavior must be left alone. | FIX |
| 7 | The "What this plan does not add" section or the mechanism-count line is absent or incomplete. | Details |
| 8 | The plan is not where the project's plan tree says it should be. | FIX; Details |
| 9 | A step changes something observable but has no adequate real-system check. | Details |
| 10 | An id breaks the project's naming rule. | FIX; Details |

## Check details

**Where checks 2 and 6 stop.** A fork the plan *names* openly ("queue or
cron?") belongs to `plan-hygiene.md`; check 2 is for the gaps the plan is
silent about. Likewise a plan-wide scope boundary and a measurable goal are
`plan-hygiene.md`'s; check 6 is per step.

**Check 7 — what the plan leaves out.** A hand-off plan has a section titled
exactly `What this plan does not add`. It lists every mechanism the author
considered and left out, and beside each the design line that makes it
unnecessary (with no design, the requirement line). `None considered.` is an
acceptable entry. The plan header also carries one line in the form
`mechanism count: design N / plan N`, counted as `simplicity.md` check 7
describes.

- Section absent, or count line absent: **BLOCK**.
- A listed mechanism with no design (or requirement) line beside it: **FIX**.
- Whether the numbers are right is `simplicity.md`'s question, not yours.

**Check 8 — placement.** When the project keeps a plan tree, flag a plan whose
path, missing README, own README, or the README rows above it disagree with
`plan-tree.md`. A project with no plans index has no tree: skip the check and
say so in a `Skipped:` line.

**Check 9 — real-system evidence.** Any step that changes what a user, a
caller or a running system can observe needs a `Real-system check:` meeting
`real-system-checks.md` sections 2–4.

| What you find | Severity |
|---|---|
| Neither a `Real-system check:` line nor a `first observed in` pointer — even if "done" is defined as a green build and passing tests | BLOCK |
| The check names nothing beyond the build or unit tests | FIX |
| The method is not quoted, with `file:line`, from a section-1 source | FIX |
| The method was written for a different host than the one that actually loads the change | FIX |
| The check says who runs it instead of what running it requires | FIX |

**Check 10 — ids.** Applies only when the project has adopted `naming.md`;
otherwise skip and say so. Flag any id `naming.md` defines — in the plan, its
README or its `GATES.md` — that fails a clause under `naming.md` "Checking an
id". A plan that predates the project's adoption of the rule and has no names
table gets a single finding for the whole plan, not one per id.

## Do not flag (negative scope)

- Plans that are not implementer hand-offs: roadmaps, work-plan rows, ADR
  proposals.
- Whether the design is the right design.
- Anything the lenses listed under "Your question" own.
- A step that prescribes what an overrides-register entry rejects. That is
  `../../code-review/references/lens-overrides.md`, which `plan-review`
  dispatches whenever it finds a register.

## Anti-hallucination contract

Every finding quotes the plan text verbatim and cites `file:line` (or
`section:line`); without both it is dropped. Then, by kind:

| Finding | Must also carry |
|---|---|
| Something missing (pattern file, test list, command) | A quote of the step where it should have appeared. For check 7, the plan header where the section or count line belongs. |
| Target or pattern file | The path you checked and what you found there. |
| Wrong build or test command | The real command, quoted from the build file or task runner with `file:line`. |
| Check 8 | The `plan-tree.md` line and the plan, README or listing entry that conflicts with it, both cited. |
| Check 9 | The step, and either the doc line in the package that describes the method or the list of section-1 sources you searched without result. If a section-1 source was never handed to you, answer "out of scope — cannot evaluate" rather than claiming it is empty. For the wrong-host case, also quote the loader or host configuration that shows where the change is loaded. |
| Check 10 | The offending id and where it sits, plus the `naming.md` rule it breaks, quoted with its line. If the clash would be with an id in some file outside your corpus, answer "out of scope — cannot evaluate". |

A complete hand-off produces an **empty report**, and that is correct. Read
the whole plan and every file you were given before reporting.

## Output format

```
Skipped: <check N — reason>          (only for a check that says to skip and say so)

[implementation-plan-standard] <file:line> [BLOCK|FIX|SUGGEST]
Finding: <one sentence: the decision left to the implementer, or what is absent>
Quote: > "<verbatim plan text>"
Source: > "<verbatim README / build file / rule text>" (<file:line>)     (when there is a second side)
Implementer check: step <id> · check: <what to verify> · surfaced by > "<the step's test or build line>" · on failure: <action>     (optional; FIX/SUGGEST that may wait for build time — SKILL.md "Implementer checks")
```

Empty report is a valid result. Do not invent findings to look thorough.
