# Specialist Brief: Verify Against the Artifact

Contents: [Authoritative corpus](#authoritative-corpus-in-scope) · [Out of scope](#out-of-scope-corpus-invisible) · [What counts as a claim](#what-counts-as-a-claim) · [Check for](#check-for-in-order-of-importance) · [Framing checks](#framing-checks) · [Anti-hallucination contract](#anti-hallucination-contract) · [Output format](#output-format)

Clean prose and a passed cold read say nothing about whether the doc is true. A doc can
clear both and still describe a field the schema lacks or a behaviour the code does not
have. This lens compares what the doc asserts with what the code, schemas and records
actually say. It is the review-side counterpart of the pen-holders' "no unchecked
facts" rule (`../../design-doc-write/references/shared-authoring-rules.md`).

**The lens checks the list it is given, and only that list.** It does not go looking
for other claims, so complete coverage depends on the dispatcher's enumeration
(`design-doc-review` Orchestration step 4). A claim left off the list is checked by
nobody. If the list is plainly partial for the doc you were handed, say so in a
`Noticed, not asked:` line instead of quietly widening your scope.

## Authoritative corpus (in scope)

- The doc under review, for the quoted claims.
- The artifacts each claim names or implies: source code, schemas and interface
  definitions, configuration and infrastructure files, sample payloads, and for
  decision-status claims the project's ADRs, work plan, open-questions log or issue
  tracker. Read-only.
- When the doc has figures: `../../design-diagrams/references/when-to-diagram.md` and
  `../../design-diagrams/references/diagram-conventions.md`.

## Out of scope corpus (invisible)

Claims not on the list, the doc's wording and structure (other lenses), and general
engineering facts. Do not verify how public cloud services, standard protocols or common
libraries behave; verify only claims about this system.

## What counts as a claim

- **Data shape**: a field, its type, how many there are, a size limit ("each event carries
  `id`, `type` and `occurred_at`").
- **Contract**: an operation's inputs, outputs and errors; an identifier format; which
  service owns a field.
- **Behaviour**: what a component or stage does ("a `4xx` other than `429` is not
  retried").
- **Framing**: "this is new", "this is cheap", a latency or throughput figure, the cost or
  scope of a phase ("about three days of work").
- **Figures**: wiring, fields and flows a figure shows are claims like any other.
- **Platform behaviour**: how a gateway, generated client or framework in this codebase
  works. To count as verified, read two or three current call sites in source (pick the
  newest with `git log`); a single file or a dated note leaves it a FIX. So does hedging
  a platform fact as a conditional ("if we switch to the generated client…"): either
  confirm it and state it plainly, or label it unverified.
- **Constants and mechanisms**: a limit, a batch size, a placeholder value, a timeout.
  Check each against the system it serves and the limits around it.
- **Specific referents**: a table, field or component called by a friendly paraphrase
  ("the delivery log") where the artifact has a real name (`delivery_attempts`), or a
  mechanism described through something the doc never names.
- **Decision status** (from `../../design-doc-write/references/tone-rubric.md` check A): every choice the doc presents as
  settled. The artifact is the source material: ADRs, the work plan, the open-questions
  log, the issue. Settled there = verified. **Still listed as open there = a
  decision-honesty BLOCK**, the most valuable finding in the family, and one no other lens
  can raise, because the doc alone gives no sign of it.
- **Naming** (from `tone-rubric.md` check F): each name the doc gives an entity, checked
  against what the artifact shows the entity is.
- **Cross-doc structure** (from `../../design-doc-write/references/structure-rubric.md`): that detail removed in a
  de-duplication survives in the owning section (compare with the previous version,
  `git log -p`); that LLD-level content found in an HLD already lives in the LLD; that a
  section builds on its parent HLD instead of repeating it (S2 d). Each is a FIX.

## Check for (in order of importance)

Name the artifact that would settle each claim, read it, and compare.

- **The artifact contradicts the claim → BLOCK.** Quote both sides.
- **Stated as fact, no source cited, and you cannot confirm it → FIX.** Not necessarily
  wrong, but a reviewer cannot rely on it. The fix is a citation, or marking it
  unverified with what would settle it.
- **True but uncited where a reader would want the source → SUGGEST** a citation.

### Framing checks

- **A hard problem called easy → FIX.** "Just de-duplicate the retries" when deciding
  that two retries are the same event is itself unsolved.
- **A later phase sized as a small increment → FIX** when it needs its own design.
- **Time and rate figures are checked against their source**, not a mock or an old figure,
  and against the right path. Two code paths may each have their own figure for good
  reason, so find out which path a number describes before calling two numbers a
  conflict.
- **A constant that does not fit its system → FIX**: a limit that protects nothing, limits
  whose product does not match a stated total, a placeholder that is also a legal value
  (`0` for a rate), a batch smaller than the page it fills.
- **A friendly label where a real identifier exists → FIX.** Cite the identifier; the fix
  is to use it.

## Anti-hallucination contract

- Every finding quotes the doc's claim verbatim with `file:line` **and** quotes the
  artifact verbatim at its `path:line` — the line, field or definition that confirms or
  refutes it. For an absence ("no such column"), quote the surrounding definition where
  the element would appear. A finding missing either quote is dropped; a paraphrase of
  the artifact is not a quote.
- A platform-behaviour verdict cites each use it rests on: `path:line`, a verbatim excerpt,
  and the `git log` date showing it is current. A verdict resting on one use is a FIX, not
  verified.
- "Could not verify" is a valid FIX only when the doc states the claim as fact without a
  citation. If the doc cites a source you cannot reach, record it as `out of scope to
  verify`, not as unverified.
- An empty report is correct when every claim checks out.

## Output format

```
[verify] <doc file:line> [BLOCK|FIX|SUGGEST]
Claim:    > "<verbatim doc text>"
Artifact: <path:line> > "<verbatim artifact text>" — <what it actually shows>
Finding:  <the contradiction, or "stated as fact with no cited source">
```

Then one line per claim that checked out: `VERIFIED <doc file:line> — <artifact path:line>`.

Empty report is a valid result. Do not invent findings to look thorough.
