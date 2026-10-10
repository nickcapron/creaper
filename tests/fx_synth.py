"""Reference effects in numpy, for testing that pluginscan recognises what an effect does."""

import numpy as np
from scipy import signal

FS = 44100


def stereo(x: np.ndarray, r: np.ndarray | None = None) -> np.ndarray:
    return np.stack([x, x if r is None else r], axis=1)


def passthrough(x):
    return stereo(x)


def gain(x, db=6.0):
    return stereo(x * 10 ** (db / 20))


def lowpass(x, fc=1500):
    return stereo(signal.sosfilt(signal.butter(4, fc, fs=FS, output="sos"), x))


def highpass(x, fc=300):
    return stereo(signal.sosfilt(signal.butter(4, fc, btype="highpass", fs=FS, output="sos"), x))


def reverb(x, rt=1.8, mix=0.5):
    n = int(rt * FS)
    rng = np.random.default_rng(3)
    t = np.arange(n) / FS
    irl = rng.standard_normal(n) * np.exp(-6.9 * t / rt)
    irr = rng.standard_normal(n) * np.exp(-6.9 * t / rt)
    irl, irr = irl / np.sqrt(np.sum(irl ** 2)), irr / np.sqrt(np.sum(irr ** 2))
    wl = signal.fftconvolve(x, irl)[: len(x)]
    wr = signal.fftconvolve(x, irr)[: len(x)]
    return np.stack([(1 - mix) * x + mix * wl, (1 - mix) * x + mix * wr], axis=1)


def delay(x, ms=375, feedback=0.45, mix=0.5):
    d = int(ms / 1000 * FS)
    y = x.copy()
    out = np.zeros_like(x)
    for k in range(1, 6):
        out[d * k:] += x[: len(x) - d * k] * feedback ** (k - 1)
    return stereo((1 - mix) * y + mix * out)


def compressor(x, threshold_db=-20.0, ratio=4.0, attack=0.005, release=0.1):
    env = np.zeros_like(x)
    a_att, a_rel = np.exp(-1 / (attack * FS)), np.exp(-1 / (release * FS))
    e = 0.0
    for i, v in enumerate(np.abs(x)):
        coeff = a_att if v > e else a_rel
        e = coeff * e + (1 - coeff) * v
        env[i] = e
    level = 20 * np.log10(env * np.sqrt(2) + 1e-9)
    over = np.maximum(0, level - threshold_db)
    g = 10 ** (-(over - over / ratio) / 20)
    return stereo(x * g)


def limiter(x):
    return compressor(x, threshold_db=-30.0, ratio=50.0, attack=0.001)


def gate(x, threshold_db=-40.0):
    env = np.convolve(np.abs(x), np.ones(441) / 441, mode="same")
    return stereo(np.where(20 * np.log10(env + 1e-9) > threshold_db, x, x * 0.001))


def saturation(x, drive=3.0):
    return stereo(np.tanh(drive * x) / np.tanh(drive))


def distortion(x, drive=30.0):
    return stereo(np.clip(drive * x, -0.5, 0.5))


def tremolo(x, rate=5.0, depth=0.6):
    t = np.arange(len(x)) / FS
    return stereo(x * (1 - depth / 2 + depth / 2 * np.sin(2 * np.pi * rate * t)))


def chorus(x, rate=0.8, depth_ms=3.0, base_ms=12.0):
    t = np.arange(len(x)) / FS
    d = (base_ms + depth_ms * np.sin(2 * np.pi * rate * t)) / 1000 * FS
    idx = np.arange(len(x)) - d
    wet = np.interp(idx, np.arange(len(x)), x, left=0)
    return np.stack([0.5 * x + 0.5 * wet, 0.5 * x - 0.5 * wet], axis=1)


def pitch_up_octave(x):
    # Crude: double the speed, then pad (only the steady sine matters for the test).
    y = x[::2]
    y = np.concatenate([np.repeat(y, 1), np.zeros(len(x) - len(y))])
    return stereo(np.concatenate([x[: len(x) // 2], y[len(x) // 2 - len(x) // 4:]])[: len(x)])


def widener(x, ms=15):
    d = int(ms / 1000 * FS)
    r = np.concatenate([np.zeros(d), x[:-d]])
    return stereo(x, r)


def latency(x, ms=10):
    d = int(ms / 1000 * FS)
    return stereo(np.concatenate([np.zeros(d), x[:-d]]))
