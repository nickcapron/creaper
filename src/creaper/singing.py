"""A speech voice made to sing: a whole phrase spoken in one go (so its words keep the
rise and fall of a sentence), cut into words at the quiet points between them, each
word stretched to its notes (consonants at their natural speed, the vowel held) and
moved to the melody's pitches with TD-PSOLA, which keeps the voice's formants (it
still sounds like the same person, not a chipmunk), with vibrato on held notes, a
short glide into each note, and a double a few milliseconds late. Pure numpy."""

from __future__ import annotations

import math

import numpy as np

FMIN, FMAX = 60.0, 600.0     # Hz: the voice's pitch range for tracking
HOP_S = 0.005
YIN_THRESHOLD = 0.15         # YIN's dip: the first period this aperiodic or less is the pitch
UNVOICED = 0.35              # more aperiodic than this and a frame is unvoiced (a consonant, a breath)
GLIDE_S = 0.04               # into each new note within a word
# Measured against the clean words (STOI), a deeper vibrato or a louder double blurs held
# words: 0.35 semitones and a double at -6 dB cost 0.1-0.2 on a long vowel.
VIBRATO = {"rate_hz": 5.5, "depth_semitones": 0.25, "after_s": 0.25, "ramp_s": 0.35, "min_note_s": 0.4}
DOUBLE = {"delay_s": 0.010, "cents": 6.0, "level": 0.3}
WIDE_SHIFT = 7.0             # semitones from the voice's own pitch: past this a voice starts to blur


def resample(x: np.ndarray, fs: int, to: int) -> np.ndarray:
    from .perception import _resample

    return _resample(x, fs, to)


def midi_hz(pitch: float) -> float:
    return 440.0 * 2 ** ((pitch - 69) / 12)


# ------------------------------------------------------------------ analysis

def _yin(frame: np.ndarray, w: int, lo: int, hi: int) -> tuple[int, float]:
    """(period in samples, aperiodicity 0-1) of a frame 2w long, by YIN: the cumulative
    mean normalised difference, taking the first dip under YIN_THRESHOLD (so a
    subharmonic, two or three periods long, never wins over the period itself)."""
    x = frame - frame.mean()
    head = x[:w]
    energy = np.concatenate([[0.0], np.cumsum(x * x)])
    n = len(x)
    spec = np.fft.rfft(x, 2 * n)
    corr = np.fft.irfft(np.conj(np.fft.rfft(head, 2 * n)) * spec)[: w + 1]
    taus = np.arange(w + 1)
    d = energy[w] + (energy[taus + w] - energy[taus]) - 2 * corr
    d[0] = 0.0
    d = np.maximum(d, 0.0)
    cum = np.cumsum(d[1:])
    cmnd = np.ones(w + 1)
    cmnd[1:] = d[1:] * np.arange(1, w + 1) / np.maximum(cum, 1e-12)
    hi = min(hi, w)
    if hi <= lo:
        return 0, 1.0
    seg = cmnd[lo:hi]
    below = np.nonzero(seg < YIN_THRESHOLD)[0]
    if below.size:
        k = int(below[0])
        while k + 1 < seg.size and seg[k + 1] < seg[k]:
            k += 1
    else:
        k = int(np.argmin(seg))
    return lo + k, float(seg[k])


