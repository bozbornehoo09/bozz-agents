# Specialist Brief: Cross-Skill Consistency

You are reviewing the project's skills and specialist briefs for consistent conventions across the family. Scope is whether all skills use the same severity vocabulary, verdict labels, output template structure, and aggregation patterns — not structural integrity within a single file, not contract quality, not scope focus (other specialists own those).

Inconsistency across the family is not a per-file failure; it shows up only when comparing skills. A user running `code-review` after `docs-review` should get visually similar reports — divergent severity labels or verdict shapes break the muscle memory the family is building.

## Authoritative corpus (in scope)

- `<skills-dir>/*/SKILL.md`
- `<skills-dir>/*/references/*.md`

## Out of scope corpus (invisible)

Never read or cite anything outside each skill's `SKILL.md` and its `references/`.

## Established conventions (the canon)

These are the conventions the family has adopted. Divergence is a finding.

- **Severity vocabulary:** `BLOCK` / `FIX` / `SUGGEST`. Three levels, in that case. Other vocabularies (`ERROR/WARN/INFO`, `HIGH/MEDIUM/LOW`, `🔴/🟡/🟢`) are non-canonical.
- **Verdict labels:** `READY` / `REVISE` / `READY-WITH-FIXES`. Other labels (`PASS/FAIL`, `OK/NOT OK`) are non-canonical.
- **Verdict mapping:** REVISE if any BLOCK; READY-WITH-FIXES if no BLOCK and at least one FIX; READY otherwise. A SUGGEST-only result is `READY`. This holds for a finished pass; an unfinished lens makes it REVISE whatever the findings.
- **Fan-out completeness:** defined once, in `skill-review/references/review-completeness.md`. Every skill that fans out lenses asks each lens to end with `COUNTS: BLOCK <n> FIX <n> SUGGEST <n>`, names an unfinished lens in the `failed:` field and returns REVISE for it (section 1), and finishes a split lens with a pair call (section 2), pointing to that file rather than restating it.
- **Specialist invocation:** independent specialists run in parallel through
  the host's subagent or delegation facility. Sequential invocation breaks the
  design; the facility's product-specific name is irrelevant.
- **Specialist brief location:** every brief lives in its owning skill's own `references/` subdirectory — not a shared top-level directory, not elsewhere. A skill may dispatch a sibling skill's brief by relative path (`../<skill>/references/<brief>.md`); the brief still has one owner and one location, and the dispatching skill must not keep a copy.
- **Output template anchors:** `# <Skill Name>: <subject>`, then a `Specialists run:` line, then severity sections in order BLOCK → FIX → SUGGEST, then `Verdict:` line at end.
- **Anti-hallucination contract anchor:** section heading `## Anti-hallucination contract` (or close variant). Variants like `## Hallucination prevention` or `## Quality guards` diverge from canon.
- **Negative-scope anchor:** section heading `## Do not flag` or `## What this skill is NOT` (often both — the first inside the brief, the second on the SKILL.md).
- **Empty-report closing line in briefs:** `Empty report is a valid result. Do not invent findings to look thorough.` (or close variant). (convention defined here; enforcement owned by `structural-integrity.md`)

## Check for (in order of importance)

1. **Severity vocabulary divergence.** A skill or brief using non-canonical severity labels. **BLOCK** if the divergence breaks aggregation across skills (e.g., one skill outputs `ERROR`, the orchestrator can't merge with another's `BLOCK`).

2. **Verdict label divergence.** A skill ending with a non-canonical verdict label or a non-standard mapping (e.g., `READY-WITH-FIXES` triggered by BLOCKs). **BLOCK** if the divergence breaks user expectation when running multiple skills.

3. **Output template structural divergence.** A skill whose output template changes the section order, omits the `Verdict:` line, or restructures findings in a way that breaks family visual consistency. **FIX**.

4. **Specialist invocation pattern divergence.** A skill that invokes
   specialists sequentially when parallel is appropriate, or allows specialists
   to share state when independence is required. Do not flag host-specific tool
   names. **FIX** if stylistic; **BLOCK** if it changes contract semantics.

5. **Specialist brief location divergence.** A specialist brief stored outside its owning skill's `references/` (e.g. a shared top-level directory, or `.claude/skills/foo/specialists/`), or a copy of a sibling skill's brief kept in a second skill instead of a `../<skill>/references/<brief>.md` pointer. **FIX** — relocate into the owning skill's `references/` and point to it. A relative-path dispatch of a sibling's brief is canonical; do not flag it.

6. **Anti-hallucination anchor divergence.** A skill or brief using a non-canonical heading for the contract section. The text may be fine; the anchor name is the convention. **FIX**.

7. **Fan-out completeness divergence.** A skill that fans out lenses but whose lens prompt lacks the `COUNTS:` end line, whose verdict rule lets a failed or unfinished lens through, or whose split rule has no pair call and no pointer to `review-completeness.md`. Quote the skill's prompt, verdict or split line and the matching line of `review-completeness.md`. **BLOCK** if a failed or unfinished lens can still yield `READY` or `READY-WITH-FIXES`; **FIX** otherwise (including a restated copy of the rules in place of the pointer).

8. **Inconsistent description tone in frontmatter.** SKILL.md `description:` fields should be one-line, imperative, and explain when to invoke. A skill whose description is multi-line, narrative, or describes what the skill *is* rather than when to use it. **SUGGEST**.

**Do not flag:** a missing or divergent canonical closing line in a brief is a required-section failure owned by `structural-integrity.md` — do not flag it here.

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
Convention violated: <severity-vocab | verdict-labels | verdict-mapping | output-template | invocation-pattern | brief-location | anti-hallucination-anchor | fan-out-completeness | description-tone>
```

Empty report is a valid result. Do not invent findings to look thorough.
