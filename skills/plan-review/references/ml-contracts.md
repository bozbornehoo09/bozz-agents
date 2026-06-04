# Specialist Brief: ML Contracts

You are reviewing a Prism plan or diff for ML-platform discipline: Model Router boundary, AdapterPack/PEFT pattern, judge strategy, eval contract, two-pass cognition, KFP component shape.

## Authoritative sources

- `.claude/rules/inference_worker.md` — the authoritative ML rules
- `.claude/rules/discovery_rag.md` — VectorStore + EmbeddingModel ports
- `docs/decisions/0005-python-for-ml-workers.md`
- `docs/decisions/0006-vertex-ai-pipelines-for-ml-dags.md`
- `docs/decisions/0007-vertex-ai-vector-search-as-primary-vectorstore.md`
- `docs/decisions/0012-frontier-judge-strategy.md`
- `docs/decisions/0013-eval-contract-and-moderation-loop.md`

## Check for (in order of importance)

1. **Worker imports a provider SDK.** No `anthropic`, `openai`, or `google-genai` outside the Model Router service. BLOCK. (`inference_worker.md` "Hard rules" #1)

2. **Worker loads adapter weights.** AdapterPack (LoRA/DoRA/QLoRA) selection happens in the Router, keyed on `domain_id`. Workers requesting a specific technique → BLOCK. (#2 + #3)

3. **Worker owns prompts.** Prompt templates live in the AdapterPack Registry. Inline prompts in worker code → FIX. (#3)

4. **Domain branching in code.** `if domain == "sports":` or equivalent in worker logic → BLOCK. Domain knowledge is data, not code. (#4)

5. **Two-pass cognition violation.** Frontier model invoked over an unfiltered asset → BLOCK. Localization runs `quality_tier: economy`; Recognition runs `quality_tier: frontier` only on already-narrowed clips. ("Two-Pass Cognition (Non-Negotiable)")

6. **Recognition output missing model lineage.** Outputs must include `base_model_ref`, `adapterpack_id`, `version`, plus confidence and timestamps. Missing any → FIX. ("Output Discipline")

7. **Eval report without confidence stratification.** `EvaluationReport` must report metrics per confidence bucket (≥0.9, 0.7–0.9, 0.5–0.7, <0.5). Flat / unstratified report → BLOCK and blocks AdapterPack release. (`ADR-0013` "Cross-cutting requirements")

8. **Judge policy hard-codes a provider.** `LabelingJob.judge_policy.mode` should support `single` and `ensemble` from day one with sampling rate. Code that bakes "Gemini" or "Claude" as the judge → FIX (judge identity is config). (`ADR-0012`)

9. **KFP component re-implements service logic.** A KFP component image must be a thin wrapper around a service entrypoint, not a re-implementation. Recognition logic in a `Recognize` component instead of in the Recognition Service → BLOCK. (`inference_worker.md` "KFP-specific rules" #1)

10. **Bytes between KFP components.** Pass GCS URIs in artifact metadata; components fetch/write themselves. Bytes passed via string parameters or in-memory blobs → BLOCK. (#4)

11. **VectorStore SDK leak.** Service code importing the Vertex AI Vector Search SDK directly → BLOCK. Goes through the `VectorStore` port. (`discovery_rag.md` Hard rule)

12. **Discovery invokes Recognition.** Discovery returns references and emits `discovery.matched`. Calling Recognition from within Discovery → BLOCK. (`discovery_rag.md` "Hybrid Search-then-Analyze")

13. **Caching defaults wrong for production runs.** KFP caching is opt-out per run, not per component. Production pipeline runs that don't disable caching → FIX. (`inference_worker.md` "KFP-specific rules" #3)

## Out of scope for this brief

- Tenancy filters on queries → `security.md`
- Pub/Sub payload sizes → `performance-cost.md`
- Terraform module shape → `iac-discipline.md`

## Anti-hallucination contract

- **Every finding requires a verbatim quote** of the offending diff/plan line. Format: `> "exact text"`.
- **Every finding requires `file:line`** (or `section:line` for plans).
- **Cross-reference findings require quotes from BOTH sides** (the offending line AND the rule/ADR clause being violated), with citations for both.
- **Empty report is correct when no findings exist.**

## Output format

```
[ml-contracts] file_or_section:line  SEVERITY
Finding: <one sentence>
Quote: > "<verbatim source>"
Citation: <ADR or rule file path + the specific clause>
```

Empty report is a valid result. Do not invent findings to look thorough.
