"""Note names, chord symbols and drum patterns, turned into MIDI notes.

Times are in quarter notes (QN) from the start of the MIDI item:
1 = quarter note, 0.5 = eighth, 0.25 = sixteenth, 4 = a bar of 4/4.
Middle C is C4 = 60, as in REAPER's default MIDI editor.
"""

from __future__ import annotations

import random
import re
from collections.abc import Callable
from dataclasses import dataclass

from . import scales as scales_db

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
_LETTERS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_NOTE_RE = re.compile(r"^([A-Ga-g])([#b♯♭]*)(-?\d+)$")
_PITCH_CLASS_RE = re.compile(r"^([A-G])([#b♯♭]*)")


def _accidental(acc: str) -> int:
    return acc.count("#") + acc.count("♯") - acc.count("b") - acc.count("♭")


def note_to_midi(note: int | str) -> int:
    """'C4' -> 60, 'F#3' -> 54, 'Bb2' -> 46; integers pass through."""
    if isinstance(note, bool):
        raise ValueError("a note must be a name like C4 or a MIDI number")
    if isinstance(note, (int, float)):
        value = int(note)
    else:
        text = str(note).strip()
        if re.fullmatch(r"-?\d+", text):
            value = int(text)
        else:
            m = _NOTE_RE.match(text)
            if not m:
                raise ValueError(f"can't read the note '{note}' (use names like C4, F#3, Bb2, or MIDI numbers; C4 = 60)")
            letter, acc, octave = m.groups()
            value = _LETTERS[letter.upper()] + _accidental(acc) + (int(octave) + 1) * 12
    if not 0 <= value <= 127:
        raise ValueError(f"note '{note}' is outside the MIDI range 0-127")
    return value


def midi_to_note(value: int) -> str:
    return f"{NOTE_NAMES[value % 12]}{value // 12 - 1}"


