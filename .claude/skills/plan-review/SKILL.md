---
name: plan-review
description: Review an implementation plan against the project's architectural ADRs and per-package rules before code is written, plus built-in generic lenses for decisiveness, simplicity, test integrity, production safety and (for plans an implementer agent will build) hand-off exactness. Use when the user has drafted a plan markdown file (in docs/, work_tracker/, or pasted inline) and wants it stress-tested, or when writing-implementation-plans needs its gate. Fans out to specialist reviewers in parallel. Read-only.
---

# Plan Review

Find what would break if a plan were built exactly as written, while fixing it
still means editing a document rather than reverting code.

Two kinds of lens run. The **generic lenses** in `references/` work on any
project with no setup. The **project briefs** are yours: copy
`references/_brief-template.md` once per architectural concern, cite your own
ADRs and rules, and they run beside the generic set. `docs/customizing.md`
explains how to write them.

## Inputs

- **The plan.** A file path (a `PLAN.md` under the plans tree, a design note
  in `docs/`), pasted markdown, or a plan agreed earlier in the conversation.
  A plan that exists only in conversation is first written out as a short
  bulleted list and confirmed with the user; the review runs on that text.
- **Scope hint** (optional), e.g. "touches the API and the storage layer".
  Without one, infer the affected packages from the plan.
- **Design sources** (optional): the design docs, ADRs and requirement docs the
  plan serves. Default: the ones the plan cites, located through the
  `decisions`, `architecture` and `rules` layers of `context-manifest.yaml`.
- **Mode** (optional, below). Default `full`.

## Modes

| Mode | What the specialists see | Requested by |
|---|---|---|
| `full` | The whole plan, every applicable lens. | Default. |
| `sweep` | A frozen hand-off plan at its pinned heads. One dispatch of `references/sweep.md` per inventory — ten in all. | `writing-implementation-plans` while closing a plan (`../writing-implementation-plans/references/closure.md`). |
| `closure` | Only `git diff <frozen commit> -- <plan>`, plus the plan header and every step the diff touches, reviewed by the `full`-mode lens set. | `writing-implementation-plans` after its closing folds. |

In `closure` mode every dispatch prompt gains one sentence: "Report only on
lines this diff changes and on what those lines break in the steps shown."
Orchestration step 4 discards anything else.

## Specialists

Each brief is a self-contained reviewer instruction file in `references/`,
covering exactly one lens. Run them as independent specialists in parallel using
the host agent's subagent or delegation facility.

