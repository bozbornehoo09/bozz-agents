Read this as soon as any lane has a pull request (open or planned), when a
lane's next step depends on something another lane produces or one PR depends
on another, and whenever the owner asks for a "full dashboard". Otherwise
the dashboard uses nothing from this file.

# Dashboard: lead, graph and tables

Here a lane means one workstream, running or not yet begun, and a unit is
whatever a step can depend on: a PR, a deploy, a doc or one of its sections,
an owner call, a review.

## Order, scope and read times

- Nothing is left out. The current milestone's series and lanes come first
  (the goal in `MANAGER-STATE.md`, else the work plan's first next-up
  block), then everything else.
- When only part of the rows were read again, the dashboard says which: its header gives each
  source's read times as a range, and a note under each table gives the read
  time, in the owner's zone, of every row not re-read for it. Outside a full
  dashboard, a lane change re-reads that lane's rows and the rows that depend
  on them.
- A **full dashboard** first re-reads every source, both those this file
  draws on and those behind the worker lines.

## The parts, in this order

These go above the worker lines.

1. **Lead**, two or three lines: what changed since the last dashboard and,
   when a table lists PRs, the counts: merged today, ready to merge now,
   ready once one upstream PR merges.
2. **Prerequisite graph**, in a code block. One node per unit. An arrow means
   "has to be done, as labelled, before", and its label is the condition
   (merged, deployed, decided, review clean). Draw only the critical paths,
   meaning the chains some waiting step depends on, and carry each one through
   to the step where its user can see the result (deployed where they use it,
   released, published). If no source you read names that last step, stop
   the path at the final unit a source does name, with a note saying so. No arrow that only means
   "feeds into".
3. **One table per PR series**, in graph order (a series that gates another
   comes first), titled with the series' purpose as its PR descriptions put
   it. Never invent a grouping: a change outside every series sits in the table
   of whichever series it gates or depends on, or else gets a one-row table
   under its own title.
   Columns `Part | Change | Depends on | Ready to merge? | Worker: doing now | Needs you`,
   each row after every row it depends on.
   - Change: the PR linked on its own text with a short note of its effect;
     for one not yet opened, `<its effect> (not opened)`.
   - Depends on: `INDEPENDENT` when every source for it was read and none
     names a wait (a failed read is `unread`); `NEXT UP` once whatever it
     waited on is done; otherwise the unit it waits on and the condition,
     from the PR's own stated merge order.
   - Ready to merge?: `Yes` when approval is all that is left; otherwise
     `No:` and the missing step; `Merged <time>` after it merges.
   - Worker: doing now: the workstream and a few words of its `Doing now:`
     (the whole line in a note), or `none`. A `No:` row with no worker gets a
     note on what it needs and who could do it.
   - Needs you: each step in plain words, or `nothing`.
4. **One table per phase** for lanes with no PR (design work), columns
   `Lane | Artifact | Depends on | State | Worker: doing now | Needs you`;
   State is the artifact's own state (review clean, approved, published), and
   the other columns follow item 3.

## Rules for every part

- Cells stay near 40 characters so a terminal can draw the table; quotes,
  evidence and conditions go in numbered notes beneath it, and no detail is
  dropped to make something fit.
- An arrow or a dependency appears only where a source you read states it:
  a PR's merge order, a brief, the work plan, a plan's gates, a fresh STATUS.
  A STALE row has `STALE (<age>)` in its worker cell and no item.
- A read that failed shows `unread`, never a guess. If the tool behind it has
  dropped, add `reconnect <tool> in <your session>` to What to prioritize.
