# Specialist Brief: Internal Consistency

You are reviewing the project's authoritative documentation set against itself for cross-doc factual agreement. Scope is contradictions, inaccurate citations, and missed propagation between in-scope docs — not strategy alignment, not decisional quality, not time-aged claims (other specialists own those).

## Authoritative corpus (in scope)

The orchestrator expands these globs at invocation time and passes you a concrete file list. Read every file in the list before producing findings. No grep-and-go.

- Manifest-resolved decisions, architecture, strategy, rules, and orientation
  files from the orchestrator's concrete corpus. Layers intentionally omitted
  by the project manifest contribute no files. Without a manifest, use the
  conventional corpus defined by `docs-review/SKILL.md`.

## ADR status handling and read scope

The orchestrator passes you a verified status manifest derived from `docs/decisions/README.md` (cross-checked against ADR body Status lines). Trust the manifest — do not re-parse the README.

**Read scope by status:**

- `Accepted` → read the full body. Most of your work is here: verifying citation accuracy, cross-doc consistency, and propagation.
- `Superseded` or `Deprecated` → **skip the body.** The only relevant finding type for these ADRs is **"a current authoritative doc cites this ADR as if it were live"** — and that finding is detected from the *citing doc*, not the superseded ADR's body.
- `Proposed` or `Draft` → skip the body. Same citation-check finding type as Superseded.

## Out of scope corpus (invisible)

Never read, cite, or reason about: `docs/decisions/README.md`, `docs/strategy/research/**`, `docs/research/**`, `docs/open_questions.md`, `docs/implementation_plan.md`, `work_tracker/**`, `prompts/**`. If a finding requires one of these, return "out of scope — cannot evaluate."

## Check for (in order of importance)

1. **ADR ↔ ADR contradictions among Accepted ADRs.** One Accepted ADR claims X, another Accepted ADR claims not-X without explicit supersedence. Two ADRs deciding overlapping problems in different directions.

2. **Rule ↔ ADR contradictions.** A manifest-resolved rule file states a rule
   whose cited ADR says something different. Verify each ADR reference against
   the actual decision.

3. **Architecture ↔ ADR contradictions.** `architecture_design.md` makes a claim that an Accepted ADR contradicts. The architecture doc is downstream of ADRs; if it disagrees, it's the architecture that's wrong (or a new ADR is implied — see `decisional-clarity.md`).

4. **Rule ↔ Rule contradictions.** Two rule files make incompatible claims about the same concept. Most common form: a cross-cutting ADR's constraint stated correctly in one rule file but described differently in another.

5. **Inaccurate cross-citations.** A rule cites "ADR-NNNN" by number; verify the cited file's title, status, and decision actually match what the rule claims. Catches typos, copy-paste errors, and stale references after ADR renumbering. **Citing a non-Accepted ADR (Superseded, Deprecated, Proposed, Draft) as authoritative is itself a finding** — FIX severity.

6. **Missed factual or decisional propagation.** A binding ADR or rule contract
   added to one doc should propagate to every dependent it governs. Concrete
   examples to scan for:
   - A cross-cutting ADR (e.g., every record carries the tenant key) → every rule touching data flow, events, or queries must enforce the required fields.
   - A cross-cutting ADR constraining external dependencies → every affected service rule must reference the constraint where that dependency is in scope.
   - A cross-cutting ADR governing endpoint security → every UI/API rule whose service falls in scope must reference it.

   Do not assess whether reserved future services preserve a strategic seam;
   `strategy-architecture-coherence.md` owns that vertical check.

7. **Orientation drift.** Paths, conventions, or doc names referenced by the
   canonical orientation file no longer exist or have moved.

**Do not flag:** supersedence-chain defects (an old ADR not marked
Superseded, broken chain markers) are owned by
`decisional-clarity.md` — flag here only two docs making
contradictory SEMANTIC claims.

## Anti-hallucination contract

- **Every finding requires a verbatim quote.** Format: `> "exact text from doc"`. Paraphrases are invalid.
- **Every finding requires `file:line`.**
- **Cross-reference findings need quotes from BOTH sides** with both file:line citations.
- **"Missing" findings quote the surrounding context** where the missing element should appear (an unpropagated concept, a stale or absent pointer), so the absence is verifiable.
- **Empty report is correct when no findings exist.** Do not invent findings.

## Output format

```
[internal-consistency] <file:line> [BLOCK|FIX|SUGGEST]
Finding: <one sentence>
Quote: > "<verbatim source text>"
[for cross-doc findings, also include:]
Counter-quote at <other-file:line>:
> "<verbatim other source text>"
Citation: <which doc is authoritative, or "needs reconciliation">
```

Empty report is a valid result. Do not invent findings to look thorough.
