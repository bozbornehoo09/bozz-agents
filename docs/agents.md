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
- **Sessions stay small.** Every model call re-sends the whole context, so a
  session's cost grows with its size. Workers hand off at a 350k-token cap
  and managers at 150k; prompts carry only the rules used on most turns and
  read the rest from reference files when a trigger says so.

## Roles

| Role | Tier | Tools | Started by | Main skills |
|---|---|---|---|---|
| `manager` | opus | file and shell tools, `Skill`, `SendMessage`; dispatches `general-purpose` only | the owner (`claude --agent bozz-agents:manager`), or its predecessor | `context-up`, `update-context` |
| `architect` | opus | file and shell tools, `Skill`, web; dispatches the four review roles and `general-purpose` | the manager, or the owner directly | `design-doc-write`, `design-doc-edit`, `design-doc-review`, `design-diagrams`, `writing-implementation-plans`, `plan-review`, `deciding-calls-by-debate`, `cross-review-requester`, `fold-review-findings`, `refining-technical-writing` |
| `implementer` | sonnet | file and shell tools, `Skill`, `WebFetch`; dispatches `review-specialist` and `artifact-verifier` | the manager, or the owner directly | `implementing-a-plan`, `preparing-code-reviews`, `code-review` |
| `review-specialist` | opus | Read, Glob, Grep, Bash | review skills (`docs-review`, `plan-review`, `code-review`, `skill-review`, `design-doc-review`), the architect's simplicity review | — |
| `cold-reader` | sonnet | Read | `design-doc-review`'s cold-read gate | — |
| `cold-reader-deep` | opus | Read | the same gate (it needs two distinct models per panel) | — |
| `artifact-verifier` | opus | Read, Glob, Grep, Bash, WebFetch, WebSearch | `design-doc-review`, `fold-review-findings` | — |

Tiers are Claude aliases, so each resolves to the current model of its tier.
The implementer runs on the middle tier because plans are written to a
zero-ambiguity bar (`writing-implementation-plans`) and it makes no design
calls. No role, and no subagent a role dispatches, is pinned to a
usage-billed top tier.

**Tool lists.** Each session role lists its tools, with `Agent(<types>)`
naming only the subagent types it dispatches (both `bozz-agents:<role>` and the
bare name, for an install without the plugin). Without that filter every call
carries the description of every agent installed, about 10k tokens on a
well-stocked machine; for the same reason every description is held to 50
words. The cost: a listed tool set no longer inherits the owner's own tool
servers. To use one in a session role, add its tools to that role's `tools`
line in a local copy, or delete the line to inherit everything again. The
subagent roles get the narrowest set their job needs and no write tools, and
the read-only ones start without the project's `CLAUDE.md`
(`omitClaudeMd: true`), which their briefs never need.

## Hand-offs

