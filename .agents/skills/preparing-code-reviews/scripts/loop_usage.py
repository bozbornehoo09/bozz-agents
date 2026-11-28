"""Per-attempt usage bookkeeping for review-loop.sh.

Subcommands:

  loop_usage.py result [--raw] <attempt.out> <report.md>
      Copy one attempt's answer into <report.md>. By default <attempt.out> is
      the JSON object `claude -p --output-format json` prints, and the answer
      is its `result` string. With --raw (another reviewer via REVIEW_CMD) the
      whole file is the answer. Exits 1 when the answer is empty.

  loop_usage.py summary <loop-dir>
      Gather every <report>.md.<n>.out in <loop-dir> into <loop-dir>/usage.json
      (one row per attempt, plus totals) and print a single USAGE line.

  loop_usage.py unavailable <report.md>
      Succeeds (status 0) only if the newest attempt of <report.md> failed
      because its model is unavailable, as said on its stderr, in the JSON
      `errors` list, or in an error `result`.

The parser is deliberately lenient. The fields it reads are `type` ("result"),
`subtype`, `is_error`, `result`, `errors`, `session_id`, `num_turns`,
`duration_ms`, `total_cost_usd` and the per-model breakdown, which it accepts
as `modelUsage` or `model_usage`, with token keys in camelCase or snake_case.
Anything absent is recorded as null, never guessed. An attempt that printed no
parsable result (a crash, or a reviewer that is not Claude Code) still counts
as an attempt, marked `telemetry: missing`. Cost is the CLI's own client-side
estimate, not a bill. The top-level `usage` field duplicates the per-model
counts and is not added in.
"""
import json
import re
import sys
from pathlib import Path

ATTEMPT_NAME = re.compile(r"^(?P<report>.+\.md)\.(?P<n>\d+)\.out$")
TOKEN_KEYS = {
    "input": ("inputTokens", "input_tokens"),
    "cache_read": ("cacheReadInputTokens", "cache_read_input_tokens"),
    "cache_write": ("cacheCreationInputTokens", "cache_creation_input_tokens"),
    "output": ("outputTokens", "output_tokens"),
}
# Row field <- result field, copied as found (None when absent).
COPIED = {"subtype": "subtype", "is_error": "is_error", "session_id": "session_id",
          "turns": "num_turns", "duration_ms": "duration_ms"}
MODEL_GONE = re.compile(r"model\b.{0,60}?\b(unavailable|not available|not found|does not exist)", re.I | re.S)


def slurp(path):
    """File text, or "" when it cannot be read."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def read_result(path):
    """The attempt's JSON result object, or None when there is none."""
    try:
        data = json.loads(slurp(path))
    except ValueError:
        return None
    is_result = isinstance(data, dict) and data.get("type") == "result"
    return data if is_result else None


def cmd_result(args):
    raw = args[0] == "--raw"
    attempt, report = args[-2:]
    if raw:
        answer = slurp(attempt)
    else:
        answer = (read_result(attempt) or {}).get("result")
        if not isinstance(answer, str):
            answer = ""
    Path(report).write_text(answer, encoding="utf-8")
    return 1 if answer.strip() == "" else 0


def model_breakdown(data):
    models = data.get("modelUsage", data.get("model_usage"))
    if not isinstance(models, dict):
        return None
    out = {}
    for name, entry in models.items():
        entry = entry if isinstance(entry, dict) else {}
        counts = {}
        for key, spellings in TOKEN_KEYS.items():
            value = next((entry[s] for s in spellings if isinstance(entry.get(s), (int, float))), 0)
            counts[key] = int(value)
        out[str(name)] = counts
    return out


def attempt_row(path, match):
    row = {"report": match["report"], "attempt": int(match["n"]), "file": path.name}
    data = read_result(path)
    cost = data.get("total_cost_usd") if data else None
    models = model_breakdown(data) if data else None
    if data is None or not isinstance(cost, (int, float)) or models is None:
        row["telemetry"] = "missing"
        return row
    row["telemetry"] = "present"
    row.update({mine: data.get(theirs) for mine, theirs in COPIED.items()})
    row["cost_estimate_usd"] = float(cost)
    row["models"] = models
    return row


def cmd_summary(args):
    loop = Path(args[0])
    names = sorted(p.name for p in loop.iterdir()) if loop.is_dir() else []
    rows = [attempt_row(loop / name, m) for name in names if (m := ATTEMPT_NAME.match(name))]
    rows.sort(key=lambda r: (r["report"], r["attempt"]))
    counted = [r for r in rows if r["telemetry"] == "present"]

    per_model = {}
    for r in counted:
        for name, counts in r["models"].items():
            bucket = per_model.setdefault(name, dict.fromkeys(TOKEN_KEYS, 0))
            for key, value in counts.items():
                bucket[key] += value
    spent = round(sum(r["cost_estimate_usd"] for r in counted), 6)
    n_sessions = len({r["report"] for r in rows})
    totals = {"attempt_count": len(rows), "session_count": n_sessions,
              "retries": len(rows) - n_sessions, "without_telemetry": len(rows) - len(counted),
              "cost_estimate_usd": spent, "tokens_by_model": per_model}

    target = loop / "usage.json"
    if loop.is_dir():
        record = {"totals": totals, "attempts": rows}
        target.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    tok = {key: sum(m[key] for m in per_model.values()) for key in TOKEN_KEYS}
    parts = [
        f"attempts {len(rows)}, sessions {n_sessions}, retried {totals['retries']}, "
        f"no telemetry {totals['without_telemetry']}",
        f"estimated ${spent:.2f}",
        f"tokens input {tok['input']:,} / cache read {tok['cache_read']:,} / "
        f"cache write {tok['cache_write']:,} / output {tok['output']:,}",
        f"models: {', '.join(sorted(per_model)) or 'none'}",
        str(target),
    ]
    print("USAGE: " + "; ".join(parts))
    return 0


def cmd_unavailable(args):
    report = Path(args[0])
    newest = max((int(m["n"]) for p in report.parent.glob(report.name + ".*.out")
                  if (m := ATTEMPT_NAME.match(p.name)) and m["report"] == report.name), default=None)
    if newest is None:
        return 1
    # Only the newest attempt decides: <report>.err accumulates every attempt's stderr.
    stem = report.parent / f"{report.name}.{newest}"
    evidence = [slurp(f"{stem}.err")]
    data = read_result(f"{stem}.out")
    if data is None:
        evidence.append(slurp(f"{stem}.out"))
    else:
        # A parsed result may be a review that merely mentions models; read its error fields only.
        errors = data.get("errors")
        evidence += [str(e) for e in errors] if isinstance(errors, list) else []
        if data.get("is_error") and isinstance(data.get("result"), str):
            evidence.append(data["result"])
    return 0 if any(MODEL_GONE.search(text) for text in evidence) else 1


def main(argv):
    cmd, args = (argv[0], argv[1:]) if argv else ("", [])
    arity_ok = {
        "result": len(args) == 2 or (len(args) == 3 and args[:1] == ["--raw"]),
        "summary": len(args) == 1,
        "unavailable": len(args) == 1,
    }
    if not arity_ok.get(cmd, False):
        sys.stderr.write(__doc__)
        return 2
    handler = {"result": cmd_result, "summary": cmd_summary, "unavailable": cmd_unavailable}[cmd]
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
