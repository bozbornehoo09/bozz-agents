"""Tests for extract_comments.py. Each test builds a throwaway git repository.

Run from the repository root:
    python3 -I -m unittest discover -s skills/refining-technical-writing/scripts
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "extract_comments.py"

GIT_IDENTITY = ("-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                "-c", "commit.gpgsign=false")

# A Java file with a doc block, a line comment, an end-of-line comment, a `//` inside a string
# and a one-line block comment in front of code.
INVOICE_JAVA = "\n".join([
    "package invoices;",
    "",
    "/**",
    " * Renders one page of {@code Invoice} rows.",
    " *",
    " * @param page the page number",
    " * @return the rendered rows",
    " */",
    "class Renderer {",
    "    // Matches the printer's page height.",
    "    static final int ROWS = 40;",
    '    String api = "https://api.example.net/v2"; // printer gateway',
    '    String glyph = "a // b";',
    "    /* one liner */ int k = 0;",
    "}",
    "",
])


class Sandbox:
    """A scratch repository that starts with one commit."""

    def __init__(self, where):
        self.dir = Path(where)
        self.git("init", "-q")
        self.write("NOTES.txt", "start\n")
        self.commit("start")

    def git(self, *args):
        done = subprocess.run(["git", "-C", str(self.dir), *GIT_IDENTITY, *args],
                              capture_output=True, text=True, check=True)
        return done.stdout

    def write(self, rel, content):
        path = self.dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content)

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "--short", "HEAD").strip()


class Result:
    def __init__(self, proc, extract):
        self.code, self.out, self.err, self.extract = (proc.returncode, proc.stdout,
                                                      proc.stderr, extract)

    def flagged(self, prefix):
        return [line for line in self.out.splitlines() if line.startswith(prefix)]


def run_tool(box, *args, with_out=True):
    extra = []
    target = box.dir / "comments.md"
    if with_out:
        extra = ["--out", str(target)]
    proc = subprocess.run([sys.executable, "-I", str(TOOL), str(box.dir), *args, *extra],
                          capture_output=True, text=True)
    extract = target.read_text() if target.exists() else ""
    return Result(proc, extract)


class ExtractTestCase(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.box = Sandbox(scratch.name)


class SlashFamily(ExtractTestCase):
    def test_java_blocks_keep_their_new_line_numbers(self):
        self.box.write("app/Renderer.java", INVOICE_JAVA)
        sha = self.box.commit("renderer")
        got = run_tool(self.box, sha)
        self.assertEqual(0, got.code, got.out + got.err)
        self.assertTrue(got.extract.startswith("# Comments added by %s in %s" % (
            sha, self.box.dir.name)), got.extract[:80])
        doc = ("## app/Renderer.java:3-8\n\nRenders one page of `Invoice` rows.\n\n"
               "@param page the page number\n\n@return the rendered rows\n")
        self.assertIn(doc, got.extract)
        self.assertIn("## app/Renderer.java:10-10\n\nMatches the printer's page height.\n",
                      got.extract)
        self.assertIn("## app/Renderer.java:12-12 (trailing)\n\nprinter gateway\n", got.extract)
        self.assertIn("## app/Renderer.java:14-14\n\none liner\n", got.extract)
        self.assertNotIn("api.example.net", got.extract)
        self.assertNotIn("a // b", got.extract)
        self.assertIn("extract_comments: 4 comment blocks; 0 lines", got.out)

    def test_go_line_and_rust_triple_slash(self):
        self.box.write("svc/main.go", "package main\n\n// Two retries cover one failover.\n"
                                      "var retries = 2\n")
        self.box.write("core/lib.rs", "/// Never touches the heap.\nfn scan() {}\n")
        got = run_tool(self.box, self.box.commit("go and rust"))
        self.assertIn("## svc/main.go:3-3\n\nTwo retries cover one failover.\n", got.extract)
        self.assertIn("## core/lib.rs:1-1\n\nNever touches the heap.\n", got.extract)

    def test_new_line_inside_an_older_doc_block_still_counts(self):
        self.box.write("K.java", "/**\n * First.\n */\nclass K {\n}\n")
        self.box.commit("k")
        self.box.write("K.java", "/**\n * First.\n * Second.\n */\nclass K {\n"
                                 "    long area = 6\n        * 7;\n"
                                 "    boolean q = c == '\"'; // ends the literal\n}\n")
        got = run_tool(self.box, self.box.commit("k2"))
        self.assertIn("## K.java:3-3\n\nSecond.\n", got.extract)
        self.assertNotIn("* 7", got.extract)  # an operator continuation line is code
        self.assertIn("## K.java:8-8 (trailing)\n\nends the literal\n", got.extract)


class HashFamily(ExtractTestCase):
    def test_yaml_and_python_count_while_markdown_and_shebang_do_not(self):
        self.box.write("deploy.yml", "# Held back: the next image lacks the arm build.\n"
                                     "image: base:3\n")
        self.box.write("task.py", "#!/usr/bin/env python3\nmark = 'a # b'\n"
                                  "size = 9  # fits a page\n")
        self.box.write("doc.md", "# Title, not a comment\n// also not one\n")
        got = run_tool(self.box, self.box.commit("hash files"))
        self.assertIn("## deploy.yml:1-1\n\nHeld back: the next image", got.extract)
        self.assertIn("## task.py:3-3 (trailing)\n\nfits a page\n", got.extract)
        for absent in ("usr/bin", "a # b", "doc.md"):
            self.assertNotIn(absent, got.extract)

    def test_docstrings_and_heredocs_are_not_comments(self):
        self.box.write("mod.py", '"""Module text.\n# still the docstring\n"""\n'
                                 'word = "isn\'t"  # why\n')
        self.box.write("run.sh", "cat <<'EOF'\n# heredoc line\nEOF\n# actual comment\n")
        got = run_tool(self.box, self.box.commit("strings"))
        self.assertIn("## mod.py:4-4 (trailing)\n\nwhy\n", got.extract)
        self.assertIn("## run.sh:4-4\n\nactual comment\n", got.extract)
        self.assertNotIn("still the docstring", got.extract)
        self.assertNotIn("heredoc line", got.extract)

    def test_here_string_and_quoted_shift_open_no_heredoc(self):
        self.box.write("x.sh", 'tr a b <<< "$s"\n# first\necho "3 << 1"\n# second\n')
        got = run_tool(self.box, self.box.commit("shell"))
        self.assertIn("## x.sh:2-2\n\nfirst\n", got.extract)
        self.assertIn("## x.sh:4-4\n\nsecond\n", got.extract)


