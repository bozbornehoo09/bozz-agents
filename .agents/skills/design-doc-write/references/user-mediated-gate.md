# Cold Read Without Subagents — the user runs the readers

Used in place of `zero-context-gate.md` step 2 when the host cannot start a subagent.

The skill cannot open a fresh session on its own, and it must not play the cold reader
itself: its own session already knows the project, which is exactly what the gate is
meant to exclude. The user runs the readers instead.

1. **Build one packet per reader.** The panel size is the gate's (one reader per declared
   audience, two at minimum). A packet is the step-2 reader prompt with the persona filled
   in and the path line swapped for the doc itself, wrapped in `<<<DOC>>>` and
   `<<<END DOC>>>` lines, with a line number at the start of every line. Drop the TOOL LOG
   section, since a pasted doc involves no file access, and ask for SUMMARY and GAPS
   only.
2. **Generate the packet with a script or a copy command, never by retyping.** A retyped
   doc has different line numbers, so every citation lands on the wrong line.
3. **Hash the doc when you build the packets and again when the answers arrive.** This
   path can take hours, so a changed hash (STALE) is likely; check it.
4. **Ask the user to paste each packet into its own brand-new session** (a new chat or a
   new agent run with no history) and bring every answer back.
5. **No gate result until all answers are in.** One at a time is fine. If the user
   declines, or an answer never comes back, the gate is INCOMPLETE: the review verdict is
   `REVISE`, never `READY`.
