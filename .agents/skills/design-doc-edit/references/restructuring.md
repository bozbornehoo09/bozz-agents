# Restructuring a Design Doc

The restructure procedure for `design-doc-edit` step 5. A restructure means reordering
sections, moving detail into appendices, rebuilding a doc solution-first, renumbering, or
any of these across a set of docs. It fails in ways the rubrics and the cold read do not
catch: facts lost when a dense block is retyped, a block duplicated or stranded by a
move, cross-references left pointing at the old layout. Follow this alongside the
rubrics, then continue with `design-doc-edit` step 7.

## Doing the edits

- **Edit in place, in small steps; never rewrite the whole file.** Change headings, move
  blocks, reformat one appendix at a time. Leave dense verbatim blocks (schemas,
  interface definitions, algorithms, large tables) physically untouched. Retyping a dense
  block from memory is where facts get lost. Prefer many small, uniquely anchored edits
  over one whole-file write.
- **Work in an order that survives being interrupted:** header and glossary first; then
  the body (build the new sections and add the `## Appendices` divider); then appendix
  moves and reformatting; then the cross-reference sweep **last**. A sweep done before
  the structure settles has to be redone.
- **Copy before you delete.** When moving body content to an appendix or to another doc,
  add it at the destination before removing it from the source, so an interruption loses
  nothing. If the destination is a file you are not editing now, either copy there or
  leave a clearly marked "move pending" note; never delete on the promise of a later
  move.
- **Solution-first shape.** Lead with the people the design serves, then the solution; a
  settled choice's comparison moves to a decision register after the divider
  (`../../design-doc-write/references/structure-rubric.md` S4). When all major choices
  come from a parent doc, one context appendix and the divider is the right shape; do not
  invent a register.

## Checking the result

- **Conservation check, after the moves and before the cross-reference sweep.** These are
  mechanical and catch what reading does not: (a) for every moved block, search for a
  distinctive phrase and confirm it appears exactly once (catches duplication); (b) list
  the headings and confirm none repeats (catches a block stranded under a re-added
  heading); (c) compare line counts before and after against the change you expect.
- **Cross-reference sweep, once, at the end, by referent.** Search for section numbers,
  `§`, appendix letters used in prose, and `#anchor` links. Sort each hit: **internal** (a
  bare number in this doc; remap it to the new numbering) or **external** (a number
  attached to a link to another doc; leave it, that doc numbers itself). Remap by what each
  reference points at, not by a blanket shift: a section split in two sends each
  reference to whichever half it means, and a section moved to an appendix turns numeric
  references into named appendix references.
- **A multi-doc restructure needs a reconciliation pass.** When several docs renumber at
  once, every inbound reference between them goes stale together. Build an old-to-new map
  for each doc (including removed or renamed appendices and where their content went),
  rewrite every inbound cross-doc reference against the target's new layout, and finish
  with a search confirming every cross-doc number exists in its target.
- **Fidelity check.** Compare counts of load-bearing tokens (field names, numeric
  constants, error codes) before and after, against the last committed version
  (`grep -c`, or a token diff). The cold read does not do this.

## Keep the doc set's conventions

- **A convention the docs already lock in beats a general style preference.** If the set
  uses a fixed marker for open gates, or keeps schemas as typed code blocks rather than
  tables, a rubric's general preference must not quietly undo it. Change a locked
  convention only when told to. Conventions resolve as in
  `../../design-doc-write/references/shared-authoring-rules.md` "Project conventions".

## If a subagent does the edits

Give it the agreed plan in full in the prompt, and have it read only the target doc, not
a stack of background material; an editor that spends its budget re-reading context runs
out before it writes. It returns the edited doc; you run the checks above.
