from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/skill-review/scripts/measure_skills.py"

# 200 distinct words: one contiguous run longer than PASSAGE_WORDS whose
# length also exceeds SHARED_WORDS, so two skills carrying it trip the limit.
SHARED = " ".join(f"word{i}" for i in range(200))


def measure(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT), *args],
        text=True,
        capture_output=True,
    )


def make_skill(root: Path, name: str, description: str, body: str, refs: dict[str, str] | None = None) -> None:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\n{body}\n",
        encoding="utf-8",
    )
    for rel, text in (refs or {}).items():
        path = skill / "references" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


class MeasureSkillsCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_small_distinct_skills_pass_strict(self) -> None:
        make_skill(self.root, "alpha", "Summarize release notes for a tag.", "Do the alpha thing.",
                    {"brief.md": "# Brief\n\nshort\n"})
        make_skill(self.root, "beta", "Lint YAML manifests in a repo.", "Do the beta thing.")
        result = measure(str(self.root), "--strict")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("| alpha | 34 |", result.stdout)
        self.assertIn("| alpha/references/brief.md |", result.stdout)
        self.assertTrue(result.stdout.rstrip().endswith("no limits crossed"))

    def test_each_limit_kind_is_printed(self) -> None:
        make_skill(self.root, "long", "x" * 900, "\n".join(["line"] * 600))
        make_skill(self.root, "one", "First skill.", SHARED)
        make_skill(self.root, "two", "Second skill.", SHARED,
                    {"big.md": "row\n" * 2100})
        make_skill(self.root, "hosty", "Host notes.",
                    "## Setup for Codex\n\n" + " ".join(["w"] * 320))
        result = measure(str(self.root))
        self.assertEqual(result.returncode, 0, result.stderr)
        out = result.stdout
        self.assertIn("OVER long desc-chars 900 > 800", out)
        self.assertIn("OVER long skill-lines", out)
        self.assertRegex(out, r"OVER one shared-words \d+ > 150 \(with two\)")
        self.assertIn("PAGE two/references/big.md 2100 lines > 2000", out)
        self.assertIn('CANDIDATE hosty branch-section "Setup for Codex" 320 > 300', out)
        self.assertEqual(measure(str(self.root), "--strict").returncode, 1)

    def test_overlap_ignored_once_descriptions_name_each_other(self) -> None:
        desc = "Review pull request diffs against architecture decisions and rules."
        make_skill(self.root, "rev-a", desc, "a")
        make_skill(self.root, "rev-b", desc, "b")
        self.assertIn("OVER rev-a description-overlap 1.00 > 0.35 (with rev-b)", measure(str(self.root)).stdout)

        named = self.root / "named"
        make_skill(named, "rev-a", desc + " Not rev-b.", "a")
        make_skill(named, "rev-b", desc + " Not rev-a.", "b")
        self.assertNotIn("description-overlap", measure(str(named)).stdout)

    def test_folded_description_and_skill_selection(self) -> None:
        skill = self.root / "folded"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            textwrap.dedent("""\
                ---
                name: folded
                description: >-
                  Spans two
                  lines here.
                ---
                # folded
                """),
            encoding="utf-8",
        )
        make_skill(self.root, "other", "Other.", "o")
        result = measure(str(self.root), "--skill", "folded")
        self.assertIn("| folded | 21 |", result.stdout)
        self.assertNotIn("| other |", result.stdout)
        self.assertNotEqual(measure(str(self.root), "--skill", "missing").returncode, 0)

    def test_runs_on_this_repository(self) -> None:
        result = measure(str(ROOT / "skills"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("| skill-review |", result.stdout)


if __name__ == "__main__":
    unittest.main()
