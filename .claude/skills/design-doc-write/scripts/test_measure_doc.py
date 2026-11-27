"""Tests for measure_doc.py, on invented docs.

Run from the repository root: python3 -I -m unittest discover -s skills/design-doc-write/scripts
"""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("measure_doc.py")
EXAMPLES = Path(__file__).resolve().parent.parent / "references" / "examples"
spec = importlib.util.spec_from_file_location("measure_doc", SCRIPT)
measure_doc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(measure_doc)

AUDIENCE = """## Appendix — Audience notes

| Field | Answer |
|---|---|
| **Readers** | Platform engineers |
| **Prior knowledge** | HIGH on the queue |
| **Takeaway** | Isolation per tenant |
| **Stakes** | Fewer pages |
| **Ask** | Approve by Friday |
| **Expected questions** | Why not a shared pool? (section 1) |
"""


def doc(body="The cache keeps a copy of each price for ten minutes.\n", opening=None,
        audience=AUDIENCE, extra_after=""):
    opening = opening or "Shoppers will see prices load in under a second. This doc covers the price cache."
    return (f"# Price Cache — Mini-Design\n\n**Status:** Draft\n\n{opening}\n\n"
            f"## 1. The cache\n\n{body}\n## Appendices\n\n{audience}{extra_after}")


def run(text, *args):
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "doc.md"
        path.write_text(text, encoding="utf-8")
        proc = subprocess.run([sys.executable, "-I", str(SCRIPT), str(path), "--json", *args],
                              capture_output=True, text=True)
    return proc.returncode, (json.loads(proc.stdout) if proc.stdout.strip() else None), proc.stderr


class Words(unittest.TestCase):
    def test_table_pipes_dashes_and_link_targets_are_not_words(self):
        self.assertEqual(measure_doc.words("| a | b — c |"), 3)
        self.assertEqual(measure_doc.words("see [the HLD](docs/very/long/path.md) now"), 4)


class Examples(unittest.TestCase):
    def test_both_bundled_examples_pass_and_infer_their_grain(self):
        for name, grain in (("webhook-delivery-hld.md", "HLD"), ("endpoint-pause-mini-design.md", "mini")):
            proc = subprocess.run([sys.executable, "-I", str(SCRIPT), str(EXAMPLES / name), "--json"],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout)
            result = json.loads(proc.stdout)
            self.assertEqual(result["grain"], grain)
            self.assertEqual(result["audience"]["unfilled_rows"], [])
            self.assertEqual(result["opening"]["status"], "ok")


class Budget(unittest.TestCase):
    def test_a_clean_doc_exits_zero(self):
        code, result, _ = run(doc())
        self.assertEqual(code, 0, result["problems"])
        self.assertEqual(result["opening"]["sentences"], 2)

    def test_over_the_ceiling_fails_and_names_the_overage(self):
        code, result, _ = run(doc(body="word " * 1200))
        self.assertEqual(code, 1)
        self.assertTrue(any("over the mini ceiling of 1000" in p for p in result["problems"]))

    def test_a_dated_acceptance_line_turns_the_overage_into_a_note(self):
        accepted = "\nLength accepted: 2026-11-01 — the state table must sit beside its rules.\n"
        code, result, _ = run(doc(body="word " * 1200, extra_after=accepted))
        self.assertEqual(code, 0, result["problems"])
        self.assertTrue(any("accepted, informational" in n for n in result["notes"]))

    def test_an_acceptance_line_without_a_reason_is_ignored(self):
        code, result, _ = run(doc(body="word " * 1200, extra_after="\nLength accepted: 2026-11-01\n"))
        self.assertEqual(code, 1)
        self.assertFalse(result["accepted"]["length"]["valid"])

    def test_glossary_code_and_comments_are_not_body_words(self):
        glossary = "## Glossary\n\n" + "".join(f"- **T{i}** — a term number {i}.\n" for i in range(35))
        text = doc().replace("## 1. The cache", glossary + "\n## 1. The cache")
        text = text.replace("ten minutes.\n", "ten minutes.\n\n```\nlots of code words here\n```\n<!-- a\nlong comment -->\n")
        code, result, _ = run(text)
        self.assertEqual(code, 0, result["problems"])  # a big glossary never fails the run
        self.assertEqual(result["glossary"]["entries"], 35)
        self.assertEqual(result["sections"][-1]["words"], 3 + 11)  # heading words + the one sentence
        self.assertTrue(any("FIX-level re-audit" in n for n in result["notes"]))

    def test_the_grain_flag_overrides_the_title(self):
        _, result, _ = run(doc(), "--type", "HLD")
        self.assertEqual((result["grain"], result["ceiling"]), ("HLD", 2500))

    def test_an_unknown_grain_is_a_usage_error(self):
        code, _, err = run(doc().replace("Mini-Design", "Notes"))
        self.assertEqual(code, 2)
        self.assertIn("--type", err)


class AudienceAndOpening(unittest.TestCase):
    def test_missing_audience_notes_fail(self):
        code, result, _ = run(doc(audience=""))
        self.assertEqual(code, 1)
        self.assertIn("no audience notes appendix", result["problems"])

    def test_a_placeholder_row_fails_but_unknown_counts_as_filled(self):
        text = doc().replace("Approve by Friday", "<the ask>").replace("Fewer pages", "unknown — ask the on-call lead")
        code, result, _ = run(text)
        self.assertEqual(code, 1)
        self.assertEqual([r["field"] for r in result["audience"]["unfilled_rows"]], ["Ask"])

    def test_notes_above_the_divider_are_misplaced(self):
        text = doc(audience="").replace("## Appendices", AUDIENCE + "\n## Appendices")
        code, result, _ = run(text)
        self.assertEqual(code, 1)
        self.assertFalse(result["audience"]["after_divider"])

    def test_a_labelled_opening_fails(self):
        code, result, _ = run(doc(opening="**Purpose:** shoppers will see prices faster."))
        self.assertEqual(code, 1)
        self.assertEqual(result["opening"]["status"], "labelled")

    def test_a_note_blockquote_is_not_mistaken_for_the_opening(self):
        text = doc().replace("**Status:** Draft\n", "**Status:** Draft\n\n> **Note:** invented example.\n")
        _, result, _ = run(text)
        self.assertEqual(result["opening"]["status"], "ok")


class Sentences(unittest.TestCase):
    def test_a_long_sentence_is_listed_with_its_line(self):
        long = "The cache " + "keeps one more copy " * 8 + "for ten minutes."
        code, result, _ = run(doc(body=f"Short one here.\n{long}\n"))
        self.assertEqual(code, 0)
        (hit,) = result["sentences"]["long"]
        self.assertGreater(hit["words"], 30)
        self.assertEqual(hit["line"], 10)


if __name__ == "__main__":
    unittest.main()
