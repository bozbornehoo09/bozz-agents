#!/usr/bin/env python3
"""Mechanical helpers for the refining-technical-writing skill. They read files and never change
the text under review. Python standard library only.

  check_prose.py FILE
      Run Vale over FILE and print its candidates as JSON.
  check_prose.py FILE --against ORIGINAL
      Print, as JSON, every protected item (number, code span, id, URL, heading, table row, or a
      modal, negation, condition or quantifier word) that FILE holds fewer of than ORIGINAL.
      Does not need Vale.
  check_prose.py --sources
      Print, as JSON, the commit of the cached Humanizer, overrides whose pattern it has lost,
      and rule homes named in references/kinds.md that do not exist.
  check_prose.py [FILE] --kind SLUG[,SLUG...]
      Gather every rule a review of those kinds applies (their kinds.md rows and sections, the
      homes those rows name, general-rules.md, Humanizer and its overrides, detail blocks left
      out) into one cached file and print where it is. Given FILE, lint it afterwards.

Vale gets vale/vale.ini, the cached Deslop pack, the rules in vale/Plain/, and rules built afresh
from references/word-lists.md each run. A word-list file that cannot be parsed costs only those
generated rules; the "word_lists" field of the JSON says why.

Exit codes:
  0  the check ran; any findings are in the output
  2  usage error, unreadable file, unknown kind, or Vale itself failed
  3  Vale, the Deslop pack or Humanizer is not installed; stderr gives the install command
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path


class CheckError(Exception):
    """Reported to the user verbatim; exit 2."""


class NotInstalled(CheckError):
    """Something install.sh provides is absent; exit 3."""


# --- Where things live ------------------------------------------------------------------------

class Layout:
    """Every path the checker reads or writes. Tests build one pointing at a scratch tree."""

    def __init__(self, skill_dir, data_home, home):
        self.skill = Path(skill_dir)
        self.refs = self.skill / "references"
        self.vale_dir = self.skill / "vale"
        self.install = self.skill / "scripts" / "install.sh"
        self.cache = Path(data_home) / "bozz-agents" / "refining-technical-writing"
        self.home = Path(home)

    @classmethod
    def from_environment(cls):
        home = Path.home()
        data = os.environ.get("XDG_DATA_HOME") or home / ".local" / "share"
        return cls(Path(__file__).resolve().parents[1], data, home)

    def ref(self, name):
        return self.refs / name

    @property
    def deslop(self):
        return self.cache / "vale" / "styles" / "Deslop"

    @property
    def humanizer(self):
        return self.cache / "humanizer"


OWN_STYLE = "Plain"
DETAIL_START = "<!-- detail -->"
DETAIL_END = "<!-- /detail -->"


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def heading_depth(line):
    """Level of an ATX heading ('## x' is 2); 0 for anything else."""
    stripped = line.lstrip("#")
    depth = len(line) - len(stripped)
    return depth if depth and stripped.startswith(" ") else 0


def opens_or_closes_fence(line):
    return line.lstrip().startswith("```")


def tidy(lines):
    """Lines joined into text with no more than one blank line in a row, ending in one newline."""
    text = "\n".join(lines)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.strip() + "\n"


# --- word-lists.md ----------------------------------------------------------------------------

LIST_SECTIONS = ("filler", "phrase-for-word", "redundant-modifiers", "coordinated-synonyms",
                 "hidden-verbs", "complex-words", "vague-quantities")
KIND_COMMENT = re.compile(r"<!--\s*kind:\s*(list|table)\s*-->")
BULLET_TERM = re.compile(r"^- `([^`]+)`")
_GO_SPECIALS = ".^$*+?()[]{}|\\"
_GO_ESCAPES = {ord(ch): "\\" + ch for ch in _GO_SPECIALS}


def go_literal(term):
    """`term` as a literal for Vale's (Go) regular expressions. Spaces stay as they are."""
    return term.translate(_GO_ESCAPES)


def split_sections(text):
    """Bodies of '## <one-word>' sections, keyed by that word. Any other heading closes one."""
    bodies, open_slug = {}, None
    for line in text.splitlines():
        if line.startswith("#"):
            words = line[3:].split() if line.startswith("## ") else []
            open_slug = words[0] if len(words) == 1 else None
            if open_slug:
                bodies[open_slug] = []
        elif open_slug:
            bodies[open_slug].append(line)
    return bodies


