"""Checks for the manager/worker agent definitions under agents/.

Run with: python3 -I -m unittest discover -s tests -p 'test_agents*.py'
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "agents"
SHARED = AGENTS / "shared"
CODEX = ROOT / "codex" / "agents"
BEHAVIORS = ROOT / "tests/data/agents/manager-behaviors.json"

ROLES = {
    # role: (model tier, tools frontmatter or None for "inherit")
    "manager": ("opus", None),
    "architect": ("opus", None),
    "implementer": ("sonnet", None),
    "review-specialist": ("opus", "Read, Glob, Grep, Bash"),
    "cold-reader": ("sonnet", "Read"),
    "cold-reader-deep": ("opus", "Read"),
    "artifact-verifier": ("opus", "Read, Glob, Grep, Bash, WebFetch, WebSearch"),
}
SESSION_ROLES = {"manager", "architect", "implementer"}
WRITE_TOOLS = {"Write", "Edit", "NotebookEdit"}
ALLOWED_MODELS = {"opus", "sonnet", "haiku"}

# Skills each role prompt names; every one must exist in skills/ or be listed
# as pending (being written in the same port; drop it here once it lands).
REFERENCED_SKILLS = {
    "manager": ["context-up", "plan-review", "update-context", "writing-implementation-plans",
                "preparing-code-reviews", "design-doc-write"],
    "architect": ["context-up", "design-doc-write", "design-doc-edit", "design-doc-review", "design-diagrams",
                  "writing-implementation-plans", "plan-review", "implementing-a-plan", "preparing-code-reviews",
                  "code-review", "docs-review", "skill-review", "cross-review-requester",
                  "fold-review-findings", "deciding-calls-by-debate", "update-context"],
    "implementer": ["context-up", "implementing-a-plan", "preparing-code-reviews", "code-review", "plan-review"],
}
SHARED_SKILLS = ["update-context", "deciding-calls-by-debate", "refining-technical-writing",
                 "update-decisions", "update-open-questions", "code-review", "preparing-code-reviews"]
PENDING_SKILLS: set = set()


def frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"{path.name}: no frontmatter")
    head, sep, body = text[4:].partition("\n---\n")
    if not sep:
        raise AssertionError(f"{path.name}: frontmatter not closed")
    fields = {}
    for line in head.splitlines():
        key, colon, value = line.partition(":")
        if colon:
            fields[key.strip()] = value.strip()
    return fields, body


def folded(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


class AgentDefinitionTests(unittest.TestCase):
    def test_exactly_the_expected_roles(self):
        found = {p.stem for p in AGENTS.glob("*.md")}
        self.assertEqual(found, set(ROLES))

    def test_frontmatter_name_description_model_tools(self):
        for role, (model, tools) in ROLES.items():
            with self.subTest(role=role):
                fields, body = frontmatter(AGENTS / f"{role}.md")
                self.assertEqual(fields.get("name"), role)
                self.assertGreater(len(fields.get("description", "")), 80)
                self.assertIn(fields.get("model"), ALLOWED_MODELS)
                self.assertEqual(fields.get("model"), model)
                self.assertEqual(fields.get("tools"), tools)
                self.assertTrue(body.strip())

    def test_no_fable_model_anywhere(self):
        for path in list(AGENTS.rglob("*")) + list(CODEX.glob("*.toml")):
            if path.is_file() and path.suffix in {".md", ".json", ".toml", ".py", ".sh", ".zsh"}:
                with self.subTest(path=path.name):
                    self.assertNotRegex(path.read_text(encoding="utf-8").lower(), r"model\s*[:=]\s*\"?fable")

    def test_subagent_roles_cannot_write(self):
        for role in set(ROLES) - SESSION_ROLES:
            with self.subTest(role=role):
                tools = {t.strip() for t in frontmatter(AGENTS / f"{role}.md")[0]["tools"].split(",")}
                self.assertFalse(tools & WRITE_TOOLS)

    def test_cold_reader_pair_shares_one_prompt_on_two_tiers(self):
        fast, fast_body = frontmatter(AGENTS / "cold-reader.md")
        deep, deep_body = frontmatter(AGENTS / "cold-reader-deep.md")
        self.assertEqual(fast_body, deep_body)
        self.assertNotEqual(fast["model"], deep["model"])

    def test_shared_folder_holds_no_agent_definitions(self):
        # A plugin's agents/ scan is recursive; the shared material must not
        # look like an agent, and plugin.json must list the role files.
        for path in SHARED.rglob("*.md"):
            with self.subTest(path=path.name):
                self.assertFalse(path.read_text(encoding="utf-8").startswith("---\n"))

    def test_session_roles_load_the_shared_material(self):
        for role in ("architect", "implementer"):
            with self.subTest(role=role):
                text = (AGENTS / f"{role}.md").read_text(encoding="utf-8")
                for name in ("worker-contract.md", "owner-talk.md", "owner-override.md"):
                    self.assertIn(name, text)
        manager = (AGENTS / "manager.md").read_text(encoding="utf-8")
        for name in ("worker-contract.md", "owner-talk.md", "owner-override.md",
                     "scripts/ctx.sh", "scripts/watch.zsh"):
            self.assertIn(name, manager)
        self.assertIn("scripts/ctxpct.sh", (SHARED / "worker-contract.md").read_text(encoding="utf-8"))

    def test_shared_files_exist(self):
        for rel in ("worker-contract.md", "owner-talk.md", "owner-override.md", "shell_deny.py",
                    "shell-deny/destructive.json", "shell-deny/readonly.json", "claude-settings.example.json",
                    "build_codex_roles.py", "scripts/ctx.sh", "scripts/ctxpct.sh", "scripts/watch.zsh"):
            with self.subTest(rel=rel):
                self.assertTrue((SHARED / rel).is_file())

    def test_referenced_skills_exist(self):
        existing = {p.name for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file()}
        checks = [(AGENTS / f"{r}.md", names) for r, names in REFERENCED_SKILLS.items()]
        checks.append((SHARED / "worker-contract.md", SHARED_SKILLS))
        for path, names in checks:
            text = path.read_text(encoding="utf-8")
            for name in names:
                with self.subTest(file=path.name, skill=name):
                    self.assertIn(f"`{name}`", text)
                    self.assertTrue(name in existing or name in PENDING_SKILLS, f"no skills/{name}/SKILL.md")

    def test_roles_point_at_context_layers_not_private_folders(self):
        text = folded(AGENTS / "manager.md") + folded(SHARED / "worker-contract.md")
        self.assertIn("context-manifest.yaml", text)
        self.assertIn("work-tracker", text)
        self.assertIn("ADRs", folded(SHARED / "worker-contract.md"))

    def test_claude_settings_example_parses(self):
        data = json.loads((SHARED / "claude-settings.example.json").read_text(encoding="utf-8"))
        for rule in data["permissions"]["deny"] + data["permissions"]["ask"]:
            with self.subTest(rule=rule):
                self.assertRegex(rule, r"^(Bash|Read)\(.+\)$")
        hook = data["hooks"]["PreToolUse"][0]
        self.assertEqual(hook["matcher"], "Bash")
        self.assertIn("shell_deny.py --family destructive", hook["hooks"][0]["command"])

    def test_helper_scripts_parse(self):
        for name in ("ctx.sh", "ctxpct.sh", "watch.zsh"):
            with self.subTest(script=name):
                try:
                    result = subprocess.run(["zsh", "-n", str(SHARED / "scripts" / name)],
                                            capture_output=True, text=True)
                except FileNotFoundError:
                    self.skipTest("zsh not installed")
                self.assertEqual(result.returncode, 0, result.stderr)


class CodexRoleTests(unittest.TestCase):
    def test_generated_role_files_are_current(self):
        result = subprocess.run([sys.executable, "-I", str(SHARED / "build_codex_roles.py"), "--check"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_role_files_have_codex_required_fields(self):
        files = sorted(CODEX.glob("*.toml"))
        self.assertEqual({p.stem for p in files}, set(ROLES) - SESSION_ROLES)
        for path in files:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("# GENERATED"))
                data = tomllib.loads(text)
                self.assertEqual(data["name"], path.stem)
                self.assertTrue(data["description"].strip())
                self.assertTrue(data["developer_instructions"].strip())
                _, body = frontmatter(AGENTS / f"{path.stem}.md")
                self.assertEqual(data["developer_instructions"].strip(), body.strip())


class ManagerBehaviorDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(BEHAVIORS.read_text(encoding="utf-8"))

    def test_schema(self):
        self.assertEqual(self.data["schema"], 1)
        cases = self.data["cases"]
        self.assertGreaterEqual(len(cases), 30)
        ids = [c["id"] for c in cases]
        self.assertEqual(len(ids), len(set(ids)), "duplicate case ids")
        for case in cases:
            with self.subTest(case=case.get("id")):
                self.assertEqual(set(case), {"id", "category", "roles", "input", "expected", "anchors"})
                self.assertRegex(case["id"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
                for key in ("category", "input", "expected"):
                    self.assertIsInstance(case[key], str)
                    self.assertTrue(case[key].strip())
                self.assertTrue(case["roles"])
                self.assertTrue(case["anchors"])

    def test_roles_exist(self):
        for case in self.data["cases"]:
            for role in case["roles"]:
                with self.subTest(case=case["id"], role=role):
                    self.assertIn(role, ROLES)
                    self.assertTrue((AGENTS / f"{role}.md").is_file())

    def test_anchors_are_in_the_prompts(self):
        for case in self.data["cases"]:
            for anchor in case["anchors"]:
                with self.subTest(case=case["id"], file=anchor["file"]):
                    path = ROOT / anchor["file"]
                    self.assertTrue(path.is_relative_to(AGENTS) and path.is_file(), anchor["file"])
                    self.assertIn(re.sub(r"\s+", " ", anchor["text"]), folded(path))

    def test_every_session_role_has_cases(self):
        covered = {r for c in self.data["cases"] for r in c["roles"]}
        self.assertLessEqual(SESSION_ROLES, covered)


if __name__ == "__main__":
    unittest.main()
