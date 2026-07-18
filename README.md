# bozz-agents

Context-management and review skills for AI coding agents.

Two families of [Agent Skills](https://agentskills.io/specification) that keep a
project's *knowledge* — its decisions, architecture, rules, and docs — accurate
and coherent as the code evolves, then stress-test that knowledge against itself:

- **`update-*` skills** — the **write** side. A discover-and-dispatch
  orchestrator (`update-context`) plus ten narrow skills, one per
  content layer (decisions, strategy, architecture, rules, AI tooling,
  open questions, work plan, backlog, orientation, work tracker). Run at
  the end of a session to capture what changed in the right place.
- **review skills** — the **check** side. A four-member review family
  (`docs-review`, `skill-review`, `plan-review`, `code-review`). Each fans out
  to 3–4 specialist briefs in parallel, reports findings as `BLOCK`/`FIX`/
  `SUGGEST`, and returns a verdict of `READY` / `READY-WITH-FIXES` / `REVISE`.
  Every specialist runs under an **anti-hallucination contract**: each finding
  needs a verbatim quote and a `file:line` citation, or it is dropped.

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
│   ├── plan-review/         #   (skeletons — add briefs for your own
│   └── code-review/         #    architecture; a template brief is included)
├── config/
│   └── context-manifest.example.yaml   # the one file you customize
├── docs/                    # concepts.md, customizing.md, prism-case-study.md
├── codex/                   # Codex install/usage notes
└── AGENTS.md                # cross-tool orientation
```

## Install

### Claude Code (plugin + marketplace)

```
/plugin marketplace add bozbornehoo09/bozz-agents
/plugin install bozz-agents@bozz-agents
```

Skills then invoke as `/bozz-agents:docs-review`, `/bozz-agents:update-context`,
and so on. Updates are a `git pull` away (or `/plugin marketplace update`).

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
2. Give `plan-review` / `code-review` **briefs for your architecture**. They
   ship as skeletons with a `_brief-template.md`; copy it into each skill's
   `references/` (one brief per concern). The Prism project's real design briefs
   live in the Prism repo as a worked example — see `docs/prism-case-study.md`.

Full guide: [`docs/customizing.md`](docs/customizing.md). The pattern itself is
explained in [`docs/concepts.md`](docs/concepts.md), and the original Prism
instantiation in [`docs/prism-case-study.md`](docs/prism-case-study.md).

## License

MIT — see [LICENSE](LICENSE).
