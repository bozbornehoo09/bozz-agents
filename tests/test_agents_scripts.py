"""Tests for the manager/worker helper scripts in agents/shared/scripts/ and the
plugin hook in hooks/. Every test runs against a fake `claude` on PATH
(tests/data/agents/stub/claude) and temporary transcripts; none starts the
real CLI or a model.

Run with: python3 -I -m unittest discover -s tests -p 'test_agents*.py'
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "agents/shared/scripts"
HOOK = ROOT / "hooks/ctxcap-hook.sh"
STUB = ROOT / "tests/data/agents/stub"
HAVE_TOOLS = all(shutil.which(t) for t in ("zsh", "jq", "git"))


def call(message_id: str, tokens: int, sidechain: bool = False) -> dict:
    return {"type": "assistant", "isSidechain": sidechain,
            "message": {"id": message_id, "model": "claude-test",
                        "usage": {"input_tokens": 1, "cache_read_input_tokens": tokens - 1,
                                  "cache_creation_input_tokens": 0}}}


def write_transcript(path: Path, sizes: list[int], extra: list[dict] | None = None, age_s: float = 0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [call(f"m{i}", n) for i, n in enumerate(sizes)] + (extra or [])
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    if age_s:
        then = time.time() - age_s
        os.utime(path, (then, then))
    return path


class ScriptCase(unittest.TestCase):
    """A temporary home: a transcripts folder, a work root and the stub state."""

    def setUp(self):
        if not HAVE_TOOLS:
            self.skipTest("zsh, jq and git are needed")
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()
        self.projects = self.tmp / "projects"
        (self.projects / "p").mkdir(parents=True)
        self.root = self.tmp / "work_tracker"
        (self.root / "work").mkdir(parents=True)
        self.state = self.tmp / "agents.json"
        self.set_agents([])

    def tearDown(self):
        self._tmp.cleanup()

    def set_agents(self, agents: list[dict]) -> None:
        self.state.write_text(json.dumps({"agents": agents}), encoding="utf-8")

    def agents(self) -> dict[str, dict]:
        return {a.get("id") or a["sessionId"]: a for a in json.loads(self.state.read_text())["agents"]}

    def stub_calls(self) -> list[list[str]]:
        log = Path(f"{self.state}.log")
        return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []

    def env(self, **extra) -> dict:
        env = dict(os.environ, PATH=f"{STUB}:{os.environ['PATH']}", STUB_STATE=str(self.state),
                   CLAUDE_PROJECTS_DIR=str(self.projects), BOZZ_CTXCAP_DIR=str(self.tmp / "ctxcap"))
        env.pop("CLAUDE_CODE_SESSION_ID", None)
        env.update({k: str(v) for k, v in extra.items()})
        return env

    def run_zsh(self, script: str, *args, stdin: str | None = None, cwd=None, **env) -> subprocess.CompletedProcess:
        return subprocess.run(["zsh", str(SCRIPTS / script), *map(str, args)], input=stdin, text=True,
                              capture_output=True, env=self.env(**env), cwd=cwd, timeout=60)

    def folder(self, name: str, status: str, session: str | None = None, age_s: float = 0,
               handoff: str | None = None, doing: str = "editing a file") -> Path:
        d = self.root / "work" / name
        (d / "channel").mkdir(parents=True, exist_ok=True)
        (d / "BRIEF.md").write_text(f"Session: {session or 'proj-' + name}\n", encoding="utf-8")
        st = d / "STATUS.md"
        st.write_text(f"Session: {session or 'proj-' + name}\nSTATUS: {status}\nDoing now: {doing}\n", encoding="utf-8")
        if age_s:
            then = time.time() - age_s
            os.utime(st, (then, then))
        if handoff is not None:
            (d / "HANDOFF.md").write_text(handoff, encoding="utf-8")
        return d


class CtxcapTests(ScriptCase):
    def hook(self, agent_type="bozz-agents:architect", sizes=None, agent_id="", session="s1", **env):
        t = write_transcript(self.projects / "p" / f"{session}.jsonl", sizes or [])
        data = {"session_id": session, "transcript_path": str(t), "hook_event_name": "PostToolUse"}
        if agent_type is not None:
            data["agent_type"] = agent_type
        if agent_id:
            data["agent_id"] = agent_id
        return subprocess.run(["sh", str(HOOK)], input=json.dumps(data), text=True, capture_output=True,
                              env=self.env(**env), timeout=60)

    def note(self, result) -> str:
        self.assertEqual(result.returncode, 0, result.stderr)
        if not result.stdout.strip():
            return ""
        out = json.loads(result.stdout)
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PostToolUse")
        return out["hookSpecificOutput"]["additionalContext"]

    START = [20_000] * 16

    def test_silent_outside_the_session_roles(self):
        for agent_type in (None, "Explore", "general-purpose", "other-plugin:architect", "bozz-agents:review-specialist"):
            with self.subTest(agent_type=agent_type):
                self.assertEqual(self.note(self.hook(agent_type, self.START + [400_000])), "")

    def test_silent_inside_a_subagent(self):
        self.assertEqual(self.note(self.hook(sizes=self.START + [400_000], agent_id="a1")), "")

    def test_silent_below_85_percent_of_the_cap(self):
        self.assertEqual(self.note(self.hook(sizes=self.START + [290_000])), "")

    def test_lean_note_from_85_percent_once_per_step(self):
        first = self.note(self.hook(sizes=self.START + [300_000]))
        self.assertIn("300k tokens of this session's 350k cap", first)
        self.assertIn("start no new review pass", first)
        self.assertEqual(self.note(self.hook(sizes=self.START + [300_000, 305_000])), "")
        self.assertIn("310k", self.note(self.hook(sizes=self.START + [300_000, 310_000])))

    def test_hand_off_note_at_the_cap(self):
        text = self.note(self.hook("bozz-agents:architect", self.START + [352_000]))
        self.assertIn("at or past this session's 350k cap", text)
        self.assertIn("Hand off now", text)

    def test_manager_cap_is_smaller_and_caps_are_configurable(self):
        self.assertIn("150k cap", self.note(self.hook("bozz-agents:manager", self.START + [151_000])))
        self.assertIn("200k cap", self.note(self.hook("bozz-agents:implementer", self.START + [180_000],
                                                     session="s2", BOZZ_CTXCAP_WORKER_K=200)))

    def test_manager_is_pointed_to_succession(self):
        at_cap = self.note(self.hook("bozz-agents:manager", self.START + [151_000]))
        self.assertIn("Succession", at_cap)
        self.assertNotIn("Handoff rules", at_cap)
        lean = self.note(self.hook("bozz-agents:manager", self.START + [130_000], session="s2"))
        self.assertIn("Succession", lean)
        self.assertIn("Handoff rules", self.note(self.hook("bozz-agents:architect", self.START + [352_000],
                                                           session="s3")))

    def test_bare_role_names_only_when_opted_in(self):
        for i, role in enumerate(("manager", "architect", "implementer")):
            with self.subTest(role=role):
                self.assertEqual(self.note(self.hook(role, self.START + [400_000], session=f"b{i}")), "")
                self.assertIn("cap", self.note(self.hook(role, self.START + [400_000], session=f"o{i}",
                                                         BOZZ_CTXCAP_BARE=1)))
        self.assertEqual(self.note(self.hook("other-plugin:manager", self.START + [400_000], session="x",
                                             BOZZ_CTXCAP_BARE=1)), "")

    def test_a_successor_that_starts_large_is_not_told_to_hand_off(self):
        self.assertEqual(self.note(self.hook(sizes=[330_000] * 3 + [340_000] * 14)), "")
        self.assertNotEqual(self.note(self.hook(sizes=[330_000] * 3 + [340_000] * 14 + [385_000])), "")

    def test_a_hold_quiets_it_for_40k(self):
        sizes = self.START + [360_000]
        write_transcript(self.projects / "p/s1.jsonl", sizes)
        result = self.run_zsh("ctxcap.sh", "hold", "s1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.tmp / "ctxcap/s1/hold").read_text().strip(), "360")
        self.assertEqual(self.note(self.hook(sizes=self.START + [390_000])), "")
        self.assertIn("400k", self.note(self.hook(sizes=self.START + [400_000])))

    def test_switched_off(self):
        self.assertEqual(self.note(self.hook(sizes=self.START + [400_000], BOZZ_CTXCAP="off")), "")

    def test_subagent_calls_do_not_count(self):
        t = write_transcript(self.projects / "p/s1.jsonl", self.START, extra=[call("x", 900_000, sidechain=True)])
        result = self.run_zsh("ctxpct.sh", "-k", "s1")
        self.assertEqual(result.stdout.strip(), "20")
        self.assertTrue(t.exists())

    def test_hooks_json_runs_the_wrapper(self):
        data = json.loads((ROOT / "hooks/hooks.json").read_text())
        entry = data["hooks"]["PostToolUse"][0]["hooks"][0]
        self.assertEqual(entry["type"], "command")
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/hooks/ctxcap-hook.sh", entry["command"])
        self.assertNotIn("PreToolUse", data["hooks"], "the shell guard stays opt-in (ADR-0005)")


class WatchTests(ScriptCase):
    PREFIX = "proj-"

    def worker(self, wid: str, name: str, status: str | None = "idle", size: int = 20_000) -> dict:
        sid = f"{wid}-0000-0000-0000-0000abcd0000"
        write_transcript(self.projects / "p" / f"{sid}.jsonl", [size], age_s=3600)
        return {"id": wid, "sessionId": sid, "name": name, "status": status, "startedAt": 1}

    def snap(self, *flags):
        return self.run_zsh("watch.zsh", "snap", self.root, self.PREFIX, *flags)

    def start(self, minutes=2):
        return self.run_zsh("watch.zsh", "start", self.root, "-m", minutes, BOZZ_WATCH_POLL=0.2)

    def test_snap_reports_first_then_no_change(self):
        self.folder("a", "WORKING")
        self.set_agents([self.worker("aaaa1111", "proj-a")])
        self.assertIn("first snapshot:", self.snap("-i", "aaaa1111").stdout)
        self.assertIn("no change since the last snapshot", self.snap("-i", "aaaa1111").stdout)

    def test_doing_now_alone_does_not_wake(self):
        d = self.folder("a", "WORKING")
        self.set_agents([self.worker("aaaa1111", "proj-a")])
        self.snap("-i", "aaaa1111")
        (d / "STATUS.md").write_text("Session: proj-a\nSTATUS: WORKING\nDoing now: something else\n")
        self.assertIn("no change in 2 minutes", self.start().stdout)

    def test_status_change_wakes(self):
        d = self.folder("a", "WORKING")
        self.set_agents([self.worker("aaaa1111", "proj-a")])
        self.snap("-i", "aaaa1111")
        (d / "STATUS.md").write_text("Session: proj-a\nSTATUS: DONE: abc123\n")
        out = self.start().stdout
        self.assertIn("STATUS: DONE: abc123", out)

    def test_size_past_the_worker_cap_shows(self):
        self.folder("a", "WORKING")
        self.set_agents([self.worker("aaaa1111", "proj-a", size=365_000)])
        self.assertIn("ctx aaaa1111 over 350k", self.snap("-i", "aaaa1111").stdout)
        self.set_agents([self.worker("aaaa1111", "proj-a", size=355_000)])
        self.snap("-i", "aaaa1111")
        self.assertNotIn("ctx aaaa1111", (self.root / ".watcher.snap").read_text())

    def test_blocker_lines(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / "doc.md").write_text("x\n")
        subprocess.run(["git", "-C", str(self.root), "add", "doc.md"], check=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@example.com",
                        "commit", "-qm", "doc"], check=True)
        self.folder("a", "WAITING-ON-MANAGER: proj-b in doc.md Retries")
        self.folder("b", "WORKING", doing="review pass over doc.md")
        out = self.snap().stdout
        self.assertIn("work/b/STATUS.md:Doing now: review pass over doc.md", out)
        self.assertIn("blocker doc.md clean", out)
        (self.root / "doc.md").write_text("y\n")
        self.assertIn("blocker doc.md dirty", self.snap().stdout)

    def test_respawns_a_retired_waiter(self):
        self.folder("a", "WAITING-ON-OWNER: retry limit")
        self.set_agents([self.worker("aaaa1111", "proj-a", status=None)])
        self.snap("-i", "aaaa1111")
        out = self.start().stdout
        self.assertIn("respawned aaaa1111", out)
        self.assertIn(["respawn", "aaaa1111"], self.stub_calls())

    def test_does_not_respawn_a_finished_worker(self):
        self.folder("a", "DONE: abc123")
        self.set_agents([self.worker("aaaa1111", "proj-a", status=None)])
        self.snap("-i", "aaaa1111")
        self.start(minutes=1)
        self.assertNotIn(["respawn", "aaaa1111"], self.stub_calls())

    def test_respawn_gives_up_after_three_tries(self):
        self.folder("a", "WORKING")
        self.set_agents([self.worker("aaaa1111", "proj-a", status=None)])
        self.snap("-i", "aaaa1111")
        result = self.run_zsh("watch.zsh", "start", self.root, "-m", 6, BOZZ_WATCH_POLL=0.1, STUB_RESPAWN="fail")
        self.assertIn("respawn of aaaa1111 keeps failing", result.stdout)

    # stop ---------------------------------------------------------------
    def stop(self, wid, folder, minutes=1):
        return self.run_zsh("watch.zsh", "stop", self.root, wid, folder, "-m", minutes, BOZZ_WATCH_POLL=0.1)

    def test_stop_refuses_a_live_listed_id(self):
        self.folder("a", "DONE: abc")
        self.set_agents([self.worker("aaaa1111", "proj-a")])
        self.snap("-i", "aaaa1111")
        self.assertIn("still a live (-i) id", self.stop("aaaa1111", "a").stdout)

    def test_stop_refuses_a_working_session(self):
        self.folder("a", "WORKING")
        self.set_agents([self.worker("aaaa1111", "proj-a")])
        self.snap()
        self.assertIn("STATUS.md says STATUS: WORKING", self.stop("aaaa1111", "a").stdout)

    def test_stop_a_done_session_once_quiet(self):
        self.folder("a", "DONE: abc")
        self.set_agents([self.worker("aaaa1111", "proj-a")])
        self.snap()
        self.assertIn("stopped aaaa1111", self.stop("aaaa1111", "a").stdout)
        self.assertIsNone(self.agents()["aaaa1111"]["status"])

    def commit_handoff(self, folder: str, session: str) -> None:
        """Commit work/<folder>/HANDOFF.md with a subject tagged [<session>], as a worker does."""
        env = self.env(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
                       GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")
        def git(*args):
            subprocess.run(["git", "-C", str(self.tmp), *args], check=True, capture_output=True, env=env)
        if not (self.tmp / ".git").exists():
            git("init", "-q", "-b", "main")
        git("add", f"work_tracker/work/{folder}/HANDOFF.md")
        git("commit", "-q", "-m", f"[{session}] handoff work/{folder}")

    def test_stop_an_old_owner_wait_with_a_handoff(self):
        self.folder("a", "WAITING-ON-OWNER: retry limit", age_s=1900, handoff="Goal: x\nOpen reviews: none\n")
        self.commit_handoff("a", "proj-a")
        self.set_agents([self.worker("aaaa1111", "proj-a")])
        self.snap()
        self.assertIn("stopped aaaa1111", self.stop("aaaa1111", "a").stdout)

    def test_no_stop_of_an_owner_wait_on_a_handoff_it_did_not_commit(self):
        self.folder("a", "WAITING-ON-OWNER: retry limit", age_s=1900, handoff="Goal: x\nOpen reviews: none\n")
        self.folder("b", "WAITING-ON-OWNER: retry limit", age_s=1900, handoff="Goal: x\nOpen reviews: none\n")
        self.commit_handoff("b", "proj-b-1")      # a predecessor's, not proj-b's
        self.set_agents([self.worker("aaaa1111", "proj-a"), self.worker("bbbb2222", "proj-b")])
        self.snap()
        for wid, folder in (("aaaa1111", "a"), ("bbbb2222", "b")):
            with self.subTest(folder=folder):
                out = self.stop(wid, folder).stdout
                self.assertIn(f"HANDOFF.md has no commit tagged [proj-{folder}]", out)
                self.assertEqual(self.agents()[wid]["status"], "idle")

    def test_no_stop_of_an_owner_wait_with_open_reviews_or_too_young(self):
        self.folder("a", "WAITING-ON-OWNER: retry limit", age_s=1900,
                    handoff="Open reviews: work_tracker/reviews/active/doc.md\n")
        self.folder("b", "WAITING-ON-OWNER: retry limit", age_s=60, handoff="Open reviews: none\n")
        self.commit_handoff("a", "proj-a")
        self.set_agents([self.worker("aaaa1111", "proj-a"), self.worker("bbbb2222", "proj-b")])
        self.snap()
        self.assertIn("lists open reviews", self.stop("aaaa1111", "a").stdout)
        self.assertIn("says STATUS: WAITING-ON-OWNER", self.stop("bbbb2222", "b").stdout)

    def test_stop_a_predecessor_whose_brief_names_a_successor(self):
        self.folder("a", "WORKING", session="proj-a-2", handoff="Goal: x\n")
        self.set_agents([self.worker("aaaa1111", "proj-a"), self.worker("cccc3333", "proj-a-2", status="busy")])
        self.snap()
        self.assertIn("stopped aaaa1111", self.stop("aaaa1111", "a").stdout)
        self.assertEqual(self.agents()["cccc3333"]["status"], "busy")

    def test_stop_a_session_busy_only_with_its_own_background_task(self):
        self.folder("a", "DONE: abc")
        w = self.worker("aaaa1111", "proj-a", status="busy")
        t = self.projects / "p" / f"{w['sessionId']}.jsonl"
        write_transcript(t, [20_000], extra=[{"type": "system", "subtype": "turn_duration"}], age_s=3600)
        self.set_agents([w])
        self.snap()
        self.assertIn("stopped aaaa1111", self.stop("aaaa1111", "a").stdout)

    def test_no_stop_mid_turn(self):
        self.folder("a", "DONE: abc")
        self.set_agents([self.worker("aaaa1111", "proj-a", status="busy")])
        self.snap()
        self.assertIn("no ten-minute idle, quiet window", self.stop("aaaa1111", "a").stdout)


class HandoffTests(ScriptCase):
    PREFIX = "proj-manager-"
    OLD = "aaaaaaaa-1111-2222-3333-4444abcd4444"

    def setUp(self):
        super().setUp()
        self.next = self.root / "NEXT-SESSION-PROMPT.md"
        self.next.write_text("next\n")
        write_transcript(self.projects / "p" / f"{self.OLD}.jsonl", [151_000], age_s=3600)
        self.set_agents([{"id": self.OLD[:8], "sessionId": self.OLD, "name": self.PREFIX + "4",
                          "status": "idle", "startedAt": 1, "cwd": str(self.tmp)}])
        self.current_file = self.root / "CURRENT-MANAGER"
        self.current_file.write_text(f"{self.PREFIX}4 {self.OLD[:8]} {self.OLD} 2026-11-27T10:00Z\n")

    def handoff(self, *args, me=OLD, **env):
        script = SCRIPTS / "manager-handoff.zsh"
        base = dict(STUB_HANDOFF=script, STUB_ROOT=self.root, STUB_PREFIX=self.PREFIX,
                    BOZZ_HANDOFF_WAIT=3, BOZZ_HANDOFF_START_WAIT=2, BOZZ_HANDOFF_POLL=0.5,
                    BOZZ_HANDOFF_QUIET=0, BOZZ_HANDOFF_STOP_WAIT=0)
        if me:
            base["CLAUDE_CODE_SESSION_ID"] = me
        base.update(env)
        return self.run_zsh("manager-handoff.zsh", *args, **base)

    def current(self) -> list[str]:
        return self.current_file.read_text().split() if self.current_file.exists() else []

    def test_hand_off_to_the_next_number(self):
        result = self.handoff("handoff", self.root, self.PREFIX, self.next)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("handed off: proj-manager-5", result.stdout)
        new = next(a for a in self.agents().values() if a["name"] == "proj-manager-5")
        self.assertEqual(self.current()[0], "proj-manager-5")
        self.assertEqual(json.loads(new["settings"]), {"promptCacheTtl": "1h", "idleCompaction": False})
        self.assertEqual(new["agent"], "bozz-agents:manager")
        self.assertEqual(new["prompt"], f"Run {self.next}")
        self.assertEqual(new["cwd"], str(self.tmp))
        self.assertIsNone(self.agents()[self.OLD[:8]]["status"], "the old manager is stopped")
        self.assertFalse((self.root / ".manager-handoff.owner").exists())

    def test_failed_handoff_restores_the_manager_and_records_a_hold(self):
        result = self.handoff("handoff", self.root, self.PREFIX, self.next, STUB_LAUNCH="silent")
        self.assertEqual(result.returncode, 1)
        self.assertIn("did not claim", result.stdout)
        self.assertEqual(self.current()[2], self.OLD)
        self.assertEqual((self.tmp / "ctxcap" / self.OLD / "hold").read_text().strip(), "151")
        new = next(a for a in self.agents().values() if a["name"] == "proj-manager-5")
        self.assertIsNone(new["status"], "the silent successor is stopped")
        self.assertEqual(self.agents()[self.OLD[:8]]["status"], "idle")

    def test_untrusted_folder_fails_fast(self):
        result = self.handoff("handoff", self.root, self.PREFIX, self.next, STUB_LAUNCH="untrusted")
        self.assertEqual(result.returncode, 1)
        self.assertIn("did not start", result.stdout)
        self.assertIn("Workspace not trusted", result.stdout)

    def test_successor_that_dies_fails(self):
        result = self.handoff("handoff", self.root, self.PREFIX, self.next, STUB_LAUNCH="die")
        self.assertEqual(result.returncode, 1)
        self.assertIn("ended before it claimed", result.stdout)

    def test_second_handoff_is_refused_while_one_runs(self):
        slow = subprocess.Popen(["zsh", str(SCRIPTS / "manager-handoff.zsh"), "handoff", str(self.root), self.PREFIX,
                                 str(self.next)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=self.env(CLAUDE_CODE_SESSION_ID=self.OLD, STUB_LAUNCH="silent",
                                             STUB_HANDOFF=SCRIPTS / "manager-handoff.zsh", STUB_ROOT=self.root,
                                             STUB_PREFIX=self.PREFIX, BOZZ_HANDOFF_WAIT=4,
                                             BOZZ_HANDOFF_START_WAIT=4, BOZZ_HANDOFF_POLL=0.5))
        try:
            for _ in range(50):
                if (self.root / ".manager-handoff.owner").exists():
                    break
                time.sleep(0.1)
            second = self.handoff("handoff", self.root, self.PREFIX, self.next)
            self.assertEqual(second.returncode, 3, second.stdout)
            guard = self.handoff("current", self.root)
            self.assertEqual(guard.returncode, 1, "the wake guard fails while a handoff runs")
        finally:
            slow.communicate(timeout=60)

    def test_first_manager(self):
        self.current_file.unlink()
        self.set_agents([])
        result = self.handoff("first", self.root, self.PREFIX, self.next, me=None)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.current()[0], "proj-manager-1")

    def test_claim_refused_while_another_manager_is_live(self):
        other = "bbbbbbbb-1111-2222-3333-4444abcd4444"
        result = self.handoff("claim", self.root, self.PREFIX, me=other)
        self.assertEqual(result.returncode, 1)
        self.assertIn("the manager is proj-manager-4", result.stdout)
        self.assertEqual(self.current()[2], self.OLD)

    def test_claim_once_the_old_manager_is_gone_and_reclaim_is_a_no_op(self):
        agents = list(self.agents().values())
        agents[0]["status"] = None
        self.set_agents(agents)
        other = "bbbbbbbb-1111-2222-3333-4444abcd4444"
        self.assertEqual(self.handoff("claim", self.root, self.PREFIX, me=other).returncode, 0)
        self.assertEqual(self.current()[2], other)
        again = self.handoff("claim", self.root, self.PREFIX, me=other)
        self.assertEqual(again.returncode, 0)
        self.assertIn("already the manager", again.stdout)

    # an interactive session, as the agent view lists it: no id
    def interactive(self, session_id: str, name: str | None, status: str = "idle") -> dict:
        row = {"pid": 4242, "cwd": str(self.tmp), "kind": "interactive", "startedAt": 2,
               "sessionId": session_id, "status": status, "state": "working"}
        if name:
            row["name"] = name
        return row

    def test_interactive_manager_claims(self):
        self.current_file.unlink()
        mine = "cccccccc-1111-2222-3333-4444abcd4444"
        self.set_agents([self.interactive(mine, self.PREFIX + "1")])
        result = self.handoff("claim", self.root, self.PREFIX, me=mine)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.current()[:3], [self.PREFIX + "1", "-", mine])
        self.assertEqual(self.handoff("current", self.root, me=mine).returncode, 0)

    def test_second_interactive_session_cannot_claim_while_the_first_is_live(self):
        first, second = "cccccccc-1111-2222-3333-4444abcd4444", "dddddddd-1111-2222-3333-4444abcd4444"
        # the owner started the first without --name, so only CURRENT-MANAGER ties it to the role
        self.set_agents([self.interactive(first, None), self.interactive(second, self.PREFIX + "2")])
        self.current_file.write_text(f"unnamed - {first} 2026-11-27T10:00Z\n")
        result = self.handoff("claim", self.root, self.PREFIX, me=second)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("another manager is live", result.stdout)
        self.assertEqual(self.current()[2], first)
        self.set_agents([{**self.interactive(first, None), "status": None, "state": "done"},
                         self.interactive(second, self.PREFIX + "2")])
        self.assertEqual(self.handoff("claim", self.root, self.PREFIX, me=second).returncode, 0)
        self.assertEqual(self.current()[2], second)

    def test_hand_off_from_an_interactive_manager(self):
        self.set_agents([self.interactive(self.OLD, self.PREFIX + "4")])
        result = self.handoff("handoff", self.root, self.PREFIX, self.next)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("handed off: proj-manager-5", result.stdout)
        self.assertIn("not listed as a background session: close it yourself", result.stdout)
        self.assertEqual(self.current()[0], "proj-manager-5")
        self.assertEqual(self.agents()[self.OLD]["status"], "idle", "an interactive session is left to the owner")
        self.assertFalse(any(c[:1] == ["stop"] for c in self.stub_calls()))

    def test_current_is_the_wake_guard(self):
        self.assertEqual(self.handoff("current", self.root).returncode, 0)
        other = self.handoff("current", self.root, me="bbbbbbbb-1111-2222-3333-4444abcd4444")
        self.assertEqual(other.returncode, 1)
        self.assertIn("proj-manager-4", other.stdout)

    def test_no_session_id_means_succession_is_off(self):
        result = self.handoff("claim", self.root, self.PREFIX, me=None)
        self.assertEqual(result.returncode, 0)
        self.assertIn("not in use", result.stdout)

    def test_bad_arguments(self):
        self.assertEqual(self.handoff("handoff", self.root, self.PREFIX, self.root / "missing.md").returncode, 2)
        self.assertEqual(self.handoff("nonsense", self.root).returncode, 2)


if __name__ == "__main__":
    unittest.main()
