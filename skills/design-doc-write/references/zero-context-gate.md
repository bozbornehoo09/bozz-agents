# Specialist Brief: Zero-Context Gate

Contents: [Authoritative corpus (in scope)](#authoritative-corpus-in-scope) · [Out of scope corpus (invisible)](#out-of-scope-corpus-invisible) · [The bar](#the-bar) · [Check for: the procedure](#check-for-in-order-of-importance-the-procedure) · [Anti-hallucination contract](#anti-hallucination-contract) · [What the gate does NOT check](#what-the-gate-does-not-check) · [Output format](#output-format)

The **cold-read** lens of `design-doc-review`, and the acceptance test every human-review
design doc must pass. The pen-holders reach it through `design-doc-review`. A template
can describe "readable without context", but only a running skill can put a reader with
no context in front of the doc and see what happens; this brief is how.

This brief is carried out by the **dispatcher** (the review orchestrator, or a pen-holder
running the review flattened), which sets up and launches the readers itself. Readers
are instruments: they report what they could not follow, and the dispatcher judges.

## Authoritative corpus (in scope)

- The doc under review, by absolute path.
- The project audience file, if one resolves (`audience-model.md`).

## Out of scope corpus (invisible)

Everything else, and for the readers literally everything else. A reader that opens a
sibling doc has learned from it what this doc should have taught, so its reading is void.

## The bar

With **nothing but this doc** and **no other knowledge of the project**, a reader can:

- **(a)** explain what the doc proposes, correctly, in their own words; and
- **(b)** name **no** in-scope concept they needed and could not resolve, counting only
  concepts that are **load-bearing** for the reader who raised them.

Load-bearing: misunderstanding the term would change what that reader decides or builds.
This qualifier is what makes the bar reachable. Without it a diligent reader of a long
doc always finds another unfamiliar word, each one becomes a glossary entry, and the
glossary swells until it outweighs the body. The glossary test in the template is the
same rule from the author's side.

### What is in scope

- **In scope**: anything the doc introduces, depends on, or is about. It needs an
  explanation in the doc.
- **Out of scope**: a concept the doc hands to another doc or system **by name and with a
  link**. A name with no link is not a hand-off.
- **General engineering vocabulary** (as `audience-model.md` defines it) is never a gap for
  an engineering persona. Project- and organization-specific names are in scope.
- **A code identifier** that the doc names and links to its owning section or source file
  is a hand-off. One with no link and no owning section is in scope.
- **"The doc doesn't decide X"** is a design question, not a readability gap. It is
  reported separately (step 4) and never counts toward FAIL.
- **The Glossary is part of the body**, above the divider. A term explained only after the
  divider is explained where body readers have stopped (step 4, `appendix-only`).

## Check for (in order of importance): the procedure

1. **Hash the doc, then hand readers its real path.**

   ```bash
   shasum -a 256 <doc>   # or sha256sum; once before the readers start
   # ... readers run ...
   shasum -a 256 <doc>   # again after the last reader returns; a mismatch is STALE
   ```

   Give each reader the absolute path and nothing else about the repository: no file
   listing, no link map, no summary. Paste the doc's text only when the reader cannot see
   the filesystem (`user-mediated-gate.md`).

2. **Set up and launch the panel.** One reader per audience named in the doc's
   **Readers** row, with **at least two readers** in total (a doc with one audience gets
   two readers). Persona for each, first match wins: a persona the caller supplies
   verbatim; the doc's **Readers** row; the project's default persona; the default reader
   in `audience-model.md`. Landing on either of the last two means the doc has no
   audience notes, which the `audience` check reports; it is not a quiet fallback.

   Launch readers through the host's subagent or delegation facility, all at once when
   the host can run them in parallel, otherwise one after another. What matters is a
   **clean context**: each reader sees its persona, the prompt below and the doc, and
   nothing from this project, this conversation or the other readers. Pick models per
   `audience-model.md` "Choosing reader models". No subagent facility at all: use
   `user-mediated-gate.md`.

   **Detect contamination instead of preventing it.** Few hosts can confine a subagent
   to one file, so every reader reports a tool log; a log listing any path other than the
   doc (and the audience file if you passed it) voids that reading (step 5).

   **Timeouts.** A reader that never returns is not a pass, and one stuck reader must not
   hold up the panel, but the timeout has to be longer than a healthy reader takes on
   this host. Use twice the slowest clean reader you have seen; with no history, 25
   minutes. After the timeout, launch a replacement, but still accept the original if it
   comes back clean. A reader hit by rate limiting is rerun with fewer readers in
   parallel; any other failure gets one retry on the same model. A reader that still
   fails leaves the panel INCOMPLETE.

   Fill in both placeholders before launching; a persona left as `{persona}` turns every
   reader into the same generic one.

   ```
   Persona: {persona}

   Read one file and nothing else:
   {absolute path}

   Treat yourself as new to this project: you know nothing about its systems, team or
   history beyond what the file says. Read the whole file. Do not open any other file
   or follow any link; links mark topics another document owns, and opening one spoils
   this exercise.

   Reply with three sections.
   1. SUMMARY. In 5 to 10 sentences of your own: what does the document propose, what
      does the thing do, and what are its main rules, flows, failure cases and open
      questions?
   2. GAPS. Each term, mechanism or reference the document relies on without
      explaining, that you needed in order to follow it. For each give the exact text
      in quotes and its line number. Leave out anything the document names and links as
      another document's topic. If something is explained only after the "Appendices"
      heading, include it and mark it "explained only in an appendix". If there are no
      gaps, write "None"; do not invent any.
   3. TOOL LOG. Every file path you opened, in order, one per line, including any you
      opened and then ignored, followed by the number of tool calls you made.
   ```

3. **Judge each summary.** Is it faithful to the doc? A confident summary that gets the
   design wrong is a finding in itself: the doc misleads cold readers. Name what was
   misread and the text that led there.

4. **Merge the gap lists, then filter per reader.** Every gap keeps the persona that
   raised it and is judged as that persona. Remove a gap only when:
   - the doc does explain it **above the divider** (check the doc);
   - it is named and linked as a hand-off;
   - it is general engineering vocabulary **for that persona**;
   - it is a known term **for that persona** in the project audience file;
   - it is **not load-bearing for that persona** (say which decision it does not affect,
     so an over-generous removal can be seen);
   - it is a linked code identifier;
   - it is a **design question** rather than a gap. List these under `Design questions
     (not gate findings)` with the persona that raised them.

   **Handle `appendix-only` after the filters.** Of the gaps left, terms explained only
   after the divider remain findings, grouped into **one** structural finding listing the
   terms, with one fix: move the explanations above the divider.

   The finding set is what remains: in-scope terms with no explanation, link or applicable
   known-term entry, plus the `appendix-only` group. List every known-term removal (term
   and persona) so an over-broad entry shows up. When readers disagree on a term and no
   filter applies, keep it: other cold readers will trip on it too.

   **If a term was removed as known, record it.** When it is project vocabulary rather than
   textbook, recommend a row in the project audience file. A glossary trim without that
   row is undone by the next panel.

5. **Gate result.** This feeds the review verdict; it is not the verdict.
   - **PASS**: every summary is faithful and no gaps survive for any reader.
   - **FAIL**: gaps survive (including `appendix-only`), or a summary is wrong. List each
     gap with quote, line, persona and a suggested one-line explanation. FAIL forces
     `REVISE`.
   - **INCOMPLETE**: some launched reader produced no usable output. Name the audiences
     left unread. A doc is not legible until every declared audience has read it, so
     INCOMPLETE forces `REVISE`, never `READY`.
   - **STALE**: the hashes differ. The round says nothing about the doc. Report both
     hashes, discard every reading, rerun. Never report STALE as FAIL.
   - **CONTAMINATED**: a reader's tool log names another path. Discard that whole reading
     and launch a replacement; the panel is INCOMPLETE until it returns.

## Anti-hallucination contract

The family contract, adjusted for readers. Two family rules do not apply: a reader cites
only the one doc, so there is no second side to quote; and owner overrides are applied by
the dispatcher in step 4, not anticipated by readers. The dispatcher silently drops any
gap that breaks these:

1. Each gap quotes the doc verbatim; paraphrase is invalid.
2. Each gap gives a line number in the doc.
3. Each gap quotes the passage where the reader met the term.
4. "None" is correct output for a doc that passes.
5. Named-and-linked dependencies are never gaps.
6. Readers finish the doc before reporting; a gap for a term explained later in the body
   is invalid.

## What the gate does NOT check

- Agreement with sibling docs or the project's ADRs: `docs-review`.
- Whether the design is sound: the human design review.
- Tone, grammar and style: the tone lens.
- Whether the code matches the doc: this family's `verify` lens, or `code-review`.

It answers one question: **can someone with no context follow this doc?**

## Output format

```
[cold-read] <file:line> [BLOCK]
Persona: <persona that raised it>
Gap: <unexplained term | wrong summary | appendix-only group>
Quote: > "<verbatim doc text>"
Suggested explanation: <one plain sentence>

Gate: <PASS | FAIL | INCOMPLETE | STALE | CONTAMINATED>  (readers: <n>, personas: <list>)
Known-term removals: <term — persona>, …
Design questions (not gate findings): <persona — question>, …
```

Empty report is a valid result. Do not invent findings to look thorough.
