"""Client for the creaper Lua bridge running inside REAPER.

The two sides talk through files in REAPER's resource folder:

    request.json   written by us (atomically), claimed and deleted by the bridge
    response.json  written by the bridge (atomically), read and deleted by us
    bridge.json    heartbeat the bridge rewrites every second while it runs

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
from typing import Any

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

    def wait_until_running(self, timeout: float) -> bool:
        """REAPER pauses scripts while it's busy (loading heavy plugins, saving undo
        state, a dialog), so a late heartbeat isn't proof the bridge has stopped."""
        deadline = time.monotonic() + timeout
        while not self.is_running():
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.1)
        return True

    def call(self, cmd: str, params: dict[str, Any] | None = None, timeout: float = 30.0) -> Any:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        with self._lock:
            # Give up at once if the bridge has never run; wait if it's just late.
            if not self.wait_until_running(STALE_HEARTBEAT_GRACE if self.heartbeat() else 0.5):
                raise BridgeError(NOT_RUNNING_HELP)
            request_id = uuid.uuid4().hex
            self.response_path.unlink(missing_ok=True)
            tmp = self.directory / f"request.{request_id}.tmp"
            tmp.write_text(json.dumps({"id": request_id, "cmd": cmd, "params": params}), encoding="utf-8")
            os.replace(tmp, self.request_path)

            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                response = self._read_response()
                if response is None:
                    time.sleep(0.01)
                    continue
                if response.get("id") != request_id:
                    continue  # stale answer to an earlier, timed-out request
                if response.get("ok"):
                    return response.get("result")
                message = response.get("error") or "unknown error"
                if response.get("traceback"):
                    message += "\n" + response["traceback"]
                raise BridgeError(message)

            self.request_path.unlink(missing_ok=True)
            raise BridgeError(
                f"REAPER didn't answer within {timeout:.0f} seconds. "
                "It may be busy or showing a dialog that needs closing."
            )

    def _read_response(self) -> dict[str, Any] | None:
        try:
            text = self.response_path.read_text(encoding="utf-8")
        except (FileNotFoundError, PermissionError):
            return None
        try:
            data = json.loads(text)
        except ValueError:
            return None
        self.response_path.unlink(missing_ok=True)
        return data
