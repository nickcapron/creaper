"""The user's sample library: an index of their sample folders, and analysis of
individual files (drum type, pitch, loop tempo, key).

The index reads file names and headers only, so it's quick even for big libraries;
audio is analysed on demand and the result cached in the index.
"""

from __future__ import annotations

import json
import math
import os
import re
import threading
import time
import uuid
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

from . import harmony, listen, theory

AUDIO_EXTENSIONS = {".wav", ".aif", ".aiff", ".flac", ".ogg", ".mp3"}
MAX_INDEX_S = 300   # seconds an index build may walk before it stops
MAX_FILES = 60000

ROLE_WORDS = {
    "kick": ("kick", "bd", "bassdrum", "kik"), "snare": ("snare", "sd", "snr"), "clap": ("clap", "clp"),
    "closed hat": ("hhclose", "closedhat", "chh", "closed", "hihat", "hat", "hh"), "open hat": ("hhopen", "openhat", "ohh", "open"),
    "crash": ("crash",), "ride": ("ride",), "cymbal": ("cymbal", "cym"), "tom": ("tom", "toms"), "rim": ("rim", "rimshot", "sidestick"),
    "shaker": ("shaker", "shaka", "maraca", "cabasa"), "tambourine": ("tamb", "tambourine"), "cowbell": ("cowbell",),
    "percussion": ("perc", "percussion", "conga", "bongo", "timbale", "clave", "woodblock"), "808": ("808",),
    "bass": ("bass", "sub", "reese"), "pad": ("pad", "pads", "atmos", "drone"), "lead": ("lead", "leads"),
    "keys": ("keys", "piano", "rhodes", "organ", "epiano"), "pluck": ("pluck", "plucks"), "chord": ("chord", "chords", "stab"),
    "arp": ("arp", "arps"), "vocal": ("vocal", "vox", "voice", "chop", "choir"), "fx": ("fx", "riser", "impact", "sweep", "noise", "downlifter", "uplifter"),
    "guitar": ("guitar", "gtr"), "strings": ("strings", "string", "violin", "cello"), "brass": ("brass", "horn", "trumpet", "sax"),
    "loop": ("loop", "loops", "groove", "break", "breaks"),
}
DRUM_ROLES = {"kick", "snare", "clap", "closed hat", "open hat", "crash", "ride", "cymbal", "tom", "rim", "shaker",
              "tambourine", "cowbell", "percussion", "808"}
# What an .sfz instrument is, from its file and folder names (VSCO's "CelloEnsSusVib",
# FreePats' "EGuitarFSBS", AVL's "Drumkits").
INSTRUMENT_WORDS = {
    "guitar": ("guitar", "gtr"), "strings": ("violin", "viola", "cello", "contrabass", "strings", "string"),
    "brass": ("horn", "trumpet", "trombone", "tuba", "brass"),
    "woodwinds": ("flute", "piccolo", "oboe", "clarinet", "bassoon", "sax", "woodwind", "woodwinds"),
    "drum kit": ("drumkit", "drumkits", "drums", "kit"),
    "percussion": ("timpani", "glockenspiel", "marimba", "xylophone", "vibraphone", "percussion", "perc", "bells"),
    "keys": ("piano", "upright", "organ", "rhodes", "harpsichord", "celesta"), "harp": ("harp",),
    "choir": ("choir", "chorus", "voices"), "bass": ("bass", "ebass", "bassguitar"),
}


INSTRUMENT_EXCLUDES = {"keys": ("bass",)}   # an "UprightBass" is a bass, not an upright piano


def instrument_kinds(name: str, folder: str = "") -> list[str]:
    """Whole words only: 'harp' isn't in 'Harpsichord', 'bass' isn't in 'bassoon'. A key
    of several words ('bass guitar') has to appear as those words in a row."""
    words = _words(name) + _words(folder)
    pairs = {" ".join(words[i:i + 2]) for i in range(len(words) - 1)}
    out = []
    for kind, keys in INSTRUMENT_WORDS.items():
        if any((k in words) if " " not in k else (k in pairs) for k in keys):
            if not any(x in words for x in INSTRUMENT_EXCLUDES.get(kind, ())):
                out.append(kind)
    return out


