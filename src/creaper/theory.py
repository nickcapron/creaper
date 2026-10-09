"""Note names, chord symbols and drum patterns, turned into MIDI notes.

Times are in quarter notes (QN) from the start of the MIDI item:
1 = quarter note, 0.5 = eighth, 0.25 = sixteenth, 4 = a bar of 4/4.
Middle C is C4 = 60, as in REAPER's default MIDI editor.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass

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
}


@dataclass(frozen=True)
class Chord:
    symbol: str
    root: int  # pitch class 0-11
    intervals: tuple[int, ...]
    bass: int | None  # pitch class of a slash bass note


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
    intervals = CHORD_QUALITIES.get(rest) or CHORD_QUALITIES.get(rest.replace("Maj", "maj"))
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
) -> list[dict]:
    """Step-sequencer patterns -> notes.

    Each lane is a string of steps: x = hit, X = accent, o/g = ghost note,
    1-9 = velocity level, . or - = rest; spaces and | are ignored.
    swing follows the MPC convention: 50 = straight, ~66 = triplet feel.
    humanize (0-1) randomizes velocities by up to +/-20 at 1.
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
        lanes.append((drum_pitch(name), cells))
    cycle_steps = max((len(cells) for _, cells in lanes), default=0)
    swing_delay = 2 * step * swing / 100 - step
    notes = []
    for r in range(max(1, repeats)):
        for pitch, cells in lanes:
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
                    "velocity": velocity, "channel": channel,
                })
    return notes
