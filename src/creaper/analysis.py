"""Measurements of a rendered audio file, for mix feedback.

Loudness follows ITU-R BS.1770-4 / EBU R128 (integrated, momentary,
short-term, loudness range); true peak uses 4x oversampling.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

# Broad ranges an engineer talks about, in Hz.
BANDS = {
    "sub (20-60 Hz)": (20, 60),
    "bass (60-250 Hz)": (60, 250),
    "low mids (250-500 Hz)": (250, 500),
    "mids (500 Hz-2 kHz)": (500, 2000),
    "upper mids (2-4 kHz)": (2000, 4000),
    "presence (4-6 kHz)": (4000, 6000),
    "air (6-20 kHz)": (6000, 20000),
}
OCTAVE_CENTERS = (31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000)


def k_weighting_sos(fs: float) -> np.ndarray:
    """BS.1770 K-weighting (pre-filter shelf + RLB high-pass) for any sample rate.

    Uses the analog-prototype constants from libebur128, which reproduce the
    48 kHz coefficients in the standard.
    """
    f0, gain_db, q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    k = math.tan(math.pi * f0 / fs)
    vh = 10 ** (gain_db / 20)
    vb = vh ** 0.4996667741545416
    a0 = 1 + k / q + k * k
    shelf = [
        (vh + vb * k / q + k * k) / a0, 2 * (k * k - vh) / a0, (vh - vb * k / q + k * k) / a0,
        1.0, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0,
    ]
    f0, q = 38.13547087602444, 0.5003270373238773
    k = math.tan(math.pi * f0 / fs)
    a0 = 1 + k / q + k * k
    highpass = [1.0, -2.0, 1.0, 1.0, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0]
    return np.array([shelf, highpass])


def _lufs(power: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore"):
        return -0.691 + 10 * np.log10(power)


def _db(x: float) -> float | None:
    return None if x <= 0 else round(20 * math.log10(x), 2)


def _round(x: float | None, places: int = 2) -> float | None:
    if x is None or not math.isfinite(x):
        return None
    return round(float(x), places)


def loudness(audio: np.ndarray, fs: float) -> dict:
    """Integrated/momentary/short-term loudness and LRA. audio: (samples, channels)."""
    sos = k_weighting_sos(fs)
    hop = int(round(0.1 * fs))
    n_hops = audio.shape[0] // hop
    if n_hops < 4:
        return {"integrated_lufs": None, "note": "too short to measure loudness (needs 400 ms)"}
    # Sum of K-weighted energy per 100 ms hop, summed over channels (all weights are 1 for stereo).
    hop_energy = np.zeros(n_hops)
    for ch in range(audio.shape[1]):
        z = signal.sosfilt(sos, audio[:, ch].astype(np.float64))
        hop_energy += np.square(z[: n_hops * hop]).reshape(n_hops, hop).sum(axis=1)
    cumulative = np.concatenate([[0.0], np.cumsum(hop_energy)])

    def windows(n: int) -> np.ndarray:
        return (cumulative[n:] - cumulative[:-n]) / (n * hop)

    momentary = windows(4)  # 400 ms blocks, 75% overlap
    block_loudness = _lufs(momentary)
    above_abs = block_loudness > -70
    integrated = None
    if above_abs.any():
        relative_gate = _lufs(momentary[above_abs].mean()) - 10
        gated = above_abs & (block_loudness > relative_gate)
        integrated = float(_lufs(momentary[gated].mean()))

    result = {
        "integrated_lufs": _round(integrated),
        "max_momentary_lufs": _round(float(block_loudness.max())),
    }
    if n_hops >= 30:
        short = windows(30)  # 3 s windows every 100 ms
        short_loudness = _lufs(short)
        result["max_short_term_lufs"] = _round(float(short_loudness.max()))
        above = short_loudness > -70
        if above.any():
            relative_gate = _lufs(short[above].mean()) - 20
            kept = short_loudness[above & (short_loudness > relative_gate)]
            if kept.size:
                result["loudness_range_lu"] = _round(float(np.percentile(kept, 95) - np.percentile(kept, 10)))
        result["_short_term"] = short_loudness
    return result


def true_peak(x: np.ndarray, fs: float, chunk: int = 1 << 20) -> float:
    factor = 4 if fs < 96000 else 2 if fs < 192000 else 1
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    if factor == 1:
        return peak
    pad = 64
    for start in range(0, x.size, chunk):
        seg_start = max(0, start - pad)
        up = signal.resample_poly(x[seg_start: start + chunk + pad], factor, 1)
        # Only count this chunk's own samples; the padding exists to keep its edges clean.
        first = (start - seg_start) * factor
        interior = up[first: first + min(chunk, x.size - start) * factor]
        peak = max(peak, float(np.max(np.abs(interior))))
    return peak


def envelope_range(audio: np.ndarray, fs: float, window_s: float = 0.05) -> float | None:
    """Spread (dB) between loud and quiet moments: the 95th minus the 10th percentile
    of short-window RMS level over audible sound. A compressor turns the loud moments
    down relative to the quiet ones, so this shrinks by roughly the gain reduction it
    applies to loud parts, whatever the output level (make-up gain doesn't change it)."""
    n = int(window_s * fs)
    count = audio.shape[0] // n
    if count < 4:
        return None
    power = np.mean(np.square(audio[: count * n].astype(np.float64)).reshape(count, n, -1), axis=(1, 2))
    audible = power > 1e-6  # above about -60 dBFS RMS
    if audible.sum() < 4:
        return None
    level = 10 * np.log10(power[audible])
    return float(np.percentile(level, 95) - np.percentile(level, 10))


def spectrum(mono: np.ndarray, fs: float) -> dict:
    nperseg = min(8192, mono.size)
    freqs, psd = signal.welch(mono, fs=fs, nperseg=nperseg)
    df = freqs[1] - freqs[0]
    total = float(psd[(freqs >= 20) & (freqs <= 20000)].sum() * df)
    if total <= 0:
        return {}

    def band_energy(lo: float, hi: float) -> float:
        mask = (freqs >= lo) & (freqs < hi)
        return float(psd[mask].sum() * df)

    bands = {}
    for name, (lo, hi) in BANDS.items():
        e = band_energy(lo, min(hi, fs / 2))
        bands[name] = {"share_pct": round(100 * e / total, 1), "db_re_total": _round(10 * math.log10(e / total)) if e > 0 else None}
    octaves = {}
    for fc in OCTAVE_CENTERS:
        if fc * math.sqrt(2) > fs / 2:
            break
        e = band_energy(fc / math.sqrt(2), fc * math.sqrt(2))
        label = f"{fc:g} Hz" if fc < 1000 else f"{fc / 1000:g} kHz"
        octaves[label] = _round(10 * math.log10(e / total)) if e > 0 else None
    audible = (freqs >= 20) & (freqs <= 20000)
    centroid = float((freqs[audible] * psd[audible]).sum() / psd[audible].sum())
    return {"bands": bands, "octave_bands_db": octaves, "spectral_centroid_hz": round(centroid)}


def stereo(audio: np.ndarray, fs: float) -> dict:
    if audio.shape[1] < 2:
        return {"channels": 1}
    left, right = audio[:, 0].astype(np.float64), audio[:, 1].astype(np.float64)
    mid, side = (left + right) / 2, (left - right) / 2
    e_mid, e_side = float(np.dot(mid, mid)), float(np.dot(side, side))
    if e_mid + e_side == 0:
        return {}

    def correlation(a: np.ndarray, b: np.ndarray) -> float | None:
        denom = math.sqrt(float(np.dot(a, a)) * float(np.dot(b, b)))
        return _round(float(np.dot(a, b)) / denom) if denom > 0 else None

    low = signal.butter(4, 150, btype="lowpass", fs=fs, output="sos")
    e_left, e_right = float(np.dot(left, left)), float(np.dot(right, right))
    # Positive = left louder. A silent side reads as +/-60 dB rather than infinity.
    if e_left > 0 and e_right > 0:
        balance = max(-60.0, min(60.0, 10 * math.log10(e_left / e_right)))
    else:
        balance = 60.0 if e_left > 0 else -60.0
    result = {
        "correlation": correlation(left, right),
        "low_end_correlation_below_150hz": correlation(signal.sosfilt(low, left), signal.sosfilt(low, right)),
        "side_to_mid_db": _round(10 * math.log10(e_side / e_mid)) if e_side > 0 and e_mid > 0 else None,
        "left_right_balance_db": _round(balance),
    }
    if e_right == 0 or e_left == 0:
        result["note"] = "only the left channel has sound" if e_right == 0 else "only the right channel has sound"
    elif e_side < e_mid * 1e-6:
        result["note"] = "effectively mono"
    return result


def analyze_file(path: str | Path, timeline_points: int = 32) -> dict:
    audio, fs = sf.read(str(path), dtype="float32", always_2d=True)
    duration = audio.shape[0] / fs
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak == 0:
        return {"duration_seconds": round(duration, 2), "silent": True}

    rms = math.sqrt(float(np.mean(np.square(audio, dtype=np.float64))))
    tp = max(true_peak(audio[:, ch], fs) for ch in range(audio.shape[1]))
    loud = loudness(audio, fs)
    short_term = loud.pop("_short_term", None)

    result: dict = {
        "duration_seconds": round(duration, 2),
        "sample_rate": fs,
        "loudness": loud,
        "levels": {
            "sample_peak_dbfs": _db(peak),
            "true_peak_dbtp": _db(tp),
            "rms_dbfs": _db(rms),
            "crest_factor_db": _round(20 * math.log10(peak / rms)) if rms > 0 else None,
            "envelope_range_db": _round(envelope_range(audio, fs)),
            "samples_over_0dbfs": int(np.count_nonzero(np.abs(audio) > 1.0)),
            "dc_offset_dbfs": _db(float(np.max(np.abs(audio.mean(axis=0, dtype=np.float64))))),
        },
        "stereo": stereo(audio, fs),
        "spectrum": spectrum(audio.mean(axis=1, dtype=np.float64), fs),
    }
    if short_term is not None and short_term.size:
        # Short-term windows end every 100 ms starting at 3 s; sample a coarse timeline.
        idx = np.linspace(0, short_term.size - 1, min(timeline_points, short_term.size)).round().astype(int)
        result["short_term_timeline"] = [
            {"t": round(3.0 + 0.1 * int(i) - 1.5, 2), "lufs": _round(float(short_term[i]), 1)} for i in idx
        ]
    return result
