"""Tests for check_prose.py. The live-Vale cases skip unless Vale and the Deslop pack are
installed (bash scripts/install.sh).

Run from the repository root:
    python3 -I -m unittest discover -s skills/refining-technical-writing/scripts
"""

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().with_name("check_prose.py")
_loader = importlib.util.spec_from_file_location("check_prose_under_test", TOOL)
cp = importlib.util.module_from_spec(_loader)
_loader.loader.exec_module(cp)

SHIPPED = cp.Layout.from_environment()
CACHE_TAIL = ("bozz-agents", "refining-technical-writing")
BARE_PATH = "/usr/bin:/bin"
HAVE_VALE = bool(cp.locate_vale(SHIPPED)) and SHIPPED.deslop.is_dir()


def invoke(*args, **env):
    """Run the CLI as a subprocess with extra environment variables."""
    merged = dict(os.environ)
    merged.update(env)
    return subprocess.run([sys.executable, "-I", str(TOOL), *args],
                          capture_output=True, text=True, env=merged)


def scratch(test):
    holder = tempfile.TemporaryDirectory()
    test.addCleanup(holder.cleanup)
    return Path(holder.name)


def put_humanizer(data_home, text, commit="c0ffee12"):
    folder = Path(data_home).joinpath(*CACHE_TAIL, "humanizer")
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(text)
    (folder / "SHA").write_text(commit + "\n")
    return folder


# --- word-lists.md ----------------------------------------------------------------------------

class WordLists(unittest.TestCase):
    def build(self, **override):
        """Text with every required section as a one-term list; None drops a section."""
        sections = {slug: "<!-- kind: list -->\n- `stub`\n" for slug in cp.LIST_SECTIONS}
        sections.update(override)
        return "".join("## %s\n%s\n" % (slug, body)
                       for slug, body in sections.items() if body is not None)

    def test_shipped_file_parses_into_all_sections(self):
        lists = cp.parse_word_lists(cp.read_text(SHIPPED.ref("word-lists.md")))
        self.assertEqual(set(cp.LIST_SECTIONS), set(lists))
        self.assertIsInstance(lists["filler"], list)
        self.assertIsInstance(lists["vague-quantities"], list)
        self.assertEqual("before", lists["phrase-for-word"]["prior to"])
        self.assertNotIn("Wordy", lists["complex-words"])

    def test_every_section_becomes_a_rule_of_the_right_type(self):
        lists = cp.parse_word_lists(cp.read_text(SHIPPED.ref("word-lists.md")))
        rules = cp.vale_rules_from(lists)
        self.assertEqual(len(lists), len(rules))
        self.assertRegex(rules["WordListFiller"], r"^extends: existence\n")
        self.assertRegex(rules["WordListHiddenVerbs"], r"^extends: substitution\n")
        self.assertIn('"make use of": "use"', rules["WordListHiddenVerbs"])

    def test_go_literal_escapes_metacharacters_only(self):
        self.assertEqual(r"x\.y \[z\]\*", cp.go_literal("x.y [z]*"))
        self.assertEqual(r"a\.b \(c\)\?", cp.go_literal("a.b (c)?"))

    def test_missing_section_is_named(self):
        with self.assertRaisesRegex(cp.CheckError, "hidden-verbs"):
            cp.parse_word_lists(self.build(**{"hidden-verbs": None}))

    def test_section_without_kind_marker_fails(self):
        with self.assertRaises(cp.CheckError):
            cp.parse_word_lists(self.build(filler="- `basically`\n"))

    def test_three_cell_row_fails(self):
        table = "<!-- kind: table -->\n| Wordy | Plain |\n|---|---|\n| x | y | z |\n"
        with self.assertRaises(cp.CheckError):
            cp.parse_word_lists(self.build(**{"complex-words": table}))

    def test_table_maps_long_form_to_short(self):
        table = "<!-- kind: table -->\n| Wordy | Plain |\n|---|---|\n| in the event that | if |\n"
        got = cp.parse_word_lists(self.build(**{"phrase-for-word": table}))
        self.assertEqual({"in the event that": "if"}, got["phrase-for-word"])


