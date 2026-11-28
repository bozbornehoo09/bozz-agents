---
name: preparing-code-reviews
description: Turn a finished branch into one clean, reviewable pull request. Use when implementing-a-plan hands over a built branch, when a small settled change qualifies for the fast path, or when the user says "prepare the PR", "squash and open a PR", "clean up this branch for review", or "address the PR comments". Finds the base branch, rebases, runs the project's checks, shapes the history (one squashed commit or a short logical series), writes the PR description, runs code-review as a review-challenge-defense loop and folds what survives, then pushes and opens the PR with gh only once the user says go.
---

# Preparing Code Reviews

The output is **one pull request a reviewer can follow without any other
context**: rebased on the current base, with history shaped on purpose,
passing the project's checks, described so each change carries its reason,
and already through an independent review whose surviving findings are
folded in. Nothing leaves the machine until the user explicitly approves.

## Scope

In scope:
- The branch's history and commit message(s), and the PR description file.
- Running the project's own checks, and `../code-review/` via the review loop.
- Pushing the branch and opening or updating its PR with `gh` — **only after
  the user's go** (Pause-for-confirmation rules).
- Folding review findings and reviewer comments back into the branch.

Out of scope:
- Building a plan's steps → `../implementing-a-plan/`, which hands its branch
  here.
- Writing a plan → `../writing-implementation-plans/`.
- What counts as a defect → `../code-review/` and its briefs.
- Merge, release, deploy, rollback.

Bundled files:
- `references/pr-description.md` — the description standard and its checks.
- `references/fast-path.md` — who qualifies for the light route, and how it
  runs.
- `scripts/review-loop.sh` — one review → challenge → defense loop over the
  branch, driven by `code-review`'s briefs (tests:
  `scripts/test_review_loop.py`).

**Inputs.** The branch (default: the current one). The spec it implements —
the plan, else the issue or design doc, else the user's request. From
`implementing-a-plan`, when it ran: its output report and the
`PRECEDENTS.md` it kept (format: `../implementing-a-plan/references/precedents.md`),
whose `Checkouts:` line lists any local precedent clones. A base branch, if
the user or the project names one. For an update, the open PR.

## Steps

### 1. Preconditions

Stop and report at the first one that fails.

- **Project rules win.** Read the repo's contribution guidance
  (`CONTRIBUTING.md`, `AGENTS.md` or `CLAUDE.md`, `.github/`) for the base
  branch, branch naming, history policy (squash, rebase or merge commits),
  commit message format and required checks. Where it disagrees with a step
  here, follow it.
- **Clean tree:** `git status --short` is empty.
- **Base branch, found rather than guessed** — unless the user or the project
  rules name a different one (a release branch, or the parent of a stacked
  PR):

  ```bash
  git fetch origin
  BASE=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD)       # e.g. origin/main
  [ -n "$BASE" ] || { git remote set-head origin --auto >/dev/null && BASE=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD); }
  [ -n "$BASE" ] || BASE="origin/$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)"
  ```

  If none of the three yields a value, ask. Never write `main` or `master` in
  by hand.
- **A real work branch:** `git branch --show-current` is non-empty (HEAD is
  not detached) and differs from the base's name.
- **Something to review:** `git log --format='%h %an %s' "$BASE"..HEAD` lists
  at least one commit. If any listed commit was made by someone other than the
  user or this session's work (an `implementing-a-plan` run counts as the
  user's), ask before any step rewrites it.
- **Existing PR?** `gh pr view --json number,url,state,baseRefName,isDraft`
  (an error means there is none). An open PR turns this into an **update
  cycle**: its base must equal `$BASE`, and step 8 edits it rather than
  creating a new one.
- **gh works:** `gh auth status` succeeds. It is first needed at step 8, but
  a failure is cheaper to learn now than after the review.

### 2. Rebase

```bash
git rev-parse HEAD                        # the undo point; it goes in the report
git rebase "$BASE"
```

Resolve a conflict yourself only when the spec or the base's own change makes
the right result clear. Otherwise run `git rebase --abort` and ask.

### 3. Project checks

Run the build, lint and tests the project documents (contribution guidance,
`Makefile`, `package.json` scripts, CI workflow files). For each, keep the
command and its summary line; they become the description's `Automated:`
line. A failing check sends you back to fix the code, not to explain the
failure. The one exception is a failure that already exists on the base —
shown by the failing file being absent from
`git diff --name-only "$BASE"...HEAD` **and** the same check failing in a
throwaway `git worktree add <tmp> "$BASE"` (remove it afterwards). Such a
failure is reported in the description as pre-existing.

### 4. Draft the description

