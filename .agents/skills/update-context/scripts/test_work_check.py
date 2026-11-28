"""Tests for work_check.py: each test builds a project (and, for close, a git repo) in a temp dir."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parent / "work_check.py"
WID = "2026-11-20-retry-api"
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
           GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")

MANIFEST = """\
project:
  name: "orders-service"
  orientation: ["AGENTS.md"]
layers:
  - id: decisions
    path: docs/decisions/
  - id: work-plan
    path: tracker/work_plan.md
  - id: work-tracker
    path: tracker/
"""


def put(path: Path, text: str = "x\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, text=True, capture_output=True, env=ENV).stdout


class Base(unittest.TestCase):
    subdir = ""     # the project root's path inside the temp dir (and, for close, inside the git repo)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.root = self.repo / self.subdir
        put(self.root / "context-manifest.yaml", MANIFEST)
        put(self.root / "AGENTS.md", "# Orientation\n")
        put(self.root / "tracker/work_plan.md", "# Plan\n\n## Owner items\n")
        self.folder = self.root / "tracker/work" / WID
        put(self.folder / "BRIEF.md", "brief\n")
        put(self.folder / "STATUS.md", "STATUS: DONE: abc123\n")
        put(self.folder / "channel/read/MSG-1.md")
        put(self.folder / "passes/2026-11-21-pass-1/report.md")
        put(self.folder / "scratch/STATE.md", "short\n")
        put(self.folder / "latency-report.md", "p99 numbers\n")

    def tearDown(self):
        self.temp.cleanup()

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "-I", str(SCRIPT), *args, "--root", str(self.root)],
                              text=True, capture_output=True, env=ENV)

    def cite_report(self) -> None:
        put(self.root / "docs/decisions/0001-retry.md",
            f"# ADR-0001: Retry\n\nRetries cap at 5 (source: work/{WID}/latency-report.md)\n")


class CheckTests(Base):
    def test_clean_project(self):
        self.cite_report()
        result = self.run_script("check")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "OK no work-folder findings")

    def test_each_check_class(self):
        put(self.root / "STATUS.md")                              # misplaced at the project root
        put(self.root / "tracker/work/notes.md")                  # loose file in work/
        put(self.root / "tracker/work/retry-stuff/x.md")          # bad folder name
        put(self.folder / "MSG-2.md")                             # message outside channel/
        put(self.folder / "scratch/STATE.md", "line\n" * 45)      # state over 40 lines
        put(self.root / "tracker/work/archive/2026-11-01-old/r.md")
        put(self.root / "tracker/work/2026-11-01-old/r.md")       # id open and archived
        put(self.root / "docs/decisions/0002-x.md",
            "# ADR-0002\n\n"
            "See [the plan](../../tracker/missing.md) and [site](https://example.com) and [top](#x).\n"
            "Raw data was in /tmp/run-42/out.csv\n"
            f"Linked [report](../../tracker/work/{WID}/latency-report.md)\n"
            "Cited (source: work/2026-10-01-gone/report.md)\n"
            f"Cited (source: work/{WID}/nope.md)\n"
            "Cited (source: work/not-an-id/x.md)\n"
            "```\n[ignored](nowhere.md) /tmp/in-fence\n```\n"
            "Template `[x](nowhere.md)` and [doc](<link>)\n")
        lines = self.run_script("check").stdout.splitlines()
        kinds = [line.split()[1] for line in lines]
        for kind, count in {"misplaced": 3, "bad-folder-name": 1, "state-too-long": 1, "id-twice": 1,
                            "dead-link": 1, "tmp-path": 1, "work-link": 1, "unresolved-cite": 2, "bad-cite": 1}.items():
            with self.subTest(kind=kind):
                self.assertEqual(kinds.count(kind), count, lines)
        self.assertIn(f"FIX tmp-path docs/decisions/0002-x.md:4 /tmp/run-42/out.csv", "\n".join(lines))
        self.assertFalse(any("nowhere.md" in line or "in-fence" in line for line in lines))

    def test_archived_cite_resolves(self):
        archived = self.root / "tracker/work/archive" / WID
        archived.parent.mkdir(parents=True)
        self.folder.rename(archived)
        self.cite_report()
        self.assertEqual(self.run_script("check").stdout.strip(), "OK no work-folder findings")

    def test_extra_home_is_scanned(self):
        put(self.root / "design/retry.md", "Uses (source: work/2026-10-01-gone/x.md)\n")
        self.assertNotIn("design/retry.md", self.run_script("check").stdout)
        self.assertIn("FIX unresolved-cite design/retry.md:1", self.run_script("check", "--home", "design").stdout)


class HandoffTests(Base):
    def test_missing_handoff_file(self):
        result = self.run_script("handoff", WID)
        self.assertEqual(result.returncode, 1)
        self.assertIn("MISSING tracker/work/2026-11-20-retry-api/HANDOFF.md", result.stdout)

    def test_names_unlanded_results_only(self):
        put(self.folder / "HANDOFF.md", "Goal: retry\nNot yet home: notes/draft.md -> tracker/work_plan.md\n")
        put(self.folder / "notes/draft.md")
        put(self.folder / "DECISION-1.md")
        result = self.run_script("handoff", WID)
        self.assertEqual(result.returncode, 1)
        out = result.stdout
        self.assertIn("latency-report.md", out)
        self.assertIn("DECISION-1.md", out)
        self.assertNotIn("draft.md", out)
        self.assertNotIn("passes/", out)
        self.assertNotIn("BRIEF.md", out)

    def test_ok_when_cited_or_named(self):
        self.cite_report()
        put(self.folder / "HANDOFF.md", f"Pending: work/{WID}/extra.md\n")
        put(self.folder / "extra.md")
        result = self.run_script("handoff", WID)
        self.assertEqual((result.returncode, result.stdout.strip()), (0, "OK"))

    def test_folder_cite_covers_everything(self):
        put(self.root / "tracker/work_plan.md", f"- [ ] follow up (source: work/{WID}/)\n")
        put(self.folder / "HANDOFF.md", "nothing\n")
        put(self.folder / "deep/a/b.md")
        self.assertEqual(self.run_script("handoff", WID).stdout.strip(), "OK")

    def test_unknown_folder(self):
        self.assertEqual(self.run_script("handoff", "2026-01-01-nothing").returncode, 2)


class CloseTests(Base):
    def setUp(self):
        super().setUp()
        git(self.root, "init", "-q", "-b", "main")
        put(self.root / ".gitignore", "*.bin\n")
        git(self.root, "add", "context-manifest.yaml", "AGENTS.md", ".gitignore", "tracker/work_plan.md",
            f"tracker/work/{WID}/latency-report.md", f"tracker/work/{WID}/passes")
        git(self.root, "commit", "-q", "-m", "seed")

    def test_refusals(self):
        put(self.folder / "STATUS.md", "STATUS: WORKING\n")
        put(self.folder / "OWNER-STEP-1.md", "prompt\n")
        put(self.folder / "dump.json", "x" * 1_000_001)
        put(self.folder / "ok.bin", "x" * 1_000_001)          # ignored by git: allowed
        put(self.folder / "channel/big.md", "x" * 1_000_001)  # never committed: allowed
        put(self.root / "tracker/work_plan.md", f"[r](work/{WID}/latency-report.md)\n")
        result = self.run_script("close", WID, "--session", "w1")
        self.assertEqual(result.returncode, 1)
        kinds = sorted(line.split()[1] for line in result.stdout.splitlines())
        self.assertEqual(kinds, ["large", "not-done", "owner-step-open", "uncited", "uncited", "uncited", "work-link"])
        self.assertNotIn("ok.bin", result.stdout.split("large", 1)[1].splitlines()[0])
        self.assertTrue(self.folder.is_dir())

    def test_dry_run_then_close(self):
        self.cite_report()
        git(self.root, "add", "docs")
        git(self.root, "commit", "-q", "-m", "cite")
        put(self.root / "other-worker.txt", "staged by someone else\n")
        git(self.root, "add", "other-worker.txt")
        dry = self.run_script("close", WID, "--session", "w1", "--dry-run")
        self.assertEqual(dry.returncode, 0, dry.stdout)
        self.assertTrue(dry.stdout.startswith("WOULD-CLOSE"))
        self.assertTrue(self.folder.is_dir())
        result = self.run_script("close", WID, "--session", "w1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(result.stdout.startswith(f"CLOSED tracker/work/{WID} -> tracker/work/archive/{WID}"))
        archived = self.root / "tracker/work/archive" / WID
        self.assertFalse(self.folder.exists())
        self.assertTrue((archived / "latency-report.md").is_file())
        self.assertTrue((archived / "BRIEF.md").is_file())
        self.assertEqual(git(self.root, "log", "-1", "--format=%s"), f"[w1] close work/{WID}\n")
        files = git(self.root, "show", "--name-only", "--format=", "HEAD").split()
        self.assertIn(f"tracker/work/archive/{WID}/latency-report.md", files)
        self.assertIn(f"tracker/work/archive/{WID}/scratch/STATE.md", files)
        self.assertNotIn(f"tracker/work/archive/{WID}/BRIEF.md", files)
        self.assertFalse(any("channel" in f or "STATUS.md" in f for f in files))
        self.assertNotIn("other-worker.txt", files)
        tracked = git(self.root, "ls-files").split()
        self.assertNotIn(f"tracker/work/{WID}/latency-report.md", tracked)
        self.assertIn(f"tracker/work/archive/{WID}/latency-report.md", tracked)
        self.assertIn("A  other-worker.txt", git(self.root, "status", "--porcelain"))
        self.assertEqual(self.run_script("check").stdout.strip(), "OK no work-folder findings")

    def test_failed_commit_restores_folder(self):
        self.cite_report()
        hook = put(self.root / ".git/hooks/pre-commit", "#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        result = self.run_script("close", WID, "--session", "w1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("REFUSE git-failed", result.stdout)
        self.assertTrue((self.folder / "latency-report.md").is_file())
        self.assertFalse((self.root / "tracker/work/archive" / WID).exists())
        self.assertEqual(git(self.root, "diff", "--cached", "--name-only"), "")

    def test_failed_commit_removes_archive_it_made(self):
        self.cite_report()
        hook = put(self.root / ".git/hooks/pre-commit", "#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        result = self.run_script("close", WID, "--session", "w1")
        self.assertIn("REFUSE git-failed", result.stdout)
        self.assertFalse((self.root / "tracker/work/archive").exists())

    def test_close_folder_with_nothing_tracked(self):
        self.cite_report()
        git(self.root, "rm", "-q", "-r", "--cached", f"tracker/work/{WID}")
        git(self.root, "commit", "-q", "-m", "untrack")
        result = self.run_script("close", WID, "--session", "w1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(result.stdout.startswith("CLOSED"), result.stdout)
        files = git(self.root, "show", "--name-only", "--format=", "HEAD").split()
        self.assertIn(f"tracker/work/archive/{WID}/latency-report.md", files)
        self.assertEqual(git(self.root, "diff", "--cached", "--name-only"), "")

    def test_not_open(self):
        self.assertEqual(self.run_script("close", "2026-01-01-none", "--session", "w1").returncode, 2)


class CloseInSubdirectoryTests(Base):
    """--root is a subdirectory of the git repo: git prints repo-top paths unless asked not to."""

    subdir = "svc"

    def setUp(self):
        super().setUp()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "add", "svc/context-manifest.yaml", "svc/AGENTS.md", "svc/tracker/work_plan.md",
            f"svc/tracker/work/{WID}/latency-report.md", f"svc/tracker/work/{WID}/passes")
        git(self.repo, "commit", "-q", "-m", "seed")
        self.cite_report()
        git(self.repo, "add", "svc/docs")
        git(self.repo, "commit", "-q", "-m", "cite")

    def test_close_commits_exactly_the_moved_paths(self):
        result = self.run_script("close", WID, "--session", "w1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(result.stdout.startswith(f"CLOSED tracker/work/{WID} -> tracker/work/archive/{WID}"))
        files = sorted(git(self.repo, "show", "--no-renames", "--name-only", "--format=", "HEAD").split())
        moved = [f"tracker/work/{WID}/{p}" for p in ("latency-report.md", "passes/2026-11-21-pass-1/report.md")]
        expected = sorted([f"svc/{p}" for p in moved]
                          + [f"svc/tracker/work/archive/{WID}/{p}" for p in
                             ("latency-report.md", "passes/2026-11-21-pass-1/report.md", "scratch/STATE.md")])
        self.assertEqual(files, expected)
        self.assertEqual(git(self.repo, "diff", "--cached", "--name-only"), "")

    def test_failed_commit_leaves_index_empty(self):
        hook = put(self.repo / ".git/hooks/pre-commit", "#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        result = self.run_script("close", WID, "--session", "w1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("REFUSE git-failed", result.stdout)
        self.assertNotIn("rollback-failed", result.stdout)
        self.assertTrue((self.folder / "latency-report.md").is_file())
        self.assertEqual(git(self.repo, "diff", "--cached", "--name-only"), "")


if __name__ == "__main__":
    unittest.main()
