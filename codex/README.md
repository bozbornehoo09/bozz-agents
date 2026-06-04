# Using bozz-agents with Codex

Codex consumes the same `SKILL.md` files as Claude Code — they follow the open
[Agent Skills](https://agentskills.io/specification) standard. No conversion is
needed; only the install location differs.

## Where Codex looks for skills

Codex discovers skills, in precedence order:

| Scope | Path |
|---|---|
| Repository | `.agents/skills/` (from cwd up to repo root) |
| User | `$HOME/.agents/skills/` |
| Admin | `/etc/codex/skills/` |

## Install

Pick the scope you want and link or copy the skills there. User scope makes them
available in every repo:

```bash
mkdir -p ~/.agents/skills
ln -s /absolute/path/to/bozz-agents/skills/* ~/.agents/skills/
```

Or vendor a subset into a single repo:

```bash
mkdir -p .agents/skills
cp -R /absolute/path/to/bozz-agents/skills/docs-review .agents/skills/
```

(Symlinks keep you current with `git pull`; copies pin a snapshot.)

## Invoke

- Explicitly: `/skills`, or type `$` and mention a skill (e.g. `$docs-review`).
- Implicitly: Codex auto-selects a skill when the task matches its
  `description`.

## Notes & expansion seams

- **Per-skill `references/`** travel with each skill folder, so a single skill
  copied on its own stays self-contained — the briefs come with it.
- **`agents/openai.yaml`** (optional, per skill) is where Codex-specific skill
  configuration would go if you need it. None of the skills here require it
  today; add one inside a skill folder only if a Codex-only behavior is needed.
- **Orientation:** Codex reads `AGENTS.md` (this repo has one at the root). In a
  consuming project, your own `AGENTS.md` is the Codex equivalent of Claude's
  `CLAUDE.md` — the `update-orientation` skill can maintain either or both.
- This adapter is intentionally thin: the skills are the source of truth, Codex
  is one consumer. Adding another tool (Cursor `.cursor/skills/`, Gemini, etc.)
  is the same move — point its skills directory at `skills/`.
