"""Gain reduction measured from dry and processed renders, and compressor calibration."""

import numpy as np
import pytest

from creaper import server  # noqa: F401  (import order: server first)
from creaper import analysis, plugin_profiles

FS = 22050


def drums(seconds=16.0, level=0.5, seed=0):
    """Hits every quarter note at 120 BPM: a fast attack and a short decay."""
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    out = np.zeros(n)
    hit = int(0.15 * FS)
    t = np.arange(hit) / FS
    shape = np.exp(-t * 25)
    for start in range(0, n - hit, int(0.5 * FS)):
        out[start:start + hit] += level * shape * rng.standard_normal(hit)
    return out


def compress(x, threshold_db, ratio=4.0, makeup_db=0.0, window=0.01):
    """A simple feed-forward compressor on 10 ms blocks."""
    n = int(window * FS)
    y = x.copy()
    for a in range(0, len(x), n):
        block = x[a:a + n]
        level = 10 * np.log10(np.mean(block ** 2) + 1e-20)
        over = max(0.0, level - threshold_db)
        y[a:a + n] = block * 10 ** ((-over * (1 - 1 / ratio) + makeup_db) / 20)
    return y


def test_gain_reduction_reads_what_a_compressor_takes_off():
    dry = drums()
    light, heavy = compress(dry, -14), compress(dry, -24)
    gl, gh = analysis.gain_reduction(dry, light, FS), analysis.gain_reduction(dry, heavy, FS)
    assert 1 < gl["gr_db_p95"] < gh["gr_db_p95"]
    assert analysis.gain_reduction(dry, dry, FS)["gr_db_p95"] == pytest.approx(0, abs=0.1)


def test_make_up_gain_and_level_dont_count():
    dry = drums()
    louder = dry * 10 ** (6 / 20)
    assert analysis.gain_reduction(dry, louder, FS)["gr_db_p95"] == pytest.approx(0, abs=0.1)
    squeezed = compress(dry, -20, makeup_db=8)
    assert analysis.gain_reduction(dry, squeezed, FS)["gr_db_p95"] > 3


def test_a_quiet_intro_evened_out_isnt_compression():
    # The old measure (the drop in loud-vs-quiet spread over the whole range) read a
    # process that only lifts a quiet intro as heavy compression.
    intro, main = drums(8, level=0.05, seed=1), drums(8, level=0.5, seed=2)
    dry = np.concatenate([intro, main])
    lifted = np.concatenate([intro * 10 ** (10 / 20), main])
    old = analysis.envelope_range(dry[:, None], FS) - analysis.envelope_range(lifted[:, None], FS)
    assert old > 3
    # Calibration reads the gain reduction on the song's loudest stretch, where nothing
    # was taken off. (Within one render, "the intro went up" and "the rest came down"
    # look alike, which is why it measures there and not across sections.)
    t0 = analysis.loudest_span(dry, FS, 6.0)
    a, b = int(t0 * FS), int((t0 + 6.0) * FS)
    assert t0 >= 8 and analysis.gain_reduction(dry[a:b], lifted[a:b], FS)["gr_db_p95"] < 0.5


def test_alignment_finds_a_plugin_delay():
    dry = drums()
    late = np.concatenate([np.zeros(64), compress(dry, -14)])[: dry.size]
    gr = analysis.gain_reduction(dry, late, FS)
    assert gr["lag_samples"] == 64 and 1 < gr["gr_db_p95"] < 8


def test_loudest_span_finds_the_loud_section():
    mono = np.concatenate([drums(20, 0.05, 1), drums(10, 0.5, 2), drums(20, 0.05, 3)])
    assert analysis.loudest_span(mono, FS, 8.0) == pytest.approx(21, abs=2)


