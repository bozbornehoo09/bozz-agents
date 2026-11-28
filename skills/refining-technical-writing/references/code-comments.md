# Code comments

<!-- detail -->
## Contents

[Who the comment is for](#who-the-comment-is-for) · [Rules C1 to C10](#rules-c1-to-c10) · [Inputs](#inputs) · [Checks per comment](#checks-per-comment) · [Severity](#severity) · [Proposing replacements](#proposing-replacements) · [Finding shape](#finding-shape)
<!-- /detail -->

This pass reviews the prose of code comments (`//`, `/* */`, `#`, Javadoc, JSDoc and similar doc
blocks), never the code next to them. Rules C1 to C10 are defined here only; any skill that writes
or reviews code links to this file instead of restating them.

## Who the comment is for

Picture an engineer opening this file years from now with no access to the project's design docs,
plans, reviews or tracker. A comment should tell them, in a glance, either what the code is for or
the one constraint the code cannot express (what decides a number, for example). How the code
works is the code's job. No comment may tempt that reader into removing or altering code that is
still needed.

## Rules C1 to C10

| # | Rule |
|---|---|
| C1 | **Self-contained.** The reason is written out in the comment. It is never a pointer to a design doc, plan, section, appendix, review, pull request, issue or ADR id, and never a person's name. Referring to a code path, or linking public documentation for a library or API the code calls, is fine when it helps. |
| C2 | **Numbers state their constraint.** Give the bound the value must clear or stay under, briefly. Not the incident that revealed it, and not the arithmetic behind it (C10). |
| C3 | **Every guard explained and tested.** Each throw or guard branch says, in its comment or clearly in its code, what it rejects and why, and some unit test exercises it. |
| C4 | **Intentional oddities say why.** A pin, a legacy client, a duplicated value or a known gap that looks like a bug says why it is kept and what would allow removing it. |
| C5 | **One term per concept.** Name each thing for what it is or serves; when a term is renamed, recheck the concept at every use, not only the spelling. |
| C6 | **Define a relied-on term once, at its home**: what it checks, accepts or rejects. Follow the naming precedents the codebase already has. |
| C7 | **Matching another value is not a reason.** "Same limit as the API gateway" does not say why that limit is correct here. |
| C8 | **Accurate, and why rather than what.** Every comment is true of the code beside it and supplies a reason. A comment that only restates a name or the code is removed. |
| C9 | **Replace, don't stack.** Wording that supersedes an existing comment takes its place instead of sitting next to it. |
| C10 | **Orient at a glance.** State the purpose of the code, or the single constraint it cannot express; leave the mechanics to the code itself. Prefer a single line wherever it is enough. Do not copy a figure, list or derivation from another value or file, since it rots when the source changes; describe the constraint in words or refer to the constant by name. |

<!-- detail -->
| # | Fails | Passes |
|---|---|---|
| C1 | `// Batch size from the ingestion RFC, section 4.` | `// Larger batches exceed the broker's 1 MB message cap.` |
| C2 | `// 10 s timed out during the load test, so 20.` | `// Has to outlast the longest upstream retry window.` |
| C3 | `if (pageSize < 1) throw new IllegalArgumentException();` with no test | The same guard, a test passing 0, and `// A zero page size would loop forever.` |
| C4 | `urllib3==1.26.18` with no note | `# Pinned: 2.x drops the TLS setting our proxy needs; unpin once the proxy is replaced.` |
| C5 | "job" meaning both the cron entry and the worker process in neighboring comments | "cron entry" and "worker process" |
| C6 | "the filter" across five comments without saying what it lets through | One definition on the class: "passes an event only when its tenant is active" |
| C7 | `// Same 5 s timeout as the mobile app.` | `// The single caller abandons the request after 5 s, so a later reply is wasted.` |
| C8 | `// Gets the order id.` above `getOrderId()` | Remove it. |
| C9 | A newly added paragraph above an older one that contradicts it | A single, rewritten comment |
| C10 | `// 8 attempts × 30 s + 2 min jitter ≈ 6 min, rounded to 10.` | `// Longer than every retry of the export job.` |
<!-- /detail -->

## Inputs

1. **The added comments.** Run
   `python3 <skill-dir>/scripts/extract_comments.py <repo> <commit | base..head | --staged> [--out <extract.md>]`.
   It always prints each flagged line as `<path>:<line>: <kind>: <text>`. With `--out` it also writes
   each added comment block under a `## <path>:<start>-<end>` heading with the comment markers
   removed; then run `check_prose.py <extract.md> --kind code-comment` for the rules and
   Vale's candidates. Its exit status: 0 when no added line cites a document (C1) or names a
   person (`TODO(<name>)`, `@author`), 1 when at least one does (each is listed), 2 on a git or
   usage error. Treat the extract as an index only: quote every comment from the source file
   itself, markers included.
2. **The code as of the change** (`git show <commit>:<path>`, or the index for `--staged`). Read
   every added or modified file in full, plus whatever a comment makes claims about: the method it
   calls, the library at its pinned version, the test. A claim no code supports is labelled
   "unverified", never stated as fact. Also read comments the diff deletes, because a surviving
   line can lose its reason in a later revision.
3. **The house style**, from two or three files near the change: whether doc tags are used,
   one-line summaries, wrap width. Replacements match it.

## Checks per comment

| Check | Report a finding when |
|---|---|
| Accurate (C8) | The comment claims the code, or something it calls, behaves in a way it does not; describes something unbuilt as built; or uses wording that dates ("temporary", a milestone name) |
| Gives a reason (C8) | It restates the identifier or the code, or a doc comment repeats the signature |
| Orients (C10) | It explains the mechanics or derives a number, takes several lines where one would do (tag lines the local doc style requires are exempt), or copies a figure or list from elsewhere |
| Numbers (C2, C7) | A value comes with no constraint, with a constraint that would not actually fix it, or with a comparison, incident or calculation offered as its reason |
| Self-contained (C1) | The reason is a document, review or tracker id, or reasoning lifted from a plan cites its source |
| Terms (C5, C6) | One word is used for two things or two words for one thing, a term the comments depend on is never defined, or a renamed term was not rechecked everywhere it appears |
| Guards (C3) | A throw or guard branch leaves its rejected input or its reason unstated, or no unit test exercises it (name the test files that were searched) |
| Intentional oddities (C4) | Something deliberately unusual does not say why it stays or what would allow removing it |
| External facts | A claim about another library or system is accepted without checking; verify it against that library's source or docs at the pinned version, and keep only what this code relies on |
| Absent | Someone new to the code would be stuck without a comment: a magic value (test sizes included), a surprising branch or ordering, or a guard that looks like dead code. Check every added line, tests too. Never flag the obvious |
| Superseded (C9) | New wording sits alongside the old wording it replaces |
| Names (C1) | A person is named in any form (`general-rules.md` "No names") |
| Prose | Everything in `general-rules.md` applies, as for any text |

Across the whole change (`general-rules.md` "Say it once"): a fact several comments rely on is
stated at a single owning site, other comments refer to it by class or function name, and each
term keeps one meaning everywhere.

## Severity

A false or misleading comment is a FIX; it becomes a BLOCK when it would push a reader into
deleting or changing needed code. Findings from every other check are FIX. Pure wording issues use
SKILL.md's severity criteria.
<!-- detail -->
If every comment in the change passes every check, the report is empty, which is a valid result
(SKILL.md contract item 6).
<!-- /detail -->

## Proposing replacements

- **Ready to paste.** Match the file's comment markers, indentation, wrap width and doc style.
  Give comment lines only, and say under `Code:` where they belong (for a missing comment, the
  line it goes above).
- **Every claim is backed by code** at a `path:line`, listed under `Claims:`. A reason the code
  does not show is written as "reason unverified: <what would confirm it>", not as fact.
- **An independent check precedes use.** The pass marks each replacement `pending`. Whichever
  session hands the findings to a person or applies them first passes them to a reader that did
  not write them: a fresh subagent or delegated task when the host supports one, or else a
  separate re-read of every cited line, recorded as `self-check`. For each finding that reader
  confirms the quoted comment appears verbatim at its lines, confirms each fact the finding and
  the replacement rely on (citing `path:line`), and quotes any overreach: an invented motive, a
  library claim that its source contradicts, a design intention presented as code fact. Finding no
  overreach is a valid outcome. That reader does not judge style or rerun the tools. Its citations
  are re-read before anything is removed; whatever it contradicts is dropped or corrected, and new
  claims from a correction are added to `Claims:`.
- Review mode never edits comments; the author of the change applies the replacements.

## Finding shape

Code-comment findings fill SKILL.md's output format with these fields:

```text
- <path>:<start>-<end> [C<n>: <check>]
  > <the comment exactly as written, markers included>
  Reason: <the defect, as the code below shows it>
  Code: <path>:<line> > <the code it was checked against, verbatim>
  Compared with: <path>:<line> > <the other comment, verbatim> (conflicting meanings, repeats or superseded wording only)
  Suggested edit: <fenced replacement, or "delete">
  Claims: <one per line, each with its path:line>
  Second reader: pending | confirmed | self-check | corrected (<the change>) | unverified (<evidence that would settle it>)
```
