# draw.io recipe: architecture and box figures

## Contents

- [When this recipe applies](#when-this-recipe-applies)
- [House style](#house-style)
- [Cloud provider icons](#cloud-provider-icons)
- [Pitfalls](#pitfalls)
- [Rendering](#rendering)
- [Installing the renderer](#installing-the-renderer)
- [No renderer available](#no-renderer-available)

## When this recipe applies

Use draw.io (diagrams.net) for topology and box figures, and always for a
figure whose source is already a `.drawio` file. Three properties make it the
default:

- The file format is uncompressed mxGraph XML, so you can write it by hand and
  review it as a text diff.
- The owner can open the same file in the desktop or browser editor and adjust
  it without any conversion.
- It bundles the official AWS, GCP, and Azure icon sets.

You never operate the editor UI. Write the XML yourself and export it with the
headless draw.io desktop CLI through `scripts/render-drawio.sh`.

## House style

`examples/webhook-dispatcher.drawio` is a small, invented example that uses
every style below (bands, a key, icon cards, plain boxes, sync and async
edges, an OPEN box). Copy its cells instead of styling from scratch.

**Bands.** One full-width rectangle per tier, its name in capitals as the
value:

```
rounded=0;whiteSpace=wrap;html=1;fillColor=#f7f8fa;strokeColor=#d0d5dd;fontColor=#667085;fontSize=11;fontStyle=1;align=left;verticalAlign=top;spacingLeft=14;spacingTop=6;
```

**Plain boxes,** for anything that is not a single cloud service (a
boundary, a third-party API, another group's platform). Add the key colors
from the table below; the value is `<b>name</b><br>what it does`:

```
rounded=1;arcSize=12;whiteSpace=wrap;html=1;fontSize=11;spacing=6;
```

**Cloud services** take two cells. First a card, `rounded=1;arcSize=10;`
with key colors, about 170 wide by 120 high. Then a 48 × 48 icon cell placed
inside the card's upper half, carrying the label underneath it via
`verticalLabelPosition=bottom;verticalAlign=top;`.

**Edges:**

```
edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endFill=1;strokeColor=#344054;fontColor=#344054;fontSize=10;labelBackgroundColor=#ffffff;
```

Append `dashed=1` when the hop is asynchronous (a queue, an event, a
callback).

**Heading and key.** A bold 16 pt text cell for the title, and under it a row
of 16 × 16 color squares, each followed by a text cell. Include an entry for
every meaning the figure uses, plus `- - ▶ asynchronous` when it has a dashed
edge and OPEN when it has an undecided element.

Key colors (each means exactly one thing; print the key on the figure):

| Meaning | fillColor | strokeColor |
|---|---|---|
| Net-new | `#d5e8d4` | `#82b366` |
| Existing, changed by this work | `#dae8fc` | `#6c8ebf` |
| Existing, unchanged | `#ffffff` | `#999999` |
| Another group's system or a third party | `#eeeeee` | `#999999` |
| OPEN (not yet decided) | `#fff2cc` | `#d6b656` with `dashed=1` |

## Cloud provider icons

Stick to one provider per figure. An icon whose shape name is not in the
installed library renders as an empty square, so check every name you have
not used before.

**AWS** uses the `aws4` resource-icon shape:

```
shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<service>;html=1;outlineConnect=0;strokeColor=#ffffff;fillColor=<fill>;gradientColor=<gradient>;gradientDirection=north;
```

`<service>` is the lower-case service name with underscores, for example
`lambda`, `sqs`, `sns`, `dynamodb`, `s3`, `api_gateway`, `step_functions`,
`eventbridge`. Colors go by AWS category:

| Category | Examples | fillColor | gradientColor |
|---|---|---|---|
| Compute | `lambda`, `fargate`, `ec2` | `#D05C17` | `#F78E04` |
| Database | `dynamodb`, `rds` | `#3334B9` | `#4D72F3` |
| Application integration | `sqs`, `sns`, `step_functions`, `eventbridge` | `#BC1356` | `#F34482` |
| Storage | `s3` | `#277116` | `#60A337` |
| Machine learning | `sagemaker` | `#01A88D` | `#56C0A7` |

**GCP and Azure** are bundled too (`gcp2` stencils; `azure2` SVG images). The
reliable way to get a correct style string is to add the shape once in the
editor (More Shapes, enable the library), open Edit Style on it, and paste the
string into your XML. GCP strings look like `shape=mxgraph.gcp2.<name>;...`;
Azure ones look like
`image;aspect=fixed;html=1;image=img/lib/azure2/<category>/<Name>.svg;`.

**Checking a name.** Search the renderer's bundled `app.asar` for the exact
name, anchored so a prefix such as `lamb` cannot match `lambda`:

```bash
# Per-user install (install-drawio-renderer.sh), Linux:
ASAR="${DRAWIO_HOME:-$HOME/.local/opt/drawio}/app/resources/app.asar"
# Per-user install, macOS:
#   ASAR="${DRAWIO_HOME:-$HOME/.local/opt/drawio}/app/draw.io.app/Contents/Resources/app.asar"
# Existing macOS app: /Applications/draw.io.app/Contents/Resources/app.asar
grep -c -a -E "mxgraph\.aws4\.<name>([^A-Za-z0-9_]|$)" "$ASAR"   # 0 means the name is wrong
```

The render is the final check: an empty square in place of an icon is a bad
name.

## Pitfalls

These are the mistakes that most often cost an extra render.

- **Give every cell id a short figure prefix** (`wd_card_queue`,
  `wd_e_enqueue`). `0` and `1` are reserved for the root and the default
  layer, and bare common words as ids clash in some loaders.
- **Size boxes to their text.** Budget roughly 0.62 × the font size in pixels
  per character of the longest line, plus 12 px on each side; at 11 pt, three
  lines need about 52 px of height. The renderer installer provides Liberation
  Sans, which is metric-compatible with Arial, so what fits in the export also
  fits in the editor.
- **Connect edges to the card, not to the icon on it,** and set
  `exitX`/`exitY`/`entryX`/`entryY` explicitly so the ports align; leaving
  them free makes arrows bend.
- **Keep edge labels off boxes.** If an edge passes over a box, its label lands
  on that box; route around it with waypoints (`<Array as="points">`).
- **Keep the width near 1200 to 1500 px** at scale 1, so the figure is
  readable at a doc's normal width.
- **Never save compressed.** In the editor use File, Properties, and clear
  Compressed; a compressed diagram is an opaque base64 string that neither a
  diff nor an agent can work with.
- **HTML labels** need `html=1` in the style, and the markup in `value` must
  be XML-escaped (`&lt;b&gt;name&lt;/b&gt;&lt;br&gt;role`).

## Rendering

```bash
scripts/render-drawio.sh <name>.drawio <name>.png            # default scale 2
scripts/render-drawio.sh <name>.drawio <name>.png --scale 3  # for a dense figure
```

The script calls the draw.io desktop CLI export (`-x -f png -s <scale>`). On
a Linux machine without a display it runs a temporary Xvfb just for that
export. When it succeeds it prints only the output path; when no renderer can
be found it exits with status 3. Afterwards, open the PNG and judge it against
`diagram-conventions.md`, as in `../SKILL.md` step 5.

## Installing the renderer

Ask the user first. The installer needs no root and is safe to re-run:

```bash
scripts/install-drawio-renderer.sh --check   # report what is present, change nothing
scripts/install-drawio-renderer.sh           # install, or repair a partial install
```

It fetches a **pinned** draw.io desktop release (31.7.0 unless
`DRAWIO_VERSION=<x.y.z>` overrides it) from the public `jgraph/drawio-desktop`
GitHub releases and checks the download against the sha512 recorded in that
release's update manifest before unpacking anything:

- **macOS:** the `draw.io-<arm64|x64>-<version>.zip` asset, checked against
  `latest-mac.yml`, unpacked to `$DRAWIO_HOME/app/draw.io.app`. An existing
  `/Applications/draw.io.app` or `~/Applications/draw.io.app` is used as is.
- **Linux:** the matching AppImage, checked against `latest-linux*.yml` and
  extracted under `$DRAWIO_HOME/app`. Xvfb and Liberation Sans must come from
  the system package manager; if either is missing the script prints the
  command for the owner to run and never calls sudo itself.

`DRAWIO_HOME` defaults to `~/.local/opt/drawio`; the render script reads it
too.

## No renderer available

Still make the edit in the `.drawio` source (an existing draw.io figure stays
in draw.io), then give the owner this export step:

> Open `<file>.drawio` in the draw.io desktop app, or at
> https://app.diagrams.net via File, Open from, Device. Export with File,
> Export as, PNG at 200% zoom, and overwrite `<file>.png`.

Report the figure as not checked.