def _table_pairs(slug, body):
    pairs = {}
    for line in body:
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 2:
            raise CheckError("word-lists.md '## %s': a table row needs exactly two cells: %s"
                             % (slug, line))
        wordy, plain = cells
        if wordy.lower() != "wordy":  # the header row
            pairs[wordy] = plain
    if not pairs:
        raise CheckError("word-lists.md '## %s': its table is empty" % slug)
    return pairs


def parse_word_lists(text):
    """{slug: [terms]} for list sections and {slug: {wordy: plain}} for table sections. A
    missing section or marker raises CheckError: better to say so than to check less in silence."""
    bodies = split_sections(text)
    out = {}
    for slug in LIST_SECTIONS:
        body = bodies.get(slug)
        if body is None:
            raise CheckError("word-lists.md has no '## %s' section" % slug)
        kind = None
        for line in body:
            marker = KIND_COMMENT.match(line.strip())
            if marker:
                kind = marker.group(1)
                break
        if kind == "table":
            out[slug] = _table_pairs(slug, body)
        elif kind == "list":
            terms = [m.group(1) for m in (BULLET_TERM.match(line) for line in body) if m]
            if not terms:
                raise CheckError("word-lists.md '## %s': no '- `term`' bullets found" % slug)
            out[slug] = terms
        else:
            raise CheckError("word-lists.md '## %s': needs a <!-- kind: list|table --> line" % slug)
    return out


def rule_name(slug):
    return "WordList" + "".join(part.capitalize() for part in slug.split("-"))


def vale_rules_from(lists):
    """One generated Vale rule (name -> YAML text) per word-list section."""
    generated = {}
    for slug, entries in lists.items():
        if isinstance(entries, dict):
            note = "'%%s' could become '%%s'; word-lists.md \"%s\" says when to change it." % slug
            body = ["extends: substitution", "message: " + json.dumps(note),
                    "level: suggestion", "ignorecase: true", "swap:"]
            body.extend("  %s: %s" % (json.dumps(go_literal(k)), json.dumps(v))
                        for k, v in entries.items())
        else:
            note = "'%%s' is on the word-lists.md \"%s\" list; apply that section's rule." % slug
            body = ["extends: existence", "message: " + json.dumps(note),
                    "level: suggestion", "ignorecase: true", "tokens:"]
            body.extend("  - " + json.dumps(go_literal(t)) for t in entries)
        generated[rule_name(slug)] = "\n".join(body) + "\n"
    return generated


# --- Vale -------------------------------------------------------------------------------------

def locate_vale(layout):
    """The pinned copy install.sh leaves in ~/.local/bin wins over whatever PATH offers."""
    pinned = layout.home / ".local" / "bin" / "vale"
    if pinned.is_file():
        return str(pinned)
    return shutil.which("vale")


def _prepare_styles(layout, root, generated):
    styles = root / "styles"
    own = styles / OWN_STYLE
    own.mkdir(parents=True)
    (styles / "Deslop").symlink_to(layout.deslop, target_is_directory=True)
    for rule in sorted((layout.vale_dir / OWN_STYLE).glob("*.yml")):
        shutil.copyfile(rule, own / rule.name)
    for name, yaml in generated.items():
        (own / (name + ".yml")).write_text(yaml, encoding="utf-8")
    ini = root / ".vale.ini"
    shutil.copyfile(layout.vale_dir / "vale.ini", ini)
    return ini


def _alerts(stdout):
    try:
        report = json.loads(stdout or "{}")
        return [{"line": a["Line"], "column": a["Span"][0], "end": a["Span"][1],
                 "rule": a["Check"], "level": a["Severity"], "quote": a["Match"],
                 "message": a["Message"]}
                for per_file in report.values() for a in per_file]
    except (ValueError, KeyError, TypeError, AttributeError, IndexError) as err:
        raise CheckError("could not read Vale's JSON output: %s" % err) from err


def _without_shadowed(alerts):
    """A pack alert that overlaps a word-list alert on its line is the same problem twice; keep
    the word-list one. Plain's own span rules never hide anything."""
    word_list = OWN_STYLE + ".WordList"
    claimed = [(a["line"], a["column"], a["end"]) for a in alerts
               if a["rule"].startswith(word_list)]
    kept = []
    for a in alerts:
        if not a["rule"].startswith(OWN_STYLE + "."):
            if any(line == a["line"] and lo <= a["end"] and a["column"] <= hi
                   for line, lo, hi in claimed):
                continue
        kept.append(a)
    return kept


