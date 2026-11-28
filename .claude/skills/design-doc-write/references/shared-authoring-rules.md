# Shared Authoring Rules — the pen, project conventions, and where facts go

Read by both pen-holders: `design-doc-write` (steps 1 and 4) and `design-doc-edit`
(steps 1 and 3). Review lenses do not get this file.

## Holding the pen

The pen-holder edits the file directly. The user supervises through the outline
checkpoint, the diff, and the review verdict rather than by typing.

- **No invented decisions.** Anything the source leaves undecided goes in Open items.
  When the user settles something during the session, record the choice, what it beat,
  and why. Never add a resolution date or the name of whoever decided.
- **No unchecked facts.** Before the doc states a field, a contract shape, a behaviour, a
  latency or throughput figure, or a framing such as "this is new" or "this is cheap",
  check it in the code, schema or config and cite where you found it, or label it
  "unverified" with what would settle it. The claim kinds and the evidence each needs are
  defined in `../../design-doc-review/references/verify-against-artifact.md`.
- **No shrinking hard problems.** Do not call a later phase a small step, or an unsolved
  mechanism "simple", unless the source shows it is.
- **Keep the owner's style corrections.** When the owner corrects how something is
  written and the project has a conventions file (below), add their correction there in
  their words so it survives the session. With no file, mention it in the hand-back.
- **No drawing.** Decide that a figure is needed and place its caption and pointer; the
  figure source belongs to `../../design-diagrams/` where installed.

## Project conventions

Before writing, look for the project's own design-doc conventions and treat each entry as
a binding rule on top of the rubrics. First match wins:

1. a `conventions` key on the `design-docs` layer in `context-manifest.yaml`;
2. `design-doc-conventions.md` at the root of the design-docs directory.

If neither exists, the rubrics are enough; do not stop to ask. A project convention beats
a general preference in the rubrics (a fixed marker for open gates, say, or schemas kept
as code blocks). It never overrides decision honesty, the history rule, or the
making-of rule in `tone-rubric.md`.

## Route each fact (currency, then depth, then home)

Decide where a fact belongs before writing it down. Most length problems start here.

- **Currency.**
  - How the design used to be, or why it changed → not in the doc. The project's ADRs or
    decision log hold that.
  - An undecided question → Open items, worded as undecided.
  - A settled choice → recorded with its alternatives and reason.
  - Process detail (meetings, review rounds, build or CI state) → not in the doc. Describe
    what the system does, not how the build is going. A real outstanding external step,
    such as a security review not yet requested, stays as an open item.
  - How the doc itself was written → never (`tone-rubric.md` check C).
- **Depth.** Body or appendix per `structure-rubric.md` S5; schemas and interface
  definitions per `tone-rubric.md` E2. If the detail lives in a file readers of the
  published doc cannot open, point to it in words ("see the full field reference")
  instead of a relative link that will break.
- **Decisions.** Placement per `structure-rubric.md` S4; content per `tone-rubric.md` D.
- **Home.** Each concept has one owning section. A rule two docs both need has one
  normative home and a one-line pointer from the other. When a figure shows a fact, the
  prose does not repeat it.
