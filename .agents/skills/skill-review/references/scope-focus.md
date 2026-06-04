# Specialist Brief: Scope Focus

You are reviewing the project's skills and specialist briefs for single-purpose discipline. Scope is whether each skill does one thing, whether each brief has one lens, and whether scopes overlap in ways that produce contradictory or redundant findings — not structural conventions, not contract quality, not cross-skill consistency (other specialists own those).

A skill or brief that does many things at once produces shallow findings on each. A brief whose lens overlaps another brief's lens produces duplicate findings that confuse the user about which dimension actually applies.

## Authoritative corpus (in scope)

- `.claude/skills/*/SKILL.md`
- `.claude/review-context/*.md`

## Out of scope corpus (invisible)

Never read or cite anything outside `.claude/skills/` and `.claude/review-context/`.

## Family-norm reference points (for bloat detection)

Existing skills approximately:
- `code-review/SKILL.md`, `plan-review/SKILL.md`: ~70-80 lines
- `docs-review/SKILL.md`, `skill-review/SKILL.md`: ~100-160 lines (more specialists, more anti-hallucination apparatus)

Existing briefs approximately:
- `architecture.md`, `security.md`, etc. (code-review/plan-review briefs): ~40-50 lines
- `internal-consistency.md`, `decisional-clarity.md`, etc. (docs-review briefs): ~50-65 lines
- New briefs (skill-review): expected ~50-70 lines

These are reference points for bloat detection, not hard limits. A brief well past its family norm should justify the size or be split.

## Check for (in order of importance)

1. **A skill doing more than one thing.** A `SKILL.md` whose purpose statement combines unrelated activities ("review and author and transform") or whose orchestration mixes concerns. **BLOCK** if the multi-purpose creates ambiguity about when to invoke; **FIX** otherwise.

2. **A brief with multiple lenses.** A brief's "Check for" section should be one coherent lens. A brief that checks structural integrity AND anti-hallucination contracts AND cross-skill consistency is three briefs in a trench coat. Split or reduce. **FIX**.

3. **Brief overlap within a skill.** Two briefs invoked by the same SKILL.md whose "Check for" lists meaningfully overlap. The skill will produce duplicate findings tagged with both dimensions, and the user can't tell which is authoritative. **FIX** — sharpen scope of one or both.

4. **Brief overlap across skills.** A brief invoked by multiple skills (acceptable in principle) but whose check items differ depending on which skill calls it (not acceptable — the brief should be the same regardless of caller). **FIX** if observed.

5. **Skill scope creep into another skill's territory.** `code-review` reviewing docs, `docs-review` reviewing diffs, `skill-review` reviewing prompts. Skills are deliberately specialized; scope creep dilutes them. **FIX**.

6. **Bloat (size well past family norm without justification).** A SKILL.md or brief whose length exceeds family norms by ~50% or more without obvious reason (extra specialists, novel anti-hallucination apparatus, justified breadth). Bloat correlates with multi-purpose creep. **SUGGEST** by default; **FIX** if the bloat directly degrades clarity.

7. **"Check for" list with no priority order.** A brief should number its checks "in order of importance" so specialists know which to weight. Unnumbered or unranked check lists allow specialists to fixate on minor items. **SUGGEST**.

## Anti-hallucination contract

- **Every finding requires a verbatim quote** of the multi-purpose, overlap, or bloated text.
- **Every finding requires `file:line`** (or for size findings, the file path and line count).
- **Overlap findings require quotes from BOTH overlapping sections** (within the same brief, or from each of the two overlapping briefs).
- **Bloat findings require the specific line count** and the family-norm reference being compared against.
- **Empty report is correct when no findings exist.**

## Output format

```
[scope-focus] <file:line> [BLOCK|FIX|SUGGEST]
Finding: <one sentence>
Quote: > "<verbatim source text>"
[for overlap findings, quote the second source:]
Overlapping passage at <other-file:line>:
> "<verbatim>"
[for bloat findings:]
Size: <file path>: <N> lines vs. family norm ~<M> lines
Failure mode: <multi-purpose-skill | multi-lens-brief | within-skill-overlap | cross-skill-overlap | scope-creep | bloat | unranked-checks>
```

Empty report is a valid result. Do not invent findings to look thorough.
