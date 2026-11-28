#!/usr/bin/env python3
"""Print one bounded start-of-session load for a project, built from its context-manifest.yaml.

  load_context.py [--root DIR] [--manifest FILE] [--date YYYY-MM-DD] [--max-chars N] [--no-git]

The load is a handful of sections, each held to its own word budget:

  Work plan      the plan's opening block (up to its second "## " heading), its "Next up" and
                 "Blocked" sections, and its first open checklist items ("- [ ]", "- [~]")
  Decisions      the decisions-in-force map (IN-FORCE.md in the decisions layer) when its
                 "## In force" section lists a decision, with the map's DRAFT line; otherwise one
                 line per ADR: number, status, title
  Work tracker   the titles of the newest entries and the body of the newest one
  Open reviews   file names under .agent-bridge/active/
  Repository     current branch, uncommitted paths, stashes, worktrees, and the local branches
                 holding commits the default branch lacks (each proved with merge-base)
  Freshness      a warning when the newest tracker entry or the plan's "As of" date is 8+ days old
  Not loaded     every other layer with its size, so the session knows what a grep can reach

HTML comments are dropped before anything is measured. The whole printout never exceeds
--max-chars (default 28,000). When it would, it is cut at a line and ends with a note that
names the section cut short, every section dropped, and keeps the map's DRAFT warning.

Without a manifest the shipped default layer paths are used. Read-only: git runs with optional
locks off and only read commands. Standard library only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path
import re
import subprocess
import sys


MAX_CHARS = 28_000
FOOTER_ROOM = 1_200
TOP_WORDS = 400        # work plan opening block
PLAN_SECTION_WORDS = 250  # each of "Next up" / "Blocked"
OPEN_ITEMS = 5
MAP_WORDS = 800        # decisions map, or the ADR title list
TITLE_WORDS = 150      # tracker titles
BODY_WORDS = 300       # newest tracker body
TRACKER_ENTRIES = 3
REVIEW_NAMES = 20
BRANCH_ROWS = 15
STALE_DAYS = 7
MAP_NAME = "IN-FORCE.md"

# Mirrors config/context-manifest.example.yaml; used when no manifest exists.
DEFAULT_LAYERS = [
    {"id": "decisions", "path": "docs/decisions/"},
    {"id": "strategy", "path": "docs/strategy/"},
    {"id": "architecture", "path": "docs/architecture/"},
    {"id": "rules", "path": "rules/"},
    {"id": "ai-tooling", "path": "skills/"},
    {"id": "open-questions", "path": "docs/open_questions.md"},
    {"id": "work-plan", "path": "work_tracker/work_plan.md"},
    {"id": "backlog", "path": "work_tracker/backlog.md"},
    {"id": "orientation", "path": "AGENTS.md"},
    {"id": "work-tracker", "path": "work_tracker/"},
]
LOADED_LAYERS = {"work-plan", "decisions", "work-tracker"}
LAYER_NOTES = {
    "orientation": "auto-loaded by the host; not re-read",
    "backlog": "parking lot; never part of a resume",
}

ADR_RE = re.compile(r"^(?P<num>\d{3,4})-[A-Za-z0-9][\w.-]*\.md$")
STATUS_RE = re.compile(r"^\s*(?:[-*]\s+)?\*\*Status:\*\*\s*(?P<value>[^;\n]+)")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
OPEN_ITEM_RE = re.compile(r"^\s*[-*] \[[ ~]\] .+$", re.M)
LIST_LINE_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+\S", re.M)
AS_OF_RE = re.compile(r"As of:?\**:?\s*(\d{4}-\d{2}-\d{2})")
DAY_RE = re.compile(r"^(?P<weekday>[a-z]+)_(?P<m>\d{1,2})-(?P<d>\d{1,2})$")
TIMED_RE = re.compile(r"^## \d{1,2}:\d{2}\b.*$", re.M)
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


# ---------------------------------------------------------------- manifest

def _uncomment(line: str) -> str:
    quote = None
    for i, ch in enumerate(line):
        if ch in "\"'":
            quote = None if quote == ch else (quote or ch)
        elif ch == "#" and quote is None and (i == 0 or line[i - 1].isspace()):
            return line[:i]
    return line


def _scalar(value: str):
    value = value.strip()
    if value in ("", "null", "~"):
        return None
    if value.startswith("[") and value.endswith("]"):
        return [_scalar(v) for v in value[1:-1].split(",") if v.strip()]
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_manifest(text: str) -> tuple[dict, list[dict]]:
    """The `project:` mapping and the `layers:` list; enough YAML for the manifest's shape."""
    project: dict = {}
    layers: list[dict] = []
    top = None
    current = None
    for raw in text.splitlines():
        line = _uncomment(raw).rstrip()
        if not line.strip():
            continue
        if not line[0].isspace() and not line.startswith("-"):
            top = line.split(":", 1)[0].strip()
            current = None
            continue
        body = line.strip()
        if top == "layers":
            if body.startswith("- "):
                current = {}
                layers.append(current)
                body = body[2:].strip()
            if current is not None and ":" in body:
                key, value = body.split(":", 1)
                current[key.strip()] = _scalar(value)
        elif top == "project" and ":" in body:
            key, value = body.split(":", 1)
            project[key.strip()] = _scalar(value)
    return project, layers


