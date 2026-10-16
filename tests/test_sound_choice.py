import pytest

from creaper import server  # noqa: F401  (loads the tool modules first)
from creaper import sound_tools as st


def test_character_moves_the_targets():
    assert st.targets("lead", ["punchy"])["attack_ms"] == (0, 10)
    assert st.targets("pad", ["soft"])["attack_ms"][0] >= 25
    assert st.targets("keys", ["sustained"]).get("decay_s") is None


def test_scores_reward_a_fit_and_explain_a_miss():
    wanted = st.targets("pad")
    good = {"silent_notes": 0, "attack_ms": 300, "richness": 2, "sustain_db": -3}
    harsh = {"silent_notes": 0, "attack_ms": 2, "richness": 25, "sustain_db": -30}
    s_good, why_good = st.score(good, wanted)
    s_bad, why_bad = st.score(harsh, wanted)
    assert s_good == 0 and not why_good
    assert s_bad > 2 and any("attack" in w for w in why_bad) and any("richness" in w for w in why_bad)
    assert st.score({"silent_notes": 2}, wanted)[0] >= 100   # silent notes can't win


def test_summarise_takes_medians_and_counts_silence():
    results = [{"attack_ms": 5, "richness": 3, "sustain_db": -2, "peak_db": -6},
               {"attack_ms": 9, "richness": 5, "sustain_db": -4, "peak_db": -8},
               {"silent": True, "peak_db": -90}]
    m = st.summarise(results)
    assert m["silent_notes"] == 1 and m["attack_ms"] == 7 and m["richness"] == 4


def test_audition_keeps_the_best_preset_and_restores_the_rest(monkeypatch):
    loaded = {"preset": None}
    calls = []
    measured = {"Dull Pad": {"attack_ms": 2, "richness": 1.2, "sustain_db": -20},
                "Lush Pad": {"attack_ms": 400, "richness": 4, "sustain_db": -2}}

    def fake_call(command, **args):
        calls.append((command, args))
        if command == "get_track_details":
            return {"fx": [{"index": 1, "name": "VSTi: Synth", "instrument": True}]}
        if command == "list_fx_presets":
            return {"presets": [{"index": 1, "name": "Dull Pad"}, {"index": 2, "name": "Lush Pad"}]}
        if command == "capture_fx_state":
            return {"plugin": "VSTi: Synth", "chunk": "orig", "instrument": True}
        if command == "update_fx":
            loaded["preset"] = args.get("preset")
        return {}

    def fake_listen(track, pitches, channel, seconds, gap, velocity, chord=None):
        m = measured.get(loaded["preset"], {"attack_ms": 300, "richness": 3, "sustain_db": -2})  # the original
        return [dict(m) for _ in pitches], {"instrument": "VSTi: Synth"}

    from creaper import music_tools
    monkeypatch.setattr(st, "call", fake_call)
    monkeypatch.setattr(st.sound_library, "search", lambda *a, **k: [])
    monkeypatch.setattr(music_tools, "_listen", fake_listen)
    result = st.audition_sounds(track=1, role="pad", candidates="presets")
    assert result["loaded"] == "Lush Pad" and result["ranking"][0]["name"] == "Lush Pad"
    assert loaded["preset"] == "Lush Pad"
    # The original state goes back before the winner is loaded on top of it.
    order = [c for c, _ in calls if c in ("apply_fx_state", "update_fx")]
    assert order[-2:] == ["apply_fx_state", "update_fx"]


def test_bright_and_dark_are_judged_against_the_other_candidates():
    # Real patches measure a richness of about 1-2, so "bright" means the brightest of
    # what's there, not an absolute number every candidate misses.
    ranked = [{"name": "A", "score": 0.0, "why": [], "measured": {"richness": 1.1}},
              {"name": "B", "score": 0.0, "why": [], "measured": {"richness": 1.8}}]
    st.relative_brightness(ranked, ["bright"])
    assert ranked[1]["score"] == 0 and ranked[0]["score"] > 0.5
    ranked = [{"name": "A", "score": 0.0, "why": [], "measured": {"richness": 1.1}},
              {"name": "B", "score": 0.0, "why": [], "measured": {"richness": 1.8}}]
    st.relative_brightness(ranked, ["dark"])
    assert ranked[0]["score"] == 0 and ranked[1]["score"] > 0.5


