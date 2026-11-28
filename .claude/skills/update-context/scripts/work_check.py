#!/usr/bin/env python3
"""Check, close and hand off work folders under the worker contract's layout rule.

The layout (``<work root>/work/<YYYY-MM-DD>-<workstream>/``), the record files
and the cite form ``(source: work/<id>/<path>)`` are defined in bozz-agents'
``agents/shared/reference/worker/work-folder.md`` ("The work folder and homes"). How this script reads
that rule is in ../references/work-folders.md.

  check   [common]                         read-only; FIX lines, exit 0
  close   <id> --session S [--dry-run] [common]
                                           refuse (REFUSE lines, exit 1) or move the
                                           folder to work/archive/<id>/ in one commit
  handoff <id> [common]                    OK, or one MISSING line per result that no
                                           home cites and HANDOFF.md does not name (exit 1)

  common: --root DIR (project root, default .)  --manifest FILE  --home PATH (repeatable:
          a file or folder the goal is about, scanned as a home besides the layers)

Homes are every manifest layer's Markdown plus the orientation files and each
--home, minus everything under <work root>/work/. Records (never cited, never
results): BRIEF.md, STATUS.md, HANDOFF.md, OWNER-STEP-<n>.md, and everything
under channel/, passes/ and scratch/. Every other file in a folder is a result.
Standard library only; git is used read-only except by ``close``.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


LARGE_BYTES = 1_000_000
STATE_LINES = 40
ID_PATTERN = r"\d{4}-\d{2}-\d{2}-[A-Za-z0-9][A-Za-z0-9._-]*"
ID_RE = re.compile(rf"^{ID_PATTERN}$")
RECORD_FILES = {"BRIEF.md", "STATUS.md", "HANDOFF.md"}
RECORD_DIRS = {"channel", "passes", "scratch"}
NEVER_COMMITTED = ("BRIEF.md", "STATUS.md", "channel")
OWNER_STEP_RE = re.compile(r"^OWNER-STEP-(\d+)\.md$")
LOOSE_RECORD_RE = re.compile(r"^(BRIEF|STATUS|HANDOFF)\.md$|^(MSG|DECISION|OWNER-STEP)-\d+(-result)?\.md$")
CITE_RE = re.compile(r"\(source:\s*([^)]*)\)")
LINK_RE = re.compile(r"\[[^\]]*\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+\"[^\"]*\")?\s*\)")
PLACEHOLDER_RE = re.compile(r"^<[^./>]*>$")
TMP_RE = re.compile(r"(?<![\w.~/-])/(?:private/)?tmp/[^\s)`'\"\]]+")
SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)
FENCE_RE = re.compile(r"^\s*(```|~~~)")
CODE_SPAN_RE = re.compile(r"`[^`\n]*`")
DEFAULT_LAYER_PATHS = ["docs/decisions/", "docs/strategy/", "docs/architecture/", "rules/", "skills/",
                       "docs/open_questions.md", "work_tracker/work_plan.md", "work_tracker/backlog.md",
                       "work_tracker/"]


# ---------------------------------------------------------------- manifest (same subset as context-up's loader)

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


def read_manifest(path: Path) -> tuple[list[str], dict[str, str]]:
    """(orientation files, layer id -> path)."""
    if not path.is_file():
        return ["AGENTS.md", "CLAUDE.md"], {"work-tracker": "work_tracker/", **{p: p for p in DEFAULT_LAYER_PATHS}}
    orientation: list[str] = []
    layers: dict[str, str] = {}
    top, current = None, None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = _uncomment(raw).rstrip()
        if not line.strip():
            continue
        if not line[0].isspace() and not line.startswith("-"):
            top, current = line.split(":", 1)[0].strip(), None
            continue
        body = line.strip()
        if top == "project" and body.startswith("orientation:"):
            value = _scalar(body.split(":", 1)[1])
            orientation = value if isinstance(value, list) else [value] if value else []
        elif top == "layers":
            if body.startswith("- "):
                current = {}
                body = body[2:].strip()
            if current is not None and ":" in body:
                key, value = body.split(":", 1)
                current[key.strip()] = _scalar(value)
                if current.get("id") and current.get("path"):
                    layers[current["id"]] = current["path"]
    return orientation, layers


# ---------------------------------------------------------------- the project model

class Project:
    def __init__(self, root: Path, manifest: Path | None, extra_homes: list[str]):
        self.root = root.resolve()
        orientation, layers = read_manifest(manifest or self.root / "context-manifest.yaml")
        self.work_root = self.root / layers.get("work-tracker", "work_tracker/")
        self.work = self.work_root / "work"
        self.archive = self.work / "archive"
        self.home_paths = [self.root / p for p in [*layers.values(), *orientation, *extra_homes] if p]

    def rel(self, path: Path) -> str:
        return path.resolve().relative_to(self.root).as_posix() if path.resolve().is_relative_to(self.root) else str(path)

    def homes(self) -> list[Path]:
        seen: dict[Path, None] = {}
        for base in self.home_paths:
            if base.is_file() and base.suffix == ".md":
                candidates = [base]
            elif base.is_dir():
                candidates = sorted(base.rglob("*.md"))
            else:
                continue
            for path in candidates:
                resolved = path.resolve()
                if resolved.is_relative_to(self.work.resolve()) or any(p.startswith(".") for p in path.relative_to(self.root).parts):
                    continue
                seen.setdefault(resolved, None)
        return list(seen)

    def open_folders(self) -> list[Path]:
        if not self.work.is_dir():
            return []
        return sorted(p for p in self.work.iterdir() if p.is_dir() and ID_RE.match(p.name))

    def folder(self, work_id: str) -> Path | None:
        for base in (self.work, self.archive):
            if (base / work_id).is_dir():
                return base / work_id
        return None


def prose_lines(path: Path):
    """(line number, text) for lines outside fenced code, with inline code spans blanked."""
    fenced = False
    for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            yield number, CODE_SPAN_RE.sub(" ", line)


def parse_cite(value: str, project: Project) -> tuple[str, str] | None:
    """(id, folder-relative path) from a cite's text, or None when it is not a work-folder cite."""
    value = value.strip().strip("`")
    prefix = project.rel(project.work_root).rstrip("/") + "/"
    if value.startswith(prefix):
        value = value[len(prefix):]
    if not value.startswith("work/"):
        return None
    rest = value[len("work/"):]
    if rest.startswith("archive/"):
        rest = rest[len("archive/"):]
    work_id, _, inner = rest.partition("/")
    inner = re.sub(r":\d+(?:-\d+)?$", "", inner).rstrip("/")
    return work_id, inner


