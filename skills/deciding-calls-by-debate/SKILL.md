---
name: deciding-calls-by-debate
description: Settle a blocking design choice while its owner is unavailable by convening a panel of read-only subagents (one panelist for a small choice, three for a mid-sized one, five for a broad one) that argue independently, cross-examine each other, and vote. The choice is applied only when the panel agrees and its evidence checks out, and every result is logged for the owner to confirm or undo; otherwise the choice is parked with its options. Use when progress would otherwise wait on the owner (an unattended run, the owner offline), or when asked to "debate this call", "decide this without me", or "run a debate on" something. Choices that are costly to undo, conflict with a recorded decision, or shift a deadline skip the panel and are parked; trivial tidy-ups are just done.
---

# Deciding Calls by Debate

A way to keep moving when a design choice is blocking you and the person who
owns it is not around. A small panel of subagents argues the choice from
assigned positions, first without seeing each other's work and then in
response to it, and finally votes. Agreement alone is not enough: the
winning option's evidence must hold up and nothing expensive may be left
unanswered. The panel's record is kept on disk so the owner can audit the
result later and reverse it with a single revert.

## Scope

Covers:
- A single blocking choice between options, debated one at a time.
- Its debate directory and, if it is decided, the one change that applies it.
- Handing the result to whichever skill owns the layer it lands in.

Does not cover:
- Hunting for defects in a plan, diff, or document: use `plan-review`,
  `code-review`, or `docs-review`.
- Authoring the ADR, open-question entry, or plan edit: `update-decisions`,
  `update-open-questions`, and `update-work-plan` do that.
- Any choice the owner can be asked about now. Ask.

What you need before starting: the choice and the candidate options; the
layer paths from `context-manifest.yaml` (decisions, open questions, rules,
work plan, work tracker); the project's overrides register, located as
`../code-review/references/register.md` defines (none is fine); and
the code and docs the choice affects.

Where debates are stored: the path of a manifest layer with `id: debates` if
one exists, else a `debates/` directory inside the work-tracker layer
(`work_tracker/debates/` by default). One subdirectory per choice, named
`<YYYY-MM-DD>-<slug>`.

## Steps

### 1. Triage

Put the choice in exactly one lane.

| Lane | What falls here | Action |
|---|---|---|
| Just do it | Tidy-ups: renaming, moving files, layout, wording, refreshing dates | Make the change and list it in your report. No panel, never parked. |
| Park | Anything costly to undo (an externally visible API or data format, a stored schema, a promise made to other people); anything that conflicts with an Accepted ADR, an open-questions entry, or the overrides register; anything that shifts a deadline or committed scope | No panel. Skip to step 6 and park it with its options. |
| Small | Confined to one file or section, reverted by a single edit, invisible to others | Panel of 1 |
| Mid-sized | Spans several files or components but is still cheap to revert | Panel of 3 |
| Broad | Touches many components, cost, security, or operations, yet remains revertible | Panel of 5 |

### 2. Write the question

Before any panelist starts, write `question.md` in the debate directory. It
holds:

1. **What is wrong:** describe the concrete mechanism (which component does
   what, and what fails as a result) before any judgement of it.
2. **Candidate options:** each real option with what it costs, and a final
   "none of these" slot.
3. **Fixed constraints:** the ADRs, rules, and register entries that bind the
   choice, each quoted with `path:line`, plus any size limits and deadlines.
4. **Orchestrator's preference:** your own pick, labelled as such.

### 3. Seat the panel

With a panel of 1, the only seat is the `contrarian`, who makes the strongest
case against your preference. With a panel of 3 or 5 (N):

- Seat one `champion-<option>` per option, at most N − 1 of them; if there are
  more options than that, leave the weakest without a champion.
- Always seat one `critic`.
- In a panel of 5, fill any seats still empty in this order:
  `fact-checker`, then `failure-hunter`, then `owner-stand-in`.

What each seat does:

| Seat | Job |
|---|---|
| `champion-<option>` | Argues for its option. |
| `critic` | Argues against every option (including any left without a champion), hunts for a hybrid or an unlisted option, and checks each against the recorded decisions. |
| `fact-checker` | Confirms or refutes every factual claim against the source, citing `path:line`. |
| `failure-hunter` | Looks for ways each option breaks: edge cases, races, the cost of backing it out. |
| `owner-stand-in` | Reasons from the ADRs, rules, and overrides register the way the owner would. |

Run each panelist as its own read-only review subagent, using whatever
subagent or delegation mechanism the host provides and the most capable
reasoning model available. Launch all panelists for a round together. If the
host cannot run that many at once or throttles you, cut the batch size in
half and try again, down to one at a time; any other failed launch gets one
retry before it is recorded as failed. Rounds never overlap: round 2 starts
only after every round-1 paper is in, and the ballot comes after the final
round-2 paper. Give each panelist the path to `question.md`, its seat, the
round's task, and the anti-hallucination contract below. Panelists write nothing; you save
their replies.

### 4. Hold the rounds