# Intervals in semitones above the root.
CHORD_QUALITIES: dict[str, tuple[int, ...]] = {
    "": (0, 4, 7), "maj": (0, 4, 7), "M": (0, 4, 7),
    "m": (0, 3, 7), "min": (0, 3, 7), "-": (0, 3, 7),
    "dim": (0, 3, 6), "°": (0, 3, 6), "o": (0, 3, 6),
    "aug": (0, 4, 8), "+": (0, 4, 8),
    "sus2": (0, 2, 7), "sus4": (0, 5, 7), "sus": (0, 5, 7),
    "5": (0, 7),
    "6": (0, 4, 7, 9), "m6": (0, 3, 7, 9),
    "6/9": (0, 4, 7, 9, 14), "69": (0, 4, 7, 9, 14),
    "7": (0, 4, 7, 10),
    "maj7": (0, 4, 7, 11), "M7": (0, 4, 7, 11), "Δ": (0, 4, 7, 11), "Δ7": (0, 4, 7, 11),
    "m7": (0, 3, 7, 10), "min7": (0, 3, 7, 10), "-7": (0, 3, 7, 10),
    "mmaj7": (0, 3, 7, 11), "mM7": (0, 3, 7, 11), "m(maj7)": (0, 3, 7, 11),
    "m7b5": (0, 3, 6, 10), "ø": (0, 3, 6, 10), "ø7": (0, 3, 6, 10),
    "dim7": (0, 3, 6, 9), "°7": (0, 3, 6, 9), "o7": (0, 3, 6, 9),
    "aug7": (0, 4, 8, 10), "7#5": (0, 4, 8, 10), "+7": (0, 4, 8, 10),
    "7b5": (0, 4, 6, 10),
    "7sus4": (0, 5, 7, 10), "7sus": (0, 5, 7, 10), "7sus2": (0, 2, 7, 10),
    "add9": (0, 4, 7, 14), "madd9": (0, 3, 7, 14), "add11": (0, 4, 7, 17),
    "9": (0, 4, 7, 10, 14), "maj9": (0, 4, 7, 11, 14), "m9": (0, 3, 7, 10, 14),
    "7b9": (0, 4, 7, 10, 13), "7#9": (0, 4, 7, 10, 15), "7#11": (0, 4, 7, 10, 18),
    "maj7#11": (0, 4, 7, 11, 18),
    "11": (0, 4, 7, 10, 14, 17), "m11": (0, 3, 7, 10, 14, 17),
    "13": (0, 4, 7, 10, 14, 21), "maj13": (0, 4, 7, 11, 14, 21), "m13": (0, 3, 7, 10, 14, 21),
    # Extended, altered and colour chords.
    "add2": (0, 2, 4, 7), "madd2": (0, 2, 3, 7), "m(add9)": (0, 3, 7, 14), "add4": (0, 4, 5, 7),
    "madd11": (0, 3, 7, 17), "m(add11)": (0, 3, 7, 17), "add#11": (0, 4, 7, 18), "add13": (0, 4, 7, 21),
    "sus2sus4": (0, 2, 5, 7), "sus24": (0, 2, 5, 7), "6sus4": (0, 5, 7, 9), "6sus2": (0, 2, 7, 9),
    "m6/9": (0, 3, 7, 9, 14), "m69": (0, 3, 7, 9, 14), "6/9#11": (0, 4, 7, 9, 14, 18),
    "maj7#5": (0, 4, 8, 11), "maj7+5": (0, 4, 8, 11), "+maj7": (0, 4, 8, 11), "augmaj7": (0, 4, 8, 11),
    "maj7b5": (0, 4, 6, 11), "maj7sus2": (0, 2, 7, 11), "maj7sus4": (0, 5, 7, 11),
    "maj9#11": (0, 4, 7, 11, 14, 18), "maj13#11": (0, 4, 7, 11, 14, 18, 21), "maj7#9": (0, 4, 7, 11, 15),
    "m(maj9)": (0, 3, 7, 11, 14), "mmaj9": (0, 3, 7, 11, 14), "mM9": (0, 3, 7, 11, 14),
    "m7b9": (0, 3, 7, 10, 13), "m7#5": (0, 3, 8, 10), "m7b13": (0, 3, 7, 10, 20),
    "m9b5": (0, 3, 6, 10, 14), "ø9": (0, 3, 6, 10, 14), "m11b5": (0, 3, 6, 10, 14, 17), "ø11": (0, 3, 6, 10, 14, 17),
    "dim(maj7)": (0, 3, 6, 11), "dimmaj7": (0, 3, 6, 11), "°maj7": (0, 3, 6, 11), "dim9": (0, 3, 6, 9, 14),
    "9sus4": (0, 5, 7, 10, 14), "9sus": (0, 5, 7, 10, 14), "13sus4": (0, 5, 7, 10, 14, 21), "13sus": (0, 5, 7, 10, 14, 21),
    "7sus4b9": (0, 5, 7, 10, 13), "7susb9": (0, 5, 7, 10, 13), "sus4b9": (0, 5, 7, 13),
    "7b13": (0, 4, 7, 10, 20), "7#5b9": (0, 4, 8, 10, 13), "7#5#9": (0, 4, 8, 10, 15), "7b5b9": (0, 4, 6, 10, 13),
    "7b5#9": (0, 4, 6, 10, 15), "7b9#11": (0, 4, 7, 10, 13, 18), "7#9#11": (0, 4, 7, 10, 15, 18),
    "7b9b13": (0, 4, 7, 10, 13, 20), "7#9b13": (0, 4, 7, 10, 15, 20), "7b9#9": (0, 4, 7, 10, 13, 15),
    "7alt": (0, 4, 10, 13, 15, 18, 20), "alt": (0, 4, 10, 13, 15, 18, 20),
    "9#11": (0, 4, 7, 10, 14, 18), "9b5": (0, 4, 6, 10, 14), "9#5": (0, 4, 8, 10, 14), "aug9": (0, 4, 8, 10, 14),
    "9b13": (0, 4, 7, 10, 14, 20), "13#11": (0, 4, 7, 10, 14, 18, 21), "13b9": (0, 4, 7, 10, 13, 21),
    "13#9": (0, 4, 7, 10, 15, 21), "7add13": (0, 4, 7, 10, 21), "7/6": (0, 4, 7, 9, 10),
    "11b9": (0, 4, 7, 10, 13, 17), "m13b5": (0, 3, 6, 10, 14, 17, 21),
    "m7add11": (0, 3, 7, 10, 17), "m7(add11)": (0, 3, 7, 10, 17), "m(add2)": (0, 2, 3, 7),
    "5add9": (0, 7, 14), "no3": (0, 7), "(no3)": (0, 7), "7no3": (0, 7, 10), "7(no3)": (0, 7, 10),
    "7no5": (0, 4, 10), "maj7no5": (0, 4, 11), "m7no5": (0, 3, 10),
    "quartal": (0, 5, 10), "q": (0, 5, 10), "quartal4": (0, 5, 10, 15), "so what": (0, 5, 10, 15, 19),
    "+add9": (0, 4, 8, 14), "aug(add9)": (0, 4, 8, 14), "b5": (0, 4, 6), "dim(add9)": (0, 3, 6, 14),
    "add6": (0, 4, 7, 9), "madd6": (0, 3, 7, 9),
    "1": (0,), "octave": (0, 12),
}


