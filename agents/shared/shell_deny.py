#!/usr/bin/env python3
"""Check a shell command against a bozz-agents shell deny family.

The families live beside this script in shell-deny/<family>.json. Each holds
rules ({id, reason, pattern, examples}) and a list of safe commands; a family
may extend another. A rule's pattern is a Python regular expression searched
anywhere in the command, after runs of whitespace are folded to one space, so
wrappers (`env X`, `bash -c 'X'`, `/usr/bin/X`) and chained commands are seen.

Two uses:

  As a Claude Code PreToolUse hook on the Bash tool (reads the hook's JSON on
  stdin; exit 2 blocks the call and the reason on stderr goes to the agent;
  exit 0 leaves the normal permission flow to decide):

      python3 -I /abs/path/agents/shared/shell_deny.py --family destructive

  By hand, to see what a command would hit:

      python3 -I shell_deny.py --family readonly --command 'git fetch'

The lists are deliberately conservative: a pattern can match text inside a
quoted argument (`grep 'aws s3 rm' notes.md`). They are a guard against
accidents, not a sandbox; a command that reaches a target indirectly (a
variable, a script file) is not seen.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LISTS = HERE / "shell-deny"


def load_family(name: str, lists: Path = LISTS) -> list[dict]:
    """Return the family's rules, inherited ones first."""
    data = json.loads((lists / f"{name}.json").read_text(encoding="utf-8"))
    rules = load_family(data["extends"], lists) if data.get("extends") else []
    return rules + data["rules"]


def normalize(command: str) -> str:
    return re.sub(r"\s+", " ", command.replace("\\\n", " ")).strip()


def matches(command: str, rules: list[dict]) -> list[dict]:
    text = normalize(command)
    return [r for r in rules if re.search(r["pattern"], text)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--family", default="destructive")
    parser.add_argument("--command", help="check this command instead of reading hook JSON on stdin")
    args = parser.parse_args(argv)
    rules = load_family(args.family)

    if args.command is not None:
        hits = matches(args.command, rules)
        for r in hits:
            print(f"DENY {r['id']}: {r['reason']}")
        if not hits:
            print("ok")
        return 2 if hits else 0

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # not a hook call we understand; leave it to the permission flow
    if payload.get("tool_name") not in (None, "Bash"):
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    hits = matches(command, rules)
    if hits:
        reasons = "; ".join(f"{r['id']}: {r['reason']}" for r in hits)
        print(f"Blocked by the {args.family} shell deny list ({reasons}). "
              "Ask the owner to run it, or to give an owner override for this task.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