class Revisions(ExtractTestCase):
    def test_commit_alone_versus_range(self):
        self.box.write("R.java", "class R {\n    int r;\n}\n")
        base = self.box.commit("r0")
        self.box.write("R.java", "class R {\n    // older note\n    int r;\n}\n")
        self.box.commit("r1")
        self.box.write("R.java", "class R {\n    // older note\n    int r;\n"
                                 "    // newer note\n    int s;\n}\n")
        tip = self.box.commit("r2")
        alone = run_tool(self.box, tip)
        self.assertIn("## R.java:4-4\n\nnewer note", alone.extract)
        self.assertNotIn("older note", alone.extract)
        span = run_tool(self.box, "%s..%s" % (base, tip))
        self.assertIn("## R.java:2-2\n\nolder note", span.extract)
        self.assertIn("## R.java:4-4\n\nnewer note", span.extract)
        self.assertIn("# Comments added by %s..%s in" % (base, tip), span.extract)

    def test_staged_file_is_read_from_the_index(self):
        self.box.write("wait.ts", "// The client stops waiting after 2 s, so answer sooner.\n"
                                  "const limit = 2;\n")
        self.box.git("add", "wait.ts")
        got = run_tool(self.box, "--staged")
        self.assertEqual(0, got.code, got.out + got.err)
        self.assertIn("## wait.ts:1-1\n\nThe client stops waiting after 2 s", got.extract)
        self.assertIn("# Comments added by the staged change", got.extract)

    def test_staged_without_out_lists_violations_on_stdout(self):
        # The call implementing-a-plan makes: no --out, findings on stdout, exit 1.
        self.box.write("Hook.java", "class Hook {\n    // Sized per ADR-12.\n    int h;\n}\n")
        self.box.git("add", "Hook.java")
        got = run_tool(self.box, "--staged", with_out=False)
        self.assertEqual(1, got.code, got.err)
        self.assertEqual(["Hook.java:2: ADR: Sized per ADR-12."], got.flagged("Hook.java:"))
        self.assertIn("extract_comments: 1 comment blocks; 1 lines", got.out)
        self.assertFalse((self.box.dir / "comments.md").exists())

    def test_staged_clean_without_out_exits_0(self):
        self.box.write("ok.py", "# Keeps the batch under the queue's size cap.\nN = 10\n")
        self.box.git("add", "ok.py")
        got = run_tool(self.box, "--staged", with_out=False)
        self.assertEqual(0, got.code, got.out + got.err)

    def test_bad_revision_is_exit_2(self):
        got = run_tool(self.box, "no-such-rev")
        self.assertEqual(2, got.code)
        self.assertIn("extract_comments:", got.err)

    def test_staged_with_a_revision_is_exit_2(self):
        self.assertEqual(2, run_tool(self.box, "HEAD~1", "--staged").code)


