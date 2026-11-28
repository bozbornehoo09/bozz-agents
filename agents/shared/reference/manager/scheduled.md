Read this when the owner sets work for a time, when a `due:` line prints, and
at session start when the state file has a `scheduled` mark.

# Scheduled work

Work set for a time ("rerun the flaky-test sweep at 6am") runs in a fresh
worker started then, with fresh tools and context.

- Convert the time to UTC with the owner's zone and write
  `scheduled <UTC time>` on the workstream's state line.
- Timer, in the background with a timeout longer than the wait:
  `wait_s=$(( $(date -u -d '<UTC time>' +%s) - $(date -u +%s) )) && sleep "$wait_s" && echo "due: <workstream> at <UTC time>"`
  (on BSD `date`, parse with `-j -f`). Set it again if it ends without
  printing.
- When it fires, tell any live session on that workstream to hand off. When
  none is live, write a brief whose first step is the scheduled work and
  launch it.
- If the owner says stop before it fires, tell them in one line that it will
  not run at their time unless they withdraw the stop, and carry it, with its
  UTC time, into `NEXT-SESSION-PROMPT.md`; the next manager sets the timer
  again, or starts the work at once if the time has passed.
- If the host offers cloud scheduled tasks, mention once that the owner may
  prefer one.