def f0_track(x: np.ndarray, fs: int, hop_s: float = HOP_S) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(frame centres in samples, f0 in Hz with 0 for unvoiced, voicing strength 0-1)."""
    hop = max(1, int(hop_s * fs))
    w = int(fs / FMIN) + 2
    lo, hi = int(fs / FMAX), int(fs / FMIN) + 1
    pad = np.pad(x.astype(np.float64), (w, w))
    centres = np.arange(0, len(x), hop)
    f0 = np.zeros(len(centres))
    strength = np.zeros(len(centres))
    floor = 1e-3 * (float(np.max(np.abs(x))) if x.size else 0.0)
    for i, c in enumerate(centres):
        frame = pad[c: c + 2 * w]
        if np.max(np.abs(frame)) <= floor:
            continue
        lag, aperiodic = _yin(frame, w, lo, hi)
        strength[i] = max(0.0, 1.0 - aperiodic)
        if lag and aperiodic < UNVOICED:
            f0[i] = fs / lag
    return centres, f0, strength


def hnr_db(x: np.ndarray, fs: int) -> float | None:
    """Harmonics-to-noise ratio (dB, median over voiced frames): a clean sung tone is
    15 dB or more, a breathy or buzzy one under 8."""
    _, f0, strength = f0_track(x, fs, 0.01)
    r = np.clip(strength[f0 > 0], 1e-4, 1 - 1e-4)   # 1 - aperiodicity: the periodic share
    if r.size < 3:
        return None
    return round(float(np.median(10 * np.log10(r / (1 - r)))), 1)


def pitch_marks(x: np.ndarray, fs: int, centres: np.ndarray, f0: np.ndarray) -> list[tuple[int, int]]:
    """(sample, period) of each glottal pulse in the voiced stretches: a mark on the
    biggest peak of each period, the next a period later, refined to its local peak."""
    marks: list[tuple[int, int]] = []
    hop = int(centres[1] - centres[0]) if len(centres) > 1 else len(x)

    def period_at(n: int) -> int:
        i = min(len(f0) - 1, max(0, int(round(n / hop))))
        return int(round(fs / f0[i])) if f0[i] > 0 else 0

    n = 0
    while n < len(x):
        p = period_at(n)
        if not p:
            n += hop
            continue
        a = int(np.argmax(np.abs(x[n: n + p]))) + n if n + p <= len(x) else n
        while a < len(x):
            p = period_at(a)
            if not p:
                break
            marks.append((a, p))
            guess = a + p
            lo, hi = guess - p // 4, min(len(x), guess + p // 4)
            if lo >= len(x) or hi <= lo:
                break
            a = lo + int(np.argmax(np.abs(x[lo:hi])))
        n = a + max(hop, 1)
    return marks


# --------------------------------------------------------------- synthesis

def psola(x: np.ndarray, fs: int, out_len: int, time_map, target_hz) -> np.ndarray:
    """TD-PSOLA: output out_len samples where output sample t plays analysis sample
    time_map(t) at pitch target_hz(t) (None keeps the voice's own pitch). Voiced grains
    are two periods long, spaced at the target period and scaled so the overlap keeps
    the level; unvoiced stretches are overlap-added in 10 ms grains 5 ms apart."""
    centres, f0, _ = f0_track(x, fs)
    marks = pitch_marks(x, fs, centres, f0)
    positions = np.array([m for m, _ in marks]) if marks else np.zeros(0)
    hop = int(centres[1] - centres[0]) if len(centres) > 1 else 1
    out = np.zeros(out_len + 4 * int(fs / FMIN))
    if len(x) == 0:
        return out[:out_len]
    unvoiced_h = max(8, int(0.005 * fs))
    rng = np.random.default_rng(0)
    t = 0
    while t < out_len:
        a = int(min(len(x) - 1, max(0, time_map(t))))
        frame = min(len(f0) - 1, a // hop)
        voiced = f0[frame] > 0 and positions.size
        if voiced:
            k = int(np.argmin(np.abs(positions - a)))
            m, p = marks[k]
            if abs(m - a) > 2 * p:
                voiced = False
        if voiced:
            hz = target_hz(t)
            step = int(round(fs / hz)) if hz else p
            lo, hi = max(0, m - p), min(len(x), m + p)
            grain = x[lo:hi] * np.hanning(hi - lo)
            start = t - (m - lo)
            gain = step / p
        else:
            # A slowed-down hiss repeats its grains every 5 ms (a 200 Hz buzz) unless each
            # grain comes from a slightly different place.
            step = unvoiced_h
            a = int(min(len(x) - 1, max(0, a + rng.integers(-2 * unvoiced_h, 2 * unvoiced_h + 1))))
            lo, hi = max(0, a - unvoiced_h), min(len(x), a + unvoiced_h)
            grain = x[lo:hi] * np.hanning(hi - lo)
            start = t - (a - lo)
            gain = 1.0
        s0 = max(0, start)
        g = grain[s0 - start:]
        out[s0: s0 + len(g)] += g * gain
        t += max(1, step)
    # Hann grains at half their length apart sum to one; voiced ones are scaled by
    # step / period, which their closer (or wider) spacing undoes.
    return out[:out_len]


def vowel_map(x: np.ndarray, fs: int, out_len: int, vowel: tuple[int, int]):
    """A time map that plays the word's consonants at natural speed and stretches (or
    squeezes) the vowel to fill out_len; the whole word scales when there's no room."""
    start, end = vowel
    head, tail = start, len(x) - end
    room = out_len - head - tail
    if end - start < int(0.03 * fs) or room < max(int(0.04 * fs), 0.4 * (end - start)):
        scale = len(x) / max(1, out_len)
        return lambda t: t * scale
    vscale = (end - start) / room

    def m(t: int) -> float:
        if t < head:
            return t
        if t < head + room:
            return start + (t - head) * vscale
        return end + (t - head - room)
    return m


