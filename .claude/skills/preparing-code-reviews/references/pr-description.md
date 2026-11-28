# PR description standard

## Contents

- [Who it is for](#who-it-is-for)
- [Layout](#layout)
- [Section by section](#section-by-section)
- [Length and form](#length-and-form)
- [Checks](#checks)

This is the single standard for a pull-request description, used by this
skill and by any skill that writes or edits one. `SKILL.md` step 4 drafts it,
the step 6 review loop treats it as part of the change, and step 9 re-checks
it on the opened PR.

## Who it is for

A reviewer opening the PR cold, without the plan, the chat or the branch
history. After reading it they should know four things without asking: what
changed, why each change is there, why this is the simplest shape that works,
and what evidence shows it works.

## Layout

**With a repository PR template** (`.github/pull_request_template.md`, a file
under `.github/PULL_REQUEST_TEMPLATE/`, `docs/pull_request_template.md`, or
`pull_request_template.md` at the root): the template's sections stay, in the
template's order. Put each part below under the template section that already
asks for it — the purpose and links under its summary or context section, the
change list under its changes section, the evidence under its testing
section. Parts the template has no place for (usually *Why it looks this way*
and *Rollout*) go as their own sections after its last content section and
before any checklist.

**Without a template**, use this skeleton:

```
<title — one plain sentence; it doubles as the squashed commit's subject>

Series: <n>/<N> — <series name>            (only for one PR of several)

## What and why
## What changed
## Why it looks this way
## Rollout
## Evidence
```

## Section by section

### What and why

Open with the outcome someone outside the code notices — what a user, a
client or an operator can now do or see — and how far this PR gets toward
it. Write in the reviewer's words, not the plan's: no plan or step ids and no
local or private paths. Code identifiers (modules, classes, functions) are
fine.

Then the links. Every link has descriptive text (`[Retry policy for the export
client](https://…)`), never a bare URL or id, and points only at pages the
reviewers can open:

- `Design:` the design doc or issue the change carries out;
- `References:` each outside guide or spec the code was written against — a
  library's upgrade notes, an API reference, an RFC — and only ones you
  actually read.

Where a link does not apply, say why in place of it:
`Design: none — one-line config fix`.

### What changed

One bullet per change, in the form *what it does — what fails or is
impossible without it*. If no reason can be given, the change does not belong
in this PR.

### Why it looks this way

The case that this is the simplest change that does the job, in four labelled
lines:

- `Follows:` for each non-obvious choice, the existing code that makes the
  same choice, linked to file and lines **at a commit**
  (`https://github.com/<owner>/<repo>/blob/<sha>/<path>#L<a>-L<b>`), with any
  difference and the plan line that decided it. Build this line from the
  implementer's `PRECEDENTS.md`, whose format
  `../../implementing-a-plan/references/precedents.md` defines: each
  `matches` or `differs` row becomes a linked entry, each `no precedent` row
  keeps its reason. Re-open every cited precedent first; one that no longer
  shows the choice is dropped or marked `unverified`, and rows for choices the
  final diff no longer makes are dropped. With no record and no non-obvious
  choice: `Follows: nothing non-obvious to match`.
- `Builds on:` the codebase conventions the change copies (a module layout, a
  class or test style) and the existing pieces it reuses (libraries,
  services, tables, helpers) — plus anything deliberately not built.
- `Rejected:` each alternative dropped, with the reason in a few words; or
  `Rejected: none considered`.
- `Pre-flight review:` written by step 6 —
  `<n> review loop(s) (review, challenge, defense); final <the Verdict: line>`,
  then each declined BLOCK with its reason in a few words, and any FIX folded
  after the last loop, marked unreviewed. A fast-path change uses the form in
  `fast-path.md`. Until step 6 has run: `Pre-flight review: pending`.

Any claim here that you have not confirmed in the code carries `unverified`.

### Rollout

- `Depends on:` what must merge or deploy before this, linked; or `nothing`.
- `Followed by:` what comes after it; or `nothing`.
- `On merge:` what changes in production once this lands — or `no runtime
  effect`.
- `To undo:` how to revert it, and anything a plain revert does not undo
  (data written, a flag flipped, a migration).

For a PR in a series, also list every PR of the series in merge order, each
linked, this one marked `(this PR)` and any not yet opened marked
`(not opened)`; and put the `Series:` line at the top.

### Evidence

Three labelled parts, kept apart:

- `Seen running:` what was exercised in a real environment and how, with the
  evidence quoted — the command and its output, a URL as a link. No local
  paths. Only what the evidence shows; anything without evidence moves to the
  next part.
- `Not yet seen:` each check still to run, as
  `<check> — pending: <stage or environment>, needs <what running it needs>`,
  and each waived one as `<check> — waived: <date>, "<the user's words>"`
  (`../../plan-review/references/real-system-checks.md` section 5). Write
  `Not yet seen: none` when nothing is outstanding.
- `Automated:` the build, lint and unit-test summary lines from step 3, each
  with the command that produced it.

From `implementing-a-plan`, the `Observed:` line of each step commit supplies
`Seen running:` and `Not yet seen:` — carry every one over, since squashing
drops the commit bodies.

## Length and form

- Readable in a few minutes. To shorten, cut in this order: secondary
  `References:` links, series narrative, `Rejected:` detail (keep the label:
  `Rejected: omitted for length`). Never cut a change's reason, the
  `Follows:` line, or `Not yet seen:`.
- No emoji. Prefer plain text where the host renders Markdown unevenly.
- Updating an open PR brings its whole description up to this standard, not
  only the new parts.

## Checks

Run them on the draft file at step 4 and on the live PR body
(`gh pr view --json body`) at step 9. Report each miss by its name, quoting
the text (with its line) where the missing element belongs.

| name | passes when |
|---|---|
| design | a `Design:` link, or `Design: none — <reason>` |
| references | a `References:` link, or `References: none — <reason>` |
| reasons | every bullet under the changes section states what fails without it |
| shape | `Why it looks this way` (or the template section holding it) has `Follows:`, `Builds on:`, `Rejected:` and `Pre-flight review:`; the last carries a `Verdict:`, or reads `pending` before step 6, or has the fast-path form |
| layout | the template's sections are present in its order, and `Rollout` is present with its four labels |
| series | for one PR of a series: the `Series:` line, the `(this PR)` mark, and every PR the merge order needs, linked or marked `(not opened)` |
| evidence | `Seen running:`, `Not yet seen:` and `Automated:` all present, and `Seen running:` backed by quoted evidence |
| links | no bare URL or id outside link text; no plan or step id; no private path |
