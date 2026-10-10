import numpy as np
import pytest
import soundfile as sf

from creaper import analysis

FS = 48000


def sine(freq, seconds, amplitude=1.0, fs=FS):
    t = np.arange(int(seconds * fs)) / fs
    return amplitude * np.sin(2 * np.pi * freq * t)


def test_k_weighting_matches_bs1770_at_48k():
    shelf, highpass = analysis.k_weighting_sos(48000)
    assert shelf[:3] == pytest.approx([1.53512485958697, -2.69169618940638, 1.19839281085285], abs=1e-9)
    assert shelf[4:] == pytest.approx([-1.69065929318241, 0.73248077421585], abs=1e-9)
    assert highpass[4:] == pytest.approx([-1.99004745483398, 0.99007225036621], abs=1e-9)


def test_full_scale_sine_in_one_channel_is_minus_3_01_lufs():
    # BS.1770: a 0 dBFS 997 Hz sine in one front channel reads -3.01 LKFS.
    left = sine(997, 10)
    audio = np.stack([left, np.zeros_like(left)], axis=1)
    result = analysis.loudness(audio, FS)
    assert result["integrated_lufs"] == pytest.approx(-3.01, abs=0.02)
    # A steady tone has (almost) no loudness range.
    assert result["loudness_range_lu"] == pytest.approx(0, abs=0.1)


def test_loudness_range_of_two_levels():
    loud = sine(1000, 20, 0.5)
    quiet = sine(1000, 20, 0.5 * 10 ** (-10 / 20))
    mono = np.concatenate([loud, quiet])
    result = analysis.loudness(np.stack([mono, mono], axis=1), FS)
    assert result["loudness_range_lu"] == pytest.approx(10, abs=0.5)


def test_true_peak_catches_intersample_overs():
    # A sine at fs/4 with a 45 degree phase only hits 0.707 on the samples.
    n = np.arange(4800)
    fade = np.minimum(1, np.minimum(n, n[::-1]) / 480)
    x = np.sin(2 * np.pi * n / 4 + np.pi / 4) * fade
    assert np.max(np.abs(x)) == pytest.approx(0.7071, abs=1e-3)
    assert analysis.true_peak(x, FS) == pytest.approx(1.0, abs=0.01)


def test_true_peak_has_no_chunk_seam_artifacts():
    # A steady tone processed in many small chunks must read the same as in one.
    n = np.arange(FS)
    x = sine(1000, 1, 0.5) * np.minimum(1, np.minimum(n, n[::-1]) / 480)
    whole = analysis.true_peak(x, FS)
    chunked = analysis.true_peak(x, FS, chunk=997)
    assert whole == pytest.approx(0.5, abs=0.005)
    assert chunked == pytest.approx(whole, abs=1e-4)


def test_analyze_file(tmp_path):
    # Bass in the center, a quieter high tone only on the left.
    low = sine(80, 8, 0.5)
    high = sine(5000, 8, 0.05)
    audio = np.stack([low + high, low], axis=1).astype(np.float32)
    path = tmp_path / "mix.wav"
    sf.write(path, audio, FS, subtype="FLOAT")

    result = analysis.analyze_file(path)
    assert result["duration_seconds"] == 8.0
    assert result["levels"]["sample_peak_dbfs"] == pytest.approx(20 * np.log10(0.55), abs=0.1)
    assert result["levels"]["samples_over_0dbfs"] == 0
    bands = result["spectrum"]["bands"]
    assert bands["bass (60-250 Hz)"]["share_pct"] > 95
    assert result["stereo"]["low_end_correlation_below_150hz"] == pytest.approx(1.0, abs=0.01)
    assert result["stereo"]["left_right_balance_db"] > 0
    assert len(result["short_term_timeline"]) > 0


def test_silence(tmp_path):
    path = tmp_path / "silence.wav"
    sf.write(path, np.zeros((FS, 2), dtype=np.float32), FS, subtype="FLOAT")
    assert analysis.analyze_file(path)["silent"] is True


def test_overs_are_counted(tmp_path):
    path = tmp_path / "hot.wav"
    x = sine(440, 2, 1.5).astype(np.float32)
    sf.write(path, np.stack([x, x], axis=1), FS, subtype="FLOAT")
    result = analysis.analyze_file(path)
    assert result["levels"]["samples_over_0dbfs"] > 0
    assert result["levels"]["sample_peak_dbfs"] == pytest.approx(3.52, abs=0.05)


def test_envelope_range_shrinks_under_compression_and_ignores_level():
    # A loud/quiet alternating tone; "compressed" turns the loud parts down 6 dB.
    t = np.arange(4 * FS) / FS
    loud = (np.floor(t * 2) % 2 == 0)
    gain = np.where(loud, 1.0, 10 ** (-12 / 20))
    tone = 0.5 * gain * np.sin(2 * np.pi * 220 * t)
    squashed = tone * np.where(loud, 10 ** (-6 / 20), 1.0)
    a = analysis.envelope_range(np.stack([tone, tone], axis=1), FS)
    b = analysis.envelope_range(np.stack([squashed, squashed], axis=1), FS)
    assert a == pytest.approx(12, abs=0.5)
    assert a - b == pytest.approx(6, abs=0.5)
    c = analysis.envelope_range(np.stack([tone, tone], axis=1) * 0.25, FS)  # 12 dB quieter, same spread
    assert c == pytest.approx(a, abs=1e-6)
    assert analysis.envelope_range(np.zeros((FS, 2)), FS) is None