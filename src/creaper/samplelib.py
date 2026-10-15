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


def _words(text: str) -> list[str]:
    t = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
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


def bpm_from_name(name: str) -> float | None:
    m = re.search(r"(?<!\d)(\d{2,3}(?:\.\d+)?)\s*-?\s*bpm", name, re.IGNORECASE)
    if m and 50 <= float(m.group(1)) <= 220:
        return float(m.group(1))
    if re.search(r"loop|break|groove", name, re.IGNORECASE):
        for n in re.findall(r"(?<![\d.])(\d{2,3})(?![\d.])", name):
            if 60 <= int(n) <= 200:
                return float(n)
    return None


def key_from_name(name: str) -> str | None:
    m = re.search(r"(?:^|[ _\-(\[])([A-G][#b]?)\s?(m|min|minor|maj|major)(?=$|[ _\-)\].])", name)
    if m:
        quality = "minor" if m.group(2).lower().startswith("m") and m.group(2).lower() not in ("maj", "major") else "major"
        return f"{m.group(1)} {quality}"
    m = re.search(r"(?:key|in)[ _\-]?([A-G][#b]?)(?=$|[ _\-)\].])", name, re.IGNORECASE)
    return f"{m.group(1).upper()} major" if m else None


# ------------------------------------------------------------------ analysis

def _load(path: str, seconds: float = 30.0) -> tuple[np.ndarray, int, float]:
    info = sf.info(path)
    frames = int(min(info.frames, seconds * info.samplerate))
    audio, fs = sf.read(path, frames=frames, dtype="float32", always_2d=True)
    return audio.mean(axis=1), int(fs), info.frames / info.samplerate


def onset_envelope(x: np.ndarray, fs: int, hop: int = 512) -> np.ndarray:
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


def analyze(path: str) -> dict:
    """What a sample is: one-shot or loop, drum type or pitch, tempo and key for loops."""
    x, fs, duration = _load(path)
    out: dict = {"duration_s": round(duration, 3), "sample_rate": fs}
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    if peak <= 1e-5:
        return {**out, "silent": True}
    out["peak_db"] = round(20 * math.log10(peak), 1)
    env = onset_envelope(x, fs)
    onsets = int((env > env.max() * 0.3).sum()) if env.size else 0
    is_loop = duration >= 1.5 and onsets >= 4
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
    return out


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
        if index and not refresh and index.get("folders") == folders:
            return index
        old = {f["path"]: f for f in index.get("files", [])}
        files = []
        for folder in folders:
            for root, _, names in os.walk(folder):
                for name in names:
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
        index = {"folders": folders, "built": time.strftime("%Y-%m-%d %H:%M"), "files": files}
        self._save_index(index)
        return index

    def remember(self, path: str, analysis: dict) -> None:
        """Caches a sample's analysis in the index (best effort: a cache)."""
        with self._lock:
            try:
                index = self._load_index()
                for f in index.get("files", []):
                    if f["path"] == path:
                        f["analysis"] = analysis
                        self._save_index(index)
                        return
            except OSError:
                pass

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
