"""Songs that finish while the user is away: no question for what can't hurt (auto_mix,
replacing creaper's own export, deleting an empty track, forgetting a note just saved),
switching back to the song's tab without asking, and saved notes that say when they
describe an older creaper."""

import time

import pytest

from creaper import server  # noqa: F401  (import order: server first)
from creaper import __version__, export_tools, knowledge, mix_tools


@pytest.fixture
def asked(monkeypatch):
    questions = []
    monkeypatch.setattr(server, "confirm_with_user", questions.append)
    monkeypatch.setattr(export_tools, "confirm_with_user", questions.append)
    monkeypatch.setenv(server.CONFIRM_FILE_ENV, "in the panel")
    return questions


def test_creapers_own_export_is_replaced_without_asking(asked, tmp_path, monkeypatch):
    monkeypatch.setattr(export_tools.bridge, "directory", tmp_path / "bridge", raising=False)
    (tmp_path / "bridge").mkdir()
    info = {"project": str(tmp_path / "song.rpp")}
    dest = tmp_path / "Master.wav"
    dest.write_bytes(b"first export")
    export_tools.remember_export(dest)
    export_tools._destination(str(tmp_path), "Master", "wav", info, overwrite=True)
    assert asked == []
    dest.write_bytes(b"the user's own edit")          # changed since creaper wrote it
    export_tools._destination(str(tmp_path), "Master", "wav", info, overwrite=True)
    assert len(asked) == 1 and "replace" in asked[0]


def test_an_empty_track_is_deleted_without_asking(asked, monkeypatch):
    tracks = {"Delay": {"number": 3, "name": "Delay", "guid": "{D}", "item_count": 0, "fx": {}},
              "Bass": {"number": 4, "name": "Bass", "guid": "{B}", "item_count": 2, "fx": ["VSTi: Mini V3"]}}
    deleted = []

    def fake_call(cmd, **kw):
        if cmd == "describe_track":
            return tracks[kw["track"]]
        deleted.append(kw["track"])
        return {"deleted": kw["track"]}

    monkeypatch.setattr(server, "call", fake_call)
    server.delete_track("Delay")
    assert asked == [] and deleted == ["{D}"]
    server.delete_track("Bass")
    assert len(asked) == 1 and "Bass" in asked[0] and deleted == ["{D}", "{B}"]


def test_auto_mix_doesnt_ask_and_checks_roles_before_rendering(monkeypatch):
    channels = [{"name": "Violin I", "track": 1, "ref": "{V}"}, {"name": "City Hum", "track": 2, "ref": "{H}"}]
    monkeypatch.setattr(mix_tools, "_channels", lambda: [dict(c) for c in channels])
    rendered = []
    monkeypatch.setattr(mix_tools, "call", lambda cmd, **kw: rendered.append(cmd) or {})
    with pytest.raises(ValueError, match="Violin 2"):
        mix_tools.auto_mix(roles={"Violin 2": "lead"})
    assert rendered == []                              # refused before ten minutes of rendering
    assert not hasattr(mix_tools, "confirm_with_user")  # auto_mix never asks: it saves a copy first


def test_auto_mix_reports_the_roles_it_used(monkeypatch):
    channels = [{"name": "Violin I", "track": 1, "ref": "{V}"}, {"name": "City Hum", "track": 2, "ref": "{H}"},
                {"name": "Guns", "track": 3, "ref": "{G}", "kit": True}]
    monkeypatch.setattr(mix_tools, "_channels", lambda: [dict(c) for c in channels])
    monkeypatch.setattr(mix_tools, "call", lambda cmd, **kw: {"stems": [], "files": []})
    report = mix_tools.auto_mix(roles={"violin i": "lead"}, dry_run=True)
    assert report["roles"] == {"Violin I": "lead", "City Hum": "fx (guessed)", "Guns": "drums (guessed)"}


def test_switch_project_tab_finds_a_tab_by_name(monkeypatch):
    tabs = [{"tab": 1, "name": "My Song.rpp", "active": False}, {"tab": 2, "name": "(unsaved)", "active": True}]
    switched = []

    def fake_call(cmd, **kw):
        if cmd == "list_project_tabs":
            return {"tabs": tabs}
        switched.append(kw["tab"])
        return {"tabs": tabs}

    monkeypatch.setattr(server, "call", fake_call)
    assert server.switch_project_tab()["tabs"] == tabs and switched == []
    server.switch_project_tab("my song")
    server.switch_project_tab("2")
    assert switched == [1, 2]
    with pytest.raises(ValueError, match="no tab"):
        server.switch_project_tab("Other Song")


def test_notes_about_creapers_tools_say_when_they_may_be_stale(tmp_path, monkeypatch):
    k = knowledge.Knowledge(tmp_path / "knowledge.json")
    monkeypatch.setattr(server, "knowledge", k)
    fresh = k.add("auto_mix handles VocalVST tracks", "mix")
    assert fresh["creaper"] == __version__ and knowledge.staleness(fresh) is None
    old_tool = {"topic": "mix", "text": "auto_mix chokes on VocalVST tracks: mix by hand", "creaper": "0.31.0"}
    unversioned = {"topic": "other", "text": "VocalVST captures at most ~100 notes per pass"}
    taste = {"topic": "preference", "text": "Wants talkbox vocals for Daft Punk style; avoid auto_mix", "creaper": "0.1.0"}
    plugin = {"topic": "plugin", "text": "Jup-8 V4's cutoff is its 12th control", "creaper": "0.20.0"}
    assert "0.31.0" in knowledge.staleness(old_tool)
    assert "older than 0.36" in knowledge.staleness(unversioned)
    assert knowledge.staleness(taste) is None and knowledge.staleness(plugin) is None
    k.add(old_tool["text"], "mix")
    with k._updating() as data:
        data["notes"][-1]["creaper"] = "0.31.0"
    found = {n["text"]: n for n in server.find_notes()["notes"]}
    assert "may_be_stale" in found[old_tool["text"]] and "may_be_stale" not in found[fresh["text"]]
    assert "saved_at" not in found[fresh["text"]]
    assert "Preference notes are the user's taste" in server.find_notes()["how_to_read"]


def test_a_note_saved_hours_ago_is_forgotten_without_asking(asked, tmp_path, monkeypatch):
    k = knowledge.Knowledge(tmp_path / "knowledge.json")
    monkeypatch.setattr(server, "knowledge", k)
    just_now = k.add("VocalVST captures at most ~100 notes per pass", "other")
    server.delete_note(just_now["id"])
    assert asked == []
    old = k.add("Prefers dark pads", "preference")
    with k._updating() as data:
        data["notes"][-1]["saved_at"] = time.time() - 3 * 86400
    server.delete_note(old["id"])
    assert len(asked) == 1 and "dark pads" in asked[0]
