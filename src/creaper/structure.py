"""How a rendered song is built over time: which bars repeat, how long a loop runs
unchanged, and whether the sections lift and fall the way their names promise.

Each bar becomes a fingerprint (energy in 24 bands, in 8 slices through the bar, so
both the sound and the rhythm count) and every bar is compared with every other one.
A song that is one loop repeated scores close to 1 on near-duplicate bars; a song
whose parts develop scores low.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import signal

from . import analysis
from . import arrange_tools  # the module, not its names: it may still be loading (circular import)

N_BANDS = 24
SLICES_PER_BAR = 8
# Two bars this alike (cosine of what sets them apart from the average bar) are the
# same bar played again; so are two bars this close outright (RMS difference of their
# fingerprints, dB), which catches a loop whose repeats differ only by humanised
# velocities and timing (their differences point anywhere, so the cosine misses them).
SAME_BAR = 0.97
SAME_BAR_DB = 1.5
HOP_S = 0.02
MARKER_TOLERANCE_S = 0.002
AVERAGE_BAR_DB = 0.25   # a bar within this (RMS over its fingerprint) of the average bar is that bar
# Verdict thresholds: share of bars that are a copy of another bar (not the next one).
REPETITIVE_SHARE = 0.4
LOOP_RUN_BARS = 16
SHORT_FOR_FORM = 0.75   # under this share of the genre's form bar count is "short"
LIFT_LU = 1.0           # a section whose name promises more energy should be at least this louder


def bar_starts(tempo_map: dict, end_seconds: float) -> list[float]:
    """Start time (s) of every bar up to end_seconds, from get_tempo_map's answer.
    A ramp is taken at its average tempo: close enough for bar-sized windows."""
    changes = sorted(tempo_map.get("changes") or [], key=lambda c: c["position"]["seconds"])
    bpm = float(tempo_map.get("start_tempo_bpm") or 120)
    num, den = (int(x) for x in str(tempo_map.get("start_time_signature") or "4/4").split("/"))
    t, k = 0.0, 0
    # The first marker usually sits at 0 and restates the start; each applies as we pass it.
    out: list[float] = []
    while t < end_seconds - 1e-6:
        # The bridge reports marker times to the millisecond, so one on this bar line can
        # read up to half a millisecond after it.
        while k < len(changes) and changes[k]["position"]["seconds"] <= t + MARKER_TOLERANCE_S:
            c = changes[k]
            bpm = float(c.get("bpm") or bpm)
            if c.get("time_signature"):
                num, den = (int(x) for x in c["time_signature"].split("/"))
            if c.get("ramp_to_next") and k + 1 < len(changes):
                bpm = (bpm + float(changes[k + 1].get("bpm") or bpm)) / 2
            k += 1
        out.append(t)
        # A change inside a bar (rare: they sit on bar lines) takes effect at the next one.
        t += num * 4 / den * 60 / bpm
    return out


def qn_to_seconds(tempo_map: dict, qn: float) -> float:
    """Project time (s) of a quarter-note position, from get_tempo_map's answer (each
    marker's position carries its seconds and qn). Ramps count at their start tempo."""
    seconds, at_qn = 0.0, 0.0
    bpm = float(tempo_map.get("start_tempo_bpm") or 120)
    for c in sorted(tempo_map.get("changes") or [], key=lambda c: c["position"].get("qn", 0)):
        mqn = c["position"].get("qn")
        if mqn is None or mqn > qn:
            break
        seconds, at_qn, bpm = c["position"]["seconds"], mqn, float(c.get("bpm") or bpm)
    return seconds + (qn - at_qn) * 60 / bpm


def bar_features(mono: np.ndarray, fs: float, starts: list[float], end_seconds: float) -> np.ndarray:
    """One fingerprint per bar: log energy in N_BANDS bands (40 Hz-12 kHz) in each of
    SLICES_PER_BAR slices through the bar. Rows are bars."""
    hop = max(1, int(HOP_S * fs))
    nperseg = 4096 if fs >= 32000 else 2048
    if mono.size < nperseg:
        return np.zeros((0, N_BANDS * SLICES_PER_BAR))
    f, times, z = signal.stft(mono, fs=fs, nperseg=nperseg, noverlap=nperseg - hop, boundary=None, padded=False)
    power = np.abs(z) ** 2
    edges = np.geomspace(40, min(12000, fs / 2 - 1), N_BANDS + 1)
    bands = np.stack([power[(f >= lo) & (f < hi)].sum(axis=0) for lo, hi in zip(edges, edges[1:])])
    bands = 10 * np.log10(bands + 1e-12)
    rows = []
    bounds = list(starts) + [end_seconds]
    for a, b in zip(bounds, bounds[1:]):
        slices = np.linspace(a, b, SLICES_PER_BAR + 1)
        row = []
        for s0, s1 in zip(slices, slices[1:]):
            mask = (times >= s0) & (times < s1)
            if not mask.any():  # a slice shorter than a hop: take the nearest frame
                mask = np.zeros(times.size, dtype=bool)
                mask[min(times.size - 1, int(np.searchsorted(times, (s0 + s1) / 2)))] = True
            row.append(bands[:, mask].mean(axis=1))
        rows.append(np.concatenate(row))
    return np.array(rows)


