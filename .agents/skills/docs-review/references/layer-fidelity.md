# Specialist Brief: Layer Fidelity

You are reviewing whether each authoritative doc holds the kind of content its layer exists for, stays true to its own declared purpose, and matches the template its owning `update-*` skill defines. Scope is one doc against its own role — not contradictions between docs (`internal-consistency`), not strategy-to-mechanism tracing (`strategy-architecture-coherence`), not the quality of a decision (`decisional-clarity`), not aging external claims (`temporal-decay`).

The point: the layer model works only while each layer holds its own content. Rationale that lives in a rule file is never superseded when the decision changes; a session log inside the architecture doc reads as current design; an orientation file that restates the rules drifts from them. Catch content that has left its layer.

## Authoritative corpus (in scope)

The orchestrator passes you a concrete file list and the layer map (each layer's id, path, and title from `context-manifest.yaml`). Read every file in the list before producing findings. No grep-and-go.

- Manifest-resolved decisions, architecture, strategy, rules, and orientation files from the orchestrator's concrete corpus. Layers intentionally omitted by the project manifest contribute no files. Without a manifest, use the conventional corpus defined by `docs-review/SKILL.md`.

Layer roles (use the manifest titles when given; these are the defaults):

| Layer | Holds | Does not hold |
|---|---|---|
| decisions (ADRs) | the WHY: context, decision, alternatives, consequences | session narrative, task lists |
| strategy | positioning and the claims it rests on | mechanism detail, task lists |
| architecture | synthesis of decisions into one design | new decisions argued in prose, session narrative |
| rules | the falsifiable WHAT per package, citing ADRs | rationale debates, history |
| orientation | a short map that points at the other layers | restated rules, rationale, plans |

## ADR status handling and read scope

The orchestrator passes you a verified status manifest. Trust it — do not re-parse the README.

- `Accepted` → read the full body.
- `Proposed` or `Draft` → read the full body; template conformance still applies.
- `Superseded` or `Deprecated` → skip the body. Historical ADRs are exempt.

## Out of scope corpus (invisible)

Never read or cite: `docs/decisions/README.md`, `docs/strategy/research/**`, `docs/research/**`, `docs/open_questions.md`, `docs/implementation_plan.md`, `work_tracker/**`, `prompts/**`, and anything under an `archive/` folder. If a finding needs one of these, return "out of scope — cannot evaluate."

## Check for (in order of importance)

1. **Content in the wrong layer.** A block whose kind belongs to another layer:
   - *Rationale outside an ADR* — a paragraph arguing why an option was chosen or rejected, inside a rule, the architecture, or the orientation file, with no ADR pointer. (A load-bearing *constraint* with no ADR is `decisional-clarity` check 7, not yours; you flag the *argument*, not the rule.)
   - *Activity narrative* — dated "today we…" / "this session…" accounts in any authoritative doc. That is the work tracker's content.
   - *Forward work* — task lists, "next we will…", or TODO markers in an authoritative doc. That is the work plan's or backlog's content.
   - *Open questions posed as pending* — "we have not decided whether…" inside an authoritative doc with no pointer to the open-questions log.
   - *Restated content* — the orientation file (or architecture) copying a rule or ADR at length instead of pointing at it, so the copy can drift.

2. **Drift from the doc's own declared purpose.** A doc states what it is for — its opening paragraph, a purpose comment, or its manifest layer title. Later sections that abandon or contradict that stated purpose, with no recorded pivot ("originally X; after Y, now Z", a newer ADR, a dated note), are a finding. A recorded pivot is the system working, not drift.

3. **Template conformance.** Check a doc against the template its owning `update-*` skill defines, when one exists. For ADRs that is the template in `update-decisions` (Date line, `## Context`, `## Decision`, `## Alternatives considered`, `## Consequences`). A required section that is missing, or present but empty, is a finding. Exclusions: the `**Status:**` value and supersedence markers are `decisional-clarity`'s (checks 3–4); a Decision section that does not decide is `decisional-clarity` check 1. A section that is legitimately absent because it does not apply yet, or a departure the doc records as deliberate, is not a finding.

## Severity

- **BLOCK** — only when misplaced or drifted text states something untrue that the next reader would act on, and you quote the line that shows it untrue (`Contradicted by:`). Without that quote, FIX at most.
- **FIX** — rationale outside an ADR, narrative or task lists in an authoritative doc, unrecorded drift from the declared purpose, a missing required template section.
- **SUGGEST** — a short restatement that could become a pointer; a purpose statement that would help a doc lacking one.

## Anti-hallucination contract

- **Every finding requires a verbatim quote** of the misplaced or drifted text. Format: `> "exact text"`.
- **Every finding requires `file:line`.**
- **Drift findings quote both sides**: the drifted text and the stated purpose it departs from, each with `file:line`. When the purpose comes from the manifest layer title, cite `context-manifest.yaml:<line>`.
- **Restated-content findings quote both sides**: the copy and the rule or ADR text it restates, each with `file:line`. Without the source quote, the finding is dropped.
- **"Missing section" findings quote the surrounding context** where the section should appear.
- **Never attribute purpose text to a line where it does not literally appear.**
- **Empty report is correct when no findings exist.** Most well-kept docs produce none.

## Output format

```
[layer-fidelity] <file:line> [BLOCK|FIX|SUGGEST]
Finding: <one sentence — what left its layer, drifted, or is missing>
Quote: > "<verbatim text>"
Belongs in / Departs from: <target layer> | > "<verbatim stated purpose>" (<file:line>) | <template section> (update-decisions template)
Restates: <restated only: > "<verbatim source rule or ADR text>" (<file:line>)>
Contradicted by: <BLOCK only: > "<verbatim line showing the text untrue>" (<file:line>)>
Failure mode: <rationale-outside-adr | narrative | forward-work | pending-question | restated | purpose-drift | missing-template-section>
Fix: <move to <layer> and leave a pointer | record the pivot | add the section>
```

Empty report is a valid result. Do not invent findings to look thorough.
