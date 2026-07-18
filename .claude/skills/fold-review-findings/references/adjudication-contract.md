# Adjudication contract

## Independence

The implementer cannot self-certify a disputed finding. Use a fresh reviewer
context with no implementation conversation and no proposed fold. Pass only:

- the original finding and stable ID;
- the exact reviewed base/head or document identity;
- the complete relevant diff;
- cited authoritative sources and commands needed to reproduce it.

Ask whether the finding is proven, disproven, or unresolved. Do not ask the
verifier to implement. Prohibit recursive delegation.

## Evidence thresholds

- **CONFIRMED:** the cited bytes match and the claimed consequence follows, or
  a focused reproduction demonstrates it.
- **REJECTED:** exact counter-evidence or reproduction disproves the claim.
  Mere disagreement, passing unrelated tests, or author intent is insufficient.
- **DEFERRED:** the finding is valid, the gate policy permits deferral, and the
  report names a durable destination, owner, and return trigger.
- **UNRESOLVED:** evidence conflicts or cannot be obtained safely. Return
  `BLOCKED`; do not force a disposition.

For a `BLOCK`, require both the fresh verifier and the parent to re-read the
cited evidence before confirming or rejecting it.

## Folding

- Apply only confirmed findings.
- Route authoritative-layer changes through that layer's declared owning
  `update-*` skill; the fold coordinates and verifies but does not become a
  second writer.
- Keep the original finding ID through commits, tests, and bridge response.
- Use the smallest coherent change that resolves the proven defect.
- Re-run the original reproduction plus proportionate regression checks.
- Compare the resulting diff to every disposition before returning.
- Do not smuggle adjacent improvements into the fold.
