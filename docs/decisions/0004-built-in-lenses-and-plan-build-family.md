# ADR-0004: Built-in generic review lenses and a plan → build → PR authoring family

**Status:** Accepted
**Date:** 2026-11-27
**Category:** Skill design

## Context

Until now `plan-review` and `code-review` shipped as skeletons: generic
orchestration plus a `_brief-template.md`, with every specialist brief left to
the consumer. That kept them architecture-neutral, but it also meant a fresh
install reviewed nothing until someone wrote briefs, and the checks that apply to
almost any plan or diff (does each step have a test, is a destructive production
step guarded, is the change simpler than it needs to be, does a comment carry a
reason) were rewritten per project or skipped.

The maintainer's private workflow had also grown skills that bozz-agents lacked
entirely: authoring an implementation plan that an implementer agent can build
without choosing anything of consequence, executing it one step per commit,
turning the branch into one reviewable pull request, deciding a design call by
structured debate when the owner is away, and writing, reviewing and editing
human-facing design docs and prose. Those skills were generalized and ported
into this repo.

## Decision

1. **Review skills ship built-in generic lenses, and consumer briefs still plug
   in.** `plan-review` always runs plan-hygiene, simplicity, testing-discipline
   and production-safety, and adds implementation-plan-standard when the plan is
   handed to an implementer agent. `code-review` always runs correctness,
   comments, decisions, precedents and (when a register exists) overrides.
   Briefs a project writes from `_brief-template.md` run alongside them. The
   built-in lenses are architecture-neutral: they check a plan or diff against
   the project's own ADRs, rules and register, never against a baked-in
   architecture.
2. **An optional overrides register** records recurring owner corrections
   ("never do X here"). `skills/code-review/references/register.md` is its single
   definition: location (a manifest layer `id: overrides`, else
   `docs/overrides.md`, else none), entry format, binding severity, and how an
   entry is added (owner confirmation before writing). Every lens that uses it
   locates it by that rule.
3. **An authoring family for the plan → build → PR loop**:
   `writing-implementation-plans` (drafts a plan and runs `plan-review` to a
   closed pass), `implementing-a-plan` (one plan step per local commit, stop on
   the first deviation), `preparing-code-reviews` (one clean pull request; never
   pushes or opens without the user's go). `deciding-calls-by-debate` settles a
   reversible design call when the owner is unavailable and parks everything
   else.
4. **Writing skills**: `design-doc-write` / `design-doc-edit` /
   `design-doc-review` for human-facing design docs, `refining-technical-writing`
   for prose and code comments, and `design-diagrams` for diagrams. They own one
   definition each (the tone rubric and template live in `design-doc-write`; the
   general prose rules and comment rules live in `refining-technical-writing`).
5. **Third-party tools are downloaded, not vendored.** Any installer pins an
   upstream release at least two weeks old and verifies a checksum where the
   upstream publishes one. Credits live in the skill's `THIRD-PARTY-NOTICES.md`.

## Alternatives considered

- **Keep the review skills as skeletons and publish the lenses as example
  briefs.** Rejected: every consumer would copy the same files, and a fresh
  install would still review nothing.
- **Make the built-in lenses opt-in per project.** Rejected: they only check a
  plan or diff against the project's own declared material, so a project with
  no ADRs or register simply gets fewer findings; opt-in adds configuration
  without a real failure mode to prevent.
- **One combined "write and ship" skill instead of plan / implement / prepare.**
  Rejected: the three steps have different gates (a closed plan review, a clean
  step build, the user's go to push), and different hosts or people run them.

## Consequences

- **Positive:** a fresh install reviews plans and diffs usefully on day one;
  the loop from design to merged change is covered end to end.
- **Positive:** one definition per concept (register, PR description, comment
  rule, tone rubric) keeps the larger surface consistent; `skill-review`'s
  cross-skill-consistency lens checks it.
- **Negative:** a much larger skill surface to maintain, and two review skills
  whose SKILL.md is now 150–250 lines rather than a thin skeleton.
- **Binds:** built-in lenses MUST stay architecture-neutral and resolve project
  material through `context-manifest.yaml`. A project-specific check belongs in a
  consumer brief, not a built-in lens. Installers MUST pin releases at least
  two weeks old.
- **Revisit when:** a built-in lens produces findings most projects decline, or
  a host gains a native equivalent of one of the authoring skills.

## References

- Skills: `skills/plan-review/`, `skills/code-review/`,
  `skills/writing-implementation-plans/`, `skills/implementing-a-plan/`,
  `skills/preparing-code-reviews/`, `skills/deciding-calls-by-debate/`,
  `skills/design-doc-{write,edit,review}/`, `skills/refining-technical-writing/`,
  `skills/design-diagrams/`
- Register: `skills/code-review/references/register.md`
- Related: [ADR-0002](0002-host-neutral-skills-generated-trees.md) (host-neutral
  canonical tree), [ADR-0005](0005-shipped-manager-worker-agents.md) (the agents
  that run this loop)