Write it to a file **outside the tracked tree** — the project's agent working
folder if there is one, else a temp file; `<desc>` below — following
`references/pr-description.md` for layout, content and checks. Work from the
spec, the diff (`git diff "$BASE"...HEAD`), the implementer's report, and
`PRECEDENTS.md` when present (the standard's `Follows:` line says how to use
it). Leave `Pre-flight review: pending` until step 6. If
`../refining-technical-writing/` is installed, run it on `<desc>` in edit mode
first, with the instruction to keep every testing claim, figure and link.
Then run the standard's **Checks** and correct each miss.

In an update cycle, start from the PR's current body (`gh pr view --json
body`), so edits the user made on the web survive.

### 5. Shape the history

Before rewriting anything, say in your reply which shape you chose and what
decided it.

- **One squashed commit (default),** unless project rules or the user ask for
  something else:
  ```bash
  git reset --soft "$BASE"
  git commit -F <commit-msg>                # title plus the description's What and why and What changed
  git rev-list --count "$BASE"..HEAD        # expect 1
  ```
- **A short logical series,** when the project or the user wants it, or the
  change is truly several independent pieces a reviewer is better off reading
  apart. Each commit must build and pass tests alone and carry its own
  message. Tidy without an interactive editor: `git commit --fixup=<sha>`,
  then `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash "$BASE"`.

Either way only history changes, not the tree. `git reset --hard <undo point>`
from step 2 restores the branch as it was.

### 6. Pre-flight review loop

The two standards are **simplicity and correctness**. Run at most **three
loops** per cycle, and stop at the first loop that leaves no real BLOCK. A
fast-path change replaces this step with the single pass in
`references/fast-path.md`.

A loop is one run of `scripts/review-loop.sh`. Every stage there is a fresh,
read-only reviewer session: first one reviewer per `code-review` specialist
brief, all in parallel; then a **challenger** that attacks each finding
against the code; then a **defense** in which the reviewers strengthen or
concede each finding and close with `code-review`'s `Verdict:` line.

```bash
DECISIONS="<ADRs and decision files>" DECLINED="<earlier loops' DECLINED.md>" \
REGISTER="<overrides register, if the project has one>" \
  bash <this skill>/scripts/review-loop.sh <loop-dir> <repo> "$BASE" <desc> <spec|-> [<precedent checkout>...]
