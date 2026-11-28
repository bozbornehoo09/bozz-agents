<!--
DESIGN DOC TEMPLATE (HLD, LLD, mini-design)

A skeleton to copy, not a rulebook. Replace every <placeholder> and delete every
HTML comment from the real doc; comments here are instructions to the author.
When a comment and a rubric disagree, the rubric is right:

  opening paragraph, audience notes       audience-and-purpose.md
  decisions, history, wording, naming     tone-rubric.md
  ordering, routing, appendices           structure-rubric.md
  body and glossary size                  length-budget.md
  what "legible cold" means               zero-context-gate.md

Grains share this skeleton and differ in depth:
  HLD          the components, flows and shaping decisions. No schemas, keys or
               storage layout; those live in the LLD that owns them.
  LLD          one part of an HLD: contracts, schemas, state, failure modes.
               Its Background lists the parent HLD's steps in one line each.
  Mini-design  one small change. Keep the opening, Background in a few lines,
               one or two concept sections, Open items, the Appendices divider and
               the audience notes. Drop Glossary and Decisions when empty.

Target: someone holding only this file can say back what it proposes and finds
no project term they needed but could not resolve. A dependency that is named
and linked is a hand-off, not a gap.
-->

# <Title> — <High-Level Design | Low-Level Design | Mini-Design>

**Status:** <Draft | In review | Accepted | Stub — design pending>

<!-- Optional note, one line, only when the doc's shape would surprise a cold reader
     (for example, a deliberate stub). Delete otherwise. -->
> **Note:** <why this doc is shaped the way it is>

<!-- THE OPENING. Unlabelled prose, at most four sentences: what the people the
     design serves will be able to do, what this doc covers, and the ask when the
     readers must decide something. -->
<Opening paragraph.>

**Not covered here:** <concern> ([<owning doc>](<link>)); <concern> ([<owning doc>](<link>)).

## Glossary
<!-- Only terms that pass all three tests: a declared reader would not know it; the
     body does not explain it where it first appears; misreading it would change
     what that reader decides or builds. Everything else is an inline gloss or
     nothing. Stays above the Appendices divider. -->

- **<Term>** — <one sentence>.
- **<ABBR>** (<expansion>) — <one sentence>.

## Background
<!-- HLD: how things work today and what is wrong, then stop.
     LLD: the parent HLD's flow as numbered one-line steps; say which steps this
     doc owns and link the doc that owns the others. -->

1. <step>
2. <step>

This doc covers step <n>; step <m> is in [<sibling doc>](<link>).

## 1. Overview
<!-- What changes for the people the design serves. Then a short numbered
     walkthrough of one real case. Then the few facts that shape the design,
     each pointing at the section that owns it. -->

## 2. <Concept, named as a claim>
<!-- Open with who this serves and what the thing is, then how it works. One
     concept per section; same-shaped facts go in a table. -->

| <Item> | <Attribute> | <Attribute> |
|---|---|---|
| <row> | <value> | <value> |

<!-- A callout is for the one rule a cold reader would otherwise get wrong. Long
     proofs go to an appendix behind a pointer. -->
> **<The non-obvious rule.>** <Why it holds.>

## 3. <Next concept>
<!-- Routing (shared-authoring-rules.md, "Route each fact"):
     needed to follow the solution, a flow, a contract, a failure, an open gate -> body
     needed only to build or audit it -> appendix, with a one-line pointer here
     history, or how this doc was produced -> nowhere -->

## <N>. Decisions
<!-- Settled calls only. A major call keeps one line where the reader meets it
     ("chose X over Y because Z") and its comparison goes to the decision register
     appendix, unless the fork is still live. No dates of resolution, no names.
     Omit the section when every call is inherited from a parent doc. -->

- <Choice> over <alternative>, because <reason>. Comparison: Appendix A.

## <N>. Open items
<!-- Every undecided question, written as undecided. A lean is allowed if marked
     "recommended". No owner column: who decides lives in the project's tracker. -->

| Item | State |
|---|---|
| <question> | Open. <options, if it is a choice>; recommended: <lean, if any> |
| <thing to confirm> | Open. <what would settle it; what it blocks> |

<!-- THE DIVIDER. Body ends here: the length budget counts down to this heading,
     and readers may stop here. Do not rename or remove it. -->
## Appendices

## Appendix A — <the one thing it holds, e.g. "Decision register">
<!-- One concern per appendix, reached from a pointer in the body, organised like
     the body. Never a superseded design. -->

| Option | For | Against | Outcome |
|---|---|---|---|
| <chosen> | <...> | <...> | Chosen: <reason> |
| <alternative> | <...> | <...> | Rejected: <reason> |

<!-- Schemas and interface definitions belong here as typed code blocks; the body
     carries a short field table and a pointer. -->

## Appendix — Audience notes
<!-- Always last. Written before the outline. Never guess a reader or an ask: ask the
     user, or write "unknown — <what would settle it>". -->

| Field | Answer |
|---|---|
| **Readers** | <roles, main reader first> |
| **Prior knowledge** | <HIGH / MEDIUM / LOW on the problem and on the people served; the gaps that matter> |
| **Takeaway** | <the single sentence a reader should leave with> |
| **Stakes** | <what gets easier for them, or what goes wrong without this> |
| **Ask** | <approve / choose between options / comment / no action — and by when> |
| **Expected questions** | <three to five, each with where the doc answers it> |
