Read this when `claude agents --json` does not answer: no `claude` command,
or one with no agent view (Codex, for instance).

# Paste mode

- **Launching.** Print the brief path and a command for the owner to run in
  a fresh terminal, such as
  `codex "Act as the bozz-agents architect: read and follow <shared>/../architect.md, then run <brief path>"`.
  The owner answers that worker in its terminal.
- **Messages** reach a worker only when it reads its channel at the start and
  end of a turn. Mark every idle worker `paste` as soon as you write it an
  MSG, and make its item `type "read your channel" — open <session>`.
- **Waking.** Where the host cannot run background jobs, run the watcher as a
  blocking call with a short `-m` (25 minutes) and do the wake steps each time
  it returns; a stop is then `snap`, `stop`, `start` in turn. Never end your
  turn while a worker is live. For the channel check's wait, run a plain
  blocking `sleep 60`.
- **Succession** needs Claude Code's session id and agent view, so it is not
  in use: skip the claim, the wake guard and the size-cap handoff, and end
  the session when the owner says stop (`end-of-session.md`).
- **Unattended:** the owner leaves your turn running while away; you show
  the morning report at their next message.