@dataclass(frozen=True)
class Chord:
    symbol: str
    root: int  # pitch class 0-11
    intervals: tuple[int, ...]
    bass: int | None  # pitch class of a slash bass note


def lookup_quality(text: str) -> tuple[int, ...] | None:
    """Chord-quality text -> intervals, tolerating common spellings: Maj7, mi7,
    min(maj7), 7(b9), (add9), -7b5, 7+, ^7."""
    candidates = [text]
    t = text.replace("Maj", "maj").replace("MA", "maj").replace("^", "maj").replace("♭", "b").replace("♯", "#")
    t = re.sub(r"^mi(?!n)", "m", t)
    t = re.sub(r"^min", "m", t)
    t = re.sub(r"^-", "m", t)
    candidates.append(t)
    no_parens = t.replace("(", "").replace(")", "").replace(",", "")
    candidates += [no_parens, no_parens.replace("+", "#"), no_parens.replace("#5", "+5")]
    if t.endswith("+") and t[:-1] in ("7", "9"):
        candidates.append(t[:-1] + "#5")
    for c in candidates:
        if c in CHORD_QUALITIES:
            return CHORD_QUALITIES[c]
    return None


def parse_chord(symbol: str) -> Chord:
    text = symbol.strip()
    m = _PITCH_CLASS_RE.match(text)
    if not m:
        raise ValueError(f"can't read the chord '{symbol}' (expected something like Am7, F#m7b5, Cmaj7/E)")
    root = (_LETTERS[m.group(1)] + _accidental(m.group(2))) % 12
    rest = text[m.end():]
    bass = None
    if "/" in rest:
        head, _, tail = rest.rpartition("/")
        bm = _PITCH_CLASS_RE.fullmatch(tail)
        if bm:
            bass = (_LETTERS[bm.group(1)] + _accidental(bm.group(2))) % 12
            rest = head
    intervals = lookup_quality(rest)
    if intervals is None:
        known = ", ".join(sorted(q for q in CHORD_QUALITIES if q))
        raise ValueError(f"unknown chord quality '{rest}' in '{symbol}'. Known qualities: {known}")
    return Chord(symbol, root, intervals, bass)


def chord_voicing(chord: Chord, octave: int = 4, inversion: int = 0) -> list[int]:
    notes = [12 * (octave + 1) + chord.root + i for i in chord.intervals]
    for _ in range(inversion % len(notes)):
        notes = notes[1:] + [notes[0] + 12]
    return notes


def _movement(prev: list[int], cand: list[int]) -> int:
    return sum(min(abs(n - p) for p in prev) for n in cand) + sum(min(abs(p - n) for n in cand) for p in prev)


