# Kinds of text: which rules apply

<!-- detail -->
## Contents

[Choosing the kind](#choosing-the-kind) · [PR descriptions](#pr-descriptions) · [Commit messages](#commit-messages) · [Design docs](#design-docs) · [ADRs](#adrs) · [READMEs](#readmes) · [Status updates](#status-updates) · [Chat](#chat) · [Email](#email) · [Issue and review comments](#issue-and-review-comments) · [Reports](#reports) · [Text under another skill's rules](#text-under-another-skills-rules)
<!-- /detail -->

`general-rules.md` applies to everything. A text's kind layers more rules on top, listed in the
last column of the table below. When a kind's rule disagrees with a general rule, the kind's rule
applies; the one exception is `general-rules.md` "No names", which every kind except `skill` must
follow. Precedence, strongest first: what the user asked for, the project's own writing
overrides, the kind's rules, the general rules, and last Humanizer as adjusted by
`humanizer-overrides.md`.
<!-- detail -->
Example of precedence: "Date commitments" wants a calendar date, but a chat reply may say
"tomorrow", because the chat kind's rule wins.
<!-- /detail -->

## Choosing the kind

Read the kind and the reader off the request and the text; ask only when neither tells you. The
first code span in each Kind cell is the slug `check_prose.py --kind` accepts. A text that is two
kinds at once takes both slugs, comma-separated (`status,email` for a status report sent as an
email).

| Kind | What the reader needs up front | Length | Where its rules live |
|---|---|---|---|
| `pr` Pull or merge request description | Defined by the PR-description standard | Defined by the PR-description standard | "PR descriptions" below; `../../preparing-code-reviews/references/pr-description.md` |
| `commit` Commit message | The effect of the commit, in the subject | Subject near 50 characters and never past 72; body wrapped at 72 | "Commit messages" below |
| `design-doc` Design doc or RFC | The problem and the proposed answer, in paragraph one | Whatever budget the project sets; otherwise length is not flagged | "Design docs" below |
| `adr` Architecture decision record | The decision and what forced it | A single decision, typically less than a page | "ADRs" below |
| `readme` README or other landing doc | What the project is and how to begin | No longer than getting started needs; push reference material into linked docs | "READMEs" below |
| `status` Status update | Each item's state, then risks with their dates | A line per item | "Status updates" below |
| `chat` Chat message or reply | The answer or the ask, on line one | A handful of lines unless detail was requested | "Chat" below |
| `email` Email | What is asked and by when, in the subject and opening paragraph | Fits on one screen | "Email" below |
| `issue` Issue, ticket or review comment | The current state or the decision, then the evidence | Brief, with evidence as a list or a link | "Issue and review comments" below |
| `report` Report or wiki page | The conclusion, then headed support | As long as the support requires | "Reports" below |
| `code-comment` Code comment, read years later by an engineer who has none of the project's other documents | The purpose of the code, or the single constraint the code cannot express | `code-comments.md` C10 | `code-comments.md` |
| `skill` Text a calling skill produces under its own style rules | Whatever that skill specifies | Whatever that skill specifies | "Text under another skill's rules" below |

## PR descriptions

- The structure, order and required parts of a pull request description are defined once, in
  `../../preparing-code-reviews/references/pr-description.md`; this file does not repeat them.
  When that file is not installed, keep the structure the description already has and review the
  writing only.
- Review the prose of each part with the general rules. A part the standard requires but the
  draft leaves empty is a **FIX** that names the evidence the author has to add; an edit never
  fills it in.
- A repository's own PR template keeps its sections and order, including any that read "none".

## Commit messages

- Write the subject in the imperative ("Cap upload retries at five"), with no closing period,
  describing what the commit does rather than what its author did.
- After a blank line, the body explains why and covers anything the diff cannot show. It does not
  enumerate changed files.
- Trailers (`Fixes:`, `Co-authored-by:`, `Signed-off-by:`) are metadata, not prose: leave them
  untouched, and "No names" does not apply to them.

## Design docs

- A human-review design doc (HLD, LLD, mini-design) belongs to `design-doc-review` and
  `design-doc-edit`; if one reaches this pass anyway, its opening follows "The opening" in
  `../../design-doc-write/references/audience-and-purpose.md`, the single definition. Each
  alternative carries the reason it lost.
- Open questions are phrased as questions, each saying what evidence would settle it.
- Whether the design is sound is a separate review; this pass judges only the writing.

## ADRs

- One decision per record, with its status, context, decision and consequences each stated once.
- An accepted ADR is a historical record. Edit mode leaves its decision and consequences as they
  are and fixes only wording that makes them unclear; any rewording of a binding sentence is
  reported as a SUGGEST for the author rather than applied.

## READMEs

- The opening lines say what the project is and whom it serves. Installation and a first working
  example come before configuration and reference material.
- Every command shown must run when pasted. The surrounding prose is reviewed; the command itself
  is protected.

## Status updates

- One line per item, naming the concrete thing (the service, the migration, the release), its
  state and the date of its next change. A date that slipped says so and gives the new date.
- Risks and blockers come after the items, each with what would remove it.

## Chat

- Short and informal, in whatever first person the author would use. Line one answers or asks.
- Near-term dates may read "today" or "tomorrow", counted from when the message is sent; if the
  send date is unknown, keep the weekday and the date.
- Put several figures in a short list rather than a table, since many chat clients do not render
  Markdown tables.
- Omit formalities the reader will not act on: reviewer rosters, numbered asks, counts and dates
  they have no use for.

## Email

- Review the subject line together with the body, since it is what the reader sees first.
  Address lines (To, Cc) are not prose, so lint matches there are false positives.
- A request lays out the facts plainly (what is needed, by when, and what a delay affects) and
  asks once and courteously, without manufactured urgency or blame.
- Leave out housekeeping the reader did not ask for.

## Issue and review comments

- Open with the decision or the status. The figures and evidence behind it follow; they are moved
  below the point, never cut. No sign-off (`humanizer-overrides.md` §26).
- A request to another group follows "Email" above.

## Reports

- State the conclusion first, then the support under headings that each make their own point.
- Present several figures as a table with units in the column headers, and give each table or
  chart a sentence on what it shows (`general-rules.md` "Numbers and evidence").

## Text under another skill's rules

- When a calling skill runs this pass over text it produced, that skill's own style rules take
  priority, including its owner and contact fields. This pass adds the general rules only where
  the caller says nothing, and the caller keeps its own scope and gates.
