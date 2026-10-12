"""What Claude can't hear, measured: how understandable words are, whether parts are in
tune, and a picture of the sound.

- intelligibility(): STOI (short-time objective intelligibility, Taal et al. 2011), the
  standard measure of how well words survive processing or a mix: the clean speech's
  1/3-octave band envelopes are correlated with the result's over 384 ms windows. As
  measured here on speech in white noise: 0.93 = noise 5 dB under the voice (clear),
  0.875 = noise as loud as the voice (effort), 0.80 = 5 dB over it, 0.72 = 10 dB over it.
- note_pitches(): how far each played or sung note is from where it should be, in cents.
- spectrogram_png(): the sound over time (log frequency, dB colour) with section lines,
  as a PNG Claude can look at.
"""

from __future__ import annotations

import math
import struct
import zlib

import numpy as np
from scipy import signal

from .samplelib import vocal_pitch

# ------------------------------------------------------------ intelligibility

STOI_FS = 10000
STOI_FRAME = 256
STOI_FFT = 512
STOI_BANDS = 15
STOI_MIN_HZ = 150
STOI_SEGMENT = 30     # frames: 384 ms
STOI_BETA = -15.0     # dB: lower signal-to-distortion bound
STOI_RANGE = 40.0     # dB: frames this far below the loudest clean frame are dropped


