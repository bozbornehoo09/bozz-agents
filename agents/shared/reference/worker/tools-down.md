Read this after any failed tool call, and as a successor whose `HANDOFF.md`
carries a `Tools down:` line. Every session holding the worker contract
follows it.

# When a tool server drops

In a long session a connected tool server can drop and stay down until the
owner reconnects it (`/mcp` in Claude Code). A fresh session starts connected.

- Work that needs the dropped tool waits. List
  `reconnect <tool> in <session>` under `Open owner items`. With the owner
  present, ask them. If they are away, do not sit waiting: hand off, except
  while an open cross-review is yours, in which case keep folding and leave
  the tool's step for a fresh session.
- Any `HANDOFF.md` you write during the outage names it:
  `Tools down: <tools>, since <UTC time>`.
- A successor's first move is one read with each tool on that line. One that
  answers clears the predecessor's item. If one still fails, rewrite the item
  under your own session name, do not hand off over it again, and go on with
  other work; once nothing else is left, hand off with
  `Blocked: all remaining work waits on <tool>`.
