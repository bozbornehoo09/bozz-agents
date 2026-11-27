#!/usr/bin/env python3
"""Read-only consistency check between ADR files and the decisions index.

The ADR body's ``**Status:**`` line is the source of truth; the index
(``README.md`` in the decisions directory) mirrors it. This helper never
writes. It prints one finding per line so ``update-decisions`` can fix the
index and ``docs-review`` can fold the lines into its report verbatim.

  check [--dir docs/decisions] [--index README.md] [--json]
  lines [--dir docs/decisions]    print the canonical list-form index lines

Finding lines: ``FIX <class> <file>:<line> <detail>``. Classes:
  missing-status       ADR body has no **Status:** line
  bad-status           Status is not Accepted | Proposed | Deprecated |
                       Superseded by ADR-NNNN
  status-mismatch      index status differs from the body status
  missing-from-index   an ADR file has no index entry
  index-orphan         an index entry names a file that does not exist
  duplicate-number     two ADR files share a number
  broken-supersedence  "Superseded by ADR-X" without X existing or without
                       X carrying "**Supersedes:** ADR-<this>"
Exit status: 0 after a completed check (findings or not), 2 on usage error.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


ADR_FILE_RE = re.compile(r"^(?P<num>\d{4})-[a-z0-9][a-z0-9-]*\.md$")
STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*(?P<value>.+?)\s*$")
SUPERSEDES_RE = re.compile(r"^\*\*Supersedes:\*\*\s*(?P<value>.+?)\s*$")
TITLE_RE = re.compile(r"^#\s+(?:ADR-\d{4}:\s*)?(?P<title>.+?)\s*$")
VALID_STATUS_RE = re.compile(r"^(Accepted|Proposed|Deprecated|Superseded by ADR-(?P<by>\d{4}))$")
# Index entries: a list line "- [ADR-NNNN](file.md) — Title — Status" or a
# table row "| [ADR-NNNN](file.md) | Title | Status |".
LIST_ENTRY_RE = re.compile(
    r"^\s*[-*]\s+\[ADR-(?P<num>\d{4})\]\((?P<file>[^)]+)\)\s+—\s+(?P<title>.+?)\s+—\s+(?P<status>.+?)\s*$"
)
TABLE_ENTRY_RE = re.compile(
    r"^\s*\|\s*\[ADR-(?P<num>\d{4})\]\((?P<file>[^)]+)\)\s*\|\s*(?P<title>.+?)\s*\|\s*(?P<status>.+?)\s*\|\s*$"
)


def read_adr(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    record = {
        "file": path.name,
        "num": ADR_FILE_RE.match(path.name).group("num"),
        "title": None,
        "status": None,
        "status_line": None,
        "supersedes": [],
    }
    for index, line in enumerate(lines[:40], start=1):
        if record["title"] is None:
            title = TITLE_RE.match(line)
            if title:
                record["title"] = title.group("title")
        status = STATUS_RE.match(line)
        if status and record["status"] is None:
            record["status"] = status.group("value")
            record["status_line"] = index
        supersedes = SUPERSEDES_RE.match(line)
        if supersedes:
            record["supersedes"] = re.findall(r"ADR-(\d{4})", supersedes.group("value"))
    return record


def read_index(path: Path) -> list[dict]:
    entries = []
    if not path.exists():
        return entries
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = LIST_ENTRY_RE.match(line) or TABLE_ENTRY_RE.match(line)
        if match:
            entries.append({**match.groupdict(), "line": index})
    return entries


def check(directory: Path, index_name: str) -> list[dict]:
    findings: list[dict] = []

    def add(kind: str, file: str, line: int, detail: str) -> None:
        findings.append({"class": kind, "file": file, "line": line, "detail": detail})

    adrs = [read_adr(path) for path in sorted(directory.iterdir()) if ADR_FILE_RE.match(path.name)]
    by_num: dict[str, dict] = {}
    for adr in adrs:
        if adr["num"] in by_num:
            add("duplicate-number", adr["file"], 1, f"ADR-{adr['num']} also used by {by_num[adr['num']]['file']}")
        else:
            by_num[adr["num"]] = adr

    for adr in adrs:
        status = adr["status"]
        if status is None:
            add("missing-status", adr["file"], 1, "no **Status:** line in the first 40 lines")
            continue
        valid = VALID_STATUS_RE.match(status)
        if not valid:
            add("bad-status", adr["file"], adr["status_line"], f"status {status!r} is not a canonical value")
            continue
        successor_num = valid.group("by")
        if successor_num:
            successor = by_num.get(successor_num)
            if successor is None:
                add("broken-supersedence", adr["file"], adr["status_line"], f"ADR-{successor_num} does not exist")
            elif adr["num"] not in successor["supersedes"]:
                add(
                    "broken-supersedence",
                    adr["file"],
                    adr["status_line"],
                    f"{successor['file']} has no '**Supersedes:** ADR-{adr['num']}' line",
                )

    index_path = directory / index_name
    entries = read_index(index_path)
    indexed_files = set()
    for entry in entries:
        indexed_files.add(entry["file"])
        adr = next((item for item in adrs if item["file"] == entry["file"]), None)
        if adr is None:
            add("index-orphan", index_name, entry["line"], f"{entry['file']} does not exist")
            continue
        if adr["status"] is not None and entry["status"] != adr["status"]:
            add(
                "status-mismatch",
                index_name,
                entry["line"],
                f"index says {entry['status']!r}; {adr['file']}:{adr['status_line']} says {adr['status']!r} (body is truth)",
            )
    for adr in adrs:
        if adr["file"] not in indexed_files:
            add("missing-from-index", adr["file"], 1, f"ADR-{adr['num']} has no entry in {index_name}")
    return findings


def canonical_lines(directory: Path) -> list[str]:
    lines = []
    for path in sorted(directory.iterdir()):
        if ADR_FILE_RE.match(path.name):
            adr = read_adr(path)
            lines.append(
                f"- [ADR-{adr['num']}]({adr['file']}) — {adr['title'] or adr['file']} — {adr['status'] or 'MISSING STATUS'}"
            )
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    check_parser = sub.add_parser("check", help="report index/body inconsistencies (read-only)")
    check_parser.add_argument("--dir", default="docs/decisions")
    check_parser.add_argument("--index", default="README.md")
    check_parser.add_argument("--json", action="store_true")
    lines_parser = sub.add_parser("lines", help="print canonical list-form index lines")
    lines_parser.add_argument("--dir", default="docs/decisions")
    args = parser.parse_args(argv)

    directory = Path(args.dir)
    if not directory.is_dir():
        print(f"error: not a directory: {directory}", file=sys.stderr)
        return 2
    if args.command == "lines":
        print("\n".join(canonical_lines(directory)))
        return 0
    findings = check(directory, args.index)
    if args.json:
        print(json.dumps({"findings": findings}, sort_keys=True))
    else:
        for item in findings:
            print(f"FIX {item['class']} {item['file']}:{item['line']} {item['detail']}")
        if not findings:
            print("OK no index/body inconsistencies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
