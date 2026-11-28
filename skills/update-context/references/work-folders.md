# Work folders: the checker

The work-folder layout, the record files, the cite form and who closes a
folder are defined once, in the worker reference (`agents/shared/reference/worker/work-folder.md`,
"The work folder and homes"). This file does not restate that rule. It says how
`scripts/work_check.py` reads it, so a result never lives only in a stopped
session or in a folder about to be archived.

## What the script treats as what

- **Work root**: the `work-tracker` layer's path in `context-manifest.yaml`
  (`work_tracker/` when unset). Open folders are `<work root>/work/<id>/`,
  closed ones `<work root>/work/archive/<id>/`, where `<id>` is
  `<YYYY-MM-DD>-<workstream>`.
- **Homes**: the Markdown in every manifest layer, the orientation files, and
  each `--home <path>` given (the files a goal is about that sit outside the
  layers, such as a design doc). Nothing under `<work root>/work/` is a home.
- **Records**: `BRIEF.md`, `STATUS.md`, `HANDOFF.md`, each `OWNER-STEP-<n>.md`
  prompt, and everything under `channel/`, `passes/` and `scratch/`. Records
  need no cite.
- **Results**: every other file in the folder, a `DECISION-<n>.md` and an
  `OWNER-STEP-<n>-result.md` included. Each needs a home line ending in
  `(source: work/<id>/<path>)`. A cite of a subfolder covers the files below
  it; a cite of `work/<id>/` covers the whole folder. A cite keeps its
  `work/<id>/` form after the folder is archived; the script looks for it in
  both places.
- **Fenced code and inline code spans** are skipped, so a documented example
  is never reported as a dead link or a stray `/tmp` path.

## Commands

All take `--root <project root>` (default `.`), `--manifest <file>` and any
number of `--home <path>`. Output is one line per finding, with paths relative
to the root.

### `check` (read-only; exit 0)

`FIX <class> <file>:<line> <detail>`, or `OK no work-folder findings`:

| Class | Meaning |
|---|---|
| `misplaced` | a brief, status, handoff, message, decision or owner-step file outside a work folder (project root, work root, `work/`); a loose file in `work/`; an `MSG-` file outside `channel/`; a `STATE.md` outside `scratch/` |
| `bad-folder-name` | a folder in `work/` whose name is not an id |
| `id-twice` | an id that is both open and archived |
| `state-too-long` | `scratch/STATE.md` over the contract's 40 lines |
| `dead-link` | a relative Markdown link in a home whose target does not exist |
| `tmp-path` | a home naming a path under `/tmp`; nothing kept lives there |
| `work-link` | a home linking into a work folder by path; the archive move would break it, so cite it instead |
| `unresolved-cite` | a `(source: work/<id>/…)` whose folder or file is in neither `work/` nor `work/archive/` |
| `bad-cite` | a work cite whose id is malformed |

A dead link is repaired by pointing it at the file's current path; the
words of the line stay as they are, ADRs and dated log lines included.

### `close <id> --session <name> [--dry-run]`

Run by whoever closes folders under the contract (the manager, or a session
working without one, at its end). It refuses, one `REFUSE <class> …` line
each and exit 1, while:

- `STATUS.md` exists and does not read `STATUS: DONE` (`not-done`);
- a result has no citing home line (`uncited`);
- an `OWNER-STEP-<n>.md` has no `OWNER-STEP-<n>-result.md` (`owner-step-open`);
- a file the close would commit is over 1 MB and not gitignored (`large`):
  move it out of the repository or ignore it;
- a home links into the folder by path (`work-link`).

Otherwise it moves the folder to `work/archive/<id>/` and makes one commit,
`[<session>] close work/<id>`, naming only the moved paths, so files another
worker staged are never swept in. `BRIEF.md`, `STATUS.md` and `channel/` move
with the folder but stay uncommitted, as the contract requires. It prints
`CLOSED <from> -> <to> <commit>`, or `WOULD-CLOSE` under `--dry-run`. If a git
step fails, the folder is moved back and the staged paths unstaged.

### `handoff <id>` (read-only)

Run after writing `HANDOFF.md` and before reporting `HANDOFF-READY`. Prints
`OK` (exit 0) when every result is either cited by a home or named in
`HANDOFF.md` by its folder-relative path or `work/<id>/<path>`. Otherwise it
prints `MISSING <path>` per such result, or `MISSING …/HANDOFF.md` when the
file is absent, and exits 1. Land each result in its home, or name it with
its home in `HANDOFF.md`, and run it again.

## Fixing `check` findings

`check` only reports; a fix is proposed first and applied on approval, by the
skill that owns the file holding the broken line (a stray file at the root is
`update-context`'s own). Per finding:

- **Dead link or gone `/tmp` path:** repoint it when exactly one present path
  fits (for a work-folder file, as a `work/<id>/…` cite); with no single
  candidate, replace the link with `(gone: <path>)`.
- **Link into a work folder:** rewrite it as a cite.
- **Misplaced file** (at the root, or loose in `work/`): move it into the work
  folder it belongs to, never over an existing file, then turn any home's link
  to it into a cite.
- **No single right answer** (two candidate folders, a name already taken):
  list it as an owner item instead of choosing.

Apply moves before link edits, then run `check` again and report what is
left. Fixing findings never closes a folder, never edits a result file and
never edits an ADR beyond a link path.