def cites(project: Project) -> list[tuple[Path, int, str, str]]:
    """(home, line, id, inner path) for every work-folder cite in the homes."""
    found = []
    for home in project.homes():
        for number, line in prose_lines(home):
            for match in CITE_RE.finditer(line):
                for part in match.group(1).split(";"):
                    parsed = parse_cite(part, project)
                    if parsed:
                        found.append((home, number, *parsed))
    return found


def results(folder: Path) -> list[str]:
    out = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        rel = path.relative_to(folder)
        if rel.parts[0] in RECORD_DIRS or (len(rel.parts) == 1 and (rel.name in RECORD_FILES or OWNER_STEP_RE.match(rel.name))):
            continue
        out.append(rel.as_posix())
    return out


def covered(result: str, inner_paths: set[str]) -> bool:
    return any(inner == "" or result == inner or result.startswith(inner + "/") for inner in inner_paths)


def link_target(raw: str) -> str | None:
    """The path a link points at, or None for a URL, an anchor or a template placeholder."""
    if PLACEHOLDER_RE.match(raw):
        return None
    target = raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw
    if not target or SCHEME_RE.match(target) or target.startswith("#") or "{" in target:
        return None
    return target


def work_links(project: Project, folder_filter: str | None = None) -> list[tuple[Path, int, str]]:
    """Markdown links from a home into an open or archived work folder by path."""
    found = []
    for home in project.homes():
        for number, line in prose_lines(home):
            for match in LINK_RE.finditer(line):
                target = link_target(match.group(1))
                if target is None:
                    continue
                resolved = (home.parent / target.split("#", 1)[0]).resolve()
                if resolved.is_relative_to(project.work.resolve()):
                    rest = resolved.relative_to(project.work.resolve()).parts
                    rest = rest[1:] if rest and rest[0] == "archive" else rest
                    if rest and (folder_filter is None or rest[0] == folder_filter):
                        found.append((home, number, target))
    return found


# ---------------------------------------------------------------- check

