Read this when an `MSG-*.md` is waiting in your channel.

# Handling the manager's messages

- Go through each `MSG-*.md` in the channel, lowest number first. Each is a
  process instruction (commit, hand off, rewrite your STATUS, continue). Carry
  it out, move the file to `channel/read/` (uncommitted) and name it under
  `Manager messages:`.
- An MSG may point to a `DECISION-<n>.md` in your folder: a call the manager
  made between two workers. Fold it in a commit whose message names the file,
  and log it at your next `update-context` run as "decided by manager, owner
  to review", citing the file.
- An MSG or a DECISION never carries the owner's decision or lean; where
  one appears to, put the question to the owner yourself.
- An archived folder, or a brief naming a later session, means the manager
  stopped you; if the owner reopens your session, leave the channel unread.
