"""Client for the creaper Lua bridge running inside REAPER.

The two sides talk through files in REAPER's resource folder (<resource>/creaper):

    requests/<id>.json   one per call, written by us (atomically), claimed by the bridge
    responses/<id>.json  the bridge's answer, read and deleted by us
    bridge.json          heartbeat the bridge rewrites every second while it runs

Separate files per call let several clients (Claude Desktop, the chat panel, Claude
Code) use REAPER at once. Bridges before protocol 2 used a single request.json and
response.json, which this client still speaks when the heartbeat says so.

Files keep the bridge dependency-free: REAPER's Lua has no sockets.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable

HEARTBEAT_MAX_AGE = 5.0
STALE_HEARTBEAT_GRACE = 15.0

NOT_RUNNING_HELP = (
    "REAPER isn't answering. Make sure REAPER is open and the creaper bridge script "
    "is running (Actions > Show action list, search for 'creaper_bridge'). "
    "If it isn't installed yet, run `creaper install-bridge`."
)


class BridgeError(RuntimeError):
    """REAPER reported an error, or couldn't be reached."""


def default_resource_dir() -> Path:
    """REAPER's resource folder for a standard (non-portable) install."""
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "REAPER"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "REAPER"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "REAPER"


def default_bridge_dir() -> Path:
    override = os.environ.get("CREAPER_BRIDGE_DIR")
    if override:
        return Path(override)
    resource = os.environ.get("CREAPER_REAPER_RESOURCE_PATH")
    return (Path(resource) if resource else default_resource_dir()) / "creaper"


class Bridge:
    def __init__(self, directory: Path | None = None) -> None:
        self.directory = Path(directory) if directory else default_bridge_dir()
        self._lock = threading.Lock()

    @property
    def request_path(self) -> Path:
        return self.directory / "request.json"

    @property
    def response_path(self) -> Path:
        return self.directory / "response.json"

    @property
    def heartbeat_path(self) -> Path:
        return self.directory / "bridge.json"

    def heartbeat(self) -> dict[str, Any] | None:
        """The bridge's last heartbeat plus its age in seconds, or None."""
        try:
            data = json.loads(self.heartbeat_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        data["age"] = time.time() - float(data.get("time", 0))
        return data

    def is_running(self) -> bool:
        beat = self.heartbeat()
        return beat is not None and beat["age"] <= HEARTBEAT_MAX_AGE

    def wait_until_running(self, timeout: float) -> dict[str, Any] | None:
        """The bridge's fresh heartbeat, waiting up to `timeout` for one. REAPER
        pauses scripts while it's busy (loading heavy plugins, saving undo state, a
        dialog), so a late heartbeat isn't proof the bridge has stopped."""
        deadline = time.monotonic() + timeout
        while True:
            beat = self.heartbeat()
            if beat is not None and beat["age"] <= HEARTBEAT_MAX_AGE:
                return beat
            if time.monotonic() >= deadline:
                return None
            time.sleep(0.05)

    def call(self, cmd: str, params: dict[str, Any] | None = None, timeout: float = 30.0) -> Any:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        # Give up soon if the bridge isn't there at all; wait if it's just late.
        beat = self.wait_until_running(STALE_HEARTBEAT_GRACE if self.heartbeat_path.exists() else 1.0)
        if beat is None:
            raise BridgeError(NOT_RUNNING_HELP)
        request_id = uuid.uuid4().hex
        body = json.dumps({"id": request_id, "cmd": cmd, "params": params})
        if int(beat.get("protocol", 1)) >= 2:
            # Own request and response files: any number of clients can talk at once.
            requests, responses = self.directory / "requests", self.directory / "responses"
            requests.mkdir(exist_ok=True)
            request_path, response_path = requests / f"{request_id}.json", responses / f"{request_id}.json"
            tmp = requests / f"{request_id}.tmp"
            _retry(lambda: tmp.write_text(body, encoding="utf-8"))
            _retry(lambda: os.replace(tmp, request_path))
            # The file is ours alone, so whatever answer lands in it is ours.
            return self._await(None, request_path, response_path, timeout)
        # Older bridge: one shared request file, so only one call at a time per process.
        with self._lock:
            _remove(self.response_path)
            tmp = self.directory / f"request.{request_id}.tmp"
            tmp.write_text(body, encoding="utf-8")
            _retry(lambda: os.replace(tmp, self.request_path))
            return self._await(request_id, self.request_path, self.response_path, timeout)

    def _await(self, request_id: str | None, request_path: Path, response_path: Path, timeout: float) -> Any:
        """Waits for the answer; with a request_id, ignores answers to other requests."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            response = _read_json(response_path)
            if response is None or (request_id is not None and response.get("id") != request_id):
                time.sleep(0.01)
                continue
            _remove(response_path)
            if response.get("ok"):
                return response.get("result")
            message = response.get("error") or "unknown error"
            if response.get("traceback"):
                message += "\n" + response["traceback"]
            raise BridgeError(message)
        _remove(request_path)  # not picked up yet: withdraw it
        raise BridgeError(
            f"REAPER didn't answer within {timeout:.0f} seconds. "
            "It may be busy or showing a dialog that needs closing."
        )


def _read_json(path: Path) -> dict[str, Any] | None:
    """None if the file is missing, locked for a moment, or not complete yet."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _retry(action: Callable[[], Any], attempts: int = 50) -> Any:
    # Windows refuses to replace or delete a file another process has open for a
    # moment (the bridge reading or writing it); that clears within milliseconds.
    for attempt in range(attempts):
        try:
            return action()
        except PermissionError:
            if attempt == attempts - 1:
                raise
            time.sleep(0.01)


def _remove(path: Path) -> None:
    try:
        _retry(lambda: path.unlink(missing_ok=True), attempts=20)
    except PermissionError:
        pass  # the bridge clears leftovers when it next starts
