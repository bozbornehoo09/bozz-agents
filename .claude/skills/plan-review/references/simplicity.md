# Specialist Brief: Simplicity

## Contents

- [Your question](#your-question)
- [Authoritative corpus](#authoritative-corpus)
- [The standard](#the-standard)
- [Check for](#check-for-in-order-of-importance)
- [Do not flag (negative scope)](#do-not-flag-negative-scope)
- [Anti-hallucination contract](#anti-hallucination-contract)
- [Output format](#output-format)

## Your question

**Does this plan build more than the design it cites asks for?** You look
only at what the plan *adds*. Forks, ordering and rollback are
`plan-hygiene.md`'s; tests are `testing-discipline.md`'s; safety is
`production-safety.md`'s; hand-off precision and required plan sections are
`implementation-plan-standard.md`'s.

## Authoritative corpus

- The plan text.
- The design the plan cites, as the dispatch provides it — design docs, ADRs,
  requirement docs — including any table or rule in them that says which
  component writes which value. If the plan cites no design, its own
  requirement lines take the design's place, and every finding says so.
- The standard below. Cite it as `simplicity.md:<line>`.

## The standard

**Principles.**

- **S1.** The plan sets the shape of the code: a lean plan gives lean code.
  Treat every step as removable until something requires it.
- **S2.** Where trouble appears at a seam — a place where one component writes
  or restores state — first try removing something, or sending the work
  through the component that already owns that state. Adding a condition, a
  handler, a timer, or a local copy of another system's state at that seam is
  a last resort, not a ban.
- **S3.** A simplicity BLOCK must state the requirement it protects and walk
  through a concrete failure as numbered steps. Missing either, it is reported
  as `FIX (no requirement / no sequence)`.

**Terms.**

- A **mechanism** is anything that adds runtime behavior: a handler, timer,
  queue, flag, cache, retry loop, poller, sweeper, reconciler branch, a newly
  persisted attribute, or a new writer of a stored value. Pinning down an edge
  case of a step the design already names is not a mechanism.
- A **second writer** is a step that writes a value which the design, an
  ownership table or an ADR assigns to some other component.

## Check for (in order of importance)

1. **Unnamed mechanism.** The plan adds a mechanism the design never
   mentions. **FIX**, unless the plan cites the design line (or, without a
   design, the requirement line) that calls for it. Remedy: remove it, or
   cite the line.
2. **Second writer.** Remedy: send the write through the component that owns
   the value. **BLOCK** when S3 is met — the requirement is named and a
   numbered two-writer failure is given; otherwise
   `FIX (no requirement / no sequence)`.
3. **Copied state.** A step stores, caches or mirrors a value owned by
   another component, where the design reads or derives it instead. Remedy:
   read it from the owner. **FIX.**
4. **Single-use knob.** The plan introduces a config value, parameter or flag
   whose only caller, by the plan's own account, always passes the same
   value. Remedy: make it a constant. **FIX.**
5. **Speculative abstraction.** An interface, base class, registry, plugin
   point or generic layer with exactly one implementation. Remedy: inline it.
   **FIX.**
6. **Step that changes nothing measurable.** Deleting the step would leave
   every acceptance criterion unchanged. Apply only when the plan states
   acceptance criteria, and never to a verification, test, rollback or
   confirmation step. Remedy: delete it. **FIX.**
7. **Mechanism count.** Every report ends with the count line
   (`mechanism count: design N / plan N`). The first number counts mechanisms
   the design specifies for the components under change (`n/a` if there is no
   design); the second counts mechanisms the plan builds. Cite every counted
   line. If the plan
   states a count that differs from yours: **FIX.**

**Severity and deferral.** Check 2 is the only one that can reach BLOCK, and
only under S3. No simplicity finding is ever turned into an implementer check
(`SKILL.md` "Implementer checks"): no test or build would expose an extra
mechanism, and resolving one changes what gets built.

## Do not flag (negative scope)

- Anything the other generic lenses own (see "Your question").
- The design's own choices. You measure the plan against the design, not the
  design against your taste.
- A departure the user approved and the plan records — a `## Plan Changes`
  row, an overrides-register entry. A justification the plan gives itself is
  not approval.
- Claims about code you have not read.

## Anti-hallucination contract

- Every finding quotes the plan text verbatim and cites `file:line` (or
  `section:line`). Without both, drop it.
- Checks 1–3 also quote the design, ownership-table or ADR line (for check 1,
  the passage where such a line would sit); check 6 quotes the acceptance
  criteria. Each quote is cited.
- A check-2 BLOCK quotes the requirement and lays out the numbered sequence.
- An empty report is fine, but it still includes the count line and the
  `Checked:` line.
- Read the whole plan and every design document you were given before
  reporting.

## Output format

```
[simplicity] <file:line> [BLOCK|FIX|SUGGEST]
Finding: <one sentence, including the remedy>
Quote: > "<verbatim plan text>"
Design: > "<verbatim design / ownership-table / ADR line, or the acceptance criteria>" (<file:line>)     (checks 1–3 and 6)
Requirement: > "<verbatim requirement>" (<file:line>)     (BLOCK only)
Sequence: 1. … 2. … 3. …     (BLOCK only)

mechanism count: design N / plan N (<lines counted>)
Checked: <plan line ranges read, per check>
```

Empty report is a valid result. Do not invent findings to look thorough.
