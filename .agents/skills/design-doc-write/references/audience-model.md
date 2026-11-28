# Audience Model — the default cold reader, and how a project overrides it

The cold-read gate (`zero-context-gate.md`) puts a simulated reader in front of the doc.
This file says who that reader is when nobody has said otherwise, and how a project
declares its own readers and the vocabulary they already have. Two separate inputs:

- **Persona**: who is reading. Taken from the doc's **Readers** row
  (`audience-and-purpose.md`).
- **Known terms**: project vocabulary that persona already has, so the gate does not
  report it. Taken from the project audience file below.

## The default reader

> An experienced software engineer from a neighbouring team. They know the trade in
> general and know nothing about this project: none of its systems, names, or history.

"The trade in general" covers public, non-proprietary vocabulary: widely used
infrastructure building blocks (queues, object stores, key-value stores, load balancers,
caches, TTLs), common protocols and formats (HTTP and its status codes, TLS, JSON, REST,
gRPC), public cloud service names, and standard computer-science ideas (idempotency,
transactions, hashing, races, backoff, consensus). Anything particular to this project or
organization is not covered and needs explaining: internal service and team names,
codenames, in-house processes, and local identifiers.

## The project audience file

Optional. Looked up in this order, first hit wins:

1. the path in an `audience` key on the `design-docs` layer of `context-manifest.yaml`;
2. `design-doc-audience.md` at the root of the design-docs directory;
3. `design-doc-audience.md` next to the doc.

With no file, the default reader applies and no terms are pre-known. A project with one
kind of reader and no house vocabulary does not need a file.

```markdown
# Design doc audience

## Default persona
<One sentence that replaces the default reader, e.g. "A backend engineer in the
payments group who knows our deploy tooling but not this team's services.">

## Known terms — engineer
| Term | Meaning |
|---|---|
| <term> | <one line> |

## Known terms — <persona as written in a Readers row, e.g. "support lead">
| Term | Meaning |
|---|---|
| <term> | <one line> |
```

## Rules for known terms

- **It excuses passing mentions only.** A term the doc defines, introduces, or is about
  still needs its explanation in the doc, whether or not it is listed.
- **Lists are per persona.** An `engineer` entry silences the gate for engineer readers
  only. If a non-engineer reader is declared, give that persona its own list instead of
  stretching the engineer one.
- **Leave a term off when unsure.** Add it only when a real reader in that role would
  know it without looking, and always with a one-line meaning, so the list can be
  reviewed.
- **Where entries come from.** Two deliberate routes: the owner rejects a gate finding
  with "these readers know this term", or a glossary trim removes an entry every declared
  reader knows. Either way, add the row; otherwise the next cold read reports the term
  again.

## Choosing reader models

Readers run through whatever subagent facility the host has. On any host:

- **Mix models when you can.** If the host lets you pick a model per subagent, use at
  least two different ones; different models stumble on different gaps, and two copies
  of one model mostly agree with each other. Use tier names rather than pinned model
  versions where the host allows, so nothing goes stale when models change.
- **Do not use a model too small for the doc.** A weak reader gives a shallow
  explanation, misses gaps, and lets a confusing doc pass. Avoid the smallest tier on
  long or dense docs.

If the host gives no choice of model, use what it has and say so in the report. Timeouts
and retries are `zero-context-gate.md`'s.
