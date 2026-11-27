---
name: implementing-a-plan
description: Build a reviewed, closed implementation plan to the letter on its own branch — a commit for every plan step, each carrying its test, check, build and real-system results — and halt with a question as soon as the repository or a result contradicts the plan; when all steps are in, pass the branch to preparing-code-reviews. Use when a plan closed by writing-implementation-plans is ready to build, or the user asks to "implement the plan", "build this plan" or "work through the plan's steps".
---

# Implementing a Plan

This skill is the builder for a plan that has already passed review. The plan
decides; the builder does not
(`../plan-review/references/implementation-plan-standard.md`). When the repo,
a test or a command disagrees with what a step says, that disagreement goes to
the user as a question. It is never settled by reading the step generously.

Real-system checks follow `../plan-review/references/real-system-checks.md`;
this file cites its sections and does not repeat them.

## Scope

In scope:
- The code change each plan step describes, confined to the files that step
  lists.
- A branch of its own carrying exactly one local commit per step.
- Running, per step, the tests, the plan's implementer checks, the
  real-system check and the build, and writing their results into the commit.
- Recording each non-obvious choice a step makes, with its precedents, in
  `PRECEDENTS.md` (`references/precedents.md` defines the file).

Out of scope:
- Changing the plan → `writing-implementation-plans` (its after-done rule).
- Rebasing, squashing, the PR description, the pre-flight review loop,
  pushing and opening the PR → `preparing-code-reviews`, which step 6 hands
  the branch to.
- Deciding what counts as a defect → `code-review` (run by
  `preparing-code-reviews`).
- Merge, deploy and rollback.

## Inputs

- The plan's path, its sweep record and its final review record
  (`../writing-implementation-plans/references/plan-tree.md`).
- The package and its directory.
- Optional: a destination branch (default: the remote's default branch, found
  in step 3).
- Optional: public repositories the user names as comparable codebases for
  precedent (`references/precedents.md`).

## Steps

1. **Confirm the plan is closed and still true.**
   - *Closed.* Apply `../writing-implementation-plans/references/closure.md`.
     Concretely: the component README (in flat layout, the plan's row in the
     plans index) has a `plan-review:` line naming a final
     review record with no BLOCK; that record's `Plan:` line names this plan; a
     sweep record for the plan exists; and the record reviewed the text you
     hold. Prove the last point in the plan's repo:
     `git status --short -- <plan>` prints nothing, and the integer from
     `git log -1 --format=%ct -- <plan>` is at most the integer from
     `git log -1 --format=%ct -- <record>`. Any non-zero exit or empty output
     counts as a failure. On failure, stop and ask the user for a fresh
     `plan-review` — do not review the plan yourself and carry on.
   - *Still true.* Run `git fetch origin`. Take the pinned head for each repo
     from the plan's `Pinned heads:` line, falling back to the sweep record's,
     and run
     `git -C <repo> diff --stat <pinned> origin/<dest> -- <files the plan cites>`.
     For every cited file that changed, open each cited `file:line` as it is
     at `origin/<dest>`. If the line only moved, keep going and put its new
     location in that step's commit body. If what the step depends on changed
     — a symbol, a signature, a condition, a value — nothing runs: stop as in
     step 5. `closure.md` treats this as a restart trigger.

2. **Inventory the steps before touching code.** For every step write down
   its id, the files it touches, the change, the tests the plan names, and the
   outcome it expects. A step that lacks one of these, or that leaves a choice
   open, is a defect in the plan: stop as in step 5 instead of filling it in.
   Two more checks belong here:
   - *Overrides register.* If the project has one (located per
     `../code-review/references/register.md`), read it. When a step
     prescribes something an entry rejects and the entry states the
     alternative, build the alternative, name the entry in the commit body,
     and list it in the hand-back so the plan can be corrected. When the entry
     gives no alternative, or following it needs a file outside the step or a
     design call, stop as in step 5.
   - *Commands exist.* Each build, test or check command the plan names must
     be defined where it runs — a target or script in the package's build file
     (`package.json` scripts, a `Makefile`, `pyproject.toml`, `build.gradle`,
     or the local equivalent). A command that appears only in a README is a
     plan defect (`plan-review` check 5 rejects it too). Stop before the first step; do not try running it to see.

