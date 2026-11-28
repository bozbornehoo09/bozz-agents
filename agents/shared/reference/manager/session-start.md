Read this when a manager session begins, straight after the claim.

# Opening a session

1. **Which mode.** Run `claude agents --json` once. If it answers, you are in
   *launch mode*: you start and message workers yourself. If there is no
   `claude` command or it has no agent view, read `paste-mode.md`.
2. **What is already there.** Run `context-up` for the project. Read
   `NEXT-SESSION-PROMPT.md` and `MANAGER-STATE.md` in the work root (create
   the state file if it is missing) and the work plan's next-up block. A
   predecessor that handed off to you left its live workers running: adopt
   its state file as it stands.
3. **Restart what died with the last manager.** Arm your watcher from the
   state file's lists, re-run the stop of every worker marked `stopping`
   (`stopping.md`), and re-arm each `scheduled` timer (or, where its time is already past,
   launch that work now; `scheduled.md`).
4. **Orphan folders.** Count the folders in `<work root>/work/` that the
   state file does not list as live and `NEXT-SESSION-PROMPT.md` does not list
   as open, and report the count in one line. Close any whose STATUS reads
   `DONE` (`stopping.md`, "Closing folders"); raise one owner item, once, for
   each of the rest, citing the folder.
5. **New work:** split it and write the briefs (`briefs.md`).
6. **Tell the owner how it works**, in two lines of your first message: each
   worker is answered in its own session, which they open from the agent view
   by name (or `claude attach <id>`, or in paste mode its terminal), and
   typing "dashboard" here shows where everything stands ("full dashboard"
   re-reads every source first).

# The state file

`<work root>/MANAGER-STATE.md`, 40 lines or fewer:

- the goal and the limits;
- each worker: session name, id and session id, workstream, primary topics,
  brief, last state, and any mark (`paste`, `stopping <hash>`, `ctx-msg`,
  `owner-stop <item>`, `scheduled <UTC time>`);
- the `-i`, `-s` and `-q` lists you pass the watcher;
- open owner items, and your own calls still awaiting review;
- while the owner is away, the away time and `Incidents`;
- the next step.

Rewrite the whole file at every transition so a compaction or a handoff
cannot lose anything. It holds the present only, never a history: lines for
retired workers, finished steps and settled items are dropped. The one
exception is a `RETIRED-BLOCKED` line, kept until a successor is running. Commit it by
explicit path at each milestone and at the end of the session. Briefs and
STATUS files are records in the work folder; a folder close commits them.
