"""layer_instrument, and a layered part mixed and measured as one."""

import pytest

from creaper import server  # noqa: F401  (import order: server first)
from creaper import ear_tools, mix_tools, sound_tools


def test_layer_instrument_routes_midi_and_builds_the_folder(monkeypatch):
    calls = []

    def fake_call(cmd, **kw):
        calls.append((cmd, kw))
        if cmd == "get_track_details":
            if kw["track"] == "Bass":
                return {"name": "Bass", "number": 2, "items": [{"id": "{A}", "type": "midi"}],
                        "fx": [{"index": 1, "name": "VST3i: Mini V3 (Arturia)", "instrument": True}]}
            return {"name": kw["track"], "fx": [{"index": 1 if "Transpose" not in str(calls) else 2,
                                                  "name": "ReaSynth", "instrument": True}]}
        if cmd == "add_fx":
            return {"index": 1 if kw.get("position") == 1 else 3}
        if cmd == "create_folder":
            return {"folder": {"name": kw["name"]}}
        if cmd == "create_track":
            return {"track": {"guid": "{LAYER-1}", "name": kw["name"]}}
        if cmd == "get_fx_parameters":
            return {"parameters": [{"name": kw["search"], "display": "180.0"}]}
        return {}

    monkeypatch.setattr(sound_tools, "call", fake_call)
    out = sound_tools.layer_instrument(track="Bass", layers=[
        sound_tools.SoundLayer(instrument="ReaSynth", octave=-1, lowpass_hz=180, volume_db=-4)])
    assert out["folder"] == "Bass (layered)"
    names = [c for c, _ in calls]
    assert ("create_track", {"name": "Bass layer 1", "instrument": "ReaSynth", "position": 3}) in calls
    transpose = next(kw for c, kw in calls if c == "set_fx_parameters" and kw["changes"][0]["parameter"].startswith("Transpose"))
    assert transpose["changes"][0]["display_value"] == -12
    lpf = next(kw for c, kw in calls if c == "set_fx_parameters" and kw["changes"][0]["parameter"] == "Frequency (Hz)")
    assert lpf["changes"][0]["value"] == pytest.approx((180 - 20) / 19980) and lpf["track"] == "{LAYER-1}"
    assert ("set_send", {"source": "Bass", "destination": "{LAYER-1}", "midi_only": True}) in calls
    folder = next(kw for c, kw in calls if c == "create_folder")
    assert folder["tracks"] == ["Bass", "{LAYER-1}"]
    assert names.index("set_send") < names.index("create_folder")
    assert out["layers"][0]["filters"] == ["low pass 180 Hz"]


def test_layer_needs_one_source_and_a_midi_part(monkeypatch):
    monkeypatch.setattr(sound_tools, "call", lambda cmd, **kw: {"name": "Pad", "items": []})
    with pytest.raises(ValueError, match="no MIDI part"):
        sound_tools.layer_instrument(track="Pad", layers=[sound_tools.SoundLayer(instrument="ReaSynth")])
    monkeypatch.setattr(sound_tools, "call", lambda cmd, **kw: {"name": "Pad", "items": [{"type": "midi"}]})
    with pytest.raises(ValueError, match="exactly one"):
        sound_tools.layer_instrument(track="Pad", layers=[sound_tools.SoundLayer(instrument="ReaSynth", sound="x")])
    with pytest.raises(ValueError, match="the part's own name"):
        sound_tools.layer_instrument(track="Pad", layers=[sound_tools.SoundLayer(instrument="ReaSynth", name="Pad")])


OVERVIEW = {"tracks": [
    {"number": 1, "name": "Drums", "item_count": 4, "fx": [], "guid": "g1"},
    {"number": 2, "name": "Bass (layered)", "item_count": 0, "fx": [], "guid": "g2"},
    {"number": 3, "name": "Bass", "item_count": 3, "fx": ["VST3i: Mini V3"], "guid": "g3"},
    {"number": 4, "name": "Bass layer 1", "item_count": 0, "fx": ["ReaSynth"], "guid": "g4"},
]}
ROUTING = {"tracks": [{"name": "Drums"}, {"name": "Bass (layered)", "folder": "starts a folder"},
                      {"name": "Bass", "in_folder": "Bass (layered)"},
                      {"name": "Bass layer 1", "in_folder": "Bass (layered)"}]}


def test_auto_mix_mixes_a_layered_part_on_its_folder(monkeypatch):
    monkeypatch.setattr(mix_tools, "call", lambda cmd, **kw: OVERVIEW if cmd == "get_project_overview" else ROUTING)
    channels = mix_tools._channels()
    assert [c["name"] for c in channels] == ["Drums", "Bass (layered)"]
    assert channels[1]["layered"] and mix_tools.role_of(channels[1]["name"]) == "bass"


def test_measure_tracks_measures_a_layered_part_as_one(monkeypatch):
    monkeypatch.setattr(ear_tools, "call", lambda cmd, **kw: ROUTING)
    assert ear_tools._parts(OVERVIEW) == [1, 2]
