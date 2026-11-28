# Specialist Brief: Structure Rubric

Contents: [Authoritative corpus (in scope)](#authoritative-corpus-in-scope) · [Out of scope corpus (invisible)](#out-of-scope-corpus-invisible) · [Check for (in order of importance)](#check-for-in-order-of-importance) · [Anti-hallucination contract](#anti-hallucination-contract) · [Output format](#output-format)

The ordering half of `design-doc-review`'s **tone** lens: where things sit in the doc and
in what order. Findings are tagged `[tone]` and use `tone-rubric.md`'s severity, contract
and output format; this file adds only the contract rules its own checks need. Check ids
are `S1` to `S8`.

## Authoritative corpus (in scope)

The doc under review, read in full including its appendices, with
`design-doc-template.md` as the reference shape. For S1 and S3, the matching headings of
`../../refining-technical-writing/references/general-rules.md` ("Lead with the point",
"Say it once").

## Out of scope corpus (invisible)

Sibling docs and the artifact. Three checks have a half that needs another doc: whether
detail removed in a de-duplication survives in its owning section, whether LLD-level
detail found in an HLD already lives in the LLD, and whether a section repeats its parent
HLD (S2 d). The dispatcher sends those to `verify` as cross-doc structure claims; here,
judge only what the doc itself shows.

## Check for (in order of importance)

### S1. Answer first

Apply "Lead with the point" from `general-rules.md` at every level: the doc, each section, each
paragraph. Design-doc specifics:

- **FIX** a section that gets to its point in the middle or at the end.
- **FIX** a group of argument headings that are topics ("Background on retries",
  "Details") where the reader needs claims ("Retries are capped so a dead endpoint cannot
  crowd out healthy ones").
- **SUGGEST** regrouping a level that has more than about seven siblings.

The doc's opening paragraph belongs to `audience-and-purpose.md`; buried answers inside
sections belong here.

### S2. Start from the people the design serves

Every design exists for someone: an end user, an API caller, an operator on call. The
doc leads with what that person can now do or see, then what is built to make it so,
then how it works. For each section ask:

- (a) Does its first paragraph name the experience it serves before any mechanism? A
  mechanism section passes if its own lead or its parent section's lead does. A reference
  section (glossary, error table) passes if its parent does.
- (b) Does each mechanism (a limit, an ordering rule, a lock, a retry, a recovery path)
  connect to an experience it enables or protects?
- (c) Is internal machinery presented as the goal rather than the means?
- (d) Does it repeat the parent HLD instead of building on it?
- (e) Is something defined only by what it is not ("outside the pipeline")?

**BLOCK** a section with no discoverable purpose: neither its lead nor its parent's says
what experience it serves. Report that once as the BLOCK, without also raising (a) or (b)
for it. **FIX** a "no" to (a) or (b), or a "yes" to (c), (d) or (e). A rewrite must not
make up an experience: name the one the doc already states, or add an Open items row
asking what the mechanism is for and whether it can go.

### S3. Each fact in one place

Apply "Say it once" from `general-rules.md`. Design-doc specifics:

- **FIX** a block that repeats what another section owns. Keep the concrete version in the
  owner, replace the repeat with a pointer, and move any unique detail across before
  deleting.
- **FIX** a figure caption that explains the mechanism, argues a reason, or raises a
  question. A caption names what the figure shows and gives one pointer.
- **FIX** a body that argues, item by item, why each out-of-scope concern belongs
  elsewhere. The `**Not covered here:**` line says it once.

### S4. Solution first, defences after the divider

Under the experience it serves, the body presents the solution and how it works. A run of
"Decision: X" sections is the wrong shape; a body heading of that form is a warning sign.

The chosen behaviour always stays where the reader meets it. Whether its alternatives and
defence stay too depends on whether the choice is still open: for an undecided question
or a pending gate, keep the options inline; for a settled choice, keep one line ("chose X;
comparison in Appendix A") and move the comparison to the decision register after the
divider. The question to ask is "is this still open?", not "is this a decision?".

- **FIX** a "Decision: X" body heading, or a settled comparison table that sits in the
  reading path ahead of the solution.
- **FIX** a body that weighs alternatives before it has shown how the solution works.
- Do **not** ask for a decision register when every major choice comes from a parent doc;
  then the right shape is a context appendix and the divider.

### S5. Everything in the body is needed there

S3's sibling: content that is correct and not repeated, but not needed in the body.
Judge the whole reading path, not one block at a time.

- A body block stays only if a reader needs it to follow the solution, a flow, a
  contract, a failure mode, or an open gate. **FIX** build-level or audit-level detail in
  the body: move it after the divider with a one-line pointer. Move the specifics intact;
  do not reduce them to a bare label.
- "Somewhat useful" is a reason to cut. Prefer cutting to moving.
- **FIX** schemas, keys, indexes or storage layout in an HLD: they belong in the LLD that
  owns them, with a pointer.

### S6. Background describes the present and stops

An HLD's Background describes the current system and the problem. An LLD's lists the
parent HLD's flow as numbered one-line steps and names the steps this doc owns. **FIX** a
Background sentence that argues for a phasing plan, sizes a rollout, or uses a term the
doc has not introduced: move it to the section that owns it, or cut it.

### S7. Requirements describe observable behaviour

A requirement says what happens: "when X, the service does Y". **FIX** a requirement that
is only a capability noun or a stored field; rewrite it as something a tester could
observe.

### S8. Appendices hold detail, not leftovers

- **FIX** an appendix that is a wall of prose or a dump of notes. Give it headings and
  tables like the body.
- **FIX** an appendix with no pointer from the body section it supports.
- **BLOCK** an appendix (or any section) holding a replaced design, a "why we changed it"
  account, or content the body contradicts. It sends reviewers the wrong way. (This is the
  appendix form of `tone-rubric.md` check B.)
- **SUGGEST** splitting an appendix that covers several unrelated concerns.

## Anti-hallucination contract

`tone-rubric.md`'s contract applies, plus:

1. **Repetition, contradiction, and re-argued scope quote both places**, each with
   `file:line`.
2. **Missing pointers, use before introduction, unconnected mechanisms and the S2 BLOCK
   are claims of absence.** Read the whole doc first, then quote the text around where the
   missing element should be.
3. **An S2 finding quotes the section's lead and its parent section's lead.**
4. **An S5 finding names the reader need the block fails**, and a move names the section
   whose reader does need it.

## Output format

`tone-rubric.md`'s block, with `Check:` set to this file's id, for example
`S2 experience-first`.

Empty report is a valid result. Do not invent findings to look thorough.