- **Round 1, independent.** Each panelist reads `question.md` and everything
  it cites, argues from its seat, and sees no other round-1 paper. Save as
  `round1-<seat>.md`.
- **Round 2, cross-examination.** Give each panelist every other round-1
  paper. Where the host lets you resume a subagent with its context, send it a
  follow-up message; where it does not, start it fresh with `question.md`,
  its own round-1 paper, and the others pasted in. Champions may change sides
  or merge options. Save as `round2-<k>-<seat>.md`. Hold a second
  cross-examination (`k = 2`) for a broad choice, or whenever the first one
  ends without agreement.
- **Ballot.** The final cross-examination prompt also asks every panelist
  for its chosen option or hybrid, its confidence (low, medium, or high), and
  the most serious objection it still holds. Collect these in `ballots.md`.

With a panel of 1, the contrarian's round-1 paper responds to your
preference, you reply, its round-2 paper responds to your reply, and it then
casts its ballot.

### 5. Check for agreement

Discard every claim in the ballots and standing objections that lacks a
verbatim quote with `path:line`, or whose quote differs from what the cited
line actually says (open the file and look). Then the choice counts as
**agreed** only if all of these hold:

1. All ballots name one and the same option or hybrid. With a panel of 1,
   the contrarian's ballot must match your preference.
2. The factual claims behind that option were confirmed against the cited
   source: by the fact-checker if one sat, otherwise by you.
3. None of the standing objections points to a bad state that can actually
   be reached, or to a cost that would be hard to reverse.

Failing any one of these means the choice is parked.

### 6. Apply or park

Write `verdict.md` in the debate directory. Line 1 reads either
`DECIDED: <option>` or `PARKED: <reason>`; line 2 is the single argument that
settled it.

If **decided**:
1. Make the change as one isolated unit (a dedicated commit when the session
   is allowed to commit) and write its id into `verdict.md`, so the owner can
   undo it in one revert.
2. Record it with the debate directory cited as the source and the label
   *decided by debate, owner to review*:
   - if it constrains future work, through `update-decisions`, as a new ADR
     whose context states it was settled by debate and awaits owner review;
   - otherwise through `update-open-questions`, as a question answered
     provisionally until the owner confirms.

If **parked**:
1. Through `update-open-questions`, log the choice, every option with its
   cost, and your preference, citing the debate directory.
2. If a planned item is waiting on it, flag that item through
   `update-work-plan`.
3. Keep going on whatever the choice does not block.

Either way, list the debate in the session's work-tracker entry.

## Anti-hallucination contract (binding on every panelist)

These bind every panelist; step 5 throws out whatever breaks them.

- A factual claim comes with a verbatim quote and the `path:line` it came
  from, whether that is code, an ADR, a rule, a register entry, or a doc.
- To say two things conflict, quote each side with its own `path:line`.
- To say something is missing, quote the text around the place it should be,
  with `path:line`.
- Saying there is no objection is allowed. Making one up, or making up a
  fact, is not.
- Stay inside the options and constraints in `question.md`; do not debate
  wording or tidy-ups.
- Read `question.md` and every file it cites end to end before arguing, not
  just a search hit.

## Pause-for-confirmation rules

- **Owner is present** (they invoked the skill themselves): PAUSE once the
  question is written, so they can confirm the lane and `question.md` before
  the panel starts; PAUSE again before a decided change is applied.
- **Nobody is watching:** do not pause and do not guess. Whatever you would
  have paused on, and the steps leave unresolved, gets parked.
- If applying a decided change would edit a file `question.md` does not
  mention, PAUSE (or park, when unattended).
- The skills you hand off to apply their own pause rules; let them.

## Style

- Keep `question.md` and `verdict.md` to about a screen each, and quote the
  constraints instead of restating them.
- Use the seat names from step 3 verbatim, in prose and in file names.
- Assume the owner reads `verdict.md` weeks later with no context: say what
  was chosen, the reason, and the exact undo.

## Output format

```
# Deciding Calls by Debate: <choice>

Lane: <just do it | park: <reason> | small | mid-sized | broad>
Debate directory: <path | none>
Seats run: <seats> (failed: <seat | none>)
Claims discarded: <n>

Result: <DECIDED: <option> | PARKED: <reason>>
Settled by: <one line>
Change: <commit or change id | n/a>
Handed to: <update-decisions | update-open-questions | update-work-plan>
```

## Pitfalls

- Convening a panel for something an Accepted ADR already answers. Follow the
  ADR.
- Calling a unanimous ballot "agreed" when nobody checked the winning
  option's claims against the source.
- Running a panel on a tidy-up, or parking one.
- Showing panelists each other's round-1 papers before all of them are saved.

## What this skill is NOT

- Not a path for choices that are costly to undo, conflict with a recorded
  decision, or move a deadline; those always go to the owner.
- Not needed for tidy-ups, which are simply done.
- Not a review: it settles one choice, while the review skills look for
  defects.
- Not a substitute for the owner: each decided choice is flagged for their
  review and can be undone with one revert.
