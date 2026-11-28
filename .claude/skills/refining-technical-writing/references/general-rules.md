# General writing rules

<!-- detail -->
## Contents

[Applying these rules](#applying-these-rules) · [Whole-document checks](#whole-document-checks) · [Claims](#claims) · [Numbers and evidence](#numbers-and-evidence) · [Sentences](#sentences) · [Words](#words) · [Spelling and grammar](#spelling-and-grammar)

Scope: every technical text someone reads, from a commit subject to a design doc to the prose
inside a code comment. Each rule is defined in this file and nowhere else. A kind of text can add
or override rules (`kinds.md`); "No names" is the exception that no kind except `skill` overrides.

Maintainer note: `../scripts/check_prose.py --kind` strips every block fenced by
`<!-- detail -->` and `<!-- /detail -->` before a review reads this file. Put only examples,
rationale and notes like this one inside such a block. A rule, a FIX or SUGGEST trigger, an
exception or a carve-out placed inside one would silently vanish from the review.
<!-- /detail -->

## Applying these rules

- Work top-down. Finish the whole-document checks before looking at single words: moving or
  cutting a paragraph rewrites its sentences, so earlier word polish is thrown away.
- A rule here is a prompt for judgment, not a banned-word list. A listed word becomes a finding
  only when its sentence reads worse because of it.
<!-- detail -->
- Every sentence can pass on its own while the text still fails: the ask sits at the bottom, a
  point is made twice, or a two-line answer has grown to a page.
- Findings obey the anti-hallucination contract in SKILL.md. Upstream credits are in
  [../THIRD-PARTY-NOTICES.md](../THIRD-PARTY-NOTICES.md).
<!-- /detail -->

## Whole-document checks

### Lead with the point

Put the conclusion, the ask or the decision in the first sentence the reader meets, and let the
supporting material come after it.

**Keep groups uniform.** A heading or lead sentence summarizes everything beneath it, and the items
under it are one sort of thing: only causes, only steps, or only risks. **FIX** a group that mixes
sorts.
<!-- detail -->
Under "Background" the draft lists a cause, a deploy step and an open risk. Either split them into
three groups or retitle the group with what the three have in common.
<!-- /detail -->

**Order with a reason.** Sequence a group by time (steps in the order they happen), by
composition (every part of a whole, none missing) or by weight (the most important first).
**FIX** an arbitrary order, and **FIX** a parts-of-a-whole list that skips a major part.

**Scope.** This holds for the document, for each section and for each paragraph, which starts with
its topic sentence. **FIX** any of the three that walks through evidence and arrives at its point
last; quote the buried point and the opening it should displace.
<!-- detail -->
Buried: "We backfilled `invoice-exporter` in staging on Tuesday. Two partitions were bigger than
estimated. The copy ran for seven hours. Production should finish Friday." Point first: "The
production backfill finishes Friday, a day late, because two partitions were bigger than
estimated and the staging copy ran for seven hours."
<!-- /detail -->

### Shape for the reader

Organize around what the reader has to decide or do, not around what the writer happens to know.
A common symptom is a section that marches through definition, then advantages, then a taxonomy.
**FIX** a section built that way; reorder it along the reader's path.

Settle four things before judging a draft: who the reader is, what they must know or do when they
finish, what they know already, and which questions they will bring (and where each is answered).

### Cause before symptom

To explain a defect or a risk, give the mechanism first, then the harm, then the conditions under
which it occurs. **FIX** an explanation that starts from an anecdote and reaches the mechanism
later.
<!-- detail -->
Anecdote first: "During a busy deploy, a webhook sometimes fires twice." Mechanism first:
"`webhook-dispatcher` marks a delivery sent only after the HTTP call returns, so a restart between
the call and the mark replays it. Deploys cause most restarts, so duplicates cluster there."
<!-- /detail -->

### Say it once

Each point appears one time. When a point repeats, cut the copy that contributes least, and never
cut the only place a condition or number is stated.

- **Restatement test.** For every paragraph, list and caption, check whether it repeats something
  another part already states. If it does, **FIX** it: shrink it to a pointer at that part, or
  remove it.
- **Keep the specifics.** Trim generic restatement; keep verified detail. A shortened block still
  carries its actual threshold, component name or measured value. Shrinking it to a bare label is
  a **FIX** of its own.
- **Merge before deleting.** When the same content sits in two places, keep the copy in the part
  that owns it and carry over anything only the duplicate had before removing the duplicate. Do not
  collapse several small, focused units into one. **FIX** a de-duplication that dropped a unique
  detail or fused units.

### Keep only what the reader needs

- A sentence stays only if a reader needs it at this spot. Marginally useful still costs reading
  time, so cut it. Keep a number only if the text does something with it.
- If a reader elsewhere needs a statement, move it there; if no reader needs it, cut it. When
  unsure, cut.

### Length

The kind of text sets the length (`kinds.md`). Measure it with `wc -w` or `wc -c`; do not guess.
Excess length is a SUGGEST naming what to cut or move behind a link, never a rewrite.

### Edits at this level

In edit mode a paragraph or sentence may be moved earlier, and a duplicate may be cut. The
argument is never rewritten, no claim is added and no condition is lost. Report a move as
"moved: <quote> from line N to line M" and a cut by quoting what was removed and where the point
still appears. Anything larger is a finding for the author to act on, not an edit.

## Claims

Apply these in order; an earlier one outranks a later one.

1. **Meaning survives.** SKILL.md's contract items 3 to 5 define what an edit must keep, and every
   check below gives way to them.
2. **Unsupported claims.** Strip praise or importance the text does not back up. A technical
   property the text supports stays; a new one needs evidence, so ask for it.
3. **Framing that repeats.** Remove a setup or summary sentence only if what it says is kept
   elsewhere in scope. A summary that helps the reader decide stays.
4. **Unnamed sources and actors.** "Everyone knows" needs a citation when the argument rests on
   it. Name an actor only when the source does, and only as the system, the component or "we"
   that the source shows. A person shown as the doer is removed, not swapped for another name
   ("No names").
5. **Stock rhetoric.** Simplify a formula contrast or a rule-of-three that hides the concrete
   point. A real comparison or a real set of three stays.
6. **Structure.** Keep headings, lists and tables that reflect real structure, and do not
   reorganize the document during a narrow pass. Wordiness is a matter for "Words" and
   "Plain statements".

<!-- detail -->
| Draft | Smallest useful response |
|---|---|
| Notably, the worker gives up after five attempts. | The worker gives up after five attempts. |
| This elegant, frictionless flow reinvents our releases. | Ask which observable change is meant; supply no figure. |
| The median filter discards these spikes. | Keep "median filter": it is the method's name. |
| Writes replicate asynchronously, so a read may lag. | Keep "asynchronously" and "may". |
| A tenant must not be purged while it holds open invoices. | Keep the obligation, the negation and the condition. |
| The upload was refused because the signature had expired. | Passive suits it; do not make up the refusing component. |
<!-- /detail -->

When an edit would need facts the supplied text lacks, leave the passage alone and report what
evidence is missing.

## Numbers and evidence

Give the reasons for a recommendation right after it. Show the evidence that cuts against it as
well as the evidence for it, point out the weaknesses in the data before a reader has to, and mark
the places where the conclusion is a judgment call because no data exists. How a kind lays out
several figures is that kind's rule (`kinds.md`).

- **Interpret the figure.** Introduce a table or chart with a sentence that says what it shows,
  and state what follows from it without stretching.
- **Co-occurrence is not causation.** Claim a cause only when the evidence shows one.
- **Anchor every number.** A figure needs a baseline, a time window or a comparison to mean
  anything.
- **Give both forms of a change.** "p95 fell 25%, from 400 ms to 300 ms", not "25% faster".

**FIX** a figure with no baseline, and a relative change given without its absolute values.
**FIX** a causal claim the cited evidence does not support, quoting the claim and the evidence.
**SUGGEST** a sentence stating the takeaway for a table or chart that has none.

## Sentences

### Sentence length

- Target a median of about 8 to 15 words per sentence, and keep nearly every sentence below 30.
- **FIX** any sentence longer than 30 words by splitting it or turning it into a list.
- Where the text is long enough to show a trend, a median well over 15, or more than roughly one
  sentence in twenty above 30 words, is too dense. Flag the trend with the counted figures.
- A run of clauses joined by "and", "which" and "so that" is a long sentence wearing a disguise.

### Splitting a long sentence

Give each sentence one idea, two at most. Break at a joining word (*and*, *but*, *so*, *which*,
*that*, *i.e.*, *e.g.*) and give every resulting idea its own subject.
<!-- detail -->
"Since the broker may hand a message to a second consumer when the first one times out, which is
most likely under load, each handler has to be idempotent so that a duplicate does not ship an
order twice" becomes "The broker may hand a message to a second consumer when the first times out.
Each handler has to be idempotent, so a duplicate never ships an order twice."
<!-- /detail -->

### Plain statements

- One em-dash aside per sentence at most; never stack them.
- Never nest a parenthetical inside another.
- Drop hedges that express no real doubt ("it is generally worth bearing in mind that, as a rule,
  …"). A hedge that records genuine uncertainty stays.
- No bold for emphasis in running text. Bold may mark a term where it is defined; a line that
  only seems important because it is bold needs stronger wording instead.
- Drop warm-up phrases ("it should be noted that", "crucially", "to be clear") and narration of
  intent ("intentionally"). Delete them and state the fact.
- **No sentence about the text instead of its subject.** Look for the shape rather than a fixed
  phrase: a count of what comes next ("Three risks follow."), a label for a paragraph, a heading
  repeated as a sentence, an instruction to the reader ("Notice the pattern here."). Before
  cutting one, ask what the reader would lose; a pointer, a scope boundary or a data transition
  ("This table shows…") stays.
- **No specialist vocabulary where an everyday phrase says the same.** Rephrase spec language
  ("normative", "by construction") and API slang ("opaque", "echo back") unless the precise term
  is needed and explained where it appears. Rephrase only when each word of the replacement refers
  to something the text actually shows.
- **Ordinal words say which order they mean** (first in time, in priority, or in the document?),
  and every pronoun or "the rest" has a single clear antecedent in its paragraph.
- **A definite reference identifies its thing.** "The list" or "the three modes" needs its members
  or a definition in view where it first appears.
- **FIX** each of these.

## Words

<!-- detail -->
`word-lists.md` holds the term inventories behind this section (everything except "No names").
Do not copy them anywhere else.
<!-- /detail -->

### Fewer words

Each match is a word-level **FIX** whose rewrite is the substitution.

- **Drop filler**: words that carry no meaning ("basically", "actually").
- **Swap a phrase for a word**: "in order to" → to; "due to the fact that" → because.
- **Remove doubling**: a modifier the noun already implies ("end result" → result), or a pair of
  words for one idea ("each and every" → each).
- **Free the verb**: an action turned into a noun and carried by a weak verb ("make a decision" →
  decide; "perform an analysis" → analyze).

### Concrete words

Be suspicious of nouns that fit any sentence: solution, item, resource, impact, outcome, users,
process, operation, improvement, capability. Put the actual thing in their place.

- **Say what a container holds** ("the three retry policies", not "the configuration") and keep
  the one property that makes it relevant. Short is not the same as fewest words. **FIX** a vague
  container noun.
- **Name who benefits.** "This lets teams move faster": which teams, faster at what? **FIX** a
  benefit with no one receiving it. The beneficiary is never the person doing a step
  ("No names").
- **Date commitments.** State a date at the precision you can keep: a day when it is near, a month
  or quarter when it is far. When a date moves, say that it moved and give the new one. **FIX** a
  commitment without a date.
- **Measure change**: replace "improved" or "much quicker" with the figure and its baseline.
- **Describe the decision, then cite it.** Refer to a decision by what it decided, in words the
  reader can follow, with any ADR or issue id after it in parentheses: "the one-writer-per-queue
  rule (ADR-4)", not "per ADR-4". The sentence must make sense with the id removed. A table column
  that exists only to hold references may contain bare ids. **FIX** each bare id carrying a
  sentence's meaning.
- **Replace vague quantities** (`word-lists.md` "vague-quantities") with the number, or with the
  change from one value to another. **FIX** each.

**A listed word is a finding only when its sentence stays vague.** Skip a match whose sentence
already gives the figure, the before-and-after values or an explicit comparison, and skip a match
inside a quotation, a cited source or a proper name.

### Active voice

Passive voice is correct when the object is what matters, when the actor is unknown or beside the
point, or when naming the actor would pull attention from the fix.

- **Passive must not conceal something the reader needs.** "An error was introduced" and "it was
  agreed" are each a **FIX**: name the actor when the source shows a system, a component or "we",
  and never a person ("No names").
- **Keep one voice within a sentence.**

Ask whether the reader needs to know who acts. If yes, use active voice.
<!-- detail -->
"The cache was flushed by the job after a timeout was reported by the probe" → "The job flushed
the cache after the probe reported a timeout."
<!-- /detail -->

### No names

Technical writing describes systems and steps rather than people. A name goes out of date
quickly, misleads after the person changes roles, and reads as blame or praise the text never
meant to assign.

- **No person, handle or alias as the one who acts, decides, finds or approves**, and no team or
  role as the one who acts ("the on-call will roll back"). A team may be named as the owner of a
  system it owns.
- **Describe the step, not its performer.** A test, rollout step or follow-up says what happens,
  in the imperative or with a system as subject, plus what it requires (production access, a
  signed build), never who holds that requirement. "Roll back the canary if p99 passes 300 ms",
  not "the on-call will roll back". **FIX** each named doer.
- **Point at the record, not a person**: cite the issue, the pull request or the dated decision,
  not "per <name>", `TODO(<name>)`, `@author` or "waived by <name>". **FIX** each.
- **Names that stay:** an ownership or contacts section the project requires; the addressee of a
  message (a chat @mention, an email's To line); a tracker's assignee field, which routes work and
  is not prose; a system or package referred to by its own name.
- This rule overrides "Active voice", "Name who benefits" and every kind's rule except the `skill`
  kind's (`kinds.md`). In edit mode, remove the named doer, keep the step and its requirement,
  substitute no other actor, and report the removal.
- Automated checks catch only some forms (`Plain.NamedActor`, and `extract_comments.py` for
  `TODO(<name>)` and `@author`). Neither can tell a person's name from a system's, so read for
  names as well.

### Short words

Prefer the short word when it works as well as the long one (`word-lists.md` "complex-words").
**FIX** each match unless the long word is a term of art the text defines or its readers use every
day.

## Spelling and grammar

Spell checkers pass a correctly spelled wrong word. Proofread the whole text, out loud if
possible, for spelling, grammar, capitalization and punctuation. **FIX** each error.
