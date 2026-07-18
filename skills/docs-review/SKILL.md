---
name: docs-review
description: Review the project's authoritative docs (ADRs, per-package rules, architecture design, strategy) against each other for internal consistency, strategy-architecture coherence, decisional clarity, and temporal decay. Use after editing any ADR, rule file, strategy doc, or the architecture design — before committing. Fans out to four specialists in parallel.
---

# Docs Review

Stress-test the project's authoritative documentation against itself. Catches contradictions between ADRs, missed propagation when a concept lands in one doc but not its dependents, strategy claims with no architectural mechanism, unfalsifiable Hard Rules, and time-decaying claims that are not flagged as such.

Third member of the review-skill family:

| Skill | Reviews | Against |
|---|---|---|
| `docs-review` (this) | authoritative docs | each other |
| `plan-review` | implementation plans | docs |
| `code-review` | diffs | docs |

## Corpus (exhaustive — do not infer)

**In scope.** Specialists read these as needed. The orchestrator expands the globs at invocation time and passes the resulting concrete file list to every specialist.

- `docs/decisions/*.md` — every ADR file (excluding `README.md` per "Out of scope" below).
- `docs/architecture/*.md` and `docs/architecture/*.mermaid` — every architecture doc and diagram.
- `docs/strategy/*.md` — every strategy doc at the top level (the `research/` subdirectory is excluded; see below).
- Rule files: use the manifest-declared `rules` layer. If absent, prefer a
  canonical `rules/` directory, then fall back to a host convention such as
  `.agents/rules/` or `.claude/rules/`. If the selected path is generated, use
  the canonical source named by its marker. Generated copies are out of scope.
- Orientation file: use `project.orientation` or the manifest-declared
  `orientation` layer. If absent, resolve the host's loaded orientation file
  (`AGENTS.md`, `CLAUDE.md`, or equivalent). If it names a generated source such
  as `ORIENTATION.md`, review that canonical source instead.

**Out of scope.** Never reviewed by this skill, even if cited by an in-scope doc.

- `docs/strategy/research/**` — preserved source artifacts; immutable by convention; reviewed via the doc that *cites* them.
- `docs/research/**` — research memos; not authoritative.
- `docs/open_questions.md` — unresolved by definition; cannot be inconsistent with anything.
- `docs/implementation_plan.md` — `plan-review`'s scope.
- `work_tracker/**` — temporal log.
- `prompts/**` — operational, not architectural.

If the user points at a doc not covered by either list, stop and ask. Do not guess scope.

### Corpus maintenance

Globs auto-include new files within existing directories — adding a new ADR or a new rule file requires no skill update. **Adding a new authoritative directory does require a skill update** (e.g., introducing `docs/specs/` or `docs/runbooks/`). When that happens, update this section in `SKILL.md` and the corpus list in each of the four specialist briefs. New top-level directories are rare events; the skill itself documents what counts as authoritative.

### Status manifest (`docs/decisions/README.md`)

`docs/decisions/README.md` is the authoritative status manifest. It carries a per-ADR line of the form:

```
- [ADR-NNNN](NNNN-slug.md) — Title — Status
```

…where Status is one of `Accepted`, `Proposed`, `Superseded by ADR-NNNN`, `Deprecated`. The ADR file body's `**Status:**` field is the underlying source of truth; the README mirrors it.

**The orchestrator builds and verifies the manifest before fanning out** (see Orchestration step 1). The verified manifest is passed to every specialist. Specialists do not re-parse the README — they consume the manifest the orchestrator gives them.

The README itself is **not subject to content review** — only its accuracy as a manifest is checked, and that check is owned by the orchestrator (with mismatches surfaced as `internal-consistency` findings).

### Superseded, deprecated, and proposed ADRs

ADR status lives in the `**Status:**` field inside the file body — it is **not** encoded in the filename. Filenames are stable; status is mutable.

Per-specialist body-read scope (drives what the specialist must actually `Read` in full):

| Status | internal-consistency | strategy-architecture-coherence | decisional-clarity | temporal-decay |
|---|---|---|---|---|
| `Accepted` | full body | full body | full body | full body |
| `Superseded` / `Deprecated` | skip body | skip body | Status line + supersedence header only | skip body |
| `Proposed` / `Draft` | skip body | skip body | full body (decisional clarity still applies; check that no doc cites it as authoritative) | skip body |

