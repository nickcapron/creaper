"""Runs creaper_bridge.lua for real, in Lua 5.4 (lupa), against a small fake of REAPER's
API (fake_reaper.lua). The bridge is loaded as REAPER loads it: its top-level code runs
(takeover, the folders, the settings a crashed bridge left changed), and a global the
tests set makes it hand back its parts in place of starting its defer loop.

Commands go the way a request does, through the bridge's own handle(): JSON in, JSON
out. Import this module only after pytest.importorskip("lupa")."""

import json
from pathlib import Path

from lupa import lua54

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "src" / "creaper" / "reaper" / "creaper_bridge.lua"
FAKE = Path(__file__).with_name("fake_reaper.lua")

_NEW_REAPER = """
function(fake_path, resource_path)
  local reaper, F = assert(loadfile(fake_path))()
  F.resource_path = resource_path
  F.ini_path = resource_path .. "/reaper.ini"
  _G.reaper = reaper
  return F
end
"""

_LOAD_BRIDGE = """
function(bridge_path)
  CREAPER_BRIDGE_TEST = true
  assert(loadfile(bridge_path))()
  local parts = CREAPER_BRIDGE_TEST
  CREAPER_BRIDGE_TEST = nil
  assert(type(parts) == "table", "the bridge didn't hand back its parts: is the test hook still there?")
  -- A request as the loop answers it: handle(), then the answer encoded as it is written.
  parts.request = function(raw) return parts.json.encode(parts.handle(raw)) end
  return parts
end
"""


class BridgeError(Exception):
    """A command answered ok = false. A fail() in the bridge has no traceback; a bug has one."""

    def __init__(self, message, traceback=None):
        super().__init__(message if not traceback else f"{message}\n{traceback}")
        self.message = message
        self.traceback = traceback


class Bridge:
    """One run of the bridge script."""

    def __init__(self, parts):
        self.parts = parts
        self.hws = parts.hws

    def call(self, cmd, **params):
        answer = json.loads(self.parts.request(json.dumps({"id": "test", "cmd": cmd, "params": params})))
        if not answer["ok"]:
            raise BridgeError(answer.get("error"), answer.get("traceback"))
        return answer.get("result")

    def step(self):
        """One tick of the bridge's loop (without the defer that schedules the next)."""
        self.parts.step()


class Rig:
    """A fake REAPER and the bridges started in it. `f` is the fake's state (a Lua table)."""

    def __init__(self, resource_path):
        self.lua = lua54.LuaRuntime(unpack_returned_tuples=True, register_eval=False)
        self.resource_path = Path(resource_path)
        self.f = self.lua.eval(_NEW_REAPER)(FAKE.as_posix(), self.resource_path.as_posix())
        self._load = self.lua.eval(_LOAD_BRIDGE)

    def start_bridge(self):
        """Runs the script from the top, as starting it in REAPER does (a second one takes over)."""
        return Bridge(self._load(BRIDGE.as_posix()))

    def table(self, value):
        """A Python dict or list as a Lua table, for the fake's helpers."""
        return self.lua.table_from(value, recursive=True)
