---
name: context-up
description: Load just enough project context to resume work with confidence — where things stand, what's next, and the specific docs the task at hand needs. Use when the user says "context up", "load context", "pick up where I left off", "what was I working on", "what's the status", or starts a session with a task and no context loaded. Read-only; modifies nothing.
---

# Context Up

Load the minimum context needed to act with full confidence on THIS
session's task — not the whole knowledge base. The start of a session is
one bounded load printed by a script; everything past it is fetched by
heading or grep when the task reaches it. A session that may later hand
off to a successor has to start small, and a layer read whole is the
fastest way not to.

Read-only: this skill never modifies files.

## Scope

Covers: the one bounded load (work plan, decisions in force, latest
work-tracker entries, open cross-reviews, repository state, layer sizes),
and the targeted reads the session's task needs after it.

Does not cover: editing any layer (the `update-*` skills do that), reviewing
docs for consistency (`docs-review`), or re-reading the auto-loaded
orientation file.

## Procedure

### Step 1 — Run the load (one call)

From the project root, run the loader bundled with this skill:

```bash
python3 -I <this skill's directory>/scripts/load_context.py --root .
```

It resolves the layers from `context-manifest.yaml` (shipped defaults when
there is none) and prints one load capped at 28,000 characters:

- the work plan's opening block, "Next up", "Blocked" and first open items;
- the decisions in force — the hand-kept map (`IN-FORCE.md` in the
  decisions layer; see `update-decisions`) when it lists any, with its
  DRAFT line, otherwise one line per ADR with its status;
- the newest work-tracker entries' titles and the newest one's body;
- open cross-review file names under `.agent-bridge/active/`;
- the branch, uncommitted paths, stashes, worktrees and the local branches
  not yet in the default branch (each checked with `git merge-base`);
- a freshness warning when the newest entry or the plan's "As of" date is
  more than 7 days old (dates from the system clock, never reasoned);
- every other layer with its size, as a list of what a grep can reach.

**That printout is the whole load.** Do not open the files it summarized
to read them in full. A load that was cut ends with a note naming the
section cut short and each section dropped; fetch those parts by grep if
the task needs them.

### Step 2 — Determine session intent

From the user's message. If they gave a task ("implement X", "design
Y", "should we Z?"), that is the intent. If they only said "context up"
or "where did I leave off", intent is **resume**, and the load is
complete.

For each open cross-review the load lists, take its state from the
cross-review helper's read-only `review_bridge.py status --file <path>`;
never read the transcript. An open review is a pending item, not context.

### Step 3 — Targeted reads by intent

Each row lists what to fetch — by heading or `grep -n`, then only the
matching lines or section. Nothing else.

| Intent | Fetch |
|---|---|
| **Resume / status** | Nothing. |
| **Implement in package X** | The manifest-resolved rules file for X; then only the ADRs and architecture sections it cites. A spec the work plan names for the item. |
| **Design / architect** | The architecture doc's headings (`grep -n '^#' <path>`), then the sections covering the affected area; the decisions-in-force lines for that area; matching `open-questions` entries. |
| **Decide an open question** | That question's entry (grep its title) plus the ADRs and memos it links. |
| **Strategy / positioning** | The strategy layer's headings, then the sections the task names. |
| **Review (plan/code/docs)** | Nothing extra — the review skill loads its own corpus. |

**An ADR is opened only for the decision at hand**: one the task is about
to rely on, change or supersede. The decisions-in-force map (or the ADR
list) already says what binds. While the map carries its DRAFT line, the
ADR a line cites is the source for that line.

If the task spans several intents, take the union — each piece still
enters through its row.

### Step 4 — Report and confirm readiness

Print the report defined in `## Output format`, then confirm readiness.

If, once work starts, a gap appears (an uncited constraint, an
unfamiliar term), grep for it then — scoped loading means late binding,
not flying blind.

## Output format

Print a tight summary (≤10 lines):

- **Project + phase:** one line.
- **Last session:** 1–2 lines from the newest tracker entry.
- **Next up:** the plan's top open item (or the user's stated task).
- **Blockers / pending:** open blockers, Proposed ADRs awaiting sign-off,
  a DRAFT decisions map, open cross-reviews (ID + state + whose turn),
  unmerged branches or a dirty tree worth naming.
- **Freshness:** only when the loader warned — e.g. "tracker last entry
  2026-07-19 (12 days) — may be stale; verified against git log."
- **Loaded:** "bounded load (<N> characters)" plus each targeted read, by
  file and section.
- **Skipped (by design):** the loader's "Not loaded" layers and any cut
  sections — say the word to pull any in.

Then: "Context loaded. Ready to continue."

## Anti-greed contract

- **One load, then grep.** The loader's printout is the start; nothing is
  read whole after it. Long docs are reached by their headings, then the
  matching section.
- **Map before ADRs.** Decisions in force come from the map or the ADR
  list in the load; never glob or read the decisions directory.
- **Citations are the trail.** Read a doc because something already read
  cites it for this task, not because it exists.
- **Don't preload "might need".** Name it as available instead; fetch it
  when the task touches it.
- **Never load** research memos, superseded ADRs, prior work-tracker
  weeks, or the backlog unless the task is specifically about them.
- **History is not current state.** Files under any `archive/` folder
  and work folders (`<work root>/work/`) never enter the load; open one
  only when the task is about that history or that piece of work.
