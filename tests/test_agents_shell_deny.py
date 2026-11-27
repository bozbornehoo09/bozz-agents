"""Checks for the shell deny families in agents/shared/shell-deny/.

Run with: python3 -I -m unittest discover -s tests -p 'test_agents*.py'
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "agents/shared/shell_deny.py"
LISTS = ROOT / "agents/shared/shell-deny"
FAMILIES = ("destructive", "readonly")

# Known, accepted over-matches: the lists see command words inside quoted
# arguments. Recorded so a change that alters them shows up here.
KNOWN_OVERMATCH = [
    ("destructive", "grep -n 'aws s3 rm s3://orders-export/k' runbook.md", "aws-mutation"),
    ("destructive", "echo 'git push --force is banned'", "git-push-force"),
]
# Commands that differ only in whitespace must be decided alike.
WHITESPACE_VARIANTS = ["git  push  -f", "git\tpush --force", "sudo\tls", "rm  -rf   /"]


def load_module():
    sys.dont_write_bytecode = True  # keep agents/shared free of __pycache__
    spec = importlib.util.spec_from_file_location("shell_deny", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def family_data(name: str) -> dict:
    return json.loads((LISTS / f"{name}.json").read_text(encoding="utf-8"))


class ShellDenyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module()

    def test_family_files_are_well_formed(self):
        for family in FAMILIES:
            data = family_data(family)
            with self.subTest(family=family):
                self.assertEqual(data["family"], family)
                self.assertTrue(data["description"].strip())
                self.assertTrue(data["safe"])
                ids = [r["id"] for r in self.mod.load_family(family)]
                self.assertEqual(len(ids), len(set(ids)), "rule ids must be unique across a family")
                for rule in data["rules"]:
                    self.assertEqual(set(rule), {"id", "reason", "pattern", "examples"})
                    re.compile(rule["pattern"])
                    self.assertTrue(rule["examples"], f"{rule['id']} has no examples")

    def test_readonly_extends_destructive(self):
        self.assertEqual(family_data("readonly")["extends"], "destructive")
        destructive = {r["id"] for r in self.mod.load_family("destructive")}
        readonly = {r["id"] for r in self.mod.load_family("readonly")}
        self.assertLess(destructive, readonly)

    def test_each_rule_blocks_its_examples(self):
        for family in FAMILIES:
            rules = self.mod.load_family(family)
            for rule in family_data(family)["rules"]:
                for example in rule["examples"]:
                    with self.subTest(family=family, rule=rule["id"], command=example):
                        hit = [r["id"] for r in self.mod.matches(example, rules)]
                        self.assertIn(rule["id"], hit)

    def test_inherited_examples_stay_blocked(self):
        rules = self.mod.load_family("readonly")
        for rule in family_data("destructive")["rules"]:
            for example in rule["examples"]:
                with self.subTest(command=example):
                    self.assertTrue(self.mod.matches(example, rules))

    def test_safe_commands_pass(self):
        for family in FAMILIES:
            rules = self.mod.load_family(family)
            for command in family_data(family)["safe"]:
                with self.subTest(family=family, command=command):
                    self.assertEqual([r["id"] for r in self.mod.matches(command, rules)], [])

    def test_readonly_safe_commands_are_safe_for_pen_holders_too(self):
        rules = self.mod.load_family("destructive")
        for command in family_data("readonly")["safe"]:
            with self.subTest(command=command):
                self.assertEqual(self.mod.matches(command, rules), [])

    def test_plain_push_is_left_to_the_ask_flow(self):
        rules = self.mod.load_family("destructive")
        self.assertEqual(self.mod.matches("git push origin fix/retry", rules), [])
        self.assertTrue(self.mod.matches("git push origin fix/retry", self.mod.load_family("readonly")))

    def test_known_overmatches(self):
        for family, command, rule_id in KNOWN_OVERMATCH:
            with self.subTest(command=command):
                hit = [r["id"] for r in self.mod.matches(command, self.mod.load_family(family))]
                self.assertIn(rule_id, hit)

    def test_whitespace_variants_are_denied(self):
        rules = self.mod.load_family("destructive")
        for command in WHITESPACE_VARIANTS:
            with self.subTest(command=command):
                self.assertTrue(self.mod.matches(command, rules))


class ShellDenyHookTests(unittest.TestCase):
    def run_hook(self, payload, family: str = "destructive") -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "-I", str(SCRIPT), "--family", family],
                              input=payload if isinstance(payload, str) else json.dumps(payload),
                              capture_output=True, text=True)

    def test_hook_blocks_with_exit_2_and_a_reason(self):
        result = self.run_hook({"tool_name": "Bash", "tool_input": {"command": "git reset --hard HEAD~3"}})
        self.assertEqual(result.returncode, 2)
        self.assertIn("git-reset-hard", result.stderr)

    def test_hook_passes_safe_commands(self):
        result = self.run_hook({"tool_name": "Bash", "tool_input": {"command": "git status --short"}})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")

    def test_hook_ignores_other_tools_and_bad_input(self):
        self.assertEqual(self.run_hook({"tool_name": "Read", "tool_input": {"file_path": "/"}}).returncode, 0)
        self.assertEqual(self.run_hook("not json").returncode, 0)

    def test_hook_uses_the_named_family(self):
        payload = {"tool_name": "Bash", "tool_input": {"command": "git fetch origin"}}
        self.assertEqual(self.run_hook(payload, "destructive").returncode, 0)
        self.assertEqual(self.run_hook(payload, "readonly").returncode, 2)

    def test_command_mode(self):
        result = subprocess.run([sys.executable, "-I", str(SCRIPT), "--family", "readonly",
                                 "--command", "cat ~/.ssh/id_ed25519"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("credential-path", result.stdout)


if __name__ == "__main__":
    unittest.main()
