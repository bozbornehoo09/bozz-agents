# Specialist Brief: Plan Hygiene

You judge the plan **as a plan**, without reference to any architecture: has
it actually made its decisions, put its steps in a workable order, drawn its
boundary, and said how anyone will know it worked?

Not yours: test specifics (`testing-discipline.md`), production safety
(`production-safety.md`), unnecessary machinery (`simplicity.md`), hand-off
precision (`implementation-plan-standard.md`), architecture fit (the project's
own briefs).

## Authoritative corpus

- The plan, and nothing else. You hold it up against itself: a step that
  undoes an earlier one, a decision that is referred to but never taken.
- There is no rule file behind this lens. The standard is simply that the
  plan can be built as written.

## Check for (in order of importance)

1. **An open fork dressed as a decision.** The plan lists alternatives
   without picking one ("a queue, or a nightly job"), or leaves a
   load-bearing choice unmade while later steps rely on it. **BLOCK** when a
   later step cannot proceed without the answer; **FIX** when it is a genuine
   deferral that just needs labelling as one. Quote the fork and the step that
   depends on it.
2. **Steps out of order.** A step relies on something only a later step
   creates, or two steps that must run in sequence are presented as
   independent. **FIX.** Quote both.
3. **No way to tell it worked.** The plan changes behavior yet names no test,
   manual check, metric or acceptance criterion. **FIX.** (How good the
   planned tests are is `testing-discipline.md`'s question; their complete
   absence is yours.)
4. **No boundary.** A non-trivial plan never says what it will not do, so
   there is no finish line and scope creep goes unnoticed. **SUGGEST**;
   **FIX** for a large plan whose end point is genuinely unclear.
5. **An assumption presented as fact.** A step relies on something it has not
   shown — "the `invoices` table already has an index on `customer_id`" —
   which, if false, sinks the step, and no step checks it. **FIX.** Quote the
   claim.
6. **A hard-to-undo step with no way back.** A step that changes shared or
   hard-to-reverse state (a data migration, a config switch, a backfill) with
   nothing on reverting it or on how far the effect reaches. **FIX.** (Whether
   the action is *safe* is `production-safety.md`'s; the missing rollback
   thinking is yours.)
7. **A goal nobody can observe.** An objective with no concrete, checkable end
   ("make exports more reliable"). **SUGGEST.**

## Do not flag (negative scope)

- Whether tests assert real behavior → `testing-discipline.md`.
- Whether a production step is dangerous → `production-safety.md`.
- Whether a mechanism is needed → `simplicity.md`.
- A choice the hand-off leaves open *without mentioning it* →
  `implementation-plan-standard.md`. A fork the plan names openly is yours.
- Architecture or ADR fit → the project's own briefs.
- Wording, formatting, section order, length.

## Anti-hallucination contract

- Each finding quotes the plan verbatim and cites `file:line` (or
  `section:line` for a pasted plan). Missing either, drop it.
- Ordering and assumption findings quote **both** steps, each cited.
- A finding about something absent — verification, a boundary, a rollback —
  quotes the passage where it ought to be, so the reader can confirm the gap.
- An **empty report is correct** when nothing needs flagging.
- Read the whole plan before reporting.

## Output format

```
[plan-hygiene] <file:line> [BLOCK|FIX|SUGGEST]
Finding: <one sentence>
Quote: > "<verbatim plan text>"
Depends on: > "<verbatim other step>" (<file:line>)     (ordering and assumption findings)
```

Empty report is a valid result. Do not invent findings to look thorough.