def test_calibration_converges_on_a_simulated_compressor(monkeypatch):
    profile = plugin_profiles.find_profile("ReaComp")
    state = {"threshold": 0.0, "enabled": True}
    dry = np.concatenate([drums(20, 0.05, 1), drums(40, 0.5, 2)])  # a quiet intro, then 20 loud bars
    renders = []

    def fake_render(track, start_bar, end_bar):
        renders.append((start_bar, end_bar))
        a, b = (int((start_bar - 1) * 2 * FS), int((end_bar - 1) * 2 * FS)) if start_bar else (0, dry.size)
        part = dry[a:b]
        out = compress(part, state["threshold"]) if state["enabled"] else part
        return np.stack([out, out], axis=1), FS, {"start": {"seconds": a / FS}}

    def fake_call(cmd, **kw):
        if cmd == "update_fx":
            state["enabled"] = kw["enabled"]
            return {}
        if cmd == "get_fx_parameters":
            return {"parameters": [{"name": profile.drive, "display": f"{state['threshold']:.1f}"}]}
        if cmd == "set_fx_parameters":
            state["threshold"] = kw["changes"][0]["display_value"]
            return {}
        if cmd == "get_project_overview":
            return {"tempo_bpm": 120, "time_signature": "4/4"}
        if cmd == "time_to_positions":
            return [{"bar": 1 + t / 2.0} for t in kw["times"]]
        raise AssertionError(cmd)

    monkeypatch.setattr(server, "_render_array", fake_render)
    monkeypatch.setattr(server, "call", fake_call)
    out = server._calibrate_compressor("Drums", 1, profile, 3.0, None, None)
    assert abs(out["loud_part_reduction_db"] - 3.0) <= 0.5, out
    assert out["measured_on_bars"][0] >= 10         # the loud part (from bar 11), not the quiet intro
    steps = [s["drive"] for s in out["calibration"]]
    assert all(abs(b - a) <= server.MAX_DRIVE_STEP_DB * 8 + 1e-6 for a, b in zip(steps, steps[1:]))


def _fake_master(monkeypatch, pre_peak=-1.0, pre_lufs=-18.0):
    """A master whose loudness follows ReaLimit's threshold (gain into its ceiling)."""
    state = {"threshold": 0.0, "fader": 0.0, "limiter_on": True}

    def fake_call(cmd, **kw):
        if cmd == "get_track_details":
            return {"fx": [{"index": 1, "name": "ReaLimit"}]}
        if cmd == "get_fx_parameters":
            return {"parameters": [{"display": f"{state['threshold']:.1f}"}]}
        if cmd == "set_fx_parameters":
            for c in kw["changes"]:
                if c["parameter"] == "Threshold":
                    state["threshold"] = c["display_value"]
            return {}
        if cmd == "update_fx":
            state["limiter_on"] = kw["enabled"]
            return {}
        if cmd == "set_track_properties":
            state["fader"] = kw.get("volume_db", state["fader"])
            return {}
        if cmd == "describe_track":
            return {"volume_db": state["fader"]}
        return {}

    def fake_analyze(**kw):
        if not state["limiter_on"]:
            return {"loudness": {"integrated_lufs": pre_lufs, "loudness_range_lu": 6},
                    "levels": {"sample_peak_dbfs": pre_peak, "true_peak_dbtp": pre_peak}, "duration_seconds": 30}
        gain = -state["threshold"]
        return {"loudness": {"integrated_lufs": round(pre_lufs + 0.9 * gain + state["fader"], 2), "loudness_range_lu": 6},
                "levels": {"sample_peak_dbfs": -1.0, "true_peak_dbtp": -1.0}, "duration_seconds": 30}

    monkeypatch.setattr(server, "call", fake_call)
    monkeypatch.setattr(server, "analyze_audio", fake_analyze)
    monkeypatch.setattr(server, "_peakiest_parts", lambda *a, **k: [{"track": "Snare", "peak_to_loudness_db": 19.0}])
    return state


def test_the_limiter_stops_at_its_cap_and_says_what_the_mix_needs(monkeypatch):
    state = _fake_master(monkeypatch)
    out = server.master_to_target(target_lufs=-9.0, glue=False, force=True)
    assert out["limiter_gr_db"] <= server.LIMITER_MAX_GR_DB + 0.01
    assert state["threshold"] >= -1.0 - server.LIMITER_MAX_GR_DB - 0.01
    assert out["reached"] is False and "needs density" in out["limited_at"]
    assert out["peakiest_parts"][0]["track"] == "Snare"
    assert out["mix_peak_to_loudness_db"] == 17.0


def test_a_reachable_target_isnt_capped(monkeypatch):
    _fake_master(monkeypatch, pre_peak=-1.0, pre_lufs=-16.0)
    out = server.master_to_target(target_lufs=-14.0, glue=False, force=True)
    assert out["reached"] is True and "limited_at" not in out and out["limiter_gr_db"] < 5