```
owner ──asks──▶ manager ──BRIEF.md──▶ worker session (architect | implementer)
                   ▲                       │  owner talks to it directly
                   │  STATUS.md each turn  │
                   └───────────────────────┘
   manager ──channel/MSG-<n>.md──▶ worker        (process only: commit, hand off, continue)
   worker  ──HANDOFF.md──▶ manager ──new BRIEF──▶ successor session (-2, -3, ...)
   worker  ──DONE──▶ manager spot-checks ──▶ folder archived ──▶ next workstream
   manager ──NEXT-SESSION-PROMPT.md──▶ manager-handoff.zsh ──▶ manager-<n+1>
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
5. **Handoff.** At its size cap a worker runs `update-context`, writes
   `HANDOFF.md` and reports `HANDOFF-READY`. The manager stops it and starts a
   successor from the handoff in the same folder. Where the size cannot be
   read, a worker hands off after each draft or plan closure, or every fourth
   fold, instead. A worker waiting on the owner also writes its handoff; after
   30 minutes the manager stops it, and starts the successor when the owner is
   ready to answer, so an idle session does not keep paying to re-read its
   context.
6. **Done.** The manager spot-checks the commits (branch, collisions, build or
   length budget, every output landed in its home with a cite), then archives
   the folder.
7. **Manager succession.** At its own cap the manager writes
   `NEXT-SESSION-PROMPT.md` and runs `manager-handoff.zsh handoff`: under a
   lock it starts `<project>-manager-<n+1>`, waits for it to claim
   `CURRENT-MANAGER`, then stops the old manager once it has been quiet for ten
   minutes. Workers keep running through the change.

## The worker contract and reference files

`agents/shared/worker-contract.md` holds the rules a worker uses on most
turns: the STATUS block, edits and topics, talking to the owner, owner-go
steps, the context budget and the handoff. The rest lives in
`agents/shared/reference/worker/` (work-folder layout, checkout, sibling
edits, closeout, owner steps, outward text, manager messages, unattended
mode, reviews, tools down) and the manager's in
`agents/shared/reference/manager/` (session start, briefs, messaging,
stopping, dashboard, unattended, scheduled work, end of session, paste
mode). Each prompt names a file behind a one-line trigger ("before your first
edit, read `checkout.md`"), and every reference file opens with its own
trigger. Rules marked *every session* bind an architect or implementer
started on its own too. `owner-talk.md` holds the rules for every message the
owner reads (plain terms, mechanism first, asks last, every lean labelled
with its session and model). `owner-override.md` holds the one way an owner
lifts a default limit for a named task.

Behaviour that changed with the cut (ADR-0007), beyond the size caps:

- Waits end the turn instead of polling: a worker blocked on a sibling's edit
  finishes its turn, and the manager's watcher wakes it when the block lifts.
- A worker reads its channel in the first shell call of each turn (again at
  the turn's end in paste mode); in launch mode messages arrive by
  SendMessage.
- A review specialist searches the roots a brief names before reading, then
  reads in full every file it cites; a brief's own reading rule wins.
- With tools down and the owner away, a worker hands off, unless it holds an
  open cross-review, which it keeps folding.
- An ask is spelled out once and restated in one line afterwards; a
  `WAITING-ON-OWNER` writes `HANDOFF.md`, and the manager may stop that
  session after 30 minutes so the owner answers in its successor.
- Every push and pull request waits for the owner's go, a draft included.

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
   `bozz-agents:<role>`, and the size-cap hook loads from `hooks/hooks.json`.
2. Apply the settings in `agents/shared/claude-settings.example.json` to your
   user settings (adjust the shell guard hook's absolute path):
   - background isolation off, so background workers run in the shared
     checkout and their STATUS files are visible (`worktree.bgIsolation`);
   - permission `deny` rules for destructive commands and credential reads,
     and `ask` rules for `git push` and PR state changes;
   - a `PreToolUse` hook on Bash that runs `agents/shared/shell_deny.py`
     (below);
   - optional `env` values for the size caps (below).
3. Start the manager: `claude --agent bozz-agents:manager`, and tell it the
   project and the goal; or, to run it as a background session that later
   managers succeed, write the goal to a prompt file and run
   `zsh agents/shared/scripts/manager-handoff.zsh first <work root> <project>-manager- <prompt file>`.
   It launches workers with
   `claude --bg --effort high --name <session> --agent bozz-agents:architect "Run <brief>"`.
   Open a session by its name in the agent view (or `claude attach <id>`).
   Type "dashboard" in the manager's session to see where everything stands,
   or "full dashboard" to have every source re-read first.
4. An architect or implementer also works on its own:
   `claude --agent bozz-agents:architect`, then give it the task.

### Size caps, effort and caching

- **The size-cap hook.** `hooks/hooks.json` runs `hooks/ctxcap-hook.sh` after
  every tool call, in every session that has the plugin enabled, so the
  script (`agents/shared/scripts/ctxcap.sh`) gates itself: it does nothing
  unless the hook input's `agent_type` is `bozz-agents:manager`,
  `bozz-agents:architect` or `bozz-agents:implementer` (bare names count only
  with `BOZZ_CTXCAP_BARE=1`, for agent files copied into your own agents
  directory), the call is not inside a
  subagent, and the session is at 85% of its cap. Then it adds one note per
  10k tokens to the tool result: below the cap "keep turns lean, start no new
  review pass", at the cap "hand off now". A session that starts large (a
  successor reading its handoff) and one whose handoff just failed get a 40k
  margin first. It needs `zsh` and `jq` and exits quietly without them.
  Settings (environment, so in the user settings' `env` block, which
  background sessions also read): `BOZZ_CTXCAP=off`, `BOZZ_CTXCAP_WORKER_K`
  (default 350), `BOZZ_CTXCAP_MANAGER_K` (default 150), `BOZZ_CTXCAP_BARE` (default 0). The opt-in shell
  guard is unchanged.
- **Effort.** Workers launch with `--effort high`; the manager and sessions
  the owner starts keep the owner's setting.
- **Prompt cache.** A manager mostly idles between wakes, so it keeps a
  one-hour prompt cache: `experimental.cacheTtl: 1h` in its frontmatter, and
  `--settings '{"promptCacheTtl":"1h","idleCompaction":false}'` on every
  launch `manager-handoff.zsh` makes (idle compaction off, since a manager's
  state moves only through the handoff it writes). Workers call without long
  gaps and stay on the default five-minute cache; a one-hour write costs more.
  Add the same `--settings` to a manager you start by hand.

### Helper scripts

The manager's helpers in `agents/shared/scripts/` need `zsh` and `jq` and use
Claude Code's agent-view commands (`claude agents --json`, `claude stop`,
`claude respawn`); confirm them with `claude --help` on your version.

- `sessions.zsh` holds the shared reads every script uses: a session's
  transcript, the size of its newest call (input + cache read + cache write
  tokens, subagent records left out), and whether its turn has ended.
- `ctxpct.sh [-k] <session>` prints a session's size as a percentage of the
  window (`CONTEXT_WINDOW_TOKENS`, default 1M) or, with `-k`, in thousands of
  tokens.
- `ctx.sh <prefix>` prints one line per live session with that name prefix.
- `ctxcap.sh` is the size-cap hook (above); `ctxcap.sh hold <session id>`
  records a hold after a failed handoff.
- `watch.zsh snap|start|stop` is the manager's watcher. It checks once a
  minute but wakes the manager only on a change it must act on: a STATUS
  line, a handoff, an unread message, a session's status, a blocker's file
  turning clean, or a worker past its cap. It respawns a worker the agent
  view retired while it waited, and its stop accepts a finished worker, a
  predecessor whose brief names a successor, and a 30-minute owner wait with
  a handoff, waiting for ten quiet minutes between turns.
- `manager-handoff.zsh claim|current|handoff|first` is manager succession
  (above).

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

The manager detects the missing agent view and runs in paste mode
(`agents/shared/reference/manager/paste-mode.md`): it prints each launch
command for the owner, workers pick up messages from their `channel/` folder
at the start and end of every turn, and manager succession is off. The
size-cap hook and the shell deny hook are Claude Code-specific; on Codex a
worker measures nothing and hands off on the draft and fold triggers, and the
sandbox and approval settings stand in for the shell guard.

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
both. The size-cap hook is the one plugin-wide hook, and it changes nothing
outside the three session roles.

## What is not verified

These behaviours are relied on but were not observed in a real session when
this was written; check them on your version.

Checked on Claude Code 2.1.332 (2026-11-27, one background Haiku session):
`CLAUDE_CODE_SESSION_ID` is set in a session's shell; `--settings` accepts an
inline JSON string; `claude agents --json --all` gives a background session an
eight-character `id` beside its `sessionId`, and lists a stopped one with no
`status` and `state: "done"`; `claude stop <id>` prints `stopped <id>`; a
finished turn's last transcript record is `system` / `turn_duration`; a
plugin agent started with `--agent <plugin>:<name>` reaches a PostToolUse hook
as `agent_type: "<plugin>:<name>"` with no `agent_id`.


- That `experimental.cacheTtl` in an agent file applies when that file runs
  the main conversation (`claude --agent`), not only to a subagent.
- That a background session honours `promptCacheTtl` and `idleCompaction`
  from inline `--settings` JSON (the flag accepts the JSON; whether the
  values take effect was not observed).
- That a session whose turn has ended lists as `busy` while a background task
  it started still runs.
- That `Agent(<types>)` in `tools` accepts plugin-scoped names
  (`bozz-agents:review-specialist`).
- The 40k start margin, the ten-minute quiet window and the 600-second claim
  wait are judgement, not measured.

## Testing

```bash
python3 -I -m unittest discover -s tests -p 'test_agents*.py'
```

`tests/test_agents.py` checks each role's frontmatter (name, a description of
at most 50 words, model tier, tool list and the subagent types it may
dispatch, `omitClaudeMd` on the read-only roles, the manager's one-hour
cache), that subagent roles cannot write or dispatch, that the cold-reader
pair shares one prompt on two tiers, that every skill a role names exists,
that every reference file a prompt names exists and opens with its trigger,
that the Codex role files are current, and that the behaviour cases in
`tests/data/agents/manager-behaviors.json` are well formed, name existing
roles, and anchor on phrases still present in the prompts.
`tests/test_agents_shell_deny.py` checks that each deny rule blocks its
examples, safe commands pass, and the hook exits 2 with a reason.
`tests/test_agents_scripts.py` runs the size-cap hook, the watcher and
manager succession against a fake `claude` (`tests/data/agents/stub/claude`)
and made-up transcripts; nothing starts the real CLI. The behaviour cases
themselves are for a human or an LLM judge running the role.