def lint(text, vale, layout, word_lists=None):
    """(findings, word-list status) for `text`."""
    if not layout.deslop.is_dir():
        raise NotInstalled("The Deslop style pack is missing from %s." % layout.deslop.parent)
    source = word_lists or layout.ref("word-lists.md")
    try:
        generated = vale_rules_from(parse_word_lists(read_text(source)))
        status = "loaded"
    except (CheckError, OSError, UnicodeError) as err:  # the rest of the rules still run
        generated, status = {}, "not loaded: %s" % err
    with tempfile.TemporaryDirectory(prefix="rtw-vale-") as scratch:
        root = Path(scratch)
        ini = _prepare_styles(layout, root, generated)
        target = root / "input.md"  # Markdown, so Vale leaves code spans, fences and URLs alone
        target.write_text(text, encoding="utf-8")
        proc = subprocess.run([vale, "--output=JSON", "--no-exit", "--no-global",
                               "--config=" + str(ini), str(target)],
                              cwd=root, capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            said = (proc.stderr or proc.stdout).strip() or "no output"
            raise CheckError("Vale failed (exit %d): %s" % (proc.returncode, said))
        alerts = _without_shadowed(_alerts(proc.stdout))
    for a in alerts:
        a.pop("end")
    alerts.sort(key=lambda a: (a["line"], a["column"], a["rule"]))
    return alerts, status


# --- What an edit must not lose ---------------------------------------------------------------

QUALIFIERS = "modal, negation, condition or quantifier word"
# Contractions go first: otherwise "can" would match the start of "can't".
_QUALIFIER_WORDS = (
    r"\w+n't", "not", "no", "none", "never", "cannot", "without",   # negation
    "must", "should", "shall", "may", "might", "will", "can",         # modality
    "if", "unless", "until", "when", "before", "after", "except",     # condition and order
    "only", "always", "every", "each", "all", "any", "at least", "at most",  # quantity
)
_VERSION_NUMBER = r"v?\d+(?:[.,:]\d+)*"
_UNIT = r"(?:%|[A-Za-z]{1,3}\b)?"
_TRACKER_ID = r"\b[A-Z][A-Z0-9]+-\d+\b"
_HASH_ID = r"(?<![\w&])#\d+\b"
_CONSTANT = r"\b[A-Z][A-Z0-9_]{3,}\b"

CLASSES = {
    "code": re.compile(r"`[^`\n]+`"),
    "url": re.compile(r"https?://[^\s)>\]]+"),
    # Not preceded by a word character or a dot, so "4.2" counts once, not as "2" too.
    "number": re.compile(r"(?<![\w.])" + _VERSION_NUMBER + _UNIT),
    "id": re.compile("|".join((_TRACKER_ID, _HASH_ID, _CONSTANT))),
    QUALIFIERS: re.compile(r"\b(?:" + "|".join(_QUALIFIER_WORDS) + r")\b", re.IGNORECASE),
    "heading": re.compile(r"^#{1,6} .*$", re.MULTILINE),
    "table row": re.compile(r"^\|.*$", re.MULTILINE),
}


def inventory(text):
    """Counter of matches per class, after turning curly apostrophes straight."""
    text = text.replace("’", "'")
    tally = {}
    for name, pattern in CLASSES.items():
        hits = pattern.findall(text)
        tally[name] = Counter(h.lower() for h in hits) if name == QUALIFIERS else Counter(hits)
    return tally


def lost_items(original, edited):
    """{class: [{text, count}]} for each protected item the edit holds fewer of."""
    before, after = inventory(original), inventory(edited)
    report = {}
    for name in CLASSES:
        gone = before[name] - after[name]
        if gone:
            report[name] = [{"text": key, "count": gone[key]} for key in sorted(gone)]
    return report


# --- Detail blocks and heading tags -----------------------------------------------------------

def tag_headings(lines, label, start=1):
    """Append `  [label:N]` to every heading line that is not inside a code fence."""
    result, in_fence = [], False
    for number, line in enumerate(lines, start):
        if opens_or_closes_fence(line):
            in_fence = not in_fence
        if not in_fence and heading_depth(line):
            line = "%s  [%s:%d]" % (line, label, number)
        result.append(line)
    return result


def strip_details(text, label):
    """`text` with headings tagged and every detail block cut out. Marks that do not pair up raise
    CheckError, so a missing close cannot quietly eat the rest of the file."""
    kept, start = [], 0
    for number, line in enumerate(tag_headings(text.splitlines(), label), 1):
        mark = line.strip()
        if mark == DETAIL_START:
            if start:
                raise CheckError("%s:%d: a detail block opens inside the one opened on line %d"
                                 % (label, number, start))
            start = number
        elif mark == DETAIL_END:
            if not start:
                raise CheckError("%s:%d: a detail block closes without being opened"
                                 % (label, number))
            start = 0
        elif not start:
            kept.append(line)
    if start:
        raise CheckError("%s:%d: this detail block has no closing mark" % (label, start))
    return tidy(kept)


# --- Humanizer --------------------------------------------------------------------------------

# Sections humanizer-overrides.md sets aside; any heading below them goes too.
SET_ASIDE = ("### Voice", "### What to return", "## Source")
EXAMPLE_START = re.compile(r"^\*\*(?:Before|After)\b[^*]*\*\*")
PATTERN_TITLE = re.compile(r"^### (\d+)\. (.+?)\s*$", re.MULTILINE)
OVERRIDE_LINE = re.compile(r"^- §(\d+) ([^:]+):", re.MULTILINE)


def _cached(folder, name):
    path = folder / name
    if not path.is_file():
        return "unknown"
    return path.read_text().strip()


def humanizer_info(layout):
    """Commit, fetch time and pattern count of the cached Humanizer, plus every override whose
    numbered pattern no longer carries the same title."""
    skill = layout.humanizer / "SKILL.md"
    if not skill.is_file():
        raise NotInstalled("Humanizer is missing from %s." % layout.humanizer)
    titles = {num: title for num, title in PATTERN_TITLE.findall(read_text(skill))}
    stale = ["§%s %s" % (num, title)
             for num, title in OVERRIDE_LINE.findall(read_text(layout.ref("humanizer-overrides.md")))
             if titles.get(num) != title.strip()]
    return {"path": str(skill), "commit": _cached(layout.humanizer, "SHA"),
            "fetched": _cached(layout.humanizer, "DATE"), "patterns": len(titles),
            "stale_overrides": stale}


def filter_humanizer(text):
    """Humanizer's SKILL.md without frontmatter, Before/After examples or the SET_ASIDE
    sections. Anything the file does not contain is simply not removed."""
    lines = text.splitlines()
    offset = 1
    if lines and lines[0].strip() == "---":
        close = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), 0)
        lines = lines[close + 1:]
        offset = close + 2
    out = []
    dropping_below = 0    # heading level of a set-aside section, while inside it
    in_example = False
    for line in tag_headings(lines, "humanizer SKILL.md", offset):
        level = heading_depth(line)
        if level:
            if dropping_below and level > dropping_below:
                continue
            dropping_below = level if line.startswith(SET_ASIDE) else 0
            if in_example:
                out.append("")
                in_example = False
        if dropping_below:
            continue
        if EXAMPLE_START.match(line):
            in_example = True
            continue
        if in_example:
            if not line.strip() or line.startswith(">"):
                continue
            out.append("")
            in_example = False
        out.append(line)
    return tidy(out)


