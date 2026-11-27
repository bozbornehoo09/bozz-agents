# Flattened Execution — when a pen-holder runs the review itself

When `design-doc-write` or `design-doc-edit` gates its own output, it does not start a
review subagent. It runs the four lenses itself, from its own level: the review is
**flattened**. Only this file describes that path and assigns each lens a runner. Both
pen-holders link here; if anything they say conflicts with the table below, follow the
table.

Flattening exists because "pen-holder → review subagent → reader subagents" is three
levels deep, and many hosts do not let a subagent start subagents of its own.

| Lens | Who runs it when flattened |
|---|---|
| cold-read | Fresh reader subagents, launched directly by the pen-holder (`../../design-doc-write/references/zero-context-gate.md`) |
| verify | A fresh read-only subagent, so the check is independent of the author. With no subagents, the pen-holder runs it and says so in the report |
| tone (tone and structure rubrics) | The pen-holder's own context or a subagent; either conforms |
| audience-and-length | The pen-holder's own context or a subagent; either conforms. The script runs wherever the lens runs |

1. **Start with the script** (`../../design-doc-write/scripts/measure_doc.py <doc> --type <grain>`).
   Missing or half-filled audience notes get fixed before any lens runs. If the
   body is over its ceiling, fix that first too, because a doc about to lose a thousand
   words will churn every other lens; the exception is a doc with a valid length
   acceptance line (`../../design-doc-write/references/length-budget.md`), where the script reports the overage as
   information and the round goes ahead.
2. **Do not start a `design-doc-review` subagent.** Run all four lenses as the table says,
   using the inputs and dispatch rules in `design-doc-review` Orchestration steps 4 and 5,
   on every pass.
3. **Check findings before folding them.** Findings are hypotheses
   (`../../fold-review-findings/SKILL.md`: verify first, edit second). Apply Orchestration
   steps 6 and 7 to the findings unchanged. This matters more here than in a standalone review: an unchecked
   finding folded by a pen-holder becomes a false statement in the doc, where in a
   standalone review it would only have been a wrong line in a report.
4. **Combine the findings and decide the verdict** with `design-doc-review`'s Severity section and
   Orchestration steps 8 and 9.
5. **Fold, then rerun on the new text**, until a pass's verdict is not `REVISE` (no BLOCK,
   and the cold-read gate complete and passing). Fold everything a pass found before the
   next pass; do not cycle one finding at a time. Fold the FIXes from that last pass
   without another round, and report its verdict with those FIXes listed as folded but
   unreviewed.
6. **Limit the loop.** Hand back `REVISE`, listing what is left and saying whether the
   approach itself needs rethinking, as soon as any of these happens: BLOCKs go up from
   one pass to the next; a BLOCK survives the fold aimed at it; pass five still has a
   BLOCK; or the only fix for a BLOCK would be a made-up fact or a closed open question. Never loop
   without end, and never report `READY` without a pass that earned it.

With no subagent facility at all, the cold read follows
`../../design-doc-write/references/user-mediated-gate.md`, and the user may instead run
`design-doc-review` in a separate session and paste the report back.
