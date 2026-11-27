#!/usr/bin/env python3
"""Measure a human-review design doc. Standard library only; measures, never judges.

Reports, for one markdown design doc:
  - body words (title down to the "## Appendices" divider, without fenced code, HTML
    comments or the Glossary) against references/length-budget.md, and words per section
  - glossary entries and any gloss over the per-gloss limit, and where the glossary sits
  - the audience notes appendix: present, after the divider, all six rows filled
  - the opening paragraph: present, unlabelled, not a placeholder, at most four sentences
  - acceptance lines ("Length accepted:", "Glossary size accepted:")
  - sentence lengths in body prose: median, share over 30 words, and each long sentence

Exit codes: 0 no gate problem; 1 a gate problem (no divider, body over ceiling without an
acceptance line, audience notes missing, misplaced or unfilled, opening missing, labelled
or a placeholder); 2 usage or input error. Glossary size never changes the exit code.

Usage: python3 -I measure_doc.py DOC.md [--type HLD|LLD|mini] [--json]
"""

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

# Copies of the tables in references/length-budget.md. Change both together.
BUDGETS = {"mini": (600, 1000), "LLD": (1800, 2500), "HLD": (2000, 2500)}  # (target, ceiling)
GLOSSARY = {"target": 15, "fix_above": 30, "gloss_words": 40}
LONG_SENTENCE = 30
DENSE_MEDIAN = 15
DENSE_LONG_SHARE = 0.05

AUDIENCE_FIELDS = ["Readers", "Prior knowledge", "Takeaway", "Stakes", "Ask", "Expected questions"]
DIVIDER = re.compile(r"^appendices\b", re.I)
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
PLACEHOLDER = re.compile(r"<[^<>\n]+>")
LABEL = re.compile(r"^\*\*[^*]{1,40}?[:.]\*\*")
ACCEPT = {
    "length": re.compile(r"^Length accepted:\s*(.*)$"),
    "glossary": re.compile(r"^Glossary size accepted:\s*(.*)$"),
}
ACCEPT_VALID = re.compile(r"^\d{4}-\d{2}-\d{2}\s*[—–-]+\s*\S")
SENTENCE_END = re.compile(r"(?<=[.!?])[\"')\]*]*\s+(?=[A-Z0-9\"'(\[`*])")
NON_PROSE_START = ("**Status:**", ">", "**Not covered here:**", "|", "- ", "* ", "#")


class MeasureError(Exception):
    pass


def words(text):
    """Whitespace tokens holding a letter or digit, so table pipes and dashes do not count."""
    text = re.sub(r"\]\([^)]*\)", "]", text)  # link targets are not read
    return sum(1 for tok in text.split() if re.search(r"[A-Za-z0-9]", tok))


def clean_lines(text):
    """Lines with HTML comments blanked and a flag for fenced code; line numbers are kept."""
    text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    out, in_fence = [], False
    for raw in text.split("\n"):
        if FENCE.match(raw):
            out.append(("", True))
            in_fence = not in_fence
            continue
        out.append((raw, in_fence))
    return out


def headings(lines):
    found = []
    for i, (line, code) in enumerate(lines):
        m = None if code else HEADING.match(line)
        if m:
            found.append((i, len(m.group(1)), m.group(2).strip()))
    return found


def h2_sections(heads, start, end):
    """(heading text, first line, end line) for each level-2 heading between start and end."""
    h2 = [(i, t) for i, lvl, t in heads if lvl == 2 and start <= i < end]
    return [(t, i, h2[k + 1][0] if k + 1 < len(h2) else end) for k, (i, t) in enumerate(h2)]


def infer_grain(title):
    t = (title or "").lower()
    if "high-level design" in t or "high level design" in t:
        return "HLD"
    if "low-level design" in t or "low level design" in t:
        return "LLD"
    if "mini-design" in t or "mini design" in t:
        return "mini"
    return None


def table_cells(line):
    if not line.strip().startswith("|"):
        return None
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
        return None  # separator row
    return cells


def paragraphs(lines, start, end, skip):
    """Prose blocks as (first line number, [(line number, text)]); list items are their own block."""
    blocks, cur = [], []
    for i in range(start, end):
        line, code = lines[i]
        s = line.strip()
        if code or i in skip or not s or HEADING.match(line) or s.startswith("|"):
            if cur:
                blocks.append(cur)
            cur = []
            continue
        if re.match(r"^([-*+]|\d+\.)\s+", s):
            if cur:
                blocks.append(cur)
            cur = [(i + 1, re.sub(r"^([-*+]|\d+\.)\s+", "", s))]
            continue
        cur.append((i + 1, s))
    if cur:
        blocks.append(cur)
    return blocks


