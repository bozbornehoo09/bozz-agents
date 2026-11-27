#!/usr/bin/env python3
"""Compute the work-tracker week/day folder for a date — never by hand.

Agents that reason about calendars drift: off-by-one weekdays, a week split at
a month edge, a week number taken from the wrong day. This read-only helper
derives everything from the date and reports what already exists.

Convention (Sunday→Saturday weeks):
  week folder  week_<NN>_<M-D>_<M-D>   e.g. week_27_6-28_7-4
               NN = ISO week number of the Monday inside the week, two digits
  day folder   <weekday>_<M>-<DD>      e.g. thursday_7-02
  entry        <week folder>/<day folder>/entry.md

A week may span two months or two years; it is never split at the edge.

  tracker_path.py [--date YYYY-MM-DD] [--root work_tracker]

Prints one JSON object. ``existing_week_folder`` / ``existing_day_folder`` name
a folder already covering the same dates under a different spelling; use it
and report the mismatch instead of creating a duplicate or renaming. Writes
nothing. Standard library only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import sys


WEEK_RE = re.compile(r"^week_(?P<num>\d+)_(?P<sm>\d{1,2})-(?P<sd>\d{1,2})_(?P<em>\d{1,2})-(?P<ed>\d{1,2})$")
DAY_RE = re.compile(r"^(?P<weekday>[a-z]+)_(?P<m>\d{1,2})-(?P<d>\d{1,2})$")


def week_bounds(day: dt.date) -> tuple[dt.date, dt.date]:
    # date.weekday(): Monday=0 … Sunday=6; shift so Sunday starts the week.
    start = day - dt.timedelta(days=(day.weekday() + 1) % 7)
    return start, start + dt.timedelta(days=6)


def week_number(start: dt.date) -> int:
    return (start + dt.timedelta(days=1)).isocalendar()[1]


def week_folder_name(day: dt.date) -> str:
    start, end = week_bounds(day)
    return f"week_{week_number(start):02d}_{start.month}-{start.day}_{end.month}-{end.day}"


def day_folder_name(day: dt.date) -> str:
    return f"{day.strftime('%A').lower()}_{day.month}-{day.day:02d}"


def find_existing_week(root: Path, start: dt.date, end: dt.date) -> str | None:
    if not root.is_dir():
        return None
    for child in sorted(root.iterdir()):
        match = WEEK_RE.match(child.name) if child.is_dir() else None
        if not match:
            continue
        if (int(match["sm"]), int(match["sd"]), int(match["em"]), int(match["ed"])) == (
            start.month,
            start.day,
            end.month,
            end.day,
        ):
            return child.name
    return None


def find_existing_day(week_dir: Path, day: dt.date) -> str | None:
    if not week_dir.is_dir():
        return None
    for child in sorted(week_dir.iterdir()):
        match = DAY_RE.match(child.name) if child.is_dir() else None
        if match and (int(match["m"]), int(match["d"])) == (day.month, day.day):
            return child.name
    return None


def resolve(day: dt.date, root: Path) -> dict:
    start, end = week_bounds(day)
    week = week_folder_name(day)
    existing_week = find_existing_week(root, start, end)
    week_dir = root / (existing_week or week)
    day_name = day_folder_name(day)
    existing_day = find_existing_day(week_dir, day)
    entry = week_dir / (existing_day or day_name) / "entry.md"
    notes = []
    if existing_week and existing_week != week:
        notes.append(f"existing week folder {existing_week!r} differs from computed {week!r}; reuse it and flag")
    if existing_day and existing_day != day_name:
        notes.append(f"existing day folder {existing_day!r} differs from computed {day_name!r}; reuse it and flag")
    return {
        "date": day.isoformat(),
        "weekday": day.strftime("%A"),
        "week_start": start.isoformat(),
        "week_end": end.isoformat(),
        "week_folder": week,
        "day_folder": day_name,
        "existing_week_folder": existing_week,
        "existing_day_folder": existing_day,
        "week_exists": week_dir.is_dir(),
        "entry_path": str(entry),
        "entry_exists": entry.is_file(),
        "notes": notes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--date", help="YYYY-MM-DD (default: today, local time)")
    parser.add_argument("--root", default="work_tracker")
    args = parser.parse_args(argv)
    try:
        day = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    except ValueError:
        print(f"error: invalid --date {args.date!r}; use YYYY-MM-DD", file=sys.stderr)
        return 2
    print(json.dumps(resolve(day, Path(args.root)), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
