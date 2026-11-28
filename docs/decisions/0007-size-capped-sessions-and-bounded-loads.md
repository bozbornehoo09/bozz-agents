# ADR-0007: Size-capped agent sessions, manager succession and bounded loads

**Status:** Accepted
**Date:** 2026-11-27
**Category:** Infrastructure
**Extends:** [ADR-0005](0005-shipped-manager-worker-agents.md) (does not supersede it)

## Context

Most of a long agent session's cost is context re-read on every call: each
call pays again for the whole conversation so far, so a session that grows
past a few hundred thousand tokens costs far more per step than a fresh one
doing the same step. The 0.5.0 agents let sessions grow until compaction,
re-read long prompts (the manager's alone was about 4,000 words) and a full
agent list on every call, woke the manager on a fixed poll, and started each
session by reading whole layers. In the maintainer's private build, replays of
the same work with these causes removed cost 26–62% less at equal blind-judged
quality, and session start-up context fell by about 40%.

## Decision

1. **Sessions hand off at a size cap.** A PostToolUse hook
   (`hooks/hooks.json` → `agents/shared/scripts/ctxcap.sh`) tells a session
   role to keep turns lean from 85% of its cap and to hand off at the cap
   (defaults 350k tokens for architect and implementer, 150k for the manager,
   set by environment). A manager hands off to its own successor
   (`agents/shared/scripts/manager-handoff.zsh`, under a lock, with a
   `CURRENT-MANAGER` claim).
2. **The hook ships enabled and gates itself.** A plugin hook runs in every
   session, so the hook is silent unless the hook input names a session role
   of this plugin and the call is not inside a subagent, and it always exits 0.
   `BOZZ_CTXCAP=off` turns it off. The shell-deny hook stays opt-in
   (ADR-0005): it changes what a session may do, while this one only adds a
   note to sessions that are already this workflow's.
3. **Prompts carry only what every call needs.** Rare rules live in
   `agents/shared/reference/{manager,worker}/` behind one-line triggers; the
   tests check that every trigger names an existing file and no file is
   orphaned.
4. **Each session role lists only the subagent types it dispatches**
   (`Agent(...)` in `tools`), descriptions stay at 50 words or fewer, and the
   read-only reviewer roles start without the project's instructions file
   (`omitClaudeMd`).
5. **The manager keeps a 1-hour cache** and idle compaction off, because it
   idles between wakes; workers keep the default cache and launch at
   `--effort high`. The watcher wakes the manager only on an actionable change.
6. **Loads are bounded.** `context-up` loads through one capped script call
   (`skills/context-up/scripts/load_context.py`), update skills read layers by
   that load, headings and grep, and a hand-kept `IN-FORCE.md` map stands in
   for reading every ADR. `update-context/scripts/work_check.py` refuses to
   close a work folder while a result exists only inside it, so no result is
   lost when a capped session stops.

## Alternatives considered

- **Rely on compaction.** Rejected: a compacted session still re-reads its
  summary and prompt on every call and loses detail unpredictably; a handoff
  file is explicit and reviewable.
- **Ship the size cap opt-in like the shell guard.** Rejected: the cap is the
  main saving and the hook is inert outside this workflow's sessions.
- **Keep the full tool list on session roles.** Rejected: the agent list alone
  cost about 10k tokens a call. Cost: a role with a listed tool set no longer
  inherits the owner's own tool servers; `docs/agents.md` says how to add them.

## Consequences

- **Positive:** long work costs less per step, and every handoff leaves a file a
  person can read.
- **Negative:** more moving parts (hook, succession lock, watcher rules), some
  of which depend on Claude Code behaviour only a live session shows;
  `docs/agents.md` lists what is not yet verified.
- **Binds:** a new session role MUST be added to the hook's role list and given
  an `Agent(...)` allowlist; a rule moved out of a prompt MUST keep a trigger
  line pointing to its reference file; the hook MUST stay silent and exit 0
  outside its roles.
- **Revisit when:** Claude Code offers a native per-agent size cap or handoff,
  or live measurements disagree with the replays.

## References

- `hooks/`, `agents/shared/scripts/{ctxcap.sh,manager-handoff.zsh,sessions.zsh,watch.zsh}`,
  `agents/shared/reference/`, `docs/agents.md`
- `skills/context-up/scripts/load_context.py`,
  `skills/update-decisions/scripts/adr_index.py`,
  `skills/update-context/scripts/work_check.py`
- Tests: `tests/test_agents.py`, `tests/test_agents_scripts.py`, and each
  skill's `scripts/test_*.py`
