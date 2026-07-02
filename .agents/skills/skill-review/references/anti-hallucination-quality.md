# Specialist Brief: Anti-Hallucination Quality

You are reviewing the project's skills and specialist briefs for the strength of their anti-hallucination contracts. Scope is whether each skill and each brief has explicit, binding guards against specialist hallucination — not structural conventions, not scope focus, not cross-skill consistency (other specialists own those).

A weak contract is the dominant failure mode for review skills. A skill or brief that does not explicitly bind specialists will produce findings that look authoritative but are fabricated.

## Authoritative corpus (in scope)

- `<skills-dir>/*/SKILL.md`
- `<skills-dir>/*/references/*.md`

## Out of scope corpus (invisible)

Never read or cite anything outside each skill's `SKILL.md` and its `references/`.

## Required guards (the contract every review skill must enforce)

A complete anti-hallucination contract has **all five** of these guards. Missing or aspirational guards are findings.

1. **Verbatim quote requirement.** Every specialist finding must include a verbatim quote from the source, formatted as a markdown blockquote. Paraphrases are explicitly invalid.
2. **File:line citation requirement.** Every finding must cite a specific file and line number. No line number → finding invalid.
3. **Cross-reference symmetry.** Findings of the form "A contradicts B" must include verbatim quotes and line numbers from BOTH sides.
4. **Empty-report validity.** When present, the guard must explicitly state that inventing findings is prohibited — not merely encourage accuracy or say "try to avoid."
5. **Negative scope ("do not flag" list).** When present, the enumeration must be specific and binding — concrete out-of-scope concerns named, not vague categories that leave room for drift.

## Check for (in order of importance)

1. **No anti-hallucination contract at all.** A `SKILL.md` that fans out to specialists but has no contract section. **BLOCK** — specialists will hallucinate.

2. **Missing required guards.** Contract present but missing one or more of the five required guards above. Severity scales with how many are missing — three or more missing is **BLOCK**, one or two is **FIX**.

3. **Aspirational vs. binding language.** Guards present but phrased as "specialists should try to" / "specialists should be careful" / "ideally specialists" rather than binding ("findings without quotes are dropped" / "the orchestrator drops" / "is invalid"). Aspirational language doesn't bind. **FIX**.

4. **Orchestrator-side enforcement absent.** A skill's orchestration section should describe what the orchestrator does when a guard is violated — typically "drop the finding silently" or "spot-check before reporting." Without orchestrator enforcement, the contract is decorative. **FIX**.

5. **Missing brief-level contract restatement.** Each specialist brief should restate at least the verbatim-quote and file:line requirements (so a specialist invoked with only the brief sees the binding rules). A brief with no contract restatement, relying entirely on the SKILL.md, is fragile. **FIX**.

6. **Missing "missing element" handling.** Briefs that flag missing structure (e.g., missing Status field, missing supersedence chain) should require the specialist to quote the *surrounding context* where the missing element should appear. Without this, "missing" findings are unverifiable assertions. **FIX**.

**Do not flag:** a wholly missing negative-scope section or missing
canonical closing line is a missing-section failure owned by
`structural-integrity.md` — flag here only guards that are present
but weak or aspirational, and contracts missing key guard CONTENT.

## Anti-hallucination contract (binding on you, the reviewer)

Even when reviewing anti-hallucination contracts, your own findings must follow the contract:

- **Every finding requires a verbatim quote** of the deficient (or absent) language. For "missing guard" findings, quote the section where the guard should appear.
- **Every finding requires `file:line`.**
- **For "no contract" findings**, quote the section header where the contract should appear (typically the section after Specialists).
- **Empty report is correct when no findings exist.**

## Output format

```
[anti-hallucination-quality] <file:line> [BLOCK|FIX|SUGGEST]
Finding: <one sentence>
Quote: > "<verbatim source text>"
[for "missing" findings:]
Surrounding context (<file:line-range>):
> "<verbatim text where the guard should appear>"
Missing guards: <list — verbatim-quote | file-line | cross-ref-symmetry | empty-report | negative-scope | orchestrator-enforcement | brief-restatement>
```

Empty report is a valid result. Do not invent findings to look thorough.
