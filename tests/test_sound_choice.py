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

    def fake_listen(track, pitches, channel, seconds, gap, velocity):
        m = measured[loaded["preset"]]
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