def similarity(features: np.ndarray, keep: np.ndarray | None = None) -> np.ndarray:
    """Cosine similarity of every bar with every other, on what sets each bar apart
    from the song's average bar: the tone every bar shares (the pad, the mix's
    balance) would otherwise make any two bars of a song look alike. keep: the bars
    the average is taken over (silent ones would make all the music look alike)."""
    rows = features if keep is None or not keep.any() else features[keep]
    x = features - rows.mean(axis=0, keepdims=True)
    norm = np.linalg.norm(x, axis=1)
    s = (x / (norm[:, None] + 1e-9)) @ (x / (norm[:, None] + 1e-9)).T
    # Bars that hardly differ from the average bar (a song that is one bar repeated)
    # have no direction to compare: they are the same bar.
    plain = norm / math.sqrt(max(1, x.shape[1])) < AVERAGE_BAR_DB
    s[np.ix_(plain, plain)] = 1.0
    # Close outright counts as the same bar (scored just over SAME_BAR).
    sq = np.sum(features ** 2, axis=1)
    dist = np.sqrt(np.maximum(0.0, sq[:, None] + sq[None, :] - 2 * features @ features.T) / max(1, features.shape[1]))
    return np.where(dist < SAME_BAR_DB, np.maximum(s, SAME_BAR + 0.01), s)


def repetition(features: np.ndarray, silent: np.ndarray | None = None) -> dict:
    """Near-duplicate bars and the longest unchanged loop.
    - near_duplicate_share: bars that have a copy elsewhere in the song, not counting
      the bar right next to them (a held chord over two bars isn't a loop).
    - longest_loop_bars: the longest stretch where every 4-bar block is a copy of the
      one before (16 = the same 4 bars played four times running).
    Silent bars are left out."""
    n = features.shape[0]
    if n < 8:
        return {"bars": n, "note": "too short to judge repetition (needs 8 bars)"}
    keep = np.ones(n, dtype=bool) if silent is None else ~silent
    s = similarity(features, keep)
    full = s.copy()
    np.fill_diagonal(s, -1)
    idx = np.arange(n - 1)
    s[idx, idx + 1] = s[idx + 1, idx] = -1
    s[:, ~keep] = -1
    best = s.max(axis=1)[keep]
    # A 4-bar block repeats the one before when each of its bars repeats the bar 4 earlier.
    blocks = n // 4
    same = [False] + [all(keep[4 * i + j] and full[4 * i + j, 4 * (i - 1) + j] > SAME_BAR for j in range(4))
                      for i in range(1, blocks)]
    run = longest = 0
    for i, s_ in enumerate(same):
        run = run + 1 if s_ else 0
        longest = max(longest, run)
    return {"bars": int(keep.sum()),
            "near_duplicate_share": round(float((best > SAME_BAR).mean()), 2) if best.size else 0.0,
            "longest_loop_bars": (longest + 1) * 4 if longest else 4}


