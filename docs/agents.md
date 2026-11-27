# Agents: the manager/worker model

bozz-agents ships seven agent roles alongside its skills. Three are
**session roles** that hold a conversation with the owner (`manager`,
`architect`, `implementer`); four are **subagent roles** the review skills
dispatch (`review-specialist`, `cold-reader`, `cold-reader-deep`,
`artifact-verifier`). The canonical definitions are the Markdown files in
`agents/`; shared material lives once in `agents/shared/`.

## The idea

Multi-step work (a design, a plan, its implementation) stalls in two ways:
one long session runs out of context, and a delegated subagent cannot stop
to ask the owner a question. The manager/worker model fixes both.

- **Workers are top-level sessions, not subagents.** Each workstream gets its
  own session that the owner can open and talk to at any time. Design calls
  go straight to the owner in that session, never through a relay.
- **The manager is a scheduler and a dashboard.** It splits the work, writes
  a brief per workstream, starts the workers, watches their STATUS files, and
  shows the owner one line per worker plus everything waiting on them. It
  authors nothing, reviews nothing, and never answers or relays a design call.
- **Files are the protocol.** Brief, STATUS, channel messages and handoff are
  plain files in a work folder, so the state survives compaction, restarts
  and a change of session.

## Roles

| Role | Tier | Tools | Started by | Main skills |
|---|---|---|---|---|
| `manager` | opus | inherits the session's | the owner (`claude --agent bozz-agents:manager`) | `context-up`, `update-context` |
| `architect` | opus | inherits | the manager, or the owner directly | `design-doc-write`, `design-doc-edit`, `design-doc-review`, `design-diagrams`, `writing-implementation-plans`, `plan-review`, `deciding-calls-by-debate`, `cross-review-requester`, `fold-review-findings`, `refining-technical-writing` |
| `implementer` | sonnet | inherits | the manager, or the owner directly | `implementing-a-plan`, `preparing-code-reviews`, `code-review` |
| `review-specialist` | opus | Read, Glob, Grep, Bash | review skills (`docs-review`, `plan-review`, `code-review`, `skill-review`, `design-doc-review`), the architect's simplicity review | — |
| `cold-reader` | sonnet | Read | `design-doc-review`'s cold-read gate | — |
| `cold-reader-deep` | opus | Read | the same gate (it needs two distinct models per panel) | — |
| `artifact-verifier` | opus | Read, Glob, Grep, Bash, WebFetch, WebSearch | `design-doc-review`, `fold-review-findings` | — |

Tiers are Claude aliases, so each resolves to the current model of its tier.
The implementer runs on the middle tier because plans are written to a
zero-ambiguity bar (`writing-implementation-plans`) and it makes no design
calls. No role, and no subagent a role dispatches, is pinned to a
usage-billed top tier.

The session roles inherit the session's tools so the owner's own connected
tool servers work in them. The subagent roles get the narrowest tool set
their job needs and no write tools.

## Hand-offs

```
owner ──asks──▶ manager ──BRIEF.md──▶ worker session (architect | implementer)
                   ▲                       │  owner talks to it directly
                   │  STATUS.md each turn  │
                   └───────────────────────┘
   manager ──channel/MSG-<n>.md──▶ worker        (process only: commit, hand off, continue)
   worker  ──HANDOFF.md──▶ manager ──new BRIEF──▶ successor session (-2, -3, ...)
   worker  ──DONE──▶ manager spot-checks ──▶ folder archived ──▶ next workstream
```

1. **Brief.** The manager opens `<work root>/work/<date>-<workstream>/` and
   writes `BRIEF.md`: goal (as the user experience it serves), mode, primary
   files, first step, limits, the home of each output, and the owner's
   presence. The work root is the `work-tracker` layer in
   `context-manifest.yaml`.
2. **One owner per file.** Two live workers never share a primary file; goals
   that need one file run in sequence.
3. **STATUS every turn.** Each worker overwrites its `STATUS.md` (at most 200
   words): state, what it is doing, commits, open owner items, next. The
   manager checks freshness against the worker's newest commits and files
   before acting, so it never acts on a stale line.