3. **Start a branch from an up-to-date, clean destination.**
   - Find the destination: `git symbolic-ref --short refs/remotes/origin/HEAD`
     with the `origin/` prefix removed; if that errors, the `HEAD branch:` line
     of `git remote show origin`. A destination the user named overrides both.
   - If `git status --short` is empty and `git branch --show-current` prints
     `<dest>`: `git fetch origin`, `git merge --ff-only origin/<dest>`,
     `git switch -c <branch> <dest>`. Name the branch, in order of preference:
     what the user asked for; the plan's `PR_` id
     (`../writing-implementation-plans/references/naming.md`, "Where ids
     appear"); a kebab-case form of the plan title.
   - If you are already on this plan's branch from an earlier session — clean
     tree, and the existing commit subjects are this plan's step ids in plan
     order — pick up at the first step that has no commit.
   - Anything else (uncommitted changes, a different branch, commits you do
     not recognise): change nothing, stop, and show the user the output of
     `git status --short`, `git branch -vv` and `git stash list`. Someone
     else's work is never stashed, reset, discarded or switched away from.

4. **Build each step in plan order.** For each one:
   1. **Edit.** Make the step's change — as amended by step 2's register rule,
      if one applied — in the step's files and nowhere else. Comments state
      their reason in plain words taken from the plan; they never point at the
      plan or a design doc and never name a person
      (`../refining-technical-writing/references/code-comments.md`, rule C1).
      A constant or guard the plan sets without giving its reason in words is
      a plan defect (step 5).
   2. **Record precedents.** If the edit makes a non-obvious choice — wiring,
      build or packaging configuration, an error's shape, a name, a handler
      chain or similar — find its precedents and add one row per choice to
      `PRECEDENTS.md` as `references/precedents.md` describes. A row whose
      verdict is `differs` and that cites no plan line is a deviation
      (step 5).
   3. **Test.** Run the step's tests exactly as written in the plan, and copy
      the result line verbatim (for example `Tests: 41 passed`). Then run this
      step's rows from the plan's `## Implementer checks`. A failing check
      takes the action its row states; a row with no action, or whose action
      would alter the plan, makes this a deviation.
   4. **Observe it in the real system.** Run the step's `Real-system check:`
      as written and keep the evidence: a screenshot path, a log query with
      its result, a URL with what it displayed. If the check needs tools you do
      not have, can only run after merge, or the step says `first observed in`
      a later step, write its `pending:` line instead (section 2 of
      `real-system-checks.md`). If the user waived it, write a `waived:` line
      quoting them (section 5). Passing build and tests alone never completes
      a step.
   5. **Build.** Run the build command the plan quotes from the package's
      build file. Copy its success line verbatim, plus the log path
      if it prints one.
   6. **Check the comments you are about to commit.** Stage the step's paths
      by name, new files included (`git add -- <paths>`), then run
      `python3 -I ../refining-technical-writing/scripts/extract_comments.py <repo-dir> --staged`:
      - exit 0 — no added comment cites a document or names a person; go on;
      - exit 1 — each printed `<path>:<line>: <kind>: <text>` is a comment to
        rewrite under `code-comments.md` (C1: give the reason in words). Fix
        it, re-stage, and run the script again until it exits 0;
      - exit 2 — the script itself failed (a git or argument error). Report
        its stderr to the user; do not commit as though the check passed.
      If `../refining-technical-writing/` is not installed, say in the step's
      report that the comment check did not run.
   7. **Commit** the staged paths and only those:
      ```bash
      git commit -m "<step id>: <the step's title in the plan>" \
                 -m "Tests: <command> -> <result line>" \
                 -m "Checks: <implementer check> -> <result line>, ..." \
                 -m "Observed: <evidence | pending: <where>, needs <what> | waived: <date>, \"<words>\">" \
                 -m "Build: <command> -> <success line>" -- <paths>
      ```
      Add a body line for each moved citation (step 1) or register entry
      (step 2) the step relied on. Note the commit hash for the report.

5. **Halt when the plan and reality part ways.** Any of these is a deviation:
   an unexpected test or build outcome; a file or symbol that does not match
   the plan's account of it; a step that can only be done by editing a file
   outside its list; command output that contradicts the plan; a
   `differs` precedent with no plan line; a plan defect from steps 1–2. Then:
   - Leave the step uncommitted. The plan is never edited by this skill.
   - Tell the user, decision first: which step; the plan's words, quoted with
     `file:line`; what actually happened, quoted (or the command that shows
     it); the options and what each would cost; your recommendation. You may
     also save that report as `ASK-<step id>.md` beside the plan so it
     outlives the session.
   - Unattended, if the plan marks later steps as independent of this one,
     you may go on with them. First park **only this step's own uncommitted
     edits**: `git stash push -u -m "<step id> deviation" -- <the step's paths>`,
     confirm with `git status --short -- <paths>` that nothing is left, and
     give the stash's message in the report. When no independent step remains, hand back as blocked.

   Correcting your own mistake within the step's files — a typo, a missing
   import — is not a deviation. Fix it and redo 4.3 through 4.6.

6. **Verify the branch and hand it on.** After the last step, build again and
   run the plan's full test command. Check that
   `git log --reverse --format=%s origin/<dest>..HEAD` shows each step id
   exactly once, in plan order. Then give the user the output report and pass
   the branch to `../preparing-code-reviews/` with what it expects as input:
   the branch, the destination as its base, the plan as the spec, the
   `PRECEDENTS.md` path (and the precedent checkouts it lists, if any), and
   this report. That skill rebases, shapes history, writes the description
   (each step's `Observed:` evidence and every `pending:` or `waived:` line
   carried into its testing section, per section 5 of
   `real-system-checks.md`), runs the review loop, and asks before anything
   is pushed. If the user asked to stop at local commits, hand back and name
   `preparing-code-reviews` as the next step instead.

## Pause-for-confirmation rules

- STOP and report at every deviation (step 5) and every failed gate (steps
  1–3). Never route around one.
- PAUSE before any push, pull request, or history rewrite (squash, rebase,
  amending a commit already reported). Those belong to
  `preparing-code-reviews`, which has its own confirmation gate.
- Never stash, reset, discard or switch away from work you did not make.
- Never run a destructive or production-affecting command unless the plan
  states it together with its confirmation gate.
- Never clone a repository from a private or internal host, or one the user
  did not name (`references/precedents.md`).

## Style

- A commit is one step: its paths, nothing else, its evidence in the body.
- Reports copy result lines; they do not paraphrase them.
- A question to the user opens with the decision it needs and then gives the
  evidence.

## Anti-hallucination contract

- A step counts as done only when the report gives its commit hash and that
  commit's body quotes the test, build and implementer-check result lines and
  its `Observed:` line.
- Report only test and build results you ran in this session, quoted.
- The gate claim in step 1 quotes the README's `plan-review:` line and the
  final record's verdict line, with the path of each.
- A re-validation stop quotes the plan's line and the current line at
  `origin/<dest>`, each with `file:line`.
- A deviation report quotes both sides — the plan text with `file:line`, and
  the conflicting output with the command that produced it. A plan-defect
  report quotes the step, with `file:line`, where the missing element should
  have been.
- A step built to a register entry quotes, in its commit body, the step with
  `file:line` and the entry with its register line.
- Every `PRECEDENTS.md` row cites a precedent you opened, at a commit; an
  absence (`no precedent`) names where you searched.

## Output format

```
Plan: <path> @ <hash> — plan-review <final record path>: <verdict>, no BLOCK; sweep <path>
Citations: <N> files checked at origin/<dest> <hash>; <M> moved, none changed in meaning
Branch: <branch> from <dest> @ <hash>
Register: <path read | none declared>
Precedents: <PRECEDENTS.md path, <n> rows | no non-obvious choice>
| step | commit | tests | build | real system |
| <step id> | <hash> | "<result line>" | "<success line>" | "<evidence>" / pending: <where>, needs <what> / waived: <date>, "<words>" |
Result: Blocked at <step id> — <the question> [(ASK-<step id>.md)]
     or Built — handed to preparing-code-reviews (<branch> → <dest>)
```

## What this skill is NOT

- Not a planner: `writing-implementation-plans` writes plans and
  `plan-review` passes them.
- Not a reviewer: `code-review` judges the change, run from
  `preparing-code-reviews`.
- Not PR packaging: rebasing, squashing, describing and publishing belong to
  `preparing-code-reviews`.
- Not deployment: merge, promotion and rollback are elsewhere.
