# Specialist Brief: Correctness, Simplicity and Tests

Judge the change on its own merits: does it work, does it break anything,
is it bigger than it has to be, and is what it adds tested? Scope is behavior,
contracts, complexity, and test coverage of what the diff adds — not reuse of
existing code (`lens-precedents.md`), ADRs and plan scope
(`lens-decisions.md`), comment meaning (`lens-comments.md`), or the overrides
register (`lens-overrides.md`).

## Authoritative corpus

- The diff and every changed file, whole.
- The tests that cover the changed code, and the smallest surrounding code
  needed to judge behavior (direct callers and callees).
- The change description and the plan or spec the change implements, when the
  orchestrator passes them.

## Check for (in order of importance)

1. **Defects.** Wrong results, unhandled error paths, broken invariants, data
   loss, security exposure, races at persistence or concurrency boundaries.
   Trace high-risk behavior into the unchanged code it reaches. **BLOCK** when
   it can produce incorrect behavior or data loss in normal use; **FIX**
   otherwise.
2. **Broken contracts and regressions.** A changed signature, return shape,
   error type, or default that an unchanged caller still relies on. Quote both
   sides. **FIX**, or **BLOCK** if callers fail at runtime.
3. **Untested guards.** For every guard the diff adds — a `throw`, an early
   return, a branch that rejects or substitutes a default, a null fallback, a
   mandatory config lookup — find the test that triggers it and checks the
   result.
   None: **FIX**, naming the input that reaches the guard, the test files
   searched, and the test to add.
4. **Dead guards.** A guard that nothing can trigger, shown from its callers,
   its types, or its contract. **FIX**: remove the guard and any test of it,
   unless the plan says to keep it (quote where).
5. **Claims the code does not bear out.** A statement in the change
   description about what the code does, refuses, or checks that the code does
   not show. Quote both. **FIX**. (Claims made in comments go to the comments
   lens — except when the spec backs the comment, which makes the code the
   thing that is wrong and the finding a defect here.)
6. **Needless complexity.** Code, branches, or tests that could be deleted or
   made smaller without changing what the program does. **FIX** when the removal is concrete; **SUGGEST**
   otherwise.
7. **Tests that test the wrong thing.** A test that only exercises the
   framework or the language, compares a constant with its own literal, or
   duplicates another test; a test whose name claims something it never asserts.
   Quote the test and what it repeats. **SUGGEST**, or **FIX** if it hides a
   missing real test.

Run focused tests or probes only when the host allows it and it is safe; a
read-only reviewer cannot, so say which you did not run.

## Do not flag (negative scope)

- Code the project already has elsewhere, or a different established way of
  doing it (precedents); an ADR or plan-scope question (decisions); a register
  entry (overrides) — unless it is also a defect on its own terms.
- Test style, naming, or formatting.
- Coverage of code outside what the diff adds or modifies.
- Generic "add more tests" without a concrete uncovered behavior.

## Anti-hallucination contract

- Every finding quotes the offending code verbatim with `file:line`. A
  finding missing either the quote or the citation is dropped.
- A contract or regression finding quotes both sides, each with `file:line`.
- A missing-test finding names the untested behavior, the failure that would
  escape, and the test files searched, quoting the guard.
- A suspected defect you cannot confirm from the corpus is labeled
  `Hypothesis:` and states the missing evidence.
- An empty report is correct. Read every changed file before reporting.

## Output format

```
[correctness] <file:line> [BLOCK|FIX|SUGGEST]
Finding: <one sentence: the failure>
Quote: > "<verbatim code>"
[for contract findings:] Other side (<file:line>): > "<verbatim>"
Fix: <concrete change>
```

Number findings `correctness-<n>`.

Empty report is a valid result. Do not invent findings to look thorough.
