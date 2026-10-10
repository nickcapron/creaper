"""Scales and modes: interval patterns with what they sound like and where they're used.

Intervals are semitones above the tonic. Scales from outside Western 12-tone music
(maqamat, ragas, gamelan tunings) are their nearest 12-tone versions and say so.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Scale:
    name: str
    intervals: tuple[int, ...]
    family: str
    sound: str
    aliases: tuple[str, ...] = ()


S = Scale
SCALE_LIST: tuple[Scale, ...] = (
    # The diatonic modes (rotations of the major scale), brightest to darkest.
    S("lydian", (0, 2, 4, 6, 7, 9, 11), "diatonic mode",
      "The brightest mode: major with a raised 4th. Dreamy, floating, wonder; film scores, Satriani, prog.",
      ("lydian mode", "yaman", "kalyan")),
    S("major", (0, 2, 4, 5, 7, 9, 11), "diatonic mode",
      "Bright and settled. The default for pop, classical, country and most happy music.",
      ("ionian", "major scale", "bilawal", "ajam")),
    S("mixolydian", (0, 2, 4, 5, 7, 9, 10), "diatonic mode",
      "Major with a flat 7th: bluesy, laid-back, anthemic. Rock (I-bVII-IV), funk, Celtic, jam bands.",
      ("mixolydian mode", "dominant scale", "khamaj")),
    S("dorian", (0, 2, 3, 5, 7, 9, 10), "diatonic mode",
      "Minor with a bright 6th: cool, soulful, hopeful-minor. Funk, jazz modal tunes, house, Santana, Celtic.",
      ("dorian mode", "kafi")),
    S("minor", (0, 2, 3, 5, 7, 8, 10), "diatonic mode",
      "Natural minor: sad, serious, dramatic. Pop ballads, EDM, film, metal, most minor-key music.",
      ("aeolian", "natural minor", "minor scale", "asavari")),
    S("phrygian", (0, 1, 3, 5, 7, 8, 10), "diatonic mode",
      "Minor with a flat 2nd: dark, Spanish, menacing. Metal riffs, flamenco, film tension, drill.",
      ("phrygian mode", "bhairavi", "kurd")),
    S("locrian", (0, 1, 3, 5, 6, 8, 10), "diatonic mode",
      "Diminished tonic: unstable and unresolved. Rare as a home key; metal riffs, dissonant textures.",
      ("locrian mode",)),
    # Melodic minor and its modes: the core of jazz harmony.
    S("melodic minor", (0, 2, 3, 5, 7, 9, 11), "melodic minor mode",
      "Minor with a major 6th and 7th: sophisticated, bittersweet. Jazz minor tonic (m6, mMaj7), film noir.",
      ("jazz minor", "ascending melodic minor")),
    S("dorian b2", (0, 1, 3, 5, 7, 9, 10), "melodic minor mode",
      "Phrygian with a natural 6th: exotic minor; jazz over sus(b9) chords.",
      ("phrygian #6", "phrygian natural 6")),
    S("lydian augmented", (0, 2, 4, 6, 8, 9, 11), "melodic minor mode",
      "Lydian with a raised 5th: shimmering, unstable; over maj7#5 chords.", ("lydian #5",)),
    S("lydian dominant", (0, 2, 4, 6, 7, 9, 10), "melodic minor mode",
      "Major with #4 and b7, like the harmonic series: bright and bluesy at once. Jazz over 7#11 and tritone subs; the Simpsons theme.",
      ("lydian b7", "acoustic scale", "overtone scale", "mixolydian #4")),
    S("mixolydian b6", (0, 2, 4, 5, 7, 8, 10), "melodic minor mode",
      "Major turning minor: hopeful then melancholy. Film, prog, 'major with a sad 6th'.",
      ("aeolian dominant", "hindu scale", "melodic major")),
    S("half-diminished", (0, 2, 3, 5, 6, 8, 10), "melodic minor mode",
      "Locrian with a natural 2nd: the jazz choice over m7b5 chords.", ("locrian #2", "locrian natural 2")),
    S("altered", (0, 1, 3, 4, 6, 8, 10), "melodic minor mode",
      "Every tension on a dominant (b9 #9 #11 b13): maximum pull to resolve. Jazz over V7alt.",
      ("super locrian", "altered dominant", "diminished whole tone")),
    # Harmonic minor and its modes.
    S("harmonic minor", (0, 2, 3, 5, 7, 8, 11), "harmonic minor mode",
      "Minor with a raised 7th, giving a true dominant (V7) and an exotic augmented 2nd. Classical minor keys, neoclassical metal, tango.",
      ("harmonic minor scale", "nahawand")),
    S("locrian #6", (0, 1, 3, 5, 6, 9, 10), "harmonic minor mode", "Dark and unusual; over m7b5 in harmonic-minor contexts."),
    S("ionian #5", (0, 2, 4, 5, 8, 9, 11), "harmonic minor mode", "Major with a raised 5th: tense and bright; over maj7#5.",
      ("ionian augmented",)),
    S("ukrainian dorian", (0, 2, 3, 6, 7, 9, 10), "harmonic minor mode",
      "Dorian with a raised 4th: Eastern European, klezmer, Romani music.",
      ("dorian #4", "romanian minor", "mi sheberach", "nikriz")),
    S("phrygian dominant", (0, 1, 4, 5, 7, 8, 10), "harmonic minor mode",
      "Phrygian with a major 3rd: flamenco, Middle Eastern, klezmer, metal. The V chord of harmonic minor as a home key.",
      ("spanish phrygian", "freygish", "hijaz", "ahava rabbah", "spanish gypsy")),
    S("lydian #2", (0, 3, 4, 6, 7, 9, 11), "harmonic minor mode", "Bright with a twisted, exotic edge; rare.",),
    S("ultralocrian", (0, 1, 3, 4, 6, 8, 9), "harmonic minor mode",
      "The darkest harmonic-minor mode; over diminished 7th chords.", ("altered bb7", "superlocrian bb7")),
    # Other heptatonic scales.
    S("harmonic major", (0, 2, 4, 5, 7, 8, 11), "heptatonic",
      "Major with a minor 6th: the borrowed iv chord built in; romantic, film, Beatles-like turns."),
    S("double harmonic", (0, 1, 4, 5, 7, 8, 11), "heptatonic",
      "Two augmented 2nds: strongly Middle Eastern and Indian. Belly-dance, Misirlou-style surf, film.",
      ("double harmonic major", "byzantine", "arabic", "bhairav", "gypsy major")),
    S("hungarian minor", (0, 2, 3, 6, 7, 8, 11), "heptatonic",
      "Harmonic minor with a raised 4th: dramatic, Romani, neoclassical metal.",
      ("double harmonic minor", "gypsy minor", "algerian")),
    S("hungarian major", (0, 3, 4, 6, 7, 9, 10), "heptatonic", "Exotic dominant colour with #2 and #4."),
    S("neapolitan major", (0, 1, 3, 5, 7, 9, 11), "heptatonic", "Dark start (b2, b3) with a bright top; operatic."),
    S("neapolitan minor", (0, 1, 3, 5, 7, 8, 11), "heptatonic", "Harmonic minor with a b2: dark and dramatic."),
    S("enigmatic", (0, 1, 4, 6, 8, 10, 11), "heptatonic", "Verdi's puzzle scale: ambiguous, eerie."),
    S("persian", (0, 1, 4, 5, 6, 8, 11), "heptatonic", "Highly chromatic and exotic; film, Middle Eastern colour."),
    S("todi", (0, 1, 3, 6, 7, 8, 11), "heptatonic", "12-tone version of raga Todi's scale (thaat Todi): serious, devotional.",
      ("raga todi", "thaat todi")),
    S("purvi", (0, 1, 4, 6, 7, 8, 11), "heptatonic", "12-tone version of thaat Purvi: dusk, mysterious.", ("raga purvi", "thaat purvi")),
    S("marwa", (0, 1, 4, 6, 7, 9, 11), "heptatonic", "12-tone version of thaat Marwa: restless, sunset.", ("raga marwa", "thaat marwa")),
    # Pentatonic scales.
    S("major pentatonic", (0, 2, 4, 7, 9), "pentatonic",
      "Major without the half steps: open, sunny, impossible to sound wrong. Folk, country, pop hooks, East Asian music.",
      ("pentatonic major", "gong")),
    S("minor pentatonic", (0, 3, 5, 7, 10), "pentatonic",
      "The rock and blues soloing scale: earthy and strong. Riffs, hooks, guitar solos, hip-hop melodies.",
      ("pentatonic minor", "yu")),
    S("egyptian", (0, 2, 5, 7, 10), "pentatonic", "Suspended pentatonic: open and ancient-sounding.",
      ("suspended pentatonic", "shang")),
    S("man gong", (0, 3, 5, 8, 10), "pentatonic", "Minor pentatonic's darker rotation; Chinese 'jue' mode.",
      ("jue", "blues minor pentatonic")),
    S("ritusen", (0, 2, 5, 7, 9), "pentatonic", "Japanese 'yo' scale and Chinese 'zhi': bright and folk-like.",
      ("yo", "zhi", "scottish pentatonic")),
    S("dominant pentatonic", (0, 2, 4, 7, 10), "pentatonic", "Major pentatonic with a b7: for dominant 7th chords."),
    S("hirajoshi", (0, 2, 3, 7, 8), "pentatonic", "Japanese koto scale: melancholy, delicate."),
    S("in sen", (0, 1, 5, 7, 10), "pentatonic", "Japanese shakuhachi colour: sparse, haunting.", ("insen",)),
    S("iwato", (0, 1, 5, 6, 10), "pentatonic", "Very dark Japanese scale with a b5."),
    S("kumoi", (0, 2, 3, 7, 9), "pentatonic", "Japanese minor pentatonic with a bright 6th."),
    S("pelog", (0, 1, 3, 7, 8), "pentatonic", "12-tone version of Balinese/Javanese pelog (real gamelan tuning differs).",
      ("pelog approx",)),
    S("slendro", (0, 2, 5, 7, 9), "pentatonic", "12-tone version of Javanese slendro (really five near-equal steps).",
      ("slendro approx",)),
    # Six-note scales.
    S("blues", (0, 3, 5, 6, 7, 10), "hexatonic",
      "Minor pentatonic plus the b5 'blue note': gritty and expressive. Blues, rock, jazz, funk.",
      ("minor blues", "blues scale")),
    S("major blues", (0, 2, 3, 4, 7, 9), "hexatonic", "Major pentatonic plus the b3 rubbing on the 3rd: country, gospel, swing.",
      ("blues major",)),
    S("whole tone", (0, 2, 4, 6, 8, 10), "symmetric",
      "All whole steps, no pull home: dreamlike, suspended. Debussy, dream sequences, over 7#5 chords.",
      ("whole-tone", "wholetone")),
    S("augmented", (0, 3, 4, 7, 8, 11), "symmetric", "Two augmented triads interlocked: jazz (Coltrane, Oliver Nelson), sci-fi.",
      ("augmented scale",)),
    S("prometheus", (0, 2, 4, 6, 9, 10), "hexatonic", "Scriabin's mystic colour: shimmering and unresolved.", ("mystic",)),
    S("tritone", (0, 1, 4, 6, 7, 10), "symmetric", "Two major triads a tritone apart: Petrushka-like tension.",
      ("petrushka",)),
    # Eight-note scales.
    S("diminished half-whole", (0, 1, 3, 4, 6, 7, 9, 10), "symmetric",
      "Half then whole steps: the jazz choice over 7b9 chords; tense, cinematic.",
      ("dominant diminished", "half-whole diminished", "octatonic half-whole")),
    S("diminished whole-half", (0, 2, 3, 5, 6, 8, 9, 11), "symmetric",
      "Whole then half steps: over diminished 7th chords; Stravinsky, horror and thriller cues.",
      ("diminished", "whole-half diminished", "octatonic")),
    S("bebop dominant", (0, 2, 4, 5, 7, 9, 10, 11), "bebop",
      "Mixolydian plus the major 7th as a passing note, so chord tones land on the beats in 8th-note lines.",
      ("bebop", "bebop mixolydian")),
    S("bebop major", (0, 2, 4, 5, 7, 8, 9, 11), "bebop", "Major plus a passing #5: swing lines over major chords."),
    S("bebop dorian", (0, 2, 3, 4, 5, 7, 9, 10), "bebop", "Dorian plus a passing major 3rd: bebop lines over m7.",
      ("bebop minor",)),
    S("bebop melodic minor", (0, 2, 3, 5, 7, 8, 9, 11), "bebop", "Melodic minor plus a passing #5."),
    S("spanish 8-tone", (0, 1, 3, 4, 5, 6, 8, 10), "octatonic",
      "Phrygian with both 3rds: flamenco and Spanish colour.", ("spanish eight-tone", "flamenco")),
    S("chromatic", tuple(range(12)), "chromatic", "All twelve notes."),
)


def _key(name: str) -> str:
    return re.sub(r"[\s_\-]+", " ", name.strip().lower()).replace("♭", "b").replace("♯", "#")


_BY_NAME: dict[str, Scale] = {}
for _s in SCALE_LIST:
    for _n in (_s.name, *_s.aliases):
        _BY_NAME.setdefault(_key(_n), _s)
_BY_NAME.setdefault("aeolian mode", _BY_NAME["minor"])
_BY_NAME.setdefault("ionian mode", _BY_NAME["major"])


def find_scale(name: str) -> Scale:
    key = _key(name)
    for candidate in (key, key.removesuffix(" scale"), key.removesuffix(" mode")):
        if candidate in _BY_NAME:
            return _BY_NAME[candidate]
    raise ValueError(f"unknown scale or mode '{name}'. Known: {', '.join(s.name for s in SCALE_LIST)}")


def scale_names() -> list[str]:
    return sorted(_BY_NAME)


def all_intervals() -> dict[str, tuple[int, ...]]:
    """Every name and alias -> intervals (for simple lookups)."""
    return {name: s.intervals for name, s in _BY_NAME.items()}


def scales_containing(pitch_classes: set[int], tonic: int | None = None, families: tuple[str, ...] | None = None) -> list[tuple[Scale, int]]:
    """Scales (and tonics) that contain every given pitch class, fewest extra notes first."""
    found = []
    for s in SCALE_LIST:
        if s.name == "chromatic" or (families and s.family not in families):
            continue
        for t in ([tonic] if tonic is not None else range(12)):
            pcs = {(t + i) % 12 for i in s.intervals}
            if pitch_classes <= pcs:
                found.append((len(pcs - pitch_classes), s, t))
    found.sort(key=lambda x: (x[0], len(x[1].intervals)))
    return [(s, t) for _, s, t in found]