# --- kinds.md and the homes it names ----------------------------------------------------------

ROW_SLUG = re.compile(r"\|\s*`([a-z-]+)`")
HOME_OR_QUOTE = re.compile(r'`([^`]+\.md)`|"([^"]+)"')
LOCAL_SECTION = re.compile(r'"([^"]+)" below')
TAG_SUFFIX = re.compile(r"\s+\[[^\]]+:\d+\]$")


def section_body(text, heading):
    """What follows the first line starting with `heading`, up to the next heading of that level
    or above (code fences respected), bold marks removed. None when the heading is absent."""
    level = heading_depth(heading)
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith(heading)), None)
    if start is None:
        return None
    body, in_fence = [], False
    for line in lines[start + 1:]:
        if opens_or_closes_fence(line):
            in_fence = not in_fence
        depth = heading_depth(line)
        if depth and not in_fence and depth <= level:
            break
        body.append(line)
    return "\n".join(body).replace("**", "")


def lead_paragraph(text, lead):
    for chunk in re.split(r"\n\s*\n", text):
        plain = chunk.replace("**", "")
        if lead in plain:
            return plain
    return None


def last_cell(line):
    return line.strip().strip("|").split("|")[-1]


def homes_in(cell):
    """[(file, [quoted parts after it])] in the order the cell names them."""
    homes = []
    for token in HOME_OR_QUOTE.finditer(cell):
        if token.group(1):
            homes.append((token.group(1), []))
        elif homes:
            homes[-1][1].append(token.group(2))
    return homes


