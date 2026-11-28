# Architecture Decision Records — bozz-agents

ADRs record the **WHY** behind bozz-agents' design — decisions that bind future
work on the skills, the per-tool generation pipeline, and the content-layer
model. They are **immutable**: supersede with a new ADR rather than editing.

bozz-agents was extracted from the **prism** project, where its foundational
decisions were first recorded — notably prism ADR-0015 (review-skill family
pattern), ADR-0016 (discover-and-dispatch update orchestrator), and ADR-0021
(context tooling extracted to this plugin). Decisions specific to this repo are
recorded below as they land.

<!-- adr-index:begin -->
| ADR | Title | Status |
|---|---|---|
| [ADR-0001](0001-bozz-agents-maintains-own-context.md) | bozz-agents maintains its own context | Accepted |
| [ADR-0002](0002-host-neutral-skills-generated-trees.md) | Host-neutral skills, generated per-host trees, packaging by manifest | Accepted |
| [ADR-0003](0003-file-scoped-cross-agent-review-lifecycle.md) | File-scoped cross-agent review lifecycle with independent finding adjudication | Accepted |
| [ADR-0004](0004-built-in-lenses-and-plan-build-family.md) | Built-in generic review lenses and a plan → build → PR authoring family | Accepted |
| [ADR-0005](0005-shipped-manager-worker-agents.md) | Ship manager/worker agent definitions alongside the skills | Accepted |
| [ADR-0006](0006-cross-review-content-pins-and-relayed-reviewers.md) | Cross-review content pins, stale-baseline reviews and relayed reviewers | Accepted |
| [ADR-0007](0007-size-capped-sessions-and-bounded-loads.md) | Size-capped agent sessions, manager succession and bounded loads | Accepted |
<!-- adr-index:end -->