def voice_progression(chords: list[Chord], octave: int = 4, voice_leading: bool = True) -> list[list[int]]:
    """Picks a voicing per chord; with voice_leading, the one closest to the last.

    Voicings stay centered around E of the given octave (E4 for octave 4).
    """
    center = 12 * (octave + 1) + 4
    voicings: list[list[int]] = []
    prev: list[int] | None = None
    for chord in chords:
        if not voice_leading:
            voicing = chord_voicing(chord, octave)
        else:
            candidates = [
                chord_voicing(chord, octave + shift, inv)
                for shift in (-1, 0, 1)
                for inv in range(len(chord.intervals))
            ]

            def cost(c: list[int]) -> float:
                drift = abs(sum(c) / len(c) - center)
                return drift if prev is None else _movement(prev, c) + 0.5 * drift

            voicing = min(candidates, key=cost)
        voicing = sorted(n for n in voicing if 0 <= n <= 127)
        voicings.append(voicing)
        prev = voicing
    return voicings


def bass_note(chord: Chord, octave: int) -> int:
    pc = chord.bass if chord.bass is not None else chord.root
    return 12 * (octave + 1) + pc


# General MIDI percussion (channel 10).
GM_DRUMS: dict[str, int] = {
    "kick": 36, "bass drum": 36, "bd": 36, "kick 2": 35,
    "snare": 38, "sd": 38, "snare 2": 40, "electric snare": 40,
    "rim": 37, "rimshot": 37, "side stick": 37, "sidestick": 37, "clap": 39, "hand clap": 39,
    "closed hat": 42, "closed hihat": 42, "hihat": 42, "hat": 42, "hh": 42, "chh": 42,
    "pedal hat": 44, "pedal hihat": 44, "open hat": 46, "open hihat": 46, "ohh": 46,
    "high tom": 50, "tom 1": 50, "hi mid tom": 48, "mid tom": 47, "tom 2": 47,
    "low tom": 45, "tom 3": 45, "floor tom": 43, "high floor tom": 43, "low floor tom": 41, "tom 4": 41,
    "crash": 49, "crash 2": 57, "ride": 51, "ride 2": 59, "ride bell": 53, "china": 52, "splash": 55,
    "tambourine": 54, "cowbell": 56, "vibraslap": 58,
    "high bongo": 60, "low bongo": 61, "mute high conga": 62, "high conga": 63, "low conga": 64,
    "high timbale": 65, "low timbale": 66, "high agogo": 67, "low agogo": 68,
    "cabasa": 69, "shaker": 70, "maracas": 70, "claves": 75,
    "high woodblock": 76, "woodblock": 76, "low woodblock": 77, "mute triangle": 80, "triangle": 81,
    "tom": 47, "bongo": 60, "conga": 63, "open conga": 63, "slap conga": 62, "timbale": 65, "agogo": 67,
    "guiro": 73, "short guiro": 73, "long guiro": 74, "whistle": 72, "short whistle": 71, "long whistle": 72,
    "cuica": 79, "open cuica": 79, "mute cuica": 78, "castanets": 85, "jingle bell": 83, "bell tree": 84,
    "sticks": 31, "metronome click": 33, "high q": 27, "slap": 28, "snare roll": 38,
}


def _norm(name: str) -> str:
    return re.sub(r"[\s_\-]+", " ", name.strip().lower()).replace("hi hat", "hihat")


_GM_LOOKUP = {_norm(k): v for k, v in GM_DRUMS.items()}


def drum_pitch(name: str | int) -> int:
    if isinstance(name, int):
        return note_to_midi(name)
    key = _norm(str(name))
    if key in _GM_LOOKUP:
        return _GM_LOOKUP[key]
    try:
        return note_to_midi(str(name))
    except ValueError:
        raise ValueError(
            f"unknown drum '{name}'. Use a General MIDI name ({', '.join(sorted(GM_DRUMS))}), "
            "a MIDI number, or a note name"
        ) from None


