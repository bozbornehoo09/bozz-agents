#!/usr/bin/env python3
"""Deterministic append-only bridge operations for cross-agent reviews.

The file is deliberately standard-library-only.  It uses advisory locks,
O_APPEND writes, fsync, transition validation, and tail verification so agents
never have to allocate global entry numbers or patch a textual EOF anchor.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sys
import tempfile
import time
from typing import Any, Iterator


PROTOCOL_VERSION = "1"
EVENT_RE = re.compile(
    r"^## \[(?P<seq>\d+)\] (?P<actor>REQUESTER|REVIEWER) → "
    r"(?P<target>REQUESTER|REVIEWER) — (?P<kind>[A-Z_]+)$",
    re.MULTILINE,
)
FIELD_RE = re.compile(r"^(?P<key>[A-Z][A-Z0-9_]*): (?P<value>.*)$")
RESERVED_BODY_FIELD_RE = re.compile(
    r"^(?:EVENT_ID|TIMESTAMP|IN_REPLY_TO|REVISION|EXPECTED_BY|GRACE|NEXT_UPDATE_BY|STATUS): ",
    re.MULTILINE,
)
RESERVED_EVENT_FIELDS = frozenset(
    {
        "EVENT_ID",
        "TIMESTAMP",
        "IN_REPLY_TO",
        "REVISION",
        "EXPECTED_BY",
        "GRACE",
        "NEXT_UPDATE_BY",
        "STATUS",
    }
)
TERMINAL_STATUSES = frozenset({"CLOSED", "ABANDONED", "SUPERSEDED", "STOPPED"})
NONTERMINAL_STATUSES = frozenset(
    {"READY_FOR_REVIEW", "REVIEWING", "REVIEW_COMPLETE", "ADJUDICATING_FINDINGS", "FOLD_COMPLETE", "WORK_IN_PROGRESS"}
)
REVISION_EVENT_KINDS = frozenset({"REVIEW_REQUESTED", "REVIEW", "RESPONSE", "CLOSE"})
REQUIRED_HEADER_FIELDS = frozenset(
    {
        "PROTOCOL_VERSION",
        "REVIEW_ID",
        "KIND",
        "SUBJECT",
        "REVIEW_SKILL",
        "REQUESTER",
        "REVIEWER",
        "CREATED_AT",
        "BASE_REVISION",
        "HEAD_REVISION",
    }
)

ALLOWED_EVENTS: dict[tuple[str, str], frozenset[str]] = {
    ("REQUESTER", "REVIEW_REQUESTED"): frozenset({"READY_FOR_REVIEW"}),
    ("REQUESTER", "WORK_UPDATE"): frozenset({"WORK_IN_PROGRESS"}),
    ("REQUESTER", "FOLD_STARTED"): frozenset({"ADJUDICATING_FINDINGS"}),
    ("REQUESTER", "FOLD_PROGRESS"): frozenset({"ADJUDICATING_FINDINGS"}),
    ("REQUESTER", "RESPONSE"): frozenset({"FOLD_COMPLETE"}),
    ("REQUESTER", "CLOSE"): TERMINAL_STATUSES,
    ("REVIEWER", "REVIEW_STARTED"): frozenset({"REVIEWING"}),
    ("REVIEWER", "REVIEW_PROGRESS"): frozenset({"REVIEWING"}),
    ("REVIEWER", "REVIEW"): frozenset({"REVIEW_COMPLETE"}),
}

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "READY_FOR_REVIEW": frozenset({"REVIEWING", *TERMINAL_STATUSES}),
    "REVIEWING": frozenset({"REVIEWING", "REVIEW_COMPLETE", *TERMINAL_STATUSES}),
    "REVIEW_COMPLETE": frozenset({"ADJUDICATING_FINDINGS", *TERMINAL_STATUSES}),
    "ADJUDICATING_FINDINGS": frozenset({"ADJUDICATING_FINDINGS", "FOLD_COMPLETE", *TERMINAL_STATUSES}),
    "FOLD_COMPLETE": frozenset({"WORK_IN_PROGRESS", "READY_FOR_REVIEW", *TERMINAL_STATUSES}),
    "WORK_IN_PROGRESS": frozenset({"WORK_IN_PROGRESS", "READY_FOR_REVIEW", *TERMINAL_STATUSES}),
}

ALLOWED_PREVIOUS_BY_KIND: dict[str, frozenset[str]] = {
    "REVIEW_STARTED": frozenset({"READY_FOR_REVIEW"}),
    "REVIEW_PROGRESS": frozenset({"REVIEWING"}),
    "REVIEW": frozenset({"REVIEWING"}),
    "FOLD_STARTED": frozenset({"REVIEW_COMPLETE"}),
    "FOLD_PROGRESS": frozenset({"ADJUDICATING_FINDINGS"}),
    "RESPONSE": frozenset({"ADJUDICATING_FINDINGS"}),
    "REVIEW_REQUESTED": frozenset({"FOLD_COMPLETE", "WORK_IN_PROGRESS"}),
    "WORK_UPDATE": frozenset({"WORK_IN_PROGRESS", "FOLD_COMPLETE"}),
    "CLOSE": NONTERMINAL_STATUSES,
}

ETA_EVENT_KINDS = frozenset(
    {"REVIEW_REQUESTED", "WORK_UPDATE", "FOLD_STARTED", "FOLD_PROGRESS", "REVIEW_STARTED", "REVIEW_PROGRESS"}
)


class BridgeError(RuntimeError):
    pass


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def format_utc(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_utc(value: str) -> dt.datetime:
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BridgeError(f"invalid RFC3339 timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise BridgeError(f"timestamp must include a timezone: {value!r}")
    return parsed.astimezone(dt.timezone.utc)


_DURATION_RE = re.compile(
    r"^PT(?:(?P<hours>\d+(?:\.\d+)?)H)?(?:(?P<minutes>\d+(?:\.\d+)?)M)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?$"
)


def parse_duration(value: str) -> float:
    match = _DURATION_RE.fullmatch(value)
    if not match or not any(match.groupdict().values()):
        raise BridgeError(f"unsupported ISO-8601 duration: {value!r}; use PT#H#M#S")
    return (
        float(match.group("hours") or 0) * 3600
        + float(match.group("minutes") or 0) * 60
        + float(match.group("seconds") or 0)
    )


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:64] or "review"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_body(path: str | None) -> str:
    if path is None:
        return ""
    if path == "-":
        return sys.stdin.read().rstrip()
    return Path(path).read_text().rstrip()


def validate_scalar(name: str, value: str | None) -> None:
    if value is not None and ("\n" in value or "\r" in value):
        raise BridgeError(f"{name} must be a single line")


def validate_body(body: str) -> None:
    if EVENT_RE.search(body):
        raise BridgeError(
            "body contains a reserved event heading; quote or indent bridge headings instead"
        )
    if RESERVED_BODY_FIELD_RE.search(body):
        raise BridgeError(
            "body contains a reserved event metadata line; quote or indent protocol fields instead"
        )


@contextlib.contextmanager
def exclusive_lock(lock_path: Path) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_create(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(tmp, path)
        except FileExistsError as exc:
            raise BridgeError(f"file already exists: {path}") from exc
        tmp.unlink()
        fsync_dir(path.parent)
    finally:
        tmp.unlink(missing_ok=True)


def append_bytes(path: Path, data: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_APPEND)
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def parse_header(text: str) -> dict[str, str]:
    first_event = EVENT_RE.search(text)
    header_text = text[: first_event.start()] if first_event else text
    fields: dict[str, str] = {}
    for line in header_text.splitlines():
        match = FIELD_RE.match(line)
        if match:
            key = match.group("key")
            if key in fields:
                raise BridgeError(f"duplicate review header field: {key}")
            fields[key] = match.group("value")
    return fields


def parse_events(text: str) -> list[dict[str, Any]]:
    matches = list(EVENT_RE.finditer(text))
    events: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        chunk = text[match.start() : end].rstrip()
        fields: dict[str, str] = {}
        field_counts: dict[str, int] = {}
        statuses: list[str] = []
        for line in chunk.splitlines()[1:]:
            field = FIELD_RE.match(line)
            if not field:
                continue
            key, value = field.group("key"), field.group("value")
            fields.setdefault(key, value)
            field_counts[key] = field_counts.get(key, 0) + 1
            if key == "STATUS":
                statuses.append(value)
        if not statuses:
            raise BridgeError(f"event [{match.group('seq')}] has no STATUS line")
        events.append(
            {
                "seq": int(match.group("seq")),
                "actor": match.group("actor"),
                "target": match.group("target"),
                "kind": match.group("kind"),
                "status": statuses[-1],
                "fields": fields,
                "field_counts": field_counts,
                "chunk": chunk,
            }
        )
    return events


def validate_history(header: dict[str, str], events: list[dict[str, Any]]) -> None:
    missing_header = sorted(REQUIRED_HEADER_FIELDS - header.keys())
    if missing_header:
        raise BridgeError(f"review header missing fields: {missing_header}")
    if header["KIND"] not in {"CODE", "PLAN", "DESIGN", "DOCS"}:
        raise BridgeError(f"unsupported review kind: {header['KIND']!r}")
    parse_utc(header["CREATED_AT"])
    for key, value in header.items():
        validate_scalar(f"header {key}", value)

    previous_status: str | None = None
    previous_event_id = "NONE"
    current_revision = header["HEAD_REVISION"]
    for event in events:
        seq = event["seq"]
        expected_target = "REVIEWER" if event["actor"] == "REQUESTER" else "REQUESTER"
        if event["target"] != expected_target:
            raise BridgeError(f"event [{seq}] has invalid target {event['target']}")
        duplicates = sorted(
            field for field in RESERVED_EVENT_FIELDS if event["field_counts"].get(field, 0) > 1
        )
        if duplicates:
            raise BridgeError(f"event [{seq}] has duplicate reserved fields: {duplicates}")
        for field in ("EVENT_ID", "TIMESTAMP", "IN_REPLY_TO", "STATUS"):
            if event["field_counts"].get(field) != 1:
                raise BridgeError(f"event [{seq}] must contain exactly one {field}")
        expected_event_id = f"E{seq:04d}"
        if event["fields"]["EVENT_ID"] != expected_event_id:
            raise BridgeError(f"event [{seq}] has invalid EVENT_ID")
        if event["fields"]["IN_REPLY_TO"] != previous_event_id:
            raise BridgeError(f"event [{seq}] has invalid IN_REPLY_TO")
        parse_utc(event["fields"]["TIMESTAMP"])
        if event["fields"].get("NEXT_UPDATE_BY"):
            parse_utc(event["fields"]["NEXT_UPDATE_BY"])
        revision = event["fields"].get("REVISION")
        validate_event(
            actor=event["actor"],
            kind=event["kind"],
            status=event["status"],
            previous_status=previous_status,
            expected_by=event["fields"].get("EXPECTED_BY"),
            grace=event["fields"].get("GRACE"),
            revision=revision,
        )
        if seq == 1:
            if event["kind"] != "REVIEW_REQUESTED" or revision != header["HEAD_REVISION"]:
                raise BridgeError("initial event must request review of HEAD_REVISION")
        elif event["kind"] == "REVIEW_REQUESTED":
            current_revision = revision or current_revision
        elif event["kind"] == "REVIEW" and revision != current_revision:
            raise BridgeError(f"event [{seq}] reviews {revision!r}, expected {current_revision!r}")
        elif event["kind"] == "RESPONSE":
            current_revision = revision or current_revision
        elif event["kind"] == "CLOSE" and revision != current_revision:
            raise BridgeError(f"event [{seq}] closes {revision!r}, expected {current_revision!r}")
        previous_status = event["status"]
        previous_event_id = expected_event_id


def load_review(path: Path) -> tuple[bytes, dict[str, str], list[dict[str, Any]]]:
    data = path.read_bytes()
    text = data.decode("utf-8")
    header = parse_header(text)
    if header.get("PROTOCOL_VERSION") != PROTOCOL_VERSION:
        raise BridgeError(
            f"unsupported protocol version {header.get('PROTOCOL_VERSION')!r}; expected {PROTOCOL_VERSION}"
        )
    events = parse_events(text)
    if not events:
        raise BridgeError("review file contains no events")
    expected = list(range(1, len(events) + 1))
    actual = [event["seq"] for event in events]
    if actual != expected:
        raise BridgeError(f"event sequence is not contiguous: {actual}")
    if not data.endswith(f"STATUS: {events[-1]['status']}\n".encode()):
        raise BridgeError("last event STATUS is not physically last")
    validate_history(header, events)
    return data, header, events


def validate_event(
    *,
    actor: str,
    kind: str,
    status: str,
    previous_status: str | None,
    expected_by: str | None,
    grace: str | None,
    revision: str | None,
) -> None:
    allowed_statuses = ALLOWED_EVENTS.get((actor, kind))
    if allowed_statuses is None or status not in allowed_statuses:
        raise BridgeError(f"illegal event tuple: actor={actor} kind={kind} status={status}")
    if previous_status is not None:
        allowed_next = ALLOWED_TRANSITIONS.get(previous_status, frozenset())
        if status not in allowed_next:
            raise BridgeError(f"illegal transition: {previous_status} -> {status}")
        allowed_previous = ALLOWED_PREVIOUS_BY_KIND.get(kind, frozenset())
        if previous_status not in allowed_previous:
            raise BridgeError(f"illegal event after {previous_status}: {kind}")
    if kind == "CLOSE" and status == "CLOSED" and previous_status != "FOLD_COMPLETE":
        raise BridgeError("CLOSED requires a completed fold; use STOPPED/ABANDONED/SUPERSEDED otherwise")
    if kind in REVISION_EVENT_KINDS and not revision:
        raise BridgeError(f"{kind} requires REVISION")
    if kind in ETA_EVENT_KINDS:
        if not expected_by or not grace:
            raise BridgeError(f"{kind} requires EXPECTED_BY and GRACE")
        parse_utc(expected_by)
        parse_duration(grace)


def render_event(
    *,
    seq: int,
    actor: str,
    kind: str,
    status: str,
    body: str,
    timestamp: str,
    in_reply_to: str,
    revision: str | None,
    expected_by: str | None,
    grace: str | None,
    next_update_by: str | None,
) -> str:
    validate_body(body)
    for name, value in {
        "timestamp": timestamp,
        "in_reply_to": in_reply_to,
        "revision": revision,
        "expected_by": expected_by,
        "grace": grace,
        "next_update_by": next_update_by,
    }.items():
        validate_scalar(name, value)
    target = "REVIEWER" if actor == "REQUESTER" else "REQUESTER"
    lines = [
        f"## [{seq}] {actor} → {target} — {kind}",
        "",
        f"EVENT_ID: E{seq:04d}",
        f"TIMESTAMP: {timestamp}",
        f"IN_REPLY_TO: {in_reply_to}",
    ]
    if revision:
        lines.append(f"REVISION: {revision}")
    if expected_by:
        lines.append(f"EXPECTED_BY: {expected_by}")
    if grace:
        lines.append(f"GRACE: {grace}")
    if next_update_by:
        parse_utc(next_update_by)
        lines.append(f"NEXT_UPDATE_BY: {next_update_by}")
    if body:
        lines.extend(["", body])
    lines.extend(["", f"STATUS: {status}", ""])
    return "\n".join(lines)


def append_event(
    path: Path,
    *,
    actor: str,
    kind: str,
    status: str,
    body: str,
    expected_by: str | None = None,
    grace: str | None = None,
    next_update_by: str | None = None,
    in_reply_to: str | None = None,
    revision: str | None = None,
    expected_sha: str | None = None,
) -> dict[str, Any]:
    lock_path = path.with_suffix(path.suffix + ".lock")
    with exclusive_lock(lock_path):
        before, _, events = load_review(path)
        before_sha = sha256_bytes(before)
        if expected_sha and before_sha != expected_sha:
            raise BridgeError(f"stale review file: expected sha {expected_sha}, found {before_sha}")
        previous = events[-1]
        validate_event(
            actor=actor,
            kind=kind,
            status=status,
            previous_status=previous["status"],
            expected_by=expected_by,
            grace=grace,
            revision=revision,
        )
        seq = previous["seq"] + 1
        previous_event_id = previous["fields"].get("EVENT_ID", f"E{previous['seq']:04d}")
        if in_reply_to is not None and in_reply_to != previous_event_id:
            raise BridgeError(
                f"IN_REPLY_TO must reference the latest event {previous_event_id}, found {in_reply_to}"
            )
        event = render_event(
            seq=seq,
            actor=actor,
            kind=kind,
            status=status,
            body=body,
            timestamp=format_utc(utc_now()),
            in_reply_to=previous_event_id,
            revision=revision,
            expected_by=expected_by,
            grace=grace,
            next_update_by=next_update_by,
        ).encode()
        append_bytes(path, event)
        after, _, after_events = load_review(path)
        last = after_events[-1]
        if last["seq"] != seq or last["kind"] != kind or last["status"] != status:
            raise BridgeError("append verification failed: new event is not physically last")
        return {"path": str(path), "sha256": sha256_bytes(after), "event": public_event(last)}


def public_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "seq": event["seq"],
        "event_id": event["fields"].get("EVENT_ID", f"E{event['seq']:04d}"),
        "actor": event["actor"],
        "kind": event["kind"],
        "status": event["status"],
        "timestamp": event["fields"].get("TIMESTAMP"),
        "expected_by": event["fields"].get("EXPECTED_BY"),
        "grace": event["fields"].get("GRACE"),
        "next_update_by": event["fields"].get("NEXT_UPDATE_BY"),
        "revision": event["fields"].get("REVISION"),
    }


def review_status(path: Path) -> dict[str, Any]:
    data, header, events = load_review(path)
    last = events[-1]
    return {
        "path": str(path),
        "sha256": sha256_bytes(data),
        "review_id": header.get("REVIEW_ID"),
        "kind": header.get("KIND"),
        "subject": header.get("SUBJECT"),
        "terminal": last["status"] in TERMINAL_STATUSES,
        "last_event": public_event(last),
    }


def locked_review_status(path: Path) -> dict[str, Any]:
    with exclusive_lock(path.with_suffix(path.suffix + ".lock")):
        return review_status(path)


def archived_path_for(active_path: Path) -> Path | None:
    if active_path.parent.name != "active":
        return None
    candidates = list((active_path.parent.parent / "archive" / "raw").glob(f"*/*/{active_path.name}"))
    if len(candidates) > 1:
        raise BridgeError(f"multiple archived reviews match {active_path.name}")
    return candidates[0] if candidates else None


def observable_review_status(path: Path) -> dict[str, Any]:
    try:
        return locked_review_status(path)
    except FileNotFoundError:
        archived = archived_path_for(path)
        if archived is None:
            raise
        state = locked_review_status(archived)
        state["archived_from"] = str(path)
        return state


def initial_document(args: argparse.Namespace, path: Path, review_id: str, body: str) -> bytes:
    created = format_utc(utc_now())
    header = [
        f"# Cross-review: {args.subject}",
        "",
        "## Protocol",
        "",
        "- Treat this file as append-only. Use the bundled bridge helper for every event.",
        "- Event numbers are local to this review and must remain contiguous.",
        "- The current owner publishes EXPECTED_BY + GRACE; inactivity stops polling but never closes the review.",
        "- Findings use BLOCK/FIX/SUGGEST and require exact evidence; requester verifies findings before folding.",
        "- Only an explicit terminal CLOSE permits archiving.",
        "",
        f"PROTOCOL_VERSION: {PROTOCOL_VERSION}",
        f"REVIEW_ID: {review_id}",
        f"KIND: {args.kind}",
        f"SUBJECT: {args.subject}",
        f"REVIEW_SKILL: {args.review_skill}",
        f"REQUESTER: {args.requester}",
        f"REVIEWER: {args.reviewer}",
        f"CREATED_AT: {created}",
        f"BASE_REVISION: {args.base}",
        f"HEAD_REVISION: {args.head}",
    ]
    if args.related:
        header.append(f"RELATED: {args.related}")
    header.extend(["", "---", "", ""])
    event = render_event(
        seq=1,
        actor="REQUESTER",
        kind="REVIEW_REQUESTED",
        status="READY_FOR_REVIEW",
        body=body,
        timestamp=created,
        in_reply_to="NONE",
        revision=args.head,
        expected_by=args.expected_by,
        grace=args.grace,
        next_update_by=args.next_update_by,
    )
    return ("\n".join(header) + event).encode()


def cmd_init(args: argparse.Namespace) -> int:
    for name in (
        "subject",
        "review_skill",
        "requester",
        "reviewer",
        "base",
        "head",
        "related",
        "expected_by",
        "grace",
        "next_update_by",
    ):
        validate_scalar(name, getattr(args, name))
    parse_utc(args.expected_by)
    parse_duration(args.grace)
    if args.next_update_by:
        parse_utc(args.next_update_by)
    root = Path(args.root).resolve()
    active = root / "active"
    now = utc_now()
    review_id = f"rvw-{now.strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(4)}"
    filename = f"{args.kind.lower()}--{slugify(args.subject)}--{review_id}.md"
    path = active / filename
    body = read_body(args.body_file)
    validate_body(body)
    validate_event(
        actor="REQUESTER",
        kind="REVIEW_REQUESTED",
        status="READY_FOR_REVIEW",
        previous_status=None,
        expected_by=args.expected_by,
        grace=args.grace,
        revision=args.head,
    )
    document = initial_document(args, path, review_id, body)
    text = document.decode("utf-8")
    header = parse_header(text)
    events = parse_events(text)
    validate_history(header, events)
    atomic_create(path, document)
    result = review_status(path)
    print(json.dumps(result, sort_keys=True))
    return 0


def cmd_append(args: argparse.Namespace) -> int:
    result = append_event(
        Path(args.file).resolve(),
        actor=args.actor,
        kind=args.kind,
        status=args.status,
        body=read_body(args.body_file),
        expected_by=args.expected_by,
        grace=args.grace,
        next_update_by=args.next_update_by,
        in_reply_to=args.in_reply_to,
        revision=args.revision,
        expected_sha=args.expected_sha,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    print(json.dumps(observable_review_status(Path(args.file).resolve()), sort_keys=True))
    return 0


def adaptive_deadline(
    last_event: dict[str, Any], *, inactivity_seconds: float, default_grace_seconds: float
) -> dt.datetime:
    timestamp = parse_utc(last_event.get("timestamp") or format_utc(utc_now()))
    deadline = timestamp + dt.timedelta(seconds=inactivity_seconds)
    expected_by = last_event.get("expected_by")
    if expected_by:
        grace = parse_duration(last_event.get("grace") or f"PT{default_grace_seconds}S")
        deadline = max(deadline, parse_utc(expected_by) + dt.timedelta(seconds=grace))
    return deadline


def adaptive_interval(
    last_event: dict[str, Any], *, now: dt.datetime, slow_seconds: float, near_seconds: float, near_window_seconds: float
) -> float:
    expected_by = last_event.get("expected_by")
    if not expected_by:
        return near_seconds
    near_at = parse_utc(expected_by) - dt.timedelta(seconds=near_window_seconds)
    if now >= near_at:
        return near_seconds
    return min(slow_seconds, max(near_seconds, (near_at - now).total_seconds()))


def cmd_wait(args: argparse.Namespace) -> int:
    path = Path(args.file).resolve()
    initial = observable_review_status(path)
    baseline = args.baseline_sha or initial["sha256"]
    while True:
        state = observable_review_status(path)
        if state["sha256"] != baseline or state["terminal"]:
            if "archived_from" in state:
                state["result"] = "archived"
            else:
                state["result"] = "changed" if state["sha256"] != baseline else "terminal"
            print(json.dumps(state, sort_keys=True))
            return 0
        now = utc_now()
        deadline = adaptive_deadline(
            state["last_event"],
            inactivity_seconds=args.inactivity_seconds,
            default_grace_seconds=args.default_grace_seconds,
        )
        if now >= deadline:
            state["result"] = "timeout"
            state["deadline"] = format_utc(deadline)
            print(json.dumps(state, sort_keys=True))
            return 3
        interval = adaptive_interval(
            state["last_event"],
            now=now,
            slow_seconds=args.slow_poll_seconds,
            near_seconds=args.near_poll_seconds,
            near_window_seconds=args.near_window_seconds,
        )
        time.sleep(max(0.01, min(interval, (deadline - now).total_seconds())))


def cmd_archive(args: argparse.Namespace) -> int:
    source = Path(args.file).resolve()
    root = Path(args.root).resolve()
    lock_path = source.with_suffix(source.suffix + ".lock")
    with exclusive_lock(lock_path):
        with exclusive_lock(root / "archive" / ".archive.lock"):
            data, header, events = load_review(source)
            last = events[-1]
            if last["status"] not in TERMINAL_STATUSES:
                raise BridgeError(f"cannot archive non-terminal review: {last['status']}")
            closed_at = parse_utc(last["fields"].get("TIMESTAMP") or format_utc(utc_now()))
            archive_dir = root / "archive" / "raw" / f"{closed_at.year:04d}" / f"{closed_at.month:02d}"
            archive_dir.mkdir(parents=True, exist_ok=True)
            destination = archive_dir / source.name
            if destination.exists():
                raise BridgeError(f"archive destination already exists: {destination}")
            digest = sha256_bytes(data)
            os.replace(source, destination)
            fsync_dir(source.parent)
            fsync_dir(destination.parent)
            digest_path = destination.with_suffix(destination.suffix + ".sha256")
            atomic_create(digest_path, f"{digest}  {destination.name}\n".encode())
            catalog = root / "archive" / "catalog.jsonl"
            record = {
                "review_id": header.get("REVIEW_ID"),
                "kind": header.get("KIND"),
                "subject": header.get("SUBJECT"),
                "outcome": last["status"],
                "closed_at": format_utc(closed_at),
                "path": str(destination),
                "sha256": digest,
            }
            catalog.parent.mkdir(parents=True, exist_ok=True)
            if not catalog.exists():
                atomic_create(catalog, b"")
            append_bytes(catalog, (json.dumps(record, sort_keys=True) + "\n").encode())
    print(json.dumps(record, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create one active review with its first request")
    init.add_argument("--root", default=".agent-bridge")
    init.add_argument("--kind", choices=("CODE", "PLAN", "DESIGN", "DOCS"), required=True)
    init.add_argument("--subject", required=True)
    init.add_argument("--review-skill", required=True)
    init.add_argument("--requester", required=True)
    init.add_argument("--reviewer", required=True)
    init.add_argument("--base", required=True)
    init.add_argument("--head", required=True)
    init.add_argument("--related")
    init.add_argument("--body-file")
    init.add_argument("--expected-by", required=True)
    init.add_argument("--grace", default="PT20M")
    init.add_argument("--next-update-by")
    init.set_defaults(func=cmd_init)

    append = subparsers.add_parser("append", help="Append one validated event")
    append.add_argument("--file", required=True)
    append.add_argument("--actor", choices=("REQUESTER", "REVIEWER"), required=True)
    append.add_argument("--kind", required=True)
    append.add_argument("--status", required=True)
    append.add_argument("--body-file")
    append.add_argument("--expected-by")
    append.add_argument("--grace")
    append.add_argument("--next-update-by")
    append.add_argument("--in-reply-to")
    append.add_argument("--revision")
    append.add_argument("--expected-sha")
    append.set_defaults(func=cmd_append)

    status = subparsers.add_parser("status", help="Print parsed review state as JSON")
    status.add_argument("--file", required=True)
    status.set_defaults(func=cmd_status)

    wait = subparsers.add_parser("wait", help="Wait adaptively for a file change or deadline")
    wait.add_argument("--file", required=True)
    wait.add_argument("--baseline-sha")
    wait.add_argument("--inactivity-seconds", type=float, default=3600)
    wait.add_argument("--default-grace-seconds", type=float, default=1200)
    wait.add_argument("--slow-poll-seconds", type=float, default=300)
    wait.add_argument("--near-poll-seconds", type=float, default=60)
    wait.add_argument("--near-window-seconds", type=float, default=600)
    wait.set_defaults(func=cmd_wait)

    archive = subparsers.add_parser("archive", help="Atomically archive an explicitly closed review")
    archive.add_argument("--file", required=True)
    archive.add_argument("--root", default=".agent-bridge")
    archive.set_defaults(func=cmd_archive)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (BridgeError, OSError, UnicodeError) as exc:
        print(json.dumps({"error": str(exc), "type": type(exc).__name__}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
