"""The checks export_mix and master_to_target refuse on unless forced."""

import numpy as np
import pytest
import soundfile as sf

from creaper import server  # noqa: F401  (import order: server first)
from creaper import analysis, export_tools, styles

FS = 22050


def test_clipped_runs_count_flat_tops_not_limited_peaks():
    t = np.arange(FS) / FS
    clipped = np.clip(1.5 * np.sin(2 * np.pi * 100 * t), -1, 1)[:, None]
    assert analysis.clipped_runs(clipped) >= 100          # every half cycle is flat-topped
    smooth = (0.98 * np.sin(2 * np.pi * 100 * t))[:, None]
    assert analysis.clipped_runs(smooth) == 0             # peaks touch the top for a sample, not a run
    assert analysis.clipped_runs(0.5 * clipped) == 0      # flat but far below full scale: not clipping
    for hz in (30, 60):  # a clean deep bass spends several samples near its top, all different
        t44 = np.arange(2 * 44100) / 44100
        assert analysis.clipped_runs(np.sin(2 * np.pi * hz * t44)[:, None]) == 0, hz
        assert analysis.clipped_runs(np.clip(1.2 * np.sin(2 * np.pi * hz * t44), -1, 1)[:, None]) > 0, hz


def song(lra=8.0, harsh=4.0, clipped=0, seconds=180.0):
    return {"duration_seconds": seconds, "loudness": {"loudness_range_lu": lra},
            "levels": {"clipped_runs": clipped}, "tone_over_time": {"harsh_2_5k_pct_p95": harsh}}


def test_gate_problems():
    house, ambient = styles.find_style("house"), styles.find_style("ambient")
    assert styles.gate_problems(song(), house) == []
    assert "clips" in styles.gate_problems(song(clipped=12), house)[0]
    assert "one level" in styles.gate_problems(song(lra=1.2), house)[0]
    assert styles.gate_problems(song(lra=1.2), ambient) == []                    # flat is the point there
    assert styles.gate_problems(song(lra=1.2), house, whole_song=False) == []    # a region isn't a song
    assert styles.gate_problems(song(lra=1.2, seconds=20), house) == []          # nor is a stinger
    limit = styles.harsh_limit(house.tone, gate=True)
    assert styles.gate_problems(song(harsh=limit - 0.5), house) == []
    assert "piercing" in styles.gate_problems(song(harsh=limit + 0.5), house)[0]
    # Without a style, the neutral limit.
    assert styles.gate_problems(song(harsh=styles.harsh_limit("neutral", gate=True) + 1))
    # A bright stinger or a region is meant to be what it is: only clipping counts.
    assert styles.gate_problems(song(harsh=40, seconds=8), house) == []
    assert styles.gate_problems(song(harsh=40), house, whole_song=False) == []
    assert styles.gate_problems(song(harsh=40, clipped=3, seconds=8), house)


def _fake_render(monkeypatch, tmp_path, audio):
    renders = tmp_path / "renders"
    renders.mkdir(exist_ok=True)
    monkeypatch.setattr(export_tools.bridge, "directory", tmp_path)

    def fake_call(cmd, **kw):
        if cmd == "render_audio":
            f = renders / "r.wav"
            sf.write(str(f), audio, FS, subtype="FLOAT")
            return {"files": [str(f)]}
        raise AssertionError(cmd)
    monkeypatch.setattr(export_tools, "call", fake_call)
    monkeypatch.setattr(export_tools, "_project_info", lambda: {"path": None, "name": "song"})
    return renders


def test_export_mix_refuses_a_clipping_mix_unless_forced(monkeypatch, tmp_path):
    t = np.arange(4 * FS) / FS
    x = np.clip(1.4 * np.sin(2 * np.pi * 220 * t), -1, 1)
    renders = _fake_render(monkeypatch, tmp_path, np.stack([x, x], axis=1))
    out_dir = tmp_path / "out"
    with pytest.raises(ValueError, match="not exported: it clips"):
        export_tools.export_mix(folder=str(out_dir))
    assert not list(renders.iterdir()) and not out_dir.exists()
    done = export_tools.export_mix(folder=str(out_dir), force=True)
    assert (out_dir / "song.wav").exists()
    assert any("force=True despite: it clips" in n for n in done["notes"])


def test_master_to_target_refuses_before_changing_anything(monkeypatch):
    changed = []

    def fake_call(cmd, **kw):
        changed.append((cmd, kw.get("enabled")))
        return {"fx": []} if cmd == "get_track_details" else {}
    monkeypatch.setattr(server, "call", fake_call)
    monkeypatch.setattr(server, "analyze_audio", lambda **a: song(lra=1.0))
    with pytest.raises(ValueError, match="nothing was changed"):
        server.master_to_target(style="house")
    assert {cmd for cmd, _ in changed} <= {"get_track_details", "render_audio"}   # looked and listened, changed nothing


def test_master_to_target_checks_the_mix_with_an_earlier_limiter_bypassed(monkeypatch):
    log, state = [], {"limiter_on": True}

    def fake_call(cmd, **kw):
        if cmd == "get_track_details":
            return {"fx": [{"index": 1, "name": "ReaComp"}, {"index": 2, "name": "ReaLimit"},
                           {"index": 3, "name": "EQ (bypassed)"}]}
        if cmd == "update_fx":
            log.append((kw["fx"], kw["enabled"]))
            if kw["fx"] == 2:
                state["limiter_on"] = kw["enabled"]
        return {}

    def fake_measure(**a):
        # Through the limiter the song is flat; the mix itself moves.
        return song(lra=1.0 if state["limiter_on"] else 7.0)
    monkeypatch.setattr(server, "call", fake_call)
    monkeypatch.setattr(server, "analyze_audio", fake_measure)
    with pytest.raises(Exception) as caught:
        server.master_to_target(style="house")
    assert "not mastered" not in str(caught.value)   # it got past the check (then the fake bridge ran out)
    assert log[:4] == [(1, False), (2, False), (1, True), (2, True)]
