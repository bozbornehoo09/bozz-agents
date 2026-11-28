Read this before the first file you write in a session.

# The work folder and homes

This is the one definition of the work folder's layout:

```
<work root>/work/<YYYY-MM-DD>-<workstream>/
  BRIEF.md                 manager writes it; you never commit it
  STATUS.md                you overwrite it each turn; you never commit it
  HANDOFF.md               you write and commit it when you hand off
  channel/MSG-<n>.md       manager's process messages; once done, move to channel/read/
  DECISION-<n>.md          a manager's call between workers; the manager commits it
  OWNER-STEP-<n>.md        a step you hand the owner; its outcome is OWNER-STEP-<n>-result.md
  passes/<date>-pass-<N>/  a pass's review reports and review file, committed with its fold
  scratch/STATE.md         state for a long loop, 40 lines at most
```

- Nothing your work makes goes at the project root, and nothing lives on in
  `/tmp`.
- The folder records where a result came from; it is not where the result
  lives. Write each result's facts into its home (the brief names one for each
  output it asks for) and end each such line with a cite back to its record,
  for example `(source: work/2026-03-02-retry-api/passes/2026-03-03-pass-2/)`.
  A home must still read correctly once the folder is archived. The cite keeps
  its `work/<id>/…` form after the folder moves to `work/archive/<id>/`, and a
  home cites a folder this way; it never links into one by path.
- **Results and records.** `DECISION-<n>.md` and `OWNER-STEP-<n>-result.md` are
  results: each needs a citing line in a home. `BRIEF.md`, `STATUS.md`,
  `HANDOFF.md`, `OWNER-STEP-<n>.md`, `channel/`, `passes/` and `scratch/` are
  records.
- Anything you leave open becomes an **owner item**: a line in your own words,
  citing its record, in the work plan's list of owner items. Mentioning it in
  STATUS does not make it one.
- When you rewrite a record (a design note, a pass's review file), its
  account of earlier steps stays: append the new decision and your action,
  and leave every earlier resolution in place.
- Only the manager closes folders, and only after `DONE`: it checks that each
  output has a citing line in its home, moves the folder to
  `<work root>/work/archive/` and commits. Where `update-context` ships
  `scripts/work_check.py`, that is `work_check.py close <id> --session <your session> --dry-run`,
  then the same without `--dry-run`. Closing is refused while a result is uncited,
  an `OWNER-STEP-<n>.md` has no result file, a home links into the folder, or
  a file over 1 MB that git does not ignore would be committed. A handoff leaves the folder in
  place for your successor.
- No manager: open the folder yourself, laid out the same way, and close it
  the same way when your task ends.
