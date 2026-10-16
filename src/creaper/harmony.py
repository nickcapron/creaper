"""Harmony: keys, correct note spelling, Roman numerals, chord naming and analysis.

- Keys are a tonic plus any scale or mode ("F# dorian", "Bbm", "C harmonic minor").
- Notes are spelled the way a musician would write them: F# major has an E#, a
  Bb minor chord is Bb-Db-F, a C dim7 has a Bbb.
- Roman numerals follow common-practice and pop/jazz conventions: case gives the
  triad quality (V major, ii minor), ° dim, ø half-diminished, + augmented; 7, maj7,
  9, 13, sus4, add9 and altered extensions; inversion figures 6, 64, 65, 43, 42;
  flats counted from the major scale, as musicians use them (bVII is a whole step
  below the tonic in any mode), sharps raising the mode's own degree (#iv°7); secondary chords
  (V7/V, vii°7/ii); Neapolitan (N6); augmented sixths (It+6, Fr+6, Ger+6); Cad64.
  Degrees count in the key's mode, so in A minor VI is F and VII is G, and in
  minor keys vii° (and viiø7, vii°7) use the raised leading tone, as in classical
  harmony.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from . import scales as scales_db
from . import theory
from .theory import CHORD_QUALITIES, Chord

LETTERS = "CDEFGAB"
LETTER_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
MAJOR = (0, 2, 4, 5, 7, 9, 11)
NATURAL_MINOR = (0, 2, 3, 5, 7, 8, 10)


def accidental_text(n: int) -> str:
    return "#" * n if n > 0 else "b" * -n


def spell(pc: int, letter: str) -> str:
    """The name of pitch class pc written on the given letter: spell(6, 'G') = 'Gb'."""
    diff = (pc - LETTER_PC[letter]) % 12
    if diff > 6:
        diff -= 12
    return letter + accidental_text(diff)


def letter_offset(letter: str, steps: int) -> str:
    return LETTERS[(LETTERS.index(letter) + steps) % 7]


def name_pc(name: str) -> tuple[int, str]:
    m = re.fullmatch(r"([A-Ga-g])([#b♯♭]*)", name.strip())
    if not m:
        raise ValueError(f"can't read the note name '{name}'")
    letter = m.group(1).upper()
    acc = m.group(2).count("#") + m.group(2).count("♯") - m.group(2).count("b") - m.group(2).count("♭")
    return (LETTER_PC[letter] + acc) % 12, letter


# ---------------------------------------------------------------------- keys

@dataclass(frozen=True)
class Key:
    tonic: int
    letter: str
    scale: scales_db.Scale

    @property
    def tonic_name(self) -> str:
        return spell(self.tonic, self.letter)

    @property
    def name(self) -> str:
        return f"{self.tonic_name} {self.scale.name}"

    @property
    def heptatonic(self) -> bool:
        return len(self.scale.intervals) == 7

    @property
    def is_minor(self) -> bool:
        """Minor-family: a minor 3rd above the tonic."""
        return 3 in self.scale.intervals and 4 not in self.scale.intervals

    @property
    def degrees(self) -> tuple[int, ...]:
        """Seven scale degrees for numerals; non-heptatonic scales use the parallel major or minor."""
        if self.heptatonic:
            return self.scale.intervals
        return NATURAL_MINOR if self.is_minor else MAJOR

    def pitch_classes(self) -> set[int]:
        return {(self.tonic + i) % 12 for i in self.scale.intervals}

    def degree_letter(self, degree: int) -> str:
        return letter_offset(self.letter, degree - 1)

    def spell_pc(self, pc: int) -> str:
        """Spells a pitch class in this key: scale notes on their own letters, others
        as alterations (flats, except a raised 4th, in flat-leaning keys and C)."""
        pc %= 12
        rel = (pc - self.tonic) % 12
        degs = self.degrees
        if self.heptatonic and rel in degs:
            return spell(pc, self.degree_letter(degs.index(rel) + 1))
        if not self.heptatonic:
            for i, d in enumerate(degs):
                if d == rel:
                    return spell(pc, self.degree_letter(i + 1))
        # Chromatic note: raise the degree below or lower the degree above.
        below = [i for i, d in enumerate(degs) if (rel - d) % 12 == 1]
        above = [i for i, d in enumerate(degs) if (d - rel) % 12 == 1]
        sharp = spell(pc, self.degree_letter(below[0] + 1)) if below else None
        flat = spell(pc, self.degree_letter(above[0] + 1)) if above else None
        prefer_sharp = self.sharpness() > 0 or rel == 6
        options = [sharp, flat] if prefer_sharp else [flat, sharp]
        for o in options:
            if o and o.count("#") + o.count("b") <= 1:
                return o
        return next(o for o in options if o)

    def spell_chord_root(self, pc: int, intervals: tuple[int, ...]) -> str:
        """Spells a chord's root in this key. In-key roots are spelled as spell_pc does;
        a chromatic root follows the chord's function rather than the key signature
        (which gave D# for bVI in G major and B#7 for the backdoor chord in D major):
        - diminished and half-diminished chords are leading-tone chords: the raised
          note below (C#dim7 passing from C to Dm, G#dim as vii°/vi in C);
        - the raised 3rd, 6th and 7th of a minor key stay raised (C#, F# in A minor);
        - a minor chord on the raised 4th stays raised (F#m in C);
        - everything else (borrowed chords, the Neapolitan, tritone substitutes,
          backdoor dominants) is the lowered note above: Eb in G, Ab7 for D7 in G."""
        pc %= 12
        rel = (pc - self.tonic) % 12
        degs = self.degrees
        if rel in degs:
            return self.spell_pc(pc)
        shape = {i % 12 for i in intervals}
        diminished = 3 in shape and 6 in shape and 7 not in shape
        minor = 3 in shape and 4 not in shape
        prefer_sharp = diminished or (self.is_minor and rel in (4, 9, 11)) or (rel == 6 and minor)
        below = [i for i, d in enumerate(degs) if (rel - d) % 12 == 1]
        above = [i for i, d in enumerate(degs) if (d - rel) % 12 == 1]
        sharp = spell(pc, self.degree_letter(below[0] + 1)) if below else None
        flat = spell(pc, self.degree_letter(above[0] + 1)) if above else None
        options = [sharp, flat] if prefer_sharp else [flat, sharp]
        for o in options:
            if o and o.count("#") + o.count("b") <= 1:
                return o
        return next(o for o in options if o)

    def sharpness(self) -> int:
        """Sharps (+) or flats (-) in the key signature of this key's parent major scale."""
        rel_major = (self.tonic - (self.degrees[0] if False else _mode_offset(self.degrees))) % 12
        letter = letter_offset(self.letter, -_mode_letter_offset(self.degrees))
        name = spell(rel_major, letter)
        return SIGNATURES.get(name, 0)

    def spell_scale(self) -> list[str]:
        if self.heptatonic:
            return [spell((self.tonic + d) % 12, self.degree_letter(i + 1)) for i, d in enumerate(self.scale.intervals)]
        return [self.spell_pc(self.tonic + i) for i in self.scale.intervals]


SIGNATURES = {"C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F#": 6, "C#": 7,
              "F": -1, "Bb": -2, "Eb": -3, "Ab": -4, "Db": -5, "Gb": -6, "Cb": -7}

_MODE_ROTATIONS = {MAJOR[i:] + tuple(x + 12 for x in MAJOR[:i]): i for i in range(7)}


def _mode_offset(degs: tuple[int, ...]) -> int:
    """Semitones from the parent major's tonic up to this mode's tonic (0 if not a major mode)."""
    for i in range(7):
        rotated = tuple((d - MAJOR[i]) % 12 for d in MAJOR[i:] + MAJOR[:i])
        if tuple(sorted(rotated)) == tuple(sorted(degs)) and rotated == tuple(degs):
            return MAJOR[i]
    return 0 if 4 in degs else 9  # other scales: lean like the parallel major / relative-major of minor


def _mode_letter_offset(degs: tuple[int, ...]) -> int:
    off = _mode_offset(degs)
    return MAJOR.index(off) if off in MAJOR else 0


def parse_key(text: str) -> Key:
    """'C', 'C major', 'Am', 'A minor', 'f#m', 'Bb dorian', 'e' (lowercase = minor),
    'D harmonic minor', 'G mixolydian'."""
    t = text.strip()
    m = re.match(r"^([A-Ga-g])([#b♯♭]*)\s*(.*)$", t)
    if not m:
        raise ValueError(f"can't read the key '{text}' (try 'A minor', 'F# dorian', 'Bb')")
    letter_raw, acc, rest = m.groups()
    pc, letter = name_pc(letter_raw + acc)
    rest = rest.strip().lower().replace("♭", "b").replace("♯", "#")
    if rest in ("", "maj", "major", "ma", "m", "min", "minor", "mi"):
        if rest in ("m", "min", "minor", "mi") or (rest == "" and letter_raw.islower()):
            scale = scales_db.find_scale("minor")
        else:
            scale = scales_db.find_scale("major")
    else:
        scale = scales_db.find_scale(rest.removeprefix("key of "))
    return Key(pc, letter, scale)


# --------------------------------------------------------------- chord names

_PREFERRED = ("", "m", "dim", "aug", "5", "sus2", "sus4", "6", "m6", "6/9", "m6/9", "7", "maj7", "m7", "m(maj7)",
              "m7b5", "dim7", "aug7", "maj7#5", "7b5", "7sus4", "7sus2", "add9", "madd9", "add11", "madd11", "9",
              "maj9", "m9", "m(maj9)", "7b9", "7#9", "7#11", "maj7#11", "11", "m11", "13", "maj13", "m13",
              "9sus4", "13sus4", "7b13", "7#5b9", "7#5#9", "7b9#11", "7#9b13", "7b9b13", "9#11", "13#11", "13b9",
              "maj9#11", "dim(maj7)", "m7b9", "m9b5", "7no5", "7no3", "sus2sus4", "6sus4", "add2", "add4",
              "7alt")
_IDENTIFY_EXCLUDE = {"1", "octave", "q", "quartal", "quartal4", "so what", "alt", "7alt", "no3", "(no3)",
                     "sus2sus4", "sus24", "6sus2", "add4", "add2", "madd2", "m(add2)", "b5", "7/6"}

CANONICAL: dict[tuple[int, ...], str] = {}
for _q in _PREFERRED:
    CANONICAL.setdefault(CHORD_QUALITIES[_q], _q)
for _q, _iv in CHORD_QUALITIES.items():
    CANONICAL.setdefault(_iv, _q)

# Interval sets (mod 12) for chord recognition, simplest name first.
_ID_SHAPES: list[tuple[frozenset[int], str, int]] = []
_seen: set[frozenset[int]] = set()
for _q in list(_PREFERRED) + list(CHORD_QUALITIES):
    if _q in _IDENTIFY_EXCLUDE:
        continue
    _shape = frozenset(i % 12 for i in CHORD_QUALITIES[_q])
    if _shape not in _seen:
        _seen.add(_shape)
        _ID_SHAPES.append((_shape, _q, len(CHORD_QUALITIES[_q])))


def quality_name(intervals: tuple[int, ...]) -> str:
    if intervals in CANONICAL:
        return CANONICAL[intervals]
    shape = frozenset(i % 12 for i in intervals)
    for s, q, _ in _ID_SHAPES:
        if s == shape:
            return q
    return "(" + ",".join(str(i) for i in intervals) + ")"


def _degree_steps(intervals: tuple[int, ...]) -> list[int]:
    """Letter steps above the root for each chord interval (3rd = 2 letters, 7th = 6...)."""
    s = {i % 12 for i in intervals}
    has_maj3, has_p5 = 4 in s, 7 in s
    dim7 = {3, 6, 9} <= s and not ({10, 11} & s)
    # An altered dominant (7alt: b9, #9 and both altered 5ths) spells them as #11 and
    # b13, as jazz writes it: C7alt is C E Bb Db D# F# Ab, not ... Gb G#.
    altered = not has_p5 and {6, 8} <= s and has_maj3 and 10 in s and bool({1, 3} & s)
    steps = []
    for i in intervals:
        x = i % 12
        steps.append({
            0: 0, 1: 1, 2: 1,
            3: 1 if (has_maj3 and x == 3) else 2,
            4: 2, 5: 3,
            6: 3 if (has_p5 or altered) else 4,
            7: 4,
            8: 5 if (has_p5 or altered) else 4,
            9: 6 if dim7 else 5,
            10: 6, 11: 6,
        }[x])
    return steps


def spell_chord(root_pc: int, root_letter: str, intervals: tuple[int, ...]) -> list[str]:
    return [spell((root_pc + i) % 12, letter_offset(root_letter, st))
            for i, st in zip(intervals, _degree_steps(intervals))]


@dataclass(frozen=True)
class SpelledChord:
    root: int
    root_name: str
    intervals: tuple[int, ...]
    bass: int | None = None
    bass_name: str | None = None

    @property
    def quality(self) -> str:
        return quality_name(self.intervals)

    @property
    def symbol(self) -> str:
        s = self.root_name + self.quality
        if self.bass is not None and self.bass != self.root:
            s += "/" + (self.bass_name or NOTE_SHARP[self.bass])
        return s

    @property
    def notes(self) -> list[str]:
        return spell_chord(self.root, self.root_name[0], self.intervals)

    def to_chord(self) -> Chord:
        return Chord(self.symbol, self.root, self.intervals, self.bass if self.bass != self.root else None)

    def pitch_classes(self) -> set[int]:
        pcs = {(self.root + i) % 12 for i in self.intervals}
        if self.bass is not None:
            pcs.add(self.bass)
        return pcs

    @property
    def inversion(self) -> int:
        if self.bass is None or self.bass == self.root:
            return 0
        rel = (self.bass - self.root) % 12
        tones = [i % 12 for i in self.intervals]
        return tones.index(rel) if rel in tones else -1


NOTE_SHARP = theory.NOTE_NAMES


def spelled_from_symbol(symbol: str, key: Key | None = None) -> SpelledChord:
    """Parses a chord symbol keeping the user's spelling of the root (and bass)."""
    c = theory.parse_chord(symbol)
    m = re.match(r"^([A-G])([#b♯♭]*)", symbol.strip())
    root_name = spell(c.root, m.group(1))
    bass_name = None
    if c.bass is not None:
        bm = re.search(r"/([A-G][#b♯♭]*)$", symbol.strip())
        bass_name = spell(c.bass, bm.group(1)[0]) if bm else (key.spell_pc(c.bass) if key else NOTE_SHARP[c.bass])
    return SpelledChord(c.root, root_name, c.intervals, c.bass, bass_name)


def chord_in_key(root: int, intervals: tuple[int, ...], key: Key, bass: int | None = None) -> SpelledChord:
    root_name = key.spell_chord_root(root, intervals)
    bass_name = None
    if bass is not None and bass != root:
        tones = spell_chord(root, root_name[0], intervals)
        rel = (bass - root) % 12
        match = [n for i, n in zip(intervals, tones) if i % 12 == rel]
        bass_name = match[0] if match else key.spell_pc(bass)
    return SpelledChord(root, root_name, intervals, bass if bass != root else None, bass_name)


def identify_chord(pitches: list[int], bass: int | None = None, key: Key | None = None, limit: int = 4) -> list[dict]:
    """Names the chord a set of notes makes. pitches can be MIDI notes (the lowest is
    taken as the bass) or pitch classes. Returns the likeliest names first."""
    if not pitches:
        return []
    pcs = {p % 12 for p in pitches}
    if bass is None and any(p > 11 for p in pitches):
        bass = min(pitches) % 12
    results = []
    for root in pcs:
        rel = frozenset((p - root) % 12 for p in pcs)
        for shape, q, size in _ID_SHAPES:
            missing = shape - rel
            extra = rel - shape
            if extra:
                continue
            # Allow a missing 5th (and 11th in 13th chords), as players usually drop them.
            if missing - {7, 5 if size >= 7 else 99, 2 if size >= 6 else 99}:
                continue
            if len(rel) < 2:
                continue
            score = 100 - 3 * size - 12 * len(missing)
            if bass is not None:
                score += 10 if bass == root else (2 if bass in {(root + i) % 12 for i in shape} else -5)
            if q in ("", "m", "7", "maj7", "m7", "dim", "dim7", "m7b5", "aug", "5", "sus4", "sus2", "6", "m6"):
                score += 4
            if key is not None and root in key.pitch_classes():
                score += 3
            results.append((score, root, q, missing))
    results.sort(key=lambda r: -r[0])
    out, seen = [], set()
    for score, root, q, missing in results:
        intervals = CHORD_QUALITIES[q]
        k = key or Key(root, NOTE_SHARP[root][0] if "#" not in NOTE_SHARP[root] else NOTE_SHARP[root][0],
                       scales_db.find_scale("major"))
        sc = chord_in_key(root, intervals, k, bass) if key else SpelledChord(
            root, _plain_name(root), intervals, bass if bass != root else None,
            _plain_name(bass) if bass is not None and bass != root else None)
        if sc.symbol in seen:
            continue
        seen.add(sc.symbol)
        entry = {"symbol": sc.symbol, "root": sc.root_name, "quality": q or "major", "notes": sc.notes,
                 "confidence": round(max(0.05, min(1.0, score / 100)), 2)}
        if missing:
            entry["omitted"] = [{7: "5th", 5: "11th", 2: "9th"}.get(m, str(m)) for m in sorted(missing)]
        if sc.bass is not None:
            entry["inversion"] = {1: "first", 2: "second", 3: "third"}.get(sc.inversion, "slash bass")
        out.append(entry)
        if len(out) >= limit:
            break
    return out


_FLAT_NAMES = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")


def _plain_name(pc: int | None) -> str:
    """Spelling without a key: flats for black keys except F#."""
    if pc is None:
        return ""
    return "F#" if pc == 6 else _FLAT_NAMES[pc]


# ------------------------------------------------------------ Roman numerals

_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7}
_ROMAN_RE = re.compile(r"^(?P<acc>[b#♭♯]*)(?P<num>VII|VI|IV|V|III|II|I|vii|vi|iv|v|iii|ii|i)(?P<mark>[°oø+]?)(?P<rest>.*)$")
_FIGURES = ("64", "65", "43", "42", "6", "2")
_INVERSION = {"6": 1, "64": 2, "65": 1, "43": 2, "42": 3, "2": 3}


@dataclass(frozen=True)
class RomanChord:
    numeral: str
    chord: SpelledChord
    key: Key
    function: str = ""
    labels: tuple[str, ...] = field(default=())

    def describe(self) -> dict:
        d = {"numeral": self.numeral, "chord": self.chord.symbol, "notes": self.chord.notes}
        if self.function:
            d["function"] = self.function
        if self.labels:
            d["labels"] = list(self.labels)
        return d


def _ext_intervals(upper: bool, mark: str, ext: str, figure: str | None) -> tuple[int, ...]:
    seventh_figure = figure in ("65", "43", "42", "2")
    if mark in ("°", "o"):
        if ext in ("7",) or (ext == "" and seventh_figure):
            return CHORD_QUALITIES["dim7"]
        if ext == "":
            return CHORD_QUALITIES["dim"]
        return _lookup("dim" + ext) or _lookup("°" + ext) or _fail(ext)
    if mark == "ø":
        if ext in ("", "7"):
            return CHORD_QUALITIES["m7b5"]
        return _lookup("ø" + ext) or _lookup("m" + ext + "b5") or _fail(ext)
    if mark == "+":
        if ext == "" and not seventh_figure:
            return CHORD_QUALITIES["aug"]
        if ext in ("7", "") :
            return CHORD_QUALITIES["aug7"]
        if ext in ("maj7", "M7", "Δ", "Δ7"):
            return CHORD_QUALITIES["maj7#5"]
        return _lookup(ext + "#5") or _lookup("aug" + ext) or _fail(ext)
    if ext == "":
        if seventh_figure:
            return CHORD_QUALITIES["7" if upper else "m7"]
        return CHORD_QUALITIES["" if upper else "m"]
    # A sus chord has no 3rd, so a lower-case numeral doesn't make it minor: "v7sus4"
    # used to look for an unknown "m7sus4".
    if ext.startswith(("sus", "5")) or "sus" in ext or ext in ("no3",):
        return _lookup(ext) or _fail(ext)
    if ext in ("maj7", "M7", "Δ", "Δ7", "maj"):
        return CHORD_QUALITIES["maj7" if upper else "m(maj7)"]
    if ext in ("maj9", "M9"):
        return CHORD_QUALITIES["maj9" if upper else "m(maj9)"]
    if upper:
        return _lookup(ext) or _fail(ext)
    return _lookup("m" + ext) or _fail(ext)


def _lookup(q: str) -> tuple[int, ...] | None:
    return theory.lookup_quality(q)


def _fail(ext: str):
    raise ValueError(f"unknown chord extension '{ext}' in a Roman numeral (try 7, maj7, 9, 11, 13, sus4, add9, 7b9)")


def _split_figure(rest: str) -> tuple[str, str | None]:
    if re.search(r"(add|sus|b|#|no)\d*$", rest) or "6/9" in rest:
        return rest, None
    for f in _FIGURES:
        if rest.endswith(f):
            head = rest[: -len(f)]
            # "13", "11" end in digits that aren't figures; a figure follows a letter, 7, or nothing.
            if head == "" or not head[-1].isdigit() or (f in ("65", "43", "42") and head.endswith("7") is False):
                if f == "6" and head.endswith(("1", "/")):
                    return rest, None
                return head, f
    return rest, None


def parse_roman(numeral: str, key: Key) -> RomanChord:
    """One Roman numeral in a key -> the chord, spelled."""
    text = numeral.strip().replace("♭", "b").replace("♯", "#").replace("º", "°")
    if not text:
        raise ValueError("empty Roman numeral")
    special = _special_numeral(text, key)
    if special:
        return special
    if "/" in text and "6/9" not in text:
        head, _, target = text.partition("/")
        if target and not re.fullmatch(r"[A-G][#b]*", target):
            target_chord = parse_roman(target, key).chord
            third = (target_chord.intervals[1] % 12) if len(target_chord.intervals) > 1 else 4
            temp = Key(target_chord.root, target_chord.root_name[0],
                       scales_db.find_scale("minor" if third == 3 else "major"))
            inner = parse_roman(head, temp)
            return RomanChord(text, inner.chord, key, "secondary", (f"secondary chord: {head} of {target}",))
    m = _ROMAN_RE.match(text)
    if not m:
        raise ValueError(f"can't read the Roman numeral '{numeral}' (e.g. I, ii7, V7/V, bVII, viiø7, iv6, N6, Ger+6)")
    acc = m.group("acc").count("#") - m.group("acc").count("b")
    num = m.group("num")
    degree = _ROMAN[num.upper()]
    upper = num.isupper()
    mark = m.group("mark")
    rest = m.group("rest")
    ext, figure = _split_figure(rest)
    intervals = _ext_intervals(upper, mark, ext, figure)
    degs = key.degrees
    # Flats count from the major scale, as musicians use them (bVII, bVI, bIII and bII are
    # the same chords in every mode); sharps raise the mode's own degree (#iv°7, #vii°).
    base = MAJOR[degree - 1] if acc < 0 else degs[degree - 1]
    root = (key.tonic + base + acc) % 12
    if key.is_minor and degree == 7 and acc == 0 and mark in ("°", "o", "ø"):
        root = (key.tonic + 11) % 12  # leading-tone chord in minor
    letter = key.degree_letter(degree)
    root_name = spell(root, letter)
    inversion = _INVERSION.get(figure, 0) if figure else 0
    tones = [i % 12 for i in intervals]
    bass = (root + tones[inversion]) % 12 if 0 < inversion < len(tones) else None
    bass_name = spell_chord(root, letter, intervals)[inversion] if bass is not None else None
    chord = SpelledChord(root, root_name, intervals, bass, bass_name)
    return RomanChord(text, chord, key, _function(degree, acc, upper, mark, key))


def _special_numeral(text: str, key: Key) -> RomanChord | None:
    t = text.replace(" ", "")
    low = t.lower()
    tonic = key.tonic
    if low in ("n", "n6", "bii6", "neapolitan"):
        root = (tonic + 1) % 12
        name = spell(root, key.degree_letter(2))
        iv = CHORD_QUALITIES[""]
        inv = low != "n"
        bass = (root + 4) % 12 if inv else None
        chord = SpelledChord(root, name, iv, bass, spell_chord(root, name[0], iv)[1] if inv else None)
        return RomanChord(text, chord, key, "predominant", ("Neapolitan sixth: a major chord on the flat 2nd, usually in first inversion, leading to V",))
    six = re.fullmatch(r"(it|fr|ger|sw)\+?6", low)
    if six:
        kind = six.group(1)
        root = (tonic + 8) % 12  # the b6 in the bass
        name = spell(root, key.degree_letter(6))
        iv = {"it": CHORD_QUALITIES["7no5"], "fr": CHORD_QUALITIES["7b5"], "ger": CHORD_QUALITIES["7"],
              "sw": CHORD_QUALITIES["7"]}[kind]
        chord = SpelledChord(root, name, iv)
        label = {"it": "Italian", "fr": "French", "ger": "German", "sw": "Swiss"}[kind]
        return RomanChord(text, chord, key, "predominant",
                          (f"{label} augmented sixth: b6 in the bass against #4 (written as a b7 here), expanding out to the octave on V",))
    if low in ("cad64", "cad6/4", "i64cad"):
        inner = parse_roman("i64" if key.is_minor else "I64", key)
        return RomanChord(text, inner.chord, key, "dominant", ("cadential 6/4: tonic notes over the dominant bass, resolving to V",))
    return None


def _function(degree: int, acc: int, upper: bool, mark: str, key: Key) -> str:
    if acc:
        return "chromatic"
    if key.is_minor:
        return {1: "tonic", 2: "predominant", 3: "tonic", 4: "predominant", 5: "dominant", 6: "predominant",
                7: "dominant" if mark else "subtonic"}[degree]
    return {1: "tonic", 2: "predominant", 3: "tonic", 4: "predominant", 5: "dominant", 6: "tonic", 7: "dominant"}[degree]


def split_numerals(progression: str) -> list[str]:
    return [p for p in re.split(r"\s*[-–—|,]\s*|\s+", progression.strip()) if p]


def parse_progression(progression: str | list[str], key: Key) -> list[RomanChord]:
    items = split_numerals(progression) if isinstance(progression, str) else list(progression)
    return [parse_roman(p, key) for p in items]


# ----------------------------------------------------- chord -> Roman numeral

_DIATONIC_CACHE: dict[tuple, list] = {}


def diatonic_chords(key: Key, sevenths: bool = False) -> list[SpelledChord]:
    """Triads (or 7ths) built on each degree of a seven-note key."""
    degs = key.degrees
    out = []
    for i in range(7):
        stack = [degs[(i + k) % 7] + (12 if i + k >= 7 else 0) for k in (0, 2, 4, 6)]
        if not sevenths:
            stack = stack[:3]
        root_rel = stack[0]
        intervals = tuple(s - root_rel for s in stack)
        root = (key.tonic + root_rel) % 12
        out.append(SpelledChord(root, spell(root, key.degree_letter(i + 1)), intervals))
    return out


def numeral_for(chord: SpelledChord, key: Key) -> RomanChord:
    """Names a chord as a Roman numeral in a key, with its function and what's
    special about it (secondary dominant, borrowed, Neapolitan, tritone sub...)."""
    degs = key.degrees
    rel = (chord.root - key.tonic) % 12
    iv = chord.intervals
    shape = {i % 12 for i in iv}
    q = chord.quality
    is_dim = {3, 6} <= shape and 7 not in shape
    if rel in degs:
        degree, acc = degs.index(rel) + 1, 0
    else:
        flat = [i for i, d in enumerate(MAJOR) if d == (rel + 1) % 12]
        sharp = [i for i, d in enumerate(degs) if d == (rel - 1) % 12]
        if key.is_minor and rel == 11 and is_dim:
            degree, acc = 7, 0
        elif (is_dim and sharp) or not flat or (key.is_minor and rel in (4, 9, 11) and sharp):
            # In minor the raised 3rd, 6th and 7th are #III, #VI, #VII (C# major in A
            # minor was "bIV", G# major "bI").
            degree, acc = sharp[0] + 1, 1
        else:
            degree, acc = flat[0] + 1, -1
    upper = 4 in shape or (3 not in shape and not is_dim)
    base = list(_ROMAN)[degree - 1]
    base = base if upper else base.lower()
    suffix = _numeral_suffix(q, upper)
    figure = ""
    inv = chord.inversion
    if inv > 0:
        is7 = len(iv) >= 4 and (10 in shape or 11 in shape or (is_dim and 9 in shape))
        figure = {1: "65", 2: "43", 3: "42"}[inv] if is7 and len(iv) == 4 else ({1: "6", 2: "64"}.get(inv, "") if len(iv) == 3 else "")
        if figure and suffix in ("7", "°7", "ø7", "maj7"):
            suffix = suffix.replace("7", "")
            if suffix == "maj" and _is_diatonic(chord, key):
                suffix = ""  # a diatonic 7th's quality is implied by the figure (IV43)
        elif not figure:
            figure = f" (bass {chord.bass_name or ''})"
    numeral = accidental_text(acc) + base + suffix + figure
    labels: list[str] = []
    function = _function(degree, acc, upper, "°" if is_dim else "", key) if acc == 0 else "chromatic"
    diatonic = _is_diatonic(chord, key)
    if not diatonic:
        labels += _chromatic_labels(chord, key, rel, shape, q)
        if function != "chromatic" and labels:
            function = "chromatic"
    if labels and labels[0].startswith("secondary"):
        function = "secondary dominant"
    elif labels and labels[0].startswith("borrowed"):
        function = {0: "tonic", 1: "predominant", 2: "predominant", 3: "tonic", 5: "predominant", 7: "dominant",
                    8: "predominant", 10: "subtonic (dominant substitute)"}.get(rel, "chromatic")
    if inv == -1 and chord.bass is not None:
        over = (chord.bass - key.tonic) % 12
        note = f"over {chord.bass_name} in the bass (not a chord tone)"
        if over == 7 and rel in (2, 5):
            note += ": a dominant sus sound, works like V9sus4 / V11"
        labels.append(note)
    return RomanChord(numeral, chord, key, function, tuple(labels))


def _numeral_suffix(q: str, upper: bool) -> str:
    table = {"": "", "m": "", "dim": "°", "dim7": "°7", "m7b5": "ø7", "aug": "+", "aug7": "+7", "maj7#5": "+maj7",
             "7": "7", "m7": "7", "maj7": "maj7", "m(maj7)": "maj7", "m9": "9", "m11": "11", "m13": "13",
             "m6": "add6", "6": "add6", "madd9": "add9", "m6/9": "6/9", "m(maj9)": "maj9", "m9b5": "ø9"}
    if q in table:
        return table[q]
    if not upper and q.startswith("m"):
        return q[1:]
    return q


def _is_diatonic(chord: SpelledChord, key: Key) -> bool:
    return chord.pitch_classes() <= key.pitch_classes() or (
        key.is_minor and chord.pitch_classes() <= {(key.tonic + i) % 12 for i in (0, 2, 3, 5, 7, 8, 10, 11)})


PARALLEL_MODES = ("minor", "major", "dorian", "mixolydian", "phrygian", "lydian", "harmonic minor", "melodic minor", "locrian")


def _chromatic_labels(chord: SpelledChord, key: Key, rel: int, shape: set[int], q: str) -> list[str]:
    labels = []
    dominant = {4, 10} <= shape or shape == {0, 4, 7}
    diatonic_roots = [(key.tonic + d) % 12 for d in key.degrees]
    if dominant:
        target = (chord.root + 5) % 12  # a 5th below = resolves to
        if target in diatonic_roots and target != chord.root:
            t_deg = diatonic_roots.index(target) + 1
            t_chord = diatonic_chords(key)[t_deg - 1]
            t_num = numeral_for(t_chord, key).numeral if t_deg != 1 else ("i" if key.is_minor else "I")
            # A diminished chord isn't tonicized: no "V/ii°" in minor (nor V/vii° in major).
            if t_chord.quality not in ("dim", "dim7", "m7b5"):
                labels.append(f"secondary dominant: V{'7' if 10 in shape else ''}/{t_num} (pulls to {t_chord.symbol})")
        sub_target = (chord.root - 1) % 12
        if 10 in shape and sub_target in diatonic_roots:
            t_deg = diatonic_roots.index(sub_target) + 1
            t_chord = diatonic_chords(key)[t_deg - 1]
            labels.append(f"tritone substitute: subV7 of {t_chord.symbol} (replaces the V7 a tritone away, bass falls a half step)")
    if {3, 6} <= shape and 7 not in shape:
        target = (chord.root + 1) % 12
        if target in diatonic_roots:
            t_chord = diatonic_chords(key)[diatonic_roots.index(target)]
            labels.append(f"leading-tone chord: vii°{'7' if 9 in shape else ('ø7' if 10 in shape else '')}/{t_chord.symbol} (resolves up a half step)")
    if rel == 1 and shape == {0, 4, 7}:
        labels.append("Neapolitan: major chord on the flat 2nd, a classic predominant before V")
    if rel == 8 and shape in ({0, 4, 10}, {0, 4, 6, 10}):
        labels.append("augmented sixth chord (Italian/French): resolves outward to V")
    for mode in PARALLEL_MODES:
        if mode == key.scale.name or labels:
            continue
        parallel = Key(key.tonic, key.letter, scales_db.find_scale(mode))
        if chord.pitch_classes() <= parallel.pitch_classes():
            labels.append(f"borrowed from {parallel.name} (modal interchange)")
            break
    third_rel = (rel % 12)
    if not labels and third_rel in (3, 4, 8, 9) and shape in ({0, 4, 7}, {0, 3, 7}):
        labels.append("chromatic mediant: a third away from the tonic with a surprising, cinematic colour")
    if not labels:
        labels.append("chromatic chord outside the key")
    return labels


# ----------------------------------------------------------- key detection

_KK_MAJOR = (6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88)
_KK_MINOR = (6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17)


def _pearson(a: list[float], b: tuple[float, ...]) -> float:
    ma, mb = sum(a) / 12, sum(b) / 12
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den if den else 0.0


def detect_key(histogram: list[float], tonic_hint: int | None = None, top: int = 3,
               spelling: dict[int, str] | None = None) -> list[dict]:
    """Ranks keys for a duration-weighted pitch-class histogram (Krumhansl-Kessler
    profiles), then checks whether a church mode fits better than major/minor."""
    if sum(histogram) <= 0:
        return []
    scores = []
    for t in range(12):
        rotated = histogram[t:] + histogram[:t]
        for mode, profile in (("major", _KK_MAJOR), ("minor", _KK_MINOR)):
            r = _pearson(rotated, profile)
            if tonic_hint is not None and t == tonic_hint:
                r += 0.08
            scores.append((r, t, mode))
    scores.sort(reverse=True)
    total = sum(histogram)
    out = []
    used = set()
    for r, t, mode in scores:
        best_mode, best_fit = mode, _fit(histogram, t, mode)
        for alt in (("dorian", "phrygian", "harmonic minor") if mode == "minor" else ("mixolydian", "lydian")):
            fit = _fit(histogram, t, alt)
            if fit > best_fit + 0.04:
                best_mode, best_fit = alt, fit
        if (t, best_mode) in used:
            continue
        used.add((t, best_mode))
        letter = (spelling or {}).get(t) or _simplest_tonic(t, best_mode)
        key = parse_key(f"{letter} {best_mode}")
        outside = [key.spell_pc(pc) for pc in range(12)
                   if histogram[pc] / total > 0.03 and pc not in key.pitch_classes()]
        entry = {"key": key.name, "correlation": round(r, 3), "notes_in_key_pct": round(100 * best_fit, 1)}
        if outside:
            entry["outside_notes"] = outside
        out.append(entry)
        if len(out) >= top:
            break
    if out:
        gap = out[0]["correlation"] - (out[1]["correlation"] if len(out) > 1 else 0)
        out[0]["confidence"] = "high" if gap > 0.1 and out[0]["correlation"] > 0.7 else ("medium" if gap > 0.03 else "low")
    return out


def _simplest_tonic(pc: int, mode: str) -> str:
    """The tonic's name with the simpler key signature: C# minor (4 sharps), not Db minor
    (8 flats, spelled with Fb and Bbb); Db major, not C# major. Ties keep the flat."""
    names = [_plain_name(pc)]
    if "b" in names[0] or names[0] == "F#":
        names.append(NOTE_SHARP[pc] if names[0] != "F#" else "Gb")
    def accidentals(name: str) -> int:
        # Counted on the spelled scale, so theoretical keys (Fb major behind Db minor)
        # score high instead of missing from the key-signature table.
        return sum(n.count("#") + n.count("b") for n in parse_key(f"{name} {mode}").spell_scale())

    best = names[0]
    try:
        fewest = accidentals(best)
        for other in names[1:]:
            if accidentals(other) < fewest:
                best, fewest = other, accidentals(other)
    except ValueError:
        pass
    return best


def _fit(histogram: list[float], tonic: int, mode: str) -> float:
    pcs = {(tonic + i) % 12 for i in scales_db.find_scale(mode).intervals}
    total = sum(histogram)
    return sum(histogram[pc] for pc in pcs) / total if total else 0.0


def histogram_from_notes(notes: list[dict]) -> list[float]:
    h = [0.0] * 12
    for n in notes:
        h[n["pitch"] % 12] += max(0.05, n.get("length", 1.0)) * (0.5 + n.get("velocity", 96) / 254)
    return h


def histogram_from_chords(chords: list[tuple[SpelledChord, float]]) -> tuple[list[float], int | None]:
    h = [0.0] * 12
    for c, length in chords:
        for pc in c.pitch_classes():
            h[pc] += length
        h[c.root] += length  # roots count double
    hint = chords[-1][0].root if chords else None
    if chords:
        h[chords[0][0].root] += chords[0][1] * 0.5
    return h, hint


# ------------------------------------------------------ progression analysis

def cadences(numerals: list[RomanChord]) -> list[dict]:
    """Cadences and famous moves between neighbouring chords."""
    found = []

    def deg(rc: RomanChord) -> tuple[int, int] | None:
        rel = (rc.chord.root - rc.key.tonic) % 12
        return rel, rc.chord.quality and 0

    n = len(numerals)
    for i in range(n - 1):
        a, b = numerals[i], numerals[i + 1]
        ra, rb = (a.chord.root - a.key.tonic) % 12, (b.chord.root - b.key.tonic) % 12
        sa, sb = {x % 12 for x in a.chord.intervals}, {x % 12 for x in b.chord.intervals}
        a_dom = ra in (7, 11) and (4 in sa or {3, 6} <= sa)
        b_tonic = rb == 0
        name = None
        if a_dom and b_tonic:
            name = "authentic cadence (V-I): the strongest resolution home"
            if a.chord.inversion == 0 and b.chord.inversion == 0 and i + 1 == n - 1:
                name = "authentic cadence (V-I), root position: perfect if the melody ends on the tonic"
        elif ra == 5 and b_tonic:
            name = "plagal cadence (IV-I): the 'amen' close" if 4 in sa else "minor plagal cadence (iv-I): bittersweet, borrowed iv"
        elif ra == 7 and 4 in sa and rb == 9 and 3 in sb:
            name = "deceptive cadence (V-vi): sets up home, then sidesteps"
        elif ra == 7 and 4 in sa and rb == 8 and 4 in sb:
            name = "deceptive cadence (V-bVI): the dramatic sidestep"
        elif ra == 10 and 4 in sa and b_tonic:
            name = "subtonic cadence (bVII-I): rock/Mixolydian resolution"
        elif ra == 1 and b_tonic:
            name = "bII-I: Phrygian or tritone-substitute resolution"
        elif ra == 5 and 3 in sa and a.chord.inversion == 1 and rb == 7:
            name = "Phrygian half cadence (iv6-V): the Baroque minor-key pause"
        elif rb == 7 and i + 1 == n - 1 and 4 in sb:
            name = "half cadence: ends on V, open, asking for more"
        if name:
            found.append({"at": i + 1, "chords": f"{a.numeral} -> {b.numeral}", "cadence": name})
        if i + 2 < n:
            c = numerals[i + 2]
            rc = (c.chord.root - c.key.tonic) % 12
            if ra == 2 and rb == 7 and rc == 0:
                found.append({"at": i + 1, "chords": f"{a.numeral} -> {b.numeral} -> {c.numeral}",
                              "cadence": "ii-V-I: the backbone of jazz harmony"})
            if ra == 8 and rb == 10 and rc == 0:
                found.append({"at": i + 1, "chords": f"{a.numeral} -> {b.numeral} -> {c.numeral}",
                              "cadence": "bVI-bVII-I: the Aeolian/'Mario' cadence, heroic and triumphant"})
            if ra == 5 and 3 in sa and rb == 10 and rc == 0:
                found.append({"at": i + 1, "chords": f"{a.numeral} -> {b.numeral} -> {c.numeral}",
                              "cadence": "backdoor cadence (iv-bVII-I): soft, soulful way home"})
    if n >= 2 and (numerals[-1].chord.root - numerals[-1].key.tonic) % 12 == 0 and numerals[-1].key.is_minor \
            and 4 in {x % 12 for x in numerals[-1].chord.intervals}:
        found.append({"at": n, "chords": numerals[-1].numeral, "cadence": "Picardy third: a minor piece ending on a major tonic"})
    return found


def negative_pc(pc: int, tonic: int) -> int:
    """Negative harmony: reflect around the axis between the b3 and 3 of the key."""
    return (2 * tonic + 7 - pc) % 12


def negative_pitch(pitch: int, tonic: int) -> int:
    base = 2 * tonic + 7 - pitch
    best = min((base + 12 * k for k in range(-12, 13)), key=lambda p: abs(p - pitch))
    return max(0, min(127, best))


def negative_chord(chord: SpelledChord, key: Key) -> SpelledChord:
    pcs = [negative_pc((chord.root + i) % 12, key.tonic) for i in chord.intervals]
    bass = negative_pc(chord.bass, key.tonic) if chord.bass is not None else None
    found = identify_chord(pcs, key=key, limit=1)
    if not found:
        raise ValueError(f"couldn't name the negative of {chord.symbol}")
    best = spelled_from_symbol(found[0]["symbol"], key)
    sc = chord_in_key(best.root, best.intervals, key, bass)
    return sc


# ---------------------------------------------------------------- modulation

def key_distance(a: Key, b: Key) -> dict:
    common = a.pitch_classes() & b.pitch_classes()
    rel_a = (a.tonic - _mode_offset(a.degrees)) % 12
    rel_b = (b.tonic - _mode_offset(b.degrees)) % 12
    steps = min((rel_a - rel_b) * 7 % 12, (rel_b - rel_a) * 7 % 12)
    return {"common_notes": len(common), "circle_of_fifths_steps": steps}


def pivot_chords(a: Key, b: Key, sevenths: bool = False) -> list[dict]:
    out = []
    b_chords = {(c.root, c.intervals): c for c in diatonic_chords(b, sevenths)}
    for c in diatonic_chords(a, sevenths):
        if (c.root, c.intervals) in b_chords:
            na, nb = numeral_for(c, a), numeral_for(b_chords[(c.root, c.intervals)], b)
            out.append({"chord": c.symbol, "in_old_key": na.numeral, "in_new_key": nb.numeral,
                        "role_in_new_key": nb.function})
    order = {"predominant": 0, "tonic": 1, "dominant": 2, "subtonic": 3}
    out.sort(key=lambda d: order.get(d["role_in_new_key"], 4))
    return out


def modulation_routes(a: Key, b: Key) -> list[dict]:
    """Ways to get from key a to key b, smoothest first, each as a chord sequence."""
    a_tonic = parse_roman("i" if a.is_minor else "I", a).chord
    b_tonic = parse_roman("i" if b.is_minor else "I", b).chord
    b_v7 = parse_roman("V7", b).chord
    routes = []
    pivots = pivot_chords(a, b)
    if pivots:
        p = pivots[0]
        routes.append({"technique": "pivot chord",
                       "chords": [a_tonic.symbol, p["chord"], b_v7.symbol, b_tonic.symbol],
                       "how": f"{p['chord']} is {p['in_old_key']} in {a.name} and {p['in_new_key']} in {b.name}; "
                              "treat it as the new key's predominant, then cadence V7-I in the new key."})
    routes.append({"technique": "secondary dominant (direct)",
                   "chords": [a_tonic.symbol, b_v7.symbol, b_tonic.symbol],
                   "how": f"Play the new key's V7 ({b_v7.symbol}) straight after the old tonic: quick and clear."})
    ii = parse_roman("iiø7" if b.is_minor else "ii7", b).chord
    routes.append({"technique": "ii-V into the new key",
                   "chords": [a_tonic.symbol, ii.symbol, b_v7.symbol, b_tonic.symbol],
                   "how": "The jazz way: approach the new tonic with its own ii-V."})
    common = sorted(set(a_tonic.pitch_classes()) & set(b_tonic.pitch_classes()))
    if common:
        routes.append({"technique": "common-tone modulation",
                       "chords": [a_tonic.symbol, b_tonic.symbol],
                       "how": f"Hold {a.spell_pc(common[0])} (in both tonic chords) in the melody or a pad while the harmony shifts."})
    interval = (b.tonic - a.tonic) % 12
    if interval in (3, 4, 8, 9):
        routes.append({"technique": "chromatic mediant (direct)",
                       "chords": [a_tonic.symbol, b_tonic.symbol],
                       "how": "Keys a third apart: just move. Film composers do it for a sudden change of light."})
    if interval in (1, 2):
        routes.append({"technique": "truck-driver key change",
                       "chords": [a_tonic.symbol, b_v7.symbol, b_tonic.symbol],
                       "how": "Up a half or whole step for the last chorus: the classic pop lift."})
    dim = parse_roman("vii°7", b).chord
    routes.append({"technique": "diminished seventh pivot",
                   "chords": [a_tonic.symbol, dim.symbol, b_tonic.symbol],
                   "how": f"{dim.symbol} resolves to {b_tonic.symbol}; any dim7 can be respelled to lead to four keys."})
    return routes
