from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "skills/update-work-tracker/scripts/tracker_path.py"
ADR_INDEX = ROOT / "skills/update-decisions/scripts/adr_index.py"


def run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-I", str(script), *args], text=True, capture_output=True)


def tracker(date: str, root: Path) -> dict:
    result = run(TRACKER, "--date", date, "--root", str(root))
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


class TrackerPathTests(unittest.TestCase):
    def test_matches_existing_convention(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cases = {
                "2026-06-28": ("week_27_6-28_7-4", "sunday_6-28"),
                "2026-07-02": ("week_27_6-28_7-4", "thursday_7-02"),
                "2026-07-18": ("week_29_7-12_7-18", "saturday_7-18"),
                "2026-07-19": ("week_30_7-19_7-25", "sunday_7-19"),
            }
            for date, (week, day) in cases.items():
                with self.subTest(date=date):
                    state = tracker(date, root)
                    self.assertEqual(state["week_folder"], week)
                    self.assertEqual(state["day_folder"], day)
                    self.assertFalse(state["entry_exists"])

    def test_week_spanning_year_edge_is_not_split(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for date in ("2026-12-27", "2026-12-31", "2027-01-02"):
                with self.subTest(date=date):
                    state = tracker(date, root)
                    self.assertEqual(state["week_folder"], "week_53_12-27_1-2")
                    self.assertEqual(state["week_start"], "2026-12-27")
                    self.assertEqual(state["week_end"], "2027-01-02")
            self.assertEqual(tracker("2027-01-03", root)["week_folder"], "week_01_1-3_1-9")

    def test_reuses_existing_differently_spelled_folders(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            entry_dir = root / "week_7_6-28_7-4" / "thursday_7-2"
            entry_dir.mkdir(parents=True)
            (entry_dir / "entry.md").write_text("- entry\n")
            state = tracker("2026-07-02", root)
            self.assertEqual(state["existing_week_folder"], "week_7_6-28_7-4")
            self.assertEqual(state["existing_day_folder"], "thursday_7-2")
            self.assertTrue(state["entry_exists"])
            self.assertTrue(state["entry_path"].endswith("week_7_6-28_7-4/thursday_7-2/entry.md"))
            self.assertEqual(len(state["notes"]), 2)

    def test_invalid_date_is_a_usage_error(self):
        result = run(TRACKER, "--date", "2026-02-30")
        self.assertEqual(result.returncode, 2)


def write_adr(directory: Path, name: str, status: str, extra: str = "") -> None:
    number = name[:4]
    (directory / name).write_text(
        textwrap.dedent(
            f"""\
            # ADR-{number}: Example {number}

            **Status:** {status}
            **Date:** 2026-01-01
            {extra}
            ## Context
            x
            """
        )
    )


class AdrIndexTests(unittest.TestCase):
    def check(self, directory: Path) -> list[dict]:
        result = run(ADR_INDEX, "check", "--dir", str(directory), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["findings"]

    def test_clean_table_and_list_indexes(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            write_adr(directory, "0001-first.md", "Superseded by ADR-0002")
            write_adr(directory, "0002-second.md", "Accepted", "**Supersedes:** ADR-0001\n")
            (directory / "README.md").write_text(
                "| ADR | Title | Status |\n|---|---|---|\n"
                "| [ADR-0001](0001-first.md) | Example 0001 | Superseded by ADR-0002 |\n"
                "- [ADR-0002](0002-second.md) — Example 0002 — Accepted\n"
            )
            self.assertEqual(self.check(directory), [])
            lines = run(ADR_INDEX, "lines", "--dir", str(directory)).stdout.splitlines()
            self.assertEqual(lines[1], "- [ADR-0002](0002-second.md) — Example 0002 — Accepted")

    def test_reports_each_inconsistency_class(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            write_adr(directory, "0001-first.md", "Superseded by ADR-0002")
            write_adr(directory, "0002-second.md", "Accepted")  # no Supersedes line
            write_adr(directory, "0003-third.md", "Maybe later")
            write_adr(directory, "0004-fourth.md", "Superseded by ADR-0009")
            (directory / "0005-fifth.md").write_text("# ADR-0005: No status\n")
            (directory / "0005-dup.md").write_text("# ADR-0005: Dup\n\n**Status:** Accepted\n")
            (directory / "README.md").write_text(
                "- [ADR-0001](0001-first.md) — Example — Accepted\n"
                "- [ADR-0008](0008-gone.md) — Gone — Accepted\n"
            )
            classes = {item["class"] for item in self.check(directory)}
            self.assertEqual(
                classes,
                {
                    "status-mismatch",
                    "index-orphan",
                    "missing-from-index",
                    "broken-supersedence",
                    "bad-status",
                    "missing-status",
                    "duplicate-number",
                },
            )

    def test_text_output_and_missing_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            write_adr(directory, "0001-first.md", "Accepted")
            result = run(ADR_INDEX, "check", "--dir", str(directory))
            self.assertEqual(result.returncode, 0)
            self.assertIn("FIX missing-from-index 0001-first.md:1", result.stdout)
        missing = run(ADR_INDEX, "check", "--dir", "/nonexistent/decisions")
        self.assertEqual(missing.returncode, 2)

    def test_repository_own_decisions_are_consistent(self):
        self.assertEqual(self.check(ROOT / "docs/decisions"), [])


if __name__ == "__main__":
    unittest.main()
