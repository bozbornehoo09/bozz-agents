Read this when the owner tells you, in your own session, that they are going
or have returned, and for as long as `MANAGER-STATE.md` records an away time.

# While the owner is away

- It starts only when the owner says so *in this session*, never on word
  reported from a worker's session. Then flip each live brief to `Owner: away`,
  record when in `MANAGER-STATE.md`, and check that a watcher is armed.
- A worker already sitting at `WAITING-ON-OWNER` starts no turn on its own,
  so that same turn message each one: "The owner is away: re-read your
  brief's Owner line and continue." For one you stopped at
  `WAITING-ON-OWNER`, start its successor from its handoff with the brief set
  to `Owner: away`. While the owner is
  still here, hand them any paste that is due.
- While they are away, keep `Incidents` in the state file: one line per
  workstream with its latest incident, what you did and a running count
  (stalls, collisions, size caps, failed starts, failed sends).
- When they come back, set `Owner: present` in each live brief and start a
  successor from the handoff of each `RETIRED-BLOCKED` workstream.
- Your first dashboard then is the **morning report**, built from the homes,
  not from memory: worker lines and incidents first, then What to prioritize,
  which also carries the calls decided by debate and the calls parked since
  the away time (their rows in the decisions, open-questions and work-plan
  layers dated after it), the asks drafted, your DECISIONs since then, and
  every owner-go and open owner item, each restated from its home with its
  path. Clear `Incidents` after it.