Non-Accepted ADRs are present in the manifest so specialists know they exist (for citation-check purposes — "is a current rule citing this non-Accepted ADR as authoritative?"), but their content does not need to be read in full unless the table above says so.

A superseded ADR with a missing or broken supersedence chain (no `**Supersedes:** ADR-NNNN` on the new ADR, or no `**Status: Superseded by ADR-NNNN**` on the old one) is a `decisional-clarity` finding.

## Specialists

Four briefs. All four run on every invocation — the corpus is small enough that conditional execution adds friction without saving cost. Each brief lives in `references/`.

| Brief | Lens | Looks for |
|---|---|---|
| `internal-consistency.md` | Cross-doc factual agreement | Two in-scope docs that make contradictory claims; an ADR cited by a rule file with the wrong number, status, or summary; a concept added to one doc that should propagate to dependents but did not (e.g., a new architecture section not reflected in the rule files it constrains; a cross-cutting ADR — tenancy, auth — not enforced in every rule file it binds). |
| `strategy-architecture-coherence.md` | Vertical (strategy → architecture → rules) | Strategy doc claims a capability or wedge with no corresponding mechanism in the architecture or rules; architecture provides a mechanism with no strategic justification (orphaned design); reserved future services named in strategy whose seams are not actually preserved in current architecture/rules. |
| `decisional-clarity.md` | Quality of individual decisions | An ADR that does not actually decide (mush, multiple options left open, no committed direction); a rule's CRITICAL OVERRIDE or Hard Rule that is not falsifiable (a future engineer cannot tell whether it was followed); ADR missing the "what changes if reversed" implicit signal — i.e., the decision is non-load-bearing. |
| `temporal-decay.md` | Epistemic hygiene | Claims that age — vendor capability rankings, model leadership, benchmark scores, prices, "currently best-in-class" language — without an explicit date or decay flag; absolute statements about external systems where the underlying state changes in months. |

## Anti-hallucination contract (binding on every specialist)

These rules are non-negotiable. The orchestrator **drops** any finding that violates them.

1. **Every finding MUST include a verbatim quote.** Format: `> "exact text from doc"`. Paraphrases are invalid. Specialist must copy the source text byte-for-byte.
2. **Every finding MUST cite `file:line`.** If a specialist cannot produce a line number, the finding is invalid.
3. **Cross-reference findings require quotes from BOTH sides.** A finding of the form "Doc A contradicts Doc B" must include verbatim quotes and line numbers from both A and B.
4. **"Missing element" findings quote the surrounding context** where the element should appear, so the absence is verifiable. Do not assert an absence (a missing Status field, an unpropagated concept) without it.
5. **An empty report is the correct output when no findings exist.** Specialists must not invent findings to justify the call. "No findings in this dimension" is a complete, valid report.
6. **Out-of-scope corpus is invisible.** Specialists do not read, cite, or reason about anything in the "Out of scope" list. If a question requires reading an out-of-scope file, the specialist returns "out of scope — cannot evaluate" rather than guessing.
7. **Specialists must read every in-scope file before producing findings.** No grep-and-go. Findings produced without full corpus read are invalid.

## Do not flag (negative scope)

- Style, grammar, prose quality, word choice.
- Markdown formatting, unless it produces semantic ambiguity (e.g., a list item that could be parsed as either a decision or an example).
- Implementation-level concerns — whether the docs are *correctly implemented* is `plan-review` / `code-review`'s job.
- Anything in the "Out of scope" corpus list.
- Open questions or research memos — by definition unresolved or non-authoritative.
- Stylistic preferences that do not violate a falsifiable rule.
- "This doc could be longer / shorter / restructured" without a specific consistency, coherence, clarity, or decay finding.

## Orchestration

1. **Verify corpus.** Expand the globs in the "In scope" list to a concrete file list. If a directory is missing or empty, stop and ask. Never proceed with a partial corpus — partial review produces false negatives on propagation findings.
2. **Build and verify the status manifest.**
   - Read `docs/decisions/README.md` and parse the index lines into `(adr_number, filename, title, status)` tuples.
   - For every ADR file in the corpus, read just the `**Status:**` line from the body (typically within the first ~10 lines). Compare to the README's status for that ADR.
   - For each mismatch, record an `internal-consistency` finding (FIX severity): README claims X, body says Y. Resolution: body is truth; update README.
   - The verified manifest passed to specialists uses **body status**, not README status, when they disagree. Specialists should not have to re-do this check.
