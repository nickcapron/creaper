"""Renders of an unchanged project are served again instead of rendered again: keyed on
REAPER's project state change count, on the changing commands this process sent, on
the project and bridge run, and on the render's parameters. A hit is the same file (a
fresh link the caller deletes like any render), so every check reads the same numbers."""

import numpy as np
import soundfile as sf

from creaper import server


class FakeReaper:
    """A bridge whose project has a state change count that moves on edits."""

    def __init__(self, tmp_path, knows_state=True, level=0.3):
        self.directory = tmp_path
        (tmp_path / "renders").mkdir(exist_ok=True)
        self.renders, self.count, self.instance, self.project = 0, 10, "run1", "C:/songs/a.rpp"
        self.knows_state, self.level, self.asked = knows_state, level, []

    def call(self, cmd, params=None, timeout=30.0):
        params = params or {}
        self.asked.append(cmd)
        if cmd == "project_state":
            if not self.knows_state:
                raise server.BridgeError("this bridge (v0.42.0) doesn't know 'project_state'; update creaper_bridge.lua")
            return {"change_count": self.count, "project": self.project, "instance": self.instance}
        if cmd == "media_online":
            return {"offline": 0, "missing": []}
        if cmd in ("set_track_properties", "set_fx_parameters", "add_fx"):
            self.count += 1
            return {}
        if cmd in ("get_track_details", "time_to_positions"):
            return {}
        self.renders += 1   # the bridge hides what its own render settings add to the count
        names = params.get("tracks") or [params.get("track", "master")]
        files = []
        for n in names:
            f = self.directory / "renders" / f"render_{self.renders}_{n}.wav"
            sf.write(str(f), np.full((4800, 2), self.level, dtype=np.float32), 48000)
            files.append(str(f))
        if cmd == "render_stems":
            return {"files": files, "stems": [{"track": {"name": f"T{n}", "number": n}, "file": f}
                                              for n, f in zip(names, files)],
                    "start": {"seconds": 0.0}, "end": {"seconds": 0.1}}
        return {"files": files, "track": {"name": "MASTER", "number": "master"},
                "start": {"seconds": 0.0}, "end": {"seconds": 0.1}}


def _fresh(monkeypatch, fake):
    monkeypatch.setattr(server, "bridge", fake)
    monkeypatch.setattr(server, "_render_cache", server.RenderCache())
    monkeypatch.setattr(server, "_media_tried", [0.0])
    monkeypatch.setattr(server, "_notices", [])
    monkeypatch.setattr(server, "_noticed", set())


def _use(result):
    """What every caller does with a render: read it, then delete it."""
    audio, fs = sf.read(result["files"][0], always_2d=True)
    for f in result["files"]:
        server.Path(f).unlink()
    return audio


def test_the_same_render_of_an_unchanged_project_is_served_from_the_first(monkeypatch, tmp_path):
    fake = FakeReaper(tmp_path)
    _fresh(monkeypatch, fake)
    first = server.call("render_audio", track="master", start_bar=None, end_bar=None)
    a = _use(first)
    second = server.call("render_audio", track="master")          # None values don't make another key
    assert fake.renders == 1
    assert second["files"][0] != first["files"][0] and second["files"][0].startswith(str(tmp_path / "renders"))
    assert second["track"] == first["track"] and second["end"] == first["end"]
    b = _use(second)
    assert np.array_equal(a, b)
    third = server.call("render_audio", track="master")           # deleting the hit didn't hurt the kept copy
    assert fake.renders == 1 and server.Path(third["files"][0]).exists()
    assert server._render_cache.hits == 2


def test_a_changing_command_or_an_edit_in_reaper_renders_afresh(monkeypatch, tmp_path):
    fake = FakeReaper(tmp_path)
    _fresh(monkeypatch, fake)
    _use(server.call("render_audio", track="master"))
    server.call("set_track_properties", track="Bass", volume_db=-3.0)   # through the bridge
    _use(server.call("render_audio", track="master"))
    assert fake.renders == 2
    _use(server.call("render_audio", track="master"))
    assert fake.renders == 2                                             # nothing since: a hit
    fake.count += 1                                                      # the user turned a knob in REAPER
    _use(server.call("render_audio", track="master"))
    assert fake.renders == 3
    server.call("get_track_details", track="Bass")                       # reading changes nothing
    _use(server.call("render_audio", track="master"))
    assert fake.renders == 3


