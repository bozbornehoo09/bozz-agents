"""Tests for load_context.py. Each test builds a project in a temp dir and runs the script."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


SCRIPT = Path(__file__).resolve().parent / "load_context.py"


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "--root", str(root), "--date", "2026-11-27", *args],
        text=True,
        capture_output=True,
    )


def load(root: Path, *args: str) -> str:
    result = run(root, *args)
    assert result.returncode == 0, result.stderr
    return result.stdout


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")


PLAN = """\
    # orders-service — Work Plan

    <!-- PURPOSE: a long hidden comment that must never reach the load -->

    **As of:** 2026-11-25

    ## 0. Status snapshot

    - Retry API landed.

    ## 1. Next up

    - [ ] Ship the webhook dispatcher
    - [~] Tune the retry backoff

    ## 2. Later

    - [ ] Archive old exports
    - [x] Done thing

    ## Blocked

    - Waiting on the queue quota.
    """


def adr(directory: Path, number: str, title: str, status: str) -> None:
    write(directory / f"{number}-{title.lower().replace(' ', '-')}.md",
          f"# ADR-{number}: {title}\n\n**Status:** {status}\n**Date:** 2026-01-01\n\n## Context\nlong body text\n")


def project(root: Path) -> None:
    write(root / "work_tracker/work_plan.md", PLAN)
    adr(root / "docs/decisions", "0001", "Use a queue", "Superseded by ADR-0002")
    adr(root / "docs/decisions", "0002", "Use a managed queue", "Accepted")
    adr(root / "docs/decisions", "0003", "Drop polling", "Proposed")
    write(root / "work_tracker/week_48_11-22_11-28/tuesday_11-24/entry.md",
          "# Tuesday 2026-11-24 — Retry API\n\n## Implemented\n- older body\n")
    write(root / "work_tracker/week_48_11-22_11-28/wednesday_11-25/entry.md",
          "# Wednesday 2026-11-25 — Dispatcher work\n\n## Implemented\n- morning body\n\n"
          "## 16:10 — Afternoon fix\n- afternoon body\n")
    write(root / "docs/architecture/design.md", "# Design\n\nwords " * 50)


class LoadContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_default_layers_without_manifest(self):
        project(self.root)
        out = load(self.root, "--no-git")
        self.assertIn("shipped defaults", out)
        self.assertIn("**As of:** 2026-11-25", out)
        self.assertIn("### Next up", out)
        self.assertIn("Waiting on the queue quota.", out)
        self.assertIn("- [ ] Archive old exports", out)
        self.assertNotIn("Done thing", out)
        self.assertNotIn("PURPOSE", out)
        self.assertIn("ADR-0003 (Proposed): Drop polling", out)
        self.assertIn("ADR-0001 (Superseded by ADR-0002): Use a queue", out)
        self.assertNotIn("long body text", out)
        self.assertIn("- architecture: docs/architecture/", out)
        self.assertNotIn("Freshness", out)

    def test_open_items_are_not_repeated(self):
        project(self.root)
        out = load(self.root, "--no-git")
        self.assertEqual(out.count("Ship the webhook dispatcher"), 1)

    def test_manifest_remaps_paths(self):
        write(self.root / "context-manifest.yaml", """\
            project:
              name: "orders-service"   # trailing comment
              orientation: ["ORIENTATION.md"]
            layers:
              - id: decisions
                path: adr/
              - id: work-plan
                path: plan/PLAN.md
              - id: work-tracker
                path: log/
              - id: open-questions
                path: notes/questions.md
            """)
        write(self.root / "plan/PLAN.md", PLAN)
        adr(self.root / "adr", "0007", "Pick a store", "Accepted")
        out = load(self.root, "--no-git")
        self.assertIn("Context load — orders-service", out)
        self.assertIn("From plan/PLAN.md", out)
        self.assertIn("ADR-0007 (Accepted): Pick a store", out)
        self.assertIn("- open-questions: notes/questions.md (absent)", out)
        self.assertNotIn("docs/architecture", out)

    def test_map_preferred_over_titles_and_draft_kept(self):
        project(self.root)
        write(self.root / "docs/decisions/IN-FORCE.md", """\
            # Decisions in force — orders-service

            DRAFT: drafted from the ADRs on 2026-11-20; the ADRs are the source until cleared.

            Map last changed: 2026-11-20

            ## In force
            <!-- one line per decision -->
            ### Messaging
            - Messages go through a managed queue (ADR-0002)

            ## Unclear
            """)
        out = load(self.root, "--no-git")
        self.assertIn("Messages go through a managed queue (ADR-0002)", out)
        self.assertIn("DRAFT: drafted from the ADRs", out)
        self.assertNotIn("ADR-0003 (Proposed)", out)
        self.assertNotIn("one line per decision", out)

    def test_empty_map_falls_back_to_titles(self):
        project(self.root)
        write(self.root / "docs/decisions/IN-FORCE.md",
              "# Map\n\nDRAFT: new\n\n## In force\n<!-- - example (ADR-0001) -->\n\n## Unclear\n")
        out = load(self.root, "--no-git")
        self.assertIn("No decisions map yet", out)
        self.assertIn("ADR-0002 (Accepted)", out)
        self.assertIn("DRAFT: new", out)

    def test_tracker_newest_entry_and_timed_block(self):
        project(self.root)
        out = load(self.root, "--no-git")
        newest = out.index("2026-11-25")
        older = out.index("2026-11-24")
        self.assertLess(newest, older)
        self.assertIn("later that day: 16:10 — Afternoon fix", out)
        body = out.split("### Newest entry body", 1)[1]
        self.assertIn("afternoon body", body)
        self.assertNotIn("morning body", body)
        self.assertNotIn("older body", out)

    def test_tracker_year_edge_uses_weekday(self):
        write(self.root / "work_tracker/week_53_12-27_1-2/sunday_12-27/entry.md", "# Dec entry\n")
        write(self.root / "work_tracker/week_53_12-27_1-2/saturday_1-02/entry.md", "# Jan entry\n")
        out = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), "--root", str(self.root), "--date", "2027-01-05", "--no-git"],
            text=True, capture_output=True,
        ).stdout
        self.assertIn("2027-01-02", out)
        self.assertIn("2026-12-27", out)
        self.assertLess(out.index("Jan entry"), out.index("Dec entry"))

    def test_freshness_warning(self):
        project(self.root)
        out = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), "--root", str(self.root), "--date", "2026-12-20", "--no-git"],
            text=True, capture_output=True,
        ).stdout
        self.assertIn("## Freshness", out)
        self.assertIn("Work plan is as of 2026-11-25 (25 days old)", out)

    def test_unreadable_as_of_date(self):
        project(self.root)
        plan = self.root / "work_tracker/work_plan.md"
        plan.write_text(plan.read_text(encoding="utf-8").replace("2026-11-25", "2026-02-30"), encoding="utf-8")
        result = run(self.root, "--no-git")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("## Freshness", result.stdout)
        self.assertIn("Work plan has an unreadable date (As of: 2026-02-30)", result.stdout)

    def test_word_cap_marks_cut(self):
        write(self.root / "work_tracker/work_plan.md", "# Plan\n\n" + "word " * 2000 + "\n\n## Next\n")
        out = load(self.root, "--no-git")
        self.assertIn("cut; grep work_tracker/work_plan.md for the rest", out)
        self.assertLess(out.count("word"), 450)

    def test_hard_cap_names_cut_sections(self):
        project(self.root)
        for n in range(200):
            adr(self.root / "docs/decisions", f"{n + 10:04d}", f"Decision number {n} with a long title", "Accepted")
        result = run(self.root, "--no-git", "--max-chars", "1500")
        self.assertEqual(result.returncode, 0)
        self.assertLessEqual(len(result.stdout.rstrip("\n")), 1500)
        self.assertIn("load cut at 1,500 characters", result.stdout)
        self.assertIn("Sections dropped:", result.stdout)
        self.assertIn("Not loaded", result.stdout.split("Sections dropped:", 1)[1])

    def test_hard_cap_keeps_draft_warning(self):
        project(self.root)
        lines = "\n".join(f"- Decision {n} stays in force (ADR-0002)" for n in range(400))
        write(self.root / "docs/decisions/IN-FORCE.md", f"# Map\n\nDRAFT: unchecked\n\n## In force\n{lines}\n")
        result = run(self.root, "--no-git", "--max-chars", "2500")
        self.assertLessEqual(len(result.stdout.rstrip("\n")), 2500)
        self.assertIn("Kept warning: DRAFT: unchecked", result.stdout)

    def test_open_reviews_listed_by_name(self):
        project(self.root)
        write(self.root / ".agent-bridge/active/rvw-1.md", "secret transcript\n")
        out = load(self.root, "--no-git")
        self.assertIn("- rvw-1.md", out)
        self.assertNotIn("secret transcript", out)

    def test_bad_arguments(self):
        self.assertEqual(run(self.root, "--max-chars", "10").returncode, 2)
        bad = subprocess.run([sys.executable, "-I", str(SCRIPT), "--root", str(self.root / "missing")],
                             text=True, capture_output=True)
        self.assertEqual(bad.returncode, 2)
        bad_date = subprocess.run([sys.executable, "-I", str(SCRIPT), "--root", str(self.root), "--date", "2026-02-30"],
                                  text=True, capture_output=True)
        self.assertEqual(bad_date.returncode, 2)

    def test_read_only(self):
        project(self.root)
        before = {p: p.stat().st_mtime_ns for p in self.root.rglob("*")}
        load(self.root, "--no-git")
        after = {p: p.stat().st_mtime_ns for p in self.root.rglob("*")}
        self.assertEqual(before, after)


def git(root: Path, *args: str) -> str:
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")
    return subprocess.run(["git", "-C", str(root), *args], check=True, text=True,
                          capture_output=True, env=env).stdout


class RepositorySectionTests(unittest.TestCase):
    def test_branches_stash_and_dirty(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            project(root)
            git(root, "add", ".")
            git(root, "commit", "-q", "-m", "base")
            git(root, "branch", "already-merged")
            git(root, "checkout", "-q", "-b", "feature-open")
            (root / "f.txt").write_text("x\n")
            git(root, "add", "f.txt")
            git(root, "commit", "-q", "-m", "feature")
            git(root, "checkout", "-q", "main")
            (root / "work_tracker/backlog.md").write_text("stash me\n")
            git(root, "stash", "push", "-q", "-u")
            (root / "scratch.txt").write_text("dirty\n")
            status_before = git(root, "status", "--porcelain")
            out = load(root)
            self.assertIn("On `main`; 1 uncommitted path(s); 1 stash(es); default branch `main`", out)
            self.assertIn("`feature-open`", out)
            self.assertNotIn("`already-merged`", out)
            self.assertIn("1 other local branch(es) fully contained in `main`", out)
            self.assertEqual(git(root, "status", "--porcelain"), status_before)
            self.assertNotIn("## Repository", load(root, "--no-git"))

    def test_not_a_repository_skips_section(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project(root)
            env_out = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), "--root", str(root), "--date", "2026-11-27"],
                text=True, capture_output=True, env=dict(os.environ, GIT_CEILING_DIRECTORIES=str(root.parent)),
            )
            self.assertEqual(env_out.returncode, 0)
            self.assertNotIn("## Repository", env_out.stdout)


if __name__ == "__main__":
    unittest.main()
