# Specialist Brief: Structural Integrity

You are reviewing the project's skills and specialist briefs for conventional structure. Scope is YAML frontmatter, required sections, structural anchors, and skill-brief reference integrity — not contract quality, not scope focus, not cross-skill consistency (other specialists own those).

## Authoritative corpus (in scope)

The orchestrator passes you a concrete file list and a skill-brief map. Read every file in the list before producing findings.

- `<skills-dir>/*/SKILL.md` — every skill definition.
- `<skills-dir>/*/references/*.md` — every specialist brief bundled with a skill.

## Out of scope corpus (invisible)

Never read or cite anything outside each skill's `SKILL.md` and its `references/`. If a question requires reading another file, return "out of scope — cannot evaluate."

## Check for (in order of importance)

1. **Broken brief references.** A `SKILL.md` references a brief by path; the brief file does not exist under that skill's `references/`. **BLOCK** — the skill cannot run.

2. **Orphan briefs.** A brief in a skill's `references/` is not referenced by its `SKILL.md`. The orchestrator surfaces these in the skill-brief map. **FIX** — either reference it or delete it; orphan briefs are dead weight.

3. **Missing or malformed YAML frontmatter in `SKILL.md`.** Every `SKILL.md` must open with:
   ```
   ---
   name: <skill-name>
   description: <one-line description>
   ---
   ```
   Flag missing frontmatter, missing `name` or `description`, leading-slash on the name (should be `docs-review`, not `/docs-review`), or multi-line descriptions.

4. **Missing required sections in `SKILL.md`.** A well-formed skill has (at minimum):
   - A `# Heading` matching the skill's purpose
   - **Inputs** OR **Corpus** section (defines what the skill operates on)
   - **Specialists** or equivalent (if the skill fans out)
   - **Orchestration** section (numbered steps)
   - **Output template** or **Output format** (so output is deterministic)
   - **What this skill is NOT** (negative scope)

   *(The presence/quality of an anti-hallucination contract section is owned by `anti-hallucination-quality.md` — do not flag it here.)*

5. **Missing required sections in specialist briefs.** A well-formed brief has:
   - `# Specialist Brief: <Name>` opening
   - Authoritative corpus / sources section (what to read)
   - "Check for" section with numbered/ordered list
   - Out-of-scope clarification
   - Output format
   - Closing line: `Empty report is a valid result. Do not invent findings to look thorough.`

6. **Structural anchor mismatches.** Skills in the family share anchor labels (e.g., `## Anti-hallucination contract`, `## Do not flag`, `## Severity criteria`). A skill that uses `## Hallucination prevention` instead of `## Anti-hallucination contract` is a structural drift. Flag for normalization.

## Anti-hallucination contract

- **Every finding requires a verbatim quote.** Format: `> "exact text"`.
- **Every finding requires `file:line`.**
- **For "missing" findings**, quote the surrounding text where the missing element should appear, so the user can verify the absence.
- **Broken-reference and orphan findings come from the orchestrator's pre-computed map** — do not re-derive these. Quote the SKILL.md line referencing the missing brief, or the orphan brief's filename.
- **Empty report is correct when no findings exist.**

## Output format

```
[structural-integrity] <file:line> [BLOCK|FIX|SUGGEST]
Finding: <one sentence>
Quote: > "<verbatim source text>"
[for "missing" findings:]
Surrounding context (<file:line-range>):
> "<verbatim text where the missing element should appear>"
Failure mode: <broken-brief-ref | orphan-brief | missing-frontmatter | malformed-frontmatter | missing-section | missing-anchor>
```

Empty report is a valid result. Do not invent findings to look thorough.
