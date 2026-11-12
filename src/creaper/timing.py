"""Where a tool call's time goes, and what a long one is doing right now.

The timing log: one JSON line per tool call and one per bridge command, appended to
timing.jsonl in the bridge folder (rotated to timing.1.jsonl at LOG_MAX_BYTES, so the two
together stay under twice that):

    {"at": "2026-11-12T14:03:22", "kind": "tool", "tool": "auto_mix", "seconds": 412.6,
     "ok": true, "renders": 14, "cache_hits": 2, "bridge_calls": 96}
    {"at": "...", "kind": "bridge", "cmd": "render_stems", "seconds": 31.2, "ok": true,
     "tool": "auto_mix"}

A failed call has "ok": false and the start of its message in "error"; a question nobody
answered has "skipped": true. "Why did this song take two hours" is then a look at this
file, not a dig through the chat logs.

Progress: in the chat panel (CREAPER_STATUS_FILE names a file the panel reads), a tool
that renders says where it is before each render, "auto_mix: compressors, render 9 of
about 14". The stage comes from the tool (stage()), the count from here, and "of about"
from what the same tool took the last few times, read from the log.

Neither may ever fail a tool: every write is best effort."""

from __future__ import annotations

import contextvars
import json
import os
import statistics
import threading
import time
from pathlib import Path
from typing import Any

from . import convstate

LOG_NAME = "timing.jsonl"
LOG_MAX_BYTES = 2_000_000
STATUS_FILE_ENV = "CREAPER_STATUS_FILE"
# REAPER, and the panel inside it, stand still during a render. The line about a render
# is written just before it starts, so the panel gets this long to read and draw it first.
STATUS_SETTLE_S = 0.15
USUAL_FROM = 5             # "of about N": the middle of this many earlier calls of the tool
USUAL_READ_BYTES = 262_144

_current: contextvars.ContextVar[dict | None] = contextvars.ContextVar("creaper_tool_call", default=None)
_write_lock = threading.Lock()


def _folder() -> Path:
    from .server import bridge   # at call time: the server module imports this one

    return Path(bridge.directory)


def log_path() -> Path:
    return _folder() / LOG_NAME


def _append(entry: dict) -> None:
    try:
        path = log_path()
        if not path.parent.is_dir():
            return
        line = json.dumps(entry, separators=(",", ":")) + "\n"
        with _write_lock:
            try:
                if path.stat().st_size + len(line) > LOG_MAX_BYTES:
                    os.replace(path, path.with_name("timing.1.jsonl"))
            except OSError:
                pass   # no log yet, or another server rotated it this instant
            with open(path, "a", encoding="utf-8") as f:
                f.write(line)
    except Exception:  # noqa: BLE001 - the log is never a reason for a tool to fail
        pass


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _short(text: Any) -> str:
    return " ".join(str(text).split())[:200]


# ---------------------------------------------------------------- tool calls

def begin(tool: str) -> dict:
    """Starts timing a tool call. The record travels with the call (a context variable:
    tools run in threads, several at once), so bridge commands and renders count
    towards the call that made them."""
    record = {"tool": tool, "start": time.monotonic(), "renders": 0, "cache_hits": 0, "bridge_calls": 0,
              "stage": None, "usual": None, "outer": _current.get()}
    record["token"] = _current.set(record)
    return record


def finish(record: dict, ok: bool, error: Any = None, skipped: bool = False) -> None:
    try:
        _current.reset(record.pop("token"))
    except (KeyError, ValueError, RuntimeError):
        _current.set(record.get("outer"))
    entry: dict[str, Any] = {"at": _now(), "kind": "tool", "tool": record["tool"],
                             "seconds": round(time.monotonic() - record["start"], 3), "ok": bool(ok),
                             "renders": record["renders"], "cache_hits": record["cache_hits"],
                             "bridge_calls": record["bridge_calls"]}
    if skipped:
        entry["skipped"] = True
    if error is not None:
        entry["error"] = _short(error)
    cid = convstate.conversation_id()
    if cid:
        entry["conversation"] = cid
    _append(entry)
    if record.get("said"):
        _write_status("")   # the tool is done: its line goes


def bridge_call(cmd: str, seconds: float, ok: bool) -> None:
    """One bridge command, as REAPER answered it (Bridge.call reports every one here)."""
    record = _current.get()
    entry: dict[str, Any] = {"at": _now(), "kind": "bridge", "cmd": cmd, "seconds": round(seconds, 3), "ok": bool(ok)}
    if record is not None:
        record["bridge_calls"] += 1
        entry["tool"] = record["tool"]
    _append(entry)


def cache_hit() -> None:
    """A render answered from the render cache instead of by REAPER."""
    record = _current.get()
    if record is not None:
        record["cache_hits"] += 1


def render_starting() -> None:
    """A render REAPER is about to make: counted, and said in the panel."""
    record = _current.get()
    if record is None:
        return
    record["renders"] += 1
    _say(record, settle=True)


# ------------------------------------------------------------------ progress

def stage(text: str | None) -> None:
    """What the running tool is doing now, in a word or two ("compressors", "drum bus"):
    it leads the progress line until the next stage."""
    record = _current.get()
    if record is None:
        return
    record["stage"] = text
    if record["renders"] or record.get("said"):
        _say(record, settle=False)


def progress_line(record: dict) -> str:
    parts = []
    if record.get("stage"):
        parts.append(str(record["stage"]))
    if record["renders"]:
        count = f"render {record['renders']}"
        usual = record.get("usual")
        if usual and usual >= record["renders"] and usual > 1:
            count += f" of about {usual}"
        parts.append(count)
    return f"{record['tool']}: {', '.join(parts)}" if parts else record["tool"]


def _say(record: dict, settle: bool) -> None:
    if not os.environ.get(STATUS_FILE_ENV):
        return
    if record.get("usual") is None:
        record["usual"] = usual_renders(record["tool"]) or 0
    if _write_status(progress_line(record)):
        record["said"] = True
        if settle:
            time.sleep(STATUS_SETTLE_S)


def _write_status(text: str) -> bool:
    path = os.environ.get(STATUS_FILE_ENV)
    if not path:
        return False
    try:
        target = Path(path)
        tmp = target.with_name(f"{target.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        tmp.write_text(json.dumps({"text": text, "at": time.time()}), encoding="utf-8")
        try:
            os.replace(tmp, target)
        finally:
            tmp.unlink(missing_ok=True)
        return True
    except OSError:   # the panel is reading it this instant, or the turn's folder is gone
        return False


def usual_renders(tool: str) -> int | None:
    """How many renders this tool's last few successful calls made (the middle value),
    from the end of the timing log; None when it hasn't run before."""
    try:
        path = log_path()
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - USUAL_READ_BYTES))
            lines = f.read().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return None
    counts: list[int] = []
    for line in reversed(lines):
        if f'"tool":"{tool}"' not in line or '"kind":"tool"' not in line:
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if entry.get("ok") and entry.get("renders"):
            counts.append(int(entry["renders"]))
            if len(counts) == USUAL_FROM:
                break
    return round(statistics.median(counts)) if counts else None
