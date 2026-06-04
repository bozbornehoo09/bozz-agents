# Specialist Brief: IaC Discipline

You are reviewing a Prism plan or diff for infrastructure-as-code discipline. Scope: Terraform usage, stack independence, IAM, the orchestration split between Vertex AI Pipelines and Cloud Workflows.

## Authoritative sources

- `.claude/rules/gcp_infrastructure.md`
- `docs/decisions/0002-target-google-cloud-platform.md`
- `docs/decisions/0003-terraform-for-iac.md`
- `docs/decisions/0006-vertex-ai-pipelines-for-ml-dags.md`

## Check for (in order of importance)

1. **Console-authored or hand-edited state.** Terraform (or OpenTofu) is the only IaC. References to manually-created GCP resources, or `terraform state rm/mv` used as a workaround → FIX. Note the underlying cause.

2. **Long-lived service account JSON keys.** Workload Identity Federation is required for any CI/CD that calls GCP. Committed JSON keys, env vars consuming them, or instructions to download the key → BLOCK. (`gcp_infrastructure.md` Hard Rule #4)

3. **Project-level Editor or basic roles.** Each Cloud Run service and Vertex AI Pipeline component gets its own service account with the minimum required roles. `roles/editor` or `roles/owner` on a service account → BLOCK. (Hard Rule #5)

4. **Cloud Workflows used for an ML DAG.** Any analysis pipeline (preprocess → embed → localize → recognize → ...) routed through Cloud Workflows instead of Vertex AI Pipelines → BLOCK. (`gcp_infrastructure.md` "Orchestration Split (Hard Rule)")

5. **Vertex AI Pipelines used for non-ML glue.** Ingest fan-out, scheduled maintenance, and HITL coordination belong in Cloud Workflows. KFP used for these → FIX.

6. **Cross-stack dependencies forcing coupled redeploys.** Five stacks (`platform-core`, `services`, `pipelines`, `observability`, `modules`) deploy independently. A `pipelines/` change that requires `platform-core/` to redeploy → FIX. (Hard Rule #1)

7. **Local Terraform state.** Remote state backend required (GCS bucket with versioning + lifecycle + CMEK). Local `.tfstate` in the repo or scripts → BLOCK. (Hard Rule #3)

8. **KFP DAG Python in `infrastructure/terraform/`.** Pipeline definitions live in `src/inference_worker/pipelines/`. Terraform provisions schedules, service accounts, GCS staging, Artifact Registry — not the DAG code. → BLOCK.

9. **Pipeline business logic in Workflows YAML.** YAML lives in `infrastructure/terraform/pipelines/workflows/` as a Terraform-managed resource; the *steps* it invokes are services owned by `src/`. Inline business logic in YAML → FIX.

10. **Bytes through Workflows.** ~512 KB variable budget. Workflow that passes blobs → BLOCK (also caught by `performance-cost.md`).

11. **Step modules not reused.** New pipeline composed of inlined resources instead of `modules/steps/<step>` → SUGGEST. (Hard Rule #6)

12. **Scale-out trigger silently exceeded.** Pub/Sub topic past ~10K msg/sec sustained, vector index past 10M per domain, or query latency past 200 ms at target recall → SUGGEST with the relevant scale-out target named.

## Out of scope for this brief

- Whether a service correctly uses the Model Router → `ml-contracts.md`
- Whether a request carries `tenant_id`/`domain_id` → `security.md`
- Whether a worker imports a provider SDK → `ml-contracts.md`

## Anti-hallucination contract

- **Every finding requires a verbatim quote** of the offending diff/plan line. Format: `> "exact text"`.
- **Every finding requires `file:line`** (or `section:line` for plans).
- **Cross-reference findings require quotes from BOTH sides** (the offending line AND the rule/ADR clause being violated), with citations for both.
- **Empty report is correct when no findings exist.**

## Output format

```
[iac-discipline] file_or_section:line  SEVERITY
Finding: <one sentence>
Quote: > "<verbatim source>"
Citation: <ADR or rule file path + the specific clause>
```

Empty report is a valid result. Do not invent findings to look thorough.
