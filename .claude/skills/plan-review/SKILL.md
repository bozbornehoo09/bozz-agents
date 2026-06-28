---
name: plan-review
description: Review an implementation plan against the project's architectural ADRs and per-package rules before code is written. Use when the user has drafted a plan markdown file (in docs/, work_tracker/, or pasted inline) and wants it stress-tested against architectural constraints. Fans out to specialist reviewers in parallel.
---

# Plan Review

> **Skeleton skill.** This ships the generic orchestration, anti-hallucination contract, and verdict logic, plus **one template brief** in `references/`. It does **not** know your architecture. Add one specialist brief per architectural concern (e.g. `architecture.md`, `security.md`, `performance.md`) to `references/`, then update the Specialists table below. For how to add briefs for your architecture, see `docs/customizing.md`.

Stress-test an implementation plan against the architecture **before** code lands — catching boundary/port violations, missed cross-cutting requirements, and decisions that need an ADR, at design time rather than at PR time. What counts as a violation is defined entirely by the briefs you add to `references/`.

## Inputs

- A plan: file path (e.g. `docs/implementation_plan.md`), pasted markdown, or "the plan we just discussed in this session".
- Optional: package scope hint (e.g. "this touches the API and the infra layer"). If not given, infer from the plan's targets.

## Specialists

Each brief is a self-contained reviewer instruction file in `references/`, covering exactly one lens. Spawn them in parallel via the Agent tool with `subagent_type: general-purpose` (or `agent-teams:team-reviewer` if running inside a `team-spawn`).

Declare your briefs and their run-conditions here. Replace this table with your own:

| Brief | When to run |
|---|---|
| `_brief-template.md` | Template only — copy it to create real briefs; do not run as-is |
| _(your `architecture.md`)_ | Always |
| _(your `security.md`)_ | Always |
| _(your domain brief)_ | When the plan touches that domain |

Convention: keep 2–3 "always" briefs (the load-bearing lenses) and gate the rest on scope.

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
4. **"Missing element" findings quote the surrounding context** where the element should appear, so the absence is verifiable. Do not assert an absence without it.
5. **An empty report is the correct output when no findings exist.** Specialists must not invent findings to justify the call.
6. **Out-of-scope corpus is invisible.** Each brief declares what it does NOT review. Specialists must not flag concerns outside their declared lens.

## Do not flag (negative scope)

- Plan formatting, prose style, section ordering preferences.
- Speculative concerns the plan doesn't actually commit to ("what if they later decide to…").
- Anything the plan explicitly defers to a future iteration with an honest "out of scope" note.
- Implementation details below the plan's stated abstraction level (those are `code-review`'s job after the plan is implemented).

## Severity criteria

- **BLOCK** — the plan contradicts an Accepted ADR or a CRITICAL OVERRIDE / hard rule, or commits to a *new* architectural decision with no ADR. Resolve before building.
- **FIX** — the plan violates a rule but is correctable in the plan (a missed cross-cutting requirement, a boundary the plan can honor with a tweak).
- **SUGGEST** — improvement that doesn't violate a rule (sequencing, clarity, future-proofing). Optional.

## Output template

```
# Plan Review: <plan title>

Scope: <inferred packages>
Specialists run: <your brief names>

## BLOCK
- [<dimension>] <finding> — <ADR/rule citation>
- ...

## FIX
- [<dimension>] <finding> — <citation>
- ...

## SUGGEST
- [<dimension>] <finding> — <citation>
- ...

Verdict: REVISE
```

## What this skill is NOT

- Not a code reviewer — the plan has no code yet. Use `code-review` after implementation.
- Not a substitute for ADR creation. If the plan implies a *new* architectural decision (alternatives genuinely considered, binds future work), surface that as a BLOCK with "needs ADR" rather than rubber-stamping it.
- Not a generic SOLID/DRY checker — every check must trace to a brief in `references/` that you wrote for your architecture.
