---
name: refining-technical-writing
description: Review technical prose, or make minimal edits to it, to remove AI-style filler, overstated claims, unsourced attribution and stock rhetoric. Covers PR descriptions, commit messages, ADRs, READMEs, status updates, chat replies, emails, issue comments, reports and the comments a code change adds; for a human-review design doc (HLD, LLD, mini-design) use design-doc-review, design-doc-edit or design-doc-write instead. Judges the whole text against its kind and reader before its sentences and words; every finding is quoted with its location, and every edit keeps each fact, condition, number, term and code span intact. Use when asked to tighten, de-slop or review writing, or when another skill hands it a finished draft.
---

# Refining Technical Writing

The goal is technical writing that is specific and quick to read, with every claim it makes left
exactly as strong as before. Rules stack in layers:

- [references/general-rules.md](references/general-rules.md) applies to every text;
- [references/kinds.md](references/kinds.md) adds the rules for the text's kind;
- Humanizer's catalogue of AI-writing patterns, fetched at a pinned commit, applies as amended by
  [references/humanizer-overrides.md](references/humanizer-overrides.md);
- [references/code-comments.md](references/code-comments.md) adds rules C1 to C10 for comments.

Vale supplies mechanical candidates, some of them generated from
[references/word-lists.md](references/word-lists.md). `scripts/install.sh` installs the external
tools; their credits are in [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

## Scope

What the pass needs:

- **The text.** A local Markdown or plain-text file; prose pasted into the conversation (save it
  to a temporary file and cite lines as `provided-text:line`); or, in review mode only, the
  comments a code change adds, extracted with
  `python3 <skill-dir>/scripts/extract_comments.py <repo> <commit | base..head | --staged> [--out <extract.md>]`.
  The extract is the file step 1 checks; `references/code-comments.md` lists what else to read.
  If no path or passage was given, ask for one.
- **The mode.** Review is the default and never modifies the source. Edit applies when the user
  asks for changes; that request already authorizes the prose edits, so do not ask a second time.
- **The context.** The kind and reader of the text, the part of it in scope, the project's
  vocabulary and any project-level writing overrides.

Only authored narrative inside the supplied text is in scope. Code, commands, metric tables,
schema fields, fixed output contracts, quotations, linked documents and the rest of the project
are out of scope. The checker parses every input as Markdown and ignores code spans and fences, so
in a plain-text file, judge lines indented four spaces or written `<like this>` by reading them.

When another skill runs this pass over its own draft, that skill's scope and gates still govern
(this pass introduces no approval or publishing step). The caller settles any "evidence needed"
finding itself, using what it knows and can cite. Everything runs inside the caller's context as
one agent, except the independent replacement check described in `references/code-comments.md`
"Proposing replacements".

## Anti-hallucination contract

1. A finding quotes the source verbatim and gives its `file:line`. If the quote or the location
   cannot be confirmed, the finding is dropped.
2. A finding that says two passages repeat or contradict each other quotes and locates both. A
   finding that says something is missing quotes the text around the gap.
3. Facts, quantities, units, negations, requirement words (`must`/`should`/`may`), quantifiers,
   scope, conditions, exceptions, stated uncertainty, decision status, sequence and chronology all
   survive an edit. If a rewrite would alter any of them, keep the original wording and explain.
   Comment replacements follow `references/code-comments.md`, whose rules remove a copied figure
   (C10) or a restatement of the code (C8) on purpose.
4. A prose edit leaves code, commands, identifiers, file paths, URLs, schemas, citations and
   table values exactly as they were.
5. The actor and the technical referent stay clear. An actor is a system, a component or "we",
   never a person, handle, role or team acting (`references/general-rules.md` "No names"). Never
   invent a measurement, an example, a mechanism, an actor, a citation, a benefit or a decision
   just so a sentence sounds concrete.
6. A report with no findings is a valid outcome. Never fabricate findings, scores or
   detector probabilities.
7. Findings judge the quality of the writing. They are not evidence of who or what wrote it.

## Do not flag

- A technical term merely because a list contains it: `median filter`, `eventually consistent`
  and `exactly-once processing` can be precise.
- Adverbs, passive voice, punctuation, headings, lists or parallel structure merely because a
  linter matched them; judge what they do in the passage. The skill's own `Plain.*` rules are
  judged by what their messages say, including the exceptions those messages state.
- Caveats the meaning needs, contractual terms that must repeat, exact identifiers, quoted source
  material or a project's established vocabulary.
- Missing design decisions, unverified platform behavior, document length budgets or design
  flaws. Those belong to design and plan reviews such as `plan-review`.

## Steps

1. **Read the text and load the rules.** Read all of the supplied text and keep to the scope. In
   edit mode, first copy it to a temporary file (step 5 compares against this copy) and note its
   sha256. Mark the facts and qualifications that must survive. Get the kind and reader from the
   request and the text, asking only if neither says, then run:
   ```bash
   python3 <skill-dir>/scripts/check_prose.py /path/to/file.md --kind <slug>
   ```
   `<skill-dir>` is this skill's own folder, not the document's. Slugs are the first code span in
   each row of `references/kinds.md`: `pr`, `commit`, `design-doc`, `adr`, `readme`, `status`,
   `chat`, `email`, `issue`, `report`, `code-comment`, `skill`; join several with commas. An
   unknown slug exits 2 and prints the valid ones. Output starts with one sources line (the
   cached Humanizer commit, stale overrides, missing kind homes), then gives the location of the
   assembled rules file: everything this pass applies, minus examples. Read that file in full before step 3. Each of its headings
   carries the `file:line` of its examples, for when a rule's reach on a passage is unclear. A
   repeat run in the same session, with those rules still in context, may drop `--kind`.
2. **Gather candidates.** The same command finishes with Vale's findings as JSON. When
   `word_lists` reads "not loaded", report that and its reason. Exit 3 means Vale, the Deslop pack
   or Humanizer is absent: show the user the printed install command, carry on with whatever did
   load, and report "Vale not run" or "Humanizer not loaded". Report any other failure verbatim,
   and never describe the text as lint-clean.
3. **Whole document, then sentences.** Apply `general-rules.md` "Whole-document checks" and the
   kind's rules first. Then take each candidate in its passage: discard false positives, note
   exemptions worth recording, and judge the remainder against the general rules, the kind's
   rules and Humanizer's patterns. Read for problems no linter can see. Propose the smallest edit
   that preserves the meaning. Where being specific needs evidence, ask rather than invent.
4. **Return the review, or apply the requested edits.** Before returning anything, check every
   quote and `file:line` against the text read in step 1 and drop any that no longer match.
   Review mode returns findings and nothing else. Edit mode first confirms the file still has its
   step-1 hash; if it changed, re-read it and recompute the edits instead of overwriting it, and
   keep unrelated changes.
5. **Verify the edited prose once.** Run
   `python3 <skill-dir>/scripts/check_prose.py <edited file> --against <original copy>`. Its JSON
   names each protected item the edit has fewer of: numbers, code spans, ids, URLs, headings,
   table rows, and words that express a modal, a negation, a condition or a quantity. Decide each: an item that was merely restated may go; a
   qualifier, number or code span that carried meaning comes back. A number that vanished with a
   whole cut sentence comes back with that sentence unless the same fact is stated elsewhere; a
   length target never overrides contract item 3. The check cannot see dropped state words
   ("disabled", "paused"), so read the claims for those as well. Then compare claims, actors
   (contract item 5), decision status and sequence by reading, and rerun the checker on the edited
   file without `--kind`. Do one editing pass and one verification pass; a zero-warning score is
   not the goal.
6. **Report what ran.** Keep Vale, the whole-document pass, the quote recheck, the `--against`
   check and the in-context review distinct. A clean lint result shows neither that the meaning
   survived nor that the prose is good. Name unresolved concerns plainly.

## Pause-for-confirmation rules

- Review mode writes nothing to the source, so reporting needs no confirmation.
- Edit mode applies only the edits the user requested. Stop and ask before any edit that would
  alter a protected element (contract items 3 and 4); report it as a BLOCK rather than applying it.
- Stop before a restructure bigger than moving or cutting one sentence or paragraph
  (`references/general-rules.md` "Edits at this level"); offer it as a finding instead.
- Do not run `scripts/install.sh` without the user's approval, because it downloads software.
  Report the command and continue with whatever is installed.
- This pass never edits code comments; replacements go to the author of the change.

## Severity criteria

- **BLOCK**: an edit that would change protected meaning, observed rather than speculated, or a
  comment that would mislead a reader into removing needed code. Leave the passage as it is and
  report the hazard.
- **FIX**: filler, repetition, inaccuracy or ambiguity that can be shown, with a correction
  grounded in the text.
- **SUGGEST**: an optional improvement, or a question only the author can answer.

## Style

- Keep findings short: the quote, a one-sentence reason, the smallest edit.
- Write the report in the plain style these rules demand: no praise, no scores, no closing
  pleasantries.
- Sort findings by severity, then by their position in the text.

## Output format

```text
# Refining Technical Writing: <path>

Mode: review | edit
Kind and reader: <kind>; <reader>
Tooling:
- Vale: <version> | not run: <reason>
- Humanizer: <commit> | not loaded
- Word lists: loaded | not loaded: <reason>
- Stale overrides / missing kind homes: <none, or the list>
- Quote recheck: <N kept, M dropped>
- --against: <items lost, with kept or restored for each> | not run

## BLOCK
- <file:line>
  > <verbatim passage>
  Risk: <the meaning that would change>
  Action: <source kept; evidence that would resolve it>

## FIX
- <file:line> [<category>]
  > <verbatim passage>
  Reason: <the weakness, specifically>
  Compared with: <file:line> > <verbatim passage>   (repeats and conflicts only)
  Context: <file:line> > <verbatim passage>         (omissions only)
  Suggested edit: <smallest rewrite>

## SUGGEST
- <file:line> [<category>]
  > <verbatim passage>
  Reason: <the optional gain, or the context missing>
  Suggested edit: <smallest rewrite, or the evidence needed>

Dismissed lint: <notable candidates set aside, with the technical reason; omit if none>
Edit mode only:
- Changes: <diff>
- Source hash: <at read> / <at apply>: matched | changed, re-read and recomputed
- Verification: <what was checked; open concerns>

Verdict: READY | READY-WITH-FIXES | REVISE
```

The verdict: REVISE if any BLOCK; READY-WITH-FIXES if no BLOCK and at least one FIX; READY
otherwise. It covers this prose pass alone. In
edit mode it describes the returned text, so a FIX that was applied no longer counts. A BLOCK or
SUGGEST that compares passages or claims an omission carries the same `Compared with:` or
`Context:` line. Code-comment findings use the shape in `references/code-comments.md`
"Finding shape".

## What this skill is NOT

It is not a detector of AI authorship, not a document author and not an architecture reviewer. It
does not publish, push or commit anything, and it changes no file other than the text it was
given.
