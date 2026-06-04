# Customizing bozz-agents for your project

The skills ship usable out of the box against a conventional layout. Two things
make them *yours*: the **manifest** (paths and layers) and the **domain briefs**
(what `plan-review` / `code-review` check against).

## 1. Remap your layers — `context-manifest.yaml`

Copy `config/context-manifest.example.yaml` to your project root as
`context-manifest.yaml` and edit it:

- **Paths.** Point each layer at where it actually lives. Keep ADRs in
  `docs/adr/` instead of `docs/decisions/`? Change the path. Use `docs/rules/`
  instead of `.claude/rules/`? Change it.
- **Layers.** Delete the ones you don't have (no strategy doc? remove the
  `strategy` layer). Add your own following the same shape — give it an `id`,
  `path`, an owning `skill`, an optional `review`, and an `order`.
- **Orientation.** List `CLAUDE.md`, `AGENTS.md`, or both, depending on which
  agents you run.

If you don't add a manifest, the skills fall back to the defaults in the example
file.

## 2. Replace the domain briefs

`docs-review` and `skill-review` are **project-agnostic** — their briefs check
universal properties (internal consistency, decisional clarity, temporal decay,
structural integrity, anti-hallucination quality, scope, cross-skill
consistency). Leave them.

`plan-review` and `code-review` are **architecture-specific**. The briefs under
their `references/` directories —

```
skills/plan-review/references/{architecture,ml-contracts,iac-discipline,security,testing,performance-cost}.md
skills/code-review/references/{...same...}.md
```

— encode the **Prism** project's hard rules (Model Router boundary, two-pass
cognition, Vertex Pipelines vs Cloud Workflows, tenant/domain scoping, …). They
are included as a **worked example**, not as defaults that fit you.

To adapt:

1. **Replace** each domain brief with one for *your* architecture. Keep the
   brief shape (a single lens, a "do not flag" negative scope, and the
   anti-hallucination contract). Use `docs/prism-case-study.md` and any existing
   brief as a template.
2. **Update both skills' `references/`.** plan-review and code-review carry
   independent copies so each skill stays self-contained; if you change one
   brief, change it in both (or let them diverge intentionally — plan-time and
   diff-time checks can differ).
3. **Update the SKILL.md specialist table** in each to list your briefs and
   their run-conditions.
4. **Update `reviews:` in the manifest** to match.

A new brief is small. The hard part — the parallel fan-out, the verdict
aggregation, the anti-hallucination enforcement — is already in the SKILL.md and
doesn't change.

## 3. Validate

If you have the reference validator:

```bash
skills-ref validate skills/<your-skill>
```

Then run the package's own `skill-review` against your changed skills — it
checks frontmatter validity, required sections, contract strength, scope, and
cross-skill consistency, and will catch a broken brief reference as a BLOCK.

## 4. (Optional) Cross-tool sync

Because every skill is in the open format, any skill-manager that speaks the
standard can install/sync these into multiple tools at once. That's a
convenience layer, not a dependency — start with the native install in the
README and add a sync CLI only if you actually run several tools in parallel.
