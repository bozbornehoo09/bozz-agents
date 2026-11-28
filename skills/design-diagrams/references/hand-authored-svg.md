# Hand-written SVG recipe

Write the SVG markup yourself when placement has to be exact or no layout
engine produces the right picture: swim-lanes, a state machine, an entity
diagram, a branching decision, or a system view that is neither a call
sequence nor plain topology.

## Contents

- [Is it worth it?](#is-it-worth-it)
- [Skeleton](#skeleton)
- [Export](#export)
- [Conventions that apply here](#conventions-that-apply-here)
- [Pitfalls](#pitfalls)

## Is it worth it?

Good fits:
- **System or swim-lane views** where each band (caller, API, workers, data)
  holds boxes at chosen positions, colored by status (new, existing, external,
  OPEN), with numbered arrows for the order of steps.
- **State machines and entity diagrams** where position itself conveys
  meaning.

The price is that every coordinate is yours to set. Keep this for the one or
two central figures of a doc; for everyday flows PlantUML or draw.io is
quicker.

## Skeleton

Put all styling in `<defs>`: one arrowhead `<marker>` and a `<style>` block of
classes. The drawing itself is then plain `<rect>`, `<text>`, `<path>`, and
`<circle>` elements that use those classes. The status classes use the same
colors as `drawio-diagrams.md` § House style, so figures from either tool
look alike.

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="380" viewBox="0 0 1100 380"
     font-family="Liberation Sans, Arial, Helvetica, sans-serif">
  <defs>
    <marker id="head" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="8" markerHeight="8"
            orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#344054"/></marker>
    <style>
      /* layout */
      .band      { fill:#f7f8fa; stroke:#d0d5dd; }
      .band-name { font-size:11px; font-weight:bold; fill:#667085; letter-spacing:0.5px; }
      .name      { font-size:13px; font-weight:bold; fill:#1d2939; text-anchor:middle; }
      .role      { font-size:10.5px; fill:#475467; text-anchor:middle; }
      /* status fills, one meaning each */
      .is-new    { fill:#d5e8d4; stroke:#82b366; stroke-width:2; }
      .is-changed{ fill:#dae8fc; stroke:#6c8ebf; stroke-width:1.5; }
      .is-same   { fill:#ffffff; stroke:#999999; stroke-width:1.5; }
      .is-ext    { fill:#eeeeee; stroke:#999999; stroke-width:1.5; }
      .is-open   { fill:#fff2cc; stroke:#d6b656; stroke-width:1.5; stroke-dasharray:6 3; }
      /* edges */
      .sync      { fill:none; stroke:#344054; stroke-width:1.5; }
      .async     { fill:none; stroke:#344054; stroke-width:1.5; stroke-dasharray:5 4; }
      .edge-text { font-size:10px; fill:#344054; text-anchor:middle; }
      .step      { fill:#344054; }
      .step-n    { font-size:9.5px; font-weight:bold; fill:#ffffff; text-anchor:middle; }
    </style>
  </defs>

  <rect width="1100" height="380" fill="#ffffff"/>
  <text x="24" y="32" font-size="17" font-weight="bold" fill="#1d2939">webhook-dispatcher: delivery</text>

  <!-- band: DISPATCH -->
  <rect class="band" x="20" y="64" width="1060" height="130"/>
  <text class="band-name" x="32" y="82">DISPATCH</text>

  <!-- box: both text lines share the box's center x (115 = 40 + 150 / 2) -->
  <rect class="is-new" x="40" y="104" width="150" height="60" rx="8"/>
  <text class="name" x="115" y="130">Ingest API</text>
  <text class="role" x="115" y="148">validates, stamps id</text>

  <rect class="is-new" x="330" y="104" width="150" height="60" rx="8"/>
  <text class="name" x="405" y="130">deliveries</text>
  <text class="role" x="405" y="148">queue, one per target</text>

  <!-- async edge with a label above it and a numbered step marker -->
  <path class="async" d="M190,134 H328" marker-end="url(#head)"/>
  <text class="edge-text" x="260" y="126">enqueue</text>
  <circle class="step" cx="206" cy="134" r="8"/><text class="step-n" x="206" y="137.5">1</text>
</svg>
```

## Export

The `.svg` you wrote is the source; generate the PNG from it:

```bash
rsvg-convert -w 2200 delivery.svg -o delivery.png   # -w sets output width in px
```

`rsvg-convert` is part of librsvg (`brew install librsvg` on macOS,
`sudo apt-get install -y librsvg2-bin` on Debian or Ubuntu). Choose a width
that keeps the smallest text sharp at the doc's display size; double the
`viewBox` width is a sensible first try.

## Conventions that apply here

All of `diagram-conventions.md` applies. In SVG terms:

- Define the key once as classes and draw a small key on the canvas itself.
- Show outcomes only, no decision references, and verify every box and arrow.
- Center both text lines of a box on its middle x with `text-anchor:middle`,
  and space them evenly inside the rect.
- Add numbered step markers to arrows when the order of steps matters.
- Group related elements under a comment so the file stays editable, and
  export and **look at the PNG** after every change.

## Pitfalls

- `rsvg-convert` does not load web fonts. Name fonts that are installed on the
  machine, or the substitute font's wider glyphs push text past box edges.
- An arrowhead marker does not take the path's color; give the marker's own
  path a `fill`.
- A literal `&` in text breaks the XML; write `&amp;`.
- Official cloud icons are much easier in draw.io or Python `diagrams` than
  embedded by hand in SVG.