def _third_octaves() -> np.ndarray:
    freqs = np.linspace(0, STOI_FS / 2, STOI_FFT // 2 + 1)
    centers = STOI_MIN_HZ * 2 ** (np.arange(STOI_BANDS) / 3)
    lo, hi = centers * 2 ** (-1 / 6), centers * 2 ** (1 / 6)
    bands = np.zeros((STOI_BANDS, len(freqs)))
    for i in range(STOI_BANDS):
        bands[i, (freqs >= lo[i]) & (freqs < hi[i])] = 1
    return bands


def _resample(x: np.ndarray, fs: int, to: int) -> np.ndarray:
    if fs == to:
        return np.asarray(x, dtype=float)
    g = math.gcd(int(fs), int(to))
    return signal.resample_poly(np.asarray(x, dtype=float), to // g, int(fs) // g)


def intelligibility(clean: np.ndarray, heard: np.ndarray, fs: int) -> float | None:
    """STOI of `heard` against the `clean` speech it carries (same length and timing,
    mono). None when there's too little speech to judge."""
    x, y = _resample(clean, fs, STOI_FS), _resample(heard, fs, STOI_FS)
    n = min(len(x), len(y))
    x, y = x[:n], y[:n]
    window = np.hanning(STOI_FRAME + 2)[1:-1]
    hop = STOI_FRAME // 2
    starts = range(0, n - STOI_FRAME, hop)
    frames_x = np.array([x[s:s + STOI_FRAME] * window for s in starts])
    frames_y = np.array([y[s:s + STOI_FRAME] * window for s in starts])
    if len(frames_x) < STOI_SEGMENT:
        return None
    energy = 20 * np.log10(np.linalg.norm(frames_x, axis=1) + 1e-12)
    keep = energy > energy.max() - STOI_RANGE
    frames_x, frames_y = frames_x[keep], frames_y[keep]
    if len(frames_x) < STOI_SEGMENT:
        return None
    bands = _third_octaves()
    X = np.sqrt(bands @ (np.abs(np.fft.rfft(frames_x, STOI_FFT, axis=1)) ** 2).T)
    Y = np.sqrt(bands @ (np.abs(np.fft.rfft(frames_y, STOI_FFT, axis=1)) ** 2).T)
    clip = 10 ** (-STOI_BETA / 20)
    scores = []
    for m in range(STOI_SEGMENT, X.shape[1] + 1):
        xs, ys = X[:, m - STOI_SEGMENT:m], Y[:, m - STOI_SEGMENT:m]
        alpha = np.linalg.norm(xs, axis=1, keepdims=True) / (np.linalg.norm(ys, axis=1, keepdims=True) + 1e-12)
        ys = np.minimum(ys * alpha, xs * (1 + clip))
        xs = xs - xs.mean(axis=1, keepdims=True)
        ys = ys - ys.mean(axis=1, keepdims=True)
        denom = np.linalg.norm(xs, axis=1) * np.linalg.norm(ys, axis=1) + 1e-12
        scores.append(np.mean(np.sum(xs * ys, axis=1) / denom))
    return float(np.mean(scores)) if scores else None


def clarity_verdict(score: float | None) -> str:
    if score is None:
        return "too little speech to judge"
    if score >= 0.90:
        return "clear"
    if score >= 0.83:
        return "understandable with effort"
    if score >= 0.76:
        return "hard to follow"
    return "mostly lost"


def robot_clarity_verdict(score: float | None) -> str:
    """For talk box and vocoder vocals, which score lower than plain speech even when
    understood (as with vocoded speech in hearing research): measured here, a talk box
    of clear words on a low melody scores about 0.72-0.78."""
    if score is None:
        return "too little speech to judge"
    if score >= 0.72:
        return "as clear as a talk box gets"
    if score >= 0.64:
        return "a little blurred"
    return "blurred: hard to make out"


def masking_verdict(drop: float) -> str:
    """How much the rest of the mix covers a vocal: the fall in STOI from alone to in the mix."""
    if drop <= 0.03:
        return "the mix isn't covering it"
    if drop <= 0.07:
        return "the mix covers it a little"
    return "the mix is burying it"


# --------------------------------------------------------------------- tuning

def note_pitches(audio: np.ndarray, fs: int, notes: list[dict], min_seconds: float = 0.12) -> list[dict]:
    """For each note (start and end in seconds within `audio`, MIDI pitch), the pitch
    actually sounding and how far off it is in cents, folded into one octave (an
    octave-up sample is in tune). Notes too short or without a clear pitch are skipped."""
    out = []
    for n in notes:
        length = n["end"] - n["start"]
        if length < min_seconds:
            continue
        a = int((n["start"] + min(0.05, length * 0.2)) * fs)
        b = a + int(min(length * 0.6, 0.4) * fs)
        hz, clarity = vocal_pitch(audio[a:b], fs, fmin=40, fmax=2000)
        if not hz or clarity < 0.7:
            continue
        played = 69 + 12 * math.log2(hz / 440)
        cents = ((played - n["pitch"]) * 100 + 600) % 1200 - 600
        out.append({**n, "heard": round(played, 2), "cents": round(cents)})
    return out


def pitch_classes_heard(audio: np.ndarray, fs: int, frame: float = 0.1) -> list[dict]:
    """The pitch of each clearly pitched 100 ms stretch: time (s), MIDI pitch (fractional)."""
    step = int(frame * fs)
    out = []
    for i in range(0, len(audio) - step, step):
        seg = audio[i:i + step]
        if np.sqrt(np.mean(seg ** 2)) < 1e-3:
            continue
        hz, clarity = vocal_pitch(seg, fs, fmin=60, fmax=1500)
        if hz and clarity >= 0.8:
            out.append({"time": round(i / fs, 2), "pitch": round(69 + 12 * math.log2(hz / 440), 2)})
    return out


# ---------------------------------------------------------------- spectrogram

def _colour(v: np.ndarray) -> np.ndarray:
    """0..1 -> RGB, a dark-to-bright 'inferno'-like ramp."""
    stops = np.array([[0, 0, 4], [40, 11, 84], [101, 21, 110], [159, 42, 99], [212, 72, 66],
                      [245, 125, 21], [250, 193, 39], [252, 255, 164]], dtype=float)
    pos = np.clip(v, 0, 1) * (len(stops) - 1)
    i = np.minimum(pos.astype(int), len(stops) - 2)
    t = (pos - i)[..., None]
    return (stops[i] * (1 - t) + stops[i + 1] * t).astype(np.uint8)


def _png(rgb: np.ndarray) -> bytes:
    h, w, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


GRID_HZ = (100, 1000, 10000)


def spectrogram_png(audio: np.ndarray, fs: int, lines: list[float] = (), width: int = 1200, height: int = 360,
                    min_hz: float = 30.0, max_hz: float = 16000.0, floor_db: float = -80.0) -> bytes:
    """The sound as a picture: time left to right, frequency bottom (30 Hz) to top
    (16 kHz) on a log scale, loudness as colour (dark = quiet, yellow = loud, relative
    to the loudest point). Faint horizontal lines at 100 Hz, 1 kHz and 10 kHz; white
    vertical lines at `lines` (seconds, e.g. section starts)."""
    x = np.asarray(audio, dtype=float)
    if x.ndim > 1:
        x = x.mean(axis=1)
    nper = 4096 if fs > 30000 else 2048
    hop = max(1, len(x) // width) if len(x) // width < nper else nper // 2
    f, t, Z = signal.stft(x, fs=fs, nperseg=nper, noverlap=max(0, nper - hop), boundary=None)
    power = np.abs(Z) ** 2 + 1e-20
    rows = np.geomspace(min_hz, max_hz, height)
    idx = np.clip(np.searchsorted(f, rows), 1, len(f) - 1)
    img = 10 * np.log10(power[idx])               # height x frames
    cols = np.linspace(0, img.shape[1] - 1, width).astype(int) if img.shape[1] else np.zeros(width, int)
    img = img[:, cols]
    img = (img - img.max() - floor_db) / -floor_db
    rgb = _colour(img[::-1])
    for hz in GRID_HZ:
        y = height - 1 - int(np.searchsorted(rows, hz))
        if 0 <= y < height:
            rgb[y] = (rgb[y] * 0.5 + 60).astype(np.uint8)
    duration = len(x) / fs
    for sec in lines:
        col = int(sec / duration * (width - 1)) if duration else -1
        if 0 <= col < width:
            rgb[:, col] = 255
    return _png(rgb)
