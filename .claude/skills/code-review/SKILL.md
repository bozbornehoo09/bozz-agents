---
name: code-review
description: Review uncommitted changes or a specific commit/range for defects and against the project's ADRs, rules, and standing owner overrides. Use after implementing a phase of a plan, before committing, or on a PR diff. Fans out built-in lenses (correctness and tests, precedents and reuse, decisions and scope, comments, owner overrides) plus any project architecture briefs in parallel, and reports findings ranked by severity.
---

# Code Review

Read a change looking for what is wrong with it. The review runs two kinds of
specialist side by side: five **built-in lenses** that ship here and apply to
any codebase, and the **project briefs** you write for your own architecture.
The report is a ranked list of findings, not a narrative, and this skill
changes no code.

## Inputs

The review target is one of:
- Uncommitted working-tree changes — default. Resolve via `git diff HEAD` and `git status`.
- A commit SHA or range — `git diff <sha>` or `git diff <base>..<head>`.
- A PR — `gh pr diff <num>`, with its description.

The user may also pass the plan or spec the change implements and local paths
to comparable codebases to treat as precedent.

When nothing resolves to a diff or a list of changed files, ask the user what
to review instead of guessing. For a diff over ~500 lines, ask whether to
review it whole or in file groups.

## Corpus

Paths come from the layers in `context-manifest.yaml` at the project root, or
the shipped defaults when there is no manifest.

- The code: the diff, each changed file in full, the tests that exercise it,
  and as much nearby code (callers, callees) as judging behavior takes. Docs
  tell a reviewer what the code must satisfy; they never replace reading it.
- The change description, and the plan or spec when one is given.
- Decisions (`id: decisions`, default `docs/decisions/`): the index plus every
  Accepted ADR.
- Rules (`id: rules`), for any project brief that cites them.
- The project's overrides register, located as `references/register.md`
  defines; that file also gives its entry format.
- Comparable codebases, and only those the user names.

## Specialists

One brief in `references/` per lens; each runs as a separate read-only
reviewer.

**Built-in lenses** run on every review:

| Brief | Lens | What it hunts |
|---|---|---|
| `lens-correctness.md` | Correctness, simplicity and tests | Bugs and regressions; callers a changed contract breaks; code or tests that could be removed; description claims the code contradicts; guards with no test, or that no input can reach; tests asserting something other than our logic. |
| `lens-precedents.md` | Precedents and reuse | Whether each new construct already exists in this repository (or a named comparable codebase), and the verdict: REUSE, COPY, or OK. |
| `lens-decisions.md` | Decisions and scope | Code or text an Accepted ADR rules out or a newer ADR has overtaken; architectural choices with no ADR; code serving a later phase. |
| `lens-comments.md` | Comments | Each added or edited comment against rules C1–C10 and their severities in `../refining-technical-writing/references/code-comments.md` (true, says why, explains its numbers, self-contained with no document or ticket ids, consistent terms, present where a reader would be lost). |
| `lens-overrides.md` | Owner overrides | Each live register entry, applied as a hard rule. Skipped when the project keeps no register. |

**Project briefs** are yours. Copy `_brief-template.md` under a descriptive
name (`architecture.md`, `security.md`, ...) and add a row below saying when
it runs. Two or three briefs that always run is a good ceiling; gate the rest
on which paths the diff touches. `docs/customizing.md` covers writing them.

| Brief | When to run |
|---|---|
| `_brief-template.md` | Template only — copy it to create real briefs; do not run as-is |
| _(your `architecture.md`)_ | Always |
| _(your domain brief)_ | When the diff touches that domain's paths |

## Orchestration

1. **Resolve.** Collect the diff, the changed-file list, and the corpus, and
   record whether the project has an overrides register.
2. **Dispatch.** In one parallel fan-out, through whatever subagent or
   delegation facility the host provides, start a read-only specialist for
   each applicable brief: all built-in lenses (the overrides lens only when a
   register exists) and every project brief whose condition matches. On a
   rate limit or capacity error, retry the failed calls at half the
   concurrency, down to one at a time; retry any other failure once, then
   record that lens as failed. Every dispatch gets:
   ```
   Review this change against {brief_path}.
   Changed files: {file_list}
   Diff: {diff_content}
   Corpus paths: {the paths this brief's corpus names}
   Anti-hallucination contract: every finding requires a verbatim quote
   AND a file:line citation. Cross-reference findings require both sides.
   An empty report is correct when no findings exist.
   Use the output format in the brief. Number findings <lens>-<n>.
   End with: COUNTS: BLOCK <n> FIX <n> SUGGEST <n>
   ```
   If a brief's corpus will not fit in one specialist's context, run that
   brief as several parts, each over one group of files, then settle the
   pairs they could not judge with one pair call, as
   `../skill-review/references/review-completeness.md` section 2 says.
