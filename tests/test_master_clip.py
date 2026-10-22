"""The master's soft clipper: when ReaLimit alone (5 dB of gain reduction at most)
can't reach a loud target, the mix's peaks are rounded before it, as little as gets
there, so dense genres reach their loudness instead of stopping 2-3 LU short."""

import numpy as np
import pytest
import soundfile as sf

from creaper import server  # noqa: F401  (import order: server first)
from creaper import analysis, batch
from creaper.mix_tools import SOFT_CLIPPER

FS = 22050


def _peaky_mix(seconds=40, seed=0):
    """Sharp kicks over a quiet bed: peaks far over the loudness, as a dense synth mix
    reaches the master."""
    rng = np.random.default_rng(seed)
    beat = int(FS * 0.5)
    n = int(FS * seconds)
    x = np.zeros(n)
    t = np.arange(beat) / FS
    for i in range(n // beat):
        x[i * beat:(i + 1) * beat] += 0.8 * np.sin(2 * np.pi * 55 * t) * np.exp(-t * 40)
    x += 0.04 * np.sin(2 * np.pi * 220 * np.arange(n) / FS) + rng.normal(0, 0.01, n)
    return np.stack([x, x * 0.97], axis=1)


def _db(x):
    return 20 * np.log10(abs(x))


def test_soft_clip_follows_reapers_js_transfer():
    # Unity, Boost 0, Brickwall 0: untouched 9 dB under the brickwall, 0 dBFS rounded to
    # about -1.9 dB, +3 dB to about -0.4, and nothing over the brickwall.
    for level_db, expect in ((-12.0, -12.0), (0.0, -1.88), (3.0, -0.40), (6.0, 0.0)):
        y = batch.soft_clip(np.array([10 ** (level_db / 20), -10 ** (level_db / 20)]), 0.0)
        assert _db(y[0]) == pytest.approx(expect, abs=0.05), level_db
        assert y[1] == pytest.approx(-y[0])      # the sign is kept
    boosted = batch.soft_clip(np.array([10 ** (-3 / 20)]), 3.0)[0]       # Boost 3 puts -3 dB at 0
    assert _db(boosted) == pytest.approx(-1.88, abs=0.05)
    capped = batch.soft_clip(np.array([2.0]), 0.0, brickwall_db=-1.0)[0]
    assert _db(capped) == pytest.approx(-1.0, abs=0.05)
    assert batch.soft_clip(np.zeros(4), 6.0).tolist() == [0.0] * 4


def test_plan_master_clip_adds_only_the_clipping_the_target_needs():
    mix = _peaky_mix()
    peak = analysis._db(float(abs(mix).max()))
    alone = batch.plan_limiter(mix, FS, -6.0, -1.0, peak - 5.0)        # the limiter at its cap
    assert alone["capped"]
    reachable = alone["lufs"] - 3.0
    assert batch.plan_master_clip(mix, FS, reachable, -1.0, 5.0) is None    # no clipping when none is needed
    plan = batch.plan_master_clip(mix, FS, alone["lufs"] + 1.0, -1.0, 5.0)
    assert plan is not None and not plan["capped"] and plan["over_db"] <= batch.MASTER_CLIP_OVER_DB
    assert 0 < plan["peak_shaved_db"] <= plan["over_db"] + 2.0            # the knee rounds a little under the brickwall too
    assert plan["peak_db"] == pytest.approx(analysis._db(float(abs(plan["audio"]).max())), abs=0.01)
    # The clipped mix with the limiter at its cap reaches what the limiter alone couldn't.
    limited = batch.plan_limiter(plan["audio"], FS, alone["lufs"] + 1.0, -1.0, plan["peak_db"] - 5.0)
    y = batch.simulate_limiter(plan["audio"], FS, limited["threshold"], -1.0, limited["fader"])
    assert analysis.loudness(y, FS)["integrated_lufs"] == pytest.approx(alone["lufs"] + 1.0, abs=0.3)
    hopeless = batch.plan_master_clip(mix, FS, alone["lufs"] + 20.0, -1.0, 5.0)
    assert hopeless["capped"] and hopeless["over_db"] == batch.MASTER_CLIP_OVER_DB


def _master_with_renders(monkeypatch, tmp_path, mix, fx_names=("ReaLimit",)):
    """A master whose renders go through the fake chain: soft clipper (when added and
    on) then ReaLimit (when on) then the fader, as REAPER would."""
    (tmp_path / "renders").mkdir(parents=True)
    monkeypatch.setattr(server.bridge, "directory", tmp_path, raising=False)
    state = {"fx": [{"index": i + 1, "name": n} for i, n in enumerate(fx_names)],
             "threshold": 0.0, "ceiling": -1.0, "fader": 0.0, "limiter_on": True,
             "clip_on": False, "boost": 0.0, "brickwall": None, "renders": 0, "added": []}

    def name_of(fx):
        return next(f["name"] for f in state["fx"] if f["index"] == fx)

    def fake_call(cmd, **kw):
        if cmd == "get_track_details":
            return {"fx": [dict(f) for f in state["fx"]]}
        if cmd == "add_fx":
            at = kw.get("position") or len(state["fx"]) + 1
            state["fx"].insert(at - 1, {"index": at, "name": kw["name"]})
            for i, f in enumerate(state["fx"]):
                f["index"] = i + 1
            state["added"].append((kw["name"], at))
            state["clip_on"] = False
            return {"index": at, "name": kw["name"]}
        if cmd == "update_fx":
            if "ReaLimit" in name_of(kw["fx"]):
                state["limiter_on"] = kw["enabled"]
            else:
                state["clip_on"] = kw["enabled"]
        elif cmd == "set_fx_parameters":
            for c in kw["changes"]:
                if c["parameter"] == "Boost (dB)":
                    state["boost"] = c["display_value"]
                elif c["parameter"] == "Output Brickwall (dB)":
                    state["brickwall"] = c["display_value"]
                else:
                    state[c["parameter"].lower()] = c["display_value"]
        elif cmd == "get_fx_parameters":
            return {"parameters": [{"name": "Threshold", "display": f"{state['threshold']}"}]}
        elif cmd == "set_track_properties":
            state["fader"] = kw["volume_db"]
        elif cmd == "describe_track":
            return {"volume_db": state["fader"]}
        elif cmd == "render_audio":
            state["renders"] += 1
            y = mix
            if state["clip_on"]:
                y = batch.soft_clip(y, state["boost"], state["brickwall"] or 0.0)
            y = (batch.simulate_limiter(y, FS, state["threshold"], state["ceiling"], state["fader"])
                 if state["limiter_on"] else y * 10 ** (state["fader"] / 20))
            f = tmp_path / "renders" / f"m{state['renders']}.wav"
            sf.write(str(f), y.astype(np.float32), FS)
            return {"files": [str(f)], "start": {"seconds": 0.0}, "end": {"seconds": mix.shape[0] / FS},
                    "track": "master"}
        return {}

    monkeypatch.setattr(server, "call", fake_call)
    monkeypatch.setattr(server, "_peakiest_parts", lambda *a, **k: [{"track": "Drums", "peak_to_loudness_db": 14.0}])
    return state


def test_master_to_target_soft_clips_when_the_limiter_alone_cant(monkeypatch, tmp_path):
    mix = _peaky_mix(24)
    peak = analysis._db(float(abs(mix).max()))
    alone = batch.plan_limiter(mix, FS, -6.0, -1.0, peak - 5.0)["lufs"]       # where the old master stopped
    state = _master_with_renders(monkeypatch, tmp_path, mix)
    out = server.master_to_target(target_lufs=round(alone + 1.0, 1), glue=False, force=True)
    assert out["reached"], out
    assert "limited_at" not in out
    assert state["added"] == [(SOFT_CLIPPER, 1)]                 # before the limiter, which moved to 2
    assert [f["name"] for f in state["fx"]] == [SOFT_CLIPPER, "ReaLimit"] == out["chain"]
    assert state["clip_on"] and state["brickwall"] == 0 and state["boost"] == out["clipper"]["boost_db"] > 0
    assert out["clipper"]["peaks_over_brickwall_db"] <= batch.MASTER_CLIP_OVER_DB
    assert out["limiter_gr_db"] <= server.LIMITER_MAX_GR_DB + 0.01
    # The limiter's threshold is measured against the clipped peak, not the raw one.
    assert state["threshold"] >= (peak + state["boost"] - out["clipper"]["peak_shaved_db"]) - server.LIMITER_MAX_GR_DB - 0.05
    assert out["true_peak_ok"] and out["peak_to_loudness_db"] >= 7


def test_a_hopeless_target_clips_its_most_and_says_so(monkeypatch, tmp_path):
    mix = _peaky_mix(24)
    state = _master_with_renders(monkeypatch, tmp_path, mix)
    out = server.master_to_target(target_lufs=-4.0, glue=False, force=True)
    assert not out["reached"] and state["clip_on"]
    assert out["clipper"]["peaks_over_brickwall_db"] == batch.MASTER_CLIP_OVER_DB
    assert "soft-clipped" in out["limited_at"] and "needs density" in out["limited_at"]
    assert "limiters on single tracks" in out["limited_at"]
    assert out["limiter_gr_db"] == pytest.approx(server.LIMITER_MAX_GR_DB, abs=0.1)


def test_no_clipper_for_a_reachable_target_or_when_turned_off(monkeypatch, tmp_path):
    mix = _peaky_mix(24)
    peak = analysis._db(float(abs(mix).max()))
    alone = batch.plan_limiter(mix, FS, -6.0, -1.0, peak - 5.0)["lufs"]
    state = _master_with_renders(monkeypatch, tmp_path, mix)
    out = server.master_to_target(target_lufs=round(alone - 2.0, 1), glue=False, force=True)
    assert out["reached"] and state["added"] == [] and "clipper" not in out
    state = _master_with_renders(monkeypatch, tmp_path / "off", mix)
    out = server.master_to_target(target_lufs=-4.0, glue=False, force=True, clip=False)
    assert not out["reached"] and state["added"] == [] and "clipper" not in out
    assert "soft-clipped" not in out["limited_at"] and "more than 5 dB of limiting" in out["limited_at"]


def test_styles_that_should_breathe_keep_the_clipper_off(monkeypatch, tmp_path):
    mix = _peaky_mix(24)
    state = _master_with_renders(monkeypatch, tmp_path, mix)
    out = server.master_to_target(target_lufs=-4.0, style="jazz", glue=False, force=True)
    assert state["added"] == [] and "clipper" not in out and not out["reached"]


def test_an_earlier_clipper_is_bypassed_for_the_measurement_and_reused(monkeypatch, tmp_path):
    mix = _peaky_mix(24)
    peak = analysis._db(float(abs(mix).max()))
    alone = batch.plan_limiter(mix, FS, -6.0, -1.0, peak - 5.0)["lufs"]
    state = _master_with_renders(monkeypatch, tmp_path, mix, fx_names=(SOFT_CLIPPER, "ReaLimit"))
    state["clip_on"], state["boost"] = True, 7.0           # left loud by an earlier run
    out = server.master_to_target(target_lufs=round(alone + 1.0, 1), glue=False, force=True)
    assert out["reached"] and state["added"] == []         # reused, not added again
    assert out["clipper"]["boost_db"] == state["boost"] < 7.0   # set for this mix, not left at 7
    # And when the limiter alone gets there, the old clipper stays off.
    state = _master_with_renders(monkeypatch, tmp_path / "quiet", mix, fx_names=(SOFT_CLIPPER, "ReaLimit"))
    state["clip_on"], state["boost"] = True, 7.0
    out = server.master_to_target(target_lufs=round(alone - 2.0, 1), glue=False, force=True)
    assert out["reached"] and not state["clip_on"] and out["clipper"]["bypassed"]


def test_peakiest_parts_leave_out_risers_and_impacts(monkeypatch):
    from creaper import ear_tools

    table = {"tracks": {"Transitions": {"peak_dbfs": -6.0, "lufs_playing": -30.0},
                        "Drums": {"peak_dbfs": -3.0, "lufs_playing": -15.0},
                        "Riser FX": {"peak_dbfs": -8.0, "lufs_playing": -28.0},
                        "Chords": {"peak_dbfs": -8.0, "lufs_playing": -18.0}}}
    monkeypatch.setattr(ear_tools, "measure_tracks", lambda **k: table)
    rows = server._peakiest_parts(None, None)
    assert [r["track"] for r in rows] == ["Drums", "Chords"]
