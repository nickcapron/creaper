"""Listening to an instrument: what each note actually sounds like.

creaper plays notes through an instrument offline, renders the result, and
measures each note: level, envelope (attack, decay, sustain, release), pitch,
brightness, noisiness and transients. From that it can tell what a drum kit has
on each key (kick, snare, clap, hats, cymbals, toms, rim, percussion) or describe
a synth patch (its range, whether it follows pitch, transposition, envelope, tone).
"""

from __future__ import annotations

import math

import numpy as np

SILENT_DB = -55.0


def _db(x: float) -> float:
    return 20 * math.log10(max(x, 1e-12))


def note_freq(pitch: int) -> float:
    return 440.0 * 2 ** ((pitch - 69) / 12)


def _pitch(x: np.ndarray, fs: float, fmin: float = 35.0, fmax: float = 2500.0) -> tuple[float | None, float]:
    """Fundamental by normalized autocorrelation: (Hz, clarity 0-1)."""
    n = len(x)
    if n < int(fs / fmin) * 2:
        return None, 0.0
    x = x - x.mean()
    energy = float(np.dot(x, x))
    if energy <= 1e-12:
        return None, 0.0
    spec = np.fft.rfft(x, 2 * n)
    ac = np.fft.irfft(spec * np.conj(spec))[:n]
    ac /= ac[0]
    lo, hi = int(fs / fmax), min(n - 1, int(fs / fmin))
    # Search past the first dip below zero, so a smooth low tone isn't read as a tiny lag.
    neg = np.where(ac[1:hi] < 0)[0]
    if neg.size:
        lo = max(lo, int(neg[0]) + 1)
    if hi <= lo + 2:
        return None, 0.0
    seg = ac[lo:hi]
    i = int(np.argmax(seg))
    clarity = float(seg[i])
    lag = lo + i
    if 1 <= lag < len(ac) - 1:  # parabolic interpolation
        a, b, c = ac[lag - 1], ac[lag], ac[lag + 1]
        denom = a - 2 * b + c
        if abs(denom) > 1e-12:
            shift = 0.5 * (a - c) / denom
            if abs(shift) < 1:
                lag = lag + shift
    if lag <= 0:
        return None, 0.0
    f0 = float(fs / lag)
    if not fmin * 0.9 <= f0 <= fmax * 1.1:
        return None, 0.0
    return f0, clarity


