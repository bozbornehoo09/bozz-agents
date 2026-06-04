# Worked example: the Prism instantiation

bozz-agents was extracted from **Prism**, an AI video-understanding platform.
The skills are generic; the *content* they were first tuned against was Prism's.
This document records that instantiation so the example briefs make sense.

## Prism's content layers

Prism mapped the eight default layers onto a concrete repo:

| Layer | Prism path | Notes |
|---|---|---|
| Decisions (WHY) | `docs/decisions/` | Numbered, immutable ADRs; superseded, never edited. |
| Strategy | `docs/strategy/` | Positioning, competitive analysis, north star. |
| Architecture | `docs/architecture/` | A canonical design doc + diagrams. |
| Rules (WHAT) | `.claude/rules/` | One file per package, with "CRITICAL OVERRIDE" / "Hard rule" blocks. |
| AI tooling | `.claude/skills/` + briefs | The very skills this package generalizes. |
| Open questions | `docs/open_questions.md` | Reconciled as ADRs land. |
| Orientation | `CLAUDE.md` | Auto-loaded each session. |
| Work tracker (WHEN) | `work_tracker/` | Session log; not authoritative. |

This is exactly the shipped default manifest — because Prism's layout is a
reasonable general convention, not because the skills are hard-wired to it.

## Why the plan-review / code-review briefs look the way they do

The six domain briefs (`architecture`, `ml-contracts`, `iac-discipline`,
`security`, `testing`, `performance-cost`) check Prism's specific architectural
commitments. A few, to show the texture of a good domain brief:

- **`ml-contracts.md`** — the Model Router is the *only* component that imports
  provider SDKs; workers never load adapter weights or own prompts; "two-pass
  cognition" (cheap localization before expensive recognition) is mandatory.
- **`iac-discipline.md`** — Terraform-only IaC; ML DAGs belong in Vertex AI
  Pipelines, not Cloud Workflows; stacks deploy independently.
- **`security.md`** — every event and record carries `tenant_id` + `domain_id`;
  isolation is enforced server-side; secrets never reach a client bundle.

Each brief is one lens, with a negative-scope "do not flag" list so specialists
don't step on each other, and the same anti-hallucination contract as the rest
of the family. That *shape* is what you reuse; the *rules* are what you replace.

## What was generalized vs. kept

- **Generalized** (now project-agnostic): the orchestrator and all `update-*`
  skills; `docs-review` and `skill-review` and their briefs; the family pattern,
  severity vocabulary, verdict labels, and anti-hallucination contract. Hardcoded
  paths became the manifest; "Prism" became "the project".
- **Shipped as skeletons** (Prism-specific content removed): `plan-review` and
  `code-review` keep the generic machinery plus a `_brief-template.md`. Prism's
  six real design briefs live in the **Prism repo's** own `.claude/skills/`, next
  to the architecture they review. Writing your own is step 2 of
  [`customizing.md`](customizing.md).

If you're adapting bozz-agents, read a couple of these briefs first — they're the
clearest illustration of how much architecture you can encode in a few hundred
words, and how to keep a reviewer honest while doing it.