def load_manifest(root: Path, manifest: Path | None) -> tuple[dict, list[dict], str]:
    path = manifest or root / "context-manifest.yaml"
    if path.is_file():
        project, layers = parse_manifest(path.read_text(encoding="utf-8"))
        return project, [layer for layer in layers if layer.get("id") and layer.get("path")], str(path.name)
    return {}, DEFAULT_LAYERS, "no manifest; shipped defaults"


# ---------------------------------------------------------------- text helpers

def read(path: Path) -> str:
    try:
        return COMMENT_RE.sub("", path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return ""


def cap_words(text: str, budget: int, note: str) -> str:
    out, used = [], 0
    for line in text.splitlines():
        words = line.split()
        if used + len(words) > budget:
            out.append(" ".join(words[: budget - used]) + f" … [{note}]")
            return "\n".join(out).strip()
        out.append(line)
        used += len(words)
    return "\n".join(out).strip()


def squeeze(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def top_block(text: str) -> str:
    out, seen = [], 0
    for line in text.splitlines():
        if line.startswith("## "):
            seen += 1
            if seen == 2:
                break
        out.append(line)
    return "\n".join(out)


def section(text: str, name: str) -> str | None:
    match = re.search(rf"^## [^\n]*{re.escape(name)}[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S | re.I)
    return match.group(1).strip() if match else None


def words_in(path: Path) -> int:
    return len(read(path).split())


# ---------------------------------------------------------------- sections

def plan_section(root: Path, layers: dict) -> str:
    rel = layers.get("work-plan")
    if not rel:
        return "(no work-plan layer declared)"
    path = root / rel
    if not path.is_file():
        return f"(no work plan at {rel})"
    text = read(path)
    note = f"cut; grep {rel} for the rest"
    parts = [f"From {rel}:", cap_words(squeeze(top_block(text)), TOP_WORDS, note)]
    shown = parts[-1]
    for name in ("Next up", "Blocked"):
        body = section(text, name)
        if body and body not in shown:
            parts.append(f"### {name}\n" + cap_words(squeeze(body), PLAN_SECTION_WORDS, note))
            shown += parts[-1]
    first_heading = re.search(r"^## ", text, re.M)
    items = OPEN_ITEM_RE.findall(text[first_heading.start():] if first_heading else "")
    fresh = [item.strip() for item in items if item.strip() not in shown][:OPEN_ITEMS]
    if fresh:
        parts.append("### First open items\n" + "\n".join(fresh))
    return "\n\n".join(parts)


def adr_records(directory: Path) -> list[dict]:
    records = []
    for path in sorted(directory.iterdir()):
        match = ADR_RE.match(path.name)
        if not match or not path.is_file():
            continue
        lines = read(path).splitlines()[:40]
        title = next((re.sub(r"^#\s+(?:ADR-\d+:\s*)?", "", l).strip() for l in lines if l.startswith("# ")), path.name)
        status = next((m.group("value").strip() for l in lines if (m := STATUS_RE.match(l))), "no Status line")
        records.append({"num": match.group("num"), "file": path.name, "title": title, "status": status})
    return records


def decisions_section(root: Path, layers: dict) -> tuple[str, str]:
    """The section text and the map's DRAFT line ('' when none)."""
    rel = layers.get("decisions")
    if not rel or not (root / rel).is_dir():
        return "(no decisions layer on disk)", ""
    directory = root / rel
    map_path = directory / MAP_NAME
    draft = ""
    if map_path.is_file():
        raw = map_path.read_text(encoding="utf-8", errors="replace")
        draft = next((l.strip() for l in raw.splitlines()[:12] if "DRAFT" in l), "")
        text = COMMENT_RE.sub("", raw)
        in_force = section(text, "In force") or ""
        if LIST_LINE_RE.search(in_force):
            unclear = section(text, "Unclear") or ""
            body = in_force + ("\n\n### Unclear\n" + unclear if LIST_LINE_RE.search(unclear) else "")
            head = f"Decisions in force, from {rel}{MAP_NAME}. Open an ADR only for the decision at hand."
            if draft:
                head += f"\n{draft}"
            return head + "\n\n" + cap_words(squeeze(body), MAP_WORDS, f"cut; open {rel}{MAP_NAME}"), draft
    records = adr_records(directory)
    if not records:
        return f"(no ADR files in {rel})", draft
    lines = [f"- ADR-{r['num']} ({r['status']}): {r['title']}" for r in records]
    head = (f"No decisions map yet; ADRs in {rel} by title. Open an ADR only for the decision at hand; "
            f"a Proposed one is pending sign-off.")
    if draft:
        head += f"\n{draft}"
    return head + "\n\n" + cap_words("\n".join(lines), MAP_WORDS, f"cut; {len(records)} ADRs in {rel}"), draft


def entry_date(day_name: str, today: dt.date) -> dt.date | None:
    """A day folder ('thursday_7-02') carries no year; take the latest year whose date is not after
    today and, when possible, whose weekday matches the folder's name."""
    match = DAY_RE.match(day_name)
    if not match:
        return None
    month, day = int(match["m"]), int(match["d"])
    fallback = None
    for year in range(today.year, today.year - 8, -1):
        try:
            candidate = dt.date(year, month, day)
        except ValueError:
            continue
        if candidate > today:
            continue
        if WEEKDAYS[candidate.weekday()] == match["weekday"]:
            return candidate
        fallback = fallback or candidate
    return fallback


def tracker_entries(root: Path, rel: str, today: dt.date) -> list[tuple[dt.date, Path]]:
    base = root / rel
    found = []
    for entry in base.glob("*/*/entry.md"):
        when = entry_date(entry.parent.name, today)
        if when:
            found.append((when, entry))
    return sorted(found, key=lambda item: (item[0], str(item[1])), reverse=True)


def entry_title(text: str, fallback: str) -> str:
    return next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), fallback)


def tracker_section(root: Path, layers: dict, today: dt.date) -> tuple[str, dt.date | None]:
    rel = layers.get("work-tracker")
    if not rel or not (root / rel).is_dir():
        return "(no work-tracker layer on disk)", None
    entries = tracker_entries(root, rel, today)
    if not entries:
        return f"(no <week>/<day>/entry.md entries under {rel})", None
    note = f"cut; grep {rel} for the rest"
    titles = []
    for when, path in entries[:TRACKER_ENTRIES]:
        text = read(path)
        titles.append(f"- {when.isoformat()} {path.relative_to(root)}: {entry_title(text, path.parent.name)}")
    newest_date, newest = entries[0]
    text = read(newest)
    timed = list(TIMED_RE.finditer(text))
    for match in timed:
        titles.append(f"  - later that day: {match.group(0)[3:].strip()}")
    if timed:
        body = text[timed[-1].start():]
    else:
        body = "\n".join(l for l in text.splitlines() if not l.startswith("# "))
    out = (cap_words("\n".join(titles), TITLE_WORDS, note) + "\n\n### Newest entry body\n"
           + cap_words(squeeze(body), BODY_WORDS, note))
    return out, newest_date


def reviews_section(root: Path) -> str | None:
    active = root / ".agent-bridge" / "active"
    if not active.is_dir():
        return None
    names = sorted(p.name for p in active.iterdir() if not p.name.startswith("."))
    if not names:
        return "none open"
    shown = names[:REVIEW_NAMES]
    more = f"\n(+{len(names) - len(shown)} more; list .agent-bridge/active/)" if len(names) > len(shown) else ""
    return ("Pending items, not context: get each one's state from the cross-review helper's "
            "`status`, never from the transcript.\n" + "\n".join(f"- {n}" for n in shown) + more)


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    return subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, env=env)