class KindTable:
    """The parsed kinds.md, resolving homes against `refs`."""

    def __init__(self, text, refs):
        self.text, self.refs = text, Path(refs)
        self.rows = {}
        for line in text.splitlines():
            found = ROW_SLUG.match(line)
            if found:
                self.rows[found.group(1)] = last_cell(line)

    def _home_file(self, name):
        return (self.refs / name).resolve()

    def missing(self):
        """Files a rules cell names that are absent, and quoted headings or leads after a file
        that it lacks. A file under a sibling skill that is itself absent reads "skill not
        installed". Quotes that come before any file are not checked here."""
        problems = []
        for line in self.text.splitlines():
            if not line.startswith("|") or line.startswith("|---"):
                continue
            for name, parts in homes_in(last_cell(line)):
                target = self._home_file(name)
                if not target.is_file():
                    sibling = self.refs.joinpath(*Path(name).parts[:3]).resolve()
                    why = "file not found" if sibling.is_dir() else "skill not installed"
                    problems.append("%s: %s" % (name, why))
                    continue
                body = read_text(target)
                for part in parts:
                    if part.startswith("#"):
                        present = section_body(body, part) is not None
                    else:
                        present = part in body.replace("**", "")
                    if not present:
                        problems.append('%s: "%s"' % (name, part))
        return problems

    def _render_home(self, name, parts):
        target = self._home_file(name)
        if not target.is_file():
            return ["", "# %s: not found" % name]
        text = strip_details(read_text(target), name)
        if not parts:
            return ["", "# " + name, "", text]
        pieces = []
        for part in parts:
            if part.startswith("#"):
                body = section_body(text, part)
                body = None if body is None else part + "\n" + body
            else:
                body = lead_paragraph(text, part)
            pieces.extend(["", "# %s %s" % (name, part), "(not found)" if body is None else body])
        return pieces

    def rules_for(self, slugs):
        """kinds.md cut down to the chosen rows and the local sections they point to, followed by
        the parts of each home those rows name (a home without parts comes in whole)."""
        unknown = [s for s in slugs if s not in self.rows]
        if unknown:
            raise CheckError("unknown kind %s; valid kinds: %s"
                             % (", ".join(unknown), ", ".join(self.rows)))
        chosen = [self.rows[s] for s in slugs]
        wanted = {t for cell in chosen for t in LOCAL_SECTION.findall(cell)}
        claimed = {t for cell in self.rows.values() for t in LOCAL_SECTION.findall(cell)}
        out, hide = [], False
        for line in strip_details(self.text, "kinds.md").splitlines():
            if line.startswith("## "):
                title = TAG_SUFFIX.sub("", line[3:])
                hide = title in claimed and title not in wanted
            if hide:
                continue
            row = ROW_SLUG.match(line)
            if row and row.group(1) not in slugs:
                continue
            out.append(line)
        for cell in chosen:
            for name, parts in homes_in(cell):
                out.extend(self._render_home(name, parts))
        return tidy(out)


def kind_table(layout):
    return KindTable(read_text(layout.ref("kinds.md")), layout.refs)


# --- One review's rules -----------------------------------------------------------------------

def assemble(layout, slugs):
    """(rules text, whether Humanizer was included)."""
    table = kind_table(layout)
    absent = ", ".join(table.missing()) or "none"
    patterns = None
    try:
        info = humanizer_info(layout)
        summary = "Humanizer %s (%d patterns, fetched %s); stale overrides: %s" % (
            info["commit"], info["patterns"], info["fetched"],
            ", ".join(info["stale_overrides"]) or "none")
        patterns = filter_humanizer(read_text(layout.humanizer / "SKILL.md"))
    except NotInstalled as err:
        summary = "Humanizer not loaded: %s" % err
    parts = [
        "# Review rules: " + ", ".join(slugs),
        "Sources: %s; kind homes not found: %s. The [file:N] after a heading points at "
        "that rule's examples." % (summary, absent),
        table.rules_for(slugs),
        strip_details(read_text(layout.ref("general-rules.md")), "general-rules.md"),
    ]
    if patterns is not None:
        parts.append(patterns)
        parts.append(strip_details(read_text(layout.ref("humanizer-overrides.md")),
                                   "humanizer-overrides.md"))
    return "\n\n".join(p.strip() for p in parts) + "\n", patterns is not None


