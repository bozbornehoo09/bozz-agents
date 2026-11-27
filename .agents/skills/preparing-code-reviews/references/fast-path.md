# Fast path

The full route — plan, `plan-review`, `implementing-a-plan`, then up to three
review loops — is too heavy for a small change whose content is already
settled. This file is the only definition of the lighter route; other skills
link here. Design docs and skills are not affected: they keep their own
gates (`../../design-doc-review/`, `../../skill-review/`).

## Who qualifies

All five tests must be a clear yes. Any doubt means no, and the change goes
the normal way.

| test | yes when |
|---|---|
| **settled** | The user, a recorded decision or a plan step already says what to change, and the change introduces nothing further of its own: no new limit, rate, name, key, schema, API shape, dependency or behavior. |
| **contained** | It stays within one package or module, adds no file other than tests, and changes roughly 50 non-test lines or fewer (a yardstick, not a hard limit). |
| **low-stakes** | It touches none of: permissions or access policy, network exposure, credentials or secrets, personal data, deletion or migration of data, infrastructure resources, a public API contract. |
| **tested** | Existing tests already cover the area, and every guard the change adds, alters or removes gets a unit test added or updated. |
| **revertible** | Reverting the commit fully undoes it. |

## How it runs

1. **Announce it** in one line of your reply — `Fast path: <the five tests,
   briefly>` — and load only what the change needs: the request, the
   project's contribution rules, the overrides register if there is one
   (`../../code-review/references/register.md` says where), and the code and
   tests involved.
2. **Make and commit the change.** Work on the user's branch or on
   `fast/<short-slug-of-the-request>`. Run the project's build, lint and
   tests, then commit by explicit path with their result lines in the body.
3. **Package it with a single review.** Follow `../SKILL.md` steps 1–5 as
   written, treating the user's request as the spec. The description meets
   `pr-description.md`; two of its lines take a set form here:
   - `Follows: nothing non-obvious to match` — if the change needed a choice
     the request did not settle, it failed **settled**;
   - under `Not yet seen:`, `<the behavior the request changes> — pending:
     <first environment after merge>, needs that deploy`, unless real
     evidence of it exists, in which case it goes under `Seen running:`.

   Then, **instead of the step 6 loop:**
   - If a register exists, compare `git diff <base>...HEAD` with it yourself.
   - Run `../../code-review/` **once** on the diff, with the description file
     counted as part of the change. On a host without subagents, read the
     diff and description against the request yourself instead.
   - Fix every finding whose quote matches at its cited `file:line`; discard
     the others. There is no second pass, whatever the severities.
   - Put `Pre-flight review: fast path, single pass (<code-review with its
     COUNTS line | own read>); <n> fixed, not re-reviewed` in the description
     and fold the fixes into the commit, rerunning the checks if any file
     changed.

   Steps 7–9 (confirm, publish, read back) then run unchanged. Review
   feedback (step 10) stays on this path as long as each fix still passes all
   five tests.

## Dropping back to the normal path

Switch as soon as the change outgrows a test, an undecided question surfaces,
a test fails for a reason you cannot see at once, or a high-stakes surface
comes into play. Say so in one line — `Leaving the fast path: <reason>` — and
continue with a plan (`../../writing-implementation-plans/`), its review, and
the full step 6 loop.

## What the fast path does not relax

The confirmation before pushing, opening or merging a PR or posting replies;
a unit test for every guard; the PR description standard.
