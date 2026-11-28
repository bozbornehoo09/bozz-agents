# Out-of-band reviewer relay

Contents: [When not to use it](#when-not-to-use-it) · [Steps](#steps) · [Brief template](#brief-template-inputmd) · [Hand-over prompt](#hand-over-prompt)

Use this when the independent reviewer cannot run `review_bridge.py` — a
browser chat model, a model on another machine, a colleague's agent with no
access to this checkout. The lifecycle does not change: one review file, the
same states, the same archive, and a mandatory `fold-review-findings` pass.
Only the transport changes: the requester hands over a self-contained brief and
relays the reviewer's output into the transcript verbatim.

## When not to use it

If the reviewer can run the helper, use `cross-reviewer` directly. Relaying is
strictly weaker evidence (the requester carries the reviewer's words), so it
is a fallback, not a convenience.

## Steps

1. **Pin and open.** Pin the artifact (commit, or
   `review_bridge.py fingerprint` for uncommitted files) and run `init` with
   `--reviewer external:<short reviewer description>`. The request body is the
   brief below.
2. **Write the brief** to `.agent-bridge/handoff/<REVIEW_ID>/INPUT.md` from the
   template below. Every placeholder is replaced; the brief must stand alone —
   the external reviewer reads only it and the files it lists. The lenses come
   from the review skill the request pins: paste each of its specialist
   briefs' "Check for" list (or the whole brief) under `## Lenses`, with the
   lens name, so the external reviewer applies that skill's checks rather than
   a generic focus list.
3. **Hand over.** Print the prompt below with absolute INPUT and OUTPUT paths
   (OUTPUT defaults to `.agent-bridge/handoff/<REVIEW_ID>/OUTPUT.md`). For a
   reviewer without file access, the user pastes the brief and the listed
   files inline and saves the reply to the OUTPUT path.
4. **Relay the claim.** When the user confirms the handoff, append
   `REVIEW_STARTED` as `--actor REVIEWER` with the user's ETA and grace and the
   first body line `RELAYED: out-of-band reviewer; requester relays, does not
   author`.
5. **Relay the review.** When OUTPUT exists, verify the pinned identity still
   matches (otherwise relay a `BASELINE: STALE` review per the protocol), then
   append `REVIEW` with the same first body line, the OUTPUT file's SHA-256, and
   the OUTPUT text **verbatim, every line prefixed with `> `** (this also keeps
   protocol-shaped lines from being read as metadata). Assign stable finding
   IDs in a short index after the quote, without rewording any finding.
6. **Fold.** Continue the requester workflow: `FOLD_STARTED`, then
   `$fold-review-findings`. The relay never accepts, rejects, or drops a
   finding — including ones that look wrong or duplicate a known-open item;
   that is the fold's decision, with evidence.
7. **Next round.** A re-request writes a new INPUT brief (same folder,
   `INPUT-r<round>.md`) naming what changed and the rejected BLOCK/FIX findings
   to re-adjudicate.

Never edit INPUT or OUTPUT after relaying them. The transcript carries the
OUTPUT verbatim with its SHA-256, so the archived transcript stays
self-sufficient; the helper does not move the handoff folder, so keep or prune
it under the project's own evidence policy.

## Brief template (`INPUT.md`)

```markdown
# Review brief — <subject>

## Task
Review the files below as the `<pinned review skill>` review would, using the
lenses listed under `## Lenses`. <One sentence on what the corpus is.>

Files (read exactly these):
- `<absolute path>` — <what it is> (PRIMARY | SUPPORTING)

Pinned identity: <commit/range or files-sha256:…>

## Context to hold
- <What the project is, in one to three sentences.>
- What changed in this round (pressure-test these first): <specific edits>.
- <Domain facts the reviewer cannot infer from the files.>

## Evidence rules
- Every finding cites file + line and quotes the text verbatim.
- A contradiction quotes both sides, each with its own file:line.
- A gap quotes the surrounding text where the missing piece belongs.
- Label each finding OBSERVED (the text shows it) or HYPOTHESIS (cannot be
  fully verified from these files — say what is missing).
- Do not assert that a live system behaves differently from the docs; at most
  note "unverifiable from the files" when it is load-bearing and suspicious.
- No findings is a valid result. Do not pad.

## Lenses (from `<pinned review skill>`)
### <lens name> (`<skill>/references/<brief>.md`)
<that brief's "Check for" list, pasted verbatim, with its severities>
<one subsection per specialist brief the skill runs>

Within each lens, pressure-test what changed in this round first. Tag each
finding with its lens name.

## Do not flag (already tracked)
- Style, wording, or formatting with no functional effect.
- <Known-open items, deliberate in-flight inconsistencies, settled decisions.>

## Output
Write to `<absolute OUTPUT path>`, most severe first. Per finding:
`[lens] · [BLOCK|FIX|SUGGEST] · [OBSERVED|HYPOTHESIS] · file:line · "quote" · problem
(one sentence) · fix (one line)`. End with `NON-FINDINGS` (at most five
bullets: what you checked and cleared) and one verdict line: REVISE if any
BLOCK; READY-WITH-FIXES if no BLOCK and at least one FIX; READY otherwise.
Do not edit any reviewed file.
```

## Hand-over prompt

```text
Read the review brief at <INPUT path> and follow it exactly. It lists the
files to review, the context to hold, the evidence rules, the lenses to
apply, and what not to flag. Review only those files. Cite file:line with a verbatim
quote for every finding; quote both sides of any contradiction; label each
finding OBSERVED or HYPOTHESIS; finding nothing is a valid result. Write your
output only to <OUTPUT path> in the format the brief specifies, and do not
modify any reviewed file.
```
