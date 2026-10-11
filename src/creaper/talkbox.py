"""Talk box: a synth shaped by speech, the way a talk box puts a synth through the
player's mouth (Zapp, Chromeo, Daft Punk's "Around the World" leads).

For every short frame, the speech's spectral envelope (its formants: the mouth shape,
from a smoothed cepstrum) is imposed on a sawtooth playing the melody. Where the speech
is noisy (s, t, f, sh) noise takes the saw's place, so consonants come through: this is
what makes a talk box far clearer than a band vocoder.
"""

from __future__ import annotations

import numpy as np
from scipy import signal

RATE = 44100
FRAME = 1024
HOP = 256
LIFTER_S = 0.0015   # cepstral cutoff: keeps the formants, drops the speaking pitch's harmonics


def _resample(x: np.ndarray, fs: int, to: int = RATE) -> np.ndarray:
    if fs == to:
        return x
    g = np.gcd(fs, to)
    return signal.resample_poly(x, to // g, fs // g)


def saw(pitches: list[tuple[float, float]], seconds: float, fs: int = RATE, glide: float = 0.02) -> np.ndarray:
    """A band-limited sawtooth following (time in s, MIDI pitch) steps, gliding briefly
    between notes."""
    n = max(1, int(round(seconds * fs)))
    t = np.arange(n) / fs
    midi = np.full(n, pitches[0][1], dtype=float)
    for start, pitch in pitches[1:]:
        midi[t >= start] = pitch
    if glide > 0:
        k = max(1, int(glide * fs))
        midi = np.convolve(np.pad(midi, (k, 0), mode="edge"), np.ones(k) / k, mode="valid")[:n]
    freq = 440.0 * 2 ** ((midi - 69) / 12)
    phase = np.cumsum(freq / fs) % 1.0
    out = 2 * phase - 1
    # PolyBLEP: smooth each wrap so the saw doesn't alias.
    dt = freq / fs
    a = phase < dt
    x = phase[a] / dt[a]
    out[a] -= x + x - x * x - 1
    b = phase > 1 - dt
    x = (phase[b] - 1) / dt[b]
    out[b] -= x * x + x + x + 1
    return out


def _envelope(mag: np.ndarray, fs: int) -> np.ndarray:
    """Smoothed spectral envelope of each STFT frame (columns) via the cepstrum."""
    log = np.log(mag + 1e-9)
    cep = np.fft.irfft(log, axis=0)
    keep = max(4, int(LIFTER_S * fs))
    cep[keep:-keep] = 0
    return np.exp(np.fft.rfft(cep, axis=0).real[: mag.shape[0]])


def cross_synthesize(speech: np.ndarray, fs: int, pitches: list[tuple[float, float]],
                     noise_mix: float = 1.0, seed: int = 0) -> np.ndarray:
    """The talk box: `speech` (mono, any rate) shapes a saw playing `pitches`.
    Returns mono audio at 44.1 kHz, the same length as the speech."""
    x = _resample(np.asarray(speech, dtype=float), fs)
    if len(x) < FRAME:
        x = np.pad(x, (0, FRAME - len(x)))
    seconds = len(x) / RATE
    carrier = saw(pitches, seconds)
    noise = np.random.default_rng(seed).standard_normal(len(x)) * 0.5
    kw = dict(fs=RATE, nperseg=FRAME, noverlap=FRAME - HOP, boundary="even")
    _, _, S = signal.stft(x, **kw)
    _, _, C = signal.stft(carrier, **kw)
    _, _, N = signal.stft(noise, **kw)
    mag = np.abs(S)
    env = _envelope(mag, RATE)
    # Whiten the sources so only the speech's envelope colours the result.
    Cw = C / (_envelope(np.abs(C), RATE) + 1e-9)
    Nw = N / (_envelope(np.abs(N), RATE) + 1e-9)
    # How noisy each speech frame is (spectral flatness above 1 kHz): consonants.
    freqs = np.fft.rfftfreq(FRAME, 1 / RATE)
    band = (freqs > 1000) & (freqs < 10000)
    power = mag[band] ** 2 + 1e-12
    flatness = np.exp(np.mean(np.log(power), axis=0)) / np.mean(power, axis=0)
    w = np.clip((flatness - 0.08) / 0.25, 0, 1) * noise_mix
    out = env * ((1 - w) * Cw + w * Nw)
    _, y = signal.istft(out, fs=RATE, nperseg=FRAME, noverlap=FRAME - HOP, boundary=True)
    y = y[: len(x)]
    peak = float(np.max(np.abs(y))) if y.size else 0.0
    return y * (10 ** (-3 / 20) / peak) if peak > 0 else y
