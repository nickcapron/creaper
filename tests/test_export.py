import numpy as np
import soundfile as sf

from creaper import export_tools as E

FS = 48000


def _tone(tmp_path, db=-12.0, seconds=2.0):
    t = np.arange(int(seconds * FS)) / FS
    x = 10 ** (db / 20) * np.sqrt(2) * np.sin(2 * np.pi * 440 * t)
    src = tmp_path / "render.wav"
    sf.write(str(src), np.stack([x, x], axis=1).astype(np.float32), FS, subtype="FLOAT")
    return src


def test_formats(tmp_path):
    src = _tone(tmp_path)
    for fmt, bits in (("wav", 24), ("wav", 16), ("flac", 24), ("mp3", 24), ("ogg", 24)):
        dest = tmp_path / f"out_{fmt}_{bits}{E.EXTENSIONS[fmt]}"
        r = E.convert(src, dest, fmt, bits)
        assert dest.exists() and r["clipped_samples"] == 0
        y, fs = sf.read(str(dest), always_2d=True)
        assert fs == FS and y.shape[1] == 2 and abs(len(y) - 2 * FS) < FS * 0.1


def test_resample_gain_and_clipping(tmp_path):
    src = _tone(tmp_path, db=-3.0)
    dest = tmp_path / "loud.wav"
    r = E.convert(src, dest, "wav", 24, sample_rate=44100, gain_db=6.0)
    assert r["sample_rate"] == 44100 and r["clipped_samples"] > 0
    y, fs = sf.read(str(dest))
    assert fs == 44100 and np.max(np.abs(y)) <= 1.0


def test_deliver_hits_loudness_without_breaking_the_ceiling(tmp_path):
    src = _tone(tmp_path, db=-20.0, seconds=6.0)
    out = E._deliver(str(src), tmp_path / "x.wav", "wav", 24, None, target_lufs=-14.0, ceiling_db=-1.0)
    assert abs(out["integrated_lufs"] + 14.0) < 0.3 and out["true_peak_dbtp"] <= -1.0 + 0.05
    out = E._deliver(str(src), tmp_path / "y.wav", "wav", 24, None, target_lufs=-1.0, ceiling_db=-3.0)
    assert out["true_peak_dbtp"] <= -2.95 and "notes" in out


def test_safe_names():
    assert E.safe_name('My: "Song"/v2?') == "My Song v2"
    assert E.safe_name("   ") == "creaper export"


def test_avoids_clipping_by_default(tmp_path):
    src = _tone(tmp_path, db=1.0, seconds=6.0)  # peaks above 0 dBFS
    out = E._deliver(str(src), tmp_path / "z.wav", "wav", 24, None, None, -1.0)
    assert out["true_peak_dbtp"] <= -0.95 and "gain_applied_db" in out
    clipped = E._deliver(str(src), tmp_path / "c.wav", "wav", 24, None, None, -1.0, avoid_clipping=False)
    assert any("clipped" in n for n in clipped["notes"])
