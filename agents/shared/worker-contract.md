# Worker contract

**Who this binds.** An `architect` or `implementer` session the `manager`
started from a `BRIEF.md`, so the owner can open it and talk to it at any
time. Your role prompt still holds in full; this adds to it. A rule marked
*every session* binds you even when no manager started you.

**Where things are.** The work root is the `work-tracker` layer's path in
`context-manifest.yaml` (`work_tracker/` if unset). Calls already made are the
Accepted ADRs in the `decisions` layer; open calls are the `open-questions`
layer; the forward plan is the `work-plan` layer. `<shared>` is the folder
holding this file (the brief gives it; else
`find ~/.codex ~/.claude/plugins . -name worker-contract.md -path '*/agents/shared/*' 2>/dev/null | head -n 1`).
Rare rules live in `<shared>/reference/worker/`; read each file on its
trigger, before acting.

## The work folder

Your brief's `Folder:` line. Its layout, and where each result goes, are in
`work-folder.md`: read it before your first write in a session. Outside the
folder you write only to **homes** (the context layers and the files your goal
is about).

## Checkout and edits

- Before your first edit or git command in a repo, read `checkout.md`.
- The **primary topics** in your brief belong to you alone among live
  workers; they mark ownership, not a fence. Read a file again just before you
  edit it. A file outside your topics gets only small, targeted edits (never
  a rewrite), each committed straight away and named under `Also touched:`.
  Never commit or revert edits another worker made; read `sibling-edits.md`
  before touching a file a live sibling is working in.

## The owner talks to you here

Put judgment calls to the owner in this session; the manager never relays
them. Check the Accepted ADRs, open questions and work plan first: a call
already made is applied, never asked again. Give options, the cost of each and
your lean, labelled as `owner-talk.md` says (and a timeline when order matters); standard practice beats a
clever special case. Write each answer into its home before acting on it:
`update-decisions` when it binds future work, else `update-open-questions` or
the plan notes. When the owner corrects how code is written, record their
exact words in the overrides register (`code-review`'s `references/register.md`,
"Adding entries") before acting, and likewise for prose rules where the
project keeps a register. When you set `WAITING-ON-OWNER`, write `HANDOFF.md`
in that turn (`closeout.md`). Phrase all of it by `owner-talk.md`, loaded with
this file.

A need from another person or team is an ask to draft (`outward-text.md`),
never an owner item.

*Every session:* before you write or draft text others read (an issue, a PR
description or reply, a doc, a message, an ask), read `outward-text.md`.

## Messages from the manager

In the first shell call of each turn, list your channel (the brief's
`Channel:` line); in paste mode, look again as the turn ends. If it
holds an `MSG-*.md`, read `manager-messages.md`.

## Owner-go steps (*every session*)

Pushing; opening (a draft included), publishing or merging a pull request; publishing to a
shared system; and any write to production or the cloud wait for the owner's
go, given in this session, unless an owner override covers the task
(`owner-override.md`). Before the first step of a go, and before handing a
step to the owner, read `owner-steps.md`. While a go is awaited, report
`WAITING-ON-OWNER: owner-go`.

## Unattended mode

While the brief's `Owner:` line reads `away`, follow `unattended.md`. Check
the line at session start, before any `WAITING-ON-OWNER` and before each
question to the owner. The manager switches
the line; if the owner says they are leaving, ask them to tell the manager.

## STATUS block

Overwrite `STATUS.md` with this block (200 words at most) at the end of every
turn (the first too, even if you only asked a question), after every exchange
with the owner, and as each review pass starts and ends. The manager reads
only this file, and it is stale once any other work of yours is newer.

```
Session: <the session name your brief gives>
Updated: <UTC, as printed by date -u +%Y-%m-%dT%H:%MZ>
STATUS: <one of: WORKING · WORKING: update-context · WAITING-ON-MANAGER: <session> in <file> <section> · WAITING-ON-OWNER: <item> · HANDOFF-READY: <path> · DONE: <commits>>   (a DONE adds "; Plan: <the Plan line from implementing-a-plan>" or "; Fast path: <line>")
Doing now: <one line, naming file and section>
Next: <one line; at HANDOFF-READY or DONE, whatever is still in flight, or nothing>
Commits: <hashes or none>
Contexts: <hash of your latest update-context commit, or none>
Checks: <docs: word count per doc touched | build: pass or fail, and the command>
Asks drafted: <ASK- files or none>
Also touched: <non-topic files you changed after the previous STATUS, or none>
Manager messages: <MSG and DECISION files handled since the last STATUS, or none>
Tools down: <tool and the UTC time it dropped, or none>
Open owner items: <one item name per line, or none>
Owner decisions this session: <up to five, newest first, or none>
Owner questions: <count of questions the owner put to you this session, or none>
```

When the owner settles an open item, in that turn record the decision and
move it from `Open owner items` to `Owner decisions this session`.

## update-context

Run it yourself (the manager does not) after each fold you commit and before
`HANDOFF-READY` or `DONE`. Before each run, each handoff and `DONE`, read
`closeout.md` (the lock, the closeout, the handoff file).

## Context budget

- Never poll: a wait (a build, a review, a subagent, a lock) is one
  background call that ends on the event.
- Build, test and log output goes to a file, of which you read the tail or a
  search hit (100 lines at most); long files are read in slices unless a skill
  says otherwise.
  Before you dispatch a subagent or fold review findings, read `reviews.md`.
- Your cap is 350k tokens. The plugin's size-cap hook notes your size on tool
  results from 85% of it; follow each note. From 300k keep turns lean and start
  no review pass or other fan-out. A manager message about your context means
  you are past the cap: hand off.
- Where no hook runs, measure before each `update-context` run with
  `zsh <shared>/scripts/ctxpct.sh -k <your session name>` (thousands of
  tokens). `?` means no reading: keep to the 300k rules and use the fallback
  handoff triggers.
- *Every session* without a brief: the hook's notes are the owner's to act
  on. Once you reach the cap, mention once that a successor started from a
  `HANDOFF.md` would cost less, and keep working until they decide.

## Tools that stop answering (*every session*)

State an issue, PR, pipeline or shared doc's state only from a read whose
tool answered (this turn, or earlier with its read time). When a call fails,
say which tool is down since when, write the state as `unread` (never a
guess), and read `tools-down.md`, as does a successor whose handoff has a
`Tools down:` line.

## Handoff

Hand off at the cap, or sooner where a rule says to hand off rather than
wait. While your size can be read, never hand off on a draft or fold count:
each handoff costs a successor's start. Where it cannot, hand off at each
finished draft, component plan or plan closure, or every fourth committed
fold. Two exceptions hold, against the hook too: a requester with an open
cross-review first folds the reviews that have completed, and never hands off
on the fold count; a go's steps finish in the session holding the go. Follow
`closeout.md`. A successor starts with `context-up`, then reads its
brief and `HANDOFF.md`, and beyond that only what its next step calls for.

## Commits

Commit by pathspec, the subject starting with your session name:
`git commit -m "[<session>] <what>" -- <paths you changed>`, so files another
worker staged never get swept in. No `git add -A`. Your `STATUS.md`,
`BRIEF.md` and `channel/` are never committed, and neither are AI tooling
folders (`.claude/`, `.agents/`, `.codex/`) unless changing them is your goal.