def playable_sfz(path: str) -> bool:
    """Whether creaper can build an .sfz: its samples are all there (Arturia's own .sfz
    files name samples a partial install never downloaded) and it fits the sampler."""
    from . import sfz

    try:
        sfz.load(path, loops=False)   # no WAV reads: loop points are for building, not listing
        return True
    except Exception:  # noqa: BLE001 - missing samples, too many zones, unreadable
        return False


def instrument_matches(entry: dict, text: str | None, role: str | None) -> bool:
    """Whether an .sfz instrument answers a find_samples search: its words, and its kind
    for the role (any drum role finds the drum kits, 'vocal' the choirs)."""
    if text:
        hay = " ".join(_words(entry["name"]) + _words(entry["folder"]) + entry["kinds"])
        if not all(w in hay for w in _words(text)):
            return False
    if role and not _wanted_kinds(role) & set(entry["kinds"]):
        return False
    return bool(text or role)


def _wanted_kinds(role: str) -> set[str]:
    r = role.lower()
    want = {r, {"drums": "drum kit", "drum": "drum kit", "vocal": "choir", "woodwind": "woodwinds"}.get(r, r)}
    if r in DRUM_ROLES:
        want.add("drum kit")
    return want


def instrument_rank(entry: dict, role: str | None) -> int:
    """0 for an instrument named for the role ('CelloEnsSusVib'), 1 for one that only sits
    in a folder named for it: Arturia's Augmented STRINGS folder holds tape and vinyl
    textures that would otherwise crowd out the string sections."""
    if not role:
        return 0
    return 0 if _wanted_kinds(role) & set(instrument_kinds(entry["name"])) else 1


def _words(text: str) -> list[str]:
    t = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    t = re.sub(r"([A-Z])([A-Z][a-z])", r"\1 \2", t)   # SViolin, FHorn, EGuitar: a letter prefix, then the word
    t = re.sub(r"([A-Za-z])(\d)", r"\1 \2", t)
    t = re.sub(r"(\d)([A-Za-z])", r"\1 \2", t)
    return [w for w in re.split(r"[^A-Za-z0-9#]+", t.lower()) if w]


def roles_from_name(name: str, folder: str = "") -> list[str]:
    words = _words(name) + _words(folder)
    joined = " ".join(words)
    roles = []
    for role, keys in ROLE_WORDS.items():
        if any(k in words or (len(k) > 4 and k in joined.replace(" ", "")) for k in keys):
            roles.append(role)
    if "open hat" in roles and "closed hat" in roles:
        roles.remove("closed hat")
    return roles


def too_broad(folder: Path) -> str | None:
    """Why a folder is too broad to index as samples (a drive, the home folder itself, a
    system folder: walking it takes ages and shows every audio file's name), or None."""
    p = folder.expanduser().resolve()
    if p.parent == p:
        return "that's a whole drive"
    if p == Path.home().resolve():
        return "that's your whole home folder"
    system = [Path(os.environ.get(k, "")) for k in ("SystemRoot", "ProgramFiles", "ProgramFiles(x86)", "ProgramData")
              if os.environ.get(k)] + [Path(x) for x in ("/System", "/usr", "/etc", "/bin", "/Library")]
    for root in system:
        try:
            p.relative_to(root.resolve())
            return "that's a system folder"
        except (ValueError, OSError):
            continue
    return None


def bpm_from_name(name: str) -> float | None:
    m = re.search(r"(?<!\d)(\d{2,3}(?:\.\d+)?)\s*-?\s*bpm", name, re.IGNORECASE)
    if m and 50 <= float(m.group(1)) <= 220:
        return float(m.group(1))
    # Loops and vocal phrases often carry their tempo bare: 'Vox_Hook_124_Am', 'Break 92'.
    if re.search(r"loop|break|groove|vocal|vox|chop|phrase|hook|acapella|acappella|adlib", name, re.IGNORECASE):
        for n in re.findall(r"(?<![\d.])(\d{2,3})(?![\d.])", name):
            if 60 <= int(n) <= 200:
                return float(n)
    return None