def contour(notes: list[tuple[float, float]], length_s: float, vibrato: bool = True, glide_s: float = GLIDE_S):
    """target_hz(t) for a word sung over notes [(start_s within the word, MIDI pitch)]:
    a GLIDE_S slide into each new note, vibrato on notes held VIBRATO['min_note_s'] or
    longer, easing in after VIBRATO['after_s']."""
    notes = sorted(notes) or [(0.0, 60.0)]
    ends = [n[0] for n in notes[1:]] + [length_s]

    def at(t_s: float) -> float:
        i = max(0, sum(1 for s, _ in notes if s <= t_s) - 1)
        start, pitch = notes[i]
        if i > 0 and glide_s > 0 and t_s - start < glide_s:
            prev = notes[i - 1][1]
            pitch = prev + (pitch - prev) * (t_s - start) / glide_s
        held = ends[i] - start
        if vibrato and held >= VIBRATO["min_note_s"] and t_s - start > VIBRATO["after_s"]:
            depth = VIBRATO["depth_semitones"] * min(1.0, (t_s - start - VIBRATO["after_s"]) / VIBRATO["ramp_s"])
            pitch += depth * math.sin(2 * math.pi * VIBRATO["rate_hz"] * (t_s - start - VIBRATO["after_s"]))
        return pitch
    return at


