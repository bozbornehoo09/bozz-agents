Read this before each `update-context` run, before writing `HANDOFF.md` (a
handoff, or a `WAITING-ON-OWNER`) and before `DONE`.

# Closeout: update-context, handoff and DONE

## Each update-context run

- Where no size-cap hook runs, measure first (`ctxpct.sh -k`, the contract's
  "Context budget"). A manager message about your context since the last run
  counts as the measurement.
- Every owner question from this session that the work tracker lacks goes
  into the session's entry there, with the answer you gave.
- One worker at a time, under a lock. `mkdir <work root>/.update-context.lock`
  either creates it or fails because someone holds it. Once it succeeds, write
  your session name and the UTC time to a file `owner` inside it. If it fails,
  wait in a single background call that returns as soon as the `mkdir` works
  or the `owner` file passes 30 minutes of age. At that age the lock is
  stale: leave it in place and report
  `WAITING-ON-OWNER: stale update-context lock`.
- While you hold it: STATUS reads `WORKING: update-context`; run the skill;
  commit the layer files it changed by explicit path; release with
  `rm <lock>/owner && rmdir <lock>`; restore your STATUS.

## Closeout

At `HANDOFF-READY` or `DONE` your STATUS block is your **closeout**: write it
after an `update-context` run that comes later than all your other commits
apart from the handoff file. A question the owner asks after that is logged
with another run, and `Owner questions:` rewritten. If the owner reopens you
after the manager stopped you (your folder is archived, or the brief names a
later session), answer and record as usual, but read no channel and write no
STATUS.

## Handoff

1. Run `update-context` first, so each result reaches its home while you
   still hold it.
2. Write and commit `HANDOFF.md`, 40 lines at most: the goal; the mode; what
   is finished; the commits; each result not yet in its home, with that home;
   the folder's records the next step must keep in step; open owner items;
   the next step; the limits; for an open review loop, its pass number and
   its last real BLOCK count; an `Open reviews:` line naming each open
   cross-review file (or `none`); any `Tools down:` line; any
   `Go needed again:` line.
3. Where `update-context` ships `scripts/work_check.py`, run its
   `handoff <id>` until it prints `OK`, so every result is either cited by a
   home or named in `HANDOFF.md`.
4. Report `HANDOFF-READY: <path>` with your closeout. The manager stops you
   and starts the successor from that file.

A requester with an open cross-review first folds the reviews that have
completed; its successor starts by going back to waiting on the files its
`Open reviews:` line names.

**At `WAITING-ON-OWNER`**, do the same in that turn (for a stale lock, skip
`update-context` and name each result not yet in its home in `HANDOFF.md`; for
a blocked checkout, leave out whatever the block rules out), then hold that
STATUS. Should the manager stop you once it is half an hour old, the
successor it starts from your handoff is the one that hears the owner's
answer.

## DONE

Report `DONE: <commits>` with your closeout once every output the brief asks
for has its citing line in its home. The manager stops you and closes the
folder; a handoff moves nothing.