def test_attack_under_5ms_doesnt_outweigh_everything_for_a_pad():
    # Attack is measured in 5 ms steps: 0 used to score log(60/0.001) = 11 for a pad.
    wanted = st.targets("pad")
    instant = st.score({"silent_notes": 0, "attack_ms": 0, "richness": 2, "sustain_db": -3}, wanted)[0]
    awful = st.score({"silent_notes": 0, "attack_ms": 5, "richness": 30, "sustain_db": -40}, wanted)[0]
    assert instant < awful


def test_a_piano_that_doesnt_decay_isnt_penalised_as_keys():
    assert st.score({"silent_notes": 0, "attack_ms": 5, "richness": 2}, st.targets("keys"))[0] == 0


def test_candidates_are_spread_through_the_list():
    names = [f"P{i}" for i in range(100)]
    picked = st._spread(names, 5)
    assert picked == ["P0", "P25", "P50", "P74", "P99"] and st._spread(names[:3], 5) == names[:3]


def _audition_fake(monkeypatch, presets, warn=(), track_fx=None):
    loaded = {"preset": None}
    calls = []

    def fake_call(command, **args):
        calls.append((command, args))
        if command == "get_track_details":
            return {"fx": track_fx or [{"index": 1, "name": "VSTi: Synth", "instrument": True}]}
        if command == "list_fx_presets":
            return {"presets": [{"index": i + 1, "name": n} for i, n in enumerate(presets)]}
        if command == "capture_fx_state":
            return {"plugin": "VSTi: Synth", "chunk": "orig", "instrument": True}
        if command == "update_fx" and "preset" in args:
            if args["preset"] in warn:
                return {"warning": f"no preset named '{args['preset']}' was found"}
            loaded["preset"] = args["preset"]
        return {}

    from creaper import music_tools
    monkeypatch.setattr(st, "call", fake_call)
    monkeypatch.setattr(st.sound_library, "search", lambda *a, **k: [])
    monkeypatch.setattr(music_tools, "_listen", lambda track, pitches, *a, **kw: (
        [{"attack_ms": 300, "richness": 2, "sustain_db": -2} for _ in pitches], {}))
    return loaded, calls


def test_a_preset_that_fails_to_load_isnt_credited_with_the_last_sound(monkeypatch):
    loaded, calls = _audition_fake(monkeypatch, ["Good Pad", "Missing Pad"], warn={"Missing Pad"})
    result = st.audition_sounds(track=1, role="pad", candidates="presets")
    missing = next(r for r in result["ranking"] if r["name"] == "Missing Pad")
    assert missing["score"] == 999.0 and "couldn't audition" in missing["why"][0]
    assert result["loaded"] == "Good Pad"


def test_track_effects_are_bypassed_while_listening_and_restored(monkeypatch):
    fx = [{"index": 1, "name": "VSTi: Synth", "instrument": True}, {"index": 2, "name": "VST: ReaVerbate (Cockos)"},
          {"index": 3, "name": "VST: ReaComp (Cockos) (bypassed)"}]
    loaded, calls = _audition_fake(monkeypatch, ["Pad A"], track_fx=fx)
    result = st.audition_sounds(track=1, role="pad", candidates="presets")
    toggles = [(a["fx"], a["enabled"]) for c, a in calls if c == "update_fx" and "enabled" in a]
    assert toggles == [("VST: ReaVerbate (Cockos)", False), ("VST: ReaVerbate (Cockos)", True)]
    assert result["effects_bypassed_while_listening"] == ["VST: ReaVerbate (Cockos)"]



def test_a_thin_bass_loses_to_one_with_low_end_weight():
    wanted = st.targets("bass")
    weighty = {"silent_notes": 0, "attack_ms": 5, "richness": 2, "sustain_db": -3, "low_share": 0.7}
    thin = {"silent_notes": 0, "attack_ms": 5, "richness": 2, "sustain_db": -3, "low_share": 0.1}
    assert st.score(weighty, wanted)[0] == 0 and st.score(thin, wanted)[0] > 1


def test_low_share_comes_from_the_measured_bands():
    results = [{"bands": {"sub": 0.3, "low": 0.3}, "attack_ms": 5}, {"bands": {"sub": 0.1, "low": 0.3}, "attack_ms": 5}]
    assert st.summarise(results)["low_share"] == 0.5