def default_branch(root: Path) -> str | None:
    head = git(root, "symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD")
    if head.returncode == 0 and head.stdout.strip():
        return head.stdout.strip()
    for name in ("main", "master", "trunk"):
        if git(root, "show-ref", "-q", "--verify", f"refs/heads/{name}").returncode == 0:
            return name
    return None


def repo_section(root: Path) -> str | None:
    probe = git(root, "rev-parse", "--is-inside-work-tree")
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        return None
    branch = git(root, "symbolic-ref", "-q", "--short", "HEAD").stdout.strip()
    if not branch:
        branch = "detached at " + git(root, "rev-parse", "--short", "HEAD").stdout.strip()
    dirty = [l for l in git(root, "status", "--porcelain").stdout.splitlines() if l.strip()]
    stashes = [l for l in git(root, "stash", "list").stdout.splitlines() if l.strip()]
    worktrees = [l[9:] for l in git(root, "worktree", "list", "--porcelain").stdout.splitlines()
                 if l.startswith("worktree ")]
    base = default_branch(root)
    lines = [f"- On `{branch}`; {len(dirty)} uncommitted path(s); {len(stashes)} stash(es)"
             + (f"; default branch `{base}`" if base else "; default branch unknown")]
    if len(worktrees) > 1:
        lines.append("- Worktrees: " + ", ".join(worktrees))
    refs = git(root, "for-each-ref", "--format=%(refname:short)\t%(committerdate:short)", "refs/heads")
    unmerged, merged = [], 0
    for row in refs.stdout.splitlines():
        name, _, date = row.partition("\t")
        if not name or name == base or name == branch:
            continue
        if base and git(root, "merge-base", "--is-ancestor", name, base).returncode == 0:
            merged += 1
            continue
        unmerged.append(f"  - `{name}` (last commit {date or 'unknown'})")
    if unmerged:
        label = f"not in `{base}`" if base else "merge state unproven (no default branch found)"
        lines.append(f"- Local branches {label}:")
        lines.extend(unmerged[:BRANCH_ROWS])
        if len(unmerged) > BRANCH_ROWS:
            lines.append(f"  - (+{len(unmerged) - BRANCH_ROWS} more; `git branch --no-merged {base or ''}`)")
    if merged:
        lines.append(f"- {merged} other local branch(es) fully contained in `{base}` (merge-base proved)")
    return "\n".join(lines)


