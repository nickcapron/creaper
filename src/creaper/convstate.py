"""What one chat-panel conversation remembers between its turns.

The panel starts a new Claude Code, and with it a new creaper server, for every message
the user sends. Whatever a server kept in memory "for the session" (the user's answer to
"may creaper load sounds into the synth?", a notice already given, a synth found to
render differently every time, the tracks creaper made) was therefore gone one message
later, and the same question came back on every message.

The panel gives each conversation an id and passes it in CREAPER_CONVERSATION. With it,
those things are kept in conversations.json in the bridge folder, under that id:

    {"<id>": {"used": <time>, "<kind>": {"<key>": [<value>, <time>]}}}

Without it (Claude Desktop, Claude Code: one server for the whole session) nothing is
stored here and every function answers "not known": each module keeps its own
per-process memory as before.

Permission answers lapse an hour after they were last used; a conversation nobody has
used for a week is dropped. Remembering is a convenience: a file that can't be read or
written means the question is asked again, never an error."""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any

from . import jsonstore

ENV = "CREAPER_CONVERSATION"
ANSWER_TTL_S = 3600.0             # a permission answer, since it was last relied on
CONVERSATION_TTL_S = 7 * 86400.0  # a conversation, since its last turn
MAX_CONVERSATIONS = 40
MAX_KEYS = 500                    # per kind, the newest kept
TOUCH_EVERY_S = 30.0              # relying on an answer rewrites its time at most this often
ID = re.compile(r"^[0-9a-fA-F-]{8,64}$")


def conversation_id() -> str | None:
    """The panel conversation this server works for, or None outside the panel."""
    value = os.environ.get(ENV, "").strip()
    return value if ID.match(value) else None


def _file() -> Path:
    from .server import bridge   # at call time: the server module imports this one

    return bridge.directory / "conversations.json"


def _read() -> dict:
    try:
        data = jsonstore.read(_file(), dict)
    except (ValueError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _prune(data: dict, now: float) -> None:
    for cid in [c for c, e in data.items()
                if not isinstance(e, dict) or now - float(e.get("used", 0) or 0) > CONVERSATION_TTL_S]:
        del data[cid]
    for cid in sorted(data, key=lambda c: data[c].get("used", 0))[:-MAX_CONVERSATIONS]:
        del data[cid]
    for entry in data.values():
        allowed = entry.get("allowed")
        if isinstance(allowed, dict):
            for key in [k for k, v in allowed.items() if now - _stamp(v) > ANSWER_TTL_S]:
                del allowed[key]
        for kind, keys in entry.items():
            if isinstance(keys, dict) and len(keys) > MAX_KEYS:
                for key in sorted(keys, key=lambda k: _stamp(keys[k]))[:-MAX_KEYS]:
                    del keys[key]


def _stamp(item: Any) -> float:
    try:
        return float(item[1])
    except (TypeError, ValueError, IndexError, KeyError):
        return 0.0


def _update(change) -> None:
    """Runs change(this conversation's entry) under the file's lock and saves it."""
    cid = conversation_id()
    if cid is None:
        return
    path = _file()
    try:
        with jsonstore.locked(path):
            try:
                data = jsonstore.read(path, dict)
            except ValueError:
                data = {}       # a damaged file holds nothing worth keeping: start it again
            if not isinstance(data, dict):
                data = {}
            now = time.time()
            entry = data.get(cid)
            if not isinstance(entry, dict):
                entry = data[cid] = {}
            entry["used"] = now
            change(entry, now)
            _prune(data, now)
            jsonstore.write(path, data, indent=None)
    except (OSError, TimeoutError):
        pass


def value(kind: str, key: str, ttl: float | None = None, touch: bool = False) -> Any | None:
    """What this conversation remembers under kind/key, or None: outside the panel, when
    nothing was kept, or when it's older than ttl seconds. touch=True counts this as a
    use, so the ttl runs from now."""
    cid = conversation_id()
    if cid is None:
        return None
    entry = _read().get(cid)
    item = (entry.get(kind) or {}).get(key) if isinstance(entry, dict) else None
    if not isinstance(item, list) or len(item) != 2:
        return None
    now = time.time()
    age = now - _stamp(item)
    if ttl is not None and age > ttl:
        return None
    if touch and age > TOUCH_EVERY_S:
        def again(e: dict, at: float) -> None:
            kept = (e.get(kind) or {}).get(key)
            if isinstance(kept, list) and len(kept) == 2:
                kept[1] = at
        _update(again)
    return item[0]


def put(kind: str, key: str, what: Any = True) -> None:
    """Remembers what under kind/key for this conversation (nothing outside the panel)."""
    def change(entry: dict, now: float) -> None:
        keys = entry.get(kind)
        if not isinstance(keys, dict):
            keys = entry[kind] = {}
        keys[key] = [what, now]
    _update(change)


def forget(kind: str, key: str) -> None:
    if value(kind, key) is None:
        return

    def change(entry: dict, now: float) -> None:
        keys = entry.get(kind)
        if isinstance(keys, dict):
            keys.pop(key, None)
    _update(change)


def allowed(question: str) -> bool:
    """Whether the user said yes to this standing question earlier in the conversation
    and it was relied on within the last hour. One key per question: a yes to one thing
    is never a yes to another."""
    return value("allowed", question, ttl=ANSWER_TTL_S, touch=True) is not None


def allow(question: str) -> None:
    put("allowed", question)
