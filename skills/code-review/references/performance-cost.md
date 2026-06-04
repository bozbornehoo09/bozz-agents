# Specialist Brief: Performance & Cost

You are reviewing a Prism plan or diff for cost, latency, and scale discipline. Two-pass cognition is the single largest cost lever in the system; payload-size discipline is the second.

## Authoritative sources

- `.claude/rules/inference_worker.md` — two-pass cognition, references-not-bytes
- `.claude/rules/ingestion_api.md` — Pub/Sub payload budgets
- `.claude/rules/gcp_infrastructure.md` — Workflows payload limits, scale-out triggers
- `.claude/rules/discovery_rag.md` — query-time vs ingest-time embedding cost

## Check for (in order of importance)

1. **Frontier model on raw asset.** Two-Pass Cognition is non-negotiable: Localization (economy tier) narrows; Recognition (frontier tier) runs only on narrowed clips. A frontier call over a full-length asset → BLOCK. (`inference_worker.md`)

2. **Bytes through Pub/Sub.** Pub/Sub hard limit is 10 MB/message; Prism's *design* ceiling is 256 KB. Any event payload carrying base64 video, frame data, or large blobs → BLOCK. Payloads are references (GCS URIs, frame ranges) and metadata only. (`ingestion_api.md` Hard Rule 4)

3. *(removed — see Out of scope: bytes-through-Workflows is owned by `iac-discipline.md`)*

4. **Re-embedding at query time.** Discovery is a cheap retrieval layer over pre-computed embeddings. Code that re-embeds the corpus inside a query path is a BLOCK. Re-embedding is a re-indexing pipeline, not a request. (`discovery_rag.md` "Cost Discipline")

5. **Vector query without (tenant_id, domain_id) filter.** Beyond the security concern (other specialist), missing partition keys forces a full-index scan — latency and cost regression. → FIX (or BLOCK if combined with the security finding).

6. **Embedding generation in a sync request path.** Embedding is an ingest-time cost. Code that calls `EmbeddingModel.embed()` in a user-facing request handler → FIX. (`discovery_rag.md`)

7. *(removed — see Out of scope: cross-stack coupling is owned by `iac-discipline.md`)*

8. **Cold-start in the request path.** Vertex AI Prediction serverless cold-start can dominate first-request latency. If a synchronous request fans out to a serverless endpoint with no warm pool / fallback, flag for SUGGEST and reference the scale-out trigger to GKE GPU pools.

9. *(removed — see Out of scope: KFP caching defaults are owned by `ml-contracts.md`)*

10. **Pub/Sub topic at >10K msg/sec sustained without scale-out plan.** Reference the Pub/Sub → Kafka on GKE trigger. SUGGEST.

## Out of scope for this brief

- Whether a port is correctly abstracted → `architecture.md`
- Whether a worker imports a provider SDK → `ml-contracts.md`
- Whether `tenant_id`/`domain_id` are present at all → `security.md` (this brief addresses the *cost consequence* of their absence on queries)
- Bytes through Cloud Workflows → `iac-discipline.md`
- Cross-stack coupling forcing platform-core redeploys → `iac-discipline.md`
- KFP caching defaults → `ml-contracts.md`

## Anti-hallucination contract

- **Every finding requires a verbatim quote** of the offending diff/plan line. Format: `> "exact text"`.
- **Every finding requires `file:line`** (or `section:line` for plans).
- **Cross-reference findings require quotes from BOTH sides** (the offending line AND the rule/ADR clause being violated), with citations for both.
- **Empty report is correct when no findings exist.**

## Output format

```
[performance-cost] file_or_section:line  SEVERITY
Finding: <one sentence>
Quote: > "<verbatim source>"
Citation: <ADR or rule file path + the specific clause>
```

Empty report is a valid result. Do not invent findings to look thorough.
