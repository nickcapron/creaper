"""The same measurements in fewer renders: shared stem passes, batched compressor
calibration from a predicted start, span hints, and the limiter model."""

import numpy as np
import pytest
import soundfile as sf

from creaper import server  # noqa: F401  (import order: server first)
from creaper import analysis, batch, plugin_profiles

FS = 22050


def drums(bars, level, seed, bpm=120):
    """A kick-and-hat loop: one bar is 2 s at 120 BPM."""
    rng = np.random.default_rng(seed)
    beat = int(FS * 60 / bpm)
    out = np.zeros(bars * 4 * beat)
    t = np.arange(beat) / FS
    for b in range(bars * 4):
        hit = np.sin(2 * np.pi * 60 * t) * np.exp(-t * 25) + rng.normal(0, 0.05, beat) * np.exp(-t * 60)
        out[b * beat:(b + 1) * beat] += hit * level * (1.0 if b % 2 == 0 else 0.6)
    return out


def test_the_model_finds_a_threshold_for_its_target():
    dry = np.stack([drums(8, 0.5, 1)] * 2, axis=1)
    t = batch.predict_threshold(dry, FS, 3.0, ratio=4, attack_ms=15, release_ms=80)
    wet = batch.simulate_compressor(dry, FS, t, 4, 15, 80)
    assert analysis.gain_reduction(dry[: len(wet)], wet, FS)["gr_db_p95"] == pytest.approx(3.0, abs=0.4)
    assert batch.predict_threshold(dry * 1e-4, FS, 3.0, 4, 15, 80, lo=-30) is None   # can't get there


class Bench:
    """Tracks whose ReaComp is the model itself, rendered in groups like render_stems."""

    def __init__(self, tracks):
        self.audio = tracks                      # name -> dry audio
        self.threshold = {n: 0.0 for n in tracks}
        self.enabled = {n: True for n in tracks}
        self.passes = []

    def call(self, cmd, **kw):
        t = kw.get("track")
        if cmd == "update_fx":
            self.enabled[t] = kw["enabled"]
        elif cmd == "get_fx_parameters":
            params = [{"name": "Threshold", "display": f"{self.threshold[t]:.2f}"},
                      {"name": "Ratio", "display": "4.0:1"}, {"name": "Attack", "display": "15 ms"},
                      {"name": "Release", "display": "80 ms"}]
            return {"parameters": params}
        elif cmd == "set_fx_parameters":
            self.threshold[t] = kw["changes"][0]["display_value"]
        return {}

    def render_group(self, tracks, lo, hi):
        self.passes.append(list(tracks))
        out = {"_fs": FS}
        for t in tracks:
            x = self.audio[t]
            out[t] = batch.simulate_compressor(x, FS, self.threshold[t], 4, 15, 80) if self.enabled[t] else x
        return out


def test_compressors_calibrate_together_in_shared_passes(monkeypatch):
    bench = Bench({"Kick": np.stack([drums(8, 0.6, 1)] * 2, axis=1), "Snare": np.stack([drums(8, 0.3, 2)] * 2, axis=1)})
    monkeypatch.setattr(server, "call", bench.call)
    monkeypatch.setattr(batch, "render_group", bench.render_group)
    profile = plugin_profiles.find_profile("ReaComp")
    jobs = [{"track": "Kick", "fx": 1, "profile": profile, "target": 2.5, "span": (9.0, 17.0)},
            {"track": "Snare", "fx": 1, "profile": profile, "target": 2.5, "span": (9.0, 17.0)}]
    out = batch.calibrate_many(jobs)
    assert all(abs(r["loud_part_reduction_db"] - 2.5) <= 0.3 for r in out), out
    assert all("predicted_start" in r for r in out)
    assert bench.passes[0] == ["Kick", "Snare"]                   # one dry pass for both
    assert len(bench.passes) <= 3                                # dry + a check or two, not 8 per track


def test_a_hinted_span_skips_the_full_render(monkeypatch):
    bench = Bench({"Drums": np.stack([drums(8, 0.5, 3)] * 2, axis=1)})
    ranges = []

    def render_array(track, lo, hi):
        ranges.append((lo, hi))
        return bench.render_group([track], lo, hi)[track], FS, {"start": {"seconds": 0.0}}

    monkeypatch.setattr(server, "call", bench.call)
    monkeypatch.setattr(server, "_render_array", render_array)
    with batch.span_hints({"Drums": (5.0, 13.0)}):
        out = server._calibrate_compressor("Drums", 1, plugin_profiles.find_profile("ReaComp"), 2.5, None, None)
    assert (None, None) not in ranges and set(ranges) == {(5.0, 13.0)}
    assert out["measured_on_bars"] == [5.0, 13.0]
    assert batch.hinted_span("Drums") is None                    # the hint ends with its block