def key_from_name(name: str) -> str | None:
    """The key a file's name gives: 'Pad_Am_120', 'Keys C# minor', 'Pad_in_D_minor',
    'Guitar key E'. "key"/"in" must be whole words before a capital note letter: matched
    inside words with any case, 'Main_B_loop' and 'Rain_in_a_jar' became B and A major."""
    m = re.search(r"(?:^|[ _\-(\[])([A-G][#b]?)[ _\-]?(m|min|minor|maj|major)(?=$|[ _\-)\].])", name)
    if m:
        quality = "minor" if m.group(2).lower().startswith("m") and m.group(2).lower() not in ("maj", "major") else "major"
        return f"{m.group(1)} {quality}"
    m = re.search(r"(?:^|[ _\-(\[])(?i:key|in)[ _\-]?([A-G][#b]?)(?=$|[ _\-)\].])", name)
    return f"{m.group(1)} major" if m else None


# ------------------------------------------------------------------ analysis

def _load(path: str, seconds: float = 30.0) -> tuple[np.ndarray, int, float]:
    info = sf.info(path)
    frames = int(min(info.frames, seconds * info.samplerate))
    audio, fs = sf.read(path, frames=frames, dtype="float32", always_2d=True)
    return audio.mean(axis=1), int(fs), info.frames / info.samplerate


def onset_envelope(x: np.ndarray, fs: int, hop: int = 512) -> np.ndarray:
    if len(x) < 2048:  # a short hit (a 40 ms click): scipy refused a window longer than the sound
        x = np.pad(x, (0, 2048 - len(x)))
    _, _, z = signal.stft(x, fs=fs, nperseg=2048, noverlap=2048 - hop, boundary=None, padded=False)
    mag = np.log1p(np.abs(z) * 100)
    flux = np.maximum(0, np.diff(mag, axis=1)).sum(axis=0)
    if flux.size < 8:
        return flux
    # A window no longer than the envelope: "same" returns the longer of the two, so a
    # 16-frame window on a short sample made a shape mismatch (a crash on short hits).
    width = min(16, flux.size)
    smooth = np.convolve(flux, np.ones(width) / width, mode="same")
    return np.maximum(0, flux - smooth)


ONSET_GAP_S, LOOP_SPREAD = 0.08, 0.4   # hits closer than this are one hit; a loop's hits span this much of it


def onset_times(env: np.ndarray, fs: int, hop: int = 512, threshold: float = 0.3) -> list[float]:
    """When the hits land (s): each rise of the onset envelope over threshold x its peak,
    rises within ONSET_GAP_S of the last counted as the same hit."""
    if not env.size or env.max() <= 0:
        return []
    above = env > env.max() * threshold
    rises = np.flatnonzero(above & ~np.concatenate(([False], above[:-1])))
    times: list[float] = []
    for frame in rises:
        t = float(frame * hop / fs)
        if not times or t - times[-1] >= ONSET_GAP_S:
            times.append(t)
    return times


