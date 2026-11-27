# The overrides register

Single definition of the overrides register: its location, its entry format,
its force, and how entries get in and out. Skills that use the register point
here rather than restating any of it; `lens-overrides.md` is the review check
built on it.

## What it is

An **optional** project file of the owner's standing corrections — things
they want honored every time, such as "handlers never retry downstream calls;
the caller decides" or "new config keys live in `settings/defaults.toml`, not
in code." Each is too small for an ADR and too project-specific for a shipped
review lens.

Projects without one lose nothing: a skill that would read it reports
`Skipped: no register`, and nothing blocks on it.

## Where it lives

Resolve it in this order and stop at the first hit:

1. A layer with `id: overrides` in the project's `context-manifest.yaml`:

   ```yaml
   layers:
     - id: overrides
       title: "Owner overrides register (optional; hand-maintained)"
       path: docs/overrides.md
       skill: null     # no update-* skill owns it; see "Adding entries"
       review: null
   ```

2. Otherwise, `docs/overrides.md` if that file exists.
3. Otherwise there is no register.

Other skills call it "the project's overrides register, located as
`register.md` defines" and do not repeat these steps.

## Entry format

One `OV-<n>` heading per entry, numbered in order added and never reused (a
retired entry keeps its heading).

```markdown
## OV-12: Webhook payloads are versioned

- **Rule:** Every outbound webhook payload carries a `schema_version` field;
  a change to a payload's shape bumps it.
- **Scope:** `webhook-dispatcher/**`. Internal queue messages are exempt.
- **Why:** "Two integrators broke silently when we renamed a field." (owner,
  2026-05-02, review of the retry-backoff change)
- **Added:** 2026-05-02
```

- **Rule** — a single sentence a reviewer can answer yes or no against a
  change. This is the line `lens-overrides.md` quotes.
- **Scope** — where it applies: paths, kinds of change, or "all code". An
  entry without Scope applies to everything the project's skills plan, write,
  or review.
- **Why** — preferably the owner's words, with when and where they said them,
  so a later reader can tell when the rule has outlived its reason.
- **Retired:** `<date>: <reason>` — once the owner withdraws it; binds nothing.

## How it binds

- A live entry is a hard rule layered over the skills' own rules. Any finding
  that cites one (`OV-<n>`) is FIX or higher.
- Declining such a finding is the owner's call alone, recorded as their quoted
  words and where they said them. Neither the implementer, the plan author,
  nor a review fold can waive it.
- If an entry conflicts with an Accepted ADR, the ADR wins until the owner
  resolves the conflict; report it as a docs inconsistency.

## Adding entries

No `update-*` skill owns the register; the owner writes it or approves each
edit. Any session may propose a change, following these steps:

1. **Spot a candidate.** A candidate is a correction the owner actually gave —
   quotable text, not an inference from an edit they made — that they framed
   as standing ("always", "never", "every time") or that repeats an earlier
   one. A single, unqualified correction stays a one-off unless the owner asks
   for it to be generalized.
2. **Check it is new.** Search the live entries and the Accepted ADRs. If an
   ADR already decides it, cite the ADR instead. If an entry already covers
   it, the repeat shows that entry's Rule was too weak or vague: propose a
   sharper Rule (or wider Scope) for it rather than a second entry.
3. **Keep it general.** A correction that only fits the change where it came
   up is fixed there, not registered.
4. **Draft it** in the format above: the correction quoted in **Why**, and a
   **Rule** a reviewer could apply to a change they have never seen.
5. **Ask before writing.** Show the owner the draft (or the proposed
   sharpening, retirement, or merge) and write it only after they confirm.
6. **Retire or merge, never delete.** A withdrawn entry gets a `Retired:` line.
   Two entries that turn out to be one rule become one: the survivor takes the
   combined Rule and the other is retired with `merged into OV-<n>`.

Proposing nothing is the right result when no correction qualifies.