def test_a_sparse_mix_aims_for_the_quiet_end_of_the_style(monkeypatch):
    from creaper import styles
    _fake_master(monkeypatch, pre_peak=-1.0, pre_lufs=-20.0)
    out = server.master_to_target(style="house", glue=False, force=True)
    assert out["target_lufs"] == styles.find_style("house").lufs[0]
    assert "quiet end" in out["target_note"]


def test_dynamics_stage_compresses_peaky_parts_and_clips_drums(monkeypatch):
    from creaper import mix_tools
    calls, faders = [], {"Drums": -3.0, "Pad": 0.0}

    def fake_call(cmd, **kw):
        calls.append((cmd, kw))
        if cmd == "add_fx":
            return {"index": 2 if kw["name"] == "ReaComp" else 3, "name": "VST: ReaComp (Cockos)" if kw["name"] == "ReaComp" else kw["name"]}
        if cmd == "get_track_details":
            return {"volume_db": faders[kw["track"]]}
        if cmd == "set_track_properties":
            faders[kw["track"]] = kw["volume_db"]
        return {}

    monkeypatch.setattr(mix_tools, "call", fake_call)
    monkeypatch.setattr(server, "_calibrate_compressor", lambda *a, **k: {"loud_part_reduction_db": 2.4, "value": -18.0})
    monkeypatch.setattr(server, "analyze_audio", lambda **kw: {"levels": {"sample_peak_dbfs": -9.0}})
    # Peaky by peak-to-loudness (peak minus loudness while playing), as the master sees them.
    channels = [{"name": "Drums", "ref": "Drums", "role": "drums", "level": -20, "peak_db": -4},     # 16 dB
                {"name": "Pad", "ref": "Pad", "role": "pad", "level": -20, "peak_db": -8},          # 12 dB
                {"name": "Bass", "ref": "Bass", "role": "bass", "level": -14, "peak_db": 0},        # the plan compresses it
                {"name": "Lead", "ref": "Lead", "role": "lead", "level": -15, "peak_db": -8}]       # 7 dB: not peaky
    actions = [{"ref": "Bass", "compress": {"ratio": 4}}]
    done = mix_tools._shape_dynamics(channels, actions, "electronic dance", None, None)
    assert [d["track"] for d in done] == ["Drums", "Pad"]
    drums = done[0]
    # Pre-fader peak -6 (-9 at a -3 fader): a 8.5 dB boost puts it 2.5 over the knee; the fader takes it back.
    assert drums["soft_clip"] == {"boost_db": 8.5, "peaks_rounded_db": 2.5, "fader_db": -11.5}
    assert drums["compressor"]["ratio"] == 4 and done[1]["compressor"]["ratio"] == 2
    assert "soft_clip" not in done[1]


@pytest.mark.parametrize("installed", [True, False])
def test_dynamics_stage_puts_bus_force_on_the_drums_when_installed(monkeypatch, installed):
    from creaper import mix_tools
    calls = []

    def fake_call(cmd, **kw):
        calls.append((cmd, kw))
        if cmd == "add_fx":
            if kw["name"] == "Bus FORCE" and not installed:
                raise RuntimeError("no FX named 'Bus FORCE'")
            return {"index": 2, "name": f"VST3: {kw['name']} (Arturia)" if kw["name"] == "Bus FORCE"
                    else "VST: ReaComp (Cockos)"}
        if cmd == "get_track_details":
            return {"volume_db": 0.0}
        return {}

    monkeypatch.setattr(mix_tools, "call", fake_call)
    monkeypatch.setattr(server, "_calibrate_compressor", lambda *a, **k: {"loud_part_reduction_db": 2.4, "value": -18.0})
    monkeypatch.setattr(server, "analyze_audio", lambda **kw: {"levels": {"sample_peak_dbfs": -9.0}})
    channels = [{"name": "Drums", "ref": "Drums", "role": "drums", "level": -20, "peak_db": -4},
                {"name": "Pad", "ref": "Pad", "role": "pad", "level": -20, "peak_db": -8}]
    done = mix_tools._shape_dynamics(channels, [], "rock", None, None)
    sets = {kw["track"]: [c["parameter"] for c in kw["changes"]] for c, kw in calls if c == "set_fx_parameters"
            and any("Attack" in ch["parameter"] for ch in kw["changes"])}
    if installed:
        assert "Bus FORCE" in done[0]["compressor"]["plugin"] and "Comp Force" in sets["Drums"]
        assert "Comp Path Mute" in sets["Drums"]                  # its compressor path opened first
    else:
        assert "ReaComp" in done[0]["compressor"]["plugin"] and "Ratio" in sets["Drums"]
    assert "ReaComp" in done[1]["compressor"]["plugin"]           # keys and pads keep ReaComp


