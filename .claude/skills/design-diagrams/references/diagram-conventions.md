# Figure conventions (every tool)

## Contents

- [Depict the outcome, not the deliberation](#depict-the-outcome-not-the-deliberation)
- [Draw only what you verified](#draw-only-what-you-verified)
- [A single color key](#a-single-color-key)
- [External systems as plain boxes](#external-systems-as-plain-boxes)
- [Sequences from the caller's side](#sequences-from-the-callers-side)
- [Labels](#labels)
- [Completeness and detail](#completeness-and-detail)
- [Check the render](#check-the-render)
- [Sources, outputs, and placement](#sources-outputs-and-placement)

These rules apply whichever recipe you use. Read them before you write a
source, and hold the exported PNG up against them before you hand it back.

## Depict the outcome, not the deliberation

A design figure shows **what exists and how requests move through it**. The
history of how that was decided stays out.

- **Never put references like `ADR-0007`, `Decision 3`, or `§4.2` on the
  figure.** Those belong in the prose. Label the effect instead: write
  "one in-flight delivery per endpoint", not "one in-flight delivery per
  endpoint (ADR-0007)".
- Reasons are the doc's job; the figure only answers *what happens*.

## Draw only what you verified

- Every node, edge, field, table name, and step must be confirmed against the
  code, design doc, schema, or contract. **Never fill gaps with likely-looking
  wiring.** An arrow that seems right is still unverified.
- When the design really has not decided something, show it as **OPEN** in its
  own style (amber fill, dashed border, labelled "OPEN: <question>"). Never
  disguise it as a settled part.
- Whether something is new or already exists is a claim too, so check it. If
  the design reuses an existing queue or service, do not color it as new.

## A single color key

- Choose the key **one time**, use it throughout, and print it on the figure.
- **A color has exactly one meaning.** A typical slip is using green for new
  components and also for arrows that cross a boundary. Keep separate color
  sets for nodes and for edges so the two never overlap.
- For draw.io, the key colors are fixed in `drawio-diagrams.md` § House style.
- A node key that suits most build-or-reuse designs:
  - **green**: a component this work creates
  - **blue**: an existing component this work modifies
  - **white with gray border**: existing and untouched
  - **gray fill**: owned by another group or a third party
  - **amber, dashed**: OPEN
- A matching edge key (adjust per project):
  - **solid dark**: synchronous call
  - **dashed dark**: asynchronous hop (queue, event, callback)
  - **orange**: a write into a store this work introduces
  - **blue, dashed**: a read from that store

## External systems as plain boxes

When a boundary or outside system is not one specific cloud service (a
gateway product, a payment provider, a platform run by another group), draw a
**plain box that states its function**, for example "Gateway: auth, rate
limits, schema checks". Do not give it a cloud icon, and do not label it
generically as a "black box".

## Sequences from the caller's side

A sequence figure should let the reader stand where the caller stands: **each
request it sends and each answer it receives**. A chain that starts at the
caller and only flows away from it is an architecture figure in disguise.

- Draw every reply back to the caller (the `202` with an id, each poll
  result, the final state) and show the gaps where the caller waits and asks
  again.
- Beginning the figure at the caller is required but does not by itself make
  it a caller's-view sequence.
- Use the **real request and response bodies**, with the field names from the
  contract (confirmed), not placeholders like "status = done".

## Labels

- Make the **main name bold** and keep any second line plain and brief.
- **Label things by what they are.** For a store, lead with the table or topic
  name in bold, then its role: "**attempts** / one row per delivery, TTL". For
  a service, name the job it does, not the compute it runs on.
- **No abbreviations**: write "transaction", not "txn".
- Short node labels; detail goes on **edge labels** or into a **companion
  table** (see the last section).

## Completeness and detail

- Include **every** entity that matters and each place it is read or written.
  Do not drop a table because space is tight.
- Keep nodes brief by putting the when and the who of a write on its edge
  ("written on create, single transaction"). If that is still crowded, make
  two figures.

## Check the render

Open the exported image and confirm:
- no label covers its icon, runs past the canvas, or sits off-center in its
  box;
- everything drawn has been verified, and every OPEN element looks open;
- the key is present and matches the colors used;
- text is still readable at the width the doc will show it.

On wide figures, crop and zoom to see detail. Each recipe's Pitfalls section
lists fixes for the usual faults.

## Sources, outputs, and placement

- The **source is text** (`.puml`, `.drawio`, `.py`, or a hand-written `.svg`),
  kept in version control and re-renderable; the **PNG is the single generated
  file**. Skip SVG exports: the source already scales, and some tools write
  SVGs that point at icons by absolute local path, which breaks on every other
  machine.
- **Optional companion table:** a short markdown table listing each node, its
  service type, and the name the project uses for it. It makes the figure
  rebuildable in another tool and works as a checklist when verifying.
- Inserting the image into a doc or publishing system is a **separate step the
  owner approves**. Uploading through the doc system's own image feature is
  usually sturdier than a relative-path link, which tends to break once
  published.
