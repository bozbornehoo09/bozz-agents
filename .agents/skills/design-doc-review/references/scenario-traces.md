# Specialist Brief: Scenario Traces

Contents: [Authoritative corpus](#authoritative-corpus-in-scope) · [Out of scope](#out-of-scope-corpus-invisible) · [Check for](#check-for-in-order-of-importance) · [Anti-hallucination contract](#anti-hallucination-contract) · [Do not flag](#do-not-flag) · [Output format](#output-format)

Set-mode lens for `design-doc-review`. Reviewing docs one by one can leave every doc
clean while the system they describe still has holes: some path through the system
depends on a fact none of the docs gives, or one doc says the opposite of another. Those
holes only show when a single reviewer follows one concrete scenario through every doc.
Scenarios are generated from the states and branches the docs themselves define, so how
much was covered can be checked, and the number of scenarios is an output of the method
rather than a guess.

The lens runs in two roles, each a separate specialist the dispatcher starts: **MATRIX**
(one specialist) builds the scenario matrix, and **TRACE** (one specialist per batch)
follows approved cases through the docs. The dispatcher owns everything around them —
pinning, sizing, approval, batching, verification and stopping — as `set-mode.md`
defines. Do only the role you were given.

## Authoritative corpus (in scope)

- The export directory of the set at the pinned commit, every file read in full.
- For TRACE: your batch and the approved `SCENARIO-MATRIX.md`.

## Out of scope corpus (invisible)

Anything outside the export, including the working tree and docs not in the set. Do not
play an implementer or a partner team: judge whether the docs specify the system well
enough for the readers each doc names in its audience notes.

## Check for (in order of importance)

### MATRIX role: build `SCENARIO-MATRIX.md`

Its header gives the commit; each doc with its token estimate, plus the total; the docs
read as last committed; how many cases there are and how many are UNDERSPECIFIED; and the
expected tracing cost (one read of the set per batch of up to ten cases), including
whether it goes past ten batches.

1. **Axes.** An axis is one dimension along which the system can be in a different state
   when something happens. A value is real only when a line in the docs makes that state
   reachable, such as an enum value, a branch, a handled error, a gate or a phase. Find
   the axes in the docs themselves. Common sources are the initiator of an action, the
   condition of a dependency at that moment, the condition of an older version, how a
   second action is timed, a failure injected on purpose, a gate, and a phase; treat these
   as hints, not a checklist. Every value has a citation. The **entry lane** axis (what
   starts the action) is required, and tracing is batched along it. The axis table has
   four columns: axis, value, citation, owning doc.
2. **Cases.**
   - *Decisions.* Each recorded decision or ADR choice that implies an outcome gets one
     case; the outcome it states is the expected end state.
   - *Pairs.* For any two axes, each feasible combination of their values is exercised by
     some case. Construct them greedily: pick a combination not yet exercised, choose the
     remaining axes' values to exercise as many other open combinations as possible, and
     continue until none are left. A combination may be skipped only when a cited line
     rules it out; record each skip and its citation. When an axis is irrelevant to a
     case, write `—` and cite the line that makes it irrelevant.
   - *Alarms and runbooks.* Each alarm and each runbook entry gets one case: what triggers
     it, and the state the system should end up in after recovery.

   When two cases share an action and every axis value, keep one and give it all the
   family tags. Case ids are `D-nn` (decision), `P-nn` (pairs) and `A-nn` (alarm); cases
   added while tracing are `X-nn`. A case records its id, family tags, entry lane, axis
   values, the numbered steps of the action, the expected end state and where it is
   stated, the anchor quote or `none`, and a score.
3. **Scoring (0 to 3).** One point each: the case's citations come from two or more
   files; the case crosses a seam (one attribute with two writers, or a recovery path);
   the case is tied to a requirement or recorded decision, quoted and cited. If no doc
   states what the end state should be, the case is **UNDERSPECIFIED**: it is not traced;
   list it with its score and a quote of the nearby text.
4. **Coverage table.** One row per axis value and one column per case family; each cell
   lists case ids. Any empty cell gets a reason, for example that no alarm watches that
   state.

### TRACE role: one `traces/<case-id>.md` per case in your batch

Steps may only cite docs in the set. Each trace ends in one of three results:

1. **CONFLICT**: two docs make statements that cannot both be true; quote and cite both.
2. **GAP**: some step depends on a fact no doc states, and that fact would change the
   outcome or allow two different implementations.
3. **TRACEABLE**: the docs state every step and the end state. If a fact is missing but
   would neither change the outcome nor allow two different implementations, add a
   `SUGGEST:` note inside the trace; it is not promoted to a finding.

For every GAP or CONFLICT, also propose neighbouring cases: the same case with a single
axis moved to a different real value, leaving out skipped combinations and cases already
present. Each neighbour carries its cited end state (or is marked UNDERSPECIFIED) and its
score.

Lead with the finding: begin each trace with one exact sentence (who acts, what they do,
in which state, and what is absent or contradictory). The impact and the background
follow.

## Anti-hallucination contract

1. Text taken from the set is quoted exactly (`> "…"`) with `path:line@<sha7>`, using the
   full path from the repository root. This includes requirements and decisions used as
   anchors or listed under `Protects:`.
2. A GAP or an UNDERSPECIFIED case quotes the nearby text, at the place where the missing
   fact would have had to be written.
3. Report nothing just to show the run did something. Style, grammar and formatting are
   never findings here.
4. The dispatcher re-reads cited lines in the export byte for byte; a matrix or batch that
   fails goes back (`set-mode.md`).

## Do not flag

- Two docs that go into different amounts of detail but do not disagree.
- An HLD that says less than its LLD; that is how layering works.
- A disagreement between docs that no traced case runs into. Consistency among the
  project's authoritative layers is `docs-review`'s job.

## Output format

MATRIX hands back the contents of `SCENARIO-MATRIX.md` (header, axis table, cases,
coverage table). TRACE hands back one file per case:

```
# <case-id> — <TRACEABLE | GAP | CONFLICT>
<the finding in one sentence: actor, action, end state, and what is absent or contradictory>
Expected end state: > "<quote>" — <path:line@sha7>
Protects: <anchor quote with citation, or none>
Steps:
1. <actor> <action> → <state> — > "<quote>" — <path:line@sha7>
2. …
Result: <GAP: which step lacks which fact, plus the nearby quote; CONFLICT: the two quotes>
Neighbours: <for GAP or CONFLICT: each proposed case with its axis values, cited end state or UNDERSPECIFIED, and score>
```

Empty report is a valid result. Do not invent findings to look thorough.
