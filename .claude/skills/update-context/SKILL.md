---
name: update-context
description: Discover what changed across the project and dispatch only the needed narrow update skills in dependency order, ending with a single consolidated docs-review. Use at the end of a working session, after a major decision, or anytime you want to lock in everything that changed.
---

# Update Context

The end-of-session one-stop. Discovers what has changed across the
project, identifies which authoritative content needs updating, invokes
only the narrow update skills that are needed, and ends with a single
comprehensive `docs-review`.

Use at the end of a working session, after a major decision, or
anytime you want to lock in everything that changed. Prefer this skill
over running the narrow skills manually — it shares discovery, picks the
right ordering, and runs review only once.

## Authoritative content layers

Each layer has its own narrow update skill, and its path is declared in
`context-manifest.yaml` (the shipped defaults are shown below). This
orchestrator dispatches to them based on what discovery surfaces.

| Layer | Path | Owning skill |
|---|---|---|
| WHY (decisions) | `docs/decisions/` | `update-decisions` |
| Strategy (positioning) | `docs/strategy/` | `update-strategy` |
| Architecture (synthesis) | `docs/architecture/` | `update-architecture` |
| WHAT (per-package rules) | `.claude/rules/` | `update-rules` |
| AI tooling | `.claude/skills/` (per-skill `references/`) | `update-skills` |
| Open questions | `docs/open_questions.md` | `update-open-questions` |
| FORWARD (work plan) | `work_tracker/work_plan.md` | `update-work-plan` |
| Backlog (longer-term) | `work_tracker/backlog.md` | `update-backlog` |
| Project orientation | `CLAUDE.md` / `AGENTS.md` | `update-orientation` |
| WHEN (activity log) | `work_tracker/` | `update-work-tracker` |

ADRs are upstream truth. Strategy and architecture reflect them. Rules
cite both. Skills evolve when conventions shift. Open questions
reconcile as ADRs land. The work plan reconciles with what landed, and
the backlog parks longer-term tasks until they are scheduled. The
orientation file summarizes the whole. The work tracker logs the
session.

## Procedure

### Step 1 — Comprehensive discovery (one subagent call)

The current conversation is your PRIMARY source for in-session
decisions, intent, and rationale. Capture these directly — a subagent
cannot see them.

For everything mechanical, spawn ONE Explore subagent with this brief:

> "Discover what's changed in <project-root> since
> <timestamp> across all authoritative content. Map findings to one
> or more of these skills:
>   - update-decisions (new ADR-worthy decisions, supersedence)
>   - update-strategy (positioning shifts, new research artifacts)
>   - update-architecture (new services, ports, principles, diagram changes)
>   - update-rules (rule changes driven by new ADRs or design shifts)
>   - update-skills (new corpus directories, new specialist briefs, contract refinements)
>   - update-open-questions (questions resolved by new ADRs, new questions surfaced)
>   - update-work-plan (plan items landed/in-flight/dropped, new work discovered, blockers)
>   - update-backlog (longer-term tasks now scheduled out, or newly deferred in)
>   - update-orientation (drift between the orientation file and current state)
>   - update-work-tracker (always — captures the session)
> Check: git log --since=<ts>, git status, and file mtimes under the
> paths declared in context-manifest.yaml (decisions, strategy,
> architecture, rules, the skills directory, docs, work_tracker) plus
> the source tree, plus the most recent work_tracker/ entry. Report a
> tight bullet list mapping each finding to the skill(s) that should
> handle it. Under 400 words."

Timestamp anchor: prefer the timestamp of the most recent
`work_tracker/` entry. If none, fall back to the start of the current
week.

### Step 2 — Categorize and confirm the dispatch plan

From your conversation + the subagent's report, build the list of
narrow update skills that need to run. Print the dispatch plan in the
format defined in `## Output format` and pause for confirmation. The
user may add a domain the discovery missed, or remove one they don't
want touched.

### Step 3 — Invoke narrow update skills in dependency order

Run only the skills in the confirmed plan, in this order:

1. `update-decisions` — ADRs decide; everything else reflects them.
2. `update-strategy` — strategy is parallel to ADRs but often
   re-evaluated when ADRs land. Run before architecture/rules.
