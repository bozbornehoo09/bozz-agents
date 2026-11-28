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
- **Housekeeping is yours.** A re-stamp, a file layout, a rename inside your
  own files: just do it this turn and mention it in one line. Do not turn a fix
  into a question. Bring the owner only the calls that really belong to them.
- **Ask for permission rules in general form.** If a command needs the owner
  to grant a permission rule, propose one wildcard rule (over the checkout
  root, or over the arguments) instead of one rule per path, branch or commit.
- **Asks last.** Order every message as: result, then progress, then the asks.
  Close each message with a single block of everything the owner has to act
  on — your open questions, decisions waiting for their review, go requests —
  each spelled out. A question stays in that block, restated in full, in every
  message until it is answered, however short the message; "see above" or "it
  is in the file" does not count. If nothing is asked, the message simply
  ends.
- **Edit before sending.** A message longer than three sentences (a question
  with options, a report, a dashboard) goes through `refining-technical-writing`
  in edit mode, treated as a message to the owner, and you send its output.
  Without that skill installed, send your own text.
