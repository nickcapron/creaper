"""creaper's sound-design knowledge: every blueprint is well formed, can be found by the
names people use, and becomes parameters a microKORG takes."""

import pytest

from creaper import microkorg as mk
from creaper import sound_design as sd

WAVES = {"saw", "pulse", "square", "triangle", "sine", "noise"}
ENV = {"attack_ms", "decay_ms", "sustain", "release_ms"}


def test_every_family_has_sounds_and_every_sound_says_how_to_check_it():
    listed = sd.index()
    assert set(listed["sounds"]) == set(sd.FAMILIES) and all(listed["sounds"].values())
    assert len(sd.SOUNDS) >= 25 and len(sd.TECHNIQUES) >= 15 and len(sd.METHOD) >= 6
    for name, s in sd.SOUNDS.items():
        assert s["family"] in sd.FAMILIES and s["what"] and s["play"], name
        assert s["check"] and s["if"], name                 # what to measure, what to change
        assert s["blueprint"].get("amp_env"), name


@pytest.mark.parametrize("name", sorted(sd.SOUNDS))
def test_a_blueprint_uses_the_units_it_promises(name):
    b = sd.SOUNDS[name]["blueprint"]
    for osc in ("osc1", "osc2"):
        o = b.get(osc) or {}
        assert o.get("wave", "saw") in WAVES and 0 <= o.get("level", 1) <= 1
        assert abs(o.get("cents", 0)) <= 30 and 0.5 <= o.get("width", 0.5) <= 0.95
    f = b.get("filter") or {}
    assert f.get("type", "lp24") in ("lp24", "lp12", "bp", "hp")
    assert 40 <= f.get("cutoff_hz", 1000) <= 16000 and 0 <= f.get("resonance", 0) <= 1
    assert 0 <= f.get("key_track", 0) <= 1 and abs(f.get("env_octaves", 0)) <= 6
    for env in ("amp_env", "filter_env"):
        e = b.get(env) or {}
        assert set(e) <= ENV and 0 <= e.get("sustain", 1) <= 1
        assert all(0 <= e.get(k, 0) <= 10000 for k in ("attack_ms", "decay_ms", "release_ms"))
    for lfo in ("lfo1", "lfo2"):
        m = b.get(lfo) or {}
        assert m.get("to", "pitch") in ("pitch", "cutoff", "amp", "pan", "width")
        assert m.get("shape", "sine") in ("triangle", "sine", "saw", "square", "random")
    assert b.get("voices", "poly") in ("poly", "mono", "unison")


def test_sounds_and_techniques_are_found_by_the_names_people_use():
    assert sd.find("string pad")[0] == sd.find("strings")[0] == sd.find("String-Pad")[0] == "string pad"
    assert sd.find("303")[0] == "acid bass" and sd.find("laser")[0] == "zap" and sd.find("808 kick")[0] == "synth kick"
    assert sd.find("a sound nobody described") is None
    assert sd.find_technique("detune")[0] == "detune" and sd.find_technique("glide")[0] == "glide"
    assert "out of tune" in sd.TECHNIQUES["detune"] and "measure" in sd.TECHNIQUES["detune"]


# ------------------------------------------------------------ onto a microKORG

@pytest.mark.parametrize("name", sorted(sd.SOUNDS))
def test_every_blueprint_becomes_a_microkorg_patch(name):
    made = mk.from_design(sd.SOUNDS[name]["blueprint"])
    assert made["params"] and isinstance(made["approximate"], list) and isinstance(made["left_out"], list)
    prog = mk.decode_program(mk.build({"params": made["params"], "name": name[:12]}))   # every value is legal
    assert prog["voice_mode"] == "single"


def test_real_units_land_on_the_values_measured():
    cal = mk.CALIBRATION
    for curve in ("eg_attack_ms", "eg_decay_ms", "eg_release_ms", "osc2_tune_cents", "lfo1_hz", "lfo2_hz",
                  "portamento_ms_per_octave", "filter_eg_octaves", "delay_time_ms", "lfo_pitch_semitones",
                  "eg_pitch_semitones"):
        points = [(v, r) for v, r in cal[curve].items() if r is not None]
        assert len(points) >= 4, curve
        v, r = points[len(points) // 2]
        assert mk._value_for(cal[curve], r) == v, curve              # a measured point comes back exactly
    # the mistakes of 2026-11-13, now impossible: 60 cents asked for as "a little detune"
    strings = mk.from_design(sd.SOUNDS["string pad"]["blueprint"])["params"]
    assert 4 <= strings["osc2_tune"] <= 7                            # 8 cents, not 12 (which is 60)
    assert mk.cutoff_for(2089) == 60 and 71 <= mk.cutoff_for(2089 * 2) <= 73 and mk.cutoff_for(1) == 0
    glide = mk.from_design({"voices": "mono", "glide_ms": 90})["params"]["portamento"]
    assert mk._value_for(cal["portamento_ms_per_octave"], 90) == glide


def test_what_the_synth_cannot_do_is_said():
    made = mk.from_design({"osc2": {"wave": "sine", "level": 1}, "fx": {"chorus": 0.5, "phaser": 0.5},
                           "lfo2": {"shape": "sine", "hz": 1, "to": "width", "depth": 0.4}})
    assert any("no sine" in a for a in made["approximate"])
    assert any("one modulation effect" in x for x in made["left_out"]) and any("LFO1" in x for x in made["left_out"])
    five = {f"lfo{n}": {"shape": "sine", "hz": 1, "to": "pan", "depth": 0.5} for n in (1, 2)}
    assert mk.from_design(five)["left_out"] == []