| Brief | The question it answers | Runs |
|---|---|---|
| `plan-hygiene.md` | Is every load-bearing choice made, ordered, bounded and verifiable? | Always |
| `simplicity.md` | Does the plan build anything its design does not call for? | Always |
| `testing-discipline.md` | Do the planned tests pin intended behavior rather than current output? | Always |
| `production-safety.md` | Could a step harm a live system, its data or its secrets? | Always |
| `implementation-plan-standard.md` | Is any decision of consequence still left to the implementer? | Hand-off plans (below) |
| `../code-review/references/lens-overrides.md` | Would a step build something the owner's standing corrections forbid? | When a register is found (below) |
| `_brief-template.md` | — | Never: template only, copy it to make a real brief |
| _(your `architecture.md`)_ | _(your architecture's boundaries)_ | Always |
| _(your domain brief)_ | _(that domain's rules)_ | When the plan touches that domain |

**Hand-off plans.** A plan is a hand-off when its header carries a `Hand-off:`
line, when `writing-implementation-plans` asked for the review, or when the
user says so. When it is unclear, ask.

**Overrides lens.** Look for the project's overrides register, located as
`../code-review/references/register.md` defines. Whenever that resolution finds
a register, dispatch `lens-overrides.md`. When it finds none, skip the lens and
put `Skipped: overrides — no register` in the report.

**Project briefs.** List them in the manifest under
`reviews.plan-review.briefs` (a bare name resolves in this skill's
`references/`; anything else is a path from the project root) and add a row to
the table above saying when each runs. With no project brief, run the generic
lenses alone and say so in the report.

**Shared reference.** `real-system-checks.md` is corpus, not a lens: it is
handed to `implementation-plan-standard`, `testing-discipline` and `sweep`
inventory 10.

## Orchestration

1. **Pin the input.** Settle the plan text (file, pasted, or restated and
   confirmed), the mode, and whether the plan is a hand-off. If the plan is in
   git, note the commit being reviewed.
2. **Give each dispatch its own corpus.** All of them get the plan. On top of
   that:

   | Dispatch | Also receives |
   |---|---|
   | `simplicity` | Every design, ADR and requirement doc the plan points to, by path; if it points to none, a note saying so. |
   | `production-safety` | The project's safety rules, if its `rules` layer or orientation file has any. |
   | `testing-discipline` | `real-system-checks.md`, and the existing tests the plan names. |
   | `implementation-plan-standard` | Everything that brief's "Authoritative corpus" section lists. |
   | `lens-overrides` | The register; when the plan names code files it changes, those files at its pinned heads. |
   | Each project brief | The ADRs and rule files it cites. |
   | Each `sweep` inventory | The plan's pinned heads (`repo @ commit`) and the files that inventory names. |

   A dispatch never sees another dispatch's extras.
3. **Fan out in parallel**, one dispatch per brief (in `sweep` mode, one per
   inventory), all with this prompt shape:
   ```
   Review this plan against {brief_path}. Plan: {plan, or path @ commit}.
   In-scope files: {this brief's corpus, with paths}.
   Anti-hallucination contract: every finding requires a verbatim quote
   AND a section:line (or file:line) citation. Cross-reference findings
   require both sides. An empty report is correct when no findings exist.
   Cite ADRs and rules by file path. Use the output format in the brief.
   End with the line 'COUNTS: BLOCK <n> FIX <n> SUGGEST <n>', an empty
   report too.
   ```
   Hand-off plans add: "A FIX or SUGGEST that can safely wait until build time
   may carry an `Implementer check:` line (SKILL.md, Implementer checks)."
   `closure` mode adds its sentence from Modes.

   When one brief's corpus will not fit a single specialist's context, split
   it by file group and finish it with a pair call
   (`../skill-review/references/review-completeness.md` section 2).
   Dispatches that fail on rate limits are re-sent with less parallelism; any
   other failure gets one retry. A lens that still has not reported, or came
   back unfinished, goes on the report's `failed:` field and forces `REVISE`
   (section 1 there) — a missing report is never read as a clean one.
4. **Verify BLOCK findings.** Re-read the cited line for every BLOCK finding
   (plan, design, rule, or code at its commit); confirm the quote matches
   byte-for-byte. Drop any with hallucinated quotes. Before keeping a BLOCK
   that says a section, line or field is absent, search the plan for it; if
   it is there, drop the finding. In `closure` mode, also drop anything outside
   the diff.
5. **Spot-check FIX/SUGGEST findings.** Verify at least 3 random findings per
   severity. Drop mismatches. For an `Implementer check:` line, confirm that the
   test or build line it quotes exists in the named step and would surface the
   problem. In `sweep` mode, also re-verify three `OK`/`n/a` rows in each table
   and confirm each table covers every step; a table that is short or failed is
   re-run once, then marked `unverified`.
6. **Aggregate.** Order by severity, then lens. When two lenses flag the same
   step for the same defect, merge them into one finding tagged with both.
   Copy every `Implementer check:` line into the report's Implementer checks
   list and every `Skipped:` line into its header. In `sweep` mode, print the
   ten tables first and the gaps after them as findings.
7. **Verdict, one line.** REVISE if any BLOCK; READY-WITH-FIXES if no BLOCK
   and at least one FIX; READY otherwise. An unfinished lens (step 3), or a
   `sweep` table marked `unverified`, makes it REVISE, and that pass never
   counts as one with no BLOCK.

## Implementer checks

Applies to hand-off plans only. A FIX or SUGGEST may be left for the
implementer to settle while building when **both** hold:

- a test or build command already written into a named step would surface the
  problem; and
- settling it adds no mechanism and changes no behavior.

The finding keeps its severity — this is a deferral tag, not a fourth level —
and gains one `Implementer check:` line: the step, what to check, the quoted
test or build line that would surface it, and what to do if it fails. At
closure, `writing-implementation-plans` copies these into the plan's
`## Implementer checks` section. A BLOCK is never deferred this way, and
neither is any `simplicity.md` finding.

## Anti-hallucination contract (binding on every specialist)

These rules are non-negotiable. The orchestrator **drops** any finding that violates them.

1. **Every finding MUST include a verbatim quote** of the plan text being flagged. Format: `> "exact text from the plan"`. Paraphrases are invalid.
2. **Every finding MUST cite `section:line`** (or `file:line` if the plan is a markdown file path). No line/section number → finding invalid.
3. **Cross-reference findings require quotes from BOTH sides.** A finding of the form "this plan step violates rule X" must include the verbatim plan text AND the verbatim rule clause being violated, with citations for both.
4. **"Missing element" findings quote the surrounding context** where the element should appear, so the absence is verifiable. Do not assert an absence without it.
5. **An empty report is the correct output when no findings exist.** Specialists must not invent findings to justify the call.
6. **Out-of-scope corpus is invisible.** Each brief declares what it does NOT review. Specialists must not flag concerns outside their declared lens. A file the dispatch did not list is neither opened nor cited; a point that would need one is reported as "out of scope — cannot evaluate".
7. **A recorded, approved departure is not a defect.** When the plan shows the user chose to diverge from a rule or template — a `## Plan Changes` row, an overrides-register entry — leave it alone.
8. **Read each in-scope file end to end before reporting.** Searching for a keyword and citing the hit is not a review.

## Do not flag (negative scope)

- Plan formatting, prose style, section ordering preferences.
- Speculative concerns the plan doesn't actually commit to ("what if they later decide to…").
- Anything the plan explicitly defers to a future iteration with an honest "out of scope" note.
- Detail below the level the plan chose to write at — that is `code-review`'s
  job once code exists. The exception is a hand-off plan: there, exact detail
  is the chosen level, and `implementation-plan-standard.md` reviews it.

## Severity criteria

- **BLOCK** — resolve before building. Built as written, the plan would:
  - contradict an Accepted ADR or a hard rule;
  - take an unsafe production action;
  - commit to a *new* architectural decision that no ADR records;
  - in a hand-off: leave the implementer a choice that changes behavior, omit
    the section listing what the plan leaves out or its mechanism-count line, or
    carry a step with neither a real-system check nor a `first observed in`
    pointer;
  - introduce a second writer of a value, when the `simplicity` finding names
    the requirement at risk and gives a numbered failure sequence.
- **FIX** — the plan breaks a rule or standard in a way an edit to the plan
  can correct, or it carries a clear regression or test-integrity risk.
- **SUGGEST** — improvement that doesn't violate a rule (sequencing, clarity,
  an explicit non-goal, a check worth adding). Optional.

## Output template

```
# Plan Review: <plan title>

Plan: <path @ commit | inline — restated and confirmed>
Mode: <full | sweep | closure on <diff range>>
Scope: <inferred packages>
Specialists run: <every lens dispatched; split parts and pair call named>; failed: <none | lens names, failed or unfinished>
Project briefs: <names | none found — generic lenses only>
Checked: <n> BLOCK quotes re-read · <n> findings spot-checked · <n> dropped
mechanism count: design N / plan N
Skipped: <lens or check — reason>          (one line per skip, if any)

## BLOCK
- [production-safety] <file:line>
  > "<verbatim plan text>"
  <what goes wrong if this is built>
  → <rule or ADR file:line> "<verbatim clause>"

## FIX
- [testing-discipline] <file:line>
  > "<verbatim plan text>"
  <what is wrong or absent>

## SUGGEST
- [plan-hygiene] <file:line>
  > "<verbatim plan text>"
  <the improvement>

## Implementer checks          (hand-off plans: deferred FIX/SUGGEST findings)
- [<lens>] <file:line> · step <id> · check: <what to verify> · surfaced by > "<test or build line>" · on failure: <action>

Verdict: REVISE
```

## What this skill is NOT

- Not a code reviewer — the plan has no code yet. Use `code-review` after implementation.
- Not an editor. It reports findings; the user, or
  `writing-implementation-plans`, changes the plan.
- Not a substitute for ADR creation. If the plan implies a *new* architectural decision (alternatives genuinely considered, binds future work), surface that as a BLOCK with "needs ADR" rather than rubber-stamping it.
- Not a generic SOLID/DRY checker. Simplicity findings come only from
  `simplicity.md`'s checks, and an architecture finding must come from a
  project brief that cites a real ADR or rule.
