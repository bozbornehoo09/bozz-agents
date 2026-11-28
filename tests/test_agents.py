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
    # role: (model tier, the tools it lists, the subagent types it may dispatch)
    "manager": ("opus", {"Read", "Write", "Edit", "Glob", "Grep", "Bash", "Skill", "ToolSearch", "SendMessage"},
                {"general-purpose"}),
    "architect": ("opus", {"Read", "Write", "Edit", "Glob", "Grep", "Bash", "Skill", "ToolSearch", "WebFetch",
                           "WebSearch"},
                  {"review-specialist", "cold-reader", "cold-reader-deep", "artifact-verifier", "general-purpose"}),
    "implementer": ("sonnet", {"Read", "Write", "Edit", "Glob", "Grep", "Bash", "Skill", "ToolSearch", "WebFetch"},
                    {"review-specialist", "artifact-verifier"}),
    "review-specialist": ("opus", {"Read", "Glob", "Grep", "Bash"}, set()),
    "cold-reader": ("sonnet", {"Read"}, set()),
    "cold-reader-deep": ("opus", {"Read"}, set()),
    "artifact-verifier": ("opus", {"Read", "Glob", "Grep", "Bash", "WebFetch", "WebSearch"}, set()),
}
SESSION_ROLES = {"manager", "architect", "implementer"}
PLUGIN = "bozz-agents"
MAX_DESCRIPTION_WORDS = 50
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
    parent = None
    for line in head.splitlines():
        key, colon, value = line.partition(":")
        if not colon:
            continue
        if line.startswith(" ") and parent:
            fields[f"{parent}.{key.strip()}"] = value.strip()
        else:
            parent = key.strip() if not value.strip() else None
            fields[key.strip()] = value.strip()
    return fields, body


def tool_list(value: str) -> tuple[set[str], set[str]]:
    """Split a tools line into plain tool names and the types inside Agent(...)."""
    agent_types: set[str] = set()
    match = re.search(r"Agent\(([^)]*)\)", value)
    if match:
        agent_types = {t.strip() for t in match.group(1).split(",") if t.strip()}
        value = value[:match.start()] + value[match.end():]
    return {t.strip() for t in value.split(",") if t.strip()}, agent_types


