"""Unit tests for review-loop.sh.

Covered: the per-brief lens sessions (concurrent, then concatenated), the
challenge and defense stages, how briefs are discovered, the single retry of a
failed session, and the exit statuses 1 and 2.

Run it in isolated mode, as a file (isolated mode leaves the working directory
off sys.path, so `-m unittest` would not find it):

    python3 -I skills/preparing-code-reviews/scripts/test_review_loop.py

No real reviewer is ever called: a fake `claude` placed first on PATH answers
every session and logs the prompt and argv it was given.
"""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

LOOP_SCRIPT = Path(__file__).resolve().parent / "review-loop.sh"

# Fake reviewer. Behaviour switches (all optional, read from the environment):
#   FAIL_LENS / FAIL_TIMES  that lens exits 1 on its first FAIL_TIMES attempts
#   EMPTY_LENS              that lens answers once without a COUNTS line
#   SLOW_LENS               that lens sleeps a second before answering
FAKE_REVIEWER = r"""#!/usr/bin/env bash
prompt="${@: -1}"
log="$CALLS/$(date +%s)-$$-$RANDOM"
printf '%s' "$prompt" > "$log.txt"
printf '%s\n' "$@" > "$log.args"
if [[ "$prompt" == "TASK: lens review ["* ]]; then
  lens=${prompt#TASK: lens review [}; lens=${lens%%]*}
  echo "start $lens" >> "$CALLS/timeline"
  [ "${SLOW_LENS:-}" = "$lens" ] && sleep 1
  echo "end $lens" >> "$CALLS/timeline"
  if [ "${FAIL_LENS:-}" = "$lens" ]; then
    tries=$(ls "$CALLS" | grep -c "^fail-$lens-")
    if [ "$tries" -lt "${FAIL_TIMES:-1}" ]; then
      touch "$CALLS/fail-$lens-$tries"; echo "rate limited" >&2; exit 1
    fi
  fi
  if [ "${EMPTY_LENS:-}" = "$lens" ] && [ ! -e "$CALLS/empty-$lens" ]; then
    touch "$CALLS/empty-$lens"; echo "nothing useful"; exit 0
  fi
  printf -- '- %s-1 [FIX] src/app.py:3\nCOUNTS: BLOCK 0 FIX 1 SUGGEST 0\n' "$lens"
elif [[ "$prompt" == "TASK: challenge."* ]]; then
  printf 'alpha-1: HOLDS quote matches\n'
else
  printf 'COUNTS: BLOCK 0 FIX 1 SUGGEST 0\nVerdict: READY-WITH-FIXES\n'
fi
"""


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=tester", "-c", "user.email=tester@example.com",
                    *args], check=True, capture_output=True)


class ReviewLoopScriptTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        skills = self.root / "skills"
        script_dir = skills / "preparing-code-reviews" / "scripts"
        script_dir.mkdir(parents=True)
        self.script = script_dir / "review-loop.sh"
        shutil.copy(LOOP_SCRIPT, self.script)

        self.cr_refs = skills / "code-review" / "references"
        self.cr_refs.mkdir(parents=True)
        (skills / "code-review" / "SKILL.md").write_text("review contract\n")
        (self.cr_refs / "_brief-template.md").write_text("template only\n")
        for lens in ("alpha", "beta"):
            (self.cr_refs / f"lens-{lens}.md").write_text(f"the {lens} lens\n")

        self.repo = self.root / "orders-service"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "commit", "-q", "--allow-empty", "-m", "initial")
        git(self.repo, "branch", "base")
        git(self.repo, "commit", "-q", "--allow-empty", "-m", "add retry")

        self.desc = self.root / "description.md"
        self.desc.write_text("what and why\n")
        self.spec = self.root / "spec.md"
        self.spec.write_text("the spec\n")
        self.adr = self.root / "0007-retries.md"
        self.adr.write_text("decided\n")

        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        fake = bin_dir / "claude"
        fake.write_text(FAKE_REVIEWER)
        fake.chmod(0o755)
        self.bin_dir = bin_dir
        self.calls = self.root / "calls"
        self.calls.mkdir()
        self.loop_dir = self.root / "loop-1"

        env = dict(os.environ)
        for var in ("REVIEW_CMD", "REVIEW_BRIEFS", "REGISTER", "DECLINED", "CODE_REVIEW_DIR"):
            env.pop(var, None)
        env.update(PATH=f"{bin_dir}:{env['PATH']}", CALLS=str(self.calls),
                   REVIEW_RETRY_PAUSE="0", DECISIONS=str(self.adr))
        self.env = env

    def tearDown(self):
        shutil.rmtree(self.root)

    # helpers -------------------------------------------------------------
    def loop(self, env_overrides=None, spec=None, precedent_dirs=(), base="base"):
        env = dict(self.env, **(env_overrides or {}))
        argv = ["bash", str(self.script), str(self.loop_dir), str(self.repo), base,
                str(self.desc), str(spec or self.spec), *precedent_dirs]
        return subprocess.run(argv, env=env, capture_output=True, text=True)

    def all_prompts(self):
        logs = sorted(self.calls.glob("*.txt"), key=os.path.getmtime)
        return [p.read_text() for p in logs]

    def lens_prompts(self):
        return [p for p in self.all_prompts() if p.startswith("TASK: lens review [")]

    def first_argv(self):
        return sorted(self.calls.glob("*.args"))[0].read_text().split("\n")

    # the happy path ------------------------------------------------------
    def test_runs_each_lens_then_challenge_then_defense(self):
        result = self.loop()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Verdict: READY-WITH-FIXES", result.stdout)
        prompts = self.all_prompts()
        self.assertEqual(len(prompts), 4)
        lenses = sorted(p.split("]")[0].split("[")[1] for p in self.lens_prompts())
        self.assertEqual(lenses, ["alpha", "beta"])
        self.assertTrue(prompts[2].startswith("TASK: challenge."))
        self.assertTrue(prompts[3].startswith("TASK: defense and verdict."))
        combined = (self.loop_dir / "1-review.md").read_text()
        self.assertLess(combined.index("the alpha lens"), combined.index("the beta lens"))
        self.assertIn("alpha-1", combined)
        self.assertIn("beta-1", combined)

    def test_prompt_carries_brief_spec_decisions_and_ids(self):
        self.loop()
        alpha = [p for p in self.lens_prompts() if p.startswith("TASK: lens review [alpha]")][0]
        self.assertIn(str(self.cr_refs / "lens-alpha.md"), alpha)
        self.assertIn(f"Spec: {self.spec}.", alpha)
        self.assertIn(f"Decisions: {self.adr}", alpha)
        self.assertIn("Overrides register: none.", alpha)
        self.assertIn("id of the form alpha-<n>", alpha)

    def test_spec_dash_means_no_spec(self):
        result = self.loop(spec="-")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Spec: none given", self.all_prompts()[0])

    # brief discovery -----------------------------------------------------
    def test_template_files_are_not_briefs(self):
        self.loop()
        self.assertFalse(any("_brief-template" in p for p in self.lens_prompts()))

    def test_falls_back_to_plain_reference_files_without_lens_files(self):
        for f in self.cr_refs.glob("lens-*.md"):
            f.unlink()
        (self.cr_refs / "layering.md").write_text("layering rules\n")
        (self.cr_refs / "register.md").write_text("register format\n")
        result = self.loop()
        self.assertEqual(result.returncode, 0, result.stderr)
        lens_prompts = self.lens_prompts()
        self.assertEqual(len(lens_prompts), 1)
        self.assertTrue(lens_prompts[0].startswith("TASK: lens review [layering]"))

    def test_review_briefs_variable_replaces_discovery(self):
        brief = self.root / "auth-boundaries.md"
        brief.write_text("auth\n")
        result = self.loop({"REVIEW_BRIEFS": str(brief)})
        self.assertEqual(result.returncode, 0, result.stderr)
        lens_prompts = self.lens_prompts()
        self.assertEqual(len(lens_prompts), 1)
        self.assertIn(str(brief), lens_prompts[0])

    # reviewer command ----------------------------------------------------
    def test_default_reviewer_is_read_only_with_scoped_dirs(self):
        self.loop({"REGISTER": str(self.adr)})
        argv = self.first_argv()
        self.assertEqual(argv[0], "-p")
        self.assertIn("dontAsk", argv)
        for tool in ("Edit", "Write"):
            self.assertNotIn(tool, argv)
        granted = {argv[i + 1] for i, a in enumerate(argv) if a == "--add-dir"}
        for expected in (self.repo, self.loop_dir, self.adr.parent, self.cr_refs.parent):
            self.assertIn(str(expected), granted)

    def test_review_cmd_swaps_in_another_agent(self):
        other = self.bin_dir / "another-agent"
        other.write_text(FAKE_REVIEWER)
        other.chmod(0o755)
        result = self.loop({"REVIEW_CMD": f"{other} exec --sandbox read-only"})
        self.assertEqual(result.returncode, 0, result.stderr)
        argv = self.first_argv()
        self.assertEqual(argv[:3], ["exec", "--sandbox", "read-only"])
        self.assertNotIn("--add-dir", argv)

    def test_precedent_checkouts_are_named_and_granted(self):
        clone = self.root / "webhook-dispatcher"
        clone.mkdir()
        result = self.loop(precedent_dirs=[str(clone)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"Precedent checkouts, read-only: {clone}.", self.lens_prompts()[0])
        argv = self.first_argv()
        granted = {argv[i + 1] for i, a in enumerate(argv) if a == "--add-dir"}
        self.assertIn(str(clone), granted)

    # retries -------------------------------------------------------------
    def test_failing_lens_gets_one_retry(self):
        result = self.loop({"FAIL_LENS": "beta"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.all_prompts()), 5)
        self.assertIn("rate limited", (self.loop_dir / "1-review-beta.md.err").read_text())

    def test_lens_output_without_counts_gets_one_retry(self):
        result = self.loop({"EMPTY_LENS": "alpha"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.all_prompts()), 5)
        self.assertIn("COUNTS:", (self.loop_dir / "1-review-alpha.md").read_text())

    def test_second_failure_stops_with_exit_1(self):
        result = self.loop({"FAIL_LENS": "beta", "FAIL_TIMES": "2"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("failed on retry", result.stderr)
        self.assertFalse((self.loop_dir / "2-challenge.md").exists())

    def test_retry_waits_for_all_first_attempts(self):
        result = self.loop({"FAIL_LENS": "beta", "SLOW_LENS": "alpha"})
        self.assertEqual(result.returncode, 0, result.stderr)
        timeline = (self.calls / "timeline").read_text().splitlines()
        beta_starts = [i for i, event in enumerate(timeline) if event == "start beta"]
        self.assertEqual(len(beta_starts), 2)
        self.assertGreater(beta_starts[1], timeline.index("end alpha"))

    # input errors (exit 2, no session started) ---------------------------
    def assert_input_error(self, result, message):
        self.assertEqual(result.returncode, 2)
        self.assertIn(message, result.stderr)
        self.assertEqual(self.all_prompts(), [])

    def test_absent_decision_file(self):
        self.assert_input_error(self.loop({"DECISIONS": str(self.root / "missing-adr.md")}), "not found:")

    def test_absent_register(self):
        self.assert_input_error(self.loop({"REGISTER": str(self.root / "missing-register.md")}), "not found:")

    def test_no_briefs_at_all(self):
        for f in self.cr_refs.glob("lens-*.md"):
            f.unlink()
        self.assert_input_error(self.loop(), "no review briefs found")

    def test_base_that_is_not_a_commit(self):
        self.assert_input_error(self.loop(base="no-such-ref"), "base is not a commit")

    def test_precedent_checkout_that_is_not_a_directory(self):
        self.assert_input_error(self.loop(precedent_dirs=[str(self.root / "webhook-dispatcher")]),
                                "precedent checkout is not a directory")

    def test_too_few_arguments(self):
        result = subprocess.run(["bash", str(self.script)], env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)


if __name__ == "__main__":
    unittest.main()
