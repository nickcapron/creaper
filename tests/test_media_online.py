"""Offline media before renders: REAPER takes audio items offline when the user is in
another app ("Set media items offline when application is not active", on by default),
and an offline item renders as silence while the MIDI parts still play.

Every render first asks the bridge which audio items are offline and brings only those
back online, without a prompt and never with "Set all media online" (on a OneDrive
project that held REAPER for minutes). The cause is explained once. A render that comes
back silent anyway still gets one "Set all media online" and a second render."""

import asyncio
import json

import numpy as np
import soundfile as sf

from creaper import server


class FakeBridge:
    def __init__(self, tmp_path, silent_until=0, offline=0, pref=True, still_offline=0, knows_media=True):
        self.directory = tmp_path
        (tmp_path / "renders").mkdir(exist_ok=True)
        self.renders, self.actions, self.silent_until = 0, [], silent_until
        self.offline, self.pref, self.still_offline, self.knows_media = offline, pref, still_offline, knows_media
        self.checks = []

    def call(self, cmd, params=None, timeout=30.0):
        params = params or {}
        if cmd == "media_online":
            if not self.knows_media:
                raise server.BridgeError("this bridge (v0.31.1) doesn't know 'media_online'; update creaper_bridge.lua")
            self.checks.append(params.get("fix"))
            out = {"offline": self.offline, "tracks": ["City Bed", "Traffic"] if self.offline else [], "missing": []}
            if self.offline:
                out["offline_when_inactive"] = self.pref or None
                out["still_offline"] = self.still_offline
                self.offline = self.still_offline
            return out
        if cmd == "describe_action":
            return {"command_id": int(params["command"]), "name": "Item: Set all media online"}
        if cmd == "run_action":
            self.actions.append(params["command"])
            return {}
        if cmd == "time_to_positions":
            return [{"bar": 1, "beat": 1} for _ in params.get("times", [])]
        self.renders += 1
        f = self.directory / "renders" / f"r{self.renders}.wav"
        level = 0.0 if self.renders <= self.silent_until else 0.3
        sf.write(str(f), np.full((4800, 2), level, dtype=np.float32), 48000)
        return {"files": [str(f)], "track": {"name": "MASTER", "number": "master"},
                "start": {"seconds": 0.0}, "end": {"seconds": 0.1}}


def _fresh(monkeypatch, fake):
    monkeypatch.setattr(server, "bridge", fake)
    monkeypatch.setattr(server, "_media_tried", [0.0])
    monkeypatch.setattr(server, "_media_explained", [False])
    monkeypatch.setattr(server, "_notices", [])
    monkeypatch.setattr(server, "_noticed", set())


def _tool(name, args):
    """Calls a tool the way the chat panel does, through the MCP wrapper."""
    result = asyncio.run(server.mcp.call_tool(name, args))
    blocks = result if isinstance(result, list) else getattr(result, "content", result)
    if isinstance(blocks, tuple):
        blocks = blocks[0]
    if getattr(result, "isError", False):
        raise AssertionError(blocks[0].text)
    return json.loads(blocks[0].text)


def test_every_render_checks_for_offline_media_first(monkeypatch, tmp_path):
    fake = FakeBridge(tmp_path)
    _fresh(monkeypatch, fake)
    server.call("render_audio", track="master")
    server.call("render_stems", tracks=[1])
    assert fake.checks == [True, True] and fake.actions == [] and fake.renders == 2


def test_offline_items_come_back_online_without_the_whole_project_action(monkeypatch, tmp_path):
    fake = FakeBridge(tmp_path, offline=3)
    _fresh(monkeypatch, fake)
    server.call("render_audio", track="master")
    assert fake.offline == 0 and fake.renders == 1
    assert fake.actions == []  # no "Set all media online", no confirmation prompt


def test_the_preference_is_named_once_on_the_next_tool_result(monkeypatch, tmp_path):
    fake = FakeBridge(tmp_path, offline=2)
    _fresh(monkeypatch, fake)
    first = _tool("analyze_audio", {"track": "master"})
    assert "Set media items offline when application is not active" in first["notice"]
    assert "Options > Preferences > Media" in first["notice"] and "City Bed" in first["notice"]
    fake.offline = 2  # the user went to another app again
    second = _tool("analyze_audio", {"track": "master"})
    assert "notice" not in second and fake.offline == 0  # fixed again, not explained again


def test_items_that_stay_offline_are_reported(monkeypatch, tmp_path):
    fake = FakeBridge(tmp_path, offline=2, still_offline=1)
    _fresh(monkeypatch, fake)
    server.call("render_audio", track="master")
    assert "couldn't bring them back online" in server._pending_notices()


def test_an_older_bridge_still_renders(monkeypatch, tmp_path):
    fake = FakeBridge(tmp_path, knows_media=False)
    _fresh(monkeypatch, fake)
    out = server.call("render_audio", track="master")
    assert fake.renders == 1 and out["files"][0].endswith("r1.wav")


def test_run_action_set_all_media_online_does_the_quick_fix_without_asking(monkeypatch, tmp_path):
    fake = FakeBridge(tmp_path, offline=2)
    _fresh(monkeypatch, fake)
    asked = []
    monkeypatch.setattr(server, "confirm_with_user", lambda action: asked.append(action))
    out = server.run_action(40101)
    assert asked == [] and fake.actions == [] and fake.offline == 0
    assert "no need" in out["note"]


def test_export_says_when_its_render_differs_from_the_master_check(monkeypatch):
    monkeypatch.setattr(server, "_master_check", {})
    whole = {"loudness": {"integrated_lufs": -20.0}, "duration_seconds": 297.9}
    server._remember_master(whole, "master", None, None)
    quieter = {"loudness": {"integrated_lufs": -20.6}, "duration_seconds": 299.9}
    assert "-20.6" in server.master_mismatch(quieter, tail_seconds=2.0)
    same = {"loudness": {"integrated_lufs": -20.2}, "duration_seconds": 297.9}
    assert server.master_mismatch(same, tail_seconds=0.0) is None
    other_length = {"loudness": {"integrated_lufs": -25.0}, "duration_seconds": 120.0}
    assert server.master_mismatch(other_length, tail_seconds=0.0) is None
    server._remember_master({"loudness": {"integrated_lufs": -30.0}, "duration_seconds": 60.0}, "master", 5, 9)
    assert server._master_check["lufs"] == -20.0  # a section measurement isn't a master check


def test_a_silent_render_brings_media_online_once(monkeypatch, tmp_path):
    fake = FakeBridge(tmp_path, silent_until=1)
    _fresh(monkeypatch, fake)
    out = server.call("render_audio", track="master")
    assert fake.actions == [server.MEDIA_ONLINE_ACTION] and fake.renders == 2
    assert out["files"][0].endswith("r2.wav") and not (tmp_path / "renders" / "r1.wav").exists()


def test_a_sounding_render_never_runs_the_action(monkeypatch, tmp_path):
    fake = FakeBridge(tmp_path, silent_until=0)
    _fresh(monkeypatch, fake)
    server.call("render_audio", track="master")
    assert fake.actions == [] and fake.renders == 1


def test_a_truly_silent_range_is_left_alone_after_one_try(monkeypatch, tmp_path):
    fake = FakeBridge(tmp_path, silent_until=99)
    _fresh(monkeypatch, fake)
    server.call("render_audio", track="master")
    server.call("render_audio", track="master")          # a quiet tail measured again
    assert fake.actions == [server.MEDIA_ONLINE_ACTION]  # tried once, not every time
