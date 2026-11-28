Read this before you first edit a file, or run git, in any repository.

# The checkout and its branches

- Work in the checkout and on the branch the brief gives. Before your first
  commit, read the branch rules file the brief names (or the branch section of
  the project orientation file); where they and the worker contract differ,
  they win.
- An integration branch is off limits unless the brief makes you its
  integration worker. Create no worktree or branch of your own unless the
  brief or the branch rules ask for one.
- If the host will not let you edit the checkout, report
  `STATUS: WAITING-ON-OWNER: checkout blocked` and stop there; no workarounds.
- Other workers commit in the same checkout. A git `index.lock` error means
  wait and try again; never remove the lock.
- **A refused git command on your own branch.** Claude Code's auto mode may
  refuse a command that moves a branch (for example `git reset --keep` on a
  candidate branch you made for this task). On a branch only you use, you may
  reach the same state another way: tag the branch's current commit first,
  detach HEAD (`git checkout --detach`), point the branch at the commit you
  want (`git branch -f <branch> <commit>`), and switch back to it
  (`git checkout <branch>`), issuing each git command as its own call since
  git will not move a branch while it is checked out. Note the tag and every
  command in your work folder. On a branch anyone else uses, report
  `WAITING-ON-OWNER: <command> refused` and stop.
