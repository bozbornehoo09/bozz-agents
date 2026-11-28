## How to write for the owner

Any role that loads this file follows it in everything the owner will read:
replies, questions, dashboards, reports, and the owner items listed in a
STATUS file.

- **Say what the thing is.** Use the real name of the queue, function, issue
  or release phase. Plan nicknames, section labels, milestone codes and step
  numbers mean nothing to someone who has not just read the plan. If a
  question turns on a field or a term of art, define it in a clause first.
  One question asks one thing. The owner should be able to follow you without
  a glossary.
- **Cause before scenario.** To explain a problem or a risk, start with the
  mechanism that produces it, then the harm, then the conditions under which
  it happens. Do not open with a story of it happening.
- **Use the owner's time zone.** Tools usually log in UTC and the owner may
  live elsewhere. Times you show the owner are in their zone, taken from the
  brief's `Owner time zone:` line, or the project orientation file, or by
  asking once. Records stay in UTC.
- **Name sessions as the owner sees them.** Point the owner at a session by
  the name the agent view lists, so they can open it there.
- **Housekeeping is yours.** A re-stamp, a file layout, a rename inside your
  own files: just do it this turn and mention it in one line. Do not turn a fix
  into a question. Bring the owner only the calls that really belong to them.
- **Ask for permission rules in general form.** If a command needs the owner
  to grant a permission rule, propose one wildcard rule (over the checkout
  root, or over the arguments) instead of one rule per path, branch or commit.
- **Asks last.** Order every message as: the answer to the owner's question
  (or the result), then progress, then the asks. Close each message with a
  single block of everything the owner has to act on (open questions,
  decisions waiting for their review, go requests), anything with a deadline
  first, with the deadline in their zone. Spell each ask out in full the first
  time; in every later message restate it in one line until it is answered.
  It never disappears into "see above", a file or a STATUS line alone. A call
  you stop on for the manager (`WAITING-ON-MANAGER`) closes your message the
  same way, options and lean in full, because the owner reads your session
  too. If nothing is asked, the message simply ends.
- **Label every lean.** Wherever you write a lean (a message, a dashboard, a
  STATUS item, an ask file, a decision row), label it
  `Lean (<session name>, <model>): ...`, so the owner sees who judged the call
  and on what model. A restated lean keeps its label; one copied from a record
  without a label gets the session that record names and `model not stated`; a
  subagent's lean you pass on without adopting names that subagent and its
  model. Leans come from the strongest tier (opus). A sonnet session leans
  only on a very simple call (easy to undo, with one option that the plan or
  standard practice already picks); otherwise it writes
  `No lean (<session name>, sonnet)`. A haiku lean is never given or passed on.
- **Edit before sending.** A message longer than three sentences (a question
  with options, a report, a dashboard beyond a header and one worker line)
  goes through `refining-technical-writing` in edit mode, treated as a message
  to the owner, and you send its output. Short status lines skip it. Without
  that skill installed, send your own text.