# Drum-kit vocabulary, so "closed hat" matches "HH Closed" or "Hi-Hat Cls".
_DRUM_SYNONYMS: dict[str, tuple[str, ...]] = {
    "bd": ("kick",), "kik": ("kick",), "kck": ("kick",), "bassdrum": ("kick",), "kicks": ("kick",),
    "sd": ("snare",), "snr": ("snare",), "sn": ("snare",), "snares": ("snare",),
    "hh": ("hat",), "hihat": ("hat",), "hats": ("hat",), "hat": ("hat",),
    "chh": ("closed", "hat"), "ch": ("closed", "hat"), "ohh": ("open", "hat"), "oh": ("open", "hat"),
    "phh": ("pedal", "hat"),
    "cl": ("closed",), "cls": ("closed",), "clsd": ("closed",), "op": ("open",), "opn": ("open",),
    "cym": ("cymbal",), "cy": ("cymbal",), "cr": ("crash",), "rd": ("ride",),
    "clp": ("clap",), "claps": ("clap",), "toms": ("tom",), "perc": ("percussion",),
    "rimshot": ("rim",), "sidestick": ("side", "stick"),
}


def drum_tokens(text: str) -> frozenset[str]:
    s = re.sub(r"([a-z])(\d)", r"\1 \2", text.lower())
    s = re.sub(r"(\d)([a-z])", r"\1 \2", s)
    raw = re.findall(r"[a-z]+|\d+", s)
    tokens: list[str] = []
    i = 0
    while i < len(raw):
        word, nxt = raw[i], raw[i + 1] if i + 1 < len(raw) else None
        if word == "hi" and nxt == "hat":  # "hi hat" / "hi-hat"
            i += 1
            continue
        if word == "bass" and nxt == "drum":
            tokens.append("kick")
            i += 2
            continue
        tokens.extend(_DRUM_SYNONYMS.get(word, (word,)))
        i += 1
    return frozenset(tokens)


def best_name_match(lane: str, names: dict[int, str], hint: int | None = None) -> int | None:
    """The key of the name that contains all of the lane's words with the fewest
    extra words; ties go to the key closest to `hint` (the General MIDI note)."""
    wanted = drum_tokens(lane)
    if not wanted:
        return None
    best: tuple[tuple[int, int], int] | None = None
    for key, name in names.items():
        tokens = drum_tokens(name)
        if wanted <= tokens:
            rank = (len(tokens - wanted), abs(key - hint) if hint is not None else key)
            if best is None or rank < best[0]:
                best = (rank, key)
    return best[1] if best else None


@dataclass(frozen=True)
class DrumLane:
    pitch: int
    channel: int | None  # None: use the pattern's channel
    source: str


def resolve_drum_lane(
    lane: str | int,
    drum_map: dict[str, dict] | None = None,
    note_names: dict[int, str] | None = None,
) -> DrumLane:
    """Finds the note a lane should play.

    Order: an explicit note (36, C1), the saved drum map for this instrument,
    the instrument's own note names, then General MIDI.
    """
    text = str(lane).strip()
    if re.fullmatch(r"-?\d+", text) or _NOTE_RE.match(text):
        return DrumLane(note_to_midi(text), None, "explicit note")
    hint = _GM_LOOKUP.get(_norm(text))
    if drum_map:
        keys = list(drum_map)
        exact = {_norm(k): k for k in keys}.get(_norm(text))
        if exact is None:
            index = best_name_match(text, dict(enumerate(keys)))
            exact = keys[index] if index is not None else None
        if exact is not None:
            entry = drum_map[exact]
            return DrumLane(entry["pitch"], entry.get("channel"), f"drum map ({exact})")
    if note_names:
        pitch = best_name_match(text, note_names, hint)
        if pitch is not None:
            return DrumLane(pitch, None, f"instrument note name '{note_names[pitch]}'")
    if hint is not None:
        return DrumLane(hint, None, "General MIDI")
    choices = sorted(set((drum_map or {}).keys()) | set((note_names or {}).values())) or sorted(GM_DRUMS)
    raise ValueError(f"unknown drum '{lane}'. Available: {', '.join(choices[:60])}")


def drum_map_entry(value: int | str | dict) -> dict:
    """36, 'C1' or {'note': 'C1', 'channel': 2} -> {'pitch': 36, 'channel': 2}."""
    if isinstance(value, dict):
        note = value.get("note", value.get("pitch"))
        if note is None:
            raise ValueError("drum map entries need a note, e.g. {'note': 'C1', 'channel': 2}")
        entry = {"pitch": note_to_midi(note)}
        if value.get("channel") is not None:
            channel = int(value["channel"])
            if not 1 <= channel <= 16:
                raise ValueError("MIDI channels go from 1 to 16")
            entry["channel"] = channel
        return entry
    return {"pitch": note_to_midi(value)}