def test_genres_that_breathe_keep_their_dynamics():
    from creaper import mix_tools
    out = mix_tools._shape_dynamics([{"name": "Drums", "ref": "D", "role": "drums", "level": -20, "peak_db": -2}],
                                    [], "classical", None, None)
    assert "keeps its dynamics" in out[0]["skipped"]


@pytest.mark.parametrize("source, filtered", [("Drums", True), ("Kick", False)])
def test_sidechain_filters_a_kit_trigger_and_measures_the_ducking(monkeypatch, source, filtered):
    sets, calibrated = [], {}

    def fake_call(cmd, **kw):
        if cmd == "setup_sidechain":
            return {"target": {"number": 2}, "is_reacomp": True, "fx_index": 1}
        if cmd == "describe_track":
            return {"name": source, "volume_db": 0.0}
        if cmd == "set_fx_parameters":
            sets.extend(kw["changes"])
        return {}

    def fake_calibrate(track, fx, profile, target, start, end, passes=7, sidechain=False):
        calibrated.update(track=track, target=target, sidechain=sidechain)
        return {"value": -31.0, "loud_part_reduction_db": 4.6}

    monkeypatch.setattr(server, "call", fake_call)
    monkeypatch.setattr(server, "analyze_audio", lambda **a: {"levels": {"sample_peak_dbfs": -8.0}})
    monkeypatch.setattr(server, "_calibrate_compressor", fake_calibrate)
    out = server.setup_sidechain(source=source, target="Bass", depth="medium")
    assert any(c["parameter"] == "Lowpass" for c in sets) is filtered
    assert calibrated == {"track": 2, "target": server.DUCK_DEPTH_DB["medium"], "sidechain": True}
    assert out["measured_ducking_db"] == 4.6 and out["threshold_db"] == -31.0



def test_the_cap_holds_on_a_rerun_with_the_master_fader_down(monkeypatch):
    state = _fake_master(monkeypatch)
    state["fader"] = -4.0                 # an earlier pass turned the master down
    orig = server.analyze_audio

    def after_the_fader(**kw):  # the measurement sits after the master fader
        m = orig(**kw)
        if not state["limiter_on"]:
            m["levels"] = {k: v + state["fader"] for k, v in m["levels"].items()}
            m["loudness"]["integrated_lufs"] += state["fader"]
        return m
    monkeypatch.setattr(server, "analyze_audio", after_the_fader)
    out = server.master_to_target(target_lufs=-9.0, glue=False, force=True)
    # Pre-limiter peak -1 (not -5): the threshold mustn't go under -6.
    assert state["threshold"] >= -1.0 - server.LIMITER_MAX_GR_DB - 0.01
    assert out["limiter_gr_db"] <= server.LIMITER_MAX_GR_DB + 0.01


def test_steady_compression_isnt_hidden_as_make_up():
    t = np.arange(8 * FS) / FS
    pad = 0.5 * np.sin(2 * np.pi * 220 * t)
    squashed = compress(pad, -25, ratio=2)     # every window over the threshold
    assert analysis.gain_reduction(pad, squashed, FS)["gr_db_p95"] > 5


def test_a_quiet_kit_gets_no_pointless_clipper(monkeypatch):
    from creaper import mix_tools
    added = []
    monkeypatch.setattr(mix_tools, "call", lambda cmd, **kw: added.append(cmd) or {"volume_db": 0.0})
    monkeypatch.setattr(server, "analyze_audio", lambda **kw: {"levels": {"sample_peak_dbfs": -14.0}})
    out = mix_tools._soft_clip("Drums", None, None)
    assert "too far to round" in out["skipped"] and "add_fx" not in added


def test_colour_keeps_a_gentle_overshoot():
    from creaper import mix_tools
    assert mix_tools.choose_colour([{"amount": 5, "rise_db": 6.0, "crest_drop_db": 0.2}])["amount"] == 5