3. **Check every BLOCK.** Open each cited line and compare the quote
   byte-for-byte — both ends of a cross-reference, and for an `OV-<n>` the
   Rule at its register line. A BLOCK that does not match is dropped.
4. **Sample the rest.** Check at least three FIX and three SUGGEST findings
   from each lens the same way; for a claimed missing test, search the test
   files the finding lists. Drop any that do not hold.
5. **Merge and rank.** Where lenses flag the same file:line, keep one finding
   carrying all their ids, any `OV-<n>`, and the higher severity. Remove an
   `OV-<n>` tag that did not come from the overrides lens. Remove a cleared
   check whose file:line now carries a finding. Order by severity, then by
   position in the diff.
6. **Verdict** on one line: REVISE if any BLOCK; READY-WITH-FIXES if no BLOCK
   and at least one FIX; READY otherwise. SUGGEST findings never change the
   verdict. A lens that failed, or came back without its `COUNTS:` line or
   unable to do a required read or check, makes it REVISE
   (`../skill-review/references/review-completeness.md` section 1).

## Anti-hallucination contract (binding on every specialist)

These rules are non-negotiable. The orchestrator **drops** any finding that violates them.

1. **Every finding MUST include a verbatim quote** of the offending code or text. Format: `> "exact text"`. Paraphrases are invalid.
2. **Every finding MUST cite `file:line`.** No line number → finding invalid.
3. **Cross-reference findings require quotes from BOTH sides** — the code AND the ADR clause, rule, register entry, or precedent — with `file:line` for each.
4. **"Missing element" findings quote the surrounding context** where the element should appear, so the absence is verifiable.
5. **`OV-<n>` belongs to the overrides lens.** No other lens tags a register entry; that lens quotes the entry's Rule at its register line.
6. **Unconfirmed suspicions say so.** Prefix them `Hypothesis:` and name the evidence that would settle them. A convention the corpus does not show is not a convention.
7. **An empty report is the correct output when no findings exist.** Do not pad the report.
8. **Out-of-scope corpus is invisible.** Each brief declares what it does NOT review; specialists stay in their lens.

## Do not flag (negative scope)

- Cosmetic choices — layout, formatting, names — that change no behavior and
  break no rule, register entry, or established precedent. (A comment's
  content is not cosmetic: it belongs to the comments lens.)
- Problems that predate the diff and that the diff does not touch or worsen.
- Scope the plan records as deliberate, unless a newer ADR or a register entry
  contradicts the plan (raise that as a `PLAN` finding).
- "More tests" with no specific behavior left uncovered.
- Generated output, unless its source changed and it was not regenerated.

## Severity criteria

- **BLOCK** — merging is unsafe: wrong behavior, lost data, a security hole, or an outage-grade operational failure; or the change breaks a CRITICAL OVERRIDE / hard rule in a rule file or contradicts an Accepted ADR.
- **FIX** — a real defect, regression, avoidable complexity, or rule breach to correct before merge. Any finding tagged `OV-<n>` is FIX or higher.
- **SUGGEST** — worth considering; nothing is broken without it.

**PLAN** tag: the code faithfully follows its plan, but the plan itself is
the mistake. Such a finding quotes the plan line and the code, citing each.

## Output template

```
# Code Review: <commit message or "uncommitted changes">

Scope: <n> files (+<adds>/-<dels>)
Specialists run: <returned; split parts and pair call named>; failed: <lens that failed or came back unfinished | none>; skipped: <lens — reason, e.g. "overrides — no register" | none>
Checked: <n> BLOCK quotes re-read; <n> others sampled; <n> dropped

## BLOCK
- <id> [<lens>] [OV-<n>] [PLAN] <path>:<line>
  > "<verbatim offending line>"
  <what goes wrong, or which rule it breaks>
  → <ADR, rule, register entry, or precedent> "<verbatim clause>"

## FIX
- ...

## SUGGEST
- ...

## Cleared checks
- <a significant check that passed; each OK precedent with both cites>

Verdict: REVISE
```

## What this skill is NOT

- Not a linter or formatter — assume those run separately.
- Not the test suite — a specialist may run a small, safe probe, but running the suite belongs to CI.
- Not `plan-review` — this judges code that exists; `plan-review` judges a plan before code (and borrows `lens-overrides.md` for it).
- Not `docs-review` — docs only constrain the code here.
- Not a substitute for human review on shared or critical code. In a personal project the fan-out is enough; elsewhere a human still reads the diff.
- Not a generic SOLID/DRY checker — every check traces to a brief in `references/`.
