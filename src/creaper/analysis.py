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


def _window_db(mono: np.ndarray, n: int) -> np.ndarray:
    count = mono.size // n
    power = np.mean(np.square(mono[: count * n].reshape(count, n)), axis=1)
    return 10 * np.log10(power + 1e-20)


def align(dry: np.ndarray, wet: np.ndarray, fs: float, max_lag_s: float = 0.05) -> int:
    """Samples the wet signal lags the dry one (a plugin's lookahead or latency), found
    by cross-correlating the first 20 seconds; 0 when they're already aligned."""
    n = min(dry.size, wet.size, int(20 * fs))
    if n < 1024:
        return 0
    a, b = dry[:n] - dry[:n].mean(), wet[:n] - wet[:n].mean()
    size = 1 << int(np.ceil(np.log2(2 * n)))
    corr = np.fft.irfft(np.fft.rfft(b, size) * np.conj(np.fft.rfft(a, size)), size)
    lag_max = int(max_lag_s * fs)
    lags = np.concatenate([np.arange(0, lag_max + 1), np.arange(-lag_max, 0)])
    values = np.concatenate([corr[: lag_max + 1], corr[-lag_max:]])
    return int(lags[int(np.argmax(values))])


GR_WINDOW_S = 0.05
GR_LOUD_DB = 12.0   # gain reduction is read where the dry signal is within this of its loudest


def gain_reduction(dry: np.ndarray, wet: np.ndarray, fs: float) -> dict:
    """How much a compressor or limiter turns the loud moments down: the level difference
    between the dry and processed renders in 50 ms windows (aligned first), relative to
    the quietest 5% of windows (which carry only make-up gain or a level change), read
    where the dry signal is within GR_LOUD_DB of its loudest. Make-up gain and output
    level don't count. Measure one section (calibration uses the loudest 16 bars, see
    loudest_span): across sections, a quiet intro turned up reads like the rest turned
    down. Returns p95 and median gain reduction in dB."""
    d = dry.mean(axis=1) if dry.ndim > 1 else dry
    w = wet.mean(axis=1) if wet.ndim > 1 else wet
    lag = align(d.astype(np.float64), w.astype(np.float64), fs)
    if lag > 0:
        w = w[lag:]
    elif lag < 0:
        d = d[-lag:]
    n = int(GR_WINDOW_S * fs)
    count = min(d.size, w.size) // n
    if count < 4:
        return {}
    dry_db, wet_db = _window_db(d[: count * n].astype(np.float64), n), _window_db(w[: count * n].astype(np.float64), n)
    audible = dry_db > -60
    if audible.sum() < 4:
        return {}
    diff = dry_db - wet_db
    # The zero point: the quietest 5% of the differences carry only make-up gain. Never
    # above 0, or compression applied everywhere (a pad held over the threshold) would
    # read as a level change and vanish. A plain cut in level reads as reduction.
    reference = min(0.0, float(np.percentile(diff[audible], 5)))
    gr = np.maximum(0.0, diff - reference)
    loud = audible & (dry_db >= dry_db[audible].max() - GR_LOUD_DB)
    return {"gr_db_p95": _round(float(np.percentile(gr[loud], 95)), 2),
            "gr_db_median": _round(float(np.median(gr[loud])), 2), "lag_samples": lag}


def loudest_span(mono: np.ndarray, fs: float, span_s: float) -> float:
    """Start (s) of the loudest span_s stretch: where a compressor is calibrated, so a
    quiet intro or breakdown doesn't decide how hard it works."""
    if mono.size <= int(span_s * fs):
        return 0.0
    hop = int(0.5 * fs)
    db = _window_db(mono.astype(np.float64), hop)
    width = max(1, int(span_s / 0.5))
    if db.size <= width:
        return 0.0
    power = 10 ** (db / 10)
    sums = np.convolve(power, np.ones(width), mode="valid")
    return float(np.argmax(sums) * 0.5)