def test_render_group_matches_stems_by_name(monkeypatch, tmp_path):
    (tmp_path / "renders").mkdir()
    monkeypatch.setattr(server.bridge, "directory", tmp_path, raising=False)

    def fake_call(cmd, **kw):
        if cmd == "get_track_details":
            return {"name": kw["track"], "number": {"Bass": 2, "Keys": 5}[kw["track"]]}
        if cmd == "render_stems":
            stems = []
            for name, number in (("Keys", 5), ("Bass", 2)):
                f = tmp_path / "renders" / f"r_{number}.wav"
                sf.write(str(f), np.full((100, 2), 0.1 * number, dtype=np.float32), FS)
                stems.append({"track": {"number": number, "name": name}, "file": str(f)})
            return {"stems": stems, "files": [s["file"] for s in stems]}
        raise AssertionError(cmd)

    monkeypatch.setattr(server, "call", fake_call)
    out = batch.render_group(["Bass", "Keys"], 1, 3)
    assert out["Bass"][0, 0] == pytest.approx(0.2, abs=1e-3) and out["Keys"][0, 0] == pytest.approx(0.5, abs=1e-3)
    assert not list((tmp_path / "renders").glob("*.wav"))       # cleaned up


def _mix(seconds=40, seed=0):
    rng = np.random.default_rng(seed)
    beat = int(FS * 0.5)
    n = int(FS * seconds)
    x = np.zeros(n)
    t = np.arange(beat) / FS
    for i in range(n // beat):
        x[i * beat:(i + 1) * beat] += 0.5 * np.sin(2 * np.pi * 55 * t) * np.exp(-t * 20)
    x += 0.05 * np.sin(2 * np.pi * 220 * np.arange(n) / FS) + rng.normal(0, 0.01, n)
    return np.stack([x, x * 0.97], axis=1)


def test_the_limiter_model_plans_a_target_and_respects_the_cap():
    mix = _mix()
    peak = analysis._db(float(abs(mix).max()))
    plan = batch.plan_limiter(mix, FS, -14.0, -1.0, peak - 5.0)
    y = batch.simulate_limiter(mix, FS, plan["threshold"], -1.0, plan["fader"])
    assert analysis.loudness(y, FS)["integrated_lufs"] == pytest.approx(-14.0, abs=0.3)
    assert not plan["capped"]
    loud = batch.plan_limiter(mix, FS, -6.0, -1.0, peak - 5.0)
    assert loud["capped"] and loud["threshold"] == pytest.approx(peak - 5.0, abs=0.06)
    quiet = batch.plan_limiter(mix * 4, FS, -30.0, -1.0, peak - 5.0)
    assert quiet["fader"] < 0 and quiet["threshold"] == 0.0      # already too loud: the fader comes down


def test_master_to_target_masters_in_two_renders_with_the_model(monkeypatch, tmp_path):
    mix = _mix(50)
    (tmp_path / "renders").mkdir()
    monkeypatch.setattr(server.bridge, "directory", tmp_path, raising=False)
    state = {"threshold": 0.0, "ceiling": -1.0, "fader": 0.0, "on": True, "renders": 0}

    def fake_call(cmd, **kw):
        if cmd == "get_track_details":
            return {"fx": [{"index": 1, "name": "ReaLimit"}]}
        if cmd == "update_fx":
            state["on"] = kw["enabled"]
        elif cmd == "set_fx_parameters":
            for c in kw["changes"]:
                state[c["parameter"].lower()] = c["display_value"]
        elif cmd == "get_fx_parameters":
            return {"parameters": [{"name": "Threshold", "display": f"{state['threshold']}"}]}
        elif cmd == "set_track_properties":
            state["fader"] = kw["volume_db"]
        elif cmd == "describe_track":
            return {"volume_db": state["fader"]}
        elif cmd == "render_audio":
            state["renders"] += 1
            y = (batch.simulate_limiter(mix, FS, state["threshold"], state["ceiling"], state["fader"]) if state["on"]
                 else mix * 10 ** (state["fader"] / 20))
            f = tmp_path / "renders" / f"m{state['renders']}.wav"
            sf.write(str(f), y.astype(np.float32), FS)
            return {"files": [str(f)], "start": {"seconds": 0.0}, "end": {"seconds": 50.0}, "track": "master"}
        return {}

    monkeypatch.setattr(server, "call", fake_call)
    out = server.master_to_target(target_lufs=-14.0, glue=False, force=True)
    assert out["reached"] and out["model"]["renders"] <= 2
    assert state["renders"] <= 3                                  # pre-limiter + at most two checks


def test_mix_spans_share_the_peak_unless_a_part_sits_it_out(monkeypatch):
    from creaper import mix_tools
    monkeypatch.setattr(mix_tools, "call", lambda cmd, **kw: (
        {"tempo_bpm": 120, "time_signature": "4/4"} if cmd == "get_project_overview"
        else [{"bar": 1 + t / 2.0} for t in kw["times"]]))
    loud = np.r_[np.full(40, 1e-4), np.full(40, 1.0), np.full(40, 1e-4)]      # 0.5 s steps: loud 20-40 s
    pad = np.r_[np.full(80, 1e-4), np.full(40, 0.5)]                          # plays only after the peak
    channels = [{"ref": "D", "name": "Drums", "track": 1, "role": "drums"},
                {"ref": "B", "name": "Bass", "track": 2, "role": "bass"},
                {"ref": "P", "name": "Pad", "track": 3, "role": "pad"}]
    spans = mix_tools._loud_spans(channels, {"D": loud, "B": loud * 0.5, "P": pad}, 0.0)
    assert spans["D"] == spans["B"] == spans["_mix"] and spans["Bass"] == spans["B"]
    assert 2 not in spans and "2" not in spans                  # never by number: a Duck bus shifts them
    assert spans["P"] != spans["_mix"] and spans["P"][0] >= 21           # its own loud part
    assert spans["_drums"] == spans["D"]


def test_saturation_trials_share_their_passes(monkeypatch):
    from creaper import mix_tools
    passes = []

    def render_group(tracks, lo, hi):
        passes.append(list(tracks))
        return {"_fs": FS, **{t: np.stack([drums(2, 0.4, 1)] * 2, axis=1) for t in tracks}}

    monkeypatch.setattr(batch, "render_group", render_group)
    monkeypatch.setattr(mix_tools, "call", lambda cmd, **kw: {"fx": []} if cmd == "get_track_details" else {"index": 4})
    out = mix_tools._add_colour([("Bass", "B"), ("drum bus", "D")], None, None, {"B": (9.0, 25.0), "D": (9.0, 25.0)})
    assert len(out) == 2 and all(p == ["B", "D"] for p in passes)    # every pass renders both
    # Identical dry and wet: no rise at all, so both stop at the hopeless point, together.
    assert len(passes) == 1 + mix_tools.COLOUR_STEPS.index(mix_tools.COLOUR_HOPELESS_AT) + 1
    assert all("skipped" in o for o in out)


# ------------------------------------------------------------- review regressions

def test_nested_hints_put_back_the_outer_one():
    with batch.span_hints({"Drums": (1.0, 9.0)}):
        with batch.span_hints({"Drums": (5.0, 13.0)}):
            assert batch.hinted_span("Drums") == (5.0, 13.0)
        assert batch.hinted_span("Drums") == (1.0, 9.0)
    assert batch.hinted_span("Drums") is None


def test_one_failing_group_keeps_the_others(monkeypatch):
    bench = Bench({"Kick": np.stack([drums(8, 0.6, 1)] * 2, axis=1), "Pad": np.zeros((FS * 16, 2))})
    monkeypatch.setattr(server, "call", bench.call)
    monkeypatch.setattr(batch, "render_group", bench.render_group)
    profile = plugin_profiles.find_profile("ReaComp")
    out = batch.calibrate_many([{"track": "Kick", "fx": 1, "profile": profile, "target": 2.5, "span": (9.0, 17.0)},
                                {"track": "Pad", "fx": 1, "profile": profile, "target": 1.5, "span": (1.0, 9.0)}])
    assert abs(out[0]["loud_part_reduction_db"] - 2.5) <= 0.3
    assert "silent" in out[1]["error"]


def test_the_block_model_measures_loudness_like_the_real_meter():
    mix = _mix(30)
    m = batch.LimiterModel(mix, FS)
    for t in (-2.0, -6.0, -10.0):
        assert m.lufs(t, -1.0) == pytest.approx(analysis.loudness(m.render(t, -1.0), FS)["integrated_lufs"], abs=0.15)
    with pytest.raises(ValueError, match="silent"):
        batch.plan_limiter(np.zeros((FS * 10, 2)), FS, -14, -1.0, -6.0)
    assert batch.plan_limiter(mix * 8, FS, -9, -1.0, 6.0)["capped"] is False   # a cap above 0: no limiting asked


def test_the_true_peak_fix_never_raises_the_ceiling_the_model_lowered(monkeypatch, tmp_path):
    mix = _mix(40)
    (tmp_path / "renders").mkdir()
    monkeypatch.setattr(server.bridge, "directory", tmp_path, raising=False)
    state = {"threshold": 0.0, "ceiling": -1.0, "fader": 0.0, "on": True, "renders": 0, "ceilings": []}

    def fake_call(cmd, **kw):
        if cmd == "get_track_details":
            return {"fx": [{"index": 1, "name": "ReaLimit"}]}
        if cmd == "update_fx":
            state["on"] = kw["enabled"]
        elif cmd == "set_fx_parameters":
            for c in kw["changes"]:
                state[c["parameter"].lower()] = c["display_value"]
                if c["parameter"] == "Ceiling":
                    state["ceilings"].append(c["display_value"])
        elif cmd == "get_fx_parameters":
            return {"parameters": [{"name": "Threshold", "display": f"{state['threshold']}"}]}
        elif cmd == "set_track_properties":
            state["fader"] = kw["volume_db"]
        elif cmd == "describe_track":
            return {"volume_db": state["fader"]}
        elif cmd == "render_audio":
            state["renders"] += 1
            y = (batch.simulate_limiter(mix, FS, state["threshold"], state["ceiling"], state["fader"]) * 1.03
                 if state["on"] else mix * 10 ** (state["fader"] / 20))       # the real limiter overshoots a little more
            f = tmp_path / "renders" / f"m{state['renders']}.wav"
            sf.write(str(f), y.astype(np.float32), FS, subtype="FLOAT")
            return {"files": [str(f)], "start": {"seconds": 0.0}, "end": {"seconds": 40.0}, "track": "master"}
        return {}

    monkeypatch.setattr(server, "call", fake_call)
    server.master_to_target(target_lufs=-12.0, glue=False, force=True, ceiling_dbtp=-1.0, clip=False)
    after_model = state["ceilings"][1] if len(state["ceilings"]) > 1 else state["ceilings"][0]
    assert all(b <= a + 1e-9 for a, b in zip(state["ceilings"][1:], state["ceilings"][2:]))   # only ever down
    assert state["ceiling"] <= after_model


class NoisyBench(Bench):
    """A bench where one track renders differently every time (a synth with free-running
    oscillators): each render of 'Pad' gets a fresh random level wobble per 50 ms window."""

    def __init__(self, tracks, noisy=("Pad",)):
        super().__init__(tracks)
        self.noisy, self.rng = noisy, np.random.default_rng(7)

    def render_group(self, tracks, lo, hi):
        out = super().render_group(tracks, lo, hi)
        n = int(FS * 0.05)
        for t in tracks:
            if t in self.noisy:
                x = out[t]
                wobble = 10 ** (self.rng.normal(0, 2.0, x.shape[0] // n + 1) / 20)
                out[t] = x * np.repeat(wobble, n)[: x.shape[0], None]
        return out


def test_a_track_that_renders_differently_each_time_is_set_by_the_model():
    pad = np.stack([drums(8, 0.5, 4)] * 2, axis=1)
    bench = NoisyBench({"Kick": np.stack([drums(8, 0.6, 1)] * 2, axis=1), "Pad": pad})
    import pytest as _pt
    mp = _pt.MonkeyPatch()
    mp.setattr(server, "call", bench.call)
    mp.setattr(batch, "render_group", bench.render_group)
    try:
        profile = plugin_profiles.find_profile("ReaComp")
        out = batch.calibrate_many([{"track": "Kick", "fx": 1, "profile": profile, "target": 2.5, "span": (9.0, 17.0)},
                                    {"track": "Pad", "fx": 1, "profile": profile, "target": 1.5, "span": (9.0, 17.0)}])
    finally:
        mp.undo()
    kick, pad_result = out
    assert abs(kick["loud_part_reduction_db"] - 2.5) <= 0.3 and "repeat_noise_db" not in kick
    assert pad_result["repeat_noise_db"] > batch.NOISE_FLOOR_DB and pad_result["method"].startswith("the compressor model")
    assert pad_result["value"] == pad_result["predicted_start"] == bench.threshold["Pad"]   # the model's threshold stands
    assert pad_result["calibration"][-1]["unreadable"] and "differ from each other" in pad_result["note"]
    # Three passes for the pad (dry, one wet, the noise check), not seven of walking the threshold at random.
    assert sum("Pad" in p for p in bench.passes) == 3


def test_a_readable_track_that_starts_off_target_still_searches():
    bench = NoisyBench({"Snare": np.stack([drums(8, 0.3, 2)] * 2, axis=1)}, noisy=())
    import pytest as _pt
    mp = _pt.MonkeyPatch()
    mp.setattr(server, "call", bench.call)
    mp.setattr(batch, "render_group", bench.render_group)
    mp.setattr(batch, "predict_threshold", lambda *a, **k: -40.0)       # a bad first guess
    try:
        profile = plugin_profiles.find_profile("ReaComp")
        out = batch.calibrate_many([{"track": "Snare", "fx": 1, "profile": profile, "target": 2.0, "span": (9.0, 17.0)}])[0]
    finally:
        mp.undo()
    assert abs(out["loud_part_reduction_db"] - 2.0) <= 0.3 and out["value"] != -40.0
    assert "repeat_noise_db" not in out and len(bench.passes) >= 4          # dry, wet, the noise check, the search
