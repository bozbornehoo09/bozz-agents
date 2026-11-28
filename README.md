# bozz-agents

Context-management, review, planning and writing skills for AI coding agents,
plus the manager/worker agents that run them.

Five families of [Agent Skills](https://agentskills.io/specification) that keep a
project's *knowledge* — its decisions, architecture, rules, and docs — accurate
and coherent as the code evolves, then stress-test that knowledge against itself:

- **`update-*` skills** — the **write** side. A discover-and-dispatch
  orchestrator (`update-context`) plus ten narrow skills, one per
  content layer (decisions, strategy, architecture, rules, AI tooling,
  open questions, work plan, backlog, orientation, work tracker). Run at
  the end of a session to capture what changed in the right place.
- **review skills** — the **check** side. A five-member review family
  (`docs-review`, `skill-review`, `plan-review`, `code-review`,
  `design-doc-review`). Each fans out to its specialist briefs in parallel —
  `plan-review` and `code-review` ship built-in generic lenses and take your
  architecture briefs alongside them — reports findings as `BLOCK`/`FIX`/
  `SUGGEST`, and returns a verdict of `READY` / `READY-WITH-FIXES` / `REVISE`.
  Every specialist runs under an **anti-hallucination contract**: each finding
  needs a verbatim quote and a `file:line` citation, or it is dropped.
- **cross-review skills** — the **independent handoff** side. A requester,
  reviewer, and evidence-first finding folder coordinate iterative reviews
  through one append-only file per review. Both active roles poll adaptively
  from agent-published ETA + grace windows; completed findings are independently
  adjudicated before the requester changes code.
- **plan → build → PR skills** — `writing-implementation-plans` drafts a plan an
  implementer agent can build without making design choices and runs
  `plan-review` to a closed pass; `implementing-a-plan` builds it one step per
  commit and stops on the first deviation; `preparing-code-reviews` turns the
  branch into one reviewable pull request (never pushed without your go).
  `deciding-calls-by-debate` settles a reversible design call by structured
  debate when you are away, and parks the rest for you.
- **writing skills** — `design-doc-write` / `design-doc-edit` for human-facing
  design docs (HLD, LLD, mini-design) with a cold-reader gate,
  `refining-technical-writing` for prose and code comments, and
  `design-diagrams` for PlantUML, draw.io and SVG diagrams.

The **agents** in `agents/` — a manager you talk to, architect and implementer
workers, and read-only reviewer subagents — run these skills as a team, locally
or in a cloud session. See [`docs/agents.md`](docs/agents.md).

It's a **local developer tool**. Nothing imports it; you install the skills into
your agent (user-level) and they're available across every project you open.

## Format & portability

Everything here is authored to the open **Agent Skills** standard (`SKILL.md`
folders). The canonical skills contain no host-specific tool calls or project
architecture. The same files work in **Claude Code**, **Codex**, and other
compatible hosts; only discovery and plugin packaging differ. There is **no
dependency on any third-party skill-manager CLI**; a sync tool is an optional
convenience you can add, not a requirement.

## Layout

```
bozz-agents/
├── .claude-plugin/
│   ├── plugin.json          # Claude Code plugin manifest
│   └── marketplace.json     # so the repo installs via /plugin marketplace add
├── .codex-plugin/
│   └── plugin.json          # Codex plugin manifest; points at canonical skills/
├── .agents/plugins/
│   └── marketplace.json     # repository-scoped Codex marketplace
├── skills/                  # canonical SKILL.md skills (flat, tool-agnostic)
│   ├── context-up/          #   session-start scoped context loader (read-only)
│   ├── update-context/      #   end-of-session orchestrator
│   ├── update-decisions/  …  update-work-tracker/   # 10 content-layer skills
│   ├── docs-review/         #   review skills; specialist briefs live in
│   ├── skill-review/        #   each skill's references/ subdirectory
│   ├── plan-review/         #   (built-in generic lenses; add briefs for
│   ├── code-review/         #    your own architecture from the template)
│   ├── design-doc-review/   #   one human-facing design doc
│   ├── writing-implementation-plans/ implementing-a-plan/ preparing-code-reviews/
│   ├── deciding-calls-by-debate/
│   ├── design-doc-write/ design-doc-edit/ design-diagrams/ refining-technical-writing/
│   ├── cross-review-requester/  # file lifecycle + adaptive polling
│   ├── cross-reviewer/          # independent review + adaptive polling
│   └── fold-review-findings/    # impartial adjudication before edits
├── agents/                  # manager/worker agent definitions (Claude Code)
│   └── shared/              #   worker contract, owner rules, shell deny lists,
│                            #   reference/ (rules read on trigger), scripts/
├── hooks/                   # size-cap hook (self-gated; ADR-0007)
├── config/
│   └── context-manifest.example.yaml   # the one file you customize
├── docs/                    # concepts.md, customizing.md, agents.md, decisions/
├── codex/                   # Codex install/usage notes; agents/ (generated roles)
└── AGENTS.md                # cross-tool orientation
```

## Install

### Claude Code (plugin + marketplace)

```
/plugin marketplace add bozbornehoo09/bozz-agents
/plugin install bozz-agents@bozz-agents
```

Skills then invoke as `/bozz-agents:docs-review`, `/bozz-agents:update-context`,
`/bozz-agents:cross-review-requester`, and so on; agents load as
`bozz-agents:manager`, `bozz-agents:cold-reader`, and so on. Updates are a `git pull` away
(or `/plugin marketplace update`).

For a quick local try without the marketplace, symlink the skills into your
user skills directory:

```
ln -s "$PWD/skills"/* ~/.claude/skills/
```

### Codex

Install the repository as a plugin:

```bash
codex plugin marketplace add bozbornehoo09/bozz-agents
codex plugin add bozz-agents@bozz-agents
```

For local development or skill-only use, Codex also discovers the generated
`.agents/skills/` tree directly. Details in [`codex/README.md`](codex/README.md).

## How the skills are distributed

`skills/` is the **only hand-authored tree** — spec-compliant `SKILL.md` folders.
The per-tool directories are **build artifacts**: a GitHub Actions workflow
(`.github/workflows/generate-tool-skills.yml`) runs `scripts/generate-tool-skills.sh`
on every push that touches `skills/**`, mirrors it into `.claude/skills/` and
`.agents/skills/`, and commits them back. The loop is broken by a path filter —
the generated commit only touches the generated dirs, which aren't in the
trigger paths.

- **Claude** gets the skills via the plugin/marketplace (above), or from the
  generated `.claude/skills/` if you clone and open the repo directly.
- **Codex / Cursor / others** read the generated `.agents/skills/` (add more
  targets by editing `TARGETS` in the workflow).
- **Never edit** `.claude/skills/` or `.agents/skills/` by hand — they're marked
  `linguist-generated` and will be overwritten. Edit `skills/`.

Reuse this in your own repo: copy `scripts/generate-tool-skills.sh` and the two
workflows. PRs validate the canonical tree against the spec; pushes regenerate.

## Customize for your project

The skills resolve paths from `context-manifest.yaml` first, then use neutral
conventions with host-specific legacy fallbacks. To adapt:

1. Copy `config/context-manifest.example.yaml` to your project as
   `context-manifest.yaml` and remap the layer paths.
2. Optionally give `plan-review` / `code-review` **briefs for your
   architecture**. Their built-in generic lenses run regardless; copy
   `_brief-template.md` into each skill's `references/` (one brief per concern)
   to add project-specific checks. The Prism project's real design briefs live
   in the Prism repo as a worked example — see `docs/prism-case-study.md`.
3. Optionally add an **overrides register** (`docs/overrides.md`, format in
   `skills/code-review/references/register.md`) for recurring corrections the
   reviewers should enforce.

Full guide: [`docs/customizing.md`](docs/customizing.md). The pattern itself is
explained in [`docs/concepts.md`](docs/concepts.md), and the original Prism
instantiation in [`docs/prism-case-study.md`](docs/prism-case-study.md).

## License

MIT — see [LICENSE](LICENSE).