def estimate_bpm(x: np.ndarray, fs: int, duration: float) -> tuple[float | None, str]:
    """Tempo of a loop: the beat period that best explains the onset rhythm (its
    autocorrelation at one, two and four beats, with a mild preference for common
    tempos), snapped to a whole number of beats across the loop when that agrees."""
    hop = 512
    env = onset_envelope(x, fs, hop)
    if env.size < 32 or not np.any(env):
        return None, "no clear rhythm"
    env = env - env.mean()
    ac = np.correlate(env, env, mode="full")[env.size - 1:]
    ac = ac / (ac[0] or 1)
    frame_s = hop / fs

    def at(lag: float) -> float:
        lo = int(math.floor(lag))
        if lo + 1 >= ac.size:
            return 0.0
        return float(ac[lo] + (ac[lo + 1] - ac[lo]) * (lag - lo))

    best, best_score = None, -1e18
    for bpm in np.arange(60, 200.5, 0.5):
        lag = 60 / bpm / frame_s
        # A real beat lines up at 1, 2 and 4 beats and, usually, at the half beat too.
        score = at(lag) + 0.5 * at(2 * lag) + 0.25 * at(4 * lag) + 0.35 * at(lag / 2)
        score *= math.exp(-0.5 * (math.log2(bpm / 120) / 1.0) ** 2)
        if score > best_score:
            best, best_score = bpm, score
    if best is None:
        return None, "no clear rhythm"
    for beats in (4, 8, 16, 32, 64, 2, 3, 6, 12, 24, 48):
        whole = 60 * beats / duration
        if abs(whole - best) / whole < 0.04:
            return round(whole, 2), f"{beats} beats long; rhythm agrees"
    return round(best, 1), "from the rhythm only (length isn't a whole number of beats)"


def estimate_key(x: np.ndarray, fs: int) -> list[dict]:
    f, _, z = signal.stft(x, fs=fs, nperseg=8192, noverlap=4096)
    power = (np.abs(z) ** 2).mean(axis=1)
    hist = [0.0] * 12
    for freq, pw in zip(f, power):
        if 55 <= freq <= 2500:
            hist[int(round(12 * math.log2(freq / 440) + 69)) % 12] += float(pw)
    return harmony.detect_key(hist, top=2)


def vocal_pitch(x: np.ndarray, fs: int, fmin: float = 70.0, fmax: float = 1100.0) -> tuple[float | None, float]:
    """The pitch of a voiced sound (Hz, clarity 0-1). Voices have strong formants that
    make plain autocorrelation lock onto a subharmonic (an octave or a twelfth low),
    so this takes the highest-pitched candidate that's nearly as strong as the best."""
    x = x - x.mean()
    n = len(x)
    lo, hi = int(fs / fmax), int(fs / fmin)
    if n < hi * 2 or not np.any(x):
        return None, 0.0
    spec = np.fft.rfft(x, 2 * n)
    ac = np.fft.irfft(spec * np.conj(spec))[: hi + 2]
    ac = ac / (ac[0] or 1.0)
    seg = ac[lo: hi + 1]
    peaks = [i for i in range(1, len(seg) - 1) if seg[i] >= seg[i - 1] and seg[i] >= seg[i + 1] and seg[i] > 0]
    if not peaks:
        return None, 0.0
    best = max(seg[i] for i in peaks)
    lag = lo + next(i for i in peaks if seg[i] >= 0.9 * best)
    # Refine to a fraction of a sample (parabola through the peak): whole samples are
    # several cents apart at higher pitches, too coarse to judge tuning.
    a, b, c = ac[lag - 1], ac[lag], ac[lag + 1]
    shift = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) != 0 else 0.0
    return fs / (lag + float(np.clip(shift, -0.5, 0.5))), float(min(1.0, max(0.0, ac[lag])))