# Step characters in drum patterns.
STEP_VELOCITY = {"x": 100, "X": 127, "o": 45, "g": 45}
REST_STEPS = set(".-_")
IGNORED_STEPS = set(" |")


def drum_pattern_notes(
    pattern: dict[str, str],
    step: float = 0.25,
    repeats: int = 1,
    swing: float = 50.0,
    start: float = 0.0,
    channel: int = 10,
    humanize: float = 0.0,
    seed: int | None = None,
    resolve: Callable[[str], DrumLane] = resolve_drum_lane,
) -> list[dict]:
    """Step-sequencer patterns -> notes.

    Each lane is a string of steps: x = hit, X = accent, o/g = ghost note,
    1-9 = velocity level, . or - = rest; spaces and | are ignored.
    swing follows the MPC convention: 50 = straight, ~66 = triplet feel.
    humanize (0-1) randomizes velocities by up to +/-20 at 1.
    resolve maps lane names to notes (and optionally a per-lane channel).
    """
    if step <= 0:
        raise ValueError("step must be positive")
    if not 50 <= swing <= 75:
        raise ValueError("swing goes from 50 (straight) to 75")
    rng = random.Random(seed)
    lanes = []
    for name, steps in pattern.items():
        cells = [c for c in steps if c not in IGNORED_STEPS]
        for c in cells:
            if c not in REST_STEPS and c not in STEP_VELOCITY and not c.isdigit():
                raise ValueError(f"unknown step '{c}' in the '{name}' lane (use x X o . or 1-9)")
        resolved = resolve(name)
        lanes.append((resolved.pitch, resolved.channel or channel, cells))
    cycle_steps = max((len(cells) for _, _, cells in lanes), default=0)
    swing_delay = 2 * step * swing / 100 - step
    notes = []
    for r in range(max(1, repeats)):
        for pitch, lane_channel, cells in lanes:
            for i, c in enumerate(cells):
                if c in REST_STEPS:
                    continue
                velocity = round(int(c) * 127 / 9) if c.isdigit() else STEP_VELOCITY[c]
                if humanize:
                    velocity += round(rng.uniform(-20, 20) * humanize)
                velocity = max(1, min(127, velocity))
                pos = start + (r * cycle_steps + i) * step
                if i % 2 == 1:
                    pos += swing_delay
                notes.append({
                    "pitch": pitch, "start": round(pos, 6), "length": round(step * 0.5, 6),
                    "velocity": velocity, "channel": lane_channel,
                })
    return notes


# --------------------------------------------------------------- MIDI edits
# Notes are dicts like get_midi_notes returns: pitch, start, length (QN from the
# item start), velocity, channel, and optionally selected/muted.

SCALES: dict[str, tuple[int, ...]] = scales_db.all_intervals()


def scale_pitch_classes(key: str, scale: str) -> set[int]:
    m = _PITCH_CLASS_RE.fullmatch(key.strip())
    if not m:
        raise ValueError(f"can't read the key '{key}' (use a note name like A, F#, Bb)")
    root = (_LETTERS[m.group(1)] + _accidental(m.group(2))) % 12
    return {(root + i) % 12 for i in scales_db.find_scale(scale).intervals}


def _clamp_pitch(p: int) -> int:
    return max(0, min(127, p))


def quantize(notes: list[dict], grid: float, strength: float = 1.0, swing: float = 50.0,
             lengths: bool = False) -> list[dict]:
    """Moves note starts toward the grid (QN; 0.25 = 16ths). strength 0-1; swing
    50-75 delays every other grid line (MPC style); lengths also snaps note ends."""
    if grid <= 0:
        raise ValueError("grid must be positive")
    out = []
    for n in notes:
        index = round(n["start"] / grid)
        target = index * grid
        if index % 2 == 1:
            target += 2 * grid * swing / 100 - grid
        start = n["start"] + (target - n["start"]) * strength
        length = n["length"]
        if lengths:
            end = n["start"] + n["length"]
            snapped_end = max(start + grid, round(end / grid) * grid)
            length = length + (snapped_end - start - length) * strength
        out.append({**n, "start": round(max(0.0, start), 6), "length": round(max(1e-3, length), 6)})
    return out


