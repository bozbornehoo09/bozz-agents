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

The layers are declared in a project-root `context-manifest.yaml` (copy the
shipped `config/context-manifest.example.yaml` to start). The shipped defaults
match a common documentation layout, but the set is yours to define.

## The write side: discover → dispatch → review

`update-context` is the end-of-session orchestrator. It:

1. **Discovers** what changed (git history, file mtimes, the current
   conversation — which is the only source for in-session rationale).
2. **Dispatches** only the `update-*` skills whose layers actually changed, in
   dependency order, pausing for your confirmation on the plan.
3. **Reviews** once at the end, instead of after every layer.

Each narrow `update-*` skill also stands alone, and the ones owning
authoritative layers bake in their own review hook — run just `update-decisions`
mid-session and you still get checked. The temporal layers (work plan, backlog,
work tracker, open questions) have no hook; they are not authoritative.

## The check side: the review-skill family

A review skill is a small, fixed shape — the **family pattern**:

- One `SKILL.md` orchestrates its specialist briefs (in `references/`), usually
  four or five. `plan-review` and `code-review` ship built-in generic lenses
  and also run any project-specific briefs a consumer adds from the template
  (ADR-0004).
- Configured briefs **fan out in parallel**; each owns one lens and is blind to
  the others.
- Findings use one severity vocabulary: **BLOCK / FIX / SUGGEST**.
- The skill returns one verdict: **READY / READY-WITH-FIXES / REVISE**.

The four members:

| Skill | Reviews | Against |
|---|---|---|
| `docs-review` | authoritative docs | each other |
| `skill-review` | skills + their references | quality conventions |
| `plan-review` | an implementation plan | the architecture (pre-code) |
| `code-review` | a diff/commit | the architecture (post-code) |
| `design-doc-review` | one human-facing design doc | the tone, structure and cold-reader gates |

`docs-review` checks the project's authoritative layers against each other;
`design-doc-review` checks one document written for human reviewers. They do not
overlap.

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

## Across agents: request → review → adjudicate → fold

The review family answers “what is wrong with this pinned artifact?” The
cross-review lifecycle answers “how do two independent agent platforms carry
that review through multiple implementation rounds without trusting either
side blindly?”

Each gate gets one append-only active file with local event IDs. The requester
pins scope and revision; the reviewer invokes the appropriate review-family
skill; then a separate folding skill verifies each finding in a fresh context
before changing code. Both requester and reviewer publish absolute ETA + grace
windows and use the same adaptive watcher, so long work remains unattended
without turning silence into closure. Explicit terminal events move the raw,
hashed transcript to an archive. When a confirmed finding targets an
authoritative layer, the fold invokes that layer's owning `update-*` skill; it
does not create a second writer. See ADR-0003. A review may also pin
uncommitted files by content fingerprint, a reviewer whose pin moved posts a
`BASELINE: STALE` review instead of findings, and a reviewer that cannot write
the file (a browser chat model) can be relayed by the requester under a
`RELAYED:` marker with its verbatim output hashed. See ADR-0006.

### Keeping temporal layers short

The work plan, open questions and backlog grow without bound if nothing trims
them. Each owning `update-*` skill can compact its own layer under one shared
rule (`skills/update-context/references/compaction.md`): entries are kept,
compressed only when the dropped detail exists elsewhere, or moved verbatim to
`archive/<stem>-history.md` with a one-line pointer left behind. Nothing is
deleted, the skill pauses for confirmation first, and `archive/` is history,
never current state. Authoritative layers and the work tracker are never
compacted.

Read-only helpers back the update skills: `update-work-tracker/scripts/tracker_path.py`
computes the week and day folder for a date, and
`update-decisions/scripts/adr_index.py` checks the ADR index against each ADR's
Status line.

## From plan to pull request

A change moves through three authoring skills, each gated by the one before:
`writing-implementation-plans` drafts a plan that leaves an implementer no
design choices and runs `plan-review` until a full pass has no BLOCK;
`implementing-a-plan` refuses a plan without that closed review, builds one step
per commit and stops on the first deviation; `preparing-code-reviews` shapes the
branch into one pull request and runs `code-review`, and pushes only after the
user's go. A design call that comes up along the way is never settled inside
a plan: it goes to the owner, or, when the owner is away and the call is cheap
to undo, to `deciding-calls-by-debate`, which records it for the owner to
review.

## The agents

`agents/` ships the roles that run this loop: a **manager** the owner talks to,
which briefs **architect** and **implementer** worker sessions and keeps the
owner's decisions batched, and read-only subagents (**review-specialist**,
**cold-reader**, **cold-reader-deep**, **artifact-verifier**) that the review
skills dispatch. Workers follow one contract (`agents/shared/worker-contract.md`)
and never decide design calls. See `docs/agents.md` and ADR-0005.

## Why this is portable

None of the above is tool-specific. The layers are markdown, the skills are
`SKILL.md` folders in the open Agent Skills format, and the review contract is
just prose discipline. The same package runs wherever the standard is read —
Claude Code and Codex today, with the set expected to grow — which is why
bozz-agents is authored to the format first and treats each tool as an adapter.

The structure enforces that portability rather than leaving it to discipline:
one canonical, host-neutral `skills/` tree is the single source of truth;
per-host discovery directories (`.claude/skills/`, `.agents/skills/`) are
generated from it by `scripts/generate-tool-skills.sh` (CI regenerates on push;
they carry GENERATED markers and are never hand-edited); and per-host packaging
is a thin manifest pointing back at canonical `skills/` (`.claude-plugin/`,
`.codex-plugin/`). Adding a host is a manifest, never a fork. See ADR-0002.