class Citations(ExtractTestCase):
    def test_odd_bytes_and_form_feed_keep_numbering(self):
        self.box.write("Z.java", b"class Z {\n    // caf\xe9 \x0c aside\n    int z;\n"
                                 b"    // ADR-8\n}\n")
        got = run_tool(self.box, self.box.commit("bytes"))
        self.assertEqual(1, got.code, got.err)
        self.assertIn("Z.java:4: ADR: ADR-8", got.out)
        self.assertIn("## Z.java:2-2\n", got.extract)

    def test_each_reference_shape_is_flagged(self):
        notes = [
            ("design doc", "Budget comes from the cache LLD."),
            ("design doc", "As the design doc says."),
            ("design doc", "See § 4.2 for the math."),
            ("design doc", "Appendix B has the table."),
            ("ADR", "ADR-021 chose this."),
            ("ADR", "ADR 9 explains the cap."),
            ("pull request", "Came in with MR 81."),
            ("pull request", "See https://github.com/acme/store/pull/77"),
            ("issue", "Tracked as bug #512."),
            ("issue", "https://github.com/acme/store/issues/9"),
            ("issue", "https://acme.atlassian.net/browse/WEB-3"),
            ("doc link", "https://docs.google.com/document/d/abc"),
            ("issue", "Filed as WEB-7781."),
        ]
        lines = ["class Cites {"]
        for i, (_, text) in enumerate(notes):
            lines += ["// " + text, "int f%d;" % i]
        self.box.write("Cites.java", "\n".join(lines + ["}", ""]))
        got = run_tool(self.box, self.box.commit("cites"))
        self.assertEqual(1, got.code)
        expected = ["Cites.java:%d: %s: %s" % (2 + 2 * i, kind, text)
                    for i, (kind, text) in enumerate(notes)]
        self.assertEqual(expected, got.flagged("Cites.java:"))

    def test_people_are_flagged_but_a_bare_todo_is_not(self):
        self.box.write("Who.java", "/**\n * Warms the cache.\n *\n * @author jdoe\n"
                                   " * @param n the size\n */\nclass Who {\n"
                                   "    // TODO(jdoe): drop the adapter.\n"
                                   "    // FIXME(@jdoe) later.\n"
                                   "    // TODO: drop the adapter after the migration.\n"
                                   "    int n;\n}\n")
        got = run_tool(self.box, self.box.commit("who"))
        self.assertEqual(1, got.code)
        self.assertEqual(["Who.java:4: name: @author jdoe",
                          "Who.java:8: name: TODO(jdoe): drop the adapter.",
                          "Who.java:9: name: FIXME(@jdoe) later."], got.flagged("Who.java:"))

    def test_public_standards_and_plain_numbers_pass(self):
        self.box.write("Std.java", "class Std {\n"
                                   "    // UTF-8 text, SHA-256 sums, at most 4000000000 bytes,\n"
                                   "    // dates in RFC-3339, ISO-8601 weeks, MPEG-4 (JDK-8000, "
                                   "PEP-484, CVE-2024-1).\n"
                                   "    // The #2 cost is TLS setup.\n    int s;\n}\n")
        got = run_tool(self.box, self.box.commit("std"))
        self.assertEqual(0, got.code, got.out)


if __name__ == "__main__":
    unittest.main()