def humanize(notes: list[dict], timing: float = 0.02, velocity: int = 8, seed: int | None = None) -> list[dict]:
    """Random nudges: timing in QN (+/-), velocity in steps (+/-)."""
    rng = random.Random(seed)
    out = []
    for n in notes:
        start = max(0.0, n["start"] + rng.uniform(-timing, timing))
        vel = max(1, min(127, n["velocity"] + round(rng.uniform(-velocity, velocity))))
        out.append({**n, "start": round(start, 6), "velocity": vel})
    return out


def transpose(notes: list[dict], semitones: int) -> list[dict]:
    moved = [n["pitch"] + semitones for n in notes]
    if any(p < 0 or p > 127 for p in moved):
        raise ValueError("that transposition would push notes outside the MIDI range")
    return [{**n, "pitch": p} for n, p in zip(notes, moved)]


def snap_to_scale(notes: list[dict], key: str, scale: str, direction: str = "nearest") -> list[dict]:
    """Moves notes outside the scale to the nearest scale note (ties go down), or
    always up/down."""
    allowed = scale_pitch_classes(key, scale)
    out = []
    for n in notes:
        p = n["pitch"]
        if p % 12 not in allowed:
            candidates = []
            for d in range(1, 12):
                if direction in ("nearest", "down") and (p - d) % 12 in allowed:
                    candidates.append(p - d)
                if direction in ("nearest", "up") and (p + d) % 12 in allowed:
                    candidates.append(p + d)
                if candidates:
                    break
            p = min(candidates) if direction != "up" else max(candidates)
        out.append({**n, "pitch": _clamp_pitch(p)})
    return out


def set_velocity(notes: list[dict], value: int | None = None, start: int | None = None, end: int | None = None,
                 scale: float | None = None) -> list[dict]:
    """A fixed velocity, a ramp from start to end across the notes' time span, or
    scaling by a factor."""
    if not notes:
        return []
    t0 = min(n["start"] for n in notes)
    t1 = max(n["start"] for n in notes)
    out = []
    for n in notes:
        v = n["velocity"]
        if value is not None:
            v = value
        elif start is not None and end is not None:
            frac = 0.0 if t1 == t0 else (n["start"] - t0) / (t1 - t0)
            v = start + (end - start) * frac
        elif scale is not None:
            v = v * scale
        out.append({**n, "velocity": max(1, min(127, round(v)))})
    return out


def strum(notes: list[dict], delay: float = 0.03, direction: str = "up") -> list[dict]:
    """Spreads notes that start together (chords): each higher (up) or lower (down)
    note starts `delay` QN after the previous one."""
    groups: dict[float, list[dict]] = {}
    for n in notes:
        groups.setdefault(round(n["start"], 4), []).append(n)
    out = []
    for start, group in groups.items():
        ordered = sorted(group, key=lambda n: n["pitch"], reverse=direction == "down")
        for i, n in enumerate(ordered):
            offset = i * delay
            out.append({**n, "start": round(n["start"] + offset, 6), "length": round(max(1e-3, n["length"] - offset), 6)})
    return sorted(out, key=lambda n: (n["start"], n["pitch"]))


def legato(notes: list[dict], gap: float = 0.0) -> list[dict]:
    """Extends each note to the next note's start (per channel), minus gap."""
    out = []
    by_channel: dict[int, list[dict]] = {}
    for n in notes:
        by_channel.setdefault(n.get("channel", 1), []).append(n)
    for group in by_channel.values():
        starts = sorted({n["start"] for n in group})
        for n in group:
            later = [s for s in starts if s > n["start"] + 1e-6]
            if later:
                out.append({**n, "length": round(max(1e-3, later[0] - n["start"] - gap), 6)})
            else:
                out.append(dict(n))
    return sorted(out, key=lambda n: (n["start"], n["pitch"]))
