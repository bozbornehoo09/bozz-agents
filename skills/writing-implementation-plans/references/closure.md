# Closing a plan

Use this as soon as a full `plan-review` pass over a hand-off plan comes back
with no BLOCK. It is the only definition of closure.

Why closure exists: review can go on forever, each pass finding something new
to polish. Closure ends that. After the first clean full pass the plan is
frozen, checked once for completeness, and from then on only verified,
mechanical corrections go in.

## The protocol

1. **Freeze.** No further full passes. The frozen text is the plan commit the
   clean pass reviewed — unedited since, and committed no later than that
   pass's review record. Only steps 3–5 may change it.

2. **Sweep.** Run `plan-review` in `sweep` mode on the frozen plan at its
   pinned heads. Take the heads from the plan's `Pinned heads:` line; failing
   that, from the commits its README records; failing that, the default
   branch heads as they are now. Inventory 10 is the real-system inventory:
   `../../plan-review/references/real-system-checks.md` section 1 for each
   package the plan changes.

   Save the result as `reviews/<date>-<PLAN id>-sweep-<n>.md`
   (`plan-tree.md`). Under its heading it carries a `Plan:` line (the plan and
   its frozen commit) and a `Pinned heads:` line. Any table marked `unverified` halts
   closure, handled as in step 5.

3. **Triage, then fold only what qualifies.** Every open item — the clean
   pass's FIXes, every `Implementer check:` finding from any full pass, and
   each sweep gap — gets exactly one outcome, written into a `## Triage`
   section of the sweep record:

   | Outcome | When |
   |---|---|
   | `folded` | Either a sweep BLOCK that can be fixed without any new mechanism, or a mechanical correction — say, an omitted field, an incorrect permission, a test expecting the wrong value — that you confirmed against a design line or against code (`path:line` at the pinned heads). Unconfirmed edits are never folded. |
   | `implementer-check` | It meets `plan-review`'s implementer-check test: a test or build line in a named step would surface it, and settling it adds no mechanism or behavior. It becomes a row in the plan's final section, `## Implementer checks` — step, check, the surfacing test or build line, the action on failure — with a `PLAN_precheck_` id (`naming.md`) if the project uses ids. |
   | `declined: <why>` | Anything else that would add a mechanism, change behavior or widen scope. |

   The boundary for `folded`: a closing fold may make an existing instruction
   clearer or confirm it; it never adds a new state, mechanism, recovery
   path, ordering rule or behavioral decision. When the plan really does need
   one of those, even to resolve a BLOCK, it has become a design call
   (`SKILL.md` step 3) and it triggers a restart.

   A SUGGEST is declined unless it is purely mechanical.

4. **Review the closing diff.** Commit the folds by explicit path, then run
   `plan-review` in `closure` mode on `git diff <frozen commit> -- <plan>`.
   Save it as `reviews/<date>-<PLAN id>-closure-<n>.md`.

5. **Handle what the closing review finds.**

   | Finding | Action |
   |---|---|
   | BLOCK caused by folding a FIX | Undo that fold; the original finding becomes an implementer check or is declined. |
   | BLOCK caused by folding a BLOCK (a fold that could not be skipped) | Correct the fold. |
   | After either of those | Run `closure` mode once more, on the new diff. |
   | A BLOCK no fold caused, or any BLOCK in that second run | Closure stops. Report the blocked output (`SKILL.md`, Output format) with `closure reopened`, and ask the user whether to restart a full review. |
   | Anything below BLOCK | Triage as in step 3, and commit the resulting rows with the final record, so nothing that needs acting on lives only inside a review record. |

6. **Done.** The final review record is the last closure review — or the
   clean full pass, if steps 3–5 changed nothing. Set the component README's
   status to `passed` and point its plan-review line at that record — in flat
   layout, the plan's row in the plans index (`plan-tree.md`); finish `GATES.md` if the project keeps one. Report using
   `SKILL.md`'s output format.

**After done.** Editing a closed plan — for instance, to fold in the answer
to a question `implementing-a-plan` raised — runs steps 4–5 on that edit's
diff alone, unless a restart trigger applies. The plan-review line (README
or flat-layout index row) then points at the new record.

## Restart triggers

A full review starts over only when one of these happens; whoever causes it
is responsible for noticing:

- an ADR or a user decision changes behavior the plan implements;
- the plan's scope changes;
- an interface or file shared with another plan changes (the interfaces are
  listed in the plans index; the plan whose edit changes one does the check);
- step 3 or step 5 turns out to need a new mechanism;
- the pinned heads have moved in a way that matters — `implementing-a-plan`
  step 1 finds a cited reference changed enough to alter what a step means.

A restart runs `SKILL.md` step 5 until a full pass is clean, then this
protocol from the top.

The plan itself never includes a step to re-check its own `file:line`
references; `implementing-a-plan` step 1 does that once, at build time.