4. **Messages are process, never decisions.** The manager writes
   `channel/MSG-<n>.md` and, where the host allows, delivers it into the live
   session. A call *between* workers that touches no owner decision is the
   manager's, recorded as `DECISION-<n>.md` and flagged for owner review.
5. **Handoff.** At 80% context, after each draft or plan closure, or every
   fourth fold, a worker runs `update-context`, writes `HANDOFF.md` and reports
   `HANDOFF-READY`. The manager stops it and starts a successor from the
   handoff in the same folder.
6. **Done.** The manager spot-checks the commits (branch, collisions, build or
   length budget, every output landed in its home with a cite), then archives
   the folder.

## The worker contract

`agents/shared/worker-contract.md` is the one definition of the work-folder
layout, the STATUS block, collision rules, the update-context lock, the
context budget, owner-go batches, handing a step to the owner, the handoff,
and commit hygiene. Workers follow it whenever their brief says so; the
sections marked *binds every session* apply to an architect or implementer
started on its own too. `owner-talk.md` holds the rules for every message the
owner reads (plain terms, mechanism first, asks last). `owner-override.md`
holds the one way an owner lifts a default limit for a named task.

Results never live in a work folder. Each lands in its home layer with a cite
back to its record: decisions through `update-decisions`, open calls through
`update-open-questions`, plan items through `update-work-plan`, the session
record through `update-work-tracker`, all orchestrated by `update-context`.

## Unattended mode

When the owner tells the manager they are leaving, the manager sets
`Owner: away` in every live brief. Workers then never wait:

- an architect decides each new design call with `deciding-calls-by-debate`,
  which applies a call only on verified consensus, records it for owner review,
  and parks hard-to-reverse calls;
- an implementer never debates: a plan deviation becomes an owner item;
- owner-go steps (push, opening or merging a PR, production writes) still wait;
- a worker whose remaining work is all blocked hands off with a `Blocked:`
  line, and the manager retires it until the owner returns.

When the owner is back, the manager's first dashboard is a morning report
built from the layers: what was decided by debate, what was parked, what is
waiting for a go.

## Running locally on Claude Code

1. Install the plugin as the README describes. Agents load as
   `bozz-agents:<role>`.