3. **Spawn all four specialists in parallel** using the host agent's subagent
   or delegation facility. Use one parallel fan-out. Each specialist gets:
   ```
   Review the project's authoritative docs against {brief_path}.
   Concrete corpus (file list from glob expansion):
   {full file list}
   Status manifest (verified, body-truth):
   {table of ADR number, title, status}
   Body-read scope per status: see "ADR status handling" in SKILL.md;
   the brief's "Read scope" section specifies what to read in full.
   Anti-hallucination contract: every finding requires a verbatim quote
   AND a file:line citation. Cross-reference findings require both sides.
   An empty report is correct when no findings exist.
   Out-of-scope corpus is invisible; do not read or cite it.
   Use the output format in the brief.
   ```
4. **Verify BLOCK findings.** Before reporting, the orchestrator re-reads the cited line for every BLOCK finding and confirms the quote matches the source byte-for-byte. A BLOCK with a hallucinated quote is dropped silently — do not report and do not retry.
5. **Spot-check FIX/SUGGEST findings.** Verify at least 3 random findings per severity. Drop any whose quote does not match the source.
6. **Aggregate.**
   - Add manifest-mismatch findings from step 2 to the `internal-consistency` group.
   - Group by severity (BLOCK / FIX / SUGGEST).
   - Within severity, group by specialist dimension.
   - Deduplicate: if two specialists raise the same line for related reasons, merge into one finding tagged with both dimensions.
7. **End with a one-line verdict.** `READY` (no BLOCKs), `REVISE` (BLOCKs present), or `READY-WITH-FIXES` (only FIX/SUGGEST).

## Severity criteria

- **BLOCK** — Two authoritative docs make contradictory claims that cannot both be true; or a strategy claim has no mechanism in the architecture and the architecture cannot be reconciled with the claim. The docs are unusable as a coherent set until resolved.
- **FIX** — Inaccurate cross-citation, missed propagation, unfalsifiable Hard Rule, or temporal claim missing a decay flag. Mechanically resolvable. Docs are coherent now but rot fast if not addressed.
- **SUGGEST** — Could be clearer, could be decay-dated, could be cited explicitly. Optional improvement.

## Output template

The block below illustrates the format only — file names are placeholders and findings are fabricated for the example.

```
# Docs Review: <project name>

Corpus reviewed: <count> files
Specialists run: internal-consistency, strategy-architecture-coherence, decisional-clarity, temporal-decay

## BLOCK
- [internal-consistency] docs/decisions/0007-example-decision.md:42 ↔ rules/example_package.md:88
  ADR-0007 says:
  > "Workers do not import provider-specific SDKs outside the adapter layer."
  Rule says:
  > "Workers may call the provider SDK directly for hot paths."
  These cannot both be true. Resolve which is authoritative.

## FIX
- [strategy-architecture-coherence] docs/strategy/competitive_positioning.md:103
  > "Our two-tier processing enables a 5× cost advantage over single-pass alternatives."
  No corresponding mechanism in `example_package.md` enforcing the processing discipline. Either propagate the constraint to the rule or scope down the strategy claim.

## SUGGEST
- [temporal-decay] docs/strategy/competitive_positioning.md:88
  > "Frontier model X 78.6% on Benchmark Y v2"
  Add date qualifier — frontier benchmark scores age in months. Mark as "as of <YYYY-MM>".

Verdict: REVISE
```

## What this skill is NOT

- Not a copy editor. Style, grammar, and prose quality are out of scope.
- Not a substitute for ADR creation. If a finding implies a *new* architectural decision, surface as BLOCK with "needs ADR" rather than auto-resolving.
- Not a research validator. Research memos and preserved artifacts are out of scope; claims sourced from them are reviewed in the doc that cites them, not in the source.
- Not `plan-review` or `code-review`. If the issue is "this plan/code violates a doc," use those skills instead.
- Not a completeness check for the architecture itself. "The architecture should also cover X" is a `gap-analysis` concern (folded into `strategy-architecture-coherence` here only when X is claimed in a strategy doc) — not a generic "more is better" lens.
