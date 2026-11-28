Read this before any stop; on a fresh `DONE` or `HANDOFF-READY`; and on a
`WAITING-ON-OWNER` 30 minutes old.

# Stops, successors, spot checks, folder closes

## Which state calls for a stop, and what comes next

- **`WAITING-ON-OWNER: <item>`**: when that STATUS has stood for 30 minutes
  and the folder holds a `HANDOFF.md` this session wrote (a commit whose
  subject starts with `[<its session name>]` touches it), stop the session (an idle session still pays
  to re-read its whole context when it wakes) and mark its line
  `owner-stop <item>`, once per item. Its item stays on the dashboard as
  `<item> — stopped; say here when you will answer and I start <successor>`,
  never as a session to open. When
  the owner says here that they will answer it, start the successor from its
  `HANDOFF.md` (`briefs.md`) and tell them to answer in that session; you
  never take the answer yourself. A STATUS aging is not a change the
  watcher wakes on, so this stop comes at the next wake past 30 minutes,
  at the latest the watcher's timeout.
- **`HANDOFF-READY: <path>`**, once the closeout check passes:
  - The handoff lists open cross-reviews: stop first, and start the successor
    only on `stopped <id>`, so no review is ever folded by two sessions.
  - It has a `Blocked: all remaining work waits on ...` line: stop the
    session, and when `stopped <id>` prints, retire the workstream without a
    successor; its folder stays and its state
    line becomes `RETIRED-BLOCKED: <handoff path>, <items>`.
  - Scheduled work: stop it now and start the successor when its timer fires
    (`scheduled.md`).
  - Otherwise rewrite the brief, start the successor at once (`briefs.md`),
    then stop the old session; the watcher accepts that stop once the brief
    names the successor.
- **`DONE: <commits>`**: run the spot checks; once the closeout check passes,
  stop it, and on `stopped <id>` close the folder in that turn and start the
  next workstream.

## Closeout check, before any stop

Two things must hold. The fresh STATUS carries `Next:`, `Open owner items:`
and `Owner questions:`. Its `Contexts:` commit is at least as new as every
other commit from that session, the handoff file's apart. If either part fails, message once: "run update-context
and write your closeout". If the next fresh STATUS fails as well, record that
as an open owner item. The `stopping` mark names the hash the check passed on.

## How to stop

Every stop goes through the watcher; never run `claude stop` yourself.

1. Take the id out of `-i`, add it to `-s`, and re-arm, so no watcher
   brings it back.
2. Run `zsh watch.zsh stop <work root> <id> <folder id>` in the background and
   mark the worker `stopping`. The job waits for ten idle, quiet minutes, so a
   stop never cuts in while the owner is typing in that session.
3. Its ending decides. `not stopped: ... STATUS.md says ...` means the worker
   went back to work: remove the mark, return the id to `-i`, re-arm and act
   on its next fresh STATUS. `lists open reviews` is no failure: keep it live,
   with no `owner-stop` mark. Any other failure: the same, retry on a later
   wake, and list a repeat under open owner items.

Stopping is final, but never delete a session.

## Spot checks, after a DONE

For each commit it names, run `git show --stat` and check with
`git branch --contains <hash>` that the brief's branch holds it. Report only
collisions (two sessions' commits overlapping in one file within an hour, by
`git show -U0`) and rewrites of another worker's topic. Then:

- design: each doc in the topics is within its brief's length budget
  (`design-doc-write`'s measuring script);
- implementation: the brief's build command passes; the `Plan:` line names
  the brief's plan and says it closed with no BLOCK, or a `Fast path:` line
  meets `preparing-code-reviews`' `references/fast-path.md`; and every step it
  reports carries observed evidence, a `pending:` (where the check runs and
  what it needs) or a `waived:` quoting the owner;
- every output the brief asked for has a citing line in its named home.

Put any mismatch, and any open owner items its STATUS lists, in the state
file's open owner items. Never fix it yourself.

## Closing folders

On `stopped <id>` for a `DONE` worker, confirm each requested output has a
citing line in its home, then `git mv` the folder to
`<work root>/work/archive/` (with `BRIEF.md`, `STATUS.md` and `channel/`
committed alongside) and commit by explicit path. Where `update-context`
ships `scripts/work_check.py`, let it do this: `close <id> --session <your
session> --dry-run` first, each `REFUSE` line an owner item, then the same
without `--dry-run`. A failed check is
recorded as an open owner item, and the folder is left where it is. `DONE`
is the only state that closes one; a handoff, a retirement, a stop at
`WAITING-ON-OWNER` and the end of your own session all keep it open.