def section_table(sections: list[dict], starts: list[float], features: np.ndarray, audio: np.ndarray,
                  fs: float, offset: float, silent: np.ndarray | None = None) -> list[dict]:
    """Per section: loudness, the energy its name promises (1 calm .. 4 peak, as
    add_transitions reads it), and whether it plays like an earlier section bar for bar.
    sections: [{'name', 'start', 'end'}] in seconds (project time); offset: the render's
    start in project time."""
    out: list[dict] = []
    s = similarity(features, None if silent is None else ~silent) if features.shape[0] else np.zeros((0, 0))
    bar_index = np.asarray(starts)
    for sec in sections:
        a, b = int(max(0, (sec["start"] - offset) * fs)), int(min(audio.shape[0], (sec["end"] - offset) * fs))
        if b - a < int(0.4 * fs):
            continue
        loud = analysis.loudness(audio[a:b], fs)
        row = {"name": sec["name"], "bars": None, "lufs": loud.get("integrated_lufs"), "energy": arrange_tools.energy(sec["name"])}
        first = int(np.searchsorted(bar_index, sec["start"] - offset - 1e-3))
        last = int(np.searchsorted(bar_index, sec["end"] - offset - 1e-3))
        row["bars"] = max(0, last - first)
        row["_bars"] = (first, min(last, s.shape[0]))
        # Bar for bar against each earlier section: a chorus that is the first chorus again.
        for prev in out:
            p0, p1 = prev["_bars"]
            span = min(p1 - p0, row["_bars"][1] - first)
            if span >= 2:
                alike = float(np.mean([s[first + i, p0 + i] for i in range(span)]))
                if alike > SAME_BAR and alike > row.get("_alike", 0):
                    row["_alike"], row["same_as"] = alike, prev["name"]
        out.append(row)
    for row in out:
        row.pop("_bars", None)
        row.pop("_alike", None)
    return out


def arc_problems(table: list[dict]) -> list[str]:
    """Where the loudness doesn't follow the energy the section names promise."""
    problems = []
    for prev, nxt in zip(table, table[1:]):
        if prev.get("lufs") is None or nxt.get("lufs") is None:
            continue
        lift = nxt["lufs"] - prev["lufs"]
        if nxt["energy"] > prev["energy"] and lift < LIFT_LU:
            problems.append(f"{nxt['name']} should lift from {prev['name']} but is {lift:+.1f} LU")
        elif nxt["energy"] < prev["energy"] and lift > -LIFT_LU:
            problems.append(f"{nxt['name']} should drop from {prev['name']} but is {lift:+.1f} LU")
    return problems


def judge(rep: dict, table: list[dict], bars: int, form_bars: int | None) -> list[str]:
    """Plain-language findings for Claude to act on."""
    findings = []
    share = rep.get("near_duplicate_share")
    if share is not None and share >= REPETITIVE_SHARE:
        findings.append(f"{round(share * 100)}% of the bars are copies of other bars: it will read as a loop. Give each "
                        "section its own version of the parts (another seed, rewritten bars, a new comping rhythm or "
                        "bass line) instead of copying items")
    if rep.get("longest_loop_bars", 0) >= LOOP_RUN_BARS:
        findings.append(f"{rep['longest_loop_bars']} bars run with the same 4 bars repeating: change something at least "
                        "every 8 bars (a part in or out, a fill, a variation)")
    for row in table:
        if row.get("same_as"):
            findings.append(f"{row['name']} plays like {row['same_as']} bar for bar: vary it (a lift, new parts, a "
                            "different groove or voicing)")
    findings += arc_problems(table)
    if form_bars and bars < SHORT_FOR_FORM * form_bars:
        findings.append(f"it's {bars} of the {form_bars} bars the genre's form runs to: build the full form")
    return findings


def form_bars(genre) -> int | None:
    return sum(n for _, n in genre.form) if getattr(genre, "form", None) else None


def bar_levels(mono: np.ndarray, fs: float, starts: list[float], end_seconds: float) -> np.ndarray:
    """Each bar's mean level (dB)."""
    bounds = list(starts) + [end_seconds]
    levels = []
    for a, b in zip(bounds, bounds[1:]):
        seg = mono[int(a * fs): int(b * fs)]
        levels.append(10 * math.log10(float(np.mean(np.square(seg))) + 1e-20) if seg.size else -200.0)
    return np.array(levels)


def silent_bars(mono: np.ndarray, fs: float, starts: list[float], end_seconds: float, below_db: float = 50.0) -> np.ndarray:
    """Bars more than below_db under the loudest bar (silence, a tail)."""
    levels = bar_levels(mono, fs, starts, end_seconds)
    return levels < levels.max() - below_db if levels.size else np.zeros(0, dtype=bool)


TAIL_DB = 20.0  # trailing bars this far under the median bar are a ring-out, not more song


def tail_bars(mono: np.ndarray, fs: float, starts: list[float], end_seconds: float) -> int:
    """How many bars at the end only ring out (a render to the project's end carries the
    last notes' release past the music)."""
    levels = bar_levels(mono, fs, starts, end_seconds)
    if levels.size < 3:
        return 0
    floor = float(np.median(levels)) - TAIL_DB
    n = 0
    while n < levels.size - 2 and levels[levels.size - 1 - n] < floor:
        n += 1
    return n
