---
name: update-work-tracker
description: Append a session entry to the activity log (the WHEN layer). Use at the end of a session to record what changed, what was decided, and what was deferred. No review hook (the work tracker is not authoritative).
---

# Update Work Tracker

Update the work tracker at <project-root>/work_tracker with
everything done since the last entry. The work tracker is the WHEN layer:
short activity logs indexed by date, NOT deep rationale (rationale lives
in `docs/decisions/` ADRs).

## Scope

In scope:
- the weekly directories and daily entries under `work_tracker/`
  (plus each week's README.md summary)

Out of scope:
- the forward work plan `work_tracker/work_plan.md` →
  `update-work-plan`
- the backlog → `update-backlog`
- rationale → ADRs via `update-decisions`

## Steps

### 1. Determine today's date and the target paths

Never compute weekdays, week numbers, or week boundaries by reasoning
about the calendar. Run the read-only helper from this skill's directory
and use its output verbatim:

```bash
python3 scripts/tracker_path.py --root <work-tracker-path>   # today
python3 scripts/tracker_path.py --root <work-tracker-path> --date YYYY-MM-DD
```

It prints the week folder, day folder, entry path, whether each exists,
and `existing_*_folder` when a folder already covers the same dates under
a different spelling. Reuse an existing folder and report the mismatch —
never rename it or create a duplicate. With no shell, take the date from
the environment context and apply the convention below carefully.

### 2. Find the correct weekly folder

Convention: `week_<NN>_<M-D>_<M-D>` (Sun→Sat), e.g. `week_27_6-28_7-4`,
where `NN` is the ISO week number of the Monday inside the week. A week
may span two months or two years; never split it at the edge.

If this week's folder does not exist, PAUSE and confirm before creating it.
When creating, also write a 1–2 line `README.md` summarizing the week's
intended focus.

### 3. Find or create today's daily folder

Inside the week folder: `<dayofweek>_<M>-<DD>/` (e.g. `thursday_7-02/`).
The daily entry lives at `<dayofweek>_<M>-<DD>/entry.md`.

If the entry already exists, PAUSE and ask whether to append a timestamped
section, replace it, or cancel.

### 4. Discovery

PRIMARY SOURCE — the current conversation. In-session decisions and intent
ONLY exist in the main thread's context.

SECONDARY SOURCES — run ONE discovery subagent using the host's subagent or
delegation facility:

> "Discover what's changed in <project-root> since
> <timestamp>. Check: `git log --since=<ts>` + `git status`; file mtimes
> under source, infrastructure, manifest-resolved rules, docs, and prompts; the most
> recent file in work_tracker/<current-week>/ for the prior baseline; any
> new files in docs/decisions/. Report a tight bullet list of what
> changed and where, with file paths. Under 300 words."

Timestamp anchor: prefer the timestamp of the most recent existing tracker
entry. If there is none, fall back to the start of the current week.

### 5. Synthesize the entry

Sections (omit any with no content):
- **Decisions** — `Decided X for Y. → ADR-NNNN` or
  `Decided X (no ADR — minor)`. One line each. Do NOT explain why — the
  ADR holds that.
- **Implemented** — concrete things built or changed, with file paths
- **Rules updated** — list manifest-resolved rule files touched (with
  `→ ADR-NNNN` citations where relevant)
- **Open questions** — unresolved items to revisit
- **Up next** — a pointer to the work plan's "Next up"
  (`work_tracker/work_plan.md`), noting only what changed this session.
  The plan owns the forward view — do not restate the queue here.
- **Reviews** — cross-review threads opened, folded, or closed this
  session: review ID, round, outcome, one line each. Read state with
  `review_bridge.py status`; the transcript stays the evidence — never
  copy it here or edit it.

Capture the why and how of investigations in one line each (what was
tried, what the evidence showed), not just the what. When an earlier
position changed, write "originally X; after Y, now Z" rather than
dropping X. Deep rationale still belongs in an ADR.

## Pause-for-confirmation rules

- PAUSE before creating a new week folder.
- PAUSE before overwriting an existing daily entry (offer: append,
  replace, or cancel).
- Otherwise apply directly and report what was written.

## Style

- Bullet points, not prose. Terse. One line per item where possible.
- Cross-reference ADRs by number; cross-reference rules by file path.
- Do not edit prior daily entries, only the current one.
- Never edit, reformat, or move files under `.agent-bridge/`; they are
  append-only review evidence.