def sentences(block):
    """Split one prose block into (line number, sentence) pairs."""
    text, starts = "", []
    for lineno, s in block:
        starts.append((len(text), lineno))
        text += re.sub(r"^(>\s*)+", "", s) + " "
    out, pos = [], 0
    for piece in SENTENCE_END.split(text):
        idx = text.find(piece, pos)
        pos = idx + len(piece)
        piece = piece.strip()
        if piece:
            lineno = max(n for off, n in starts if off <= idx)
            out.append((lineno, piece))
    return out


def measure(path, grain=None):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise MeasureError(f"cannot read {path}: {exc}")
    lines = clean_lines(text)
    heads = headings(lines)
    title_i = next((i for i, lvl, _ in heads if lvl == 1), None)
    title = next((t for i, lvl, t in heads if lvl == 1), None)
    grain = grain or infer_grain(title)
    if grain not in BUDGETS:
        raise MeasureError("grain unknown: pass --type HLD, LLD or mini (or put the grain in the title)")
    n = len(lines)
    divider = next((i for i, lvl, t in heads if lvl == 2 and DIVIDER.match(t)), None)
    body_start = title_i if title_i is not None else 0
    body_end = divider if divider is not None else n
    problems, notes = [], []
    if divider is None:
        problems.append('no "## Appendices" divider: the whole file is counted as body')

    sections = h2_sections(heads, 0, n)
    glossary = next(((s, e) for t, s, e in sections if t.lower() == "glossary"), None)
    gloss_lines = set(range(*glossary)) if glossary else set()

    # Body words, overall and per section.
    def count(a, b):
        return sum(words(lines[i][0]) for i in range(a, b) if not lines[i][1] and i not in gloss_lines)

    body_sections = h2_sections(heads, body_start, body_end)
    first_h2 = body_sections[0][1] if body_sections else body_end
    per_section = [{"section": "(title and opening)", "line": body_start + 1, "words": count(body_start, first_h2)}]
    for t, s, e in body_sections:
        if t.lower() != "glossary":
            per_section.append({"section": t, "line": s + 1, "words": count(s, e)})
    body_words = sum(x["words"] for x in per_section)
    appendix_words = sum(words(lines[i][0]) for i in range(body_end, n) if not lines[i][1])
    code_lines = sum(1 for _, code in lines if code)

    # Glossary.
    entries, long_glosses = 0, []
    if glossary:
        for i in range(glossary[0] + 1, glossary[1]):
            line, code = lines[i]
            s = line.strip()
            gloss = None
            if not code and re.match(r"^[-*+]\s+", s):
                parts = re.split(r"\s[—–-]\s|:\s", s, maxsplit=1)
                gloss = parts[1] if len(parts) > 1 else ""
            elif not code:
                cells = table_cells(s)
                if cells and len(cells) > 1 and cells[0].lower().strip("* ") not in ("term", ""):
                    gloss = cells[1]
            if gloss is not None:
                entries += 1
                if words(gloss) > GLOSSARY["gloss_words"]:
                    long_glosses.append({"line": i + 1, "words": words(gloss)})
    glossary_after_divider = bool(glossary and divider is not None and glossary[0] > divider)

    # Audience notes and acceptance lines.
    audience = next(((t, s, e) for t, s, e in sections if "audience" in t.lower()), None)
    aud = {"present": bool(audience), "line": audience[1] + 1 if audience else None,
           "after_divider": bool(audience and divider is not None and audience[1] > divider),
           "missing_rows": [], "unfilled_rows": []}
    accepted = {}
    if audience:
        rows = {}
        for i in range(audience[1] + 1, audience[2]):
            line, code = lines[i]
            cells = None if code else table_cells(line)
            if cells and len(cells) > 1:
                rows[cells[0].strip("* ").lower()] = (i + 1, cells[1])
            for key, rx in ACCEPT.items():
                m = None if code else rx.match(line.strip())
                if m:
                    accepted[key] = {"line": i + 1, "valid": bool(ACCEPT_VALID.match(m.group(1)))}
        for field in AUDIENCE_FIELDS:
            row = rows.get(field.lower())
            if row is None:
                aud["missing_rows"].append(field)
            elif not row[1] or PLACEHOLDER.search(row[1]) or row[1].strip().lower() in ("tbd", "todo", "?"):
                aud["unfilled_rows"].append({"field": field, "line": row[0]})
        if not aud["after_divider"]:
            problems.append("audience notes sit in the reading path: move them after the divider")
        if aud["missing_rows"] or aud["unfilled_rows"]:
            problems.append("audience notes incomplete: "
                            + ", ".join(aud["missing_rows"] + [r["field"] for r in aud["unfilled_rows"]]))
    else:
        problems.append("no audience notes appendix")
    for key, acc in accepted.items():
        if not acc["valid"]:
            notes.append(f"{key} acceptance line at {acc['line']} lacks a date or a reason; ignored")

    # Opening paragraph.
    opening = {"line": None, "sentences": 0, "status": "missing"}
    for block in paragraphs(lines, (title_i + 1) if title_i is not None else 0, first_h2, set()):
        first = block[0][1]
        if any(first.startswith(p) for p in NON_PROSE_START):
            continue
        joined = " ".join(s for _, s in block)
        opening = {"line": block[0][0], "sentences": len(sentences(block)), "status": "ok"}
        if LABEL.match(joined):
            opening["status"] = "labelled"
        elif PLACEHOLDER.search(joined):
            opening["status"] = "placeholder"
        break
    if opening["status"] != "ok":
        problems.append(f"opening paragraph {opening['status']}")
    elif opening["sentences"] > 4:
        notes.append(f"opening runs {opening['sentences']} sentences (at most 4)")

    # Sentence lengths in body prose.
    lengths, long_ones = [], []
    for block in paragraphs(lines, (title_i + 1) if title_i is not None else 0, body_end, gloss_lines):
        for lineno, s in sentences(block):
            w = words(s)
            lengths.append(w)
            if w > LONG_SENTENCE:
                long_ones.append({"line": lineno, "words": w, "start": " ".join(s.split()[:10])})
    median = statistics.median(lengths) if lengths else 0
    share = (len(long_ones) / len(lengths)) if lengths else 0.0
    if lengths and (median > DENSE_MEDIAN or share > DENSE_LONG_SHARE):
        notes.append(f"prose is dense: median {median} words, {share:.1%} over {LONG_SENTENCE}")

    # Budget verdict.
    target, ceiling = BUDGETS[grain]
    length_ok = "length" in accepted and accepted["length"]["valid"]
    if body_words > ceiling:
        if length_ok:
            notes.append(f"body {body_words} over ceiling {ceiling} by {body_words - ceiling}; accepted, informational")
        else:
            problems.append(f"body {body_words} words over the {grain} ceiling of {ceiling} by {body_words - ceiling}")
    elif body_words > target:
        notes.append(f"body {body_words} over the {grain} target of {target} (under the ceiling)")
    if entries > GLOSSARY["target"]:
        gl_ok = "glossary" in accepted and accepted["glossary"]["valid"]
        level = "FIX" if entries > GLOSSARY["fix_above"] and not gl_ok else "SUGGEST"
        notes.append(f"glossary has {entries} entries (target {GLOSSARY['target']}, FIX above "
                     f"{GLOSSARY['fix_above']}): {level}-level re-audit" + ("; accepted" if gl_ok else ""))
    if glossary_after_divider:
        notes.append("glossary sits after the divider; move it into the body")

    return {
        "doc": str(path), "grain": grain, "divider_line": divider + 1 if divider is not None else None,
        "body_words": body_words, "target": target, "ceiling": ceiling,
        "appendix_words": appendix_words, "code_lines": code_lines, "sections": per_section,
        "glossary": {"entries": entries, "long_glosses": long_glosses, "after_divider": glossary_after_divider},
        "audience": aud, "accepted": accepted, "opening": opening,
        "sentences": {"count": len(lengths), "median": median, "over_30_share": round(share, 4),
                      "long": long_ones},
        "problems": problems, "notes": notes,
    }


def render(r):
    out = [f"{r['doc']} ({r['grain']})",
           f"Body: {r['body_words']} words (target {r['target']}, ceiling {r['ceiling']}); "
           f"appendices {r['appendix_words']} words; fenced code {r['code_lines']} lines",
           "Per section:"]
    out += [f"  {s['words']:>6}  {s['section']} (line {s['line']})" for s in r["sections"]]
    g = r["glossary"]
    out.append(f"Glossary: {g['entries']} entries" + "".join(
        f"; gloss at line {x['line']} is {x['words']} words" for x in g["long_glosses"]))
    s = r["sentences"]
    out.append(f"Sentences: {s['count']}, median {s['median']} words, {s['over_30_share']:.1%} over {LONG_SENTENCE}")
    out += [f"  line {x['line']}: {x['words']} words: {x['start']} ..." for x in s["long"]]
    out += [f"PROBLEM: {p}" for p in r["problems"]] + [f"note: {x}" for x in r["notes"]]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Measure a design doc against the length budget.")
    ap.add_argument("doc")
    ap.add_argument("--type", choices=sorted(BUDGETS), help="grain; inferred from the title if omitted")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        result = measure(args.doc, args.type)
    except MeasureError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2) if args.json else render(result))
    return 1 if result["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
