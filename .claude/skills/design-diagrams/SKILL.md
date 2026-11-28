---
name: design-diagrams
description: Produce a design figure as a text source that lives in version control and can be re-rendered at any time (a PlantUML sequence, a draw.io architecture or box figure with public AWS, GCP, or Azure icons, a quick render with the Python `diagrams` package, or an SVG written by hand), export it to PNG, and inspect the PNG before handing it back. Use when asked to draw or diagram a flow, an architecture, a sequence, or an interaction, to add a figure to a design doc, or when a design-doc task concludes that a figure is needed. Owns only the figure source; it never edits doc prose and never embeds the figure itself.
---

# Design Diagrams

The deliverable is a figure **source** checked in next to the doc, plus one
PNG generated from it. Choose the figure type, write the source using that
type's recipe, export it, and then actually inspect the PNG and correct what
you see. A source that compiles is not done; a render that passes the
conventions is.

## Scope

Figure types and their recipes (paths relative to this file):

| Figure type | Pick it when you need | Tool | Recipe |
|---|---|---|---|
| **Sequence** | What a caller sends and what it gets back over time: request and response, waiting on async work, retries, a handshake between several parties | PlantUML | `references/plantuml-diagrams.md` |
| **Architecture / box** | How services connect, with official cloud icons; a box figure for a design doc; anything already saved as `.drawio` | draw.io XML, exported headless | `references/drawio-diagrams.md` |
| **Architecture, quick** | A disposable topology render when draw.io is not available | Python `diagrams` on Graphviz | `references/python-diagrams.md` |
| **Hand-written SVG** | Exact placement: swim-lanes, state machines, ERDs, decision flows | SVG, exported with `rsvg-convert` | `references/hand-authored-svg.md` |

Also here:
- `references/diagram-conventions.md`: the rules every figure is judged by.
  Read it before writing any source.
- `references/when-to-diagram.md`: whether a design needs a figure, and of
  which type. The design-doc skills (`../design-doc-write/`, and
  `../design-doc-edit/` where installed) use it and call this skill when it
  says yes.
- `references/examples/webhook-dispatcher.drawio`: a small invented draw.io
  figure demonstrating the house style.
- `scripts/render-drawio.sh`: exports a `.drawio` to PNG or JPG without a GUI.
- `scripts/install-drawio-renderer.sh`: installs a pinned draw.io desktop
  release for the current user, verified by checksum; `--check` only
  reports.

Not covered:
- Doc prose: `../design-doc-write/` or `../design-doc-edit/`.
- Reviewing a design doc: `../design-doc-review/`.
- Placing the figure into a doc, wiki, or site; the owner does that.
- Data charts (bars, lines, scatter plots); use a plotting library.

## Steps

### 1. Choose the type and pin down the frame

Use the Scope table; if the user did not specify, infer and say which you
picked. Behaviour over time means a sequence, connections mean architecture,
and lanes, states, or entities mean hand-written SVG. Many designs are best
served by a pair: a sequence from the caller's side and an architecture
figure for the topology. Suggest both when that applies.

Then settle the frame before drawing anything:
- the actor whose point of view the figure takes;
- the single flow it covers (creating a record and editing it are separate
  figures);
- any phase or release labels that limit what appears.

### 2. List and check every claim

Write down each node, edge, and label the figure will show, and confirm each
one against the code, the design doc, the schema, or the API contract. Draw
nothing you could not confirm. Where the design has not decided something,
plan an **OPEN** element for it (`diagram-conventions.md` § Draw only what you
verified). Fix the color key now, including which parts are new and which
already exist.

### 3. Write the source

Start from the skeleton in the matching recipe; the recipes record layout
fixes that took many renders to find, so reuse them. Apply the conventions:
short node names in bold, a single printed key, plain boxes for external
systems, no decision citations, and the caller's perspective for sequences.

Unless the project says otherwise, store `diagrams/<name>.<ext>` next to the
doc it belongs to, with `diagrams/<name>.png` committed alongside. Keep exactly
one copy of each source so nothing drifts.

### 4. Export to PNG

Each source produces **one PNG**, which is both the embeddable output and the
thing you inspect in step 5. The recipe has the command and the install
steps. Do not produce an SVG export as well; the source is already the
editable, scalable form (a hand-written `.svg` counts as source). If no
renderer can be installed, return the recipe's manual export instructions and
state that the figure was not inspected.

### 5. Inspect and fix

**Open the PNG and look at it**, using `diagram-conventions.md` § Check the
render. In particular:
- labels colliding with icons, spilling off the canvas, or off-center;
- a missing key, or one color used for two meanings;
- anything unconfirmed drawn as settled, or an OPEN element that does not
  look open;
- citations of decisions inside the figure, unreadable text, or entities
  left out.

For a wide figure, crop to the area in question (ImageMagick:
`magick in.png -crop WxH+X+Y +repage out.png`). Edit the source, export again,
and look again until it passes. Each recipe's Pitfalls section covers the
usual layout faults.

### 6. Report

Return the block in Output format. Do not place the figure in any document.

## Pause-for-confirmation rules

- **Ask before drawing** if the actor, the flow, or the phase is unclear; a
  wrong frame invalidates everything after it.
- **Ask, or draw it as OPEN,** when you cannot confirm an element. An
  unconfirmed arrow is never drawn as settled.
- **Never embed or publish** the figure. Return the paths; the owner or the
  doc's author places it.
- **Never port an existing `.drawio` to another tool.** Edit the file you
  have.
- **Ask before installing a renderer** on the user's machine. The installers
  are safe to re-run, and `--check` changes nothing.

## Style

- Text source under version control; the PNG is always regenerated from it.
- One flow per figure. Split before you crowd.
- The figure shows what happens; the reasons belong in the doc.
- Brief bold node names; put detail on edge labels or in a companion table.
- A single key, printed on the figure, with one meaning per color.

## Output format

```
Figure:   <one line on what it depicts>
Source:   <path to .puml | .drawio | .py | .svg>
PNG:      <path, or "not rendered: <manual export step>">
Inspected: <what step 5 checked and corrected, or "not inspected: no render">
Belongs in: <doc path and section>
Open items: <OPEN elements or unconfirmed wiring found, or "none">
```

## What this skill is NOT

- **Not a doc author.** Prose and captions belong to the doc skills; this
  skill owns the figure source only.
- **Not an editor operator.** It writes `.drawio` XML and exports from the
  command line. If the owner edits in the draw.io app, continue from the
  file they saved, uncompressed.
- **Not a decision log.** Figures carry no ADR or section references.
- **Not a source of new facts.** Only confirmed elements are drawn; the rest
  is OPEN.