def voiced_span(x: np.ndarray, fs: int, min_s: float = 0.03) -> tuple[int, int] | None:
    """The word's longest voiced stretch (its vowel, or a voiced consonant like m or l),
    one-frame dropouts bridged: the part a singer holds. None when nothing in it is
    voiced long enough (a whispered or unvoiced word)."""
    if len(x) == 0:
        return None
    centres, f0, _ = f0_track(x, fs, 0.01)
    voiced = f0 > 0
    for i in range(1, len(voiced) - 1):
        voiced[i] |= voiced[i - 1] and voiced[i + 1]
    best, start = (0, 0), None
    for i, v in enumerate(list(voiced) + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start > best[1] - best[0]:
                best = (start, i)
            start = None
    hop = int(0.01 * fs)
    a, b = best[0] * hop, min(len(x), best[1] * hop)
    return (a, b) if b - a >= min_s * fs else None


def own_pitch(x: np.ndarray, fs: int) -> float | None:
    """The voice's median pitch (MIDI) in a stretch of speech."""
    _, f0, _ = f0_track(x, fs, 0.01)
    voiced = f0[f0 > 0]
    return float(69 + 12 * np.log2(np.median(voiced) / 440)) if voiced.size else None


def sing_word(x: np.ndarray, fs: int, seconds: float, notes: list[tuple[float, float]],
              vowel: tuple[int, int], vibrato: bool = True, hard: bool = False) -> np.ndarray:
    """One spoken word sung: stretched to `seconds`, on the notes' pitches. hard: tuned
    like a hard pitch corrector (Daft Punk, T-Pain): each note dead on its pitch, no
    glide into it and no vibrato, so the steps between notes are heard."""
    out_len = max(1, int(round(seconds * fs)))
    pitch = contour(notes, seconds, vibrato and not hard, 0.0 if hard else GLIDE_S)
    y = psola(x, fs, out_len, vowel_map(x, fs, out_len, vowel), lambda t: midi_hz(pitch(t / fs)))
    fade = min(len(y) // 4, int(0.006 * fs))
    if fade:
        ramp = np.linspace(0, 1, fade)
        y[:fade] *= ramp
        y[-fade:] *= ramp[::-1]
    peak = float(np.max(np.abs(y))) if y.size else 0.0
    return y / peak * 0.8 if peak > 0 else y


def _biquad(kind: str, f0: float, fs: int, gain_db: float = 0.0, q: float = 0.707):
    """RBJ cookbook coefficients (b, a) for a peak, high shelf or high-pass."""
    a_ = 10 ** (gain_db / 40)
    w = 2 * math.pi * f0 / fs
    cos, alpha = math.cos(w), math.sin(w) / (2 * q)
    if kind == "peak":
        b = [1 + alpha * a_, -2 * cos, 1 - alpha * a_]
        a = [1 + alpha / a_, -2 * cos, 1 - alpha / a_]
    elif kind == "highshelf":
        sq = 2 * math.sqrt(a_) * alpha
        b = [a_ * ((a_ + 1) + (a_ - 1) * cos + sq), -2 * a_ * ((a_ - 1) + (a_ + 1) * cos),
             a_ * ((a_ + 1) + (a_ - 1) * cos - sq)]
        a = [(a_ + 1) - (a_ - 1) * cos + sq, 2 * ((a_ - 1) - (a_ + 1) * cos), (a_ + 1) - (a_ - 1) * cos - sq]
    else:  # highpass
        b = [(1 + cos) / 2, -(1 + cos), (1 + cos) / 2]
        a = [1 + alpha, -2 * cos, 1 - alpha]
    return np.array(b) / a[0], np.array(a) / a[0]


VOICE_EQ = (("highpass", 90, 0.0, 0.707), ("peak", 450, -3.0, 1.0), ("peak", 2500, 5.0, 0.9),
            ("highshelf", 5000, 4.0, 0.707))


def voice_eq(y: np.ndarray, fs: int) -> np.ndarray:
    """The speech voices are dark (about 1% of their energy at 2-4 kHz, where a singer's
    presence is): a high-pass, a dip in the boxy 450 Hz, presence at 2.5 kHz and air,
    so the sung line starts out sounding like a vocal instead of needing an EQ first."""
    from scipy import signal

    out = y.astype(np.float64)
    for kind, f0, gain, q in VOICE_EQ:
        if f0 < fs / 2 - 100:
            b, a = _biquad(kind, f0, fs, gain, q)
            out = signal.lfilter(b, a, out, axis=0)
    peak = float(np.max(np.abs(out))) if out.size else 0.0
    return out / peak * 0.8 if peak > 0 else out


def double(y: np.ndarray, fs: int) -> np.ndarray:
    """Stereo: the voice in the middle and a double DOUBLE['delay_s'] late, a few cents
    sharp on the left and flat on the right, the way a second take sits with the first."""
    d = int(DOUBLE["delay_s"] * fs)
    out = np.zeros((len(y), 2))
    out[:, 0] = out[:, 1] = y
    n = np.arange(len(y))
    for ch, sign in ((0, 1), (1, -1)):
        ratio = 2 ** (sign * DOUBLE["cents"] / 1200)
        shifted = np.interp(n * ratio, n, y, right=0.0)
        out[d:, ch] += DOUBLE["level"] * shifted[: len(y) - d]
    peak = float(np.max(np.abs(out))) if out.size else 0.0
    return out / peak * 0.8 if peak > 0 else out


# ------------------------------------------------------------- the phrase

def _features(x: np.ndarray, fs: int, bands: int = 24) -> np.ndarray:
    """Log energy in log-spaced bands (80 Hz-8 kHz) per 10 ms, level removed: what a
    word sounds like, frame by frame, whatever its loudness."""
    from scipy import signal

    hop = int(0.01 * fs)
    nper = 2 * hop
    if len(x) < nper:
        x = np.pad(x, (0, nper - len(x)))
    f, _, z = signal.stft(x, fs=fs, nperseg=nper, noverlap=nper - hop, boundary=None, padded=False)
    power = np.abs(z) ** 2
    edges = np.geomspace(80, min(8000, fs / 2 - 1), bands + 1)
    feats = np.stack([power[(f >= lo) & (f < hi)].sum(axis=0) for lo, hi in zip(edges, edges[1:])], axis=1)
    feats = np.log10(feats + 1e-10)
    loud = feats.max(axis=1, keepdims=True)
    return np.concatenate([feats - loud, (loud - loud.max()) / 2], axis=1)


def align_words(phrase: np.ndarray, fs: int, words: list[np.ndarray]) -> list[tuple[int, int]]:
    """Where each word is in a phrase spoken in one go, by aligning it (dynamic time
    warping) against the same words spoken one at a time, whose edges are known.
    Connected speech has no pauses between words to cut at; this needs none. Every
    word gets at least 20 ms."""
    hop = int(0.01 * fs)
    target = _features(phrase, fs)
    parts = [_features(w, fs) for w in words]
    ref = np.concatenate(parts)
    edges = np.cumsum([0] + [len(p) for p in parts])
    n, m = len(target), len(ref)
    cost = np.sqrt(((target[:, None, :] - ref[None, :, :]) ** 2).sum(axis=2))
    acc = np.full((n + 1, m + 1), np.inf)
    acc[0, 0] = 0.0
    for i in range(1, n + 1):
        row, prev, c = acc[i], acc[i - 1], cost[i - 1]
        for j in range(1, m + 1):
            row[j] = c[j - 1] + min(prev[j - 1], prev[j], row[j - 1])
    # Walk back the cheapest path: phrase frame i <-> reference frame j.
    i, j = n, m
    first_i = np.full(m, n - 1)
    while i > 0 and j > 0:
        first_i[j - 1] = i - 1
        step = int(np.argmin([acc[i - 1, j - 1], acc[i - 1, j], acc[i, j - 1]]))
        i, j = (i - 1, j - 1) if step == 0 else (i - 1, j) if step == 1 else (i, j - 1)
    starts = [int(first_i[min(e, m - 1)]) for e in edges[:-1]]
    min_frames = 2
    for k in range(1, len(starts)):
        starts[k] = max(starts[k], starts[k - 1] + min_frames)
    for k in range(len(starts) - 1, 0, -1):     # and leave room for the words after
        starts[k - 1] = min(starts[k - 1], starts[k] - min_frames)
    starts[0] = max(0, starts[0])
    bounds = [s * hop for s in starts] + [len(phrase)]
    return [(a, max(a + min_frames * hop, b)) for a, b in zip(bounds, bounds[1:])]


def split_phrase(x: np.ndarray, fs: int, weights: list[float]) -> list[tuple[int, int]]:
    """Cuts a spoken phrase into len(weights) words: each boundary at the quietest
    10 ms near where the words' weights (their syllables) put it. Returns (start, end)
    sample spans, the leading and trailing silence left out."""
    frame = max(1, int(0.01 * fs))
    n = len(x) // frame
    if n == 0 or not weights:
        return [(0, len(x))] * max(1, len(weights))
    level = 20 * np.log10(np.sqrt(np.mean(x[: n * frame].reshape(n, frame) ** 2, axis=1)) + 1e-9)
    loud = np.nonzero(level > level.max() - 35)[0]
    first, last = int(loud[0]), int(loud[-1]) + 1
    total = float(sum(weights))
    cuts = [first]
    acc = 0.0
    for i, w in enumerate(weights[:-1]):
        acc += w
        guess = first + (last - first) * acc / total
        span = (last - first) * min(w, weights[i + 1]) / total * 0.45
        lo = max(cuts[-1] + 2, int(guess - span))
        hi = min(last - 2 * (len(weights) - i - 1), int(guess + span) + 1)
        if hi <= lo:
            cuts.append(min(last - 1, max(cuts[-1] + 1, int(round(guess)))))
            continue
        cuts.append(lo + int(np.argmin(level[lo:hi])))
    cuts.append(last)
    return [(a * frame, b * frame) for a, b in zip(cuts, cuts[1:])]