def check(project: Project) -> list[str]:
    out: list[str] = []

    def fix(kind: str, path: Path, line: int, detail: str) -> None:
        out.append(f"FIX {kind} {project.rel(path)}:{line} {detail}")

    for base in (project.root, project.work_root, project.work):
        if base.is_dir():
            for path in sorted(base.iterdir()):
                if path.is_file() and LOOSE_RECORD_RE.match(path.name):
                    fix("misplaced", path, 1, "work-folder file outside a work/<id>/ folder")
    if project.work.is_dir():
        for path in sorted(project.work.iterdir()):
            if path.name.startswith(".") or path.name == "archive" or path.name == "README.md":
                continue
            if path.is_file():
                fix("misplaced", path, 1, "loose file in work/; put it in its work folder")
            elif not ID_RE.match(path.name):
                fix("bad-folder-name", path, 1, "work folder name is not <YYYY-MM-DD>-<workstream>")
            elif (project.archive / path.name).exists():
                fix("id-twice", path, 1, f"id is both open and in {project.rel(project.archive)}/")
    for folder in project.open_folders():
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(folder)
            if rel.name.startswith("MSG-") and rel.parts[0] != "channel":
                fix("misplaced", path, 1, "manager messages belong in channel/")
            elif rel.name == "STATE.md" and rel.parts[0] != "scratch":
                fix("misplaced", path, 1, "long-loop state belongs in scratch/STATE.md")
        state = folder / "scratch" / "STATE.md"
        if state.is_file():
            count = len(state.read_text(encoding="utf-8", errors="replace").splitlines())
            if count > STATE_LINES:
                fix("state-too-long", state, STATE_LINES + 1, f"{count} lines; the limit is {STATE_LINES}")

    for home in project.homes():
        for number, line in prose_lines(home):
            for match in LINK_RE.finditer(line):
                target = link_target(match.group(1))
                if target is None:
                    continue
                path_part = target.split("#", 1)[0]
                if path_part and not (home.parent / path_part).exists():
                    fix("dead-link", home, number, f"{target} does not exist")
            for match in TMP_RE.finditer(line):
                fix("tmp-path", home, number, f"{match.group(0)}: nothing kept lives in /tmp")
    for home, number, target in work_links(project):
        fix("work-link", home, number, f"{target} links into a work folder; cite it as (source: work/<id>/<path>)")
    for home, number, work_id, inner in cites(project):
        if not ID_RE.match(work_id):
            fix("bad-cite", home, number, f"work/{work_id} is not a <YYYY-MM-DD>-<workstream> id")
            continue
        folder = project.folder(work_id)
        if folder is None:
            fix("unresolved-cite", home, number, f"no work folder {work_id} open or archived")
        elif inner and not (folder / inner).exists():
            fix("unresolved-cite", home, number, f"{inner} not found in {project.rel(folder)}/")
    return out


# ---------------------------------------------------------------- close / handoff

def cited_inner(project: Project, work_id: str) -> set[str]:
    return {inner for _, _, cid, inner in cites(project) if cid == work_id}


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    return subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, env=env)


def ignored(root: Path, path: Path) -> bool:
    return git(root, "check-ignore", "-q", "--", str(path)).returncode == 0


def would_commit(folder: Path) -> list[Path]:
    keep = []
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.relative_to(folder).parts[0] not in NEVER_COMMITTED:
            keep.append(path)
    return keep


