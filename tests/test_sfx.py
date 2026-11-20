"""Sound effects: one file per region, trimmed, normalised, mono or stereo, loops seamless."""
import numpy as np
import soundfile as sf

from creaper import sfx_tools as x

FS = 44100


def hit(seconds=0.3, delay=0.05, fs=FS):
    t = np.arange(int(seconds * fs)) / fs
    body = np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.04)
    return np.concatenate([np.zeros(int(delay * fs)), body * 0.5])[:, None]


def test_head_is_trimmed_to_within_a_millisecond():
    trimmed, cut = x.trim_head(hit(delay=0.05), FS)
    assert 48 <= cut <= 50
    onset = np.nonzero(np.abs(trimmed[:, 0]) > 0.5 * 10 ** (-50 / 20))[0][0]
    assert onset <= 0.0012 * FS and abs(trimmed[0, 0]) < 1e-3


def test_tail_cut_off_is_noticed_and_silence_dropped():
    sound = hit(0.3, delay=0)
    assert not x.tail_state(np.concatenate([sound, np.zeros((FS // 2, 1))]))["cut_off"]
    assert x.tail_state(sound[: int(0.03 * FS)])["cut_off"]
    assert len(x.trim_tail(np.concatenate([sound, np.zeros((FS, 1))]))) < len(sound) + 10


def test_peak_mono_and_dc():
    stereo = np.stack([np.full(1000, 0.1), np.full(1000, 0.3)], axis=1) + np.sin(np.arange(1000) / 5)[:, None] * 0.2
    mono = x.to_channels(stereo, "mono")
    assert mono.shape == (1000, 1)
    assert abs(x.remove_dc(mono).mean()) < 1e-12
    norm, _ = x.normalize_peak(mono, -1.0)
    assert abs(20 * np.log10(np.abs(norm).max()) + 1.0) < 1e-9


def test_loops_wrap_without_a_jump():
    rng = np.random.default_rng(0)
    noise = np.convolve(rng.standard_normal(5 * FS), np.ones(30) / 30, mode="same")[:, None] * 0.3
    length, xf = 3 * FS, FS // 2
    loop = x.make_loop(noise, length, xf)
    assert len(loop) == length
    assert x.loop_seam_db(loop) < 6
    tone = np.sin(np.arange(5 * FS) * 2 * np.pi * 101.3 / FS)[:, None]
    assert x.loop_seam_db(tone[:length]) > 20                 # a raw cut mid-cycle clicks
    assert x.loop_seam_db(x.make_loop(tone, length, xf)) < 6


def test_export_regions_writes_one_file_per_region(tmp_path, monkeypatch):
    renders = tmp_path / "renders"
    renders.mkdir()
    out = tmp_path / "sfx"
    # A render from 0 s: shot_01 at 0-0.5 s, shot_02 at 1-1.5 s (cut off), crowd_bed 2-6 s (stereo loop).
    total = np.zeros((int(7.5 * FS), 2))
    total[int(0.02 * FS): int(0.02 * FS) + len(hit(0.3, 0))] += hit(0.3, 0) * 0.5
    total[int(1.0 * FS): int(1.0 * FS) + int(0.6 * FS), 0] += 0.4 * np.sin(np.arange(int(0.6 * FS)) / 7)
    rng = np.random.default_rng(1)
    total[int(2 * FS):, :] += np.convolve(rng.standard_normal(len(total) - 2 * FS), np.ones(20) / 20, mode="same")[:, None] * 0.2
    sf.write(str(renders / "r.wav"), total, FS, subtype="FLOAT")
    regions = [{"name": "shot_01", "start": {"seconds": 0.0}, "end": {"seconds": 0.5}},
               {"name": "shot_02", "start": {"seconds": 1.0}, "end": {"seconds": 1.5}},
               {"name": "crowd_bed", "start": {"seconds": 2.0}, "end": {"seconds": 6.0}}]

    def fake_call(cmd, **kw):
        if cmd == "get_project_overview":
            return {"regions": regions}
        if cmd == "project_paths":
            return {}
        assert cmd == "render_audio" and kw["start_seconds"] == 0.0 and kw["end_seconds"] == 6.0
        return {"files": [str(renders / "r.wav")]}
    monkeypatch.setattr(x, "call", fake_call)
    monkeypatch.setattr(x.export_tools, "_check_renders", lambda files: None)
    r = x.export_regions(folder=str(out), stereo=["crowd_*"], loops=["crowd_bed*"])
    by = {f["file"]: f for f in r["files"]}
    one, _ = sf.read(str(out / "shot_01.wav"), always_2d=True)
    bed, _ = sf.read(str(out / "crowd_bed.wav"), always_2d=True)
    assert one.shape[1] == 1 and bed.shape[1] == 2
    assert sf.info(str(out / "shot_01.wav")).subtype == "PCM_24"
    assert abs(by["shot_01.wav"]["peak_dbfs"] + 1.0) < 0.05 and 18 <= by["shot_01.wav"]["head_trimmed_ms"] <= 20
    assert by["crowd_bed.wav"]["loop_length_s"] == 4.0 and by["crowd_bed.wav"]["seam_db"] < 6
    assert by["shot_02.wav"].get("tail_cut_off") and any("shot_02" in p for p in r["problems"])


def test_a_lingering_offset_and_a_minus_100_db_floor_still_trim():
    """A low sine's DC residue, and a generator fading to -100 dB instead of silence,
    kept near-silent tails in exported one-shots."""
    sound = hit(0.2, delay=0)
    residue = np.concatenate([sound, np.full((FS, 1), 2e-4)])             # an offset left after the sound
    assert len(x.trim_tail(x.remove_dc(residue, FS))) < len(sound) + FS // 4
    hiss = np.concatenate([sound, 10 ** (-100 / 20) * np.random.default_rng(0).standard_normal((FS, 1))])
    assert len(x.trim_tail(hiss)) <= len(sound) + 50


def recorded(sound_at=1.0, seconds=3.0, hiss_dbfs=-90.0, level=0.1):
    """A synth recorded through an interface: a hit with hiss before, under and after it."""
    audio = 10 ** (hiss_dbfs / 20) / 3 * np.random.default_rng(3).standard_normal((int(seconds * FS), 1))
    body = hit(0.3, delay=0) * 2 * level
    audio[int(sound_at * FS): int(sound_at * FS) + len(body)] += body
    return audio


def test_a_recorded_sound_ends_where_it_sinks_into_the_hiss():
    """Live 2026-11-16, microKORG prints: hiss at -86 dBFS under sounds peaking at -28,
    so the tail never fell 80 dB and a 0.1 s blip kept a second of hiss."""
    audio = recorded()
    noise = x.noise_floor_db(audio, FS)
    assert -95 < noise < -85
    assert x.noise_floor_db(np.concatenate([hit(), np.zeros((FS, 1))]), FS) is None     # a plugin: silence, no hiss
    assert x.noise_floor_db(hit(2.0, delay=0)[: FS // 2], FS) is None                   # no gap: that's the sound
    plain = x.trim_tail(x.trim_head(audio, FS)[0])
    assert len(plain) > 1.9 * FS                                                         # what it did before
    sound, cut = x.trim_head(audio, FS, noise_db=noise)
    sound = x.trim_tail(sound, noise_db=noise, fs=FS)
    assert 995 <= cut <= 1000 and 0.15 * FS < len(sound) < 0.4 * FS
    assert abs(sound[-1, 0]) < 1e-9                                                      # faded, no tick
    assert not x.tail_state(audio, noise)["cut_off"]
    assert x.tail_state(audio[: int(1.03 * FS)], noise)["cut_off"]                       # still caught mid-sound


def test_export_regions_trims_recorded_sounds_and_names_a_hissy_one(tmp_path, monkeypatch):
    renders = tmp_path / "renders"
    renders.mkdir()
    total = recorded(sound_at=0.5, seconds=6.0)
    quiet = hit(0.3, delay=0) * 2 * 0.002                    # peaks 37 dB over the hiss
    total[int(3.5 * FS): int(3.5 * FS) + len(quiet)] += quiet
    sf.write(str(renders / "r.wav"), np.repeat(total, 2, axis=1), FS, subtype="FLOAT")
    regions = [{"name": "blip", "start": {"seconds": 0.0}, "end": {"seconds": 2.5}},
               {"name": "faint", "start": {"seconds": 3.0}, "end": {"seconds": 5.5}}]
    monkeypatch.setattr(x, "call", lambda cmd, **kw: {"get_project_overview": {"regions": regions}, "project_paths": {},
                                                      "render_audio": {"files": [str(renders / "r.wav")]}}[cmd])
    monkeypatch.setattr(x.export_tools, "_check_renders", lambda files: None)
    r = x.export_regions(folder=str(tmp_path / "sfx"))
    by = {f["file"]: f for f in r["files"]}
    assert -95 < r["recording_hiss_dbfs"] < -85
    assert by["blip.wav"]["length_s"] < 0.4 and 495 <= by["blip.wav"]["head_trimmed_ms"] <= 500
    assert by["blip.wav"]["hiss_db_below_peak"] > 60 and not by["blip.wav"].get("tail_cut_off")
    assert [p for p in r["problems"] if p.startswith("faint: recorded quietly")]
    assert not any(p.startswith("blip") for p in r["problems"])


def test_regions_that_would_share_a_file_are_refused(tmp_path, monkeypatch):
    # "shot/01" and "shot 01" both become "shot 01.wav": one silently overwrote the other.
    import pytest

    regions = [{"name": "shot/01", "start": {"seconds": 0.0}, "end": {"seconds": 0.5}},
               {"name": "shot 01", "start": {"seconds": 1.0}, "end": {"seconds": 1.5}}]
    monkeypatch.setattr(x, "call", lambda cmd, **kw: {"regions": regions})
    with pytest.raises(ValueError, match="same file"):
        x.export_regions(folder=str(tmp_path))