# --- --against --------------------------------------------------------------------------------

class Preservation(unittest.TestCase):
    Q = cp.QUALIFIERS

    def test_dropped_bound_condition_and_code_span(self):
        before = "Retry at least 3 times via `probe`; do not drop a shard until its lag clears.\n"
        after = "Retry via probe; drop a shard once its lag clears.\n"
        lost = cp.lost_items(before, after)
        self.assertEqual({"at least", "not", "until"}, {i["text"] for i in lost[self.Q]})
        self.assertEqual([{"text": "3", "count": 1}], lost["number"])
        self.assertEqual([{"text": "`probe`", "count": 1}], lost["code"])

    def test_one_of_two_repeats_gone_counts_once(self):
        lost = cp.lost_items("Never cache. Really never cache.\n", "Never cache.\n")
        self.assertEqual({self.Q: [{"text": "never", "count": 1}]}, lost)

    def test_contractions_curly_or_straight_and_versions(self):
        before = "The worker won’t restart and it doesn't alert without a quorum. Needs v3.1.4.\n"
        after = "The worker will restart and it does alert with a quorum. Needs v3.4.1.\n"
        lost = cp.lost_items(before, after)
        self.assertEqual({"won't", "doesn't", "without"}, {i["text"] for i in lost[self.Q]})
        self.assertEqual([{"text": "v3.1.4", "count": 1}], lost["number"])

    def test_ticket_keys_hash_numbers_and_constants_are_ids(self):
        lost = cp.lost_items("Fixes WEB-210 and #88 via MAX_POOL.\n", "Fixes the leak.\n")
        self.assertEqual({"WEB-210", "#88", "MAX_POOL"}, {i["text"] for i in lost["id"]})

    def test_headings_rows_urls(self):
        before = "## Plan\n| a | b |\nSee https://example.com/x.\n"
        lost = cp.lost_items(before, "Plan.\n")
        self.assertIn("heading", lost)
        self.assertIn("table row", lost)
        self.assertEqual("https://example.com/x.", lost["url"][0]["text"])

    def test_unchanged_text_loses_nothing(self):
        text = "## Steps\n| step | check |\n|---|---|\nRunbook at https://example.com/r and WEB-1.\n"
        self.assertEqual({}, cp.lost_items(text, text))

    def test_cli_works_with_no_vale_anywhere(self):
        tmp = scratch(self)
        (tmp / "a.md").write_text("Bodies must never exceed 512 KB.\n")
        (tmp / "b.md").write_text("Bodies must exceed 512 KB.\n")
        proc = invoke(str(tmp / "b.md"), "--against", str(tmp / "a.md"), PATH=BARE_PATH)
        self.assertEqual(0, proc.returncode, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertEqual({self.Q: [{"text": "never", "count": 1}]}, report["lost"])
        self.assertEqual(str((tmp / "a.md").resolve()), report["against"])


# --- Humanizer --------------------------------------------------------------------------------

OVERRIDDEN = [("5", "Arguing with no one"), ("8", "Dashes as the universal connector"),
              ("22", "Chatbot residue"),
              ("25", "Writing about the document instead of its subject"),
              ("26", "Re-explaining what the reader knows")]

HUMANIZER_FIXTURE = "\n".join([
    "---",
    "name: humanizer",
    "description: test copy",
    "---",
    "",
    "# Humanizer",
    "",
    "## Method",
    "",
    "1. **Read first.** Take in the whole text.",
    "",
    "### Voice",
    "",
    "Mirror the sample's cadence.",
    "",
    "### What to return",
    "",
    "Return the rewrite.",
    "",
    "## A. Structure",
    "",
    "Name each pattern once.",
    "",
    "### 1. Empty contrast",
    "",
    "**Watch for:** a setup and a twist.",
    "**Problem:** Filler. Keep the contrast only when both halves state facts.",
    "**Before:**",
    "> Not a failure, a lesson.",
    "**After (cut):**",
    "> The retry limit was low.",
    "",
    "### 2. Neat endings",
    "",
    "Text with no label stays.",
    "",
    "## Source",
    "",
    "Provenance notes.",
    "",
])


class Humanizer(unittest.TestCase):
    def sources(self, skill_text):
        data = scratch(self)
        put_humanizer(data, skill_text)
        return invoke("--sources", XDG_DATA_HOME=str(data))

    def test_matching_titles_report_commit_and_no_stale_override(self):
        proc = self.sources("".join("### %s. %s\n" % pair for pair in OVERRIDDEN))
        self.assertEqual(0, proc.returncode, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertEqual("c0ffee12", report["humanizer"]["commit"])
        self.assertEqual("unknown", report["humanizer"]["fetched"])
        self.assertEqual(5, report["humanizer"]["patterns"])
        self.assertEqual([], report["humanizer"]["stale_overrides"])
        self.assertEqual([], report["kind_homes_missing"])

    def test_renamed_and_absent_patterns_are_stale(self):
        proc = self.sources("### 5. Arguing with nobody\n### 22. Chatbot residue\n")
        self.assertEqual(0, proc.returncode, proc.stderr)
        stale = json.loads(proc.stdout)["humanizer"]["stale_overrides"]
        self.assertIn("§5 Arguing with no one", stale)
        self.assertIn("§25 Writing about the document instead of its subject", stale)
        self.assertNotIn("§22 Chatbot residue", stale)

    def test_no_cache_means_exit_3_with_install_command(self):
        proc = invoke("--sources", XDG_DATA_HOME=str(scratch(self)))
        self.assertEqual(3, proc.returncode)
        self.assertEqual(False, json.loads(proc.stdout)["humanizer"]["loaded"])
        self.assertIn("install.sh", proc.stderr)

    def test_filter_keeps_patterns_and_drops_examples_and_set_aside_parts(self):
        out = cp.filter_humanizer(HUMANIZER_FIXTURE)
        title_line = HUMANIZER_FIXTURE.splitlines().index("### 1. Empty contrast") + 1
        for kept in ("Read first", "Name each pattern once", "**Watch for:** a setup and a twist.",
                     "Keep the contrast only when both halves state facts.",
                     "Text with no label stays.",
                     "### 1. Empty contrast  [humanizer SKILL.md:%d]" % title_line):
            self.assertIn(kept, out)
        for dropped in ("description: test copy", "### Voice", "cadence", "Return the rewrite",
                        "a lesson", "limit was low", "Provenance", "**Before"):
            self.assertNotIn(dropped, out)


# --- kinds.md homes ---------------------------------------------------------------------------

class KindHomes(unittest.TestCase):
    def missing(self, row, files):
        root = scratch(self)
        refs = root / "skills" / "refining-technical-writing" / "references"
        refs.mkdir(parents=True)
        (root / "skills" / "neighbour").mkdir()
        for name, text in files.items():
            (refs / name).write_text(text)
        kinds = "| Kind | Reader | Length | Rules |\n|---|---|---|---|\n%s\n" % row
        return cp.KindTable(kinds, refs).missing()

    def test_shipped_table_resolves(self):
        self.assertEqual([], cp.kind_table(SHIPPED).missing())

    def test_absent_heading_and_absent_lead(self):
        row = '| K | r | l | `home.md` "## Here" "## Gone" "a bold lead" "a lost lead" |'
        files = {"home.md": "## Here\nWords around **a bold lead** here.\n"}
        self.assertEqual(['home.md: "## Gone"', 'home.md: "a lost lead"'],
                         self.missing(row, files))

    def test_missing_file_versus_missing_skill(self):
        row = ('| K | r | l | `../../neighbour/references/x.md` "## Y", '
               '`../../absent/references/z.md` |')
        self.assertEqual(["../../neighbour/references/x.md: file not found",
                          "../../absent/references/z.md: skill not installed"],
                         self.missing(row, {}))

    def test_quotes_before_the_first_file_are_ignored(self):
        row = '| K | r | l | "Some section" below; `local.md` |'
        self.assertEqual([], self.missing(row, {"local.md": "Text.\n"}))

    def test_hash_line_inside_a_fence_does_not_end_a_section(self):
        text = "## Owner\n```sh\n# shell comment\n```\nThe rule.\n## Next\nOther.\n"
        body = cp.section_body(text, "## Owner")
        self.assertIn("The rule.", body)
        self.assertNotIn("Other.", body)
        self.assertIsNone(cp.section_body(text, "## Nowhere"))


class GeneralRulePointers(unittest.TestCase):
    """Every `general-rules.md` "Name" pointer in the skill names a real heading or bold lead."""

    POINTER = re.compile(r'general-rules\.md`?\s+"([^"]+)"')

    def test_pointers_resolve(self):
        rules = cp.read_text(SHIPPED.ref("general-rules.md"))
        names = set(re.findall(r"(?m)^#{2,3} (.+?)\s*$", rules))
        names.update(re.findall(r"\*\*([^*]+?)\.?\*\*", rules))
        files = [SHIPPED.skill / "SKILL.md", SHIPPED.vale_dir / "vale.ini"]
        files += sorted(SHIPPED.refs.glob("*.md"))
        files += sorted((SHIPPED.vale_dir / cp.OWN_STYLE).glob("*.yml"))
        for path in files:
            for name in self.POINTER.findall(path.read_text()):
                name = " ".join(name.split())  # pointers can wrap across lines
                self.assertIn(name, names, "%s: no target for %r" % (path.name, name))


# --- Detail blocks ----------------------------------------------------------------------------

class Details(unittest.TestCase):
    def test_block_removed_and_neighbours_kept(self):
        text = ("# Title\n\n## Rule\n\nFIX this case.\n<!-- detail -->\nAn example.\n"
                "<!-- /detail -->\nExcept that one.\n")
        out = cp.strip_details(text, "r.md")
        self.assertIn("## Rule  [r.md:3]", out)
        self.assertIn("FIX this case.\nExcept that one.", out)
        self.assertNotIn("example", out)

    def test_headings_inside_fences_are_not_tagged(self):
        out = cp.strip_details("```\n# not a heading\n```\n# real\n", "f.md")
        self.assertIn("# not a heading\n", out)
        self.assertIn("# real  [f.md:4]", out)

    def test_unpaired_marks_raise(self):
        broken = ["<!-- detail -->\nleft open\n", "stray\n<!-- /detail -->\n",
                  "<!-- detail -->\n<!-- detail -->\n<!-- /detail -->\n"]
        for text in broken:
            with self.subTest(text=text), self.assertRaises(cp.CheckError):
                cp.strip_details(text, "r.md")

    def test_shipped_references_pair_their_marks(self):
        for path in sorted(SHIPPED.refs.glob("*.md")):
            self.assertNotIn("<!-- detail", cp.strip_details(path.read_text(), path.name), path)

    def test_shipped_general_rules_keep_triggers_and_drop_examples(self):
        out = cp.strip_details(cp.read_text(SHIPPED.ref("general-rules.md")), "general-rules.md")
        self.assertNotIn("production backfill finishes Friday", out)
        self.assertIn("**FIX** any of the three that walks", out)
        self.assertIn("A listed word is a finding only when its sentence stays vague", out)


# --- Rule assembly ----------------------------------------------------------------------------

KINDS_FIXTURE = (
    "# Kinds\n\nPrecedence note.\n<!-- detail -->\nMaintainer aside.\n<!-- /detail -->\n\n"
    "| Kind | Reader | Length | Rules |\n|---|---|---|---|\n"
    '| `chat` Chat | a | b | "Talking" below |\n'
    '| `pr` Pull request | a | b | "Reviews" below; `std.md` "## Pieces" "a flagged lead" |\n'
    '| `comment` Comment | a | b | `whole.md` |\n\n'
    "Common guidance.\n\n## Talking\n\nBe brief.\n\n## Reviews\n\nReview prose notes.\n\n"
    "## Shared\n\nAlways included.\n")
STD_FIXTURE = ("## Pieces\n\nSummary, then testing.\n<!-- detail -->\nA pieces example.\n"
               "<!-- /detail -->\n\n## Other\n\nNot asked for.\n\n"
               "There is **a flagged lead** here.\nIt continues.\n\nUnrelated text.\n")
WHOLE_FIXTURE = "# Whole\n\nAll of it.\n<!-- detail -->\nA sample.\n<!-- /detail -->\n"


class Assembly(unittest.TestCase):
    def rules(self, slugs):
        refs = scratch(self)
        (refs / "std.md").write_text(STD_FIXTURE)
        (refs / "whole.md").write_text(WHOLE_FIXTURE)
        return cp.KindTable(KINDS_FIXTURE, refs).rules_for(slugs)

    def test_one_kind_gets_row_section_and_requested_parts(self):
        out = self.rules(["pr"])
        for kept in ("Precedence note.", "| `pr` Pull request", "Common guidance.",
                     "Review prose notes.", "Always included.", "## Pieces",
                     "Summary, then testing.", "There is a flagged lead here.\nIt continues.",
                     "# std.md ## Pieces", "# std.md a flagged lead"):
            self.assertIn(kept, out)
        for dropped in ("| `chat`", "Be brief.", "Not asked for.", "Unrelated text."):
            self.assertNotIn(dropped, out)

    def test_whole_file_home_and_two_slugs(self):
        out = self.rules(["chat", "comment"])
        self.assertIn("# whole.md\n", out)
        self.assertIn("All of it.", out)
        self.assertIn("Be brief.", out)
        self.assertNotIn("Review prose notes.", out)

    def test_details_are_removed_everywhere(self):
        out = self.rules(["pr", "comment"])
        for dropped in ("Maintainer aside", "pieces example", "A sample", "<!-- detail"):
            self.assertNotIn(dropped, out)

    def test_absent_home_and_absent_part_are_marked(self):
        kinds = '| `x` X | a | b | `gone.md`, `std.md` "## Missing" |\n'
        refs = scratch(self)
        (refs / "std.md").write_text(STD_FIXTURE)
        out = cp.KindTable(kinds, refs).rules_for(["x"])
        self.assertIn("# gone.md: not found", out)
        self.assertIn("# std.md ## Missing\n(not found)", out)

    def test_unknown_slug_lists_the_valid_ones(self):
        with self.assertRaisesRegex(cp.CheckError, "valid kinds: chat, pr, comment"):
            self.rules(["memo"])

    def test_every_shipped_row_has_a_slug(self):
        lines = cp.read_text(SHIPPED.ref("kinds.md")).splitlines()
        rows = [l for l in lines if l.startswith("|") and not l.startswith(("|---", "| Kind "))]
        self.assertEqual(len(rows), len(cp.kind_table(SHIPPED).rows))

    def test_every_shipped_kind_renders_completely(self):
        table = cp.kind_table(SHIPPED)
        for slug in table.rows:
            out = table.rules_for([slug])
            self.assertNotIn("(not found)", out, slug)
            self.assertNotIn(": not found", out, slug)

    def test_pr_kind_brings_in_the_pr_description_standard_when_installed(self):
        name = "../../preparing-code-reviews/references/pr-description.md"
        if not (SHIPPED.refs / name).resolve().is_file():
            self.skipTest("preparing-code-reviews is not installed beside this skill")
        out = cp.kind_table(SHIPPED).rules_for(["pr"])
        self.assertIn("# " + name, out)
        self.assertIn("## PR descriptions", out)


class KindCommand(unittest.TestCase):
    def test_kind_writes_a_cached_file_and_reuses_it(self):
        data = scratch(self)
        put_humanizer(data, HUMANIZER_FIXTURE)
        first = invoke("--kind", "commit", XDG_DATA_HOME=str(data), PATH=BARE_PATH)
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertTrue(first.stdout.startswith("# Review rules: commit\n\nSources: Humanizer "
                                                "c0ffee12"), first.stdout[:120])
        self.assertLess(len(first.stdout), 2000)  # a pointer, not the rules themselves
        path = Path(re.search(r"^Rules file: (\S+)$", first.stdout, re.M).group(1))
        self.assertTrue(path.is_relative_to(Path(data).joinpath(*CACHE_TAIL, "rules")), path)
        rules = path.read_text()
        self.assertIn("Name each pattern once", rules)
        self.assertIn("Humanizer: what applies, and the overrides", rules)
        self.assertIn("## Commit messages", rules)
        self.assertNotIn("## Status updates", rules)
        again = invoke("--kind", "commit", XDG_DATA_HOME=str(data), PATH=BARE_PATH)
        self.assertIn("Rules file: %s\n" % path, again.stdout)

    def test_kind_without_humanizer_exits_3_but_still_points_at_rules(self):
        proc = invoke("--kind", "commit", XDG_DATA_HOME=str(scratch(self)))
        self.assertEqual(3, proc.returncode)
        self.assertIn("Humanizer not loaded", proc.stdout)
        self.assertIn("Rules file: ", proc.stdout)
        self.assertIn("install.sh", proc.stderr)

    def test_unknown_kind_exits_2(self):
        proc = invoke("--kind", "memo", XDG_DATA_HOME=str(scratch(self)))
        self.assertEqual(2, proc.returncode)
        self.assertIn("valid kinds:", proc.stderr)


class Failures(unittest.TestCase):
    def test_missing_vale_exits_3_and_prints_nothing(self):
        home = scratch(self)
        (home / "note.md").write_text("A short note.\n")
        proc = invoke(str(home / "note.md"), HOME=str(home), PATH=BARE_PATH)
        self.assertEqual(3, proc.returncode)
        self.assertIn("install.sh", proc.stderr)
        self.assertEqual("", proc.stdout)

    def test_missing_deslop_exits_3(self):
        home = scratch(self)
        fake = home / ".local" / "bin" / "vale"
        fake.parent.mkdir(parents=True)
        fake.write_text("#!/bin/sh\necho 'vale 0.0'\n")
        fake.chmod(0o755)
        (home / "note.md").write_text("A short note.\n")
        proc = invoke(str(home / "note.md"), HOME=str(home), XDG_DATA_HOME=str(home / "d"))
        self.assertEqual(3, proc.returncode)
        self.assertIn("Deslop", proc.stderr)

    def test_failing_vale_exits_2_with_its_message(self):
        home = scratch(self)
        fake = home / ".local" / "bin" / "vale"
        fake.parent.mkdir(parents=True)
        fake.write_text('#!/bin/sh\ncase "$1" in --version) echo "vale 0.0"; exit 0;; esac\n'
                        "echo 'E201 bad rule' >&2\nexit 2\n")
        fake.chmod(0o755)
        Path(home, "d", *CACHE_TAIL, "vale", "styles", "Deslop").mkdir(parents=True)
        (home / "note.md").write_text("A short note.\n")
        proc = invoke(str(home / "note.md"), HOME=str(home), XDG_DATA_HOME=str(home / "d"))
        self.assertEqual(2, proc.returncode)
        self.assertIn("Vale failed (exit 2): E201 bad rule", proc.stderr)
        self.assertNotIn("install.sh", proc.stderr)

    def test_unreadable_files_exit_2_cleanly(self):
        proc = invoke("/nonexistent/edit.md", "--against", "/nonexistent/orig.md")
        self.assertEqual(2, proc.returncode)
        self.assertTrue(proc.stderr.startswith("check_prose: "), proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_no_arguments_is_a_usage_error(self):
        self.assertEqual(2, invoke().returncode)


class PackDeduplication(unittest.TestCase):
    """The shadowing step, without Vale: word-list alerts displace overlapping pack alerts."""

    def alert(self, rule, line, lo, hi):
        return {"line": line, "column": lo, "end": hi, "rule": rule}

    def test_overlap_on_same_line_is_dropped(self):
        alerts = [self.alert("Plain.WordListPhraseForWord", 1, 5, 15),
                  self.alert("Deslop.Substitutions", 1, 10, 20),
                  self.alert("Deslop.Substitutions", 2, 10, 20),
                  self.alert("Plain.SentenceLength", 1, 1, 80)]
        kept = [(a["rule"], a["line"]) for a in cp._without_shadowed(alerts)]
        self.assertEqual([("Plain.WordListPhraseForWord", 1), ("Deslop.Substitutions", 2),
                          ("Plain.SentenceLength", 1)], kept)


@unittest.skipUnless(HAVE_VALE, "needs Vale and the Deslop pack (bash scripts/install.sh)")
class WithVale(unittest.TestCase):
    def found(self, text, **env):
        tmp = scratch(self)
        (tmp / "doc.md").write_text(text)
        proc = invoke(str(tmp / "doc.md"), **env)
        self.assertEqual(0, proc.returncode, proc.stderr)
        return [(f["line"], f["rule"]) for f in json.loads(proc.stdout)["findings"]]

    def test_plain_rules_fire_and_code_and_links_do_not(self):
        hits = self.found(
            "We utilize the queue in order to scale.\n\n"
            "One aside — like this — is fine. But this — one — has — four.\n\n"
            "Open (the [guide](https://example.com/g(h)) page) and `in order to`.\n\n"
            "A (wrapper (inner) aside).\n\n"
            "Paths `src/**`, `lib/**` and **shouty** words. It ran prior to the cutover.\n")
        self.assertIn((1, "Plain.WordListComplexWords"), hits)
        self.assertIn((1, "Plain.WordListPhraseForWord"), hits)
        self.assertNotIn((1, "Deslop.Substitutions"), hits)
        self.assertEqual(1, sum(r == "Plain.StackedEmDashes" for _, r in hits))
        self.assertNotIn((5, "Plain.WordListPhraseForWord"), hits)
        self.assertNotIn((5, "Plain.NestedParentheses"), hits)
        self.assertIn((7, "Plain.NestedParentheses"), hits)
        self.assertEqual(1, sum(l == 9 and r == "Plain.EmphasisBold" for l, r in hits))
        self.assertIn((9, "Plain.WordListPhraseForWord"), hits)

    def test_broken_word_lists_leave_other_rules_running(self):
        tmp = scratch(self)
        (tmp / "word-lists.md").write_text("## filler\n- `x`\n")
        findings, status = cp.lint("We utilize it. A — b — c — d.\n",
                                   cp.locate_vale(SHIPPED), SHIPPED, tmp / "word-lists.md")
        self.assertTrue(status.startswith("not loaded: "), status)
        rules = {f["rule"] for f in findings}
        self.assertIn("Plain.StackedEmDashes", rules)
        self.assertFalse(any(r.startswith("Plain.WordList") for r in rules))

    def test_long_sentence_does_not_hide_pack_findings(self):
        hits = self.found("That being said, " + " ".join(["word"] * 31) + ".\n")
        self.assertIn((1, "Plain.SentenceLength"), hits)
        self.assertTrue(any(r.startswith("Deslop.") for l, r in hits if l == 1), hits)

    def test_sentence_length_boundary(self):
        text = " ".join(["word"] * 31) + ".\n\n" + " ".join(["word"] * 30) + ".\n"
        self.assertEqual([1], [l for l, r in self.found(text) if r == "Plain.SentenceLength"])

    def test_user_vale_config_is_ignored(self):
        conf = scratch(self)
        (conf / "vale").mkdir()
        (conf / "vale" / ".vale.ini").write_text("[*]\nBasedOnStyles = Vale, Microsoft\n")
        self.found("A short note.\n", XDG_CONFIG_HOME=str(conf))

    def test_named_actor_flags_people_and_roles_not_systems(self):
        actors = ["Cutover: platform team to rotate the keys.", "The on-call will call the vendor.",
                  "Waiting until the owner must approve.", "The lead will sign it.",
                  "Load test: pending: owner, https://perf.example.com",
                  "This rollback needs the on-call.", "Skipped, waived by owner."]
        fine = ["Three teams use the cache.", "The team's backlog is short.",
                "Rotate the keys in staging.", "Lets teams deploy faster.",
                "The scheduler will retry.", "Runs 1 PM to 4 PM UTC.",
                "Pending: the load test at https://perf.example.com, needs staging access."]
        hits = self.found("\n\n".join(actors + fine) + "\n")
        flagged = [l for l, r in hits if r == "Plain.NamedActor"]
        self.assertEqual([1 + 2 * i for i in range(len(actors))], flagged)


if __name__ == "__main__":
    unittest.main()