def freshness_section(root: Path, layers: dict, today: dt.date, newest: dt.date | None) -> str | None:
    notes = []
    if newest and (today - newest).days > STALE_DAYS:
        notes.append(f"- Newest tracker entry is {newest.isoformat()} ({(today - newest).days} days old).")
    plan = layers.get("work-plan")
    if plan and (root / plan).is_file():
        match = AS_OF_RE.search(read(root / plan))
        if match:
            try:
                as_of = dt.date.fromisoformat(match.group(1))
            except ValueError:
                notes.append(f"- Work plan has an unreadable date (As of: {match.group(1)}); its age is unknown.")
                as_of = None
            if as_of and (today - as_of).days > STALE_DAYS:
                notes.append(f"- Work plan is as of {as_of.isoformat()} ({(today - as_of).days} days old).")
    if not notes:
        return None
    return "\n".join(notes) + "\nVerify against `git log` and the files before relying on it; update-context fixes it."


def size_of(path: Path) -> str:
    if path.is_file():
        return f"{words_in(path):,} words"
    files = [p for p in path.rglob("*.md") if "archive" not in p.relative_to(path).parts]
    return f"{len(files)} .md files, {sum(words_in(p) for p in files):,} words"


def not_loaded_section(root: Path, layers: list[dict]) -> str:
    lines = []
    for layer in layers:
        if layer["id"] in LOADED_LAYERS:
            continue
        path = root / layer["path"]
        if not path.exists():
            lines.append(f"- {layer['id']}: {layer['path']} (absent)")
            continue
        extra = LAYER_NOTES.get(layer["id"])
        lines.append(f"- {layer['id']}: {layer['path']} ({size_of(path)}" + (f"; {extra})" if extra else ")"))
    return "Reach these by headings and grep at need (`grep -n '<term>' <path>`), never whole:\n" + "\n".join(lines)


