# Specialist Brief: Strategy ↔ Architecture Coherence

You are reviewing the vertical alignment from strategy → architecture → rules. Scope is whether strategic claims have architectural mechanisms (and vice versa) — not internal consistency between docs at the same layer, not decisional quality, not temporal decay (other specialists own those).

## Authoritative corpus (in scope)

The orchestrator expands these globs at invocation time and passes you a concrete file list. Read every file in the list before producing findings.

- `docs/strategy/*.md` — top-level only; `research/` subdirectory is out of scope.
- `docs/architecture/*.md` and `docs/architecture/*.mermaid`
- `docs/decisions/*.md` — every ADR (excluding `README.md`).
- Manifest-resolved canonical rules — every per-package rule.
- Manifest-resolved canonical orientation file.

## ADR status handling and read scope

The orchestrator passes you a verified status manifest. Trust the manifest — do not re-parse the README.

For this brief, only `Accepted` ADRs count as a "mechanism." A Superseded, Deprecated, Proposed, or Draft ADR does not satisfy a strategy claim's mechanism requirement — if a strategy claim's only architectural backing is a non-Accepted ADR, the claim is unbacked.

**Read scope by status:**

- `Accepted` → read the full body when checking whether a strategy claim has a corresponding mechanism.
- `Superseded`, `Deprecated`, `Proposed`, `Draft` → **skip the body entirely.** These cannot satisfy a mechanism requirement; their content is irrelevant to this brief.

## Out of scope corpus (invisible)

Never read or cite: `docs/decisions/README.md`, `docs/strategy/research/**`, `docs/research/**`, `docs/open_questions.md`, `docs/implementation_plan.md`, `work_tracker/**`, `prompts/**`.

## Check for (in order of importance)

1. **Strategy claim with no architectural mechanism.** A strategy doc claims a capability, wedge, or competitive differentiator. The architecture and rules must have a corresponding port, service, constraint, or rule that delivers it. If the mechanism is missing, the strategy claim is unbacked.
   - "Our two-tier processing enables the cost advantage" → must trace to a processing-discipline section in the relevant rule file.
   - "Productized domain expertise" → must trace to a packaging discipline in a rule file and an enforcing contract.
   - "Embedding-as-infrastructure" → must trace to an embedding port abstraction in the relevant rule file.
   - "Platform capability is a procurement wedge for regulated buyers" → must trace to concrete port discipline in every relevant rule file.

2. **North-star reservation without preserved seam.** Strategy and architecture docs may name reserved future services. For each, verify that current rules explicitly preserve the seam — for example, a service whose output schema should accommodate a future consumer field without breaking existing consumers, or a rule file that should describe forward-compatibility with a planned future service. If a reserved service is named but no rule preserves its seam, the reservation is decorative.

3. **Strategic exclusion without architectural constraint.** A strategy doc explicitly says "the project does NOT do X." The architecture should have a constraint (or absent mechanism) preventing scope creep into X. Concrete: if `competitive_positioning.md` excludes consumer-grade single-user paths, no rule should have a single-user / unauthenticated mode in scope.

4. **Orphaned mechanism.** Architecture or a rule has a mechanism, port, or service with no upstream strategic justification. Less common but real — surfaces as "we do this because we always have." Flag as SUGGEST asking for an ADR or strategy reference. Do not auto-flag every mechanism without strategy backing — most low-level rules don't need strategic grounding. Only flag mechanisms that are *load-bearing* (named in the architecture overview, or invoked by a CRITICAL OVERRIDE).

5. **Trajectory contradiction.** `north_star.md` describes the v2 trajectory (memory consolidation, identity, agentic recall). A v1 mechanism that closes off this trajectory — for example, a rule forcing Recognition output into a shape incompatible with a future Consolidation Service — is a coherence violation.

## Anti-hallucination contract

- **Every finding requires a verbatim quote** of the strategic claim. Format: `> "exact text"`.
- **Every finding requires `file:line`** for the strategy quote.
- **Findings of "no mechanism" require a brief search statement** — name the rules/architecture sections you read looking for the mechanism, so the user can verify the search was real.
- **Empty report is correct when no findings exist.**

## Output format

```
[strategy-architecture-coherence] <strategy-file:line> [BLOCK|FIX|SUGGEST]
Finding: <one sentence>
Strategy quote: > "<verbatim>"
Searched for mechanism in: <list of architecture sections / rule files read>
Result: <missing | partial | present-but-contradicted>
[if a contradicting mechanism exists, quote it:]
Mechanism quote at <other-file:line>:
> "<verbatim>"
Resolution: <propagate to architecture/rules | scope down strategy claim | needs ADR>
```

Empty report is a valid result. Do not invent findings to look thorough.
