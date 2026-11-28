Read this before you edit a file another live worker is working in.

# Editing a file a sibling holds

- First look at its STATUS and check the file with
  `git diff --quiet -- <file>`. You count as blocked when its `Doing now:` names the section you would edit or a
  review pass over that file (your edit would spoil the pass), or when the
  file has uncommitted changes (yours are always committed, so they are its).
- If you are clear, commit what you changed there straight away rather than
  holding it for a fold.
- A block by a sibling is never an owner item, and never a blocked item
  either, whether or not the owner is here. Report
  `STATUS: WAITING-ON-MANAGER: <session> in <file> <section>`, write
  `Doing now: waiting on <session>`, and finish the turn without polling.
  When the watcher shows the block gone, the manager's message ("the block
  has cleared; continue") opens your next turn. Then restore your STATUS and go on.
