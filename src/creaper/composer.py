"""Composition and analysis on top of harmony.py.

- A library of named progressions, plus suggestions by key, mood and genre.
- Reharmonization: sevenths, extensions, secondary dominants, ii-V's, tritone subs,
  modal interchange, passing diminished chords, backdoor and deceptive cadences,
  pedal points, negative harmony.
- Voicings (close, open, drop 2/3, shell, rootless, quartal, spread, power, cluster)
  and four-part SATB voice leading that follows the common-practice rules, plus a
  checker that finds parallel fifths, hidden octaves, crossings and the like.
- Parts: comping rhythms, basslines, melodies built from motifs and phrases, and
  arpeggios. Rhythms: clave, tresillo, Euclidean patterns, polyrhythms.
- Analysis of MIDI: chords over time, non-chord tones, and harmonizing a melody.

Times are quarter notes (QN). A chord timeline is a list of ChordEvent.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from itertools import product
from typing import Callable

from . import harmony as H
from . import scales as scales_db
from .harmony import Key, SpelledChord


@dataclass
class ChordEvent:
    chord: SpelledChord
    start: float
    length: float
    numeral: str | None = None

    @property
    def end(self) -> float:
        return self.start + self.length


def timeline(chords: list[SpelledChord], lengths: list[float] | float = 4.0, start: float = 0.0,
             numerals: list[str] | None = None) -> list[ChordEvent]:
    if not isinstance(lengths, list):
        lengths = [float(lengths)] * len(chords)
    out, t = [], start
    for i, (c, length) in enumerate(zip(chords, lengths)):
        out.append(ChordEvent(c, t, length, numerals[i] if numerals else None))
        t += length
    return out


def chord_at(events: list[ChordEvent], t: float) -> ChordEvent | None:
    for e in events:
        if e.start - 1e-6 <= t < e.end - 1e-6:
            return e
    return events[-1] if events and t >= events[-1].start else None


# ------------------------------------------------------- progression library

@dataclass(frozen=True)
class Progression:
    name: str
    numerals: str
    mode: str
    moods: tuple[str, ...]
    styles: tuple[str, ...]
    about: str


PROGRESSIONS: tuple[Progression, ...] = (
    Progression("axis / four-chord pop", "I-V-vi-IV", "major", ("uplifting", "anthemic", "nostalgic"),
                ("pop", "rock", "edm", "country"), "The most-used pop loop; a tonic-dominant pull softened by vi."),
    Progression("sensitive / emotional pop", "vi-IV-I-V", "major", ("emotional", "bittersweet", "anthemic"),
                ("pop", "edm", "pop punk"), "The axis loop starting on vi: same chords, sadder centre of gravity."),
    Progression("50s doo-wop", "I-vi-IV-V", "major", ("nostalgic", "romantic", "innocent"),
                ("doo-wop", "pop", "soul"), "The ice-cream changes: a full T-T-PD-D cycle every bar or two."),
    Progression("Pachelbel / canon", "I-V-vi-iii-IV-I-IV-V", "major", ("majestic", "romantic", "wedding"),
                ("baroque", "pop", "classical"), "Descending-bass sequence (bass falls by 4ths and rises by 2nds)."),
    Progression("royal road (oudou shinkou)", "IVmaj7-V7-iii7-vi", "major", ("emotional", "yearning", "bright"),
                ("j-pop", "anime score", "city pop", "k-pop"), "J-pop's signature: starts on the predominant, never on I."),
    Progression("just the two of us", "IVmaj7-III7-vi7-v7-I7", "major", ("smooth", "romantic", "soulful"),
                ("r&b", "neo soul", "city pop", "jazz"), "III7 is V7/vi; the v7-I7 makes I7 a V7/IV, so it loops forever."),
    Progression("ii-V-I", "ii7-V7-Imaj7", "major", ("sophisticated", "resolved", "jazzy"),
                ("jazz", "bossa nova", "neo soul"), "The core cadence of jazz: predominant, dominant, tonic, with guide tones moving by step."),
    Progression("minor ii-V-i", "iiø7-V7b9-i7", "minor", ("noir", "dramatic", "jazzy"),
                ("jazz", "bolero", "tango"), "Half-diminished ii and an altered V give the minor cadence its bite."),
    Progression("jazz turnaround", "Imaj7-vi7-ii7-V7", "major", ("jazzy", "bouncy", "classic"),
                ("jazz", "swing", "musical theatre"), "I-vi-ii-V: the end-of-chorus loop back to the top."),
    Progression("tritone-sub turnaround", "Imaj7-bIII7-bVI7-bII7", "major", ("slick", "jazzy", "chromatic"),
                ("jazz", "bossa nova"), "Each dominant of the I-vi-ii-V replaced by its tritone sub: chromatic descending roots."),
    Progression("12-bar blues", "I7-I7-I7-I7-IV7-IV7-I7-I7-V7-IV7-I7-V7", "major", ("bluesy", "gritty", "classic"),
                ("blues", "rock", "jazz", "boogie-woogie"), "Three 4-bar lines: statement, repeat over IV, answer over V-IV."),
    Progression("quick-change blues", "I7-IV7-I7-I7-IV7-IV7-I7-I7-V7-IV7-I7-V7", "major", ("bluesy",),
                ("blues", "chicago blues"), "Like the 12-bar but visits IV7 in bar 2."),
    Progression("jazz blues", "I7-IV7-I7-v7-I7-IV7-#iv°7-I7-iii7-VI7-ii7-V7-I7-VI7-ii7-V7", "major", ("jazzy", "bluesy"),
                ("jazz", "bebop"), "Blues form with ii-V's and a #iv°7 passing chord (shown at 1 chord per half bar)."),
    Progression("minor blues", "i7-i7-i7-i7-iv7-iv7-i7-i7-bVI7-V7-i7-V7", "minor", ("moody", "bluesy", "dark"),
                ("blues", "jazz"), "The minor 12-bar, with the bVI7-V7 sliding into the turnaround."),
    Progression("rhythm changes (A)", "Imaj7-vi7-ii7-V7-iii7-VI7-ii7-V7", "major", ("bouncy", "bebop"),
                ("bebop", "swing"), "Gershwin's I Got Rhythm A section: two turnarounds per 4 bars."),
    Progression("andalusian cadence", "i-VII-VI-V", "minor", ("dramatic", "spanish", "fiery"),
                ("flamenco", "rock", "surf rock", "tango"), "Descending tetrachord in the bass (A-G-F-E) landing on a major V: Phrygian colour."),
    Progression("epic minor loop", "i-VI-III-VII", "minor", ("epic", "heroic", "melancholic"),
                ("edm", "cinematic", "epic trailer", "pop"), "The Aeolian loop of trailers and festival drops."),
    Progression("aeolian vamp", "i-VI-VII", "minor", ("driving", "dark", "heroic"),
                ("metal", "rock", "edm"), "Minor rock's bread and butter; VII-i is the subtonic cadence."),
    Progression("mario cadence", "I-bVI-bVII-I", "major", ("triumphant", "heroic", "victorious"),
                ("video game", "rock", "cinematic"), "Borrowed bVI and bVII rising by whole step back home."),
    Progression("mixolydian rock", "I-bVII-IV-I", "major", ("anthemic", "laid-back", "classic rock"),
                ("classic rock", "britpop", "celtic"), "Double plagal motion (bVII-IV-I), the sound of 60s/70s rock."),
    Progression("dorian vamp", "i7-IV7", "dorian", ("funky", "cool", "hypnotic"),
                ("funk", "modal jazz", "house", "latin"), "The major IV over a minor tonic is dorian's signature."),
    Progression("phrygian vamp", "i-bII", "phrygian", ("menacing", "spanish", "dark"),
                ("metal", "flamenco", "drill"), "The flat-2 chord a half step above the tonic: instant tension."),
    Progression("lydian lift", "I-II", "lydian", ("dreamy", "wonder", "floating"),
                ("cinematic", "dream pop", "prog rock"), "The major II (from the #4) gives lydian's floating brightness."),
    Progression("creep / major-minor IV", "I-III-IV-iv", "major", ("bittersweet", "melancholic", "alt"),
                ("alternative rock", "indie", "grunge"), "III is V/vi; the IV-iv borrowed shift sighs back home."),
    Progression("minor plagal / soul", "I-IV-iv-I", "major", ("bittersweet", "soulful", "nostalgic"),
                ("soul", "pop ballad", "britpop"), "Borrowed iv: the 'heartbreak' chord before home."),
    Progression("backdoor", "ii7-bVII7-Imaj7", "major", ("soulful", "warm", "jazzy"),
                ("neo soul", "gospel", "r&b"), "bVII7 resolves up a whole step instead of V7's fifth: soft and soulful."),
    Progression("gospel walk-up", "I-I7-IV-#iv°7-I64-V7-I", "major", ("uplifting", "churchy", "joyful"),
                ("gospel", "soul", "doo-wop"), "I7 to IV, a passing #iv°7, a cadential 6/4 and home."),
    Progression("circle of fifths", "vi7-ii7-V7-Imaj7", "major", ("classic", "flowing", "resolved"),
                ("jazz", "musical theatre", "baroque"), "Roots fall by fifths: the strongest root motion there is."),
    Progression("descending fifths sequence", "I-IV-vii°-iii-vi-ii-V-I", "major", ("baroque", "flowing", "inevitable"),
                ("baroque", "classical"), "The full diatonic circle; sounds inevitable, used in sequences everywhere."),
    Progression("lament bass", "i-v6-iv6-V", "minor", ("grief", "tragic", "baroque"),
                ("baroque", "classical", "cinematic"), "Bass descends stepwise from tonic to dominant (Dido's Lament)."),
    Progression("romanesca", "I-V-vi-iii-IV-I-ii-V", "major", ("noble", "renaissance", "flowing"),
                ("baroque", "classical"), "The Renaissance/Baroque ground, ancestor of Pachelbel."),
    Progression("chromatic mediant hero", "I-III-IV-I", "major", ("heroic", "wonder", "cinematic"),
                ("cinematic", "adventure score"), "The major III is a chromatic mediant: the film-score 'awe' colour."),
    Progression("hollywood minor", "i-bVI-i-bIII", "minor", ("ominous", "epic", "cinematic"),
                ("cinematic", "epic trailer", "horror score"), "Mediant shifts over a minor tonic for brooding scale."),
    Progression("neo-soul loop", "Imaj9-iii7-vi9-V9sus4", "major", ("smooth", "lush", "late night"),
                ("neo soul", "lo-fi", "r&b"), "Extended chords moving by thirds; the sus dominant floats rather than resolves."),
    Progression("lo-fi loop", "IVmaj7-iii7-ii7-Imaj7", "major", ("chill", "nostalgic", "mellow"),
                ("lo-fi", "jazz rap", "city pop"), "Stepwise descending 7th chords: relaxed and endlessly loopable."),
    Progression("house minor vamp", "i7-iv7", "minor", ("hypnotic", "deep", "soulful"),
                ("deep house", "house", "garage"), "Two minor 7ths, two bars each; modal and groove-first."),
    Progression("trance anthem", "i-VI-III-VII", "minor", ("euphoric", "epic", "uplifting"),
                ("trance", "uplifting trance", "edm"), "Aeolian loop under supersaw plucks; the VII-i lift at the end of each 8."),
    Progression("emo/pop-punk", "I-V-vi-IV", "major", ("energetic", "angsty"), ("pop punk", "emo"),
                "The axis loop driven with power chords and 8th-note bass."),
    Progression("reggae one-two", "I-IV", "major", ("easy", "sunny", "laid-back"), ("reggae", "ska", "rocksteady"),
                "Two chords, skanked on the offbeat; the space is the point."),
    Progression("bossa ii-V", "Imaj7-II7-ii7-V7", "major", ("breezy", "romantic", "saudade"),
                ("bossa nova", "jazz"), "II7 (V7/V) to a ii-V: Jobim-style chromatic inner voices."),
    Progression("dark trap minor", "i-VI-iv-V", "minor", ("dark", "menacing", "cinematic"),
                ("trap", "drill", "phonk"), "Minor loop with a harmonic-minor V for menace (E major in A minor)."),
    Progression("doo-wop minor (Stand by Me-type bass)", "I-vi-IV-V-I", "major", ("soulful", "classic"),
                ("soul", "doo-wop"), "The 50s loop resolved to I at the end of each 8."),
    Progression("picardy close", "i-iv-V7-I", "minor", ("hopeful", "resolved", "sacred"),
                ("baroque", "choral", "classical"), "A minor cadence ending on a major tonic: the Picardy third."),
    Progression("neapolitan cadence", "i-N6-V7-i", "minor", ("tragic", "romantic"),
                ("classical", "romantic"), "bII6 as the predominant: darker and more poignant than iv."),
    Progression("augmented sixth cadence", "i-iv6-Ger+6-V-i", "minor", ("dramatic", "romantic"),
                ("romantic", "classical", "opera"), "The German sixth's outer voices expand to the octave on V."),
    Progression("coltrane changes", "Imaj7-bIII7-bVImaj7-VII7-IIImaj7-V7-Imaj7", "major", ("virtuosic", "restless"),
                ("hard bop", "post-bop"), "Tonal centres a major third apart (Giant Steps cycle), each reached by its V7."),
    Progression("modal interchange ballad", "I-iii-IV-iv-I", "major", ("tender", "bittersweet"),
                ("pop ballad", "singer-songwriter"), "The major-to-minor iv on the way home."),
    Progression("k-pop pre-chorus lift", "IV-V-iii-vi-ii-V", "major", ("building", "euphoric"),
                ("k-pop", "j-pop", "dance pop"), "Royal-road motion into a ii-V that launches the chorus."),
    Progression("afrobeats loop", "ii7-V7-Imaj7-vi7", "major", ("warm", "sunny", "danceable"),
                ("afrobeats", "afroswing", "amapiano"), "Jazzy 7ths in a two-bar loop; the groove carries it."),
    Progression("amapiano minor", "i9-iv9-VII-III", "minor", ("deep", "hypnotic", "late night"),
                ("amapiano",), "Lush minor 9ths over log-drum bass."),
)

MOOD_MODES = {
    "happy": ("major", "lydian"), "uplifting": ("major",), "bright": ("lydian", "major"), "dreamy": ("lydian", "major"),
    "sad": ("minor",), "melancholic": ("minor", "dorian"), "dark": ("phrygian", "minor", "harmonic minor"),
    "menacing": ("phrygian", "harmonic minor"), "epic": ("minor",), "heroic": ("major", "minor"),
    "mysterious": ("harmonic minor", "phrygian dominant", "lydian"), "funky": ("dorian", "mixolydian"),
    "chill": ("major", "dorian"), "romantic": ("major",), "spanish": ("phrygian dominant", "phrygian"),
    "bluesy": ("mixolydian", "dorian"), "jazzy": ("major", "dorian"), "exotic": ("double harmonic", "phrygian dominant"),
    "nostalgic": ("major",), "tense": ("harmonic minor", "locrian"), "hopeful": ("mixolydian", "major"),
}


def find_progressions(mood: str | None = None, style: str | None = None, mode: str | None = None) -> list[Progression]:
    out = []
    for p in PROGRESSIONS:
        if mood and not any(mood.lower() in m for m in p.moods):
            continue
        if style and not any(style.lower() in s or s in style.lower() for s in p.styles):
            continue
        if mode and scales_db.find_scale(mode).name != scales_db.find_scale(p.mode).name:
            continue
        out.append(p)
    return out


def realize(numerals: str, key: Key) -> list[H.RomanChord]:
    """Numerals with an optional 'mode:' prefix -> chords in the key (the mode prefix
    switches to that mode on the same tonic)."""
    body = numerals
    if ":" in numerals:
        mode, _, body = numerals.partition(":")
        key = Key(key.tonic, key.letter, scales_db.find_scale(mode.strip()))
    return H.parse_progression(body.strip(), key)


# Functional grammar for generating new progressions (major and minor).
_GRAMMAR = {
    "major": {
        "I": (("IV", 3), ("vi", 3), ("V", 2), ("ii", 2), ("iii", 1)),
        "ii": (("V", 5), ("vii°", 1), ("IV", 1)),
        "iii": (("vi", 4), ("IV", 3)),
        "IV": (("V", 4), ("I", 2), ("ii", 2), ("iv", 1), ("vi", 1)),
        "iv": (("I", 4), ("V", 1)),
        "V": (("I", 5), ("vi", 2), ("IV", 1)),
        "vi": (("IV", 4), ("ii", 3), ("V", 1), ("iii", 1)),
        "vii°": (("I", 5), ("iii", 1)),
    },
    "minor": {
        "i": (("iv", 3), ("VI", 3), ("VII", 2), ("V", 2), ("III", 2), ("iiø7", 1)),
        "iiø7": (("V", 5),),
        "III": (("VI", 3), ("iv", 2), ("VII", 2)),
        "iv": (("V", 3), ("i", 2), ("VII", 2), ("VI", 1)),
        "V": (("i", 5), ("VI", 2)),
        "VI": (("VII", 3), ("iv", 2), ("III", 2), ("V", 2), ("i", 1)),
        "VII": (("III", 3), ("i", 3), ("VI", 1)),
    },
}

_SEVENTHS = {"I": "Imaj7", "ii": "ii7", "iii": "iii7", "IV": "IVmaj7", "V": "V7", "vi": "vi7", "vii°": "viiø7",
             "i": "i7", "III": "IIImaj7", "iv": "iv7", "VI": "VImaj7", "VII": "VII7", "iv7": "iv7"}


def generate_progression(key: Key, length: int = 4, seed: int | None = None, sevenths: bool = False,
                         end_on_tonic: bool = False) -> list[str]:
    """A new progression from functional-harmony transition weights."""
    rng = random.Random(seed)
    family = "minor" if key.is_minor else "major"
    grammar = _GRAMMAR[family]
    tonic = "i" if family == "minor" else "I"
    seq = [tonic]
    if end_on_tonic and length == 2:
        return ["V7" if sevenths else "V", tonic]
    while len(seq) < length:
        options = grammar.get(seq[-1], grammar[tonic])
        if end_on_tonic and len(seq) == length - 2:
            # The chord before the last: a dominant, or (after V itself) a predominant.
            dominants = [o for o in options if o[0] in ("V", "vii°")] or [("V", 1)]
            options = [o for o in dominants if o[0] != seq[-1]] or \
                [o for o in options if o[0] not in (tonic, seq[-1])] or [("V", 1)]
        if end_on_tonic and len(seq) == length - 1:
            seq.append(tonic)
            break
        names, weights = zip(*options)
        # Never the same chord twice running, and no A-B-A-B ping-pong.
        allowed = [(n_, w_) for n_, w_ in zip(names, weights) if n_ != seq[-1]
                   and not (len(seq) >= 3 and n_ == seq[-2] and seq[-1] == seq[-3])]
        if allowed:
            names, weights = zip(*allowed)
        choice = rng.choices(names, weights)[0]
        seq.append(choice)
    if sevenths:
        seq = [_SEVENTHS.get(n, n) for n in seq]
    return seq


# ------------------------------------------------------ harmony per section

SECTION_KINDS = [  # in order: "pre-chorus" before "chorus"
    (r"pre[- ]?chorus|build|lift", "pre"), (r"chorus|hook|refrain|drop", "chorus"), (r"bridge|middle 8", "bridge"),
    (r"break", "breakdown"), (r"intro", "intro"), (r"outro|ending|coda", "outro"), (r"verse|main|groove|a section", "verse"),
]
_PRE = {"major": ["ii", "IV", "vi", "V"], "minor": ["iv", "VI", "VII", "V"]}


def section_kind(name: str) -> str:
    import re as _re
    n = name.lower()
    return next((kind for pattern, kind in SECTION_KINDS if _re.search(pattern, n)), "verse")


def _numerals(progression: str) -> tuple[str | None, list[str]]:
    mode = None
    body = progression
    if ":" in progression:
        mode, _, body = progression.partition(":")
        mode = mode.strip()
    return mode, [p for p in body.replace(" ", "").split("-") if p]


def plan_harmony(progressions: list[str], key: Key, sections: list[str], lift_last_chorus: bool = False,
                 seed: int | None = None, default_mode: str | None = None) -> list[dict]:
    """A progression for each section so the song moves harmonically: verses (and the
    intro, outro) the style's first progression; choruses its second, or the first
    rotated to start on IV or vi (VI or iv in minor) when there's only one; the
    pre-chorus avoids the tonic and ends on V, leaning into the chorus; a bridge the
    verse reharmonised (borrowed chords and relative substitutes); breakdowns the
    chorus's chords. With lift_last_chorus the last chorus goes up a whole step.
    Only progressions in the key's family (major or minor) are used: a progression
    without a "mode:" prefix is in default_mode. When none fits, they are played on the
    relative key (major ones on C for A minor), which has the same notes.
    Returns [{'section', 'kind', 'numerals', 'chords', 'key'}]; a bridge whose
    reharmonisation splits chords also has 'slots', each chord's length in the verse's
    chord lengths (0.5 = half of one)."""
    if not progressions:
        raise ValueError("give at least one progression")

    def minor_mode(mode: str) -> bool:
        return scales_db.find_scale(mode).intervals[2] == 3

    def fits(p: str) -> bool:
        mode = _numerals(p)[0] or default_mode
        return mode is None or minor_mode(mode) == key.is_minor

    fitting = [p for p in progressions if fits(p)]
    home = key if fitting else _relative(key)   # where the numerals are played
    progressions = fitting or list(progressions)
    family = "minor" if key.is_minor else "major"
    home_family = "minor" if home.is_minor else "major"
    verse_mode, verse = _numerals(progressions[0])
    verse_mode = verse_mode or default_mode
    if len(progressions) > 1 and _numerals(progressions[1])[1] != verse:
        chorus_mode, chorus = _numerals(progressions[1])
        chorus_mode = chorus_mode or default_mode
    else:
        chorus_mode = verse_mode
        starts = ("IV", "vi") if home_family == "major" else ("VI", "iv")
        turn = next((i for i, n in enumerate(verse) if n.rstrip("7maj9") in starts or n in starts), None)
        chorus = verse[turn:] + verse[:turn] if turn else verse[1:] + verse[:1]
    pre = _PRE[family]

    def realise(numerals: list[str], mode: str | None, k: Key) -> list[str]:
        text = "-".join(numerals)
        return [rc.chord.symbol for rc in realize(f"{mode}: {text}" if mode else text, k)]

    verse_events = timeline([rc.chord for rc in realize(("%s: " % verse_mode if verse_mode else "") + "-".join(verse), home)], 4.0)
    verse_symbols = [e.chord.symbol for e in verse_events]
    # The bridge: the verse reharmonised. Borrowed chords do nothing to a progression
    # already in minor, so minor keys try dominants and mediants first.
    sets = ([["secondary_dominants", "chromatic_mediants"], ["modal_interchange", "relative_subs"]] if home_family == "minor"
            else [["modal_interchange", "relative_subs"], ["secondary_dominants", "chromatic_mediants"]])
    bridge_chords, how = verse_symbols, "the verse reharmonised"
    bridge_slots = [1.0] * len(verse_symbols)   # each chord's length, in the verse's chord slots
    for techniques in sets + [["tritone_subs", "deceptive"]]:
        evs, _ = reharmonize(verse_events, home, techniques, seed=seed, amount=0.9)
        if [e.chord.symbol for e in evs] != verse_symbols:
            bridge_chords = [e.chord.symbol for e in evs]
            bridge_slots = [round(e.length / 4.0, 6) for e in evs]
            how = f"the verse reharmonised ({', '.join(t.replace('_', ' ') for t in techniques)})"
            break
    choruses = [i for i, s in enumerate(sections) if section_kind(s) == "chorus"]
    out = []
    for i, name in enumerate(sections):
        kind = section_kind(name)
        k, shown = home, key
        if kind in ("chorus", "breakdown"):
            numerals, mode = chorus, chorus_mode
        elif kind == "pre":
            numerals, mode, k = pre, None, key
        elif kind == "bridge":
            out.append({"section": name, "kind": kind, "numerals": None, "chords": " ".join(bridge_chords),
                        "key": key.name, "how": how, "slots": bridge_slots})
            continue
        else:
            numerals, mode = verse, verse_mode
        row = {"section": name, "kind": kind, "numerals": "-".join(numerals)}
        if k is not key:
            row["how"] = f"played on {home.name}, the relative key (the same notes)"
        if lift_last_chorus and choruses and i == choruses[-1] and len(choruses) > 1:   # one chorus: nothing to lift
            k, shown = _key_up(k, 2), _key_up(key, 2)
            row["how"] = "the last chorus a whole step up"
        row["chords"] = " ".join(realise(numerals, mode, k))
        row["key"] = shown.name
        out.append(row)
    return out


def _relative(key: Key) -> Key:
    """The relative major of a minor key, or the relative minor of a major one."""
    return _key_up(H.parse_key(f"{key.spell_pc(key.tonic)} {'major' if key.is_minor else 'minor'}"),
                   3 if key.is_minor else -3)


def _key_up(key: Key, semitones: int) -> Key:
    """The same mode on a tonic `semitones` higher, spelled as musicians would."""
    mode = "minor" if key.is_minor else "major"
    # The spelling with fewer accidentals: Db major but C# minor, Ab major but G# minor.
    names = (["C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"] if key.is_minor
             else ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"])
    return H.parse_key(f"{names[(key.tonic + semitones) % 12]} {mode}")


# -------------------------------------------------------------- reharmonize

REHARM_TECHNIQUES = (
    "sevenths", "extensions", "secondary_dominants", "ii_v", "tritone_subs", "modal_interchange",
    "passing_diminished", "backdoor", "deceptive", "sus_dominants", "pedal", "relative_subs",
    "chromatic_mediants", "negative_harmony", "picardy",
)


def _sc(key: Key, root: int, quality: str, bass: int | None = None) -> SpelledChord:
    return H.chord_in_key(root % 12, H.CHORD_QUALITIES[quality], key, bass)


def _rel(c: SpelledChord, key: Key) -> int:
    return (c.root - key.tonic) % 12


def _shape(c: SpelledChord) -> set[int]:
    return {i % 12 for i in c.intervals}


def _is_dominant(c: SpelledChord) -> bool:
    s = _shape(c)
    return 4 in s and 10 in s


def _seventh_quality(c: SpelledChord, key: Key) -> str:
    """The diatonic 7th chord for a triad in this key."""
    for d in H.diatonic_chords(key, sevenths=True):
        if d.root == c.root and set(d.intervals[:3]) == set(c.intervals[:3]):
            return H.quality_name(d.intervals)
    s = _shape(c)
    if s == {0, 4, 7}:
        return "7" if _rel(c, key) in (2, 4, 7, 9, 10) else "maj7"
    if s == {0, 3, 7}:
        return "m7"
    if s == {0, 3, 6}:
        return "m7b5"
    return H.quality_name(c.intervals)


def reharmonize(events: list[ChordEvent], key: Key, techniques: list[str], seed: int | None = None,
                amount: float = 1.0) -> tuple[list[ChordEvent], list[str]]:
    """Applies techniques in order. amount (0-1) is how often optional changes happen.
    Returns the new timeline and a note for each change."""
    rng = random.Random(seed)
    notes: list[str] = []
    evs = [ChordEvent(e.chord, e.start, e.length) for e in events]
    for tech in techniques:
        if tech not in REHARM_TECHNIQUES:
            raise ValueError(f"unknown technique '{tech}'. Known: {', '.join(REHARM_TECHNIQUES)}")
        evs = _apply(tech, evs, key, rng, amount, notes)
    return evs, notes


def _split(e: ChordEvent, first: SpelledChord | None, second: SpelledChord) -> list[ChordEvent]:
    """Replaces the second half of an event with another chord (first half keeps e's chord or `first`)."""
    if e.length < 1:
        return [ChordEvent(second, e.start, e.length)]
    half = e.length / 2 if e.length >= 2 else e.length / 2
    return [ChordEvent(first or e.chord, e.start, half), ChordEvent(second, e.start + half, e.length - half)]


def _apply(tech: str, evs: list[ChordEvent], key: Key, rng: random.Random, amount: float, notes: list[str]) -> list[ChordEvent]:
    out: list[ChordEvent] = []
    n = len(evs)
    tonic_rel = 0

    def maybe() -> bool:
        return rng.random() < amount

    if tech == "sevenths":
        for e in evs:
            if len(e.chord.intervals) == 3 and _shape(e.chord) in ({0, 4, 7}, {0, 3, 7}, {0, 3, 6}):
                q = _seventh_quality(e.chord, key)
                new = _sc(key, e.chord.root, q, e.chord.bass)
                notes.append(f"{e.chord.symbol} -> {new.symbol} (diatonic 7th)")
                out.append(ChordEvent(new, e.start, e.length))
            else:
                out.append(e)
        return out

    if tech == "extensions":
        upgrades = {"maj7": "maj9", "m7": "m9", "7": "9", "": "add9", "m": "madd9", "6": "6/9", "m7b5": "m9b5"}
        for i, e in enumerate(evs):
            q = e.chord.quality
            target = upgrades.get(q)
            if q == "7":
                nxt = evs[(i + 1) % n].chord
                minor_target = 3 in _shape(nxt) and (nxt.root - e.chord.root) % 12 == 5
                target = "7b9" if minor_target else ("13" if maybe() else "9")
            if target and maybe():
                new = _sc(key, e.chord.root, target, e.chord.bass)
                notes.append(f"{e.chord.symbol} -> {new.symbol} (extension)")
                out.append(ChordEvent(new, e.start, e.length))
            else:
                out.append(e)
        return out

    if tech in ("secondary_dominants", "ii_v"):
        for i, e in enumerate(evs):
            nxt = evs[i + 1].chord if i + 1 < n else None
            if nxt is None or _rel(nxt, key) == tonic_rel and tech == "secondary_dominants" and i + 1 == n - 1 and False:
                out.append(e)
                continue
            target_is_dim = {3, 6} <= _shape(nxt) and 7 not in _shape(nxt)
            already = _is_dominant(e.chord) and (nxt.root - e.chord.root) % 12 == 5
            if target_is_dim or already or not maybe() or e.length < 1:
                out.append(e)
                continue
            v = _sc(key, nxt.root + 7, "7")
            if tech == "secondary_dominants":
                parts = _split(e, None, v)
                notes.append(f"added {v.symbol} before {nxt.symbol} (V7 of {nxt.symbol})")
            else:
                minor_target = 3 in _shape(nxt)
                ii = _sc(key, nxt.root + 2, "m7b5" if minor_target else "m7")
                if e.length >= 2 and _rel(e.chord, key) != _rel(nxt, key):
                    parts = [ChordEvent(e.chord, e.start, e.length / 2),
                             ChordEvent(ii, e.start + e.length / 2, e.length / 4),
                             ChordEvent(v, e.start + 3 * e.length / 4, e.length / 4)]
                else:
                    parts = [ChordEvent(ii, e.start, e.length / 2), ChordEvent(v, e.start + e.length / 2, e.length / 2)]
                notes.append(f"added {ii.symbol}-{v.symbol} leading into {nxt.symbol} (its ii-V)")
            out.extend(parts)
        return out

    if tech == "tritone_subs":
        for i, e in enumerate(evs):
            if _is_dominant(e.chord) and maybe():
                nxt = evs[(i + 1) % n].chord
                if (nxt.root - e.chord.root) % 12 == 5 or i + 1 == n:
                    q = "7" if e.chord.quality in ("7", "9", "13", "7b9", "7#9", "7alt") else "7"
                    new = _sc(key, e.chord.root + 6, q, None)
                    notes.append(f"{e.chord.symbol} -> {new.symbol} (tritone sub: same 3rd and 7th, bass slides down a half step)")
                    out.append(ChordEvent(new, e.start, e.length))
                    continue
            out.append(e)
        return out

    if tech == "modal_interchange":
        swaps_major = {5: ("m", "iv from the parallel minor"), 9: (None, ""), 2: ("m7b5", "iiø7 from the parallel minor")}
        for i, e in enumerate(evs):
            r, s = _rel(e.chord, key), _shape(e.chord)
            new, why = None, ""
            if not key.is_minor:
                if r == 5 and 4 in s and maybe():
                    new, why = _sc(key, e.chord.root, "m7" if len(e.chord.intervals) > 3 else "m"), "borrowed iv: the bittersweet minor subdominant"
                elif r == 9 and 3 in s and maybe():
                    new, why = _sc(key, key.tonic + 8, "maj7" if len(e.chord.intervals) > 3 else ""), "bVI from the parallel minor"
                elif r == 2 and 3 in s and maybe():
                    new, why = _sc(key, e.chord.root, "m7b5"), swaps_major[2][1]
                elif r == 7 and 4 in s and i + 1 < n and _rel(evs[i + 1].chord, key) == 0 and amount >= 0.8 and maybe():
                    new, why = _sc(key, key.tonic + 10, "7" if len(e.chord.intervals) > 3 else ""), "bVII as a softer dominant (backdoor colour)"
            else:
                if r == 5 and 3 in s and maybe():
                    new, why = _sc(key, e.chord.root, "7" if len(e.chord.intervals) > 3 else ""), "major IV from the parallel dorian"
                elif r == 7 and 3 in s and maybe():
                    new, why = _sc(key, e.chord.root, "7"), "major V7 (harmonic minor) for a real cadence"
            if new is not None:
                notes.append(f"{e.chord.symbol} -> {new.symbol} ({why})")
                out.append(ChordEvent(new, e.start, e.length))
            else:
                out.append(e)
        return out

    if tech == "passing_diminished":
        for i, e in enumerate(evs):
            nxt = evs[i + 1].chord if i + 1 < n else None
            if nxt is not None and (nxt.root - e.chord.root) % 12 == 2 and e.length >= 2 and maybe():
                dim = _sc(key, e.chord.root + 1, "dim7")
                out.extend(_split(e, None, dim))
                notes.append(f"added {dim.symbol} between {e.chord.symbol} and {nxt.symbol} (chromatic passing diminished)")
            else:
                out.append(e)
        return out

    if tech == "backdoor":
        for i, e in enumerate(evs):
            nxt = evs[i + 1].chord if i + 1 < n else None
            if nxt is not None and _is_dominant(e.chord) and _rel(e.chord, key) == 7 and _rel(nxt, key) == 0 and maybe():
                iv = _sc(key, key.tonic + 5, "m7")
                b7 = _sc(key, key.tonic + 10, "7")
                out.extend(_split(e, iv, b7))
                notes.append(f"{e.chord.symbol} -> {iv.symbol}-{b7.symbol} (backdoor ii-V: home from a whole step below)")
            elif nxt is not None and _shape(e.chord) == {0, 4, 7} and _rel(e.chord, key) == 7 and _rel(nxt, key) == 0 and maybe():
                b7 = _sc(key, key.tonic + 10, "")
                out.append(ChordEvent(b7, e.start, e.length))
                notes.append(f"{e.chord.symbol} -> {b7.symbol} (bVII-I backdoor cadence)")
            else:
                out.append(e)
        return out

    if tech == "deceptive":
        done = False
        for i in range(n - 1, 0, -1):
            a, b = evs[i - 1].chord, evs[i].chord
            if not done and _rel(a, key) == 7 and 4 in _shape(a) and _rel(b, key) == 0:
                new = _sc(key, key.tonic + (8 if key.is_minor else 9), "" if key.is_minor else "m")
                evs = evs[:i] + [ChordEvent(new, evs[i].start, evs[i].length)] + evs[i + 1:]
                notes.append(f"{b.symbol} -> {new.symbol} (deceptive cadence: V resolves to {'bVI' if key.is_minor else 'vi'})")
                done = True
        return evs

    if tech == "sus_dominants":
        for e in evs:
            if _rel(e.chord, key) == 7 and 4 in _shape(e.chord) and e.length >= 2 and maybe():
                sus = _sc(key, e.chord.root, "7sus4" if _is_dominant(e.chord) else "sus4")
                out.extend([ChordEvent(sus, e.start, e.length / 2), ChordEvent(e.chord, e.start + e.length / 2, e.length / 2)])
                notes.append(f"{e.chord.symbol} -> {sus.symbol}-{e.chord.symbol} (4-3 suspension)")
            else:
                out.append(e)
        return out

    if tech == "pedal":
        for e in evs:
            new = H.chord_in_key(e.chord.root, e.chord.intervals, key, key.tonic) if e.chord.root != key.tonic else e.chord
            out.append(ChordEvent(new, e.start, e.length))
        notes.append(f"held {key.tonic_name} in the bass under every chord (tonic pedal)")
        return out

    if tech == "relative_subs":
        for i, e in enumerate(evs):
            r = _rel(e.chord, key)
            new = None
            if 0 < i < n - 1 and maybe():
                if not key.is_minor and r == 0 and 4 in _shape(e.chord):
                    new = _sc(key, key.tonic + rng.choice((9, 4)), "m7" if len(e.chord.intervals) > 3 else "m")
                elif not key.is_minor and r == 5 and 4 in _shape(e.chord):
                    new = _sc(key, key.tonic + 2, "m7" if len(e.chord.intervals) > 3 else "m")
                elif key.is_minor and r == 0:
                    new = _sc(key, key.tonic + rng.choice((3, 8)), "maj7" if len(e.chord.intervals) > 3 else "")
            if new is not None:
                notes.append(f"{e.chord.symbol} -> {new.symbol} (substitute with the same function)")
                out.append(ChordEvent(new, e.start, e.length))
            else:
                out.append(e)
        return out

    if tech == "chromatic_mediants":
        for i, e in enumerate(evs):
            if 0 < i and _rel(e.chord, key) == 0 and maybe():
                shift = rng.choice((4, 8, 3, 9))
                new = _sc(key, key.tonic + shift, "")
                notes.append(f"{e.chord.symbol} -> {new.symbol} (chromatic mediant: shares one note, sudden change of light)")
                out.append(ChordEvent(new, e.start, e.length))
            else:
                out.append(e)
        return out

    if tech == "negative_harmony":
        for e in evs:
            new = H.negative_chord(e.chord, key)
            notes.append(f"{e.chord.symbol} -> {new.symbol} (negative harmony mirror)")
            out.append(ChordEvent(new, e.start, e.length))
        return out

    if tech == "picardy":
        last = evs[-1]
        if key.is_minor and _rel(last.chord, key) == 0 and 3 in _shape(last.chord):
            new = _sc(key, key.tonic, "")
            notes.append(f"{last.chord.symbol} -> {new.symbol} (Picardy third)")
            return evs[:-1] + [ChordEvent(new, last.start, last.length)]
        return evs
    return evs


# ------------------------------------------------------------------ voicings

def essential_tones(chord: SpelledChord, max_notes: int = 4) -> list[int]:
    """Chord intervals by importance: 3rd and 7th (the guide tones), root, colour
    tones, then the perfect 5th (the first to drop). Avoids the natural 11 over a
    major 3rd."""
    iv = list(chord.intervals)
    s = {i % 12: i for i in iv}
    order: list[int] = []

    def add(x: int | None) -> None:
        if x is not None and x not in order:
            order.append(x)

    for third in (4, 3):
        if third in s:
            add(s[third])
            break
    else:
        for sus in (5, 2):
            if sus in s and s[sus] < 12:
                add(s[sus])
    for sev in (10, 11, 9):
        if sev in s and not (sev == 9 and 10 not in s and 11 not in s and {3, 6} <= s.keys() and len(iv) == 4 and False):
            add(s[sev])
            break
    add(0)
    for i in iv:
        x = i % 12
        if x in (1, 2, 3, 6, 8, 9) and i >= 12 or (x in (6, 8) and 7 not in s):
            if x == 5 and 4 in s:
                continue
            add(i)
    for i in iv:
        if i % 12 == 5 and 4 in s and i >= 12:
            continue  # natural 11 clashes with a major 3rd
        add(i)
    if 7 in s:
        order.remove(7) if 7 in order else None
        order.append(7)
    return order[:max_notes] if len(order) > max_notes else order


def _rotations(pcs: list[int], base: int) -> list[list[int]]:
    """Every inversion of a close-position stack built from pitch classes, starting at or above base."""
    out = []
    n = len(pcs)
    for r in range(n):
        order = pcs[r:] + pcs[:r]
        notes = []
        last = base - 1
        for pc in order:
            p = last + 1 + ((pc - (last + 1)) % 12)
            notes.append(p)
            last = p
        out.append(notes)
    return out


def _candidates(chord: SpelledChord, style: str, octave: int) -> list[list[int]]:
    base = 12 * (octave + 1)
    root = chord.root
    tones = essential_tones(chord, 4 if style not in ("close", "cluster") else 5)
    pcs = [(root + t) % 12 for t in tones]
    s = _shape(chord)
    cands: list[list[int]] = []
    if style in ("close", "cluster", "satb"):
        triad_pcs = [(root + i) % 12 for i in chord.intervals] if len(chord.intervals) <= 4 else pcs
        if style == "cluster":
            add9 = (root + 2) % 12
            triad_pcs = list(dict.fromkeys(triad_pcs + [add9]))
        triad_pcs = sorted(dict.fromkeys(triad_pcs), key=lambda pc: (pc - root) % 12)
        for shift in (-12, 0, 12):
            for v in _rotations(triad_pcs, base + shift - 5):
                cands.append(v)
        if style == "cluster":
            cands = [v for v in cands if v[-1] - v[0] <= 10] or cands
    elif style in ("open", "drop2", "drop3"):
        # Four-voice close position: four distinct tones, or a triad with its
        # lowest note doubled on top; then drop the 2nd (or 3rd) voice from the top.
        four = list(dict.fromkeys(pcs))[:4]
        if len(four) < 3:
            four = [(root + i) % 12 for i in chord.intervals[:3]]
        four.sort(key=lambda pc: (pc - root) % 12)  # close position needs the tones in order
        for shift in (-12, 0, 12):
            for v in _rotations(four, base + shift):
                v = sorted(v)
                if len(v) == 3:
                    v = v + [v[0] + 12]
                k = 3 if style == "drop3" else 2
                dropped = v[-k] - 12
                v = sorted([dropped] + v[:-k] + v[-k + 1:])
                cands.append(v)
    elif style == "shell":
        third = next((root + t for t in (4, 3, 5, 2) if t in s), root + 4)
        seventh = next((root + t for t in (10, 11, 9) if t in s), None)
        guide = [third, seventh] if seventh is not None else [third, root + 7]
        for shift in (-12, 0, 12):
            r = base - 12 + root % 12 + shift
            g1 = [r + ((g - r) % 12) for g in guide]
            cands.append(sorted([r] + g1))
            cands.append(sorted([r, g1[1], g1[0] + 12]))
    elif style == "rootless":
        third = next((t for t in (4, 3, 5) if t in s), 4)
        seventh = next((t for t in (10, 11) if t in s), 10 if third == 3 else 9)  # m7 colour for minor, 6 for major
        fifth = 7 if 7 in s else (6 if 6 in s else (8 if 8 in s else 7))
        ninth = 1 if 1 in s else (3 if (3 in s and 4 in s) else 2)
        thirteenth = 9 if 9 in s and seventh != 9 else None
        dominant = third == 4 and seventh == 10
        top5 = thirteenth if (dominant and thirteenth is not None) else (9 if dominant else fifth)
        a_form = [third, top5, seventh, ninth + 12]
        b_form = [seventh, ninth + 12, third + 12, top5 + 12]
        for form in (a_form, b_form):
            for shift in (-12, 0, 12):
                v = sorted((base + root % 12 + shift + x) for x in form)
                cands.append(v)
    elif style == "quartal":
        start = 2 if 3 in s else 4
        stack = [start, start + 5, start + 10, start + 15]
        if 3 in s:
            stack = [2, 7, 12, 17]  # 9, 5, root, 11 (So What)
        for shift in (-12, 0, 12):
            cands.append([base + root % 12 + shift + x for x in stack])
    elif style == "spread":
        third = next((t for t in (4, 3, 5, 2) if t in s), 4)
        top = next((t for t in (10, 11, 9) if t in s), 12)
        for shift in (-12, 0):
            r = base - 12 + root % 12 + shift
            cands.append([r, r + 7, r + 12 + third, r + 12 + top if top != 12 else r + 24])
    elif style == "power":
        for shift in (-12, 0):
            r = base - 12 + root % 12 + shift
            cands.append([r, r + 7, r + 12])
    else:
        raise ValueError(f"unknown voicing '{style}'")
    return [sorted(n for n in v if 0 <= n <= 127) for v in cands if v]


def _muddy(v: list[int]) -> float:
    """Low-interval-limit penalty: close intervals sound muddy in the bass register."""
    penalty = 0.0
    for a, b in zip(v, v[1:]):
        gap = b - a
        if a < 48 and gap < 5:
            penalty += (48 - a) * (5 - gap) * 0.8
        if a < 40 and gap < 7:
            penalty += 6
    return penalty


def voice_chords(chords: list[SpelledChord], style: str = "close", octave: int = 4,
                 prev: list[int] | None = None, key: Key | None = None) -> list[list[int]]:
    """A voicing per chord in the given style, each chosen to move as little as possible
    from the last, without the same top note three times running (the line on top goes
    somewhere) and, when a chord comes back, in another inversion than last time."""
    if style == "satb":
        return satb(chords, key or Key(chords[0].root, chords[0].root_name[0], scales_db.find_scale("major")))
    center = 12 * (octave + 1) + 4
    out: list[list[int]] = []
    last_for: dict[str, list[int]] = {}
    for c in chords:
        cands = _candidates(c, style, octave)
        tops = [v[-1] for v in out[-2:]]
        same_top = len(tops) == 2 and tops[0] == tops[1]
        before = last_for.get(c.symbol)
        just_before = out[-1] if out else None

        def cost(v: list[int]) -> float:
            drift = abs(sum(v) / len(v) - center)
            move = 0.0 if prev is None else _movement(prev, v)
            penalty = 0.0
            if same_top and v[-1] == tops[-1]:
                penalty += TOP_REPEAT_PENALTY
            if before is not None and v == before and v != just_before:
                penalty += REVOICE_PENALTY   # the chord came back: another inversion this time
            return move + 0.6 * drift + _muddy(v) + penalty

        best = min(cands, key=cost)
        out.append(best)
        last_for[c.symbol] = best
        prev = best
    return out


TOP_REPEAT_PENALTY = 5.0   # as costly as moving a voice five semitones
REVOICE_PENALTY = 3.0

# Comping patterns whose chord changes can land an 8th early (anticipated, pushed).
ANTICIPATE_STYLES = {"stabs", "push", "charleston"}
# Held patterns that take a 4-3 suspension on a phrase's last chord.
SUSPEND_STYLES = {"sustain", "half_notes", "quarters"}


def develop_comp(notes: list[dict], events: list[ChordEvent], pattern: str, anticipate: bool | None = None,
                 suspensions: bool = True, phrase_chords: int = 4) -> list[dict]:
    """A chord part that moves like a player's: in stab styles (or with anticipate=True)
    each chord change lands an 8th early, cutting the chord before it short; in held
    styles the last chord of each phrase (every phrase_chords chords) starts with its
    third raised to the 4th and resolves down to it halfway (a 4-3 suspension)."""
    out = [dict(n) for n in notes]
    if anticipate is None:
        anticipate = pattern in ANTICIPATE_STYLES
    if anticipate:
        for e in events[1:]:
            hits = [n for n in out if abs(n["start"] - e.start) < 1e-6]
            if not hits:
                continue
            new_start = e.start - 0.5
            # The old chord's own hits in that 8th give way to the new chord.
            out = [n for n in out if not (new_start - 1e-6 <= n["start"] < e.start - 1e-6)]
            for n in out:
                if n["start"] < new_start - 1e-6 and n["start"] + n["length"] > new_start:
                    n["length"] = round(max(0.05, new_start - n["start"] - 0.02), 6)
            for n in hits:
                n["start"] = round(new_start, 6)
                n["length"] = round(n["length"] + 0.5, 6)
    if suspensions and pattern in SUSPEND_STYLES:
        for i, e in enumerate(events):
            if (i + 1) % phrase_chords or e.length < 2:
                continue
            third = next((iv for iv in e.chord.intervals if iv % 12 in (3, 4)), None)
            if third is None or 5 in [iv % 12 for iv in e.chord.intervals]:
                continue
            third_pc = (e.chord.root + third) % 12
            fourth_pc = (e.chord.root + 5) % 12
            for n in [n for n in out if abs(n["start"] - e.start) < 1e-3 and n["pitch"] % 12 == third_pc]:
                half = round(n["length"] / 2, 6)
                sus = dict(n, pitch=n["pitch"] + (fourth_pc - third_pc) % 12, length=half)
                n["start"], n["length"] = round(n["start"] + half, 6), round(n["length"] - half, 6)
                out.append(sus)
    return sorted(out, key=lambda n: (n["start"], n["pitch"]))


def _movement(a: list[int], b: list[int]) -> float:
    return sum(min(abs(n - p) for p in a) for n in b) + sum(min(abs(p - n) for n in b) for p in a)


# ---------------------------------------------------------- SATB voice leading

RANGES = {"soprano": (60, 79), "alto": (55, 74), "tenor": (48, 67), "bass": (40, 62)}
VOICE_NAMES = ("bass", "tenor", "alto", "soprano")


def _satb_candidates(c: SpelledChord, key: Key) -> list[tuple[int, int, int, int]]:
    pcs = [(c.root + i) % 12 for i in c.intervals]
    if len(pcs) > 4:
        pcs = [(c.root + i) % 12 for i in essential_tones(c, 4)]
    bass_pc = c.bass if c.bass is not None else c.root
    leading = (key.tonic + 11) % 12
    seventh = next(((c.root + i) % 12 for i in c.intervals if i % 12 in (10, 11, 9) and len(c.intervals) >= 4), None)
    root, third = c.root % 12, next(((c.root + i) % 12 for i in c.intervals if i % 12 in (3, 4)), None)
    fifth = next(((c.root + i) % 12 for i in c.intervals if i % 12 in (6, 7, 8)), None)
    out = []
    lo, hi = RANGES["bass"]
    basses = [p for p in range(lo, hi + 1) if p % 12 == bass_pc]
    tenors = [p for p in range(*_r("tenor")) if p % 12 in pcs]
    altos = [p for p in range(*_r("alto")) if p % 12 in pcs]
    sops = [p for p in range(*_r("soprano")) if p % 12 in pcs]
    for b in basses:
        for t in tenors:
            if t < b or t - b > 19:
                continue
            for a in altos:
                if a < t or a - t > 12:
                    continue
                for s in sops:
                    if s < a or s - a > 12:
                        continue
                    present = [x % 12 for x in (b, t, a, s)]
                    if third is not None and third not in present:
                        continue
                    if root not in present:
                        continue
                    if seventh is not None and seventh not in present:
                        continue
                    if len(set(present)) < len(pcs) - (1 if fifth is not None and fifth not in present else 0):
                        continue
                    if present.count(leading) > 1 and leading in pcs:
                        continue
                    if seventh is not None and present.count(seventh) > 1:
                        continue
                    out.append((b, t, a, s))
    return out


def _r(voice: str) -> tuple[int, int]:
    lo, hi = RANGES[voice]
    return lo, hi + 1


def _chord_seventh(chord) -> int | None:
    """The pitch class of a chord's 7th, which should fall by step: a minor or major
    7th, or the diminished 7th (9 semitones) of a dim7 chord. A 6th (C6, Am6) isn't a
    7th: it used to be flagged as an "unresolved seventh", and a major 7th never was."""
    shape = {i % 12 for i in chord.intervals}
    if len(chord.intervals) < 4:
        return None
    for iv in chord.intervals:
        if iv % 12 in (10, 11) or (iv % 12 == 9 and {3, 6} <= shape):
            return (chord.root + iv) % 12
    return None


def _transition_cost(p: tuple[int, ...], q: tuple[int, ...], pc_prev: SpelledChord, pc_next: SpelledChord, key: Key) -> float:
    cost = 0.0
    for i in range(4):
        leap = abs(q[i] - p[i])
        weight = 0.3 if i == 0 else (1.0 if i in (1, 2) else 0.8)
        cost += leap * weight
        if i in (1, 2) and leap > 4:
            cost += (leap - 4) * 2
        if leap > 12:
            cost += 40
        if i > 0 and leap == 6:
            cost += 8  # melodic tritone
    for i in range(4):
        for j in range(i + 1, 4):
            a, b = (p[j] - p[i]) % 12, (q[j] - q[i]) % 12
            moved = q[i] != p[i] and q[j] != p[j]
            same_dir = (q[i] - p[i]) * (q[j] - p[j]) > 0
            if moved and a == b and a in (0, 7) and same_dir:
                cost += 120  # parallel fifths/octaves
            if i == 0 and j == 3 and same_dir and b in (0, 7) and abs(q[3] - p[3]) > 2:
                cost += 25  # hidden fifths/octaves in the outer voices
    for i in range(3):
        if q[i] > p[i + 1] or q[i + 1] < p[i]:
            cost += 12  # voice overlap
    leading = (key.tonic + 11) % 12
    resolves_home = (pc_next.root - key.tonic) % 12 == 0
    if resolves_home and (pc_prev.root - key.tonic) % 12 in (7, 11):
        if p[3] % 12 == leading and q[3] != p[3] + 1:
            cost += 30  # leading tone in the soprano should rise to the tonic
        for i in (1, 2):
            if p[i] % 12 == leading and q[i] % 12 not in (key.tonic, (key.tonic + 7) % 12):
                cost += 6
    seventh = _chord_seventh(pc_prev)
    if seventh is not None:
        for i in range(4):
            if p[i] % 12 == seventh and not (0 < p[i] - q[i] <= 2) and q[i] != p[i]:
                cost += 25  # the chord 7th should resolve down by step
    return cost


def satb(chords: list[SpelledChord], key: Key, beam: int = 60) -> list[list[int]]:
    """Four-part voicings (bass, tenor, alto, soprano) for a progression, searched to
    minimize motion and avoid parallel fifths/octaves, hidden octaves, overlaps,
    unresolved leading tones and sevenths."""
    states: list[tuple[float, list[tuple[int, int, int, int]]]] = []
    first = _satb_candidates(chords[0], key)
    if not first:
        raise ValueError(f"can't voice {chords[0].symbol} in four parts")
    center = (52, 60, 65, 72)
    for v in first:
        states.append((sum(abs(a - b) for a, b in zip(v, center)) * 0.2, [v]))
    states.sort(key=lambda s: s[0])
    states = states[:beam]
    for k in range(1, len(chords)):
        cands = _satb_candidates(chords[k], key)
        if not cands:
            raise ValueError(f"can't voice {chords[k].symbol} in four parts")
        new_states = []
        for cost, path in states:
            p = path[-1]
            scored = sorted(cands, key=lambda q: _transition_cost(p, q, chords[k - 1], chords[k], key))[:12]
            for q in scored:
                new_states.append((cost + _transition_cost(p, q, chords[k - 1], chords[k], key), path + [q]))
        new_states.sort(key=lambda s: s[0])
        states = new_states[:beam]
    return [list(v) for v in states[0][1]]


def check_voice_leading(voicings: list[list[int]], key: Key | None = None, chords: list[SpelledChord] | None = None) -> list[dict]:
    """Common-practice voice-leading problems between consecutive voicings (each
    listed low to high, with the same number of voices)."""
    issues: list[dict] = []
    if not voicings:
        return issues
    n_voices = len(voicings[0])
    names = VOICE_NAMES if n_voices == 4 else tuple(f"voice {i + 1}" for i in range(n_voices))
    if n_voices == 4:
        names = VOICE_NAMES

    def add(at: int, issue: str, detail: str) -> None:
        issues.append({"chord": at, "issue": issue, "detail": detail})

    for k, v in enumerate(voicings):
        if len(v) != n_voices:
            add(k + 1, "voice count", f"has {len(v)} notes, expected {n_voices}")
            continue
        for i in range(n_voices - 1):
            if v[i] > v[i + 1]:
                add(k + 1, "voice crossing", f"{names[i]} is above {names[i + 1]}")
        if n_voices == 4:
            for i, name in enumerate(names):
                lo, hi = RANGES[name]
                if not lo - 2 <= v[i] <= hi + 2:
                    add(k + 1, "range", f"{name} at {_n(v[i])} is outside its comfortable range ({_n(lo)}-{_n(hi)})")
            if v[3] - v[2] > 12:
                add(k + 1, "spacing", "more than an octave between soprano and alto")
            if v[2] - v[1] > 12:
                add(k + 1, "spacing", "more than an octave between alto and tenor")
        if key is not None:
            leading = (key.tonic + 11) % 12
            chord = chords[k] if chords else None
            if chord is not None and leading in chord.pitch_classes() and [x % 12 for x in v].count(leading) > 1:
                add(k + 1, "doubled leading tone", f"{key.spell_pc(leading)} appears twice; it wants to resolve, so doubling it causes parallels")
    for k in range(1, len(voicings)):
        p, q = voicings[k - 1], voicings[k]
        if len(p) != len(q):
            continue
        for i in range(len(p)):
            for j in range(i + 1, len(p)):
                a, b = (p[j] - p[i]) % 12, (q[j] - q[i]) % 12
                moved = q[i] != p[i] and q[j] != p[j]
                same_dir = (q[i] - p[i]) * (q[j] - p[j]) > 0
                if moved and same_dir and a == b == 7:
                    add(k + 1, "parallel fifths", f"{names[i]} and {names[j]} move in parallel 5ths ({_n(p[i])}-{_n(p[j])} to {_n(q[i])}-{_n(q[j])})")
                elif moved and same_dir and a == b == 0 and p[j] != p[i]:
                    add(k + 1, "parallel octaves", f"{names[i]} and {names[j]} move in parallel octaves/unisons")
                elif moved and a != b and b in (0, 7) and same_dir and i == 0 and j == len(p) - 1 and abs(q[j] - p[j]) > 2:
                    add(k + 1, "hidden " + ("octave" if b == 0 else "fifth"),
                        f"outer voices move in the same direction into a perfect {'octave' if b == 0 else 'fifth'} with a leap in the top voice")
                if b == 7 and a == 6 and moved and same_dir and i == 0:
                    add(k + 1, "unequal fifths", f"{names[i]} and {names[j]} move from a diminished to a perfect 5th (often avoided with the bass)")
            leap = q[i] - p[i]
            if abs(leap) > 12:
                add(k + 1, "large leap", f"{names[i]} leaps more than an octave")
            elif abs(leap) == 6:
                add(k + 1, "melodic tritone", f"{names[i]} leaps a tritone")
            if key is not None and "harmonic minor" in key.scale.name and abs(leap) == 3:
                lowered6, leading = (key.tonic + 8) % 12, (key.tonic + 11) % 12
                if {p[i] % 12, q[i] % 12} == {lowered6, leading}:
                    add(k + 1, "augmented second", f"{names[i]} moves an augmented 2nd ({key.spell_pc(lowered6)}-{key.spell_pc(leading)})")
        for i in range(len(p) - 1):
            if q[i] > p[i + 1]:
                add(k + 1, "voice overlap", f"{names[i]} moves above where {names[i + 1]} just was")
            if q[i + 1] < p[i]:
                add(k + 1, "voice overlap", f"{names[i + 1]} moves below where {names[i]} just was")
        if key is not None and chords:
            a, b = chords[k - 1], chords[k]
            leading = (key.tonic + 11) % 12
            if (a.root - key.tonic) % 12 in (7, 11) and (b.root - key.tonic) % 12 == 0:
                if p[-1] % 12 == leading and q[-1] - p[-1] != 1:
                    add(k + 1, "unresolved leading tone", f"the top voice's leading tone {key.spell_pc(leading)} doesn't rise to {key.tonic_name}")
            seventh = _chord_seventh(a)
            if seventh is not None:
                for i in range(len(p)):
                    if p[i] % 12 == seventh and q[i] != p[i] and not (0 < p[i] - q[i] <= 2):
                        add(k + 1, "unresolved seventh", f"the chord 7th in the {names[i]} should fall by step")
    return issues


def _n(p: int) -> str:
    return H.theory.midi_to_note(p)


# ---------------------------------------------------------------- comping

def _bar_len(meter: str) -> float:
    num, den = (int(x) for x in meter.split("/"))
    return num * 4 / den


# Positions (QN within a 4/4 bar), lengths, and which notes play: "all", "upper"
# (everything but the lowest), "low", or an arpeggio index.
_COMP = {
    "half_notes": [(0, 2, "all"), (2, 2, "all")],
    "quarters": [(b, 0.9, "all") for b in range(4)],
    "eighths": [(b / 2, 0.45, "all") for b in range(8)],
    "offbeat": [(b + 0.5, 0.4, "all") for b in range(4)],
    "skank": [(1, 0.3, "upper"), (3, 0.3, "upper")],
    "stabs": [(0, 0.25, "all"), (0.75, 0.25, "all"), (2.5, 0.25, "all")],
    "charleston": [(0, 0.5, "all"), (1.5, 0.4, "all")],
    "push": [(0, 0.7, "all"), (0.75, 0.6, "all"), (1.5, 1.0, "all"), (3, 0.4, "all"), (3.5, 0.5, "all")],
    "tresillo": [(0, 1.4, "all"), (1.5, 1.4, "all"), (3, 0.9, "all")],
    "pulse_16": [(b / 4, 0.2, "all") for b in range(16)],
    "gospel": [(0, 0.7, "all"), (0.75, 0.5, "upper"), (1.5, 0.9, "all"), (2.5, 0.4, "upper"), (3, 0.5, "all"), (3.5, 0.4, "upper")],
}
_BOSSA = [(0, 0.5, "low"), (0.5, 0.4, "upper"), (1.5, 0.5, "upper"), (2, 0.5, "low"), (2.5, 0.4, "upper"),
          (4, 0.5, "low"), (5, 0.4, "upper"), (6, 0.5, "low"), (6.5, 0.4, "upper"), (7.5, 0.4, "upper")]
_MONTUNO = [(0, 0.45, "outer"), (0.5, 0.45, "inner"), (1.0, 0.45, "outer"), (1.5, 0.95, "inner"), (2.5, 0.45, "outer"),
            (3, 0.45, "inner"), (3.5, 0.45, "outer"),
            (4.5, 0.45, "inner"), (5, 0.45, "outer"), (5.5, 0.95, "inner"), (6.5, 0.45, "outer"), (7, 0.45, "inner"),
            (7.5, 0.45, "outer")]
_STRUM = [(0, "D"), (1, "D"), (1.5, "U"), (2.5, "U"), (3, "D"), (3.5, "U")]


def comp(events: list[ChordEvent], voicings: list[list[int]], pattern: str = "sustain", meter: str = "4/4",
         velocity: int = 84, rate: float = 0.5, seed: int | None = None) -> list[dict]:
    """Plays voiced chords in a rhythm. Patterns repeat per bar from the bar line."""
    rng = random.Random(seed)
    bar = _bar_len(meter)
    notes: list[dict] = []

    def hit(pitches: list[int], t: float, length: float, vel: int) -> None:
        for p in pitches:
            notes.append({"pitch": p, "start": round(t, 6), "length": round(max(0.05, length), 6),
                          "velocity": max(1, min(127, vel)), "channel": 1})

    def pick(v: list[int], which: str) -> list[int]:
        if which == "all":
            return v
        if which == "upper":
            return v[1:] if len(v) > 2 else v
        if which == "low":
            return v[:1]
        if which == "outer":
            return [v[0], v[-1]] if len(v) > 1 else v
        if which == "inner":
            return v[1:-1] or v
        return v

    for e, v in zip(events, voicings):
        if pattern in ("none",):
            continue
        if pattern == "sustain":
            hit(v, e.start, e.length * 0.98, velocity)
            continue
        if pattern in ("arpeggio_up", "arpeggio_updown", "broken", "alberti"):
            if pattern == "arpeggio_up":
                seq = v
            elif pattern == "arpeggio_updown":
                seq = v + v[-2:0:-1] if len(v) > 2 else v
            elif pattern == "broken":
                seq = [v[0], v[len(v) // 2], v[-1], v[len(v) // 2]] if len(v) >= 3 else v
            else:
                seq = [v[0], v[-1], v[len(v) // 2], v[-1]] if len(v) >= 3 else v
            t, i = e.start, 0
            while t < e.end - 1e-6:
                length = min(rate, e.end - t)
                hit([seq[i % len(seq)]], t, length * 0.95, velocity - (0 if i % 2 == 0 else 8))
                t += rate
                i += 1
            continue
        if pattern == "waltz":
            t = e.start
            while t < e.end - 1e-6:
                pos = (t % bar)
                if abs(pos) < 1e-6:
                    hit(v[:1], t, min(1, e.end - t) * 0.95, velocity + 4)
                else:
                    hit(v[1:] or v, t, min(1, e.end - t) * 0.8, velocity - 10)
                t += 1
            continue
        if pattern == "strum":
            bar_start = math.floor(e.start / bar) * bar
            t0 = bar_start
            while t0 < e.end - 1e-6:
                for pos, direction in _STRUM:
                    t = t0 + pos
                    if not (e.start - 1e-6 <= t < e.end - 1e-6) or pos >= bar:
                        continue
                    order = v if direction == "D" else list(reversed(v))
                    for k, p in enumerate(order):
                        notes.append({"pitch": p, "start": round(t + 0.02 * k, 6),
                                      "length": round(max(0.1, min(0.5, e.end - t) - 0.02 * k), 6),
                                      "velocity": max(1, min(127, velocity + (6 if direction == "D" else -10) + rng.randint(-4, 4))),
                                      "channel": 1})
                t0 += bar
            continue
        template = {"bossa": _BOSSA, "montuno": _MONTUNO}.get(pattern) or _COMP.get(pattern)
        if template is None:
            raise ValueError(f"unknown comping pattern '{pattern}'")
        cycle = 8.0 if pattern in ("bossa", "montuno") else bar
        if pattern not in ("bossa", "montuno") and bar < 4:
            template = [x for x in template if x[0] < bar]
        elif pattern not in ("bossa", "montuno") and bar > 4:
            # A longer bar (5/4, 7/4): carry on from the top of the one-bar pattern
            # so the extra beats aren't silent.
            template = list(template) + [(pos + 4, length, which) for pos, length, which in template
                                         if pos + 4 < bar - 1e-6]
        cycle_start = math.floor(e.start / cycle) * cycle
        t0 = cycle_start
        while t0 < e.end - 1e-6:
            for pos, length, which in template:
                t = t0 + pos
                if e.start - 1e-6 <= t < e.end - 1e-6:
                    accent = 8 if abs(pos % 1) < 1e-6 and pos % 2 == 0 else 0
                    hit(pick(v, which), t, min(length, e.end - t), velocity + accent + rng.randint(-3, 3))
            t0 += cycle
    return notes


# ----------------------------------------------------------------- basslines

def _near(pc: int, target: int, lo: int = 28, hi: int = 55) -> int:
    best = min((p for p in range(lo, hi + 1) if p % 12 == pc % 12), key=lambda p: abs(p - target))
    return best


def bassline(events: list[ChordEvent], style: str = "root", key: Key | None = None, octave: int = 2,
             meter: str = "4/4", velocity: int = 100, seed: int | None = None) -> list[dict]:
    """A bass part following the chords. style: see genres.BASS_STYLES."""
    rng = random.Random(seed)
    bar = _bar_len(meter)
    notes: list[dict] = []
    center = 12 * (octave + 1) + 4
    last = center

    def note(p: int, t: float, length: float, vel: int = velocity) -> None:
        notes.append({"pitch": max(0, min(127, p)), "start": round(t, 6), "length": round(max(0.05, length), 6),
                      "velocity": max(1, min(127, vel)), "channel": 1})

    def root_of(e: ChordEvent) -> int:
        return e.chord.bass if e.chord.bass is not None else e.chord.root

    def tones(e: ChordEvent) -> list[int]:
        return [(e.chord.root + i) % 12 for i in e.chord.intervals]

    if style == "none":
        return []
    for idx, e in enumerate(events):
        nxt = events[idx + 1] if idx + 1 < len(events) else None
        r = _near(root_of(e), last)
        fifth_pc = (e.chord.root + 7) % 12 if 7 in _shape(e.chord) else (e.chord.root + next((i for i in e.chord.intervals if i % 12 in (6, 8)), 7)) % 12
        fifth = r + ((fifth_pc - r) % 12)
        fifth_below = fifth - 12 if fifth - 12 >= 26 else fifth
        third_pc = next(((e.chord.root + i) % 12 for i in e.chord.intervals if i % 12 in (3, 4)), (e.chord.root + 4) % 12)
        third = r + ((third_pc - r) % 12)
        seventh_pc = next(((e.chord.root + i) % 12 for i in e.chord.intervals if i % 12 in (10, 11)), None)

        def each_beat(step: float):
            t = e.start
            while t < e.end - 1e-6:
                yield t
                t += step

        if style in ("whole", "reese"):
            note(r, e.start, e.length * (1.0 if style == "reese" else 0.97))
        elif style == "root":
            for t in each_beat(bar):
                note(r, t, min(bar, e.end - t) * 0.95)
        elif style == "eighths":
            for i, t in enumerate(each_beat(0.5)):
                note(r, t, 0.42, velocity - (0 if i % 2 == 0 else 10))
        elif style == "sixteenths":
            for i, t in enumerate(each_beat(0.25)):
                note(r, t, 0.2, velocity - (0 if i % 4 == 0 else 14))
        elif style == "offbeat":
            for t in each_beat(1):
                if t + 0.5 < e.end:
                    note(r, t + 0.5, 0.4)
        elif style == "root_fifth":
            for i, t in enumerate(each_beat(bar / 2)):
                note(r if i % 2 == 0 else fifth_below, t, min(bar / 2, e.end - t) * 0.9)
        elif style == "octaves":
            for i, t in enumerate(each_beat(0.5)):
                note(r if i % 2 == 0 else r + 12, t, 0.4, velocity - (0 if i % 2 == 0 else 6))
        elif style == "arpeggio":
            seq = [r, third, fifth, r + 12]
            for i, t in enumerate(each_beat(0.5)):
                note(seq[i % 4], t, 0.45)
        elif style == "pedal":
            p = _near(key.tonic if key else root_of(events[0]), center)
            for i, t in enumerate(each_beat(0.5)):
                note(p, t, 0.45, velocity - (0 if i % 2 == 0 else 8))
        elif style == "boogie":
            six = r + 9
            b7 = r + 10
            seq = [r, third, fifth, six, b7, six, fifth, third]
            for i, t in enumerate(each_beat(0.5)):
                note(seq[i % 8], t, 0.45, velocity - (0 if i % 2 == 0 else 8))
        elif style == "motown":
            # These one-bar patterns are written for 4/4; in a shorter bar the
            # positions past its end are skipped instead of spilling into the next.
            lead_in = bar - 0.5
            for t0 in each_beat(bar):
                pattern = [(0, r, 0.9), (1, r + 12, 0.4), (1.5, fifth, 0.4), (2, r, 0.9), (3, fifth, 0.4)]
                for pos, p, length in pattern:
                    if pos < lead_in - 1e-6 and t0 + pos < e.end - 1e-6:
                        note(p, t0 + pos, length)
                if nxt and t0 + bar >= e.end - 1e-6 and t0 + lead_in < e.end:
                    target = _near(root_of(nxt), r)
                    note(target + (1 if rng.random() < 0.5 else -1), t0 + lead_in, 0.4, velocity - 8)
                elif t0 + lead_in < e.end:
                    note(fifth, t0 + lead_in, 0.4, velocity - 8)
        elif style == "alberti":
            seq = [r, fifth, r + 12 + (third - r), fifth]
            for i, t in enumerate(each_beat(0.5)):
                note(seq[i % 4], t, 0.45, velocity - (0 if i % 2 == 0 else 10))
        elif style == "walking":
            beats = list(each_beat(1))
            target = _near(root_of(nxt), r) if nxt else r
            line = [r]
            chord_pcs = tones(e)
            scale = key.pitch_classes() if key else set(chord_pcs)
            for b in range(1, len(beats)):
                remaining = len(beats) - b
                cur = line[-1]
                if remaining == 1:
                    approach = target + (1 if cur > target else -1) if rng.random() < 0.6 else target - 5
                    line.append(approach if abs(approach - cur) <= 7 else cur + (1 if target > cur else -1))
                    continue
                direction = 1 if target > cur else -1
                options = [cur + direction * s for s in (1, 2, 3, 4)]
                good = [o for o in options if o % 12 in chord_pcs] + [o for o in options if o % 12 in scale]
                line.append(good[0] if good else cur + direction * 2)
            for t, p in zip(beats, line):
                p = max(28, min(55, p))
                note(p, t, 0.9, velocity - (0 if abs(t % bar) < 1e-6 else 8))
        elif style == "808":
            for t0 in each_beat(bar):
                hits = [(0, r), (1.75, r), (2.5, r + 12 if rng.random() < 0.3 else r)]
                for k, (pos, p) in enumerate(hits):
                    t = t0 + pos
                    if t >= e.end - 1e-6 or pos >= bar - 1e-6:
                        break
                    nxt_t = t0 + hits[k + 1][0] if k + 1 < len(hits) else min(e.end, t0 + bar)
                    note(p, t, max(0.25, min(nxt_t, e.end) - t))
        elif style == "syncopated":
            for t0 in each_beat(bar):
                pattern = [(0, r, 0.4), (0.75, r, 0.2), (1.5, r + 12, 0.25), (2.5, r, 0.4), (3.25, fifth, 0.2), (3.5, r, 0.4)]
                for pos, p, length in pattern:
                    if pos < bar - 1e-6 and t0 + pos < e.end - 1e-6:
                        note(p, t0 + pos, length, velocity - (0 if pos == 0 else 10))
        elif style == "one_drop":
            for t0 in each_beat(bar):
                pattern = [(0, r, 0.9), (1.5, fifth_below, 0.4), (2, r, 0.9), (3, third, 0.4), (3.5, fifth, 0.4)]
                for pos, p, length in pattern:
                    if pos < bar - 1e-6 and t0 + pos < e.end - 1e-6:
                        note(p, t0 + pos, length)
        elif style == "tumbao":
            for t0 in each_beat(bar):
                if 1.5 < bar - 1e-6 and t0 + 1.5 < e.end - 1e-6:
                    note(fifth_below if fifth_below > 28 else fifth, t0 + 1.5, 1.4)
                if 3 < bar - 1e-6 and t0 + 3 < e.end - 1e-6:
                    ahead = root_of(nxt) if (nxt and t0 + bar >= e.end - 1e-6) else root_of(e)
                    note(_near(ahead, r), t0 + 3, 2.4)
        else:
            raise ValueError(f"unknown bass style '{style}'")
        last = r
        if seventh_pc is not None:
            pass
    return notes


# Styles whose notes are short enough to take approach notes and fills; held styles
# (whole, reese, root), a pedal and lines that already lead (walking, tumbao) are left
# as they are.
_DEVELOP_STYLES = {"eighths", "sixteenths", "offbeat", "root_fifth", "octaves", "arpeggio", "boogie",
                   "motown", "alberti", "808", "syncopated", "one_drop"}


def bar_variety(notes: list[dict], meter: str = "4/4") -> float:
    """Distinct bars (pitches and positions) over all bars: a four-bar loop repeated
    eight times is 4/32 = 0.12; a part where every bar is new is 1."""
    bar = _bar_len(meter)
    if not notes:
        return 0.0
    t0 = min(n["start"] for n in notes)
    by_bar: dict[int, list] = {}
    for n in notes:
        b = int((n["start"] - t0) // bar + 1e-9)
        by_bar.setdefault(b, []).append((n["pitch"], round((n["start"] - t0) % bar, 2)))
    bars = [tuple(sorted(by_bar.get(b, []))) for b in range(max(by_bar) + 1)]
    return round(len(set(bars)) / max(1, len(bars)), 2)


def develop_bass(notes: list[dict], events: list[ChordEvent], style: str, meter: str = "4/4",
                 seed: int | None = None, groove: list[float] | None = None, kick: str = "lock") -> list[dict]:
    """A bass part that moves instead of looping one bar: an approach note (a semitone
    or the 5th) into each chord change, every second bar of a two-bar cell varied (one
    weak note to the octave, the 5th or the chord's 7th), and the last beat of every
    4th bar a fill (an octave run, a b7 lead-in, or a drop-out). groove: the kick's
    positions in the bar (QN, e.g. [0, 1, 2, 3]); kick 'lock' accents notes on the kick
    and softens the rest, 'avoid' moves notes off the kick to the next 16th (an offbeat
    house bass). Notes never leave their bar or the part."""
    if style not in _DEVELOP_STYLES or not notes or not events:
        return notes
    rng = random.Random(None if seed is None else seed * 7 + 3)
    bar = _bar_len(meter)
    t0, end = events[0].start, events[-1].end
    out = [dict(n) for n in sorted(notes, key=lambda n: n["start"])]

    def bar_of(t: float) -> int:
        return int((t - t0) // bar + 1e-9)

    # Approach notes into each change of root.
    for e, nxt in zip(events, events[1:]):
        target_pc = (nxt.chord.bass if nxt.chord.bass is not None else nxt.chord.root) % 12
        here = (e.chord.bass if e.chord.bass is not None else e.chord.root) % 12
        if target_pc == here:
            continue
        last = [n for n in out if e.end - 1.0 - 1e-6 <= n["start"] < e.end - 1e-6]
        if not last:
            continue
        n = last[-1]
        target = min((p for p in range(n["pitch"] - 7, n["pitch"] + 8) if p % 12 == target_pc),
                     key=lambda p: abs(p - n["pitch"]))
        n["pitch"] = target + (rng.choice((-1, 1)) if rng.random() < 0.6 else -5)
        n["length"] = min(n["length"], e.end - n["start"])
    # The second bar of each two-bar cell: one weak-beat note moves.
    for b in range(1, bar_of(end - 1e-6) + 1, 2):
        weak = [n for n in out if bar_of(n["start"]) == b and abs((n["start"] - t0) % 1) > 1e-6]
        if not weak:
            continue
        n = rng.choice(weak)
        ev = chord_at(events, n["start"])
        root = (ev.chord.bass if ev and ev.chord.bass is not None else (ev.chord.root if ev else n["pitch"])) % 12
        seventh = next(((ev.chord.root + i) % 12 for i in ev.chord.intervals if i % 12 in (10, 11)), None) if ev else None
        options = [n["pitch"] + 12 if n["pitch"] + 12 <= 60 else n["pitch"] - 12, n["pitch"] + 7 if n["pitch"] + 7 <= 60 else n["pitch"] - 5]
        if seventh is not None:
            options.append(min((p for p in range(n["pitch"] - 6, n["pitch"] + 7) if p % 12 == seventh), key=lambda p: abs(p - n["pitch"])))
        if n["pitch"] % 12 == root:
            n["pitch"] = rng.choice(options)
    # A fill on the last beat of every 4th bar.
    for b in range(3, bar_of(end - 1e-6) + 1, 4):
        beat_start = t0 + (b + 1) * bar - 1.0
        if beat_start >= end - 1e-6:
            continue
        in_beat = [n for n in out if beat_start - 1e-6 <= n["start"] < beat_start + 1.0 - 1e-6]
        anchor_note = next((n for n in reversed(out) if n["start"] < beat_start), None)
        if anchor_note is None:
            continue
        r = anchor_note["pitch"]
        kind = rng.choice(("run", "b7", "dropout"))
        for n in in_beat:
            out.remove(n)
        for n in out:
            if n["start"] < beat_start and n["start"] + n["length"] > beat_start - 0.02:
                n["length"] = round(max(0.05, beat_start - n["start"] - 0.02), 6)
        if kind == "run":
            for i, step in enumerate((0, 12, 7, 12)):
                p = r + step if r + step <= 60 else r + step - 12
                out.append({"pitch": p, "start": round(beat_start + i * 0.25, 6), "length": 0.2,
                            "velocity": max(1, min(127, anchor_note.get("velocity", 100) - 4 + 3 * i)), "channel": 1})
        elif kind == "b7":
            out.append({"pitch": r + 10 if r + 10 <= 60 else r - 2, "start": round(beat_start + 0.5, 6), "length": 0.45,
                        "velocity": anchor_note.get("velocity", 100), "channel": 1})
        # dropout: the beat stays empty, so the downbeat after it lands harder
    out.sort(key=lambda n: n["start"])
    # Against the kick.
    if groove:
        kicks = [g % bar for g in groove]
        for n in out:
            pos = (n["start"] - t0) % bar
            on_kick = any(abs(pos - k) < 0.05 for k in kicks)
            if kick == "lock":
                n["velocity"] = max(1, min(127, n.get("velocity", 100) + (8 if on_kick else -6)))
            elif kick == "avoid" and on_kick:
                moved = n["start"] + 0.25
                if bar_of(moved) == bar_of(n["start"]) and moved < end - 0.05:
                    n["start"] = round(moved, 6)
                    n["length"] = round(max(0.05, n["length"] - 0.25), 6)
    return _tidy_line(out, end)


def _tidy_line(notes: list[dict], end: float) -> list[dict]:
    """No two notes of one pitch on one start, none running into the next note of its
    pitch, none past the end."""
    out: list[dict] = []
    seen: set = set()
    for n in sorted(notes, key=lambda n: (n["start"], n["pitch"])):
        k = (n["pitch"], round(n["start"], 4))
        if k in seen or n["start"] >= end - 1e-6:
            continue
        seen.add(k)
        out.append(n)
    for i, n in enumerate(out):
        nxt = next((m for m in out[i + 1:] if m["pitch"] == n["pitch"]), None)
        stop = min(end, nxt["start"] - 0.02 if nxt else end)
        if n["start"] + n["length"] > stop:
            n["length"] = round(max(0.05, stop - n["start"]), 6)
    return out


# ------------------------------------------------------------------- melody

_DENSITY_ONSETS = {"sparse": (2, 4), "medium": (4, 6), "busy": (6, 9)}


def _motif_rhythm(rng: random.Random, density: str, bar: float, syncopation: float) -> list[float]:
    lo, hi = _DENSITY_ONSETS.get(density, (4, 6))
    count = rng.randint(lo, hi)
    grid = [i * 0.5 for i in range(int(bar * 2))] if density != "busy" else [i * 0.25 for i in range(int(bar * 4))]
    weights = []
    for g in grid:
        if abs(g % 1) < 1e-6:
            w = 3.0 if abs(g % 2) < 1e-6 else 2.2
        elif abs(g % 0.5) < 1e-6:
            w = 1.2 + syncopation * 1.5
        else:
            w = 0.6 + syncopation
        weights.append(w)
    if not grid:
        return [0.0]
    # A short bar (2/4, 3/8) can have fewer slots than the density asks for; drawing
    # until the count was reached never finished there.
    count = min(count, len(grid))
    chosen = {0.0} if rng.random() < 0.7 else set()
    while len(chosen) < count:
        chosen.add(rng.choices(grid, weights)[0])
    return sorted(chosen)


# The cell's moves, in scale steps: mostly steps, the odd leap.
_MOVES = ([-2, -1, 1, 2, 3, -3, 4, -4], [2.0, 5.0, 5.0, 2.5, 1.5, 1.0, 0.7, 0.5])
# Where each shape sits in the range (0 = low end, 1 = top).
_SHAPE_HEIGHT = {"hook": 0.6, "verse": 0.35, "answer": 0.5}
# The period: each phrase's kind, in order (A, its answer, a contrast, A again to close).
_PERIOD = ("A", "A'", "B", "A''")


def _cell(rng: random.Random, density: str, bar: float, syncopation: float) -> tuple[list[float], list[int]]:
    """A one-bar idea: a rhythm and the scale-step moves between its notes (the first is 0)."""
    rhythm = _motif_rhythm(rng, density, bar, syncopation)
    moves = [0] + [rng.choices(*_MOVES)[0] for _ in rhythm[1:]]
    # A cell that only climbs or only falls has no shape to remember: turn its last move.
    if len(moves) > 2 and all(m > 0 for m in moves[1:]) or len(moves) > 2 and all(m < 0 for m in moves[1:]):
        moves[-1] = -moves[-1]
    return rhythm, moves


def _rhythm_variant(rng: random.Random, rhythm: list[float], bar: float) -> list[float]:
    """The same rhythm with one onset moved or added: recognisably the cell, not a copy."""
    slots = [x * 0.5 for x in range(int(bar * 2))]
    out = list(rhythm)
    if len(out) > 1 and rng.random() < 0.5:
        out.pop(rng.randrange(1, len(out)))
    out.append(rng.choice(slots))
    return sorted(set(round(x, 3) for x in out))


def _bar_plan(phrase_bars: int) -> list[str]:
    """What each bar of a phrase does: the cell, the cell moved to the chord, its rhythmic
    variant, ..., and the ending."""
    if phrase_bars <= 1:
        return ["end"]
    body = ["cell", "shift", "variant", "shift"]
    return [body[i % 4] for i in range(phrase_bars - 1)] + ["end"]


def melody(events: list[ChordEvent], key: Key, density: str = "medium", low: int = 60, high: int = 79,
           scale: str | None = None, meter: str = "4/4", phrase_bars: int = 4, seed: int | None = None,
           syncopation: float = 0.3, velocity: int = 92, shape: str = "hook", rests: bool = True,
           register_lift: int = 0) -> list[dict]:
    """A melody built like a song's: one bar-long cell (a rhythm and a contour) that
    phrases repeat, move onto each bar's chord and vary, phrases in a period A A' B A''
    (A and B different cells, B higher), question phrases ending on the 2nd or 5th and
    answers on the tonic, a held last note and a breath at the end of each phrase
    (rests), chord tones on strong beats, pickups short and phrase endings long, and the
    tonic at the end; each later period a step higher, so it builds. shape sets the
    register (hook high, verse low, answer between);
    register_lift raises it this many scale steps (a chorus a 3rd-5th over the verse)."""
    rng = random.Random(seed)
    bar = _bar_len(meter)
    if not events:
        return []
    total_start, total_end = events[0].start, events[-1].end
    scale_pcs = ({(key.tonic + i) % 12 for i in scales_db.find_scale(scale).intervals} if scale else key.pitch_classes())
    pool = [p for p in range(low, high + 1) if p % 12 in scale_pcs]
    if not pool:
        raise ValueError("no scale notes in that range")
    n_bars = max(1, math.ceil((total_end - total_start) / bar - 1e-6))
    cells = {"A": _cell(rng, density, bar, syncopation), "B": _cell(rng, density, bar, syncopation)}
    # B answers A: the other cell, its contour turned upside down so it's a contrast.
    cells["B"] = (cells["B"][0], [0] + [-m for m in cells["B"][1][1:]])
    variants = {k: _rhythm_variant(rng, r, bar) for k, (r, _) in cells.items()}
    home = int(round((len(pool) - 1) * _SHAPE_HEIGHT.get(shape, 0.5))) + register_lift
    home = max(0, min(len(pool) - 1, home))
    plan = _bar_plan(phrase_bars)
    n_phrases = math.ceil(n_bars / phrase_bars)
    # Room to build: the last period reaches the shape's height, earlier ones sit under it.
    home = max(0, home - min(2, (n_phrases - 1) // 4))

    def nearest_index(pitch_pcs: set[int], around: int, spread: int = 3) -> int:
        cands = [i for i in range(max(0, around - spread), min(len(pool), around + spread + 1)) if pool[i] % 12 in pitch_pcs]
        return min(cands, key=lambda i: (abs(i - around), -i)) if cands else around

    notes: list[dict] = []
    for b in range(n_bars):
        phrase, step = divmod(b, phrase_bars)
        kind = _PERIOD[phrase % 4]
        last_phrase = phrase == n_phrases - 1
        role = plan[min(step, len(plan) - 1)] if b < n_bars - 1 else "end"
        rhythm, moves = cells["B" if kind == "B" else "A"]
        if role == "variant":
            rhythm = variants["B" if kind == "B" else "A"]
            moves = moves + [rng.choice(_MOVES[0][:4]) for _ in range(len(rhythm) - len(moves))]
        bar_start = total_start + b * bar
        e = chord_at(events, bar_start)
        chord_pcs = e.chord.pitch_classes() if e else scale_pcs
        # Each later period sits a step higher: the line builds, and its peak comes late.
        start_index = home + (2 if kind == "B" else 0) + (1 if kind == "A''" and role == "shift" else 0) + min(2, phrase // 4)
        if role in ("shift", "variant", "end"):
            start_index = nearest_index(chord_pcs, start_index)   # the cell moved onto this bar's chord
        if role == "end":
            # The phrase closes: the cell's first half, then one long note and a breath.
            head = [x for x in rhythm if x < bar / 2] or [0.0]
            closing = (last_phrase and b == n_bars - 1) or kind in ("A'", "A''")
            target_pcs = {key.tonic % 12} if closing else {(key.tonic + 2) % 12, (key.tonic + 7) % 12}
            onsets = head
        else:
            onsets = rhythm
            target_pcs = None
        # The contour centred on the bar's start, so a climbing cell can't run into the
        # top of the range early and leave the later periods nowhere higher to go.
        path = [0]
        for j in range(1, len(onsets)):
            path.append(path[-1] + (moves[j] if j < len(moves) else rng.choice((-1, 1))))
        middle = round((max(path) + min(path)) / 2)
        bar_notes = []
        for j, x in enumerate(onsets):
            t = bar_start + x
            if t >= total_end - 0.1:
                break
            idx = start_index + path[j] - middle
            idx = max(0, min(len(pool) - 1, idx))
            strong = abs(x % 1) < 1e-6
            ec = chord_at(events, t)
            pcs = ec.chord.pitch_classes() if ec else scale_pcs
            if strong and pool[idx] % 12 not in pcs:
                idx = nearest_index(pcs, idx, 1)
            bar_notes.append([t, idx])
        if role == "end" and bar_notes:
            # The held note: the target degree nearest where the line is.
            bar_notes[-1][1] = nearest_index(target_pcs, bar_notes[-1][1], 4)
        for k, (t, i) in enumerate(bar_notes):
            nxt = bar_notes[k + 1][0] if k + 1 < len(bar_notes) else bar_start + bar
            length = (nxt - t) * 0.9
            in_bar = t - bar_start
            if k + 1 < len(bar_notes) and in_bar % 1 >= 0.5 - 1e-6:
                length = min(length, (nxt - t) * 0.6)                        # a pickup: short
            if role == "end" and k == len(bar_notes) - 1:
                length = max(bar * 0.5 - in_bar % bar, (bar - in_bar) * (0.6 if rests else 0.95))  # held, then a breath
            strong = abs(in_bar % 1) < 1e-6
            notes.append({"pitch": pool[i], "start": round(t, 6),
                          "length": round(max(0.1, min(length, total_end - t)), 6),
                          "velocity": max(1, min(127, velocity + (6 if strong else -6) + rng.randint(-4, 4))),
                          "channel": 1})
    if notes:
        # The last note is the tonic, nearest the line, and lasts to the end.
        tonics = [q for q in pool if q % 12 == key.tonic]
        if tonics:
            notes[-1]["pitch"] = min(tonics, key=lambda q: abs(q - notes[-1]["pitch"]))
        notes[-1]["length"] = round(max(0.1, total_end - notes[-1]["start"]), 6)
    return notes


def hook_score(notes: list[dict], meter: str = "4/4") -> dict:
    """How memorable a melody's shape is: bar_repetition (share of bars whose rhythm and
    intervals come back from an earlier bar: a hook repeats, a ramble doesn't), range
    (semitones), rest_ratio (share of the time silent: room to breathe), peak_position
    (the last time it reaches its highest note, 0 start .. 1 end), and score (0 best; how far those
    sit from 0.35-0.75, 7-15, 0.08-0.35 and 0.45-0.85)."""
    if not notes:
        return {}
    bar = _bar_len(meter)
    t0 = min(n["start"] for n in notes)
    by_bar: dict[int, list[dict]] = {}
    for n in sorted(notes, key=lambda n: n["start"]):
        by_bar.setdefault(int((n["start"] - t0) // bar + 1e-9), []).append(n)
    seen, repeats = set(), 0
    for b in sorted(by_bar):
        ns = by_bar[b]
        sig = tuple((round((n["start"] - t0) % bar, 2), ns[i]["pitch"] - ns[i - 1]["pitch"] if i else 0)
                    for i, n in enumerate(ns))
        repeats += sig in seen
        seen.add(sig)
    end = max(n["start"] + n["length"] for n in notes)
    covered = sum(n["length"] for n in notes)
    # The climax: the last time the line reaches its highest note.
    highest = max(n["pitch"] for n in notes)
    top = max((n for n in notes if n["pitch"] == highest), key=lambda n: n["start"])
    out = {"bar_repetition": round(repeats / max(1, len(by_bar)), 2),
           "range": max(n["pitch"] for n in notes) - min(n["pitch"] for n in notes),
           "rest_ratio": round(max(0.0, 1 - covered / max(1e-9, end - t0)), 2),
           "peak_position": round((top["start"] - t0) / max(1e-9, end - t0), 2)}

    def off(v: float, lo: float, hi: float, scale: float) -> float:
        return 0.0 if lo <= v <= hi else (lo - v if v < lo else v - hi) / scale
    out["score"] = round(off(out["bar_repetition"], 0.35, 0.75, 0.1) + off(out["range"], 7, 15, 3)
                         + off(out["rest_ratio"], 0.08, 0.35, 0.05) + off(out["peak_position"], 0.45, 0.85, 0.1), 2)
    return out


# ------------------------------------------------------------------- rhythm

def euclidean(hits: int, steps: int, rotate: int = 0) -> str:
    """Spreads hits as evenly as possible over steps (Bjorklund), e.g. (3, 8) = tresillo."""
    if not 0 <= hits <= steps or steps <= 0:
        raise ValueError("need 0 <= hits <= steps")
    pattern = ["x" if (i * hits) % steps < hits else "." for i in range(steps)]
    pattern = [pattern[(i - 0) % steps] for i in range(steps)]
    # Bresenham gives the same necklace as Bjorklund; rotate so a hit starts unless asked otherwise.
    first = pattern.index("x") if "x" in pattern else 0
    pattern = pattern[first:] + pattern[:first]
    rotate %= steps
    return "".join(pattern[rotate:] + pattern[:rotate])


RHYTHMS: dict[str, dict] = {
    "son clave 3-2": {"step": 0.5, "steps": "x..x..x...x.x...", "about": "The Cuban timeline: 3 side then 2 side (2 bars of 8ths)."},
    "son clave 2-3": {"step": 0.5, "steps": "..x.x...x..x..x.", "about": "Son clave starting on the 2 side."},
    "rumba clave 3-2": {"step": 0.5, "steps": "x..x...x..x.x...", "about": "Like son clave with the third stroke delayed: more tension."},
    "rumba clave 2-3": {"step": 0.5, "steps": "..x.x...x..x...x", "about": "Rumba clave from the 2 side."},
    "bossa clave": {"step": 0.5, "steps": "x..x..x...x..x..", "about": "Bossa nova's clave: the last stroke shifted late."},
    "tresillo": {"step": 0.5, "steps": "x..x..x.", "about": "3+3+2: the backbone of Latin, reggaeton, Afro-Caribbean and pop rhythm."},
    "cinquillo": {"step": 0.5, "steps": "x.xx.xx.", "about": "Five-stroke Cuban/Caribbean cell (danzón, merengue)."},
    "habanera": {"step": 0.5, "steps": "x..xx.x.", "about": "Dotted figure of the habanera and tango."},
    "dembow (snare)": {"step": 0.25, "steps": "...x..x....x..x.", "about": "Reggaeton's snare over a four-on-the-floor kick."},
    "bembe bell (12/8)": {"step": 0.5, "steps": "x.x.xx.x.x.x", "about": "The West African standard bell pattern (7 strokes in 12)."},
    "shiko": {"step": 0.25, "steps": "x...x.x...x.x...", "about": "West African timeline related to the clave."},
    "four on the floor": {"step": 0.25, "steps": "x...x...x...x...", "about": "A kick on every beat: disco, house, techno."},
    "backbeat": {"step": 0.25, "steps": "....x.......x...", "about": "Snare on 2 and 4."},
    "half-time backbeat": {"step": 0.25, "steps": "........x.......", "about": "Snare on beat 3: hip-hop, trap, dubstep feel."},
    "one drop": {"step": 0.25, "steps": "........x.......", "about": "Reggae: kick and rim together on beat 3, nothing on 1."},
    "shuffle": {"step": 1 / 3, "steps": "x.xx.xx.xx.x", "about": "Triplet shuffle: long-short pairs."},
    "aksak 7/8 (2+2+3)": {"step": 0.5, "steps": "x.x.x..", "about": "Balkan 7/8 grouped short-short-long."},
    "aksak 9/8 (2+2+2+3)": {"step": 0.5, "steps": "x.x.x.x..", "about": "Balkan/Turkish 9/8 (karsilama)."},
    "5/4 (3+2)": {"step": 0.5, "steps": "x..x.x..x.", "about": "Five beats grouped 3+2."},
    "maqsum": {"step": 0.25, "steps": "x.x...x.x...x...", "about": "Arabic iqa' (dum tek - tek dum - tek -, in eighths): dums on beats 1 and 3, teks on the 'and' of 1, the 'and' of 2 and beat 4."},
}


def polyrhythm(a: int, b: int) -> dict[str, str]:
    steps = a * b // math.gcd(a, b)
    return {f"{a} against {b} (A)": "".join("x" if i % (steps // a) == 0 else "." for i in range(steps)),
            f"{a} against {b} (B)": "".join("x" if i % (steps // b) == 0 else "." for i in range(steps))}


# --------------------------------------------------------- motif transforms

def _scale_index(pitch: int, key: Key) -> float:
    """Position of a pitch in the key's scale (fractional for chromatic notes)."""
    degs = sorted(key.scale.intervals)
    octave, pc = divmod(pitch - key.tonic, 12)
    for i, d in enumerate(degs):
        if d == pc:
            return octave * len(degs) + i
    below = max((i for i, d in enumerate(degs) if d < pc), default=0)
    return octave * len(degs) + below + 0.5


def _from_index(index: float, key: Key, original: int | None = None) -> int:
    degs = sorted(key.scale.intervals)
    n = len(degs)
    whole = math.floor(index)
    frac = index - whole
    octave, i = divmod(whole, n)
    pitch = key.tonic + 12 * octave + degs[i]
    if frac >= 0.5:
        pitch += 1
    return pitch


def diatonic_transpose(notes: list[dict], steps: int, key: Key) -> list[dict]:
    out = []
    for n in notes:
        idx = _scale_index(n["pitch"], key) + steps
        out.append({**n, "pitch": max(0, min(127, _from_index(idx, key)))})
    return out


def invert(notes: list[dict], axis: int | None = None, key: Key | None = None) -> list[dict]:
    """Mirror image of a melody around a pitch (default: its first note): diatonic in a key, else chromatic."""
    if not notes:
        return []
    first = min(notes, key=lambda n: n["start"])
    axis = first["pitch"] if axis is None else axis
    out = []
    for n in notes:
        if key is not None:
            idx = 2 * _scale_index(axis, key) - _scale_index(n["pitch"], key)
            p = _from_index(idx, key)
        else:
            p = 2 * axis - n["pitch"]
        out.append({**n, "pitch": max(0, min(127, p))})
    return out


def retrograde(notes: list[dict]) -> list[dict]:
    if not notes:
        return []
    t0 = min(n["start"] for n in notes)
    t1 = max(n["start"] + n["length"] for n in notes)
    return sorted(({**n, "start": round(t0 + (t1 - (n["start"] + n["length"])) - 0, 6)} for n in notes),
                  key=lambda n: (n["start"], n["pitch"]))


def scale_time(notes: list[dict], factor: float) -> list[dict]:
    """Augmentation (factor 2) or diminution (0.5), from the first note."""
    if not notes:
        return []
    t0 = min(n["start"] for n in notes)
    return [{**n, "start": round(t0 + (n["start"] - t0) * factor, 6), "length": round(n["length"] * factor, 6)} for n in notes]


def add_harmony(notes: list[dict], key: Key, steps: int = 2, below: bool = False, velocity_scale: float = 0.85,
                chord_at: Callable[[float], set[int] | None] | None = None) -> list[dict]:
    """Adds a parallel line a number of scale steps away (2 = thirds, 5 = sixths).
    With chord_at (start -> pitch classes sounding then), each harmony note that
    isn't in the chord moves to the nearest chord tone on the same side of the
    melody, at least a minor third away, so the line follows chords borrowed from
    outside the key (secondary dominants, borrowed chords) instead of rubbing."""
    moved = diatonic_transpose(notes, -steps if below else steps, key)
    if chord_at:
        moved = [fit_to_chord(m, n["pitch"], chord_at(n["start"]), below) for m, n in zip(moved, notes)]
    return notes + [{**n, "velocity": max(1, round(n["velocity"] * velocity_scale))} for n in moved]


def fit_to_chord(harmony_note: dict, melody_pitch: int, chord: set[int] | None, below: bool) -> dict:
    """The harmony note itself if it's a chord tone (or no chord is known), else the
    chord tone nearest to it on the harmony's side of the melody, a 3rd to an octave away."""
    if not chord or harmony_note["pitch"] % 12 in chord:
        return harmony_note
    sign = -1 if below else 1
    options = [melody_pitch + sign * d for d in range(3, 13) if (melody_pitch + sign * d) % 12 in chord]
    if not options:
        return harmony_note
    best = min(options, key=lambda p: (abs(p - harmony_note["pitch"]), abs(p - melody_pitch)))
    return {**harmony_note, "pitch": best}


def chord_lookup(chord_notes: list[dict], hold: float = 4.0) -> Callable[[float], set[int] | None]:
    """start (QN) -> the pitch classes of the chord in force then: the notes sounding,
    or else the last chord struck within `hold` QN (stabs and pushed chords)."""
    onsets: dict[float, set[int]] = {}
    for n in chord_notes:
        onsets.setdefault(round(n["start"], 3), set()).add(n["pitch"] % 12)
    times = sorted(onsets)

    def at(t: float) -> set[int] | None:
        sounding = {n["pitch"] % 12 for n in chord_notes if n["start"] <= t + 1e-3 < n["start"] + n["length"]}
        if len(sounding) >= 2:
            return sounding
        before = [x for x in times if x <= t + 1e-3 and t - x <= hold]
        return onsets[before[-1]] if before else (sounding or None)
    return at


# ------------------------------------------------------------ second lines

HOLD_QN = 1.0   # a melody note this long leaves room for the counter-melody to move under it


def counter_melody(melody_notes: list[dict], chords_at: Callable[[float], set[int] | None], key: Key,
                   low: int | None = None, high: int | None = None, density: float = 0.5,
                   seed: int | None = None, velocity: int = 78) -> list[dict]:
    """A second line that answers the melody instead of doubling it. It moves where
    the melody rests or holds (in 8ths through a gap, on the beats under a long note)
    and, where the melody is busy for a half bar, holds one long note under it instead.
    It moves against the melody's direction, never repeats a note straight away, sits
    on chord tones on the beat, a 3rd or 6th under the melody where they meet (never in
    unison or an octave with any melody note it sounds against), below the melody's
    register by default, and avoids parallel 5ths and octaves with it.
    density (0-1): how much of the room it fills."""
    if not melody_notes:
        return []
    rng = random.Random(seed)
    mel = sorted((n for n in melody_notes if not n.get("muted")), key=lambda n: n["start"])
    if not mel:
        return []
    lo_m = min(n["pitch"] for n in mel)
    low = low if low is not None else lo_m - 14
    high = high if high is not None else lo_m - 1
    pool = [p for p in range(low, high + 1) if p % 12 in key.pitch_classes()]
    if not pool:
        raise ValueError("no scale notes in that range for the counter-melody")
    end = max(n["start"] + n["length"] for n in mel)

    def melody_at(t: float) -> dict | None:
        return next((n for n in mel if n["start"] <= t + 1e-6 < n["start"] + n["length"]), None)

    def melody_move(t: float) -> int:
        """+1 / -1 / 0: where the melody is heading around t."""
        before = [n for n in mel if n["start"] <= t]
        after = [n for n in mel if n["start"] > t]
        if before and after:
            return (after[0]["pitch"] > before[-1]["pitch"]) - (after[0]["pitch"] < before[-1]["pitch"])
        return 0

    # Room: inside long held notes (after their first 8th) and in the gaps between notes.
    slots: list[float] = []
    t = min(n["start"] for n in mel)
    grid = 0.5
    while t < end - 1e-6:
        here = melody_at(t)
        moving = any(abs(n["start"] - t) < 1e-6 for n in mel)
        in_gap = here is None
        # Under a held note it moves in quarters (on the beat); in a gap, in 8ths.
        under_hold = (here is not None and here["length"] >= HOLD_QN and t >= here["start"] + grid - 1e-6
                      and not moving and abs(t % 1) < 1e-6)
        if (in_gap or under_hold) and rng.random() < 0.35 + 0.6 * density:
            slots.append(round(t, 6))
        t += grid
    # Where the melody is busy for a whole half bar: one held note under it.
    first = min(n["start"] for n in mel)
    w = math.ceil(first / 2 - 1e-9) * 2   # from the first half bar the melody is in, never before it
    while w < end - 1e-6:
        if not any(w - 1e-6 <= s_ < w + 2 - 1e-6 for s_ in slots) and rng.random() < 0.3 + 0.7 * density:
            slots.append(float(w))
        w += 2
    slots.sort()

    def sounding(t0: float, t1: float) -> list[dict]:
        return [n for n in mel if n["start"] < t1 - 1e-6 and n["start"] + n["length"] > t0 + 1e-6]

    notes: list[dict] = []
    recent: list[int] = []
    prev = pool[len(pool) // 2]
    prev_interval = None
    for k, t in enumerate(slots):
        strong = abs(t % 1) < 1e-6
        pcs = chords_at(t) or key.pitch_classes()
        above = melody_at(t)
        nxt = slots[k + 1] if k + 1 < len(slots) else t + 1.0
        length = min(max(0.25, (nxt - t) * 0.92), 2.0)
        against = sounding(t, t + length)
        # Against the melody where it moves; free (but still moving) where it holds or rests.
        melody_moves = any(abs(n["start"] - t) <= 0.5 + 1e-6 for n in mel)
        direction = -melody_move(t) if melody_moves else 0
        best, best_cost = None, None
        for p in pool:
            step = p - prev
            cost = abs(step) * 0.5
            if step == 0:
                cost += 3.0                      # a line, not one note repeated
            elif p in recent:
                cost += 1.2                      # nor two notes swapped back and forth
            if direction and step and (step > 0) != (direction > 0):
                cost += 2.0                      # contrary motion: against the melody's way
            if strong and p % 12 not in pcs:
                cost += 4.0
            if any((n["pitch"] - p) % 12 == 0 for n in against):
                cost += 10.0                     # unison or octave with the melody
            if above is not None:
                iv = (above["pitch"] - p) % 12
                if iv in (3, 4, 8, 9):
                    cost -= 1.5                  # a 3rd or 6th under it
                if prev_interval is not None and iv in (0, 7) and prev_interval == iv:
                    cost += 8.0                  # parallel 5ths or octaves
            cost += rng.random() * 0.5
            if best_cost is None or cost < best_cost:
                best, best_cost = p, cost
        notes.append({"pitch": best, "start": t, "length": round(length, 6),
                      "velocity": max(1, min(127, velocity + (4 if strong else -4))), "channel": 1})
        prev_interval = ((above["pitch"] - best) % 12) if above is not None else None
        prev = best
        recent = (recent + [best])[-2:]
    return notes


def answer(motif: list[dict], key: Key, gap: float = 0.0) -> list[dict]:
    """A reply to a motif, placed right after it (plus gap QN): the same rhythm, its
    contour turned upside down around its first note, and its last note on the tonic
    (or on the 5th when the motif itself ends home), the way a call gets its response."""
    if not motif:
        return []
    ns = sorted(motif, key=lambda n: n["start"])
    t0 = ns[0]["start"]
    span = max(n["start"] + n["length"] for n in ns) - t0
    turned = invert(ns, axis=ns[0]["pitch"], key=key)
    shift = span + gap
    out = [dict(n, start=round(n["start"] + shift, 6)) for n in turned]
    last = out[-1]
    home_pc = key.tonic if ns[-1]["pitch"] % 12 != key.tonic else (key.tonic + 7) % 12
    last["pitch"] = min((p for p in range(max(0, last["pitch"] - 7), min(127, last["pitch"] + 7) + 1)
                         if p % 12 == home_pc), key=lambda p: abs(p - last["pitch"]))
    return out


def sequence(notes: list[dict], key: Key, repeats: int = 2, steps: int = -1, span: float | None = None) -> list[dict]:
    """Repeats a motif, each time moved by scale steps (a melodic sequence)."""
    if not notes:
        return []
    t0 = min(n["start"] for n in notes)
    t1 = max(n["start"] + n["length"] for n in notes)
    length = span or math.ceil((t1 - t0) - 1e-6)
    out = list(notes)
    for r in range(1, repeats + 1):
        moved = diatonic_transpose(notes, steps * r, key)
        out += [{**n, "start": round(n["start"] + length * r, 6)} for n in moved]
    return out


def negative(notes: list[dict], key: Key) -> list[dict]:
    return [{**n, "pitch": H.negative_pitch(n["pitch"], key.tonic)} for n in notes]


# -------------------------------------------------------------- MIDI analysis

def chords_from_notes(notes: list[dict], meter: str = "4/4", resolution: str = "auto",
                      key: Key | None = None) -> list[dict]:
    """Chords over time from MIDI notes: segments notes on a grid (bar, half bar or
    beat), names each segment's chord, and merges repeats."""
    if not notes:
        return []
    bar = _bar_len(meter)
    end = max(n["start"] + n["length"] for n in notes)
    grids = {"bar": bar, "half": bar / 2, "beat": 1.0}
    if resolution == "auto":
        results = {r: _segment(notes, g, end, key) for r, g in grids.items()}
        # Prefer the coarsest grid that doesn't blur changes: compare chord counts.
        beat_changes = len(results["beat"])
        half_changes = len(results["half"])
        if beat_changes > half_changes * 1.5 and _avg_conf(results["beat"]) > _avg_conf(results["half"]) + 0.05:
            return results["beat"]
        if half_changes > len(results["bar"]) * 1.3 and _avg_conf(results["half"]) >= _avg_conf(results["bar"]) - 0.02:
            return results["half"]
        return results["bar"]
    if resolution not in grids:
        raise ValueError("resolution is auto, bar, half or beat")
    return _segment(notes, grids[resolution], end, key)


def _avg_conf(segs: list[dict]) -> float:
    return sum(s.get("confidence", 0) for s in segs) / len(segs) if segs else 0


def _segment(notes: list[dict], grid: float, end: float, key: Key | None) -> list[dict]:
    segs: list[dict] = []
    t = 0.0
    start0 = min(n["start"] for n in notes)
    t = math.floor(start0 / grid) * grid
    while t < end - 1e-6:
        w = [0.0] * 12
        lowest, lowest_pitch = None, 999
        for n in notes:
            overlap = min(n["start"] + n["length"], t + grid) - max(n["start"], t)
            if overlap <= 1e-6:
                continue
            onset_bonus = 1.3 if t - 1e-6 <= n["start"] < t + grid else 1.0
            w[n["pitch"] % 12] += overlap * onset_bonus
            if n["pitch"] < lowest_pitch:
                lowest_pitch, lowest = n["pitch"], n["pitch"] % 12
        top = max(w)
        if top > 0:
            pcs = [pc for pc in range(12) if w[pc] >= top * 0.22]
            found = H.identify_chord(pcs, bass=lowest, key=key, limit=1)
            if found:
                f = found[0]
                if segs and segs[-1]["chord"] == f["symbol"] and abs(segs[-1]["start"] + segs[-1]["length"] - t) < 1e-6:
                    segs[-1]["length"] += grid
                else:
                    segs.append({"chord": f["symbol"], "start": round(t, 4), "length": grid,
                                 "confidence": f["confidence"], "notes": f["notes"]})
        t += grid
    return segs


def nonchord_tones(melody_notes: list[dict], events: list[ChordEvent]) -> list[dict]:
    """Classifies each melody note that isn't in the chord under it."""
    mel = sorted(melody_notes, key=lambda n: n["start"])
    out = []
    for i, n in enumerate(mel):
        e = chord_at(events, n["start"])
        if e is None or n["pitch"] % 12 in e.chord.pitch_classes():
            continue
        prev = mel[i - 1]["pitch"] if i > 0 else None
        nxt = mel[i + 1]["pitch"] if i + 1 < len(mel) else None
        p = n["pitch"]
        d1 = p - prev if prev is not None else None
        d2 = nxt - p if nxt is not None else None
        kind = "non-chord tone"
        on_beat = abs(n["start"] % 1) < 1e-6
        next_chord = chord_at(events, mel[i + 1]["start"]) if i + 1 < len(mel) else None
        if d1 is not None and d2 is not None:
            if d1 == 0 and d2 in (-1, -2):
                kind = "suspension (held over and resolving down by step)"
            elif d1 == 0 and d2 in (1, 2):
                kind = "retardation (held over and resolving up)"
            elif 0 < abs(d1) <= 2 and 0 < abs(d2) <= 2 and d1 * d2 > 0:
                kind = "passing tone" + (" (accented)" if on_beat else "")
            elif 0 < abs(d1) <= 2 and 0 < abs(d2) <= 2 and d1 * d2 < 0:
                kind = "neighbor tone" + (" (accented)" if on_beat else "")
            elif abs(d1) > 2 and 0 < abs(d2) <= 2 and d1 * d2 < 0:
                kind = "appoggiatura (leap in, step out the other way)"
            elif 0 < abs(d1) <= 2 and abs(d2) > 2 and d1 * d2 < 0:
                kind = "escape tone (step in, leap out the other way)"
            elif d2 == 0 and next_chord is not None and next_chord is not e and p % 12 in next_chord.chord.pitch_classes():
                kind = "anticipation (arrives early on the next chord's note)"
        elif d2 == 0 and next_chord is not None and p % 12 in next_chord.chord.pitch_classes():
            kind = "anticipation"
        out.append({"note": H.theory.midi_to_note(p), "start": n["start"], "over": e.chord.symbol, "kind": kind})
    return out


def harmonize(melody_notes: list[dict], key: Key, chords_per_bar: float = 1, meter: str = "4/4",
              palette: str = "diatonic", sevenths: bool = False) -> list[ChordEvent]:
    """Chooses chords for a melody (Viterbi over segments): melody notes on strong
    beats should be chord tones, chords should move functionally (T-PD-D-T), and
    the last chord should be the tonic, approached from a dominant if possible.
    palette: diatonic, or colorful (adds secondary dominants and borrowed chords)."""
    if not melody_notes:
        return []
    bar = _bar_len(meter)
    seg = bar / chords_per_bar
    t0 = math.floor(min(n["start"] for n in melody_notes) / bar) * bar
    t1 = max(n["start"] + n["length"] for n in melody_notes)
    n_seg = max(1, math.ceil((t1 - t0) / seg - 1e-6))
    cands = list(H.diatonic_chords(key, sevenths))
    if key.is_minor:
        cands.append(H.parse_roman("V7" if sevenths else "V", key).chord)
    if palette == "colorful":
        for num in ("V7/V", "V7/vi", "V7/ii", "iv", "bVII", "bVI") if not key.is_minor else ("V7/iv", "IV", "bII", "V7/III"):
            try:
                cands.append(H.parse_roman(num, key).chord)
            except ValueError:
                pass
    numerals = [H.numeral_for(c, key) for c in cands]
    funcs = [rc.function for rc in numerals]

    def emission(ci: int, s: int) -> float:
        c = cands[ci]
        pcs = c.pitch_classes()
        score = 0.0
        lo, hi = t0 + s * seg, t0 + (s + 1) * seg
        for n in melody_notes:
            overlap = min(n["start"] + n["length"], hi) - max(n["start"], lo)
            if overlap <= 0:
                continue
            strong = 2.0 if abs((n["start"] - lo)) < 1e-6 else (1.5 if abs(n["start"] % 1) < 1e-6 else 1.0)
            w = overlap * strong
            if n["pitch"] % 12 in pcs:
                score += w
            elif n["pitch"] % 12 in key.pitch_classes():
                score -= 0.35 * w
            else:
                score -= 1.0 * w
        if funcs[ci] in ("chromatic", "secondary dominant"):
            score -= 0.4
        return score

    order = {"tonic": 0, "predominant": 1, "dominant": 2, "subtonic": 2, "secondary dominant": 1.5, "chromatic": 1}

    def transition(a: int, b: int) -> float:
        fa, fb = order.get(funcs[a], 1), order.get(funcs[b], 1)
        if a == b:
            return -0.6
        if fa == 2 and fb == 0:
            return 1.6
        if fa == 1 and fb == 2:
            return 1.2
        if fa == 0 and fb in (1, 2):
            return 0.6
        if fa == 2 and fb == 1:
            return -0.8
        if funcs[a] == "secondary dominant":
            return 1.4 if (cands[b].root - cands[a].root) % 12 == 5 else -1.5
        return 0.2

    tonic_idx = [i for i, c in enumerate(cands) if c.root == key.tonic]
    dominant_idx = [i for i, c in enumerate(cands) if (c.root - key.tonic) % 12 == 7]
    score = [[-1e9] * len(cands) for _ in range(n_seg)]
    back = [[0] * len(cands) for _ in range(n_seg)]
    for ci in range(len(cands)):
        score[0][ci] = emission(ci, 0) + (1.0 if ci in tonic_idx else 0)
    for s in range(1, n_seg):
        for b in range(len(cands)):
            best, arg = -1e9, 0
            for a in range(len(cands)):
                v = score[s - 1][a] + transition(a, b)
                if v > best:
                    best, arg = v, a
            bonus = 0.0
            if s == n_seg - 1 and b in tonic_idx:
                bonus += 2.5
            if s == n_seg - 2 and b in dominant_idx:
                bonus += 1.0
            score[s][b] = best + emission(b, s) + bonus
            back[s][b] = arg
    last = max(range(len(cands)), key=lambda c: score[-1][c])
    path = [last]
    for s in range(n_seg - 1, 0, -1):
        path.append(back[s][path[-1]])
    path.reverse()
    return [ChordEvent(cands[ci], t0 + s * seg, seg, numerals[ci].numeral) for s, ci in enumerate(path)]
