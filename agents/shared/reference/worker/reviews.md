Read this before dispatching any subagent, before folding findings from a
review, and before starting a review loop.

# Subagents and reviews

## Subagents

- A subagent returns findings only: the full text goes to a file you name,
  and its reply stays within 200 words. Where it has no write tool (the
  read-only review roles) or its skill fixes the reply shape, keep that shape
  and save the reply to the pass's file yourself. Hand over file paths, not
  pasted file contents.
- Run independent jobs (review lenses, debaters, cold readers, verifiers) in
  parallel by default, through the host's subagent mechanism, using the
  installed review-family roles: `review-specialist`, `cold-reader` and
  `cold-reader-deep`, `artifact-verifier`.
- On rate-limit or overload errors, send the failed jobs again at half the
  parallel count, halving while the errors continue. At two in parallel, run
  them one at a time; a job that still fails then is a failure. Any other
  failure gets one retry on the same tier.
- Pick each subagent's tier by its job: `haiku` only for mechanical lookups,
  `sonnet` to read a single document, `opus` to reason and verify. The two
  cold readers keep fixed tiers, because the design-doc gate needs two
  different models on every panel.

## Folding findings

- Fold real defects only: an end state that is bad and reachable, something
  an implementer would get wrong, or two sources (two docs, or code and its
  plan) that contradict each other.
- Turn down matters of taste and anything the plan notes or a sibling doc
  already covers, and write the reason in the pass's review file.
- Check a reviewer's claim in the source before folding a change that rests
  on it. Cite `path:line`; mark what you did not see as unverified.
- Keep each pass's reports and review file in `passes/<date>-pass-<N>/` and
  commit them with the fold.

## When a review loop ends

Every pass of any loop (the simplicity review, a skill's own gate) reads the
whole artifact. A pass with real BLOCKs is folded and followed by another. On
the first pass with none, fold its real FIXes without another review and
present them as folded but unreviewed. Stop sooner, and present the work with
its open findings and your view on whether the approach should change, when a
pass turns up more real BLOCKs than its predecessor, or again finds one the
previous fold should have fixed, or when pass ten still has any; with the owner away, park those as
owner items and go on with what they do not block. Where a skill's own rule
stops the loop earlier, it wins. The pass's review file says why each finding
not folded was left.
