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
        assert cmd == "render_audio" and kw["start_seconds"] == 0.0 and kw["end_seconds"] == 6.0
        return {"files": [str(renders / "r.wav")]}
    monkeypatch.setattr(x, "call", fake_call)
    monkeypatch.setattr(x, "_check_renders", lambda files: None)
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
