Read this before writing any MSG or DECISION file; on a watcher diff that
carries an unread MSG, a `WAITING-ON-MANAGER` or `blocker` line,
`ctx <id> over <cap>k` or `respawned <id>`; after the machine restarts; and
when the owner gives a verdict on one of your calls.

# Messaging workers

## What a wake can call for

- **Context.** A `ctx <id> over <cap>k` line means a worker is past its cap
  and the hook did not move it. Send it, once,
  "Your context is past <cap>k: hand off by your contract's Handoff." Skip a
  worker marked `stopping` or whose fresh STATUS is `HANDOFF-READY` or `DONE`.
  Mark it `ctx-msg`, send no second one while the mark stands, and remove
  the mark once that line is gone from the diff. A successor starts unmarked.
- **Restarts.** A machine restart, or a `respawned <id>`, ends every
  background job the session had (watchers, timers, review waits). Tell each
  affected worker to re-arm any wait it had going.

## MSGs

- A process instruction (commit, hand off, rewrite your STATUS, continue) is
  a file `<folder>/channel/MSG-<n>.md`, point first, with a number never used
  before. Write one only after that worker passes the freshness check; the
  exceptions are "rewrite your STATUS" and the context message.
- In launch mode, also deliver it straight away with `SendMessage` to the
  session's name, its first line `Read your channel: <MSG path>`; that starts
  a turn even in an idle session.
- Never stop and resume a worker to deliver a message: a resumed background
  session can come back as a copy under a new id and drop out of the owner's
  view.

## Channel check

Sixty seconds after a send (`sleep 60; echo channel-check` in the
background), and on each wake for as long as any MSG sits unread: if a worker
is idle and an MSG over a minute old is still in its `channel/` (not
`channel/read/`), it never began a turn.
Mark it `paste`, send it nothing more until its messages are read, and make
its item, and your one line to the owner, `type "read your channel" — open <session>`.

## Lifting a sibling block

A waiter that reported `WAITING-ON-MANAGER: <session> in <file> <section>`
has ended its turn. The watcher's diff carries the blocking worker's
`Doing now:` line and a `blocker <file> clean|dirty` line. While the blocker
has uncommitted edits in the file, ask it to commit. Once three things hold
(the file is clean, the waiter is idle, and the blocker's `Doing now:`
mentions neither that section nor a review pass over the file) send the
waiter "the block has cleared; continue".

## Calls between workers

- A call that involves no owner decision is yours: which of two plans builds
  a shared piece, which worker goes first. Record it as `DECISION-<n>.md`,
  committed where the worker whose work changes keeps its folder: one
  sentence stating the call, then what you decided, then the evidence as `file:line` from files you
  read, with anything you did not see marked unverified. Send an MSG naming it
  to every worker it affects and tell the owner in one line.
- In the same commit, add an owner item citing it, marked "decided by
  manager, owner to review", and list it under the state file's manager calls
  to review.
- Never write a DECISION that states, implies or applies an owner decision or
  lean; escalate those to the owner, each lean labelled as `owner-talk.md`
  says.
- A manager call stays open until a work-tracker line cites its DECISION and
  quotes the owner's verdict; write that line when the owner gives one.
