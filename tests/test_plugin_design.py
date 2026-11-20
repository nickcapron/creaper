"""Blueprints in real units as a plugin synth's parameter values (Prophet-5 V)."""

import pytest

from creaper import server  # noqa: F401  (import order: server first)
from creaper import music_tools, plugin_design as pd, sound_design, sound_tools


def values(blueprint):
    design = pd.PROFILES["Prophet-5 V"]["from_design"](blueprint)
    return {c["parameter"]: c.get("display_value", c.get("display_text", c.get("value"))) for c in design["changes"]}, design


def test_real_units_go_through_the_measured_calibration():
    """Measured offline 2026-11-18: the envelope dial 1.00 = 1.11 octaves, a decay shown as
    0.5 s falls 20 dB in 0.158 s, a release shown as 0.5 s in 0.24 s, fine tune 0.3 = 30 cents."""
    v, d = values({"voices": "poly", "osc1": {"wave": "saw", "level": 1.0}, "osc2": {"wave": "square", "level": 0.8, "cents": 12},
                   "filter": {"type": "lp24", "cutoff_hz": 350, "resonance": 0.2, "env_octaves": 2.5, "key_track": 0.4},
                   "filter_env": {"attack_ms": 1, "decay_ms": 160, "sustain": 0.25, "release_ms": 80},
                   "amp_env": {"attack_ms": 30, "release_ms": 240}})
    assert v["Filter Frequency"] == 350 and v["Filter Resonance"] == 2.0 and v["Filter Key Follow"] == "Off"
    assert v["Filter Envelope Modulation"] == pytest.approx(2.25, abs=0.01)
    assert v["VCF Decay"] == pytest.approx(0.485, abs=0.005) and v["VCF Sustain"] == 0.25
    assert v["VCA Attack"] == pytest.approx(0.05, abs=0.001) and v["VCA Release"] == pytest.approx(0.5, abs=0.005)
    assert v["VCO 2 Square"] == "On" and v["VCO 2 Saw"] == "Off" and v["VCO 2 Level"] == 8.0 and v["VCO 2 Fine Tune"] == 0.12
    assert v["SawOn1"] == "On" and v["Unison"] == "Off" and not d["left_out"]


def test_what_the_plugin_cannot_do_is_said_not_dropped():
    v, d = values({"osc1": {"wave": "sine", "level": 1.0}, "osc2": {"wave": "saw"}, "osc_mod": "ring",
                   "filter": {"type": "hp", "cutoff_hz": 9000, "velocity": 0.5, "env_octaves": -2},
                   "lfo1": {"shape": "random", "hz": 6, "to": "pan", "depth": 0.5}, "lfo2": {"hz": 1}, "fx": {"distortion": True}})
    assert v["VCO 1 Level"] == 0.0 and v["VCO 2 Triangle"] == "On"            # the triangle is on VCO 2
    said = " | ".join(d["left_out"])
    for word in ("osc2", "ring", "filter type hp", "velocity", "closes the filter", "random", "LFO to pan", "lfo2"):
        assert word in said, word
    assert any("no sine" in a for a in d["approximate"]) and v["Filter Frequency"] == 6214
    assert d["effects"] == [{"add": "JS: Saturation", "set": [{"parameter": "Amount (%)", "display_value": 45}], "for": "distortion"}]


def test_vibrato_and_a_pitch_envelope_use_the_measured_depths():
    v, d = values({"voices": "mono", "glide_ms": 90, "lfo1": {"shape": "triangle", "hz": 5.5, "to": "pitch", "depth": 0.3},
                   "pitch_env": {"semitones": 12, "decay_ms": 100}})
    assert v["Mod Wheel"] == pytest.approx(0.0657, abs=0.001) and v["MW/LFO VCO 1 Frequency Modulation"] == "On"
    assert v["Filter Envelope"] == pytest.approx(3.28, abs=0.01) and v["Freq 1"] == "On" and v["VCF Sustain"] == 0.0
    assert v["Unison"] == "On" and v["Glide"] == 0.09 and v["LFO Rate Unsynced"] == 5.5