def clipped_runs(audio: np.ndarray, min_run: int = 3, near_full_scale: float = 0.99) -> int:
    """Flat tops: runs of min_run or more samples in a row with the same value, at the
    file's highest level, when that level is at full scale. A plugin or a fixed-point
    stage that clipped leaves them; a clean peak doesn't, even a deep bass note that
    spends several samples near its top (they still differ from sample to sample)."""
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak < near_full_scale:
        return 0
    runs = 0
    for ch in range(audio.shape[1]):
        x = audio[:, ch].astype(np.float64)
        # Steps between neighbours that stay put, both at the top.
        flat = (np.abs(np.diff(x)) < 1e-7) & (np.abs(x[:-1]) >= peak * 0.999)
        if not flat.any():
            continue
        edges = np.diff(np.concatenate([[0], flat.astype(np.int8), [0]]))
        lengths = np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1)
        runs += int(np.count_nonzero(lengths >= min_run - 1))
    return runs


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


# Tone over time, in seconds-long windows: how much of the sound sits where the ear is
# most sensitive (2-5 kHz: "harsh", "piercing"), in sibilance and fizz (5-10 kHz) and in
# the low mids (200-500 Hz: "muddy", "boxy"). Shares, so they don't depend on level.
TONE_BANDS = {"harsh_2_5k": (2000, 5000), "sibilance_5_10k": (5000, 10000), "mud_200_500": (200, 500)}
# Only windows within this of the loud part count: in a quiet intro or a fading tail
# the little that is left (hiss, a hat) would otherwise read as harsh.
TONE_GATE_DB = 20.0


def tone_over_time(mono: np.ndarray, fs: float, window_s: float = 1.0) -> dict:
    """Median and 95th percentile of each tone band's share of the energy (%) over
    window_s windows of the loud part of the sound, and the 10th percentile of each
    window's crest factor (dB; low = squashed even in its liveliest moments)."""
    n = int(window_s * fs)
    count = mono.size // n
    if count < 1:
        return {}
    frames = mono[: count * n].astype(np.float64).reshape(count, n)
    power = np.mean(np.square(frames), axis=1)
    if not (power > 0).any():
        return {}
    loud = 10 * np.log10(np.percentile(power[power > 0], 95))
    keep = power > 0
    keep &= 10 * np.log10(np.where(keep, power, 1e-30)) > loud - TONE_GATE_DB
    frames, power = frames[keep], power[keep]
    nperseg = min(4096, n)
    freqs, psd = signal.welch(frames, fs=fs, nperseg=nperseg, axis=1)
    audible = (freqs >= 20) & (freqs <= 20000)
    total = psd[:, audible].sum(axis=1) + 1e-30
    out: dict = {"windows": int(frames.shape[0])}
    for name, (lo, hi) in TONE_BANDS.items():
        if lo >= fs / 2:
            continue
        share = 100 * psd[:, (freqs >= lo) & (freqs < hi)].sum(axis=1) / total
        out[f"{name}_pct_median"] = _round(float(np.median(share)), 1)
        out[f"{name}_pct_p95"] = _round(float(np.percentile(share, 95)), 1)
    crest = 20 * np.log10(np.max(np.abs(frames), axis=1) / np.sqrt(power))
    out["crest_db_p10"] = _round(float(np.percentile(crest, 10)), 1)
    return out


NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def _note_at(hz: float, within_cents: float = 30.0) -> str | None:
    """The note name (C4 = middle C) a frequency sits on, if it's within_cents of one."""
    midi = 69 + 12 * math.log2(hz / 440)
    nearest = round(midi)
    if abs(midi - nearest) * 100 > within_cents:
        return None
    return f"{NOTE_NAMES[nearest % 12]}{nearest // 12 - 1}"