# ---------------------------------------------------------------- assembly

def assemble(sections: list[tuple[str, str]], limit: int, draft: str) -> str:
    text = "\n\n".join(f"## {name}\n{body}" if name else body for name, body in sections)
    if len(text) <= limit:
        return text
    room = min(FOOTER_ROOM, max(limit // 3, 200))
    cut = text.rfind("\n", 0, max(limit - room, 0))
    cut = cut if cut > 0 else max(limit - room, 0)
    kept, dropped = text[:cut], text[cut:]
    short = [l[3:] for l in kept.splitlines() if l.startswith("## ")][-1:]
    lost = [l[3:] for l in dropped.splitlines() if l.startswith("## ")]
    footer = (f"\n\n… [load cut at {limit:,} characters. Cut short: {'; '.join(short) or 'none'}. "
              f"Sections dropped: {'; '.join(lost) or 'none'}."
              + (f" Kept warning: {draft}" if draft else "") + " Grep the layers for the rest.]")
    footer = footer[: limit - len(kept)]
    return kept + footer


def build(root: Path, manifest: Path | None, today: dt.date, limit: int, use_git: bool) -> str:
    project, layer_list, source = load_manifest(root, manifest)
    layers = {layer["id"]: layer["path"] for layer in layer_list}
    name = project.get("name") or root.resolve().name
    decisions, draft = decisions_section(root, layers)
    tracker, newest = tracker_section(root, layers, today)
    sections: list[tuple[str, str]] = [
        ("", f"# Context load — {name} ({today.isoformat()}; layers: {source})\n"
             "This is the whole load. Everything else is a grep at need."),
    ]
    stale = freshness_section(root, layers, today, newest)
    if stale:
        sections.append(("Freshness", stale))
    sections += [("Work plan", plan_section(root, layers)), ("Decisions", decisions), ("Work tracker", tracker)]
    reviews = reviews_section(root)
    if reviews:
        sections.append(("Open cross-reviews", reviews))
    if use_git:
        repo = repo_section(root)
        if repo:
            sections.append(("Repository", repo))
    sections.append(("Not loaded", not_loaded_section(root, layer_list)))
    return assemble(sections, limit, draft)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".", help="project root (default: current directory)")
    parser.add_argument("--manifest", help="manifest path (default: <root>/context-manifest.yaml)")
    parser.add_argument("--date", help="today as YYYY-MM-DD (default: the system clock)")
    parser.add_argument("--max-chars", type=int, default=MAX_CHARS)
    parser.add_argument("--no-git", action="store_true", help="skip the Repository section")
    args = parser.parse_args(argv)
    root = Path(args.root)
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    try:
        today = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    except ValueError:
        print(f"error: invalid --date {args.date!r}; use YYYY-MM-DD", file=sys.stderr)
        return 2
    if args.max_chars < 200:
        print("error: --max-chars must be at least 200", file=sys.stderr)
        return 2
    manifest = Path(args.manifest) if args.manifest else None
    print(build(root, manifest, today, args.max_chars, not args.no_git))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
