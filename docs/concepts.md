# Concepts

bozz-agents encodes one idea: **a project's knowledge is a set of authoritative
layers, each owned by exactly one writer and checked by an adversarial reader.**
Everything else follows from that.

## Authoritative content layers

Most projects accumulate knowledge in predictable places: decisions, strategy,
architecture, per-package rules, an orientation file, an activity log. Left
unmanaged, these drift — a decision lands in an ADR but never propagates to the
rules; the orientation file describes a structure that no longer exists.

bozz-agents names these layers explicitly and gives each one:

- a **single owning `update-*` skill** (the only thing that writes it), and
- a place in a **dependency order** (decisions are upstream truth; strategy,
  architecture, and rules reflect them; orientation summarizes the whole).

The layers are declared in `config/context-manifest.yaml`. The shipped defaults
match a common documentation layout, but the set is yours to define.

## The write side: discover → dispatch → review

`update-context` is the end-of-session orchestrator. It:

1. **Discovers** what changed (git history, file mtimes, the current
   conversation — which is the only source for in-session rationale).
2. **Dispatches** only the `update-*` skills whose layers actually changed, in
   dependency order, pausing for your confirmation on the plan.
3. **Reviews** once at the end, instead of after every layer.

Each narrow `update-*` skill also stands alone and bakes in its own review hook,
so you can run just `update-decisions` mid-session and still get checked.

## The check side: the review-skill family

A review skill is a small, fixed shape — the **family pattern**:

- One `SKILL.md` orchestrates **3–4 specialist briefs** (in `references/`).
- Briefs **fan out in parallel**; each owns one lens and is blind to the others.
- Findings use one severity vocabulary: **BLOCK / FIX / SUGGEST**.
- The skill returns one verdict: **READY / READY-WITH-FIXES / REVISE**.

The four members:

| Skill | Reviews | Against |
|---|---|---|
| `docs-review` | authoritative docs | each other |
| `skill-review` | skills + their references | quality conventions |
| `plan-review` | an implementation plan | the architecture (pre-code) |
| `code-review` | a diff/commit | the architecture (post-code) |

## The anti-hallucination contract

The reason the review family is trustworthy: **a finding without evidence is
dropped.** Binding on every specialist —

1. every finding includes a **verbatim quote** (`> "exact text"`);
2. every finding cites **`file:line`**;
3. cross-reference findings quote **both** sides;
4. a "missing X" finding quotes the **surrounding context** where X should be;
5. an **empty report is correct** when there's nothing to flag;
6. out-of-scope corpus is **invisible** — not read, not cited.

The orchestrator re-reads cited lines for BLOCK findings and spot-checks the
rest, dropping anything whose quote doesn't match byte-for-byte. This is what
keeps a parallel fan-out of LLM reviewers from inventing plausible-but-false
problems.

## Why this is portable

None of the above is tool-specific. The layers are markdown, the skills are
`SKILL.md` folders in the open Agent Skills format, and the review contract is
just prose discipline. The same package runs wherever the standard is read —
Claude Code, Codex, and others — which is why bozz-agents is authored to the
format first and treats each tool as an adapter.