def slice_vocal(path: str, floor_db: float = -35.0, min_gap: float = 0.08, min_length: float = 0.06,
                max_length: float = 0.6) -> list[dict]:
    """Cuts a vocal recording into syllable-sized slices: sounding stretches split at
    each new attack. Each slice has its start and end (seconds), level and, when it's
    sung, its pitch (MIDI number, fractional: how in tune it is)."""
    x, fs, _ = _load(path)
    frame = int(0.01 * fs)
    n = len(x) // frame
    if n < 5:
        return []
    rms = np.sqrt(np.mean(x[: n * frame].reshape(n, frame) ** 2, axis=1)) + 1e-9
    level = 20 * np.log10(rms / rms.max())
    loud = level > floor_db
    hop = 256
    env = onset_envelope(x, fs, hop)
    attacks = []
    if env.size and env.max() > 0:
        for i in range(1, len(env) - 1):
            if env[i] > 0.25 * env.max() and env[i] >= env[i - 1] and env[i] >= env[i + 1]:
                t = i * hop / fs
                if not attacks or t - attacks[-1] >= min_gap:
                    attacks.append(t)
    slices = []
    i = 0
    while i < n:
        if not loud[i]:
            i += 1
            continue
        j = i
        while j < n and loud[j]:
            j += 1
        start, end = i * 0.01, j * 0.01
        cuts = [start] + [a for a in attacks if start + min_gap <= a <= end - min_gap] + [end]
        for a, b in zip(cuts, cuts[1:]):
            if b - a >= min_length:
                slices.append({"start": round(a, 3), "end": round(b, 3)})
        i = j
    for sl in slices:
        a, b = int(sl["start"] * fs), int(sl["end"] * fs)
        core = x[a + (b - a) // 5: b - (b - a) // 5][: int(0.3 * fs)]
        hz, clarity = vocal_pitch(core, fs)
        seg = x[a:b]
        sl["level_db"] = round(20 * math.log10(float(np.sqrt(np.mean(seg ** 2))) + 1e-9), 1)
        if hz and clarity >= 0.6:
            sl["pitch"] = round(69 + 12 * math.log2(hz / 440), 2)
    # An attack inside one sustained note isn't a new syllable: join touching slices
    # on the same pitch back into one (up to max_length), so held chops can ring.
    merged: list[dict] = []
    for sl in slices:
        prev = merged[-1] if merged else None
        if (prev and abs(sl["start"] - prev["end"]) < 0.015 and "pitch" in sl and "pitch" in prev
                and abs(sl["pitch"] - prev["pitch"]) < 0.5 and sl["end"] - prev["start"] <= max_length):
            prev["end"] = sl["end"]
            prev["level_db"] = max(prev["level_db"], sl["level_db"])
        else:
            merged.append(dict(sl))
    return merged


ANALYSIS_VERSION = 2     # cached analyses from before (no sub_share, punch...) are redone
# Stored lo-fi (an old sampler's 8-bit or low-rate files, like the CMI's): sounds dated
# unless that's the style. A kick with nothing above 14 kHz is just a kick, so bandwidth
# (top_hz) is reported but doesn't decide it.
LOFI_BITS = 8
LOFI_RATE = 32000


def hit_measures(x: np.ndarray, fs: int) -> dict:
    """What a drum hit measures like, for choosing samples by fit: sub_share (energy under
    90 Hz in its first second), punch_db (its first 10 ms against the 30-100 ms after:
    how hard the transient hits), level_db (RMS over its first 300 ms) and top_hz (the
    frequency 99.5% of its energy sits under: a dull or lo-fi file stops early)."""
    env = np.abs(x)
    above = np.flatnonzero(env > env.max() * 0.1) if x.size else np.array([])
    if not above.size:
        return {}
    a = int(above[0])
    seg = x[a: a + fs]
    out: dict = {}
    spec = np.abs(np.fft.rfft(seg * np.hanning(seg.size))) ** 2 if seg.size > 64 else None
    if spec is not None and spec.sum() > 0:
        freqs = np.fft.rfftfreq(seg.size, 1 / fs)
        total = spec.sum()
        out["sub_share"] = round(float(spec[(freqs >= 20) & (freqs < 90)].sum() / total), 2)
        cum = np.cumsum(spec) / total
        out["top_hz"] = int(freqs[min(len(freqs) - 1, int(np.searchsorted(cum, 0.995)))])

    def rms_db(lo: float, hi: float) -> float | None:
        part = x[a + int(lo * fs): a + int(hi * fs)]
        return 10 * math.log10(float(np.mean(np.square(part))) + 1e-20) if part.size else None

    head, body = rms_db(0, 0.01), rms_db(0.03, 0.1)
    if head is not None and body is not None:
        out["punch_db"] = round(head - body, 1)
    level = rms_db(0, 0.3)
    if level is not None:
        out["level_db"] = round(level, 1)
    return out


def bit_depth(path: str) -> int | None:
    import soundfile as sf

    try:
        subtype = sf.info(path).subtype
    except RuntimeError:
        return None
    if subtype in ("FLOAT", "DOUBLE"):
        return 32
    digits = "".join(ch for ch in subtype if ch.isdigit())
    return int(digits) if digits else None


def analyze(path: str) -> dict:
    """What a sample is: one-shot or loop, drum type or pitch, tempo and key for loops."""
    x, fs, duration = _load(path)
    out: dict = {"v": ANALYSIS_VERSION, "duration_s": round(duration, 3), "sample_rate": fs}
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    if peak <= 1e-5:
        return {**out, "silent": True}
    out["peak_db"] = round(20 * math.log10(peak), 1)
    env = onset_envelope(x, fs)
    hits = onset_times(env, fs)
    # Hits spread over the file make a loop; one long ringing hit doesn't. (Counting frames
    # over the threshold called a 1.6 s acoustic kick with a tail a loop "in A phrygian",
    # so it never ranked as a kick.)
    is_loop = duration >= 1.5 and len(hits) >= 4 and hits[-1] - hits[0] >= LOOP_SPREAD * duration
    out["kind"] = "loop" if is_loop else "one-shot"
    f = listen.features(x[: int(3 * fs)], fs)
    if f.get("starts_late_ms", 0) >= 8:
        out["starts_late_ms"] = f["starts_late_ms"]
    if is_loop:
        bpm, how = estimate_bpm(x, fs, duration)
        out["bpm"], out["bpm_basis"] = bpm, how
        if bpm:
            out["bars_at_4_4"] = round(duration * bpm / 240, 2)
        keys = estimate_key(x, fs)
        if keys:
            out["key"] = keys[0]["key"]
            out["key_confidence"] = keys[0].get("confidence")
    else:
        kind, conf = listen.classify_drum(f)
        out["sounds_like"] = kind
        out["confidence"] = conf
        if f.get("pitch_hz") and f.get("clarity", 0) > 0.7:
            out["pitch"] = theory.midi_to_note(int(round(69 + 12 * math.log2(f["pitch_hz"] / 440))))
        out["decay_s"] = f.get("decay_s")
        out["brightness_hz"] = f.get("centroid_hz")
        out.update(hit_measures(x, fs))
    bits = bit_depth(path)
    if bits:
        out["bit_depth"] = bits
    if (bits and bits <= LOFI_BITS) or fs < LOFI_RATE:
        out["lofi"] = True
    return out


UNMEASURED_DECAY_COST = 2.0
# Synth waveform folders (Arturia's Augmented and Pigments wavetables): a 0.2 s cycle
# that "sounds like" a kick is never the kick a role search wants.
WAVEFORM_FOLDER = re.compile(r"wavetable|single.?cycle|waveform", re.I)


def drum_fit(heard: dict, target) -> tuple[float, list[str]]:
    """How far a sample's measurements sit outside a palette's Drum target (0 = inside
    every range) and why. Ratios for times and brightness, 0.1 steps for the sub share,
    3 dB steps for punch."""
    total, why = 0.0, []
    for key, measured_key, scale in (("sub_share", "sub_share", 0.1), ("decay_s", "decay_s", None),
                                     ("brightness_hz", "brightness_hz", None), ("punch_db", "punch_db", 3.0)):
        lo, hi = getattr(target, key)
        v = heard.get(measured_key)
        if v is None:
            if key == "decay_s" and (lo, hi) != (0.0, 5.0):
                # No tail to read: a wavetable cycle or a click, not a drum (Arturia's
                # "BD Smash" wavetable ranked as a perfect pop kick this way).
                total += UNMEASURED_DECAY_COST
                why.append("decay unmeasured (no tail to read: a waveform or a click, not a hit)")
            continue
        if lo <= v <= hi:
            continue
        edge = lo if v < lo else hi
        d = abs(v - edge) / scale if scale else abs(math.log(max(v, 1e-3) / max(edge, 1e-3)))
        total += d
        why.append(f"{key.replace('_', ' ')} {v:g} (wanted {lo:g}-{hi:g})")
    return round(total, 2), why


# ----------------------------------------------------------------- the index

def default_folders() -> list[str]:
    home = Path.home()
    candidates = [Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "Arturia" / "Samples",
                  home / "SILA" / "library", home / "Music", home / "Documents" / "REAPER Media",
                  home / "Samples", home / "Documents" / "Samples"]
    return [str(p) for p in candidates if p.is_dir()]


class SampleLibrary:
    def __init__(self, directory: Path) -> None:
        self.config_path = Path(directory) / "sample_folders.json"
        self.index_path = Path(directory) / "sample_index.json"

    def folders(self) -> list[str]:
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            return list(dict.fromkeys(data.get("folders", [])))
        except FileNotFoundError:
            return default_folders()

    def set_folders(self, folders: list[str]) -> list[str]:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps({"folders": folders}, indent=1), encoding="utf-8")
        return folders

    # Several searches at once (Claude runs tools in parallel) fought over the index:
    # one shared temp file, and Windows refusing to replace a file another reader has
    # open ("Access denied"). Writes now take turns, use their own temp file, and retry.
    _lock = threading.RLock()

    def _load_index(self) -> dict:
        for attempt in range(50):
            try:
                return json.loads(self.index_path.read_text(encoding="utf-8"))
            except (FileNotFoundError, ValueError):
                return {}
            except PermissionError:
                time.sleep(0.02)
        raise OSError(f"the sample index ({self.index_path}) is locked by another program; try again")

    def _save_index(self, index: dict) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.index_path.with_name(f"{self.index_path.stem}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp")
        tmp.write_text(json.dumps(index), encoding="utf-8")
        for attempt in range(50):
            try:
                tmp.replace(self.index_path)
                return
            except PermissionError:
                time.sleep(0.02)
        tmp.unlink(missing_ok=True)
        raise OSError(f"couldn't update the sample index ({self.index_path}): another program has it open")

    def index(self, refresh: bool = False) -> dict:
        with self._lock:  # one scan at a time, not one per parallel search
            return self._index(refresh)

    def _index(self, refresh: bool) -> dict:
        index = self._load_index()
        folders = self.folders()
        if (index and not refresh and index.get("folders") == folders and not index.get("partial")
                and "instruments" in index):
            return index
        old = {f["path"]: f for f in index.get("files", [])}
        old_inst = {i["path"]: i for i in index.get("instruments", []) if "mtime" in i}
        old_bad = index.get("unplayable_sfz", {})
        files, instruments, unplayable = [], [], {}
        started = time.time()
        for folder in folders:
            if len(files) >= MAX_FILES or time.time() - started > MAX_INDEX_S:
                break
            for root, _, names in os.walk(folder):
                if len(files) >= MAX_FILES or time.time() - started > MAX_INDEX_S:
                    break   # a huge tree stops here instead of walking on with nothing to add
                for name in names:
                    if Path(name).suffix.lower() == ".sfz":
                        path = os.path.join(root, name)
                        try:
                            mtime = int(os.stat(path).st_mtime)
                        except OSError:
                            continue
                        # Checked once per file version: an .sfz names hundreds of samples. A
                        # missing sample installed later shows up on refresh=True.
                        prev = old_inst.get(path)
                        if prev and prev.get("mtime") == mtime and not refresh:
                            instruments.append(prev)
                        elif old_bad.get(path) == mtime and not refresh:
                            unplayable[path] = mtime
                        elif playable_sfz(path):
                            rel = os.path.relpath(root, folder)
                            instruments.append({"path": path, "name": Path(name).stem, "folder": rel,
                                                "kinds": instrument_kinds(Path(name).stem, rel), "mtime": mtime})
                        else:
                            unplayable[path] = mtime
                        continue
                    if Path(name).suffix.lower() not in AUDIO_EXTENSIONS:
                        continue
                    path = os.path.join(root, name)
                    try:
                        st = os.stat(path)
                    except OSError:
                        continue
                    prev = old.get(path)
                    if prev and prev.get("mtime") == int(st.st_mtime):
                        files.append(prev)
                        continue
                    entry = {"path": path, "name": Path(name).stem, "folder": os.path.relpath(root, folder),
                             "library": folder, "mtime": int(st.st_mtime)}
                    try:
                        info = sf.info(path)
                        entry["duration_s"] = round(info.frames / info.samplerate, 3)
                        entry["channels"] = info.channels
                    except Exception:  # noqa: BLE001 - unreadable files are skipped, not fatal
                        continue
                    entry["roles"] = roles_from_name(entry["name"], Path(root).name)
                    bpm, key = bpm_from_name(name), key_from_name(Path(name).stem)
                    if bpm:
                        entry["bpm"] = bpm
                    if key:
                        entry["key"] = key
                    files.append(entry)
                    if len(files) >= MAX_FILES:
                        break
        index = {"folders": folders, "built": time.strftime("%Y-%m-%d %H:%M"), "files": files,
                 "instruments": instruments, "unplayable_sfz": unplayable}
        if len(files) >= MAX_FILES or time.time() - started > MAX_INDEX_S:
            index["partial"] = True   # cut short: the next call carries on (unchanged files are reused)
        self._save_index(index)
        return index

    def remember(self, path: str, analysis: dict) -> None:
        """Caches a sample's analysis in the index (best effort: a cache)."""
        self.remember_many({path: analysis})

    def remember_many(self, analyses: dict[str, dict]) -> None:
        """Caches several analyses with one write of the index."""
        if not analyses:
            return
        with self._lock:
            try:
                index = self._load_index()
                hit = False
                for f in index.get("files", []):
                    if f["path"] in analyses:
                        f["analysis"] = analyses[f["path"]]
                        hit = True
                if hit:
                    self._save_index(index)
            except OSError:
                pass

    def instruments(self, text: str | None = None, role: str | None = None) -> list[dict]:
        """The .sfz instruments in the sample folders that answer a search, the ones
        named for the role first."""
        found = [i for i in self.index().get("instruments", []) if instrument_matches(i, text, role)]
        return sorted(found, key=lambda i: instrument_rank(i, role))

    def search(self, text: str | None = None, role: str | None = None, kind: str | None = None,
               bpm: float | None = None, key: str | None = None, max_duration: float | None = None) -> list[dict]:
        files = self.index().get("files", [])
        words = _words(text) if text else []
        out = []
        for f in files:
            hay = " ".join(_words(f["name"]) + _words(f["folder"]))
            if words and not all(w in hay for w in words):
                continue
            if role and role.lower() not in f.get("roles", []) and role.lower() != (f.get("analysis") or {}).get("sounds_like"):
                continue
            if role and WAVEFORM_FOLDER.search(f.get("folder", "")):
                continue   # a role search wants hits and phrases, not synth waveforms (a text search still finds them)
            dur = f.get("duration_s", 0)
            looks_loop = "loop" in f.get("roles", []) or "bpm" in f or (f.get("analysis") or {}).get("kind") == "loop"
            if kind == "loop" and not looks_loop:
                continue
            if kind == "one-shot" and (looks_loop or dur > 4):
                continue
            if max_duration and dur > max_duration:
                continue
            file_bpm = f.get("bpm") or (f.get("analysis") or {}).get("bpm")
            if bpm and file_bpm and not any(abs(file_bpm * k - bpm) / bpm < 0.06 for k in (1, 2, 0.5)):
                continue
            if key and f.get("key") and key.lower().split()[0] != f["key"].lower().split()[0]:
                continue
            out.append(f)
        return out