def store(layout, slugs, rules):
    """Write `rules` to a content-addressed file in the cache and return its path. Hosts read a
    file whole more reliably than a long stdout that they may truncate."""
    stamp = hashlib.sha256(rules.encode("utf-8")).hexdigest()[:12]
    target = layout.cache / "rules" / ("%s-%s.md" % ("+".join(slugs), stamp))
    if not target.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.parent / ("%s.%d.part" % (target.name, os.getpid()))
        temp.write_text(rules, encoding="utf-8")
        os.replace(temp, target)
    return target


# --- Commands ---------------------------------------------------------------------------------

def cmd_kind(layout, slugs):
    rules, with_humanizer = assemble(layout, slugs)
    path = store(layout, slugs, rules)
    head = rules.split("\n\n", 2)
    print(head[0])
    print()
    print(head[1])
    print()
    print("Rules file: %s" % path)
    print("Read the whole file before reviewing (%d lines, %d words): every rule, trigger and "
          "exception for this pass, without the examples." % (rules.count("\n"), len(rules.split())))
    print()
    return with_humanizer


def cmd_against(edited_path, edited_text, original_path):
    original_path = original_path.resolve()
    original = original_path.read_bytes().decode("utf-8")
    payload = {"file": str(edited_path), "against": str(original_path),
               "lost": lost_items(original, edited_text),
               "note": "Judge each item: something only restated may go; a qualifier, number "
                       "or code span that carried meaning must come back."}
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def cmd_lint(layout, path, raw, text):
    vale = locate_vale(layout)
    if not vale:
        raise NotInstalled("Vale is missing.")
    engine = subprocess.run([vale, "--version"], capture_output=True, text=True,
                            timeout=30).stdout.strip()
    findings, lists = lint(text, vale, layout)
    payload = {"file": str(path), "engine": engine, "vale": vale,
               "source_sha256": hashlib.sha256(raw).hexdigest(), "word_lists": lists,
               "findings": findings,
               "note": "Candidates only: confirm each quote and what it means technically, in "
                       "its passage, before reporting it."}
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def cmd_sources(layout):
    try:
        info = humanizer_info(layout)
    except NotInstalled as err:
        info = {"loaded": False, "reason": str(err)}
    print(json.dumps({"humanizer": info, "kind_homes_missing": kind_table(layout).missing()},
                     indent=2, ensure_ascii=False))
    if info.get("loaded") is False:
        raise NotInstalled(info["reason"])


def options():
    cli = argparse.ArgumentParser(
        prog="check_prose.py",
        description="Vale candidates, edit-preservation checks and rule assembly for the "
                    "refining-technical-writing skill. Exit 0 ran, 2 error, 3 not installed.")
    cli.add_argument("file", nargs="?", type=Path, help="Markdown or plain-text file")
    cli.add_argument("--against", metavar="ORIGINAL", type=Path,
                     help="report protected items FILE has lost compared with ORIGINAL")
    cli.add_argument("--sources", action="store_true",
                     help="report the cached Humanizer and missing kind homes")
    cli.add_argument("--kind", metavar="SLUG[,SLUG]",
                     help="write this pass's rules to the cache and print the path")
    return cli


def run(argv=None, layout=None):
    cli = options()
    opts = cli.parse_args(argv)
    layout = layout or Layout.from_environment()
    humanizer_ok = True
    try:
        if opts.kind and not opts.against:
            slugs = [s.strip() for s in opts.kind.split(",") if s.strip()]
            humanizer_ok = cmd_kind(layout, slugs)
            if opts.file is None:
                if not humanizer_ok:
                    raise NotInstalled("Humanizer is missing from %s." % layout.humanizer)
                return 0
            print("# Candidates")
            print()
        if opts.sources:
            cmd_sources(layout)
            return 0
        if opts.file is None:
            cli.error("pass FILE, --sources or --kind")
        path = opts.file.resolve()
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        if opts.against:
            cmd_against(path, text, opts.against)
            return 0
        cmd_lint(layout, path, raw, text)
        if not humanizer_ok:
            raise NotInstalled("Humanizer is missing from %s." % layout.humanizer)
        return 0
    except NotInstalled as err:
        sys.stderr.write("check_prose: %s Install it with: bash %s\n" % (err, layout.install))
        return 3
    except (CheckError, OSError, UnicodeError, subprocess.TimeoutExpired) as err:
        sys.stderr.write("check_prose: %s\n" % err)
        return 2


if __name__ == "__main__":
    raise SystemExit(run())
