---
name: plan-review
description: Review an implementation plan against the project's architectural ADRs and per-package rules before code is written. Use when the user has drafted a plan markdown file (in docs/, work_tracker/, or pasted inline) and wants it stress-tested against architectural constraints. Fans out to specialist reviewers in parallel.
---

# Plan Review

> **Worked example.** The specialist briefs under `references/` encode the **Prism** project's architecture and are included as a template. Replace them with briefs for your own architecture — see `docs/customizing.md`. The orchestration, fan-out, and anti-hallucination contract below are project-agnostic and stay as-is.

Stress-test an implementation plan against the architecture **before** code lands. In the Prism example, that means catching port violations, missed tenancy/domain scoping, two-pass cognition skips, and Cloud Workflows-vs-Vertex-Pipelines confusion at design time, not at PR time.

## Inputs

- A plan: file path (e.g. `docs/implementation_plan.md`), pasted markdown, or "the plan we just discussed in this session".
- Optional: package scope hint (e.g. "this touches `src/inference_worker/` and `infrastructure/terraform/services/`"). If not given, infer from the plan's targets.

## Specialists

Each brief lives in `references/`. Spawn them in parallel via the Agent tool with `subagent_type: general-purpose` (or `agent-teams:team-reviewer` if running inside a `team-spawn`). Always run the first three; add the rest based on scope.

| Brief | When to run |
|---|---|
| `architecture.md` | Always |
| `security.md` | Always |
| `ml-contracts.md` | Always (Prism is an ML platform — Model Router/AdapterPack discipline is load-bearing even on UI work) |
| `performance-cost.md` | Plan touches inference pipelines, Pub/Sub, Workflows, vector store, or any frontier model invocation |
| `iac-discipline.md` | Plan touches `infrastructure/terraform/**`, IAM, schedules, or service accounts |
| `testing.md` | Plan adds/changes tests, or skips testing entirely on a non-trivial change |

## Orchestration

1. Read the plan once. Note its package scope and which specialists apply.
2. Send the **same prompt shape** to each specialist in a single message (parallel Agent calls via `subagent_type: general-purpose`):
   ```
   Review this plan against {brief_path}. Plan content: {plan}.
   Anti-hallucination contract: every finding requires a verbatim quote
   AND a section:line (or file:line) citation. Cross-reference findings
   require both sides. An empty report is correct when no findings exist.
   Cite ADRs and rules by file path. Use the output format in the brief.
   ```
3. **Verify BLOCK findings.** Re-read the cited line for every BLOCK finding; confirm the quote matches byte-for-byte. Drop any with hallucinated quotes.
4. **Spot-check FIX/SUGGEST findings.** Verify at least 3 random findings per severity. Drop mismatches.
5. Aggregate findings into one report:
   - Group by severity (BLOCK / FIX / SUGGEST).
   - Within severity, group by dimension.
   - Each finding cites its specialist brief and the ADR/rule that justifies it.
6. End with a one-line verdict: `READY` (no BLOCKs), `REVISE` (BLOCKs present), or `READY-WITH-FIXES` (only FIX/SUGGEST).

## Anti-hallucination contract (binding on every specialist)

These rules are non-negotiable. The orchestrator **drops** any finding that violates them.

1. **Every finding MUST include a verbatim quote** of the plan text being flagged. Format: `> "exact text from the plan"`. Paraphrases are invalid.
2. **Every finding MUST cite `section:line`** (or `file:line` if the plan is a markdown file path). No line/section number → finding invalid.
3. **Cross-reference findings require quotes from BOTH sides.** A finding of the form "this plan step violates rule X" must include the verbatim plan text AND the verbatim rule clause being violated, with citations for both.
4. **An empty report is the correct output when no findings exist.** Specialists must not invent findings to justify the call.
5. **Out-of-scope corpus is invisible.** Each brief declares what it does NOT review. Specialists must not flag concerns outside their declared lens.

## Do not flag (negative scope)

- Plan formatting, prose style, section ordering preferences.
- Speculative concerns the plan doesn't actually commit to ("what if they later decide to…").
- Anything the plan explicitly defers to a future iteration with an honest "out of scope" note.
- Implementation details below the plan's stated abstraction level (those are `code-review`'s job after the plan is implemented).

## Output template

```
# Plan Review: <plan title>

Scope: <inferred packages>
Specialists run: architecture, security, ml-contracts, ...

## BLOCK
- [architecture] <finding> — <ADR/rule citation>
- ...

## FIX
- [security] <finding> — <citation>
- ...

## SUGGEST
- [performance-cost] <finding> — <citation>
- ...

Verdict: REVISE
```

## What this skill is NOT

- Not a code reviewer — the plan has no code yet. Use `code-review` after implementation.
- Not a substitute for ADR creation. If the plan implies a *new* architectural decision (alternatives genuinely considered, binds future work), surface that as a BLOCK with "needs ADR" rather than rubber-stamping it.
- Not a generic SOLID/DRY checker — those are inside `architecture.md`, scoped to Prism's actual port boundaries.
