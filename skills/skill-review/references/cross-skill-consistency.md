# Specialist Brief: Cross-Skill Consistency

You are reviewing the project's skills and specialist briefs for consistent conventions across the family. Scope is whether all skills use the same severity vocabulary, verdict labels, output template structure, and aggregation patterns — not structural integrity within a single file, not contract quality, not scope focus (other specialists own those).

Inconsistency across the family is not a per-file failure; it shows up only when comparing skills. A user running `code-review` after `docs-review` should get visually similar reports — divergent severity labels or verdict shapes break the muscle memory the family is building.

## Authoritative corpus (in scope)

- `.claude/skills/*/SKILL.md`
- `.claude/review-context/*.md`

## Out of scope corpus (invisible)

Never read or cite anything outside `.claude/skills/` and `.claude/review-context/`.

## Established conventions (the canon)

These are the conventions the family has adopted. Divergence is a finding.

- **Severity vocabulary:** `BLOCK` / `FIX` / `SUGGEST`. Three levels, in that case. Other vocabularies (`ERROR/WARN/INFO`, `HIGH/MEDIUM/LOW`, `🔴/🟡/🟢`) are non-canonical.
- **Verdict labels:** `READY` / `REVISE` / `READY-WITH-FIXES`. Other labels (`PASS/FAIL`, `OK/NOT OK`) are non-canonical.
- **Verdict mapping:** no BLOCKs → `READY`; only FIX/SUGGEST → `READY-WITH-FIXES`; any BLOCK → `REVISE`.
- **Specialist invocation:** parallel via Agent (typically `subagent_type: general-purpose`), single message with multiple tool calls. Sequential invocation breaks the design.
- **Specialist brief location:** `.claude/review-context/`. Not under each skill's directory; not elsewhere.
- **Output template anchors:** `# <Skill Name>: <subject>`, then a `Specialists run:` line, then severity sections in order BLOCK → FIX → SUGGEST, then `Verdict:` line at end.
- **Anti-hallucination contract anchor:** section heading `## Anti-hallucination contract` (or close variant). Variants like `## Hallucination prevention` or `## Quality guards` diverge from canon.
- **Negative-scope anchor:** section heading `## Do not flag` or `## What this skill is NOT` (often both — the first inside the brief, the second on the SKILL.md).
- **Empty-report closing line in briefs:** `Empty report is a valid result. Do not invent findings to look thorough.` (or close variant).

## Check for (in order of importance)

1. **Severity vocabulary divergence.** A skill or brief using non-canonical severity labels. **BLOCK** if the divergence breaks aggregation across skills (e.g., one skill outputs `ERROR`, the orchestrator can't merge with another's `BLOCK`).

2. **Verdict label divergence.** A skill ending with a non-canonical verdict label or a non-standard mapping (e.g., `READY-WITH-FIXES` triggered by BLOCKs). **BLOCK** if the divergence breaks user expectation when running multiple skills.

3. **Output template structural divergence.** A skill whose output template changes the section order, omits the `Verdict:` line, or restructures findings in a way that breaks family visual consistency. **FIX**.

4. **Specialist invocation pattern divergence.** A skill that invokes specialists sequentially when parallel is appropriate, or invokes them via a different mechanism than `Agent` with `subagent_type`. **FIX** if it's a stylistic choice; **BLOCK** if it changes the contract semantics (e.g., specialists pass state to each other).

5. **Specialist brief location divergence.** A specialist brief stored under the skill's own directory (`.claude/skills/foo/specialists/`) instead of `.claude/review-context/`. **FIX** — relocate.

6. **Anti-hallucination anchor divergence.** A skill or brief using a non-canonical heading for the contract section. The text may be fine; the anchor name is the convention. **FIX**.

7. **Closing-line divergence in briefs.** A brief omitting the canonical closing line (or using a substantively different one). The line is small but reinforces the empty-report-is-correct guard. **SUGGEST**.

8. **Inconsistent description tone in frontmatter.** SKILL.md `description:` fields should be one-line, imperative, and explain when to invoke. A skill whose description is multi-line, narrative, or describes what the skill *is* rather than when to use it. **SUGGEST**.

## Anti-hallucination contract

- **Every finding requires a verbatim quote** of the diverging text.
- **Every finding requires `file:line`.**
- **Cross-skill comparisons require quotes from at least two skills** with file:line for each, so the divergence is concrete.
- **"Canonical" claims must be backed by quoting at least one skill that follows the convention** — do not assert "the canon is X" without showing it in use.
- **Empty report is correct when no findings exist.** If all skills agree on conventions, this brief produces no output.

## Output format

```
[cross-skill-consistency] <file:line> [BLOCK|FIX|SUGGEST]
Finding: <one sentence>
Diverging quote: > "<verbatim source text>"
Canonical example at <other-file:line>:
> "<verbatim canonical convention>"
Convention violated: <severity-vocab | verdict-labels | verdict-mapping | output-template | invocation-pattern | brief-location | anti-hallucination-anchor | closing-line | description-tone>
```

Empty report is a valid result. Do not invent findings to look thorough.
