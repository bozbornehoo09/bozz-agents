# Does this design need a figure?

Use this file to decide **whether** to draw and, if so, **what kind** of
figure. The design-doc skills (`../../design-doc-write/`, and
`../../design-doc-edit/` where installed) check it while writing and call this
skill when the answer is yes. How to draw is `../SKILL.md` § Steps; what a
finished figure must satisfy is `diagram-conventions.md`.

## Why figures help at all

Text delivers one idea after another, which suits reasoning: motives,
alternatives, tradeoffs. A diagram is read all at once, so the reader can see
several connections side by side instead of rebuilding them from paragraphs.

So the question is not how many components there are, but whether the
**shape** of their interaction is hard to follow in text. Shapes that usually
are: branches, request and reply, parallel work, loops, state written by more
than one party, fan-out, a lifecycle, relationships between entities. "The
`orders-service` calls `webhook-dispatcher`" needs no picture. Add a third
party, a reply that comes back later, or a table both sides write, and it
probably does.

## Picking the type

| What the design contains | What the figure must make visible | Type | Recipe |
|---|---|---|---|
| Three or more components connected in a non-obvious way: fan-out, a shared store, hops across a boundary, new parts next to existing ones | how things are connected | architecture | `drawio-diagrams.md`, or `python-diagrams.md` for a quick one |
| A call and its reply, a wait-then-poll, retries, ordering constraints, a handshake among several actors, an API contract | what happens, in order | sequence | `plantuml-diagrams.md` |
| Something that moves through states, with defined transitions and triggers | the lifecycle | hand-written SVG | `hand-authored-svg.md` |
| Entities where ownership, cardinality, or keys shape the design | how the data relates | hand-written SVG | `hand-authored-svg.md` |
| Logic that branches, where the branches themselves are important | the decision paths | hand-written SVG | `hand-authored-svg.md` |

Expect to need two figures for many designs: a sequence showing the caller's
experience and an architecture figure showing the parts. Each one still covers
a single flow.

## When not to draw

No figure is better than one that misleads or clutters.

- **A straight line.** If it is just "first this, then that, then done", a
  sentence or a numbered list says it better.
- **One exchange between two parties.** Write it.
- **A table in disguise.** Lists of dependencies or fields are already in
  their best form.
- **Missing facts.** If drawing it means guessing at connections, record an
  OPEN question in the doc instead of a confident-looking picture.
- **The figure is doing the arguing.** Reasons live in the prose. If the doc
  only makes sense with the figure, rework the prose; the figure should only
  show the outcome.

## Readers with no context

Design docs are often read by people who were not in the room: a reviewer
from elsewhere in the organization, someone checking security, a new hire. A
figure that lets them see, within seconds, which parts talk to which, where
the new work sits, and where the trust boundaries fall, is a cheap way to make
a complex design understandable to them. The two figures most docs end up
wanting are a sequence for the API contract and an architecture view of the
system.

## How the design-doc skills use this file

- They make the yes/no and which-type call here, then hand the drawing to this
  skill instead of producing the figure themselves.
- In the doc, the author writes only a **caption and a one-line reference**
  to the figure. The caption tells the reader what they are looking at; it
  does not restate the design argument.
- Putting the rendered image into the doc is a separate step that the owner
  approves. The source sits next to the doc; the caption sits in it.
