# The decisions-in-force map (`IN-FORCE.md`)

The ADR index lists every decision ever recorded. A session that only needs
the calls currently binding it would have to open each ADR and work out what
is still live. The map saves that read: one hand-kept line per decision in
force, citing the ADRs that set its current form. `context-up`'s loader
prints it in place of the ADR list once it has a decision in it.

## Where it lives and who writes it

- `IN-FORCE.md` in the `decisions` layer directory, beside `README.md`.
- **The map is written by hand.** Which ADRs still bind, and in what form,
  is a judgement. `adr_index.py write` creates it from the skeleton below
  only when the file is missing, and never writes an existing map.
- **The index is generated.** `adr_index.py write` rewrites the lines between
  the `adr-index` markers in `README.md` from each ADR's Status line. Prose
  outside the markers is never touched. An index with no markers is left
  alone and reported, so a hand-kept table keeps working until someone wraps
  it in the markers.

## Shape

1. A `DRAFT:` line, kept until every map line has been checked against the
   ADR it cites. While it stands, the ADRs themselves are the source; the
   loader repeats the line even when a load is cut.
2. `Map last changed: YYYY-MM-DD`, from the system clock.
3. `## In force`: decisions grouped under `### <topic>` headings the project
   picks (storage, API contract, deployment …). One line each: the decision
   as it stands today in one sentence, then the ADRs that made and shaped it,
   e.g. `- Webhooks retry with capped backoff (ADR-0004; narrowed by ADR-0009)`.
4. `## Unclear`: decisions whose current form the ADRs do not settle, left for
   the owner. A supersession nobody recorded is listed here, never inferred.

## Keeping it current

- Writing, superseding or deprecating an ADR updates the map lines it
  changes, in the same change as the ADR.
- `adr_index.py check` reads the map when it exists and reports
  `map-missing` (an Accepted ADR the map never cites), `map-orphan` (a cited
  ADR that does not exist) and `superseded-in-map` (a line citing a
  Superseded ADR without its successor, or a Deprecated one).
- On a first build, draft every line from the Accepted ADRs, check each one
  against its ADR's Decision section, move anything uncertain to
  `## Unclear`, and only then delete the `DRAFT:` line.

## Skeleton

The block below is what `adr_index.py write` copies into a new map;
`{project}` and `{date}` are filled in.

```markdown
# Decisions in force — {project}

DRAFT: created {date} with no lines checked. Until each line has been checked against its ADR and this line is deleted, read the ADRs themselves.

Map last changed: {date}

## In force
<!-- One line per decision under a ### topic heading:
- <the decision as it stands, in one sentence> (ADR-NNNN; refined by ADR-MMMM) -->

## Unclear
<!-- Decisions the ADRs leave unsettled, for the owner. -->
```