def features(x: np.ndarray, fs: float, note_off: float | None = None) -> dict:
    """Measurements of one note's audio (mono), starting at the note-on."""
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    out: dict = {"peak_db": round(_db(peak), 1)}
    if _db(peak) < SILENT_DB:
        out["silent"] = True
        return out
    hop = max(1, int(fs * 0.005))
    frames = len(x) // hop
    env = np.sqrt(np.mean(np.square(x[: frames * hop]).reshape(frames, hop), axis=1)) + 1e-12
    p = int(np.argmax(env))
    env_db = 20 * np.log10(env / env[p])
    # How late the sound starts after the note-on (silence at the start of a sample,
    # or unreported plugin latency), then the attack measured from there.
    start_frames = np.where(env_db >= -40)[0]
    start = int(start_frames[0]) if start_frames.size else 0
    out["starts_late_ms"] = round(start * hop / fs * 1000, 1)
    reach = np.where(env_db >= -3)[0]
    out["attack_ms"] = round(((reach[0] if reach.size else p) - start) * hop / fs * 1000, 1)
    held_end = int(note_off * fs / hop) if note_off is not None else frames
    below = np.where(env_db[p:held_end] < -30)[0] if held_end > p else np.array([])
    if below.size:
        out["decay_s"] = round((below[0] * hop) / fs, 3)
    else:
        rest = np.where(env_db[p:] < -30)[0]
        # Still sounding while held (a sustained sound) unless it's a short note past its end.
        out["decay_s"] = None if note_off is not None else (round(rest[0] * hop / fs, 3) if rest.size else None)
    if note_off is not None:
        held = int(note_off * fs / hop)
        if p < held - 4 < frames:
            out["sustain_db"] = round(float(np.mean(env_db[max(p, held - 20):held])), 1)
            after = np.where(env_db[held:] < -40)[0]
            out["release_s"] = round(after[0] * hop / fs, 3) if after.size else None
    # Spectrum of the first 200 ms after the attack.
    a = p * hop
    win = x[a: a + int(0.2 * fs)]
    if len(win) < 256:
        win = x[: int(0.2 * fs)]
    w = win * np.hanning(len(win))
    spec = np.abs(np.fft.rfft(w, 8192)) ** 2
    freqs = np.fft.rfftfreq(8192, 1 / fs)
    total = float(spec[(freqs >= 20) & (freqs <= 20000)].sum()) or 1e-12

    def band(lo: float, hi: float) -> float:
        return float(spec[(freqs >= lo) & (freqs < hi)].sum()) / total

    out["bands"] = {"sub": round(band(20, 90), 3), "low": round(band(90, 250), 3), "low_mid": round(band(250, 800), 3),
                    "mid": round(band(800, 3000), 3), "high": round(band(3000, 8000), 3), "air": round(band(8000, 20000), 3)}
    audible = (freqs >= 20) & (freqs <= 20000)
    out["centroid_hz"] = round(float((freqs[audible] * spec[audible]).sum() / total))
    f0, clarity = _pitch(x[a + int(0.02 * fs): a + int(0.25 * fs)], fs, fmin=25.0)
    out["clarity"] = round(clarity, 2)
    if f0 and clarity > 0.5:
        out["pitch_hz"] = round(f0, 1)
    # Pitch glide: kicks and toms drop fast at the start; bass and synth notes hold.
    early, c1 = _pitch(x[a: a + int(0.07 * fs)], fs, fmin=30.0)
    late, c2 = _pitch(x[a + int(0.09 * fs): a + int(0.22 * fs)], fs, fmin=30.0)
    if early and late and c1 > 0.5 and c2 > 0.5:
        out["pitch_glide"] = round(early / late, 2)
    # Separate bursts in the first 80 ms (claps have several), each with a dip between.
    fine = max(1, int(fs * 0.002))
    onset_frames = np.where(env_db >= -20)[0]
    onset = int(onset_frames[0]) * hop if onset_frames.size else a
    head = x[onset: onset + int(0.08 * fs)]
    bursts = 1
    if len(head) > fine * 10:
        n = len(head) // fine
        e = np.sqrt(np.mean(np.square(head[: n * fine]).reshape(n, fine), axis=1))
        e = np.convolve(e, np.ones(2) / 2, mode="same")
        top = e.max()
        peaks, i = [], 1
        while i < n - 1:
            if e[i] >= 0.4 * top and e[i] >= e[i - 1] and e[i] >= e[i + 1]:
                if not peaks or (i - peaks[-1] >= 3 and e[peaks[-1]:i].min() < 0.55 * min(e[i], e[peaks[-1]])):
                    peaks.append(i)
                elif e[i] > e[peaks[-1]]:
                    peaks[-1] = i
            i += 1
        bursts = max(1, len(peaks))
    out["bursts"] = bursts
    return out


DRUM_KINDS = ("kick", "snare", "clap", "rim", "closed hat", "open hat", "crash", "ride", "tom", "shaker",
              "cowbell", "percussion")


def classify_drum(f: dict) -> tuple[str, float]:
    """A drum type and a rough confidence (0-1) from features()."""
    if f.get("silent"):
        return "silent", 1.0
    b = f["bands"]
    sub, low, low_mid, mid = b["sub"], b["low"], b["low_mid"], b["mid"]
    high = b["high"] + b["air"]
    centroid = f["centroid_hz"]
    clarity = f.get("clarity", 0.0)
    noise = 1 - clarity
    decay = f["decay_s"] if f["decay_s"] is not None else 3.0
    attack = f["attack_ms"]
    pitch = f.get("pitch_hz")
    bursts = f.get("bursts", 1)
    glide = f.get("pitch_glide")
    if high >= 0.6 and centroid >= 4500:
        if attack >= 12 and 0.08 <= decay < 0.45:
            return "shaker", 0.65
        if decay < 0.22:
            return "closed hat", 0.85
        if decay < 1.4:
            return "open hat", 0.75
        return ("ride", 0.55) if clarity > 0.3 else ("crash", 0.75)
    if decay >= 1.2 and centroid < 4500 and clarity > 0.5:
        return "tonal", 0.6  # sustained pitched note: a bass, keys or pad, not a drum
    if sub >= 0.35 or (sub + low >= 0.6 and pitch is not None and pitch < 75):
        if (glide is None or glide < 1.08) and clarity > 0.85 and decay > 0.15 and centroid > 90:
            return "tonal", 0.5  # steady pitch: more like a bass note than a kick
        return "kick", round(min(0.95, 0.6 + sub * 0.35 - centroid / 2000), 2)
    if bursts >= 3 and mid + low_mid >= 0.4 and noise > 0.5:
        return "clap", 0.7
    if low >= 0.4 and clarity > 0.5 and centroid < 1200:
        return "tom", 0.75
    if decay < 0.09 and centroid >= 600:
        return "rim", 0.65
    if clarity > 0.6 and 350 <= centroid <= 3500 and sub + low < 0.2:
        return "cowbell", 0.55
    body_and_snap = low + low_mid >= 0.2 and high + mid >= 0.3 and clarity < 0.9
    if 900 <= centroid <= 7500 and decay < 0.9 and (noise > 0.4 or body_and_snap):
        return "snare", 0.7 if low + low_mid > 0.05 else 0.55
    if high >= 0.4:
        return "shaker", 0.4
    return "percussion", 0.3


