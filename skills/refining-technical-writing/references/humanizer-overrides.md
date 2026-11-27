# Humanizer: what applies, and the overrides

From Humanizer this pass takes its working method ("How to work") and its 26 numbered AI-writing
patterns, grouped A to F and followed by "When not to act". Everything in this skill outranks
Humanizer when the two disagree: SKILL.md's contract and its "Do not flag" list,
`general-rules.md`, the kind's rules from `kinds.md`, and the `--against` check.

Two Humanizer sections are not loaded. "What to return" is replaced by SKILL.md's output format.
"Voice" targets blogs and personal essays; the one idea kept from it is that a writing sample the
user provides sets the sentence length, vocabulary, punctuation, openings and transitions, ahead
of the patterns (dashes at the sample's own rate, §8). With no sample, technical prose stays
neutral and plain while still sounding like a person wrote it.

<!-- detail -->
`../scripts/install.sh` fetches Humanizer at a pinned commit into the cache this skill reads.
Every override below names its pattern by number and exact title, so that
`check_prose.py --sources` (and `--kind`) can flag an override whose pattern was renamed or
removed upstream. A pin bump that renumbers the patterns is then corrected here instead of
silently going unapplied.
<!-- /detail -->

- §5 Arguing with no one: in an ADR, a design doc or a pull request description, an option that
  was rejected, with the reason, is the record of alternatives considered. Keep it unless the text
  says it twice; the pattern's "fake alternative" example does not cover this case.
- §8 Dashes as the universal connector: a single dash aside per sentence is acceptable; stacked
  asides are flagged under `general-rules.md` "Plain statements".
- §22 Chatbot residue: when a message closes with questions for its reader or asks for a go or
  no-go, that closing block is content. Neither mode removes it; edit mode may move a question
  down into it but never moves one out of it.
- §25 Writing about the document instead of its subject: remove narration of history or method
  without putting an unsupported fact in its place. The pattern's first example does add one, so
  it does not apply.
- §26 Re-explaining what the reader knows: in an issue or review comment, put the decision first
  and keep its figures and evidence after it (move them, do not cut them), with no sign-off
  (§22). The pattern's example discards them and does not apply.
