"""Tests for adr_index.py's map checks and its write command (check/lines are covered in tests/)."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parent / "adr_index.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], text=True, capture_output=True)


def adr(directory: Path, number: str, status: str, supersedes: str = "") -> None:
    extra = f"**Supersedes:** ADR-{supersedes}\n" if supersedes else ""
    (directory / f"{number}-decision-{number}.md").write_text(
        f"# ADR-{number}: Decision {number}\n\n**Status:** {status}\n**Date:** 2026-01-01\n{extra}\n## Context\nx\n",
        encoding="utf-8",
    )


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name) / "orders-service" / "docs" / "decisions"
        self.dir.mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, *args: str) -> list[str]:
        result = run("write", "--dir", str(self.dir), "--date", "2026-11-27", *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.splitlines()

    def findings(self) -> list[dict]:
        result = run("check", "--dir", str(self.dir), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["findings"]


class WriteTests(Base):
    def test_creates_index_and_map_when_missing(self):
        adr(self.dir, "0001", "Accepted")
        out = self.write()
        self.assertEqual(out[0], "CREATED README.md")
        self.assertTrue(out[1].startswith("CREATED IN-FORCE.md"))
        index = (self.dir / "README.md").read_text()
        self.assertIn("- [ADR-0001](0001-decision-0001.md) — Decision 0001 — Accepted", index)
        self.assertIn("<!-- adr-index:begin", index)
        new_map = (self.dir / "IN-FORCE.md").read_text()
        self.assertIn("# Decisions in force — orders-service", new_map)
        self.assertIn("DRAFT: created 2026-11-27", new_map)
        self.assertIn("Map last changed: 2026-11-27", new_map)
        self.assertNotIn("{project}", new_map)
        self.assertNotIn("```", new_map)

    def test_regenerates_only_inside_markers(self):
        adr(self.dir, "0001", "Accepted")
        self.write()
        readme = self.dir / "README.md"
        readme.write_text("# Hand title\n\nHand prose stays.\n\n" + readme.read_text().split("\n\n", 2)[2]
                          + "\nTrailing hand note.\n")
        adr(self.dir, "0002", "Proposed")
        self.assertEqual(self.write()[0], "WROTE README.md")
        text = readme.read_text()
        self.assertIn("Hand prose stays.", text)
        self.assertIn("Trailing hand note.", text)
        self.assertIn("— Decision 0002 — Proposed", text)
        self.assertEqual(self.write()[0], "UNCHANGED README.md")

    def test_keeps_table_form_inside_markers(self):
        adr(self.dir, "0001", "Accepted")
        (self.dir / "README.md").write_text(
            "# ADRs\n\n<!-- adr-index:begin -->\n| ADR | Title | Status |\n|---|---|---|\n"
            "| [ADR-0001](0001-decision-0001.md) | Old title | Proposed |\n<!-- adr-index:end -->\n")
        self.write()
        text = (self.dir / "README.md").read_text()
        self.assertIn("| [ADR-0001](0001-decision-0001.md) | Decision 0001 | Accepted |", text)
        self.assertNotIn("Old title", text)
        self.assertEqual(self.findings(), [{"class": "map-missing", "file": "0001-decision-0001.md",
                                            "line": 3, "detail": "Accepted ADR-0001 is cited nowhere in IN-FORCE.md"}])

    def test_hand_kept_index_and_existing_map_never_written(self):
        adr(self.dir, "0001", "Accepted")
        hand_index = "# ADRs\n\n- [ADR-0001](0001-decision-0001.md) — Decision 0001 — Accepted\n"
        hand_map = "# My map\n\n## In force\n- We decided this (ADR-0001)\n"
        (self.dir / "README.md").write_text(hand_index)
        (self.dir / "IN-FORCE.md").write_text(hand_map)
        out = self.write()
        self.assertTrue(out[0].startswith("SKIP README.md:3"))
        self.assertTrue(out[1].startswith("KEEP IN-FORCE.md"))
        self.assertEqual((self.dir / "README.md").read_text(), hand_index)
        self.assertEqual((self.dir / "IN-FORCE.md").read_text(), hand_map)

    def test_hand_kept_index_in_unparsed_layout_is_skipped(self):
        adr(self.dir, "0001", "Accepted")
        for hand_index in ("# ADRs\n\n| # | Decision | Status |\n|---|---|---|\n"
                           "| 0001 | [Decision](0001-decision-0001.md) | Accepted |\n",
                           "# ADRs\n\nSee ADR-0001 for the queue choice.\n"):
            with self.subTest(index=hand_index):
                (self.dir / "README.md").write_text(hand_index)
                self.assertTrue(self.write()[0].startswith("SKIP README.md:"))
                self.assertEqual((self.dir / "README.md").read_text(), hand_index)

    def test_index_without_entries_gets_block_appended(self):
        adr(self.dir, "0001", "Accepted")
        (self.dir / "README.md").write_text("# ADRs\n\nIntro only.\n")
        self.assertEqual(self.write()[0], "WROTE README.md")
        text = (self.dir / "README.md").read_text()
        self.assertTrue(text.startswith("# ADRs\n\nIntro only.\n\n<!-- adr-index:begin"))

    def test_dry_run_writes_nothing(self):
        adr(self.dir, "0001", "Accepted")
        out = self.write("--dry-run")
        self.assertEqual(out[0], "WOULD-CREATED README.md")
        self.assertTrue(out[1].startswith("WOULD-CREATED IN-FORCE.md"))
        self.assertFalse((self.dir / "README.md").exists())
        self.assertFalse((self.dir / "IN-FORCE.md").exists())

    def test_unterminated_marker_is_skipped(self):
        adr(self.dir, "0001", "Accepted")
        original = "# ADRs\n\n<!-- adr-index:begin -->\nold\n"
        (self.dir / "README.md").write_text(original)
        self.assertIn("no end marker", self.write()[0])
        self.assertEqual((self.dir / "README.md").read_text(), original)

    def test_bad_date_is_usage_error(self):
        self.assertEqual(run("write", "--dir", str(self.dir), "--date", "2026-13-01").returncode, 2)


class MapCheckTests(Base):
    def setUp(self):
        super().setUp()
        adr(self.dir, "0001", "Superseded by ADR-0002")
        adr(self.dir, "0002", "Accepted", supersedes="0001")
        adr(self.dir, "0003", "Deprecated")
        adr(self.dir, "0004", "Accepted")
        self.write()  # index + skeleton map

    def test_skeleton_map_reports_every_accepted_adr(self):
        classes = sorted((f["class"], f["file"]) for f in self.findings())
        self.assertEqual(classes, [("map-missing", "0002-decision-0002.md"), ("map-missing", "0004-decision-0004.md")])

    def test_each_map_class(self):
        (self.dir / "IN-FORCE.md").write_text(
            "# Map\n\n## In force\n"
            "<!-- an example (ADR-0009)\n spanning lines -->\n"
            "- Old form still listed (ADR-0001)\n"
            "- Superseded with successor is fine (ADR-0002, replacing ADR-0001)\n"
            "- Deprecated call (ADR-0003)\n"
            "- Ghost (ADR-0042)\n"
            "\n## Unclear\n- Whether ADR-0001 still binds\n"
        )
        found = sorted((f["class"], f["line"]) for f in self.findings())
        self.assertEqual(found, [
            ("map-missing", 3),          # ADR-0004's Status line
            ("map-orphan", 9),
            ("superseded-in-map", 6),
            ("superseded-in-map", 8),
        ])

    def test_clean_map_and_text_output(self):
        (self.dir / "IN-FORCE.md").write_text("## In force\n- A (ADR-0002)\n- B (ADR-0004)\n")
        self.assertEqual(self.findings(), [])
        out = run("check", "--dir", str(self.dir)).stdout
        self.assertEqual(out.strip(), "OK no index/body inconsistencies")

    def test_no_map_means_no_map_findings(self):
        (self.dir / "IN-FORCE.md").unlink()
        self.assertEqual(self.findings(), [])


if __name__ == "__main__":
    unittest.main()
