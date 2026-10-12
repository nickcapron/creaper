"""The measurements that stand in for listening."""
import asyncio
import struct
import zlib

import numpy as np
import pytest

from creaper import perception

FS = 16000


def _speechlike(seconds=3.0, seed=0):
    """Amplitude-modulated harmonic bursts with changing formants: enough like speech
    for band envelopes to carry 'words'."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * FS)) / FS
    out = np.zeros_like(t)
    for start in np.arange(0, seconds - 0.3, 0.3):
        a, b = int(start * FS), int((start + 0.25) * FS)
        f0, formant = rng.uniform(100, 200), rng.uniform(400, 2500)
        seg_t = t[a:b] - start
        tone = sum(np.sin(2 * np.pi * f0 * k * seg_t) * np.exp(-((f0 * k - formant) / 600) ** 2) for k in range(1, 40))
        out[a:b] = tone * np.hanning(b - a)
    return out


def test_intelligibility_falls_as_noise_rises():
    clean = _speechlike()
    rng = np.random.default_rng(1)
    scores = []
    for snr in (30, 5, -5, -15):
        noise = rng.standard_normal(len(clean))
        noise *= np.sqrt(np.mean(clean ** 2) / np.mean(noise ** 2)) / 10 ** (snr / 20)
        scores.append(perception.intelligibility(clean, clean + noise, FS))
    assert perception.intelligibility(clean, clean, FS) == pytest.approx(1.0, abs=1e-6)
    assert scores == sorted(scores, reverse=True) and scores[0] > 0.9 and scores[-1] < 0.7
    assert perception.intelligibility(clean[:1000], clean[:1000], FS) is None   # too short to judge


def test_note_pitches_finds_a_detuned_note():
    fs = 44100
    t = np.arange(int(1.0 * fs)) / fs
    def tone(hz):
        return sum(np.sin(2 * np.pi * hz * k * t[: fs // 2]) / k for k in range(1, 6))
    audio = np.concatenate([tone(220.0), tone(220.0 * 2 ** (30 / 1200))])   # A3, then A3 30 cents sharp
    got = perception.note_pitches(audio, fs, [{"start": 0.0, "end": 0.5, "pitch": 57},
                                              {"start": 0.5, "end": 1.0, "pitch": 57}])
    assert abs(got[0]["cents"]) <= 3 and 26 <= got[1]["cents"] <= 34


def test_spectrogram_png_is_a_valid_image():
    png = perception.spectrogram_png(_speechlike(), FS, lines=[1.0], width=300, height=100)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    w, h = struct.unpack(">II", png[16:24])
    assert (w, h) == (300, 100)
    idat = png[png.index(b"IDAT") + 4: png.index(b"IEND") - 8]
    assert len(zlib.decompress(idat)) == h * (1 + w * 3)


def test_show_spectrogram_returns_a_picture_to_claude(monkeypatch):
    from creaper import ear_tools, server
    audio = np.stack([_speechlike()] * 2, axis=1)
    monkeypatch.setattr(ear_tools, "_render", lambda *a: (audio, FS, {
        "track": "master", "start": {"seconds": 0.0, "bar": 1}, "end": {"seconds": 3.0, "bar": 3}}))
    monkeypatch.setattr(ear_tools, "call", lambda cmd, **kw: {"regions": [
        {"name": "Drop", "start": {"seconds": 1.5, "bar": 2}}], "markers": []})
    result = asyncio.run(server.mcp.call_tool("show_spectrogram", {}))
    blocks = result if isinstance(result, list) else getattr(result, "content", result)
    if isinstance(blocks, tuple):
        blocks = blocks[0]
    kinds = [getattr(b, "type", None) for b in blocks]
    assert "image" in kinds and "text" in kinds
    text = next(b.text for b in blocks if getattr(b, "type", None) == "text")
    assert "Drop" in text


def _tone(seconds, fs=FS):
    t = np.arange(int(seconds * fs)) / fs
    return 0.3 * np.sin(2 * np.pi * 220 * t)


def test_ending_profile_tells_a_fade_a_silence_and_a_cut_apart():
    steady = perception.ending_profile(_tone(16), FS)
    assert steady["trailing_silence_s"] == 0 and abs(steady["end_vs_loudest_db"]) < 1 and steady["abrupt"]
    faded = _tone(16) * np.concatenate([np.ones(10 * FS), np.linspace(1, 0.02, 6 * FS)])
    assert perception.ending_profile(faded, FS)["end_vs_loudest_db"] < -6
    long_fade = _tone(16) * np.concatenate([np.ones(8 * FS), np.linspace(1, 0.3, 8 * FS)])   # like REAPER's 8 s fade
    assert perception.ending_profile(long_fade, FS)["end_vs_loudest_db"] < -6
    gap = perception.ending_profile(np.concatenate([_tone(14), np.zeros(2 * FS)]), FS)
    assert 1.9 <= gap["trailing_silence_s"] <= 2.1
    t = np.arange(16 * FS) / FS
    dying = _tone(16) * np.exp(-np.maximum(0, t - 8) * 1.5)
    assert not perception.ending_profile(dying, FS)["abrupt"]