3. `update-architecture` — synthesizes ADRs; rules cite it.
4. `update-rules` — cites ADRs and architecture.
5. `update-skills` — only if doc conventions changed (new ADR
   Status value, new doc directory, etc.).
6. `update-open-questions` — reconcile resolved questions after
   ADRs land.
7. `update-work-plan` — reconcile the forward plan once decisions
   and questions have settled.
8. `update-backlog` — reconcile the longer-term parking lot; promote
   anything now scheduled into the plan (run after `update-work-plan`).
9. `update-orientation` — orientation is downstream of everything.
10. `update-work-tracker` — always last; logs the entire session.

**Suppress per-skill reviews during this sweep.** Each narrow update
skill that has a review hook (`docs-review` or `skill-review`) runs it
for standalone use. When invoked from this orchestrator, skip the
per-skill review — a single comprehensive review runs in step 4.
Likewise, narrow skills skip their own discovery subagent during a
sweep — reuse the step 1 discovery findings instead.

### Step 4 — Final comprehensive review (in parallel)

After all narrow update skills complete, invoke the appropriate review
skills **in parallel** against the current state. They operate on
disjoint corpuses and have no dependency on each other's output:

- Always run `docs-review` (covers ADRs, strategy, architecture, rules,
  the orientation file).
- If `update-skills` ran in this sweep, also run `skill-review`
  (covers the skills directory and each skill's `references/`).

Both reviews are standalone skills — they are not exclusive to the
narrow update skills that call them. The orchestrator invokes them
directly here. Each review internally fans out to 4 specialists in
parallel, so a sweep that runs both reviews has up to 8 specialists
running concurrently.

Read each report and either:
- **READY** → that review's domain is clean.
- **READY-WITH-FIXES** → surface findings to the user; address or
  defer per their direction.
- **REVISE** → BLOCK findings present; the sweep is not complete
  until they are resolved. Common cause: a propagation gap (concept
  added to ADR but missed in rules) — usually a follow-up
  `update-rules` invocation.

The sweep is complete when both review skills (the ones that ran)
return `READY` or `READY-WITH-FIXES` and any deferred findings have
been surfaced to the user.

### Step 5 — Confirm sweep complete

Surface the final summary defined in `## Output format`.

## Output format

**Dispatch plan** (print before executing; pause for confirmation):

```
Dispatch plan:
- update-decisions — <one-line reason>
- update-architecture — <one-line reason>
- update-rules — <one-line reason>
- update-work-plan — <one-line reason>
- update-work-tracker — always
- (skipping: update-strategy, update-skills, update-open-questions, update-orientation — no changes detected)
```

**Final summary** (print after all skills complete):

- Which skills ran.
- Which skills were skipped (and why).
- The final `docs-review` verdict.
- Any deferred findings.

## Style across all layers

- Bullet points, not prose. Terse. One line per item where possible.
- Plain language; rules and tracker are read by humans too.
- Be honest. Half-formed decisions are Proposed, not Accepted.
  Negative consequences belong in ADRs alongside positives.
- Cross-reference always: ADR ↔ rule ↔ architecture ↔ tracker entry.

## Narrow alternatives (when not to use this orchestrator)

If you only need to update one layer in isolation and you trust that
no other layer is affected, skip this orchestrator and call the
narrow update skill directly:

- `update-decisions` — single ADR mid-session
- `update-strategy` — strategy doc edits without ADR work
- `update-architecture` — design doc / diagram changes
- `update-rules` — rule changes without sweep
- `update-skills` — skills + their `references/` briefs
- `update-open-questions` — question reconciliation only
- `update-work-plan` — plan reconciliation only
- `update-backlog` — longer-term backlog reconciliation only
- `update-orientation` — orientation drift only
- `update-work-tracker` — log without other changes

Each narrow update skill runs its own review at the end:
- `update-decisions`, `update-strategy`, `update-architecture`,
  `update-rules`, `update-orientation` → `docs-review`
- `update-skills` → `skill-review`
- `update-work-tracker`, `update-work-plan`, `update-backlog`,
  `update-open-questions` → no review hook (work tracker, work plan, and
  backlog are not authoritative; open questions are excluded from review
  scope by definition)

Prefer this orchestrator for end-of-session updates — it shares
discovery and runs `docs-review` only once.