def test_the_winner_is_level_matched_to_the_original(monkeypatch):
    calls = []
    levels = {None: -12.0, "Loud Pad": -2.0}
    loaded = {"preset": None}

    def fake_call(command, **args):
        calls.append((command, args))
        if command == "get_track_details":
            return {"fx": [{"index": 1, "name": "VSTi: Synth", "instrument": True}], "volume_db": -3.0}
        if command == "list_fx_presets":
            return {"presets": [{"index": 1, "name": "Loud Pad"}]}
        if command == "capture_fx_state":
            return {"plugin": "VSTi: Synth", "chunk": "orig", "instrument": True}
        if command == "update_fx" and "preset" in args:
            loaded["preset"] = args["preset"]
        if command == "apply_fx_state":
            loaded["preset"] = None
        return {}

    from creaper import music_tools
    monkeypatch.setattr(st, "call", fake_call)
    monkeypatch.setattr(st.sound_library, "search", lambda *a, **k: [])
    monkeypatch.setattr(music_tools, "_listen", lambda track, pitches, *a, **kw: (
        [{"attack_ms": 300, "richness": 2, "sustain_db": -2, "peak_db": levels[loaded["preset"]]} for _ in pitches], {}))
    result = st.audition_sounds(track=1, role="pad", candidates="presets")
    assert result["fader_moved_db_to_match_level"] == -10.0
    assert ("set_track_properties", {"track": 1, "volume_db": -13.0}) in calls


# ------------------------------------------------------------------- tuning

def _note(freqs, seconds=1.2, fs=48000):
    """A harmonic tone gliding through `freqs` (Hz) over its length."""
    import numpy as np
    n = int(seconds * fs)
    f = np.interp(np.arange(n), np.linspace(0, n - 1, len(freqs)), freqs)
    phase = 2 * np.pi * np.cumsum(f) / fs
    return 0.3 * (np.sin(phase) + 0.5 * np.sin(2 * phase) + 0.25 * np.sin(3 * phase))


def test_features_measure_cents_off_and_drift():
    from creaper import listen
    in_tune = listen.features(_note([440]), 48000, note_off=1.0, expected_hz=440)
    sharp = listen.features(_note([452]), 48000, note_off=1.0, expected_hz=440)
    sagging = listen.features(_note([440, 440, 428]), 48000, note_off=1.0, expected_hz=440)
    assert abs(in_tune["cents_off"]) < 3 and abs(in_tune.get("drift_cents", 0)) < 3
    assert sharp["cents_off"] == pytest.approx(46.6, abs=3)
    assert sagging["drift_cents"] < -15
    # An octave up isn't out of tune.
    assert abs(listen.features(_note([880]), 48000, note_off=1.0, expected_hz=440)["cents_off"]) < 3


def test_out_of_tune_patches_score_worse_unless_detuned_is_wanted():
    wanted = st.targets("pad")
    base = {"silent_notes": 0, "attack_ms": 200, "richness": 2, "sustain_db": -3}
    in_tune = st.summarise([{"cents_off": 2.0}, {"cents_off": -3.0}, {"cents_off": 1.0}])
    off = st.summarise([{"cents_off": 2.0}, {"cents_off": -28.0}, {"cents_off": 1.0, "drift_cents": -40.0}])
    assert in_tune["tuning_spread_cents"] == 5.0 and off["tuning_spread_cents"] == 30.0 and off["drift_cents"] == 40.0
    good, _ = st.score({**base, **in_tune}, wanted)
    bad, why = st.score({**base, **off}, wanted)
    assert bad > good + 1 and any("out of tune" in w for w in why)
    allowed, why = st.score({**base, **off}, wanted, detuned=True)
    assert allowed == good and not any("out of tune" in w for w in why)


# ------------------------------------------------------- patches with a pattern

def _held(kind, seconds=1.2, fs=48000):
    import numpy as np
    t = np.arange(int(seconds * fs)) / fs
    f = np.full(t.size, 220.0)
    amp = np.minimum(1, t / 0.01)
    if kind == "vibrato":
        f = 220 * 2 ** (0.3 / 12 * np.sin(2 * np.pi * 6 * t))
    elif kind == "tremolo":
        amp = amp * 10 ** (3 * np.sin(2 * np.pi * 4 * t) / 20)
    elif kind == "arp":  # 16ths at 120 BPM over a minor triad and its octave, each re-attacked
        steps = np.array([0, 3, 7, 12])
        idx = (t / 0.125).astype(int)
        f = 220 * 2 ** (steps[idx % 4] / 12)
        amp = np.exp(-(t % 0.125) * 18)
    elif kind == "gate":  # a trance gate on 8ths
        amp = np.where((t / 0.25) % 1 < 0.5, 1.0, 0.02)
    phase = 2 * np.pi * np.cumsum(f) / fs
    return 0.3 * amp * (np.sin(phase) + 0.4 * np.sin(2 * phase))