```

- `<loop-dir>`: a new folder for every loop, outside the tracked tree
  (`<working folder>/reviews/<date>-<branch>-<N>/`, with `<N>` counting loops
  across all cycles). A loop can take many minutes; run it in the background
  if the host supports that. Exit 2 means an input is missing or wrong — fix
  it. Exit 1 means a session failed twice — stop and ask. Neither counts
  toward the three loops.
- The default reviewer is `claude -p` limited to read-only tools. Another
  host's non-interactive agent goes in `REVIEW_CMD` (for example
  `REVIEW_CMD="codex exec --sandbox read-only"`). If `code-review` has no real
  briefs yet (only `_brief-template.md`), the script exits 2: add briefs (see
  `../code-review/SKILL.md`), or run `code-review` once yourself and write
  `Pre-flight review: one pass, no specialist briefs`.
- Precedent checkouts: the local directories on `PRECEDENTS.md`'s
  `Checkouts:` line, if they still exist (re-clone a public one at the
  recorded commit if not); with `Checkouts: none` or no record, pass none —
  the precedents lens then judges only this repository.

**Verifying.** A loop counts as a `code-review` pass only once `3-final.md`
has been through `../code-review/SKILL.md` Orchestration steps 3–6: every BLOCK
quote re-read byte-for-byte at its `file:line` (both ends of a
cross-reference, and for an `OV-<n>` the register Rule), the FIX and SUGGEST
sample, the merge, and the verdict recomputed by that rule — not taken from
the defense's `Verdict:` line. Log each finding dropped there in the loop
folder's `DROPPED.md`. Confirm that each BLOCK and FIX the defense withdrew or
lowered was conceded on evidence, and reinstate any that was not.

**Folding.** Findings are hypotheses, not orders
(`../fold-review-findings/SKILL.md`: verify first, edit second). Fold every
real finding into the branch — amend the squashed commit, or add a
fixup commit in series mode — update `<desc>` if the fold changes what it
says, rerun the step 3 checks, and start the next loop. A finding you decline
goes into the loop folder's `DECLINED.md` with severity, `file:line`, quote and
reason, so later loops leave it alone. A **PLAN** finding (the code matches
the spec, and the spec is what is wrong) is folded as well, with a note for
the spec's owner; if it needs a design decision, stop for the user.

**When to stop.** At the first loop with no real BLOCK, fold its real FIXes
without running another loop, then fill in `Pre-flight review:` (loop count,
final `Verdict:` line, each declined BLOCK and why, FIXes folded after the
last loop and so unreviewed). Stop and ask the user instead when a loop
produces **more** real BLOCKs than the previous one, brings back a BLOCK the
previous fold was supposed to resolve, or the third loop still has one — and
say whether you think the approach itself should change.

### 7. Confirm with the user

Show this before anything is pushed:

```
About to publish: <branch> → <base> (<new PR | update #<n>>)
History: <1 squashed commit <sha> | <n> logical commits>; undo point <sha>
Checks: <summary lines>
Review: <the Pre-flight review: line>
Title: <title>
Description: <desc path> (checks: all pass | <misses>)
Commands: git push <-u | --force-with-lease> origin <branch>; gh pr <create --draft | edit> …
Open as draft, or ready for review?
```

Wait for an explicit go. If anything changes after it (another fold, a
rebase), ask again.

### 8. Push and open — after the go

```bash
git status --short                                         # must be empty
git push -u origin <branch>                                # first push
git push --force-with-lease origin <branch>                # history rewritten since the last push
gh pr create --base "${BASE#origin/}" --head <branch> --title "<title>" --body-file <desc> [--draft]
gh pr edit <n> --title "<title>" --body-file <desc>        # update cycle
```

`--force-with-lease`, never `--force`. Open as `--draft` unless the user chose
ready for review.

### 9. Read it back

`gh pr view --json url,number,state,isDraft,baseRefName,headRefOid,commits,body`,
then confirm:
- `headRefOid` is `git rev-parse HEAD`, and `baseRefName` is the base;
- `commits` has the chosen shape (one commit, or the series);
- the live `body` passes the **Checks** in `references/pr-description.md` —
  any miss fails the read-back and is reported by name;
- `gh pr checks <n>` gives the CI status; a pending run is checked again
  later.

Call the PR ready only once this passes.

### 10. Respond to feedback (a later cycle)

Collect every comment: `gh pr view <n> --comments`, plus
`gh api repos/{owner}/{repo}/pulls/<n>/comments` for line comments. Each one
is either folded as a commit or declined with a reason. Then go round again
from step 2 — rebase, refresh the description, reshape history, rerun checks
and the review loop, confirm, push, read back. Draft one reply per comment
(what changed and where, or why not), quoting the comment, in a file next to
`<desc>`. **Do not post replies** until the user says go.

## Pause-for-confirmation rules

- **No push, PR creation or update, ready-for-review, merge or PR comment**
  without the user's explicit go in this conversation, given after the step 7
  summary. A go never carries over to a later change.
- **Ask before rewriting** commits that are neither the user's nor this
  session's.
- **Ask on a rebase conflict** the spec does not settle, after aborting the
  rebase.
- **Announce the history shape** (squash or series) and its source before
  step 5 runs; ask when neither the project nor the user decides it and both
  shapes are reasonable.
- **Ask before force-pushing** a branch others may have fetched (a PR with
  outside commits, or suggestions applied on the web).
- **Stop and ask** on any step 6 stop condition, on a PLAN finding that needs
  a design decision, or whenever a step's output is not what it expects (an
  unexpected commit count, a read-back mismatch). No workarounds.

## Style

- Write the description for a reader with no context: plain words, no plan
  ids, a reason for every change, descriptive text for every link.
- Back every claim: a check result quotes its summary line; a review claim
  quotes the final loop's `COUNTS` and `Verdict:` lines and names the
  `3-final.md` path; "done" quotes the read-back.
- Loop folders and description and reply drafts never enter the PR's diff.
- Stage by explicit path; never `git add -A` while folding review findings.

## Output format

```
# Preparing Code Reviews: <branch> → <base>

PR: <url | not opened: <why>> (<draft | ready>; <new | updated>)
Base: <base> (from <origin/HEAD | gh | project rules | user>)
History: <squash: 1 commit <sha> | series: <n> commits>; undo point <sha>
Checks: "<summary line>" (<command>) …; pre-existing failures: <file:line or none>
Review loop: <n> loop(s); "<final COUNTS line>" "<Verdict: line>" (<3-final.md path>);
  folded after the final loop (unreviewed): <finding → file:line, or none>;
  declined: <finding → reason, or none>; dropped (quote not found): <n>
  | Fast path: <tests met>; single pass: <COUNTS line | own read>; fixed: <n>
Description: <desc path>; checks: <all pass | misses by name>
Read-back: head <sha> = HEAD; base <name>; commits <n>; body checks <pass | misses>; CI <status>
Left for the user: <publish, mark ready, merge, post replies, or none>
```

## What this skill is NOT

- **Not a reviewer.** `code-review` and its briefs decide what is wrong; this
  skill runs them and folds what holds up.
- **Not plan execution.** `implementing-a-plan` builds the change; this skill
  packages it.
- **Not a merge bot.** Merge, release and rollback stay with the user.
- **Not a publisher on its own authority.** Nothing is pushed, opened or
  posted without the user's go.