def tracks_pitch(results: list[dict]) -> tuple[bool, int | None]:
    """Whether the detected pitch follows the played note, and the offset (semitones,
    e.g. +12 if the patch sounds an octave up)."""
    offsets = []
    for r in results:
        f0 = r.get("pitch_hz")
        if f0 and r.get("clarity", 0) > 0.6:
            offsets.append(12 * math.log2(f0 / note_freq(r["pitch"])))
    if len(offsets) < max(3, len(results) // 3):
        return False, None
    rounded = [round(o) for o in offsets]
    common = max(set(rounded), key=rounded.count)
    agree = sum(1 for o in offsets if abs(o - common) < 0.6)
    return agree >= 0.6 * len(offsets), common


def choose_lanes(results: list[dict], gm_hint: bool = True) -> dict[str, int]:
    """The best key for each drum lane, toms split low/mid/high by pitch."""
    by_kind: dict[str, list[tuple[float, dict]]] = {}
    for r in results:
        if r["kind"] in ("silent", "percussion", "tonal"):
            continue
        near_gm = abs(r["pitch"] - _GM.get(r["kind"], r["pitch"])) * 0.005 if gm_hint else r["pitch"] * 0.001
        by_kind.setdefault(r["kind"], []).append((r["confidence"] - near_gm, r))
    lanes: dict[str, int] = {}
    for kind, items in by_kind.items():
        if kind == "tom":
            toms = sorted((r for _, r in items), key=lambda r: r.get("pitch_hz") or r["centroid_hz"])
            if len(toms) == 1:
                lanes["mid tom"] = toms[0]["pitch"]
            else:
                lanes["low tom"] = toms[0]["pitch"]
                lanes["high tom"] = toms[-1]["pitch"]
                if len(toms) >= 3:
                    lanes["mid tom"] = toms[len(toms) // 2]["pitch"]
            continue
        best = max(items, key=lambda t: t[0])[1]
        lanes[kind] = best["pitch"]
    return lanes


_GM = {"kick": 36, "snare": 38, "clap": 39, "rim": 37, "closed hat": 42, "open hat": 46, "crash": 49, "ride": 51,
       "tom": 45, "shaker": 70, "cowbell": 56}


def describe_patch(results: list[dict]) -> dict:
    sounding = [r for r in results if not r.get("silent")]
    if not sounding:
        return {"sounding": False}
    follows, offset = tracks_pitch(sounding)
    attacks = [r["attack_ms"] for r in sounding]
    decays = [r["decay_s"] for r in sounding]
    sustains = [r["sustain_db"] for r in sounding if r.get("sustain_db") is not None]
    centroid = float(np.median([r["centroid_hz"] for r in sounding]))
    attack = float(np.median(attacks))
    sustain = float(np.median(sustains)) if sustains else None
    held = sum(1 for d in decays if d is None)
    words = []
    words.append("bright" if centroid > 3000 else ("dark" if centroid < 900 else "mid-toned"))
    if attack > 80:
        words.append("slow attack (pad/swell)")
    elif attack < 10:
        words.append("sharp attack")
    if sustain is not None and sustain > -10:
        words.append("sustained")
    elif held == 0:
        words.append("plucky/decaying")
    if np.median([1 - r.get("clarity", 0) for r in sounding]) > 0.6:
        words.append("noisy")
    return {
        "sounding": True,
        "lowest_sounding": sounding[0]["note"], "highest_sounding": sounding[-1]["note"],
        "follows_pitch": follows,
        "transposition_semitones": offset if follows else None,
        "median_attack_ms": round(attack, 1),
        "median_sustain_db": round(sustain, 1) if sustain is not None else None,
        "median_brightness_hz": round(centroid),
        "character": ", ".join(words),
        "looks_like": "a pitched instrument" if follows else "a drum kit, one-shot or unpitched sound",
    }


# ------------------------------------------------------------ kit mapping

GM_KEYS = {"kick": (36, 35), "snare": (38, 40), "clap": (39,), "rim": (37,), "closed hat": (42, 44),
           "open hat": (46,), "crash": (49, 57, 52, 55), "ride": (51, 59, 53), "tom": (41, 43, 45, 47, 48, 50),
           "cowbell": (56,), "shaker": (70, 69, 54)}


def _z(values: list[float]) -> list[float]:
    m = float(np.mean(values))
    s = float(np.std(values)) or 1.0
    return [(v - m) / s for v in values]


# Scoring weights fitted by random search on kits built from real, labelled drum
# samples, half the sample banks for fitting and half held out. Held out: about 88%
# of core lanes right when the kit follows General MIDI, about 50% on custom layouts.
W = {
    "k_low": 1.27, "k_bright": 2.23, "k_long": 0.48, "k_glide": 0.39, "s_bright": 0.92, "s_center": 0.0,
    "s_noise": 1.27, "s_low": 0.0, "s_long": 0.44, "s_dec": 0.02, "s_burst": 1.6, "s_mid": 0.0,
    "c_burst": 0.86, "c_noise": 1.24, "c_bright": 0.11, "r_long": 1.51, "r_bright": 2.16, "h_bright": 2.44,
    "h_high": 0.32, "h_long": 1.11, "h_noise": 0.82, "o_bright": 0.53, "o_high": 0.35, "o_long": 0.03,
    "o_toolong": 0.49, "x_bright": 0.79, "x_long": 1.26, "x_noise": 0.68, "t_clar": 1.2, "t_bright": 0.81,
    "t_low": 0.5, "gm_main": 3.57, "gm_alt": 0.1,
}


def _looks_gm(keys: list[dict], scores: dict[str, list[float]]) -> bool:
    """Whether the kit is laid out as General MIDI: at least two of these hold up: the
    kit's most kick-like sound is on C1/B0; a better-than-most snare is on D1/E1; a
    better-than-most closed hat is on F#1/G#1. Decided once for the whole kit, so one stray sound can't fool it."""
    votes = 0
    for lane, gm_keys in (("kick", (36, 35)), ("snare", (38, 40)), ("closed hat", (42, 44))):
        raw = scores[lane]
        if lane == "kick":
            ok = any(k["pitch"] in gm_keys and raw[i] >= max(raw) for i, k in enumerate(keys))
        else:
            ok = any(k["pitch"] in gm_keys and raw[i] >= float(np.median(raw)) for i, k in enumerate(keys))
        votes += ok
    return votes >= 2


def map_kit(keys: list[dict], gm: bool = True) -> tuple[dict[str, int], dict[int, tuple[str, float]]]:
    """Assigns drum lanes for a whole kit. Each sound is compared with the rest of the
    kit (the darkest punchy one is the kick, the brightest short one the closed hat),
    which holds up across lo-fi and hi-fi kits, and keys on the General MIDI layout
    that most commercial kits follow get a bonus. Returns (lane -> pitch, pitch ->
    (label, confidence))."""
    keys = [k for k in keys if not k.get("silent")]
    if not keys:
        return {}, {}
    n = len(keys)
    bright = _z([math.log(max(k["centroid_hz"], 20)) for k in keys])
    decay = _z([math.log(max(k["decay_s"] if k["decay_s"] is not None else 2.5, 0.01)) for k in keys])
    lowness = _z([k["bands"]["sub"] + k["bands"]["low"] for k in keys])
    highness = _z([k["bands"]["high"] + k["bands"]["air"] for k in keys])
    mid = _z([k["bands"]["mid"] + k["bands"]["low_mid"] for k in keys])
    scores: dict[str, list[float]] = {}
    for i, k in enumerate(keys):
        clar = k.get("clarity", 0.0)
        bursts = k.get("bursts", 1)
        glide = k.get("pitch_glide") or 1.0
        long_ = decay[i]
        w = W
        s = {
            "kick": w["k_low"] * lowness[i] - w["k_bright"] * bright[i] - w["k_long"] * max(0.0, long_ - 1.0)
                    + (w["k_glide"] if glide > 1.1 else 0),
            "snare": -w["s_bright"] * abs(bright[i] - w["s_center"]) + w["s_noise"] * (1 - clar)
                     - w["s_low"] * lowness[i] - w["s_long"] * abs(long_ - w["s_dec"]) - (w["s_burst"] if bursts >= 3 else 0)
                     + w["s_mid"] * mid[i],
            "clap": (w["c_burst"] if bursts >= 3 else -w["c_burst"] / 2) + w["c_noise"] * (1 - clar)
                    - w["c_bright"] * abs(bright[i]) - 0.3 * lowness[i],
            "rim": -w["r_long"] * long_ - w["r_bright"] * abs(bright[i] - 0.3) - 0.4 * lowness[i] + 0.3 * clar,
            "closed hat": w["h_bright"] * bright[i] + w["h_high"] * highness[i] - w["h_long"] * long_ + w["h_noise"] * (1 - clar),
            "open hat": w["o_bright"] * bright[i] + w["o_high"] * highness[i] + w["o_long"] * long_
                        - w["o_toolong"] * max(0.0, long_ - 1.4),
            "crash": w["x_bright"] * bright[i] + 0.4 * highness[i] + w["x_long"] * long_ + w["x_noise"] * (1 - clar),
            "ride": 0.8 * bright[i] + 1.0 * long_ + 0.6 * clar,
            "tom": w["t_clar"] * clar - w["t_bright"] * bright[i] + w["t_low"] * lowness[i] * (1 if lowness[i] < 1.5 else -1)
                   - 0.3 * abs(long_) + (0.3 if glide > 1.03 else 0),
        }
        for lane, value in s.items():
            scores.setdefault(lane, [0.0] * n)[i] = value
    if gm and _looks_gm(keys, scores):
        for lane, raw in scores.items():
            gm_keys = GM_KEYS.get(lane, ())
            for i, k in enumerate(keys):
                if k["pitch"] in gm_keys[:1]:
                    raw[i] += W["gm_main"]
                elif k["pitch"] in gm_keys:
                    raw[i] += W["gm_alt"]
    lanes: dict[str, int] = {}
    labels: dict[int, tuple[str, float]] = {}
    taken: set[int] = set()
    order = ("kick", "closed hat", "snare", "open hat", "crash", "clap", "ride", "rim")
    for lane in order:
        ranked = sorted((v, i) for i, v in enumerate(scores[lane]) if i not in taken)
        if not ranked:
            break
        best_v, best_i = ranked[-1]
        runner = ranked[-2][0] if len(ranked) > 1 else best_v - 1
        alone = classify_drum(keys[best_i])[0]
        # Only claim optional lanes when the sound really fits (its own type agrees, or it stands out).
        if lane not in ("kick", "snare", "closed hat"):
            compatible = {"open hat": {"open hat", "crash", "closed hat", "shaker", "ride"},
                          "crash": {"crash", "open hat", "ride"}, "ride": {"ride", "crash", "open hat", "cowbell"},
                          "clap": {"clap", "snare"}, "rim": {"rim", "cowbell", "snare", "percussion"}}[lane]
            if alone not in compatible and best_v - runner < 0.8:
                continue
        lanes[lane] = keys[best_i]["pitch"]
        labels[keys[best_i]["pitch"]] = (lane, round(max(0.3, min(0.95, 0.55 + (best_v - runner) / 3)), 2))
        taken.add(best_i)
    toms = [i for i in range(n) if i not in taken and classify_drum(keys[i])[0] in ("tom", "kick", "tonal", "percussion")
            and scores["tom"][i] > 0.2]
    toms.sort(key=lambda i: keys[i].get("pitch_hz") or keys[i]["centroid_hz"])
    names = {1: ("mid tom",), 2: ("low tom", "high tom"), 3: ("low tom", "mid tom", "high tom")}
    picked = toms if len(toms) <= 3 else [toms[0], toms[len(toms) // 2], toms[-1]]
    for lane, i in zip(names.get(len(picked), ()), picked):
        lanes[lane] = keys[i]["pitch"]
        labels[keys[i]["pitch"]] = (lane, 0.5)
        taken.add(i)
    for i, k in enumerate(keys):
        if i not in taken:
            kind, conf = classify_drum(k)
            labels[k["pitch"]] = (kind, min(conf, 0.5))
    return lanes, labels


def follows_gm(lanes: dict[str, int]) -> bool:
    """Whether the core sounds sit where General MIDI puts them."""
    hits = sum(1 for lane, keys in (("kick", (35, 36)), ("snare", (38, 40)), ("closed hat", (42, 44)))
               if lanes.get(lane) in keys)
    return hits >= 2