def test_a_different_range_track_or_tail_is_its_own_render(monkeypatch, tmp_path):
    fake = FakeReaper(tmp_path)
    _fresh(monkeypatch, fake)
    _use(server.call("render_audio", track="master"))
    _use(server.call("render_audio", track="master", start_bar=9.0, end_bar=17.0))
    _use(server.call("render_audio", track="Drums"))
    _use(server.call("render_audio", track="master", tail_seconds=2.0))
    assert fake.renders == 4
    _use(server.call("render_audio", track="master", tail_seconds=0))   # no tail is the plain render
    _use(server.call("render_audio", track="master", start_bar=9.0, end_bar=17.0))
    assert fake.renders == 4


def test_stems_come_back_mapped_to_their_tracks(monkeypatch, tmp_path):
    fake = FakeReaper(tmp_path)
    _fresh(monkeypatch, fake)
    first = server.call("render_stems", tracks=[1, 2])
    for f in first["files"]:
        server.Path(f).unlink()
    again = server.call("render_stems", tracks=[1, 2])
    assert fake.renders == 1
    assert [s["track"]["number"] for s in again["stems"]] == [1, 2]
    assert again["files"] == [s["file"] for s in again["stems"]]
    assert all(server.Path(s["file"]).exists() for s in again["stems"])
    assert server.call("render_stems", tracks=[2, 1])["files"] != again["files"] and fake.renders == 2


def test_an_older_bridge_renders_as_before_and_is_asked_once(monkeypatch, tmp_path):
    fake = FakeReaper(tmp_path, knows_state=False)
    _fresh(monkeypatch, fake)
    _use(server.call("render_audio", track="master"))
    _use(server.call("render_audio", track="master"))
    assert fake.renders == 2 and fake.asked.count("project_state") == 1


def test_silence_a_restarted_reaper_and_old_age_are_not_served(monkeypatch, tmp_path):
    fake = FakeReaper(tmp_path, level=0.0)
    _fresh(monkeypatch, fake)
    monkeypatch.setattr(server, "_media_tried", [server.time.time()])   # the offline-media retry already ran
    _use(server.call("render_audio", track="master"))
    _use(server.call("render_audio", track="master"))
    assert fake.renders == 2                                             # a silent render may be offline media
    fake.level = 0.3
    _use(server.call("render_audio", track="master"))
    _use(server.call("render_audio", track="master"))
    assert fake.renders == 3
    fake.instance = "run2"                                               # REAPER restarted: counts start over
    _use(server.call("render_audio", track="master"))
    assert fake.renders == 4
    for entry in server._render_cache._entries.values():
        entry["at"] -= server.CACHE_TTL_S + 1
    _use(server.call("render_audio", track="master"))
    assert fake.renders == 5


def test_kept_renders_live_in_their_own_folder_and_make_room(monkeypatch, tmp_path):
    fake = FakeReaper(tmp_path)
    _fresh(monkeypatch, fake)
    monkeypatch.setattr(server, "CACHE_MAX_BYTES", 2 * 20000)   # room for two of these 19 KB renders
    for track in ("Kick", "Snare", "Hat"):
        _use(server.call("render_audio", track=track))
    folder = server._render_cache.folder()
    assert folder.parent == tmp_path / "renders" / "cache"
    assert len(list(folder.iterdir())) == 2                                  # the oldest (Kick) made room
    _use(server.call("render_audio", track="Kick"))
    assert fake.renders == 4
    server.call("add_fx", track="Kick", name="ReaEQ")
    _use(server.call("render_audio", track="Hat"))
    assert len(list(folder.iterdir())) == 1                                  # the rest can't hit again
