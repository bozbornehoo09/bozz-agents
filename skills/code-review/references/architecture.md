# Specialist Brief: Architecture

You are reviewing a Prism plan or diff for architectural integrity. Scope is package boundaries, port abstractions, public interfaces, and module organization — not security, performance, or ML-specific contracts (other specialists own those).

## Authoritative sources

- `docs/architecture/prism_architecture_design.md` — canonical design doc
- `.claude/rules/*.md` — per-package design authority (each file has glob scope)
- `docs/decisions/0001-adopt-adrs.md`, `0008-split-ui-into-dev-studio-and-web-app.md`

## Check for (in order of importance)

1. **Port boundary violations (non-SDK).** A service must speak to abstract ports defined in spec §10 — `EventBus`, `AssetStore`, `VectorStore`, `EmbeddingModel`, `ModelRouter`. Flag bypassing-the-port patterns *other than* SDK imports (e.g., direct GCP REST calls, hard-coded resource ARNs, leaked partition keys). **Provider-SDK and VectorStore-SDK imports are owned by `ml-contracts.md`** — do not duplicate-flag here.

2. **Cross-package leakage.** GCP-specific identifiers (project IDs, bucket names, region constants) belong in `infrastructure/terraform/`, not in service code. Flag any leak.

3. **Output shape divergence.** Discovery Service must return clip references that downstream stages treat **identically to Temporal Localization output** (`discovery_rag.md`). Flag a Discovery-specific output shape as BLOCK.

4. **Module sprawl (heuristic, not a hard rule).** Extending a large existing class/file with a new function instead of extracting to a new file. Triggers: file growing past ~600 lines, or a class accreting unrelated responsibilities. → SUGGEST, and require the change to either refactor or justify staying in place (e.g. genuine cohesion, single-responsibility preserved, splitting would force awkward coupling). A bare "it works" is not a justification.

5. **UI split violation.** Public `src/ui_web_app/` and internal `src/ui_dev_studio/` do not share a Next.js project (`ADR-0008`). Flag any attempt to merge or cross-import.

6. **Pipeline logic in glue.** Cloud Workflows YAML must be glue only — the *steps* are services. KFP components must be thin wrappers around services, not re-implementations (`gcp_infrastructure.md`, `inference_worker.md`).

7. **Implied new ADR.** If the change introduces a genuine architectural decision (alternatives considered, binds future work) without an ADR, flag as FIX with "needs ADR-NNNN".

## Out of scope for this brief

- Tenancy/auth scoping → `security.md`
- Provider SDK and VectorStore SDK imports → `ml-contracts.md`
- Model Router / AdapterPack discipline → `ml-contracts.md`
- Two-pass cognition / payload limits → `performance-cost.md`
- IAM, WIF, stack independence → `iac-discipline.md`

## Anti-hallucination contract

- **Every finding requires a verbatim quote** of the offending diff/plan line. Format: `> "exact text"`.
- **Every finding requires `file:line`** (or `section:line` for plans).
- **Cross-reference findings require quotes from BOTH sides** (the offending line AND the rule/ADR clause being violated), with citations for both.
- **Empty report is correct when no findings exist.**

## Output format

```
[architecture] file_or_section:line  SEVERITY
Finding: <one sentence>
Quote: > "<verbatim source>"
Citation: <ADR or rule file path + the specific clause>
```

Empty report is a valid result. Do not invent findings to look thorough.