2. Apply the settings in `agents/shared/claude-settings.example.json` to your
   user settings (adjust the hook's absolute path):
   - background isolation off, so background workers run in the shared
     checkout and their STATUS files are visible (`worktree.bgIsolation`;
     check the name against your version's settings reference);
   - permission `deny` rules for destructive commands and credential reads,
     and `ask` rules for `git push` and PR state changes;
   - a `PreToolUse` hook on Bash that runs `agents/shared/shell_deny.py`
     (below).
3. Start the manager: `claude --agent bozz-agents:manager`, and tell it the
   project and the goal. It launches workers with
   `claude --bg --name <session> --agent bozz-agents:architect "Run <brief>"`.
   Open a worker with `claude attach <id>` or the agent view. Type
   "dashboard" in the manager's session to see where everything stands.
4. An architect or implementer also works on its own:
   `claude --agent bozz-agents:architect`, then give it the task.

The manager's helpers in `agents/shared/scripts/` need `zsh` and `jq` and use
Claude Code's agent-view commands (`claude agents --json`, `claude stop`,
`claude respawn`); confirm them with `claude --help` on your version.

- `ctxpct.sh <session>` prints a session's context use as a percentage, read
  from its transcript (`CONTEXT_WINDOW_TOKENS` sets the window, default 1M).
- `ctx.sh <prefix>` prints one line per live session with that name prefix.
- `watch.zsh snap|start|stop` is the manager's watcher: it wakes the manager
  when any STATUS, handoff or unread message changes, respawns a vanished
  worker, and stops a finished one only after ten idle, quiet minutes.

## Running in the cloud

Cloud sessions (Claude Code on the web, or other hosted background agents)
each get their own clone, and a local watcher cannot see them. The model
still works with two changes:

- **One workstream per cloud session, one branch each.** Start the session
  with the brief as its prompt and the role named in it ("Act as the
  bozz-agents architect: read and follow `agents/architect.md` and
  `agents/shared/worker-contract.md`"). Because no shared checkout exists, the
  worker commits `STATUS.md` and `HANDOFF.md` on its work branch at the end of
  each turn instead of leaving them uncommitted.
- **The manager runs in paste mode.** It reads each worker's state by
  fetching its branch, and messages reach a worker through the owner (or a
  committed `channel/` file the worker reads at the start of its turn). The
  owner talks to each worker in its cloud session as usual.

Owner-go rules are unchanged: a cloud worker pushes only its own work branch,
and opens or merges a PR only on the owner's go. Hosted scheduled tasks are a
natural fit for the manager's scheduled work.

## Running on Codex

Codex discovers custom agent roles from `agents/*.toml` in a config folder
(`.codex/agents/` for a project, `~/.codex/agents/` for a user). The four
subagent roles are generated for it in `codex/agents/` by
`python3 -I agents/shared/build_codex_roles.py`, each carrying its canonical
prompt as `developer_instructions`. Copy or symlink them into one of those
folders. Set a `model` in `cold-reader.toml` that differs from
`cold-reader-deep`'s, since the cold-read gate needs two distinct models. The
read-only roles set `sandbox_mode = "read-only"`; where Codex applies the
parent session's sandbox instead, the prompts' read-only rules still bind.

The session roles have no Codex role file: a Codex role configures a spawned
subagent, and a worker must be a session the owner talks to. Run them with an
explicit prompt in a new terminal:

```bash
codex "Act as the bozz-agents architect: read and follow <bozz-agents>/agents/architect.md, then run <brief path>"
```

The manager detects the missing agent view and runs in paste mode: it prints
each launch command for the owner, and workers pick up messages from their
`channel/` folder at the start and end of every turn. The shell deny hook is
Claude Code-specific; on Codex, rely on its sandbox and approval settings.

## Shell guard

Plugin agents cannot carry hooks or a permission mode, and an agent's tool
list names whole tools, not commands. So the shell guard is session-wide and
opt-in:

- **Permission rules** (`claude-settings.example.json`): `deny` and `ask`
  rules match command prefixes, so `git -C repo push --force` slips past a
  `Bash(git push --force *)` rule. They are the first line, not the only one.
- **The deny hook** (`agents/shared/shell_deny.py`) checks every Bash command
  against a family of regular expressions that see commands anywhere in the
  line (after `env`, inside `bash -c '...'`, after `;` or `&&`, with git
  options before the subcommand). Exit 2 blocks the call and tells the agent
  why. Two families live in `agents/shared/shell-deny/`:
  - `destructive`, for every session: recursive deletes of broad targets,
    disk formatting, force pushes and remote branch deletes, `git reset
    --hard`, `git clean -f`, discarding all changes, force branch deletes,
    dropping stashes, `sudo`, and cloud or cluster deletes (AWS mutating
    verbs, `gcloud`/`gsutil` delete, `az` delete, `kubectl delete`,
    `terraform destroy` and unreviewed applies). Plain `git push` is left to
    the `ask` rule: pushing is an owner-go step, not a forbidden one.
  - `readonly`, which adds every ref-moving git command and any command that
    names a credential store; use it for a session dedicated to review.

Both families are guards against accidents, not a sandbox: a command that
reaches its target indirectly (a variable, a script file) is not seen, and a
pattern can match inside a quoted argument. Each rule carries the examples it
must block, and each family the safe commands it must pass; the tests check
both.

## Testing

```bash
python3 -I -m unittest discover -s tests -p 'test_agents*.py'
```

`tests/test_agents.py` checks each role's frontmatter (name, description,
model tier, tool set), that subagent roles cannot write, that the cold-reader
pair shares one prompt on two tiers, that every skill a role names exists,
that the Codex role files are current, and that the behaviour cases in
`tests/data/agents/manager-behaviors.json` are well formed, name existing
roles, and anchor on phrases still present in the prompts.
`tests/test_agents_shell_deny.py` checks that each deny rule blocks its
examples, safe commands pass, and the hook exits 2 with a reason. The
behaviour cases themselves are for a human or an LLM judge running the role.
