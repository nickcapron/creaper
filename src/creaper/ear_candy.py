"""Transition sounds made from scratch: risers, reverse swells, impacts and
downlifters. Synthesised from noise and sine sweeps, so they're original (no samples,
no licences) and exactly as long as the bars they fill.

Every function returns stereo float audio at `fs` (frames x 2), peaking at `peak_db`."""

from __future__ import annotations

import numpy as np
from scipy import signal

FS = 44100


def _normalise(audio: np.ndarray, peak_db: float) -> np.ndarray:
    peak = float(np.max(np.abs(audio))) or 1.0
    return audio * (10 ** (peak_db / 20) / peak)


def _shaped_noise(seconds: float, centre_hz: np.ndarray | None, width_oct: float, fs: int, seed: int,
                  bright_tilt: float = 0.0) -> np.ndarray:
    """Stereo noise whose spectrum is a band around centre_hz(t) (one value per STFT
    frame), or tilted brighter (bright_tilt dB/octave) when centre_hz is None."""
    rng = np.random.default_rng(seed)
    n = max(1, int(seconds * fs))
    out = np.zeros((n, 2))
    for ch in range(2):  # independent noise per side: a wide, natural stereo image
        noise = rng.standard_normal(n + 4096)
        f, _, z = signal.stft(noise, fs=fs, nperseg=2048, noverlap=1536)
        frames = z.shape[1]
        logf = np.log2(np.maximum(f, 20.0))
        if centre_hz is not None:
            centres = np.interp(np.linspace(0, 1, frames), np.linspace(0, 1, len(centre_hz)), np.log2(centre_hz))
            mask = np.exp(-0.5 * ((logf[:, None] - centres[None, :]) / width_oct) ** 2)
        else:
            mask = np.repeat((10 ** (bright_tilt * (logf - 10) / 20))[:, None], frames, axis=1)
        _, shaped = signal.istft(z * mask, fs=fs, nperseg=2048, noverlap=1536)
        out[:, ch] = shaped[:n]
    return out


def riser(seconds: float, fs: int = FS, peak_db: float = -6.0, seed: int = 1, tone: bool = True) -> np.ndarray:
    """Noise sweeping up from 300 Hz to 9 kHz and swelling to full level right at the
    end (the downbeat it leads into), with a rising tone underneath when tone=True."""
    n = max(1, int(seconds * fs))
    frames = max(2, n // 512)
    centres = 300 * (9000 / 300) ** (np.linspace(0, 1, frames) ** 1.6)
    audio = _shaped_noise(seconds, centres, 0.9, fs, seed)
    t = np.linspace(0, 1, n)
    audio *= (t ** 2.2)[:, None]
    if tone:
        freq = 180 * (1400 / 180) ** (t ** 1.5)
        phase = 2 * np.pi * np.cumsum(freq) / fs
        sweep = (np.sin(phase) + 0.3 * np.sin(2 * phase)) * (t ** 3) * 0.35
        audio += np.stack([sweep, sweep], axis=1) * np.max(np.abs(audio))
    return _normalise(audio, peak_db)


def downlifter(seconds: float, fs: int = FS, peak_db: float = -8.0, seed: int = 2) -> np.ndarray:
    """A riser played backwards: starts bright and loud at the downbeat and falls away,
    for a drop into a quieter section."""
    return _normalise(riser(seconds, fs, 0.0, seed, tone=True)[::-1].copy(), peak_db)


def reverse_swell(seconds: float, fs: int = FS, peak_db: float = -8.0, seed: int = 3) -> np.ndarray:
    """A bright, cymbal-like wash played backwards: it swells out of nothing and stops
    on the downbeat (the classic reverse-cymbal suck-in)."""
    n = max(1, int(seconds * fs))
    wash = _shaped_noise(seconds, None, 0.0, fs, seed, bright_tilt=3.0)
    decay = np.exp(-np.linspace(0, 1, n) * 5.5)
    wash *= decay[:, None]
    hp = signal.butter(2, 2500, btype="highpass", fs=fs, output="sos")
    wash = signal.sosfilt(hp, wash, axis=0)
    return _normalise(wash[::-1].copy(), peak_db)


def impact(seconds: float = 2.5, fs: int = FS, peak_db: float = -3.0, seed: int = 4) -> np.ndarray:
    """A downbeat hit: a sub drop (70 Hz falling to 35 Hz), a short noise crack and a
    darker tail that dies away like a big room."""
    n = max(1, int(seconds * fs))
    t = np.arange(n) / fs
    freq = 35 + 35 * np.exp(-t * 6)
    sub = np.sin(2 * np.pi * np.cumsum(freq) / fs) * np.exp(-t * 2.2)
    crack = _shaped_noise(seconds, None, 0.0, fs, seed, bright_tilt=-1.5)
    crack *= np.exp(-t * 28)[:, None]
    tail = _shaped_noise(seconds, None, 0.0, fs, seed + 1, bright_tilt=-4.0)
    tail *= (np.exp(-t * 2.8) * 0.35)[:, None]
    lp = signal.butter(2, 3000, btype="lowpass", fs=fs, output="sos")
    tail = signal.sosfilt(lp, tail, axis=0)
    audio = np.stack([sub, sub], axis=1) * 1.0 + crack * 0.6 + tail
    fade = np.ones(n)
    k = min(n, int(0.05 * fs))
    fade[-k:] = np.linspace(1, 0, k)  # no click if the tail is still sounding at the end
    return _normalise(audio * fade[:, None], peak_db)