def close(project: Project, work_id: str, session: str, dry_run: bool) -> tuple[int, list[str]]:
    folder = project.work / work_id
    if not ID_RE.match(work_id) or not folder.is_dir():
        return 2, [f"REFUSE not-open no folder {project.rel(folder)}/"]
    if git(project.root, "rev-parse", "--is-inside-work-tree").stdout.strip() != "true":
        return 1, [f"REFUSE no-git {project.rel(project.root)} is not a git work tree"]
    refusals = []
    status = folder / "STATUS.md"
    if status.is_file() and not re.search(r"^STATUS:\s*DONE\b", status.read_text(encoding="utf-8"), re.M):
        refusals.append(f"REFUSE not-done {project.rel(status)} does not read STATUS: DONE")
    inner = cited_inner(project, work_id)
    for result in results(folder):
        if not covered(result, inner):
            refusals.append(f"REFUSE uncited {project.rel(folder / result)} has no (source: work/{work_id}/...) line in a home")
    for path in sorted(folder.iterdir()):
        match = OWNER_STEP_RE.match(path.name)
        if match and not (folder / f"OWNER-STEP-{match.group(1)}-result.md").exists():
            refusals.append(f"REFUSE owner-step-open {project.rel(path)} has no result file")
    for path in would_commit(folder):
        size = path.stat().st_size
        if size > LARGE_BYTES and not ignored(project.root, path):
            refusals.append(f"REFUSE large {project.rel(path)} is {size:,} bytes; move it out or gitignore it")
    for home, number, target in work_links(project, work_id):
        refusals.append(f"REFUSE work-link {project.rel(home)}:{number} links to {target}; the move would break it")
    if refusals:
        return 1, refusals
    target = project.archive / work_id
    if target.exists():
        return 1, [f"REFUSE id-twice {project.rel(target)}/ already exists"]
    if dry_run:
        return 0, [f"WOULD-CLOSE {project.rel(folder)} -> {project.rel(target)}"]

    old, new = project.rel(folder), project.rel(target)
    # A folder with nothing tracked is not a pathspec git knows, so only name it when it has tracked files.
    tracked_old = bool(git(project.root, "ls-files", "--", old).stdout.strip())
    made_archive = not project.archive.exists()
    project.archive.mkdir(parents=True, exist_ok=True)
    shutil.move(str(folder), str(target))
    excludes = [f":(exclude){new}/{name}" for name in NEVER_COMMITTED]
    staged: list[str] = []
    try:
        added = git(project.root, "add", "-A", "--", *([old] if tracked_old else []), new, *excludes)
        if added.returncode != 0:
            raise RuntimeError(added.stderr.strip())
        # --relative: paths relative to --root (not the repo top), the same base commit and reset resolve against.
        listed = git(project.root, "diff", "--cached", "--relative", "--no-renames", "--name-only", "--", old, new)
        staged = [l for l in listed.stdout.splitlines() if l]
        if not staged:
            return 0, [f"CLOSED {old} -> {new} (nothing tracked to commit)"]
        message = f"[{session}] close work/{work_id}"
        committed = git(project.root, "commit", "-q", "-m", message, "--", *staged)
        if committed.returncode != 0:
            raise RuntimeError(committed.stderr.strip() or committed.stdout.strip())
    except RuntimeError as error:
        lines = []
        if staged:
            reset = git(project.root, "reset", "-q", "--", *staged)
            if reset.returncode != 0:
                lines.append(f"REFUSE rollback-failed git reset did not unstage the move ({reset.stderr.strip()}); "
                             f"run `git reset -- {old} {new}` before the next commit")
        shutil.move(str(target), str(folder))
        if made_archive and not any(project.archive.iterdir()):
            project.archive.rmdir()
        return 1, [f"REFUSE git-failed {error}; the folder is back at {old}", *lines]
    sha = git(project.root, "rev-parse", "--short", "HEAD").stdout.strip()
    return 0, [f"CLOSED {old} -> {new} {sha}"]


def handoff(project: Project, work_id: str) -> tuple[int, list[str]]:
    folder = project.work / work_id
    if not ID_RE.match(work_id) or not folder.is_dir():
        return 2, [f"MISSING folder {project.rel(folder)}/"]
    note = folder / "HANDOFF.md"
    if not note.is_file():
        return 1, [f"MISSING {project.rel(note)}"]
    text = note.read_text(encoding="utf-8", errors="replace")
    inner = cited_inner(project, work_id)
    missing = []
    for result in results(folder):
        if covered(result, inner):
            continue
        if result in text or f"work/{work_id}/{result}" in text:
            continue
        missing.append(f"MISSING {project.rel(folder / result)} is neither cited by a home nor named in HANDOFF.md")
    return (1, missing) if missing else (0, ["OK"])


def main(argv: list[str] | None = None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=".")
    common.add_argument("--manifest")
    common.add_argument("--home", action="append", default=[])
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", parents=[common])
    close_parser = sub.add_parser("close", parents=[common])
    close_parser.add_argument("id")
    close_parser.add_argument("--session", required=True)
    close_parser.add_argument("--dry-run", action="store_true")
    handoff_parser = sub.add_parser("handoff", parents=[common])
    handoff_parser.add_argument("id")
    args = parser.parse_args(argv)
    root = Path(args.root)
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    project = Project(root, Path(args.manifest) if args.manifest else None, args.home)
    if args.command == "check":
        findings = check(project)
        print("\n".join(findings) if findings else "OK no work-folder findings")
        return 0
    if args.command == "close":
        code, lines = close(project, args.id, args.session, args.dry_run)
    else:
        code, lines = handoff(project, args.id)
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
