---
name: code-review
description: Review uncommitted changes or a specific commit/range against the project's architectural ADRs and per-package rules. Use after implementing a phase of a plan, before committing, or on a PR diff. Fans out to specialist reviewers in parallel and reports findings ranked by severity.
---

# Code Review

> **Skeleton skill.** This ships the generic orchestration, anti-hallucination contract, and verdict logic, plus **one template brief** in `references/`. It does **not** know your architecture. Add one specialist brief per architectural concern (e.g. `architecture.md`, `security.md`, `performance.md`) to `references/`, then update the Specialists table below. For a full worked instantiation, see `docs/prism-case-study.md` — the Prism project's design briefs live in the Prism repo, not here.

Review actual code against the project's architecture. What counts as a violation is defined entirely by the specialist briefs in `references/`, each citing your ADRs and rules.

## Inputs

One of:
- Uncommitted working-tree changes — default. Resolve via `git diff HEAD` and `git status`.
- A commit SHA or range — `git diff <sha>` or `git diff <base>..<head>`.
- A PR — `gh pr diff <num>`.

If the diff is large (>500 lines), ask the user whether to chunk by file group or proceed whole.

## Specialists

Each brief is a self-contained reviewer instruction file in `references/`, covering exactly one lens. Declare your briefs and run-conditions here. Replace this table with your own:

| Brief | When to run |
|---|---|
| `_brief-template.md` | Template only — copy it to create real briefs; do not run as-is |
| _(your `architecture.md`)_ | Always |
| _(your `security.md`)_ | Always |
| _(your domain brief)_ | When the diff touches that domain's paths |

Convention: keep 2–3 "always" briefs and gate the rest on changed-file paths.

## Orchestration

1. Resolve the diff. Capture `git diff` output and the list of changed files.
2. Spawn specialists in parallel via Agent (`subagent_type: general-purpose`) — one Agent call per applicable brief, all in a single message:
   ```
   Review this diff against {brief_path}.
   Changed files: {file_list}
   Diff: {diff_content}
   Anti-hallucination contract: every finding requires a verbatim quote
   AND a file:line citation. Cross-reference findings require both sides.
   An empty report is correct when no findings exist.
   Cite ADRs and rules by file path. Use the output format in the brief.
   ```
3. **Verify BLOCK findings.** Re-read the cited line for every BLOCK finding; confirm the quote matches byte-for-byte. Drop any with hallucinated quotes.
4. **Spot-check FIX/SUGGEST findings.** Verify at least 3 random findings per severity. Drop mismatches.
5. Deduplicate: if two specialists flag the same line for related reasons, merge into one finding tagged with both dimensions.
6. Rank by severity, then by file order.

## Anti-hallucination contract (binding on every specialist)

These rules are non-negotiable. The orchestrator **drops** any finding that violates them.

1. **Every finding MUST include a verbatim quote** of the offending diff line. Format: `> "exact text from the diff"`. Paraphrases are invalid.
2. **Every finding MUST cite `file:line`** — the file path and line number in the diff. No line number → finding invalid.
3. **Cross-reference findings require quotes from BOTH sides.** A finding of the form "this code violates rule X" must include the verbatim diff line AND the verbatim rule clause being violated, with file:line for both.
4. **"Missing element" findings quote the surrounding context** where the element should appear, so the absence is verifiable. Do not assert an absence without it.
5. **An empty report is the correct output when no findings exist.** Specialists must not invent findings to justify the call. "No findings in this dimension" is a complete, valid report.
6. **Out-of-scope corpus is invisible.** Each brief declares what it does NOT review (other specialists own those dimensions). Specialists must not flag concerns outside their declared lens.

## Do not flag (negative scope)

- Style, formatting, naming preferences that don't violate a Hard Rule.
- Comments, docstring content, log message phrasing.
- Test failures or flakes (those are CI's job, not a code reviewer).
- Anything outside the diff being reviewed (broader codebase context is read for understanding, not flagged unless the diff *causes* a violation there).

## Severity criteria

- **BLOCK** — violates a CRITICAL OVERRIDE / hard rule in a rule file, or contradicts an Accepted ADR. Do not merge.
- **FIX** — violates a rule but is mechanically fixable, or introduces a clear regression risk.
- **SUGGEST** — improvement that doesn't violate a rule (cleanup, naming, future-proofing). Optional.

## Output template

```
# Code Review: <commit message or "uncommitted changes">

Files: <count> changed (<+adds>/<-dels>)
Specialists run: <your brief names>

## BLOCK
- <path>:<line> [<dimension>]
  > "<verbatim offending line>"
  <why it violates the rule>
  → <rule/ADR file> "<verbatim rule clause>"

## FIX
- ...

## SUGGEST
- ...

Verdict: REVISE | READY-WITH-FIXES | READY
```

## What this skill is NOT

- Not a linter or formatter — assume those run separately.
- Not a test runner — flag missing tests but do not execute the suite.
- Not a substitute for human review on enterprise-bound code. In a personal project the fan-out is enough; on shared/critical code, a human still reads the diff.
- Not a generic SOLID/DRY checker — every check must trace to a brief in `references/` that you wrote for your architecture.
