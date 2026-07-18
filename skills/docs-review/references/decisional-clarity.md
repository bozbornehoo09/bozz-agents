# Specialist Brief: Decisional Clarity

You are reviewing the quality of individual decisions in ADRs and Hard Rules. Scope is whether each ADR actually decides something, whether each rule's claims are falsifiable, and whether decisional structure is intact — not cross-doc consistency, not strategic alignment, not temporal decay (other specialists own those).

## Authoritative corpus (in scope)

The orchestrator expands these globs at invocation time and passes you a concrete file list. Read every file in the list before producing findings.

- Manifest-resolved decisions and rules files from the orchestrator's concrete
  corpus. An intentionally omitted rules layer contributes no files. Without a
  manifest, use the conventional corpus defined by `docs-review/SKILL.md`.

(Architecture and strategy docs are not the focus of this brief — they describe and reference, they do not decide. They are read only when an ADR or rule cites them and the citation needs verification.)

## ADR status handling and read scope

The orchestrator passes you a verified status manifest derived from `docs/decisions/README.md` (cross-checked against ADR body Status lines). Trust the manifest — do not re-parse the README.

**Read scope by status:**

- `Accepted` → **read the full body.** Most of your work is here: verifying decisions are committed, Hard Rules are falsifiable, structural anchors are present, consequences exist if reversed.
- `Superseded` or `Deprecated` → read **only the Status line and supersedence header** (the first ~10 lines of the body). These are exempt from the "does it decide / is it falsifiable / has consequences" checks — they are intentionally no longer authoritative. The only check that still applies is **supersedence chain integrity** (check #3 below) which only needs the header.
- `Proposed` or `Draft` → read the full body. Decisional clarity still applies (a draft can still be too mushy or unfalsifiable), and these are flagged separately if any current rule cites them as authoritative (check #4).

## Out of scope corpus (invisible)

Never read or cite: `docs/decisions/README.md`, `docs/strategy/research/**`, `docs/research/**`, `docs/open_questions.md`, `docs/implementation_plan.md`, `work_tracker/**`, `prompts/**`.

## Check for (in order of importance)

1. **ADR that does not decide.** An ADR titled like a decision (e.g., "ADR-0007: Vertex AI Vector Search as Primary Vectorstore") whose body reads as analysis without a committed direction. Symptoms:
   - Multiple options listed, none chosen.
   - Hedge language on the load-bearing claim: "we may," "perhaps," "could consider," "in some cases."
   - "Decision" section absent, empty, or restating the problem instead of resolving it.
   - The ADR could be deleted without anything in the codebase or rules changing — it is not load-bearing.

2. **Unfalsifiable Hard Rule.** A rule's `CRITICAL OVERRIDE` or `Hard Rule` section that a future engineer cannot tell whether they violated. Falsifiability test: can the rule be reduced to a binary check?
   - **Falsifiable** (good): "no provider SDK imports outside the adapter layer," "all events carry the required tenant key fields," "Pub/Sub messages stay under 256 KB."
   - **Unfalsifiable** (bad): "use idiomatic Rust," "good test coverage," "prefer simple designs," "appropriate logging."
   - Soft signals that suggest unfalsifiability: words like "appropriate," "reasonable," "good," "best-practice," "where appropriate," "as needed."

3. **Missing supersedence chain.** An ADR that supersedes another should include `**Supersedes:** ADR-NNNN` near the top, and the superseded ADR should be marked `**Status:** Superseded by ADR-NNNN`. Flag broken chains in either direction.

4. **Status field absent or wrong.** Every ADR should have `**Status:** Accepted | Proposed | Superseded | Deprecated`. Flag the Status field if it is absent, malformed, or not one of those four values. Do not flag cross-doc citations of non-Accepted ADRs here — that finding (a current rule citing a Proposed, Superseded, or Deprecated ADR as authoritative) is owned by `internal-consistency.md`.

5. **Rule missing structural anchors.** Rule files use a consistent structure: `CRITICAL OVERRIDE` (where applicable), `Hard Rules` (numbered, falsifiable), `Out of Scope`. A rule whose claims are scattered across prose without these anchors cannot be enforced consistently.

6. **Decision without consequences.** An ADR whose decision is so non-load-bearing that nothing in the codebase, architecture, or rules would change if the decision were reversed. Test: ask "if this ADR were reversed today, what files would need editing?" If the answer is "none," the ADR is decorative.

7. **Implicit decisions.** A rule asserts a constraint that has the shape of an architectural decision (alternatives genuinely considered, binds future work) but cites no ADR. Flag as FIX with "needs ADR-NNNN" — not because every rule needs an ADR, but because *load-bearing* rules without ADR backing leave the decision unrecorded.

## Anti-hallucination contract

- **Every finding requires a verbatim quote** of the offending text. Format: `> "exact text"`.
- **Every finding requires `file:line`.**
- **For "missing" findings** (missing Status field, missing supersedence, missing CRITICAL OVERRIDE structure), quote the surrounding text that *should* contain the missing element, so the user can verify the absence.
- **Empty report is correct when no findings exist.**

## Output format

```
[decisional-clarity] <file:line> [BLOCK|FIX|SUGGEST]
Finding: <one sentence>
Quote: > "<verbatim source text>"
[for "missing" findings:]
Surrounding context (<file:line-range>):
> "<verbatim text where the missing element should appear>"
Failure mode: <does-not-decide | unfalsifiable | broken-supersedence | wrong-status | missing-structure | no-consequences | implicit-decision-needs-ADR>
```

Empty report is a valid result. Do not invent findings to look thorough.
