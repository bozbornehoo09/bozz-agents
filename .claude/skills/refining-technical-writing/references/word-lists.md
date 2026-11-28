# Word lists

## Contents

- [How this file is read](#how-this-file-is-read)
- Lists: [filler](#filler), [vague-quantities](#vague-quantities)
- Tables: [phrase-for-word](#phrase-for-word), [redundant-modifiers](#redundant-modifiers),
  [coordinated-synonyms](#coordinated-synonyms), [hidden-verbs](#hidden-verbs),
  [complex-words](#complex-words)

These inventories back the rules in `general-rules.md` "Words". `../scripts/check_prose.py` turns
every section into a generated Vale rule, so a match is only a candidate: the matching rule in
`general-rules.md` decides, sentence by sentence, whether it is a finding. This file is the only
copy of the lists; duplicating them elsewhere invites drift.

## How this file is read

- A section is a level-two heading holding just its slug. Every slug the checker expects must be
  present. If one is missing or renamed, the checker skips all word lists and reports
  "not loaded" with the reason instead of quietly checking less.
- Directly under the heading sits `<!-- kind: list -->` or `<!-- kind: table -->`.
- In a list section, each bullet opens with the term in backticks; text after it is a comment.
- A table section has exactly two columns, `| Wordy | Plain |`. The header row and the separator
  row are ignored.
- Matching ignores case, respects word boundaries and skips code spans and fences.

## filler
<!-- kind: list -->
Delete the word and the sentence still says the same thing.

- `actually`
- `basically`
- `essentially`
- `really`
- `simply`
- `just` — it stays when it means "only" or "very recently"
- `sort of`
- `kind of`
- `in terms of`
- `at this point in time`
- `at the end of the day`
- `as a matter of fact`
- `for all intents and purposes`
- `needless to say`
- `in my opinion`

## phrase-for-word
<!-- kind: table -->
A multi-word phrase that one or two words cover.

| Wordy | Plain |
|---|---|
| in order to | to |
| due to the fact that | because |
| owing to the fact that | because |
| despite the fact that | although |
| in the event that | if |
| prior to | before |
| until such time as | until |
| at the present time | now |
| with regard to | about |
| for the purpose of | for |
| is able to | can |
| has the ability to | can |
| a large number of | many |
| in close proximity to | near |
| under no circumstances | never |

## redundant-modifiers
<!-- kind: table -->
The modifier repeats something the noun or verb already means.

| Wordy | Plain |
|---|---|
| end result | result |
| final outcome | outcome |
| past history | history |
| future plans | plans |
| advance warning | warning |
| unexpected surprise | surprise |
| basic fundamentals | fundamentals |
| close proximity | proximity |
| general consensus | consensus |
| new innovation | innovation |
| absolutely essential | essential |
| completely eliminate | eliminate |
| join together | join |
| repeat again | repeat |

## coordinated-synonyms
<!-- kind: table -->
A pair of words that name one idea; one of them is enough.

| Wordy | Plain |
|---|---|
| each and every | each / every |
| any and all | any / all |
| first and foremost | first |
| full and complete | full / complete |
| null and void | void |
| various and sundry | various |

## hidden-verbs
<!-- kind: table -->
The action lives in a noun and a weak verb (*make*, *perform*, *give*, *have*, *take*) carries
it. Nouns ending in `-tion`, `-ment` or `-ance` are the usual sign.

| Wordy | Plain |
|---|---|
| make a decision | decide |
| makes a decision | decides |
| make an adjustment | adjust |
| make use of | use |
| makes use of | uses |
| perform an analysis | analyze |
| performs an analysis | analyzes |
| perform a migration | migrate |
| carry out a review | review |
| conduct an investigation | investigate |
| give consideration to | consider |
| take into consideration | consider |
| provide support for | support |
| provides support for | supports |
| reach an agreement | agree |
| come to the conclusion | conclude |
| have a discussion | discuss |

## complex-words
<!-- kind: table -->
A long word where a short one does the job. A term of art that the text defines, or that its
readers use every day, is not a finding (`general-rules.md` "Short words").

| Wordy | Plain |
|---|---|
| utilize | use |
| utilizes | uses |
| utilizing | using |
| utilization | use |
| leverage | use |
| facilitate | help |
| commence | start |
| terminate | end |
| endeavor | try |
| ascertain | find out |
| subsequently | later |
| approximately | about |
| demonstrate | show |
| methodology | method |
| functionality | feature |

## vague-quantities
<!-- kind: list -->
Words that suggest a measurement without giving one. Replace them with the figure, or with the
before-and-after values. A match is a finding only when its sentence stays vague: in "p95 dropped
from 400 ms to 300 ms, lower than the budget", `lower` is exact. Hedging modals (`might`,
`could`, `should`) are not listed here; `general-rules.md` "Plain statements" covers them.

- `significant`
- `significantly`
- `substantially`
- `dramatically`
- `greatly`
- `vastly`
- `much better`
- `much faster`
- `better`
- `faster`
- `slower`
- `higher`
- `lower`
- `most`
- `many`
- `some`
- `few`
- `nearly all`
- `almost`
- `often`
- `usually`
- `soon`
- `arguably`
- `clearly`
- `obviously`