def _prominence(level: np.ndarray, freqs: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """How far each bin in idx stands above the spectrum around it (dB), smoothed in dB
    over a third of an octave (f/2^(1/6) .. f*2^(1/6))."""
    cumulative = np.concatenate([[0.0], np.cumsum(level)])
    lo = np.searchsorted(freqs, freqs[idx] / 2 ** (1 / 6))
    hi = np.searchsorted(freqs, freqs[idx] * 2 ** (1 / 6), side="right")
    return level[idx] - (cumulative[hi] - cumulative[lo]) / np.maximum(1, hi - lo)


def resonances(mono: np.ndarray, fs: float, min_db: float = 8.0, persistence: float = 0.75, window_s: float = 2.0,
               limit: int = 4) -> list[dict]:
    """Narrow peaks, 100 Hz-10 kHz, that stand more than min_db above the spectrum
    around them in at least `persistence` of the loud windows: a ringing filter, a
    resonance pushed too far, a boxy room. A held note is a peak too, but the notes move
    with the chords and a resonance stays put, so peaks in only some windows are
    left out. A drone or a tonic pedal still shows up, so a peak that sits on a note
    says which (check it against the key before cutting it). Most persistent first."""
    n = int(window_s * fs)
    count = mono.size // n
    nperseg = min(8192, n)
    if count < 2 or nperseg < 1024:
        return []
    frames = mono[: count * n].astype(np.float64).reshape(count, n)
    power = np.mean(np.square(frames), axis=1)
    if not (power > 0).any():
        return []
    loud = 10 * np.log10(np.percentile(power[power > 0], 95))
    frames = frames[10 * np.log10(power + 1e-30) > loud - TONE_GATE_DB]
    if frames.shape[0] < 2:
        return []
    freqs, psd = signal.welch(frames, fs=fs, nperseg=nperseg, axis=1)
    idx = np.flatnonzero((freqs >= 100) & (freqs <= min(10000, fs / 2)))
    if idx.size < 3:
        return []
    # Each window's peaks, spread to the neighbouring bin either side: a resonance's peak
    # wobbles by a bin from window to window.
    hits = np.zeros(idx.size)
    heights = [[] for _ in range(idx.size)]
    for row in psd:
        above = _prominence(10 * np.log10(row + 1e-30), freqs, idx)
        peaks, props = signal.find_peaks(above, height=min_db)
        mark = np.zeros(idx.size, dtype=bool)
        for p, h in zip(peaks, props["peak_heights"]):
            for q in (p - 1, p, p + 1):
                if 0 <= q < idx.size:
                    mark[q] = True
                    heights[q].append(float(h))
        hits += mark
    share = hits / frames.shape[0]
    found = sorted((i for i in range(idx.size) if share[i] >= persistence), key=lambda i: (-share[i], -np.median(heights[i])))
    out: list[dict] = []
    for i in found:
        hz = float(freqs[idx[i]])
        # One report per region: neighbouring bins of one peak aren't separate resonances.
        if all(abs(math.log2(hz / o["hz"])) > 1 / 12 for o in out):
            found_at = {"hz": int(round(hz)), "db_above_surroundings": _round(float(np.median(heights[i])), 1),
                        "share_of_song": _round(float(share[i]), 2)}
            note = _note_at(hz)
            if note:
                found_at["note"] = note
            out.append(found_at)
        if len(out) == limit:
            break
    return out


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

    mono = audio.mean(axis=1, dtype=np.float64)
    tone = tone_over_time(mono, fs)
    if tone:
        tone["resonances"] = resonances(mono, fs)
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
            "clipped_runs": clipped_runs(audio),
            "dc_offset_dbfs": _db(float(np.max(np.abs(audio.mean(axis=0, dtype=np.float64))))),
        },
        "stereo": stereo(audio, fs),
        "spectrum": spectrum(mono, fs),
        "tone_over_time": tone,
    }
    if short_term is not None and short_term.size:
        # Short-term windows end every 100 ms starting at 3 s; sample a coarse timeline.
        idx = np.linspace(0, short_term.size - 1, min(timeline_points, short_term.size)).round().astype(int)
        result["short_term_timeline"] = [
            {"t": round(3.0 + 0.1 * int(i) - 1.5, 2), "lufs": _round(float(short_term[i]), 1)} for i in idx
        ]
    return result
