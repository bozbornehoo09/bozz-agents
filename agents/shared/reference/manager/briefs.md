Read this before dividing work into workstreams, before writing a `BRIEF.md`
or rewriting one, and before any launch.

# Workstreams, briefs and launches

## Dividing the work

- Each workstream has a single goal, the files that goal is about (its
  primary topics) and exactly one worker. Give
  each a short lowercase name; no name contains another, ends in `-<digits>`
  or is `manager` (managers are `<project>-manager-<n>`).
- **A file has one live owner.** No primary file is shared between two live
  workers; goals that need the same file run in sequence.
- Implementation splits by repository or package checkout: one implementer
  per checkout, never two.

## The brief

Make `<work root>/work/<YYYY-MM-DD>-<workstream>/` (add `-2` if that id is
taken) and write `BRIEF.md` there, 40 lines at most. A successor reuses the
folder. The brief holds:

- `Session: <project>-<workstream>` on its own line (the watcher reads it);
  successors append `-2`, `-3` and so on.
- The checkout's absolute path, the branch to commit on, and the project's
  branch rules file if there is one (named, not restated).
- The goal, first, as the user experience it serves (what someone can do or
  see once it is done), and only then the mechanism.
- The mode (design or implementation) and the role (`architect` or
  `implementer`).
- The primary topics, always including the folder's `HANDOFF.md`.
- Design: the length budget of each doc it touches. Implementation: the build
  and test command, the plan's path, and each step's real-system check
  (`plan-review`'s `references/real-system-checks.md`), or the fast-path line
  when the change takes `preparing-code-reviews`' fast path.
- The first step.
- A home for every output it asks for. A brief that asks for a result without
  naming its home is not finished.
- For design or plan work, the decisions layer as the record of calls in
  force; for writing or building a plan, the plan's path in the plan tree
  (`writing-implementation-plans`, `references/plan-tree.md`).
- The session's limits. For an owner-go workstream,
  `Owner-go steps (one go covers all; a production step is still confirmed on its own): <steps in order, exact targets>`.
- `Owner: present` or `Owner: away`, and `Owner time zone: <zone>`.
- These six lines exactly, paths filled in:

```
Role contract: you work for the manager; follow <shared>/worker-contract.md.
update-context: you run it yourself, holding the contract's lock.
Folder: <absolute work folder path>/
Channel: <absolute work folder path>/channel/
Context: keep to the contract's "Context budget".
Handoff: when the contract's "Handoff" says.
```

## A successor's brief

- Rewrite `BRIEF.md` with the next session name, the same topics, the six
  lines and "Read <handoff path> first". If the old worker left work off the
  brief's branch or uncommitted (check `git worktree list`, `git status
  --short` and `git branch --no-merged <brief branch>`), its first step brings
  that work onto the branch.
- After a stop at `WAITING-ON-OWNER`, the new brief's first step is that
  item, which the owner answers in the new session. An `owner-go` item is
  carried as the brief's `Owner-go steps`; the go itself never is.
- A handoff with a `Go needed again:` line makes those steps the new brief's
  `Owner-go steps`, and you tell the owner the new session needs their go
  afresh, in its own session.
- Launch it as below, then tell the owner the name of the session now
  running.

## Before a launch

- **Shared checkout.** Before the first launch, make sure background sessions
  run in the shared checkout, not a private worktree: in Claude Code,
  `worktree.bgIsolation` is `none` at user level, with no other value in the
  launch folder's project settings. If not, ask the owner once to set it and
  launch nothing until it is set; a worker in its own worktree writes a STATUS
  you never see.
- Before an implementation wave, confirm each plan gives a real-system check
  for its steps; if one does not, tell the owner before launching.

## Launching

1. **Reserve first.** Replace the folder's `STATUS.md` with
   `STATUS: STARTING` and `Session: <name>`, and enter the worker in the state
   file (session name, workstream, topics, brief), so a quick first turn is
   never overwritten.
2. **Launch** from a folder the owner trusts:
   `claude --bg --effort high --name <session> --agent bozz-agents:architect "Run <absolute brief path>"`
   (`bozz-agents:implementer` for implementation). Workers run at high effort
   and on the default five-minute prompt cache: they call without long gaps,
   so a one-hour cache would only raise what they pay to write it. The owner's
   own effort setting applies to you and to sessions they start themselves.
3. Add the session's id and session id from `claude agents --json` (`.id`,
   `.sessionId`) to its state line; `claude stop` takes the id.
4. Put the id in `-i`, re-arm, and show the dashboard.

## After a launch

While its STATUS reads `STARTING`, do nothing unless the agent list lacks the
session: then show "failed start" with the command to rerun it. If the list
shows it busy or idle while STATUS still says `STARTING`, look for its STATUS
and commits in other checkouts (`git worktree list`) and report what you find
on its line.
