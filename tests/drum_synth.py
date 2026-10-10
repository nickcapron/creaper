"""Synthesized drum sounds for testing the listener (no samples needed)."""

import numpy as np
from scipy import signal

FS = 44100


def _env(n: int, decay: float, attack: float = 0.001) -> np.ndarray:
    t = np.arange(n) / FS
    a = np.clip(t / attack, 0, 1)
    return a * np.exp(-t / decay)


def _noise(n: int, lo: float | None, hi: float | None, seed: int) -> np.ndarray:
    x = np.random.default_rng(seed).standard_normal(n)
    if lo and hi:
        sos = signal.butter(4, [lo, hi], btype="bandpass", fs=FS, output="sos")
    elif lo:
        sos = signal.butter(4, lo, btype="highpass", fs=FS, output="sos")
    else:
        sos = signal.butter(4, hi, btype="lowpass", fs=FS, output="sos")
    return signal.sosfilt(sos, x)


def _norm(x: np.ndarray, peak: float = 0.7) -> np.ndarray:
    return x * peak / np.max(np.abs(x))


def kick(length: float = 1.5) -> np.ndarray:
    n = int(length * FS)
    t = np.arange(n) / FS
    freq = 45 + 90 * np.exp(-t / 0.04)
    phase = 2 * np.pi * np.cumsum(freq) / FS
    return _norm(np.sin(phase) * _env(n, 0.25))


def snare(length: float = 1.5) -> np.ndarray:
    n = int(length * FS)
    t = np.arange(n) / FS
    body = 0.5 * np.sin(2 * np.pi * 185 * t) * _env(n, 0.06)
    return _norm(body + _noise(n, 1200, 7000, 1) * _env(n, 0.12))


def clap(length: float = 1.5) -> np.ndarray:
    n = int(length * FS)
    out = np.zeros(n)
    burst = _noise(n, 900, 3500, 2)
    for k, start in enumerate((0, 0.011, 0.022)):
        s = int(start * FS)
        out[s:] += burst[: n - s] * _env(n - s, 0.006) * (1 - 0.1 * k)
    s = int(0.03 * FS)
    out[s:] += burst[: n - s] * _env(n - s, 0.12) * 0.7
    return _norm(out)


def closed_hat(length: float = 1.5) -> np.ndarray:
    n = int(length * FS)
    return _norm(_noise(n, 7000, None, 3) * _env(n, 0.03))


def open_hat(length: float = 1.5) -> np.ndarray:
    n = int(length * FS)
    return _norm(_noise(n, 6500, None, 4) * _env(n, 0.3))


def crash(length: float = 1.5) -> np.ndarray:
    n = int(length * FS)
    return _norm(_noise(n, 3500, None, 5) * _env(n, 1.2))


def tom(freq: float = 140, length: float = 1.5) -> np.ndarray:
    n = int(length * FS)
    t = np.arange(n) / FS
    f = freq * (1 + 0.15 * np.exp(-t / 0.05))
    phase = 2 * np.pi * np.cumsum(f) / FS
    return _norm(np.sin(phase) * _env(n, 0.3) + 0.05 * _noise(n, 300, 2000, 6) * _env(n, 0.05))


def rim(length: float = 1.5) -> np.ndarray:
    n = int(length * FS)
    t = np.arange(n) / FS
    return _norm(_noise(n, 1500, 5000, 7) * _env(n, 0.008) + 0.6 * np.sin(2 * np.pi * 820 * t) * _env(n, 0.012))


def cowbell(length: float = 1.5) -> np.ndarray:
    n = int(length * FS)
    t = np.arange(n) / FS
    x = signal.square(2 * np.pi * 540 * t) + signal.square(2 * np.pi * 800 * t)
    sos = signal.butter(2, [400, 4000], btype="bandpass", fs=FS, output="sos")
    return _norm(signal.sosfilt(sos, x) * _env(n, 0.15))


def shaker(length: float = 1.5) -> np.ndarray:
    n = int(length * FS)
    return _norm(_noise(n, 5000, 14000, 8) * _env(n, 0.07, attack=0.03))


def tone(freq: float, length: float = 2.5, held: float = 1.0) -> np.ndarray:
    n = int(length * FS)
    t = np.arange(n) / FS
    env = np.clip(t / 0.01, 0, 1) * np.where(t < held, 1.0, np.exp(-(t - held) / 0.05))
    return _norm(signal.sawtooth(2 * np.pi * freq * t) * env)


KIT = {"kick": kick, "snare": snare, "clap": clap, "closed hat": closed_hat, "open hat": open_hat,
       "crash": crash, "tom": tom, "rim": rim, "cowbell": cowbell, "shaker": shaker}
