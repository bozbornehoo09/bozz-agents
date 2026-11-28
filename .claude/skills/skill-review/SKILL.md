---
name: skill-review
description: Review a project's Agent Skills (SKILL.md files and their bundled references/ briefs) against quality conventions — structural integrity, anti-hallucination contract quality, scope focus, and cross-skill consistency. Use after creating or modifying a skill or specialist brief, before committing. Fans out to four specialists in parallel.
---

# Skill Review

Stress-test a project's AI-tooling set against itself. Catches structural drift (missing frontmatter, missing required sections), weak anti-hallucination contracts that allow specialist hallucination, scope bloat or specialist overlap, and divergence between skills on shared conventions (severity vocabulary, output formats, verdict labels).

Fourth member of the review-skill family:

| Skill | Reviews | Against |
|---|---|---|
| `docs-review` | authoritative docs | each other |
| `plan-review` | implementation plans | docs |
| `code-review` | diffs | docs |
| `skill-review` (this) | skills + specialist briefs | quality conventions |

Self-review is allowed: skill-review can review itself. The orchestrator is the same skill being reviewed; this is recursive but not paradoxical. Findings about skill-review's own files are reported the same as findings about any other skill.

## Corpus (exhaustive — do not infer)

Skills follow the [Agent Skills](https://agentskills.io/specification) open standard: a skill is a directory containing a `SKILL.md`, optionally with `references/`, `scripts/`, and `assets/` subdirectories. The skills directory is the one the host tool reads — `.claude/skills/` (Claude Code), `.agents/skills/` (Codex), `.cursor/skills/` (Cursor), or a path declared in the project's context manifest.

**In scope.** Specialists read these as needed.

- `<skills-dir>/*/SKILL.md` — every skill definition.
- `<skills-dir>/*/references/*.md` — every specialist brief or reference file bundled with a skill.

**Out of scope.** Never reviewed by this skill.

- `<skills-dir>/*/scripts/**`, `<skills-dir>/*/assets/**` — executable code and static assets; not markdown contracts.
- Rule files, ADRs, strategy, architecture, orientation (`docs/**`, `.claude/rules/**`, `CLAUDE.md`, `AGENTS.md`) — `docs-review` reviews these.

**Measurement input.** The orchestrator also runs this skill's bundled `scripts/measure_skills.py` (standard-library Python 3) and hands its output to every specialist. The script is not reviewed; its table and limit lines are evidence that `structural-integrity` and `scope-focus` may cite.

If the user points at a file not covered, stop and ask. Do not guess scope.

## Specialists

Four briefs. All four run on every invocation. Each lives in this skill's `references/` directory.

| Brief | Lens | Looks for |
|---|---|---|
| `structural-integrity.md` | Conventional structure | Missing or malformed YAML frontmatter (required `name`/`description`; `name` must be lowercase-kebab, ≤64 chars, and match the parent directory); missing required sections for the skill's family (review fan-out skills: Inputs/Corpus, Specialists, Orchestration, Output template, What this skill is NOT; single-agent authoring skills: Scope, Steps, Pause-for-confirmation rules, Style, Output format where a structured report is emitted; briefs: their equivalents); skill-references-brief integrity (every brief referenced by a SKILL.md exists under that skill's `references/`; every brief in a skill's `references/` is referenced by its SKILL.md — orphan briefs are dead weight). |
| `anti-hallucination-quality.md` | Contract strength | Skill or brief that lacks an explicit anti-hallucination contract; contract present but missing key guards (verbatim-quote requirement, file:line citation, empty-report-is-correct, negative-scope "do not flag" list); contract guards that are aspirational ("specialists should be careful") rather than binding ("findings without a quote are dropped"). |
| `scope-focus.md` | Single-purpose discipline | A skill doing more than one thing (review + author + transform); a brief whose "Check for" list spans multiple lenses that should be split; bloat (skill body over the spec's recommended ~500-line ceiling, or a brief well over family-norm length, without justification); overlap between briefs within a skill, or between skills. |
| `cross-skill-consistency.md` | Family conventions | Severity vocabulary divergence (one skill uses BLOCK/FIX/SUGGEST, another uses ERROR/WARN/INFO); verdict label divergence (READY / REVISE / READY-WITH-FIXES vs. PASS / FAIL); output template structural divergence; aggregation pattern divergence; a fan-out skill not following `review-completeness.md`. |

`references/review-completeness.md` is not a brief. It is the review family's one definition of what an unfinished lens and a split lens do; review skills point to it, and `cross-skill-consistency.md` checks that they follow it.

## Anti-hallucination contract (binding on every specialist)

These rules are non-negotiable. The orchestrator **drops** any finding that violates them.

1. **Every finding MUST include a verbatim quote.** Format: `> "exact text from file"`. Paraphrases are invalid.
2. **Every finding MUST cite `file:line`.** No line number → finding invalid.
3. **Cross-reference findings require quotes from BOTH sides** with both file:line citations.
4. **"Missing" findings require quoting the surrounding context** where the missing element should appear, so the user can verify the absence.
5. **An empty report is the correct output when no findings exist.** Do not invent findings.
6. **Out-of-scope corpus is invisible.** Specialists do not read or cite anything outside the skills directory's `SKILL.md` and `references/*.md` files. The one exception is the measurement output the orchestrator hands them.
7. **Specialists must read every in-scope file before producing findings.** No grep-and-go.
8. **Findings built on the measurement output** — size, shared passages, description overlap, branch sections — cite the measured file as `<file>:1` and copy, exactly, the table row or the `OVER` / `PAGE` / `CANDIDATE` line they rest on.

## Do not flag (negative scope)

- Style, grammar, prose quality, word choice.
- Markdown formatting, unless it produces semantic ambiguity.
- The content the skill reviews (that's docs-review / plan-review / code-review's job — skill-review reviews the *skill itself*, not what the skill would surface).
- Anything outside the skills directory's `SKILL.md` and `references/*.md` files.
- Stylistic preferences that don't violate a falsifiable convention.

## Orchestration

1. **Verify corpus and measure.** List every `<skills-dir>/*/SKILL.md` and every `<skills-dir>/*/references/*.md`. If the directory is empty or missing, stop and ask. Then run `python3 -I <this skill's directory>/scripts/measure_skills.py <skills-dir>` (add `--skill <name>` per skill under review on a targeted pass; it still compares against every skill) and keep its output for every specialist. If Python is unavailable, say so in the report and continue without it.
2. **Build the skill-brief map.** For each `SKILL.md`, extract referenced brief paths. Compute:
   - Briefs referenced by their owning SKILL.md, or by a sibling SKILL.md through `../<skill>/references/<brief>.md` → live.
   - Briefs present in a skill's `references/` but referenced by no SKILL.md → orphans (`structural-integrity` finding, FIX severity).
   - Briefs referenced by a SKILL.md but not present at the referenced path (that skill's `references/`, or the sibling's for a relative-path dispatch) → broken references (`structural-integrity` finding, BLOCK severity).
3. **Spawn all four specialists in parallel** using the host agent's subagent
   or delegation facility. Use one parallel fan-out. Retry a call that fails
   on a rate limit at lower parallelism and any other failed call once. If a
   lens's corpus will not fit one specialist's context, split it and finish
   it with a pair call (`references/review-completeness.md` section 2). Each
   specialist gets:
   ```
   Review the project's skills and specialist briefs against {brief_path}.
   Concrete corpus:
   {full file list}
   Skill-brief map (built by orchestrator):
   {map of skill → referenced briefs, plus orphan list and broken-ref list}
   Measurement output (scripts/measure_skills.py):
   {its tables and OVER / PAGE / CANDIDATE lines}
   Anti-hallucination contract: every finding requires a verbatim quote
   AND a file:line citation. Cross-reference findings require both sides.
   "Missing" findings require quoting the surrounding context where the
   missing element should appear.
   An empty report is correct when no findings exist.
   Out-of-scope corpus is invisible; do not read or cite it.
   Use the output format in the brief. End with the line
   'COUNTS: BLOCK <n> FIX <n> SUGGEST <n>', an empty report too.
   ```
4. **Verify BLOCK findings.** For each BLOCK, re-read what it cites — the file line, or for a finding built on measurements, the output kept in step 1 — and confirm the quote matches byte-for-byte. Drop any with hallucinated quotes.
5. **Spot-check FIX/SUGGEST findings.** Verify at least 3 random findings per severity. Drop mismatches.
6. **Aggregate.**
   - Add orchestrator-detected findings (orphan briefs, broken references) to `structural-integrity` group.
   - Name any lens that failed or came back unfinished in the `failed:` field of `Specialists run:`.
   - Group by severity (BLOCK / FIX / SUGGEST).
   - Within severity, group by specialist dimension.
   - Deduplicate cross-specialist findings on the same line.
7. **End with a one-line verdict.** REVISE if any BLOCK; READY-WITH-FIXES if no BLOCK and at least one FIX; READY otherwise. An unfinished lens makes it REVISE (`references/review-completeness.md` section 1).

## Severity criteria

- **BLOCK** — A skill that, if run, would produce broken or misleading output. References a non-existent brief; has invalid required frontmatter (missing `name`/`description`, or `name` that won't validate); has no anti-hallucination contract; specialists with overlapping scopes that produce contradictory findings; severity vocabulary that breaks aggregation.
- **FIX** — Quality issue that is mechanically resolvable. Orphan brief, bloated section, a measured limit crossed (`OVER` or `PAGE`), missing concrete example, inconsistent severity label, missing required structural anchor.
- **SUGGEST** — Improvement that doesn't violate a convention. Better example, clearer phrasing, tighter scope language.

## Output template

The block below illustrates the format only. `foo` and `wibble` are placeholder skill names and the findings are fabricated for the example — real output cites real files in the project's skills directory.

```
# Skill Review: <skills directory>

Skills reviewed: <count>
Briefs reviewed: <count>
Specialists run: structural-integrity, anti-hallucination-quality, scope-focus, cross-skill-consistency; failed: none

## BLOCK
- [structural-integrity] skills/foo/SKILL.md:42
  > "Specialist briefs: bar.md, baz.md, qux.md"
  Brief `qux.md` does not exist under skills/foo/references/. Skill cannot run.

## FIX
- [anti-hallucination-quality] skills/foo/references/widget.md:55
  > "Specialists should try to avoid hallucinating findings."
  Aspirational language; not a binding contract. Replace with verbatim-quote requirement and "findings without quotes are dropped."

## SUGGEST
- [scope-focus] skills/wibble/SKILL.md:88
  > "Also consider checking the user's intent before running."
  Out-of-scope creep. Skill should focus on its declared purpose; intent-checking is a separate concern.

Verdict: REVISE
```

## What this skill is NOT

- Not a code reviewer for any `scripts/` a skill bundles. The Agent Skills standard allows executable scripts; skill-review audits the `SKILL.md` contract and its `references/`, not bundled code. Run a normal code review on scripts.
- Not a substitute for `update-skills`. That skill evolves the tooling; this one audits it.
- Not a content reviewer. Whether the skill is *useful* is a judgment for the user; whether it is *well-formed* is what this skill checks.
- Not a reviewer for rules, ADRs, or any non-skill content.
