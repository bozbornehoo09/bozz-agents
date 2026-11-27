# Python `diagrams` recipe: quick topology renders

## Contents

- [What it is for](#what-it-is-for)
- [One-time setup](#one-time-setup)
- [Starter script](#starter-script)
- [Pitfalls](#pitfalls)
- [Pick another recipe when](#pick-another-recipe-when)

## What it is for

A fast way to get a topology picture with **official cloud icons** from a
short Python file, using the open-source `diagrams` package
(github.com/mingrammer/diagrams, MIT licence). It includes icon modules for
AWS (`diagrams.aws.*`), GCP (`diagrams.gcp.*`), Azure (`diagrams.azure.*`),
Kubernetes, on-premises software, and generic shapes; changing provider is a
matter of changing imports. Figures that will live in a design doc, or that
already exist as `.drawio`, go through `drawio-diagrams.md` instead.

## One-time setup

You need Graphviz plus the package. Install the package into its own virtual
environment at a pinned version, and note that version next to the source:

```bash
brew install graphviz        # Debian/Ubuntu: sudo apt-get install -y graphviz
python3 -m venv ~/.venvs/diagrams
~/.venvs/diagrams/bin/pip install 'diagrams==0.23.4'
```

Render to **PNG only**:

```bash
~/.venvs/diagrams/bin/python delivery-path.py    # produces delivery-path.png
```

Avoid SVG output from this tool. Graphviz links each icon into the SVG by its
**absolute path inside your venv**, so the icons disappear on any other
machine. A PNG has the icons baked in, and the `.py` file remains the source
you re-run.

## Starter script

```python
"""webhook-dispatcher delivery path, rendered with the `diagrams` package."""
from diagrams import Cluster, Diagram, Edge, Node
from diagrams.aws.compute import Lambda        # GCP alternative: diagrams.gcp.compute.Functions
from diagrams.aws.database import Dynamodb     # GCP alternative: diagrams.gcp.database.Firestore
from diagrams.aws.integration import SQS       # GCP alternative: diagrams.gcp.analytics.Pubsub

# ---- labels ---------------------------------------------------------------
def html_label(title, *lines):
    """Graphviz HTML label: bold title, then plain lines.
    Never put a raw <, > or & in title/lines (write the arrow character, &amp;)."""
    body = "".join(f"<BR/>{line}" for line in lines)
    return f"<<B>{title}</B>{body}>"

# ---- node factories -------------------------------------------------------
# Icon nodes: fixed size, taller than wide, icon anchored at the top centre and
# the label at the bottom, so text never lands on the icon.
# Rule of thumb: height is about width + 0.4 (inches).
ICON_NODE = dict(fixedsize="true", width="2.0", height="2.4",
                 imagescale="true", imagepos="tc", labelloc="b")

def service(kind, title, *lines):
    return kind(html_label(title, *lines), **ICON_NODE)

def outside(title, *lines):
    """Plain rounded box for a boundary or third-party system (no single icon).
    fixedsize false lets it grow to its text; labelloc c centres the text."""
    return Node(html_label(title, *lines), shape="box", style="rounded,filled",
                fixedsize="false", labelloc="c", width="1.8", height="0.6",
                margin="0.18,0.12", fillcolor="#eeeeee", color="#999999",
                fontcolor="#1d2939", fontname="Helvetica", fontsize="10.5")

# ---- color key: each value means one thing, and the title prints it -------
NEW_GROUP = dict(style="rounded", bgcolor="#eef8ec", pencolor="#4d8a3c", color="#4d8a3c",
                 penwidth="2.4", fontcolor="#4d8a3c", fontsize="10", margin="14")
OPEN_GROUP = dict(style="rounded,dashed", bgcolor="#fff8e1", pencolor="#a6731a",
                  color="#a6731a", penwidth="2", fontcolor="#a6731a", fontsize="10", margin="14")
CALL = dict(color="#344054", fontcolor="#344054")
HOP = dict(style="dashed", color="#344054", fontcolor="#344054")
WRITE_NEW = dict(color="#d9480f", fontcolor="#d9480f", penwidth="1.6")
READ_NEW = dict(style="dashed", color="#1c5bd9", fontcolor="#1c5bd9")

TITLE = ("webhook-dispatcher: delivery path\n"
         "green group = net-new | solid = sync call | dashed = async hop | "
         "orange = write to new table | blue dashed = read from it")

with Diagram(
    TITLE, filename="delivery-path", outformat="png", show=False, direction="LR",
    graph_attr=dict(label=TITLE, labelloc="t", fontname="Helvetica-Bold", fontsize="15",
                    bgcolor="white", pad="0.9", nodesep="0.6", ranksep="1.0"),
    node_attr=dict(fontname="Helvetica", fontsize="11"),
):
    producer = outside("orders-service", "emits order events")
    subscriber = outside("Subscriber endpoint", "customer-hosted HTTPS")

    with Cluster("net-new", graph_attr=NEW_GROUP):
        ingest = service(Lambda, "Ingest API", "validates, stamps id")
        queue = service(SQS, "deliveries", "one message per target")
        sender = service(Lambda, "Sender", "signs and posts")
        attempts = service(Dynamodb, "attempts", "status per delivery")

    producer >> Edge(label="POST /v1/events", **CALL) >> ingest
    ingest >> Edge(label="enqueue", **HOP) >> queue
    queue >> Edge(label="consume", **HOP) >> sender
    sender >> Edge(label="signed POST", **CALL) >> subscriber
    sender >> Edge(label="records outcome", **WRITE_NEW) >> attempts
```

`OPEN_GROUP` and `READ_NEW` are unused here; keep them so the key stays the
same across figures, and wrap an undecided part in
`Cluster("OPEN: <question>", graph_attr=OPEN_GROUP)`.

## Pitfalls

- **Label drawn over the icon.** Without help the icon fills the whole node
  and the label sits on it. `ICON_NODE` fixes that with a tall fixed node,
  `imagepos=tc`, and `labelloc=b`. Too tall leaves a gap; stay near
  height = width + 0.4.
- **Text spilling out of icon nodes.** Fixed-size nodes do not grow. Limit an
  icon label to the bold title plus one short line; move the rest onto edges.
- **Partial bold needs an HTML label** (`html_label()` builds
  `<<B>...</B>...>`). In an HTML label a raw `<`, `>`, or `&` is a Graphviz
  parse error: use the arrow character and `&amp;`. Plain edge labels may use
  `->`.
- **Box text overflowing or stuck at the bottom.** A plain `Node(shape="box")`
  inherits the package defaults `fixedsize="true"` and `labelloc="b"`;
  override them as `outside()` does.
- **Group border ignores `color`.** A cluster's border is `pencolor` and its
  fill is `bgcolor`; set both.
- **Showing a node's internals** (say, the steps inside a workflow): add a
  plain `Node(shape="box", fixedsize="false")` whose lines end in `\l` for
  left alignment (`\\l` in a Python string), linked by
  `Edge(style="dotted", dir="none", color="#667085")`.
- **A store written from both ends of the figure** produces long, crossing
  arrows. Note each write point briefly on its writer and draw a single edge
  per writer.
- **Rightmost labels cut off.** Increase `pad` and shorten the labels; the
  canvas does not always grow to fit a label that overflows its icon node.
- **Very wide output or long backward edges** usually mean a store is placed
  far from its writer. Regroup the nodes, or live with it; `nodesep` and
  `ranksep` adjust spacing.

## Pick another recipe when

- The figure is about **calls and replies over time**: `plantuml-diagrams.md`.
- It needs **custom lanes, states, or an ERD**: `hand-authored-svg.md`.
- It will go in a **design doc and be hand-edited later**, or a `.drawio`
  already exists: `drawio-diagrams.md`.