@pytest.mark.parametrize("kind, expected", [("plain", False), ("vibrato", False), ("tremolo", False),
                                            ("arp", True), ("gate", True)])
def test_held_notes_that_play_a_pattern_are_caught(kind, expected):
    from creaper import listen
    f = listen.features(_held(kind), 48000, note_off=1.0, expected_hz=220)
    assert listen.plays_pattern(f) is expected, {k: f.get(k) for k in ("retriggers", "off_pitch_share")}


def test_a_patch_with_a_pattern_loses_the_audition():
    wanted = st.targets("lead")
    base = {"silent_notes": 0, "attack_ms": 5, "richness": 2, "sustain_db": -3}
    plain = st.summarise([{"retriggers": 0, "off_pitch_share": 0.0}] * 3)
    arp = st.summarise([{"retriggers": 6, "off_pitch_share": 0.7}] * 3)
    assert "plays_own_pattern" not in plain and arp["plays_own_pattern"] == 3
    good, _ = st.score({**base, **plain}, wanted)
    bad, why = st.score({**base, **arp}, wanted)
    assert bad >= good + 5 and any("pattern of its own" in w for w in why)


def _chord(arp, seconds=1.2, fs=48000):
    import numpy as np
    t = np.arange(int(seconds * fs)) / fs
    hz = [130.8, 164.8, 196.0]  # C major
    if arp:  # legato 16ths through the chord: no level dips, only the notes moving
        idx = (t / 0.125).astype(int) % 3
        f = np.array(hz)[idx]
        phase = 2 * np.pi * np.cumsum(f) / fs
        return 0.3 * (np.sin(phase) + 0.3 * np.sin(2 * phase))
    return sum(0.1 * (np.sin(2 * np.pi * h * t) + 0.3 * np.sin(4 * np.pi * h * t)) for h in hz)


def test_a_chord_shows_an_arpeggiator_a_single_note_hides():
    from creaper import listen
    held = listen.chord_motion(_chord(False), 48000, 1.0, 130.8)
    arped = listen.chord_motion(_chord(True), 48000, 1.0, 130.8)
    assert held["moving_share"] < 0.1 and not listen.plays_pattern(held)
    assert arped["moving_share"] > 0.5 and listen.plays_pattern(arped)


def test_a_deep_note_isnt_mistaken_for_retriggers():
    import numpy as np
    from creaper import listen
    t = np.arange(int(1.2 * 48000)) / 48000
    deep = 0.3 * np.minimum(1, t / 0.5) * (np.sin(2 * np.pi * 41.2 * t) + 0.5 * np.sin(4 * np.pi * 41.2 * t))
    f = listen.features(deep, 48000, note_off=1.0, expected_hz=41.2)
    assert f["retriggers"] == 0 and not listen.plays_pattern(f)



def test_a_patch_tuned_to_another_key_is_caught():
    from creaper import listen
    up3 = [listen.features(_note([440 * 2 ** ((p + 3) / 12)]), 48000, note_off=1.0, expected_hz=440 * 2 ** (p / 12))
           for p in (-12, 0, 7)]
    assert [r["semitones_off"] for r in up3] == [3, 3, 3]
    assert listen.transposition(up3) == 3
    in_tune = [listen.features(_note([440 * 2 ** (p / 12)]), 48000, note_off=1.0, expected_hz=440 * 2 ** (p / 12))
               for p in (-12, 0, 7)]
    assert listen.transposition(in_tune) is None
    # One misread note isn't a transposed patch.
    assert listen.transposition([{"semitones_off": 0}, {"semitones_off": 5}, {"semitones_off": 0}]) is None
    wanted = st.targets("lead")
    base = {"silent_notes": 0, "attack_ms": 5, "richness": 2, "sustain_db": -3}
    shifted = st.summarise(up3)
    assert shifted["transposed_semitones"] == 3
    bad, why = st.score({**base, **shifted}, wanted)
    assert bad >= 5 and any("another key" in w for w in why)
