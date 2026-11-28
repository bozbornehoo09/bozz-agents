Read this once the owner tells you to stop, and whenever you are about to
write `NEXT-SESSION-PROMPT.md` (closing down, or handing off at your cap).

# Closing a session

## After the owner's stop

1. No successor and no new workstream starts from that moment.
2. Send each live worker not at a fresh `HANDOFF-READY` or `DONE`: "hand off
   by your contract's Handoff, with update-context and your closeout."
3. Wait for every live STATUS to be a fresh `HANDOFF-READY` or `DONE`. For a
   start that failed, record its goal, topics and first step as an open
   workstream in `NEXT-SESSION-PROMPT.md`.
4. Route every stop through the watcher (`stopping.md`).
5. Once every stop has printed `stopped <id>`, run `update-context` for
   whatever no worker recorded.
6. Write `NEXT-SESSION-PROMPT.md`, then commit it together with
   `MANAGER-STATE.md`.

## NEXT-SESSION-PROMPT.md

Build it from the state file: the open workstreams with their folders and
handoff paths; the open owner items; the limits; any go the owner must give
again; any scheduled work with its UTC time; and the last dashboard's graph
and tables stamped with their UTC read time, which your successor re-reads
from source before showing. At a size-cap handoff the live workers keep
running: say so, and point the successor at `MANAGER-STATE.md`, which it
adopts as it stands.