def test_every_built_in_blueprint_translates_and_the_plain_sound_is_whole():
    for name, entry in sound_design.SOUNDS.items():
        v, d = values(entry["blueprint"])
        assert all(isinstance(c["parameter"], str) for c in d["changes"]), name
    plain = [c["parameter"] for c in pd.P5_PLAIN]
    assert len(plain) == len(set(plain)) and {"FX1 Bypass", "FX2 Bypass", "FX3 Bypass", "Arp On/Off", "Master Volume"} <= set(plain)
    assert pd.find("VST3i: Prophet-5 V (Arturia)")[0] == "Prophet-5 V" and pd.find("Jun-6 V") is None


def test_the_tool_sets_the_plain_sound_then_the_blueprint_and_listens(monkeypatch):
    calls = []

    def fake(cmd, **kw):
        calls.append((cmd, kw))
        if cmd == "get_track_details":
            return {"name": "Lead", "number": 3, "fx": [{"index": 1, "name": "VST: ReaEQ (Cockos)"}]}
        if cmd == "add_fx":
            return {"index": kw.get("position") or 9, "instrument": "Prophet" in kw["name"],
                    "name": "JS: Saturation" if "Saturation" in kw["name"] else "VST3i: Prophet-5 V (Arturia)"}
        if cmd == "set_fx_parameters":
            return {"results": [{"parameter": c["parameter"]} for c in kw["changes"]]}
        raise AssertionError(cmd)

    monkeypatch.setattr(sound_tools, "call", fake)
    monkeypatch.setattr(music_tools, "audition_instrument", lambda track: {
        "summary": {"sounding": True, "median_brightness_hz": 1800}, "notes": [{"note": "C3", "decay_s": 0.2, "more": 1}]})
    dry = sound_tools.design_plugin_sound(track="Lead", sound="acid bass", dry_run=True)
    assert dry["dry_run"] and dry["set"]["Filter Resonance"] == 7.0 and not calls and dry["effects"][0]["for"] == "distortion"
    out = sound_tools.design_plugin_sound(track="Lead", sound="acid bass")
    added = [kw for c, kw in calls if c == "add_fx"]
    assert added[0]["name"] == "Prophet-5 V" and added[0]["position"] == 1
    assert {k: added[1][k] for k in ("track", "name", "position")} == {"track": 3, "name": "JS: Saturation", "position": 2}
    sets = [kw for c, kw in calls if c == "set_fx_parameters"]
    names = [c["parameter"] for c in sets[0]["changes"]]
    assert names.index("FX1 Bypass") < len(pd.P5_PLAIN) <= len(names) - 1 and names[len(pd.P5_PLAIN):]     # plain first, the blueprint over it
    assert out["measured"] == {"sounding": True, "median_brightness_hz": 1800, "notes": [{"note": "C3", "decay_s": 0.2}]}
    assert out["effects"][0]["on_the_track"] == "JS: Saturation"
    assert out["play"] and out["check"]
    with pytest.raises(ValueError, match="no design profile"):
        sound_tools.design_plugin_sound(track="Lead", sound="acid bass", plugin="Serum")
    with pytest.raises(ValueError, match="not blueprint fields"):
        sound_tools.design_plugin_sound(track="Lead", blueprint={"filtre": {}})


def test_every_audition_role_has_a_blueprint_to_design_from():
    import typing

    roles = set(typing.get_args(sound_tools.Role))
    assert set(sound_tools.ROLE_BLUEPRINTS) == roles
    for role, name in sound_tools.ROLE_BLUEPRINTS.items():
        assert sound_design.find(name) is not None, (role, name)


def test_audition_points_to_design_only_when_nothing_fits():
    """The song procedure picks presets first; when the best is still well off, audition_sounds
    says to design the sound (design_plugin_sound) instead of keeping a near miss."""
    assert sound_tools.none_fit_note("lead", {"score": 0.4}) is None
    assert sound_tools.none_fit_note("lead", {"score": sound_tools.NO_FIT_SCORE}) is None
    far = sound_tools.none_fit_note("pad", {"score": 3.2})
    assert "design_plugin_sound(track, sound='warm pad')" in far and "3.2" in far
    assert "no candidate played properly" in sound_tools.none_fit_note("bass", None)


def test_game_sound_rules_are_in_the_guide():
    """The slot-machine rules a real game's set was rebuilt by (2026-11-18), found by the panel."""
    for asked in ("game sounds", "game"):
        name, how = sound_design.find_technique(asked)
        assert name == "game sounds"
    for rule in ("one key", "never buzzes", "tritone", "plate", "frequent ticks -14"):
        assert rule in how, rule
