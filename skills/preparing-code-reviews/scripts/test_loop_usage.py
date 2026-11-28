"""Unit tests for loop_usage.py, the review loop's usage record.

Run it in isolated mode, as a file or through discovery:

    python3 -I skills/preparing-code-reviews/scripts/test_loop_usage.py
    python3 -I -m unittest discover -s skills/preparing-code-reviews/scripts
"""
import contextlib
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location("loop_usage", Path(__file__).resolve().parent / "loop_usage.py")
loop_usage = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(loop_usage)


def result_json(text="ok", cost=0.5, ok=True, **extra):
    out = {"type": "result", "subtype": "success" if ok else "error_during_execution", "is_error": not ok,
           "num_turns": 2, "duration_ms": 9, "session_id": "s1", "total_cost_usd": cost,
           "modelUsage": {"model-a": {"inputTokens": 3, "cacheReadInputTokens": 30,
                                      "cacheCreationInputTokens": 6, "outputTokens": 2}}}
    if ok:
        out["result"] = text
    out.update(extra)
    return json.dumps(out)


class LoopUsageTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.dir)

    def write(self, name, text):
        (self.dir / name).write_text(text)
        return self.dir / name

    def run_cmd(self, *argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            rc = loop_usage.main([str(a) for a in argv])
        return rc, buf.getvalue()

    # result --------------------------------------------------------------
    def test_result_copies_the_json_answer(self):
        attempt = self.write("r.md.1.out", result_json("COUNTS: BLOCK 0 FIX 0 SUGGEST 0"))
        rc, _ = self.run_cmd("result", attempt, self.dir / "r.md")
        self.assertEqual(rc, 0)
        self.assertEqual((self.dir / "r.md").read_text(), "COUNTS: BLOCK 0 FIX 0 SUGGEST 0")

    def test_result_without_an_answer_exits_1(self):
        for name, body in (("empty", ""), ("text", "Error: crashed"), ("error", result_json(ok=False)),
                           ("other-json", json.dumps({"type": "assistant", "result": "x"}))):
            with self.subTest(name):
                attempt = self.write(f"{name}.md.1.out", body)
                rc, _ = self.run_cmd("result", attempt, self.dir / f"{name}.md")
                self.assertEqual(rc, 1)
                self.assertEqual((self.dir / f"{name}.md").read_text(), "")

    def test_raw_result_is_the_whole_output(self):
        attempt = self.write("r.md.1.out", "- a-1 [FIX] x.py:1\nCOUNTS: BLOCK 0 FIX 1 SUGGEST 0\n")
        rc, _ = self.run_cmd("result", "--raw", attempt, self.dir / "r.md")
        self.assertEqual(rc, 0)
        self.assertIn("COUNTS:", (self.dir / "r.md").read_text())

    # summary -------------------------------------------------------------
    def test_summary_totals_attempts_in_numeric_order(self):
        for n in range(1, 11):
            self.write(f"a.md.{n}.out", result_json(cost=0.1))
        self.write("a.md", "answer")
        self.write("a.md.err", "")
        self.write("notes.txt.1.out", result_json())  # not a report attempt
        rc, out = self.run_cmd("summary", self.dir)
        self.assertEqual(rc, 0)
        usage = json.loads((self.dir / "usage.json").read_text())
        self.assertEqual([a["attempt"] for a in usage["attempts"]], list(range(1, 11)))
        self.assertEqual(usage["totals"]["retries"], 9)
        self.assertEqual(usage["totals"]["cost_estimate_usd"], 1.0)
        self.assertEqual(usage["totals"]["tokens_by_model"]["model-a"],
                         {"input": 30, "cache_read": 300, "cache_write": 60, "output": 20})
        self.assertTrue(out.startswith("USAGE: attempts 10, sessions 1, retried 9, no telemetry 0; estimated $1.00;"))

    def test_summary_accepts_snake_case_and_counts_missing_telemetry(self):
        snake = {"type": "result", "subtype": "success", "result": "x", "total_cost_usd": 0.25,
                 "model_usage": {"model-b": {"input_tokens": 1, "output_tokens": 4}}}
        self.write("a.md.1.out", json.dumps(snake))
        self.write("b.md.1.out", "")
        self.write("c.md.1.out", json.dumps({"type": "result", "result": "no cost fields"}))
        rc, out = self.run_cmd("summary", self.dir)
        self.assertEqual(rc, 0)
        usage = json.loads((self.dir / "usage.json").read_text())
        self.assertEqual([a["telemetry"] for a in usage["attempts"]], ["present", "missing", "missing"])
        self.assertEqual(usage["totals"]["tokens_by_model"]["model-b"],
                         {"input": 1, "cache_read": 0, "cache_write": 0, "output": 4})
        self.assertIn("no telemetry 2; estimated $0.25", out)

    def test_summary_of_an_empty_folder(self):
        rc, out = self.run_cmd("summary", self.dir)
        self.assertEqual(rc, 0)
        self.assertIn("attempts 0", out)
        self.assertIn("models: none", out)

    # unavailable ---------------------------------------------------------
    def test_unavailable_reads_only_the_latest_attempt(self):
        report = self.dir / "r.md"
        self.write("r.md.1.out", "")
        self.write("r.md.1.err", "Error: model x-1 is unavailable")
        self.write("r.md.2.out", result_json(ok=False))
        self.write("r.md.2.err", "connection reset")
        self.assertEqual(self.run_cmd("unavailable", report)[0], 1)
        self.write("r.md.3.out", result_json(ok=False, errors=["Model x-1 not found"]))
        self.assertEqual(self.run_cmd("unavailable", report)[0], 0)

    def test_unavailable_ignores_a_successful_answer_that_mentions_models(self):
        self.write("r.md.1.out", result_json("the model is not available in region b, says the doc"))
        self.assertEqual(self.run_cmd("unavailable", self.dir / "r.md")[0], 1)

    def test_unavailable_with_no_attempts(self):
        self.assertEqual(self.run_cmd("unavailable", self.dir / "r.md")[0], 1)

    def test_bad_arguments_exit_2(self):
        for argv in ((), ("nope",), ("summary",), ("result", "only-one")):
            with self.subTest(argv=argv):
                self.assertEqual(self.run_cmd(*argv)[0], 2)


if __name__ == "__main__":
    unittest.main()