def folded(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


class AgentDefinitionTests(unittest.TestCase):
    def test_exactly_the_expected_roles(self):
        found = {p.stem for p in AGENTS.glob("*.md")}
        self.assertEqual(found, set(ROLES))

    def test_frontmatter_name_description_model_tools(self):
        for role, (model, tools, dispatches) in ROLES.items():
            with self.subTest(role=role):
                fields, body = frontmatter(AGENTS / f"{role}.md")
                self.assertEqual(fields.get("name"), role)
                description = fields.get("description", "")
                self.assertGreater(len(description), 80)
                self.assertLessEqual(len(description.split()), MAX_DESCRIPTION_WORDS,
                                     "every description is re-sent in each agent listing")
                self.assertIn(fields.get("model"), ALLOWED_MODELS)
                self.assertEqual(fields.get("model"), model)
                plain, agent_types = tool_list(fields.get("tools", ""))
                self.assertEqual(plain, tools)
                self.assertNotIn("Agent", plain, "Agent is listed only with the types it may dispatch")
                # each bozz-agents type appears plugin-scoped and bare (an install without the plugin)
                want = {t for t in dispatches if t == "general-purpose"}
                want |= {f"{PLUGIN}:{t}" for t in dispatches if t != "general-purpose"}
                want |= {t for t in dispatches if t != "general-purpose"}
                self.assertEqual(agent_types, want)
                self.assertTrue(body.strip())

    def test_read_only_reviewers_start_without_claude_md(self):
        for role in set(ROLES) - SESSION_ROLES:
            with self.subTest(role=role):
                self.assertEqual(frontmatter(AGENTS / f"{role}.md")[0].get("omitClaudeMd"), "true")

    def test_cache_lifetimes(self):
        # managers idle between wakes, so they keep the one-hour cache; workers call
        # without long gaps and stay on the default five minutes
        self.assertEqual(frontmatter(AGENTS / "manager.md")[0].get("experimental.cacheTtl"), "1h")
        for role in set(ROLES) - {"manager"}:
            with self.subTest(role=role):
                self.assertNotIn("experimental.cacheTtl", frontmatter(AGENTS / f"{role}.md")[0])
        briefs = folded(SHARED / "reference/manager/briefs.md")
        self.assertIn("claude --bg --effort high --name <session> --agent bozz-agents:architect", briefs)
        handoff = (SHARED / "scripts/manager-handoff.zsh").read_text(encoding="utf-8")
        self.assertIn('{"promptCacheTtl":"1h","idleCompaction":false}', handoff)

    def test_no_fable_model_anywhere(self):
        for path in list(AGENTS.rglob("*")) + list(CODEX.glob("*.toml")):
            if path.is_file() and path.suffix in {".md", ".json", ".toml", ".py", ".sh", ".zsh"}:
                with self.subTest(path=path.name):
                    self.assertNotRegex(path.read_text(encoding="utf-8").lower(), r"model\s*[:=]\s*\"?fable")

    def test_subagent_roles_cannot_write_or_dispatch(self):
        for role in set(ROLES) - SESSION_ROLES:
            with self.subTest(role=role):
                plain, agent_types = tool_list(frontmatter(AGENTS / f"{role}.md")[0]["tools"])
                self.assertFalse(plain & WRITE_TOOLS)
                self.assertFalse(agent_types)
                self.assertNotIn("Agent", plain)

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
                     "scripts/ctx.sh", "scripts/watch.zsh", "scripts/manager-handoff.zsh"):
            self.assertIn(name, manager)
        self.assertIn("scripts/ctxpct.sh", (SHARED / "worker-contract.md").read_text(encoding="utf-8"))

    def test_every_reference_trigger_names_an_existing_file(self):
        # the prompts name reference files by bare name behind a trigger; each must exist
        sources = {
            "manager": [AGENTS / "manager.md"],
            "worker": [SHARED / "worker-contract.md", AGENTS / "architect.md", AGENTS / "implementer.md"],
        }
        for folder, paths in sources.items():
            have = {p.name for p in (SHARED / "reference" / folder).glob("*.md")}
            named = set()
            for path in paths:
                named |= set(re.findall(r"`(?:[\w/]*reference/%s/)?([a-z-]+\.md)`" % folder, path.read_text()))
            named -= {"owner-talk.md", "owner-override.md", "worker-contract.md", "architect.md",
                      "work-folder.md"} if folder == "manager" else {"owner-talk.md", "owner-override.md",
                                                                      "worker-contract.md"}
            with self.subTest(folder=folder):
                self.assertTrue(named, "no reference triggers found")
                self.assertLessEqual(named, have, f"missing: {sorted(named - have)}")
                self.assertEqual(have - named, set(), "a reference file no prompt points at")

    def test_reference_files_open_with_their_trigger(self):
        for path in (SHARED / "reference").rglob("*.md"):
            with self.subTest(path=path.name):
                self.assertTrue(path.read_text(encoding="utf-8").startswith("Read this "))

    def test_shared_files_exist(self):
        for rel in ("worker-contract.md", "owner-talk.md", "owner-override.md", "shell_deny.py",
                    "shell-deny/destructive.json", "shell-deny/readonly.json", "claude-settings.example.json",
                    "build_codex_roles.py", "scripts/ctx.sh", "scripts/ctxpct.sh", "scripts/watch.zsh",
                    "scripts/sessions.zsh", "scripts/ctxcap.sh", "scripts/manager-handoff.zsh"):
            with self.subTest(rel=rel):
                self.assertTrue((SHARED / rel).is_file())

    def test_referenced_skills_exist(self):
        existing = {p.name for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file()}
        checks = [([AGENTS / f"{r}.md"] + sorted((SHARED / "reference/manager").glob("*.md"))
                   if r == "manager" else [AGENTS / f"{r}.md"], names)
                  for r, names in REFERENCED_SKILLS.items()]
        checks.append(([SHARED / "worker-contract.md", SHARED / "owner-talk.md"]
                       + sorted((SHARED / "reference/worker").glob("*.md")), SHARED_SKILLS))
        for paths, names in checks:
            path = paths[0]
            text = "".join(p.read_text(encoding="utf-8") for p in paths)
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
        for name in ("ctx.sh", "ctxpct.sh", "watch.zsh", "sessions.zsh", "ctxcap.sh", "manager-handoff.zsh"):
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
