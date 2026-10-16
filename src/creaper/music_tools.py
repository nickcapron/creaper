"""MCP tools for music theory, the genre library and composition.

Theory tools (scales, chord naming, analysis, progressions, reharmonization,
voice leading, modulation, rhythms, genres) are pure calculation and don't touch
REAPER. Writing tools put parts into MIDI items; sketch_song builds a whole
arrangement for a genre in one call.
"""

from __future__ import annotations

import math
import random
import re
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from . import composer, feel, genres, harmony, scales as scales_db, theory
from .harmony import Key, SpelledChord
from .server import READ_ONLY, ItemId, add_drum_pattern, call, tool

ChordsArg = Annotated[list[str] | str, Field(description=(
    "Chord symbols (Am7, F#m7b5, C/E, Bbmaj9) or, with a key, Roman numerals (ii7, V7/V, bVII, viiø7, iv6, N6). "
    "A list, or one string like 'Am F C G' or 'i-VI-III-VII'. A 'mode:' prefix such as 'dorian: i7-IV7' "
    "reads the numerals in that mode on the key's tonic."))]
KeyArg = Annotated[str | None, Field(description="Key with any scale or mode: 'A minor', 'F# dorian', 'Bb', 'Eb mixolydian', 'C harmonic minor'")]
LengthsArg = Annotated[list[float] | None, Field(description="Length of each chord in QN (4 = a bar of 4/4); default: chord_length for all")]
Voicing = Literal["close", "open", "drop2", "drop3", "shell", "rootless", "quartal", "spread", "power", "cluster", "satb"]
Rhythm = Literal["sustain", "half_notes", "quarters", "eighths", "offbeat", "skank", "stabs", "charleston", "bossa",
                 "montuno", "strum", "arpeggio_up", "arpeggio_updown", "broken", "alberti", "pulse_16", "push",
                 "tresillo", "waltz", "gospel"]
BassStyle = Literal["whole", "root", "eighths", "sixteenths", "root_fifth", "octaves", "walking", "808", "syncopated",
                    "offbeat", "one_drop", "tumbao", "arpeggio", "pedal", "boogie", "motown", "alberti", "reese"]
Technique = Literal["sevenths", "extensions", "secondary_dominants", "ii_v", "tritone_subs", "modal_interchange",
                    "passing_diminished", "backdoor", "deceptive", "sus_dominants", "pedal", "relative_subs",
                    "chromatic_mediants", "negative_harmony", "picardy"]


class TimedChord(BaseModel):
    chord: str = Field(description="Chord symbol (Am7, Cmaj7/E) or, with a key, a Roman numeral (ii7, V7/V)")
    length: float = Field(4.0, gt=0, description="Length in QN (4 = a bar of 4/4)")
    start: float | None = Field(None, ge=0, description="Start in QN from the item start; default: after the previous chord")


TimedChordsArg = Annotated[list[TimedChord] | str, Field(description=(
    "Chords with lengths, or one string like 'Am7 D7 Gmaj7' / 'ii7-V7-Imaj7' (each lasting chord_length)."))]


# ------------------------------------------------------------------ helpers

def _key(key: str | None) -> Key | None:
    return harmony.parse_key(key) if key else None


_LETTER_NUMERAL = re.compile(r"^(?:(?:Fr|Ger)\+?6|Cad6/?4)$", re.IGNORECASE)


def _parse_list(chords: list[str] | str, key: Key | None) -> tuple[list[SpelledChord], list[str | None], Key | None]:
    text = chords if isinstance(chords, str) else None
    if text is not None and ":" in text:
        mode, _, text = text.partition(":")
        if key is None:
            raise ValueError("a 'mode:' prefix needs a key for its tonic")
        key = Key(key.tonic, key.letter, scales_db.find_scale(mode.strip()))
    tokens = harmony.split_numerals(text) if text is not None else [c.strip() for c in chords if c.strip()]
    if not tokens:
        raise ValueError("no chords given")
    out, nums = [], []
    for t in tokens:
        # Ger+6, Fr+6 and Cad64 are numerals that start like a chord letter.
        if t[0] in "ABCDEFG" and not _LETTER_NUMERAL.match(t):
            out.append(harmony.spelled_from_symbol(t, key))
            nums.append(None)
        else:
            if key is None:
                raise ValueError(f"'{t}' looks like a Roman numeral; give a key too (e.g. key='A minor')")
            out.append(harmony.parse_roman(t, key).chord)
            nums.append(t)
    return out, nums, key


def _detect_from_chords(chords: list[SpelledChord], lengths: list[float]) -> tuple[Key, list[dict]]:
    h, hint = harmony.histogram_from_chords(list(zip(chords, lengths)))
    spelling = {c.root: c.root_name for c in chords}
    found = harmony.detect_key(h, hint, spelling=spelling)
    if not found:
        raise ValueError("couldn't tell the key; give one")
    return harmony.parse_key(found[0]["key"]), found


def _events(chords: list[TimedChord] | str, key: Key | None, chord_length: float, start: float = 0.0
            ) -> tuple[list[composer.ChordEvent], Key]:
    if isinstance(chords, str):
        parsed, nums, key2 = _parse_list(chords, key)
        events = composer.timeline(parsed, chord_length, start, [n or "" for n in nums])
    else:
        parsed, nums, key2 = _parse_list([c.chord for c in chords], key)
        events, t = [], start
        for c, sc, num in zip(chords, parsed, nums):
            at = c.start if c.start is not None else t
            events.append(composer.ChordEvent(sc, at, c.length, num))
            t = at + c.length
    if key2 is None:
        key2, _ = _detect_from_chords([e.chord for e in events], [e.length for e in events])
    return events, key2


def _project_meter() -> str:
    try:
        return call("get_project_overview").get("time_signature") or "4/4"
    except Exception:  # noqa: BLE001 - fall back to 4/4 if REAPER is busy
        return "4/4"


FeelName = Literal["none", "tight", "natural", "laid back", "pushed", "expressive"]
FeelArg = Annotated[FeelName, Field(description=(
    "How the part is played: natural (default) adds a player's timing and dynamics for its role; tight for "
    "quantised electronic styles, laid back or pushed for the pocket, expressive for rubato styles; none for "
    "exactly on the grid. A genre's profile suggests one (performance_feel)"))]


def _perform(notes: list[dict], role: str, feel_name: str, seed: int | None = None, amount: float = 1.0) -> list[dict]:
    """The notes played with a feel at the project's tempo and meter ('none' leaves them)."""
    if feel_name == "none" or not notes:
        return notes
    try:
        overview = call("get_project_overview")
    except Exception:  # noqa: BLE001 - a busy REAPER: play at a typical tempo
        overview = {}
    bpm = float(overview.get("tempo_bpm") or 120)
    return feel.apply(notes, role, feel_name, bpm=bpm, meter=overview.get("time_signature") or "4/4", seed=seed,
                      amount=amount)


def feel_mod_for(g) -> str:
    """The performance feel a genre's profile suggests (tight, laid back, expressive...)."""
    return feel.feel_for_genre(g.feel, g.family, g.swing, g.name)


def _note_names(pitches: list[int]) -> list[str]:
    return [theory.midi_to_note(p) for p in pitches]


def _interval_names(scale: scales_db.Scale) -> list[str]:
    major = (0, 2, 4, 5, 7, 9, 11)
    if len(scale.intervals) == 7:
        return [harmony.accidental_text(iv - major[i]) + str(i + 1) for i, iv in enumerate(scale.intervals)]
    table = ("1", "b2", "2", "b3", "3", "4", "#4", "5", "b6", "6", "b7", "7")
    return [table[i] for i in scale.intervals]


def _chord_entry(rc: harmony.RomanChord) -> dict:
    d = rc.describe()
    return d


def _match_named(chords: list[SpelledChord], key: Key) -> list[dict]:
    """Famous progressions the chords contain (same roots and chord types, any rotation)."""

    def sig(c: SpelledChord) -> tuple[int, str]:
        s = {i % 12 for i in c.intervals}
        kind = "dim" if {3, 6} <= s and 7 not in s else ("min" if 3 in s and 4 not in s else "maj")
        return ((c.root - key.tonic) % 12, kind)

    seq = [sig(c) for c in chords]
    found = []
    for p in composer.PROGRESSIONS:
        try:
            pk = Key(key.tonic, key.letter, scales_db.find_scale(p.mode))
            pseq = [sig(rc.chord) for rc in composer.realize(p.numerals, pk)]
        except ValueError:
            continue
        if len(pseq) > len(seq) or len(pseq) < 2:
            continue
        doubled = seq + seq
        if any(doubled[i:i + len(pseq)] == pseq for i in range(len(seq))):
            found.append({"name": p.name, "numerals": p.numerals, "about": p.about})
    return found[:4]


def _write(item_id: str, notes: list[dict], replace: bool) -> dict:
    if not notes:
        raise ValueError("nothing to write")
    return call("add_midi_notes", item_id=item_id, notes=notes, replace=replace)


# ------------------------------------------------------------ theory tools

@tool(annotations=READ_ONLY)
def get_scale(key: Annotated[str, Field(description="e.g. 'D dorian', 'F# major', 'A harmonic minor', 'E phrygian dominant'")]) -> dict:
    """Explains one key or mode: its notes spelled correctly, intervals, sound and
    uses, the chords on each degree (triads and 7ths with Roman numerals and
    functions), and the modes that share its notes. Use it to know which notes and
    chords fit before writing; list_scales browses all the scales by family and
    sound. Read-only."""
    k = harmony.parse_key(key)
    out: dict = {"key": k.name, "notes": k.spell_scale(), "intervals": _interval_names(k.scale),
                 "family": k.scale.family, "sound": k.scale.sound}
    if k.scale.aliases:
        out["also_called"] = list(k.scale.aliases)
    if k.heptatonic:
        out["triads"] = [_chord_entry(harmony.numeral_for(c, k)) for c in harmony.diatonic_chords(k)]
        out["sevenths"] = [{"numeral": harmony.numeral_for(c, k).numeral, "chord": c.symbol}
                           for c in harmony.diatonic_chords(k, sevenths=True)]
        pcs = k.pitch_classes()
        relatives = []
        for s in scales_db.SCALE_LIST:
            if len(s.intervals) != 7:
                continue
            for i, name in enumerate(k.spell_scale()):
                t = harmony.name_pc(name)[0]
                if {(t + x) % 12 for x in s.intervals} == pcs and not (t == k.tonic and s.name == k.scale.name):
                    relatives.append(f"{name} {s.name}")
        out["same_notes_as"] = relatives
    else:
        out["note"] = "Not a seven-note scale: chords are built from the parallel major/minor."
    out["parallel_modes_bright_to_dark"] = [f"{k.tonic_name} {m}" for m in
                                            ("lydian", "major", "mixolydian", "dorian", "minor", "phrygian", "locrian")]
    return out


@tool(annotations=READ_ONLY)
def list_scales(family: Annotated[str | None, Field(description="diatonic mode, melodic minor mode, harmonic minor mode, heptatonic, pentatonic, hexatonic, symmetric, bebop, octatonic")] = None) -> dict:
    """Lists the scales and modes creaper knows (all of them, or one family), each
    with its intervals, what it sounds like and its other names: for choosing a scale
    by mood or finding a name creaper accepts. To spell one scale in a given key, use
    get_scale. Read-only."""
    items = [s for s in scales_db.SCALE_LIST if not family or family.lower() in s.family]
    return {"count": len(items), "scales": [{"name": s.name, "family": s.family, "intervals": _interval_names(s),
                                             "sound": s.sound, **({"also": list(s.aliases)} if s.aliases else {})}
                                            for s in items]}


@tool(annotations=READ_ONLY)
def identify_chord(
    notes: Annotated[list[str | int], Field(description="Notes, e.g. ['A2','C4','E4','G4'] or MIDI numbers; the lowest is the bass")],
    key: KeyArg = None,
) -> dict:
    """Names the chord some notes make (with inversion or slash bass), most likely first,
    and, with a key, its Roman numeral and function."""
    pitches = [theory.note_to_midi(n) for n in notes]
    k = _key(key)
    found = harmony.identify_chord(pitches, key=k)
    if not found:
        raise ValueError("no chord found in those notes")
    if k is not None:
        for f in found:
            rc = harmony.numeral_for(harmony.spelled_from_symbol(f["symbol"], k), k)
            f["numeral"], f["function"] = rc.numeral, rc.function
            if rc.labels:
                f["labels"] = list(rc.labels)
    return {"notes": _note_names(pitches), "chords": found}


@tool(annotations=READ_ONLY)
def analyze_progression(
    chords: ChordsArg,
    key: KeyArg = None,
    lengths: LengthsArg = None,
) -> dict:
    """Roman-numeral analysis of a progression: the key (detected if not given), each
    chord's numeral, function and spelling, secondary dominants, borrowed chords,
    tritone subs, Neapolitan and augmented sixths, cadences, and famous progressions it matches."""
    k = _key(key)
    parsed, nums, k = _parse_list(chords, k)
    lens = lengths or [4.0] * len(parsed)
    detected = None
    if k is None:
        k, detected = _detect_from_chords(parsed, lens)
    rcs = []
    for c, given in zip(parsed, nums):
        rc = harmony.numeral_for(c, k)
        if given:
            rc = harmony.RomanChord(given, c, k, rc.function, rc.labels)
        rcs.append(rc)
    out: dict = {"key": k.name, "scale": k.spell_scale(), "chords": [_chord_entry(rc) for rc in rcs],
                 "cadences": harmony.cadences(rcs)}
    if detected:
        out["key_candidates"] = detected
    named = _match_named(parsed, k)
    if named:
        out["known_progressions"] = named
    outside = [rc.chord.symbol for rc in rcs if rc.labels]
    if outside:
        out["chromatic_chords"] = outside
    return out


@tool(annotations=READ_ONLY)
def suggest_progressions(
    key: Annotated[str, Field(description="e.g. 'A minor', 'Eb major', 'D dorian'")],
    genre: Annotated[str | None, Field(description="A genre from list_genres; its typical progressions come first")] = None,
    mood: Annotated[str | None, Field(description="e.g. uplifting, sad, dark, epic, dreamy, jazzy, nostalgic, menacing, romantic")] = None,
    length: Annotated[int, Field(ge=2, le=16, description="Chords in newly generated progressions")] = 4,
    count: Annotated[int, Field(ge=1, le=20, description="How many progressions to suggest")] = 8,
    sevenths: Annotated[bool, Field(description="Use seventh chords in generated progressions")] = False,
    seed: Annotated[int | None, Field(description="Varies the generated progressions; same seed, same suggestions")] = None,
) -> dict:
    """Suggests chord progressions for a key: the genre's own idioms, famous named
    progressions that fit the mood, and fresh ones generated from functional
    harmony. Each comes with numerals, chord symbols in the key and what makes it
    work. Use it to choose chords before writing parts with add_chord_progression;
    to rework chords you already have, use reharmonize. Read-only; writes nothing."""
    k = harmony.parse_key(key)
    out: list[dict] = []
    seen: set[str] = set()

    def add(name: str, numerals: str, mode: str | None, about: str, source: str) -> None:
        try:
            body = numerals if ":" in numerals or not mode else f"{mode}: {numerals}"
            rcs = composer.realize(body, k)
        except ValueError:
            return
        symbols = " ".join(rc.chord.symbol for rc in rcs)
        if symbols in seen:
            return
        seen.add(symbols)
        out.append({"name": name, "numerals": numerals, "chords": symbols, "about": about, "source": source})

    g = genres.find(genre) if genre else None
    if g:
        for p in g.progressions:
            mode = None if ":" in p else g.modes[0]
            add(f"{g.name} idiom", p, mode, g.harmony[:160], "genre")
    family_minor = k.is_minor
    for p in composer.find_progressions(mood=mood, style=g.name if g else None) or composer.find_progressions(mood=mood):
        p_minor = scales_db.find_scale(p.mode).intervals[2] == 3
        if p_minor == family_minor or mood:
            add(p.name, p.numerals, p.mode, p.about, "library")
    rng = random.Random(seed)
    tries = 0
    while len(out) < count and tries < 40:
        tries += 1
        seq = composer.generate_progression(k, length, seed=rng.randint(0, 10**6), sevenths=sevenths)
        add("generated (functional harmony)", "-".join(seq), None, "Built from tonic/predominant/dominant motion.", "generated")
    if sevenths:
        for entry in out:
            pass
    return {"key": k.name, "progressions": out[:count]}


@tool(annotations=READ_ONLY)
def reharmonize(
    chords: ChordsArg,
    key: KeyArg = None,
    techniques: Annotated[list[Technique], Field(description=(
        "Applied in order. sevenths, extensions (9/11/13), secondary_dominants, ii_v, tritone_subs, "
        "modal_interchange (borrowed iv, bVI, iiø7), passing_diminished, backdoor (iv7-bVII7-I), deceptive, "
        "sus_dominants, pedal, relative_subs, chromatic_mediants, negative_harmony, picardy. "
        "Jazz: ['sevenths','ii_v','tritone_subs','extensions']. Soul: ['sevenths','modal_interchange','backdoor'].")),
    ] = ("sevenths", "secondary_dominants"),
    lengths: LengthsArg = None,
    amount: Annotated[float, Field(ge=0, le=1, description="How often optional changes are made")] = 0.7,
    seed: Annotated[int | None, Field(description="Varies which optional changes are made; same seed, same result")] = None,
) -> dict:
    """Reharmonizes an existing progression with jazz, soul, classical and film
    techniques (tritone subs, secondary dominants, borrowed chords...), keeping its
    length, and explains each change. Works on chord symbols, not on the project:
    write the result with add_chord_progression. For new progressions from scratch,
    use suggest_progressions. Read-only."""
    k = _key(key)
    parsed, _, k = _parse_list(chords, k)
    lens = lengths or [4.0] * len(parsed)
    if k is None:
        k, _ = _detect_from_chords(parsed, lens)
    events = composer.timeline(parsed, lens)
    new, notes = composer.reharmonize(events, k, list(techniques), seed=seed, amount=amount)
    return {
        "key": k.name,
        "before": [c.symbol for c in parsed],
        "after": [{"chord": e.chord.symbol, "length": round(e.length, 3), "numeral": harmony.numeral_for(e.chord, k).numeral}
                  for e in new],
        "changes": notes,
        "tip": "Write it with add_chord_progression (pass these chords and lengths).",
    }


@tool(annotations=READ_ONLY)
def check_voice_leading(
    chords: Annotated[list[str] | str | None, Field(description="Chords to voice in four parts (SATB) by the rules")] = None,
    voicings: Annotated[list[list[str | int]] | None, Field(description="Or your own voicings to check, each low to high, e.g. [['C3','G3','E4','C5'], ...]")] = None,
    key: KeyArg = None,
) -> dict:
    """Common-practice voice leading. Given chords, writes a four-part SATB realization
    that avoids parallel fifths/octaves, hidden octaves, crossings, bad spacing and
    unresolved leading tones/sevenths. Given voicings, lists every rule they break."""
    k = _key(key)
    parsed = None
    if chords:
        parsed, _, k = _parse_list(chords, k)
        if k is None:
            k, _ = _detect_from_chords(parsed, [4.0] * len(parsed))
    if voicings:
        # In the order given (bass, tenor, alto, soprano): sorting them reassigned the
        # voices, so crossed voices could never be reported.
        pitches = [[theory.note_to_midi(n) for n in v] for v in voicings]
        issues = composer.check_voice_leading(pitches, k, parsed if parsed and len(parsed) == len(pitches) else None)
        return {"issues": issues, "verdict": "clean" if not issues else f"{len(issues)} issue(s)"}
    if not parsed:
        raise ValueError("give chords to voice or voicings to check")
    v = composer.satb(parsed, k)
    issues = composer.check_voice_leading(v, k, parsed)
    return {"key": k.name, "voicings": [{"chord": c.symbol, "bass": _note_names([x[0]])[0], "tenor": _note_names([x[1]])[0],
                                         "alto": _note_names([x[2]])[0], "soprano": _note_names([x[3]])[0]}
                                        for c, x in zip(parsed, v)],
            "remaining_issues": issues,
            "tip": "Write it with add_chord_progression(voicing='satb')."}


@tool(annotations=READ_ONLY)
def find_modulation(
    from_key: Annotated[str, Field(description="e.g. 'C major'")],
    to_key: Annotated[str, Field(description="e.g. 'E major', 'A minor'")],
) -> dict:
    """How to change key: how close the keys are, pivot chords they share, and chord
    routes from smoothest to most dramatic (pivot, ii-V, common tone, chromatic
    mediant, truck-driver, diminished pivot)."""
    a, b = harmony.parse_key(from_key), harmony.parse_key(to_key)
    return {"from": a.name, "to": b.name, **harmony.key_distance(a, b),
            "pivot_chords": harmony.pivot_chords(a, b), "routes": harmony.modulation_routes(a, b)}


@tool(annotations=READ_ONLY)
def get_rhythm(
    name: Annotated[str | None, Field(description="son clave 3-2, rumba clave 2-3, bossa clave, tresillo, cinquillo, habanera, dembow (snare), bembe bell (12/8), shiko, one drop, shuffle, aksak 7/8 (2+2+3), maqsum... or 'list'")] = None,
    euclid_hits: Annotated[int | None, Field(ge=1, le=64, description="Euclidean rhythm: hits spread evenly...")] = None,
    euclid_steps: Annotated[int | None, Field(ge=1, le=64, description="...over this many steps")] = None,
    rotate: int = 0,
    polyrhythm: Annotated[list[int] | None, Field(description="e.g. [3, 2] for 3 against 2, [4, 3], [5, 4]")] = None,
) -> dict:
    """Rhythm patterns as step strings ready for add_drum_pattern (x = hit, . = rest):
    named timelines (clave, tresillo, bell patterns), Euclidean rhythms and polyrhythms."""
    if euclid_hits is not None and euclid_steps is not None:
        return {"pattern": composer.euclidean(euclid_hits, euclid_steps, rotate),
                "about": f"{euclid_hits} hits spread over {euclid_steps} steps (E({euclid_hits},{euclid_steps}))"}
    if polyrhythm:
        if len(polyrhythm) != 2:
            raise ValueError("polyrhythm takes two numbers, e.g. [3, 2]")
        lanes = composer.polyrhythm(*polyrhythm)
        return {"lanes": lanes, "tip": "Use each lane for a different drum; set step so the cycle spans a bar or a beat."}
    if not name or name == "list":
        return {"rhythms": {k: v["about"] for k, v in composer.RHYTHMS.items()}}
    key = name.strip().lower()
    match = composer.RHYTHMS.get(key) or next((v for k, v in composer.RHYTHMS.items() if key in k), None)
    if not match:
        raise ValueError(f"unknown rhythm '{name}'. Known: {', '.join(composer.RHYTHMS)}")
    return {"pattern": match["steps"], "step": match["step"], "about": match["about"]}


# ------------------------------------------------------------- genre library

@tool(annotations=READ_ONLY)
def list_genres(
    family: Annotated[str | None, Field(description="e.g. electronic dance, hip-hop, jazz, latin, metal and punk, classical, film and games")] = None,
    search: Annotated[str | None, Field(description="Words to look for: an artist, instrument, mood or era")] = None,
    tempo: Annotated[float | None, Field(description="Genres that fit this BPM (or half/double)")] = None,
    mode: Annotated[str | None, Field(description="Genres that use this mode, e.g. dorian, phrygian")] = None,
) -> dict:
    """Browses and searches the library of genre profiles (by family, artist,
    instrument, mood, tempo or mode) and returns the matching genres with their
    family and tempo range. Every profile covers composition (modes, progressions,
    voicings, bass, melody), rhythm (groove, swing, feel), arrangement (form,
    instruments, sound design) and mixing (loudness, tone, width); get_genre_profile
    shows one in full. Read-only."""
    found = genres.search(search, family, tempo, mode)
    families: dict[str, int] = {}
    for g in genres.GENRES:
        families[g.family] = families.get(g.family, 0) + 1
    return {"count": len(found), "total": len(genres.GENRES), "families": families,
            "genres": [{"genre": g.name, "family": g.family, "tempo": list(g.tempo),
                        **({"also": list(g.aliases)} if g.aliases else {})} for g in found[:300]]}


@tool(annotations=READ_ONLY)
def get_genre_profile(
    genre: str,
    key: Annotated[str | None, Field(description="Show the progressions in this key (default: the genre's favourite)")] = None,
) -> dict:
    """Everything creaper knows about a genre: history and touchstones, tempo, feel and
    swing, modes and favourite keys, progressions (spelled in a key), harmony habits,
    voicing and comping, bass, melody, drum groove (ready for add_genre_groove), form,
    instruments, sound design, production, mix targets and theory notes."""
    g = genres.find(genre)
    k = harmony.parse_key(key) if key else (harmony.parse_key(g.keys[0]) if g.keys else
                                            harmony.parse_key(f"{'A' if 'minor' in g.modes[0] or g.modes[0] in ('dorian', 'phrygian') else 'C'} {g.modes[0]}"))
    progressions = []
    for p in g.progressions:
        body = p if ":" in p else f"{g.modes[0]}: {p}"
        try:
            progressions.append({"numerals": p, "in_key": " ".join(rc.chord.symbol for rc in composer.realize(body, k))})
        except ValueError:
            progressions.append({"numerals": p})
    m = g.mix
    form_bars = sum(b for _, b in g.form)
    num, den = (int(x) for x in g.meter.split("/"))
    seconds = form_bars * num * 4 / den * 60 / (sum(g.tempo) / 2)
    return {
        "genre": g.name, "family": g.family, "also": list(g.aliases), "parent": g.parent,
        "description": g.description, "era": g.era, "touchstones": list(g.touchstones),
        "tempo_bpm": list(g.tempo), "meter": g.meter, "feel": g.feel, "swing": g.swing,
        "performance_feel": feel_mod_for(g),
        "modes": list(g.modes), "favourite_keys": list(g.keys),
        "progressions": progressions, "shown_in": k.name if not key else key, "chords_per_bar": g.harmonic_rhythm,
        "harmony": g.harmony, "voicing": g.voicing, "comping": g.comping,
        "bass": {"style": g.bass_style, "how": g.bass},
        "melody": {"density": g.melody_density, "scale": g.melody_scale, "how": g.melody},
        "drums": {"groove": g.groove, "how": g.drums},
        "form": [{"section": s, "bars": b} for s, b in g.form],
        "length": {"bars": form_bars, "minutes": f"{int(seconds // 60)}:{int(seconds % 60):02d}",
                   "note": "a full track in this style; write all of it unless the user asks for a sketch or loop"},
        "instruments": list(g.instruments), "sound_design": g.sound_design, "production": g.production,
        "theory": g.theory,
        "mix": {"integrated_lufs": list(m.lufs), "loudness_range_lu": list(m.lra), "true_peak_dbtp": m.true_peak,
                "low_end": m.low_end, "tone": m.tone, "stereo_width": m.width},
        "caveat": "rules of thumb from the records that define the style, not laws",
    }


# ------------------------------------------------------------- writing tools

@tool()
def add_chord_progression(
    item_id: ItemId,
    chords: TimedChordsArg,
    key: KeyArg = None,
    voicing: Annotated[Voicing, Field(description=(
        "close (triads/7ths, smooth inversions), open/drop2/drop3 (spread jazz/pop voicings), shell (root-3-7), "
        "rootless (Bill Evans A/B forms), quartal (stacked 4ths), spread (piano/orchestral), power (1-5-8), "
        "cluster (with added 9ths), satb (four-part chorale by the voice-leading rules)"))] = "close",
    rhythm: Annotated[Rhythm, Field(description="How the chords are played: sustain, stabs, offbeat, skank, strum, bossa, montuno, charleston, arpeggio_up, alberti, pulse_16...")] = "sustain",
    chord_length: Annotated[float, Field(gt=0, description="QN per chord when chords is a string")] = 4.0,
    octave: Annotated[int, Field(ge=1, le=7, description="Register; 4 is around middle C")] = 4,
    bass_octave: Annotated[int | None, Field(ge=0, le=6, description="Also add the root (or slash bass) in this octave, e.g. 2")] = None,
    arp_rate: Annotated[float, Field(gt=0, le=4, description="Note length for arpeggio patterns in QN (0.25 = 16ths)")] = 0.5,
    velocity: Annotated[int, Field(ge=1, le=127, description="Note velocity, 1-127")] = 80,
    start: Annotated[float, Field(ge=0, description="Where the first chord starts, in QN from the item start")] = 0.0,
    replace: Annotated[bool, Field(description="Delete the item's existing notes first")] = False,
    seed: Annotated[int | None, Field(description="Seeds the small random velocity variations; same seed, same part")] = None,
    feel: FeelArg = "natural",
) -> dict:
    """Writes a chord part (pads, piano or guitar comping, stabs, arpeggios) into a
    MIDI item from chord symbols or Roman numerals with a key, in the voicing and
    comping rhythm you choose, with smooth voice leading between chords. Use it for
    harmony parts; write_bassline and write_melody write the bass and lead over the
    same chords, and add_midi_notes takes exact notes you've written yourself.
    suggest_progressions or a genre profile can supply the chords. Returns each
    chord's Roman numeral and the notes chosen. It's played with a feel (chords
    rolled slightly low to high, the top voice singing, accents on the beat; held
    pads stay smooth) unless feel is 'none'."""
    k = _key(key)
    events, k = _events(chords, k, chord_length, start)
    voicings = composer.voice_chords([e.chord for e in events], voicing, octave, key=k)
    meter = _project_meter() if rhythm not in ("sustain",) else "4/4"
    notes = composer.comp(events, voicings, rhythm, meter=meter, velocity=velocity, rate=arp_rate, seed=seed)
    if bass_octave is not None:
        for e in events:
            notes.append({"pitch": theory.bass_note(e.chord.to_chord(), bass_octave), "start": e.start,
                          "length": e.length * 0.98, "velocity": velocity, "channel": 1})
    role = "pad" if rhythm == "sustain" else "arp" if rhythm.startswith(("arpeggio", "alberti", "pulse")) else "chords"
    notes = _perform(notes, role, feel, seed)
    result = _write(item_id, notes, replace)
    result["key"] = k.name
    result["chords"] = [{"chord": e.chord.symbol, "numeral": e.numeral or harmony.numeral_for(e.chord, k).numeral,
                         "start": e.start, "notes": _note_names(v)} for e, v in zip(events, voicings)]
    return result


@tool()
def write_bassline(
    item_id: ItemId,
    chords: TimedChordsArg,
    style: Annotated[BassStyle, Field(description=(
        "whole/reese (held), root (one per bar), eighths, sixteenths, root_fifth (country 2-feel), octaves (disco), "
        "walking (jazz quarters with chromatic approaches), 808 (trap), syncopated (funk/house), offbeat (trance/house), "
        "one_drop (reggae), tumbao (salsa, anticipated), arpeggio, pedal (tonic pedal), boogie, motown, alberti"))] = "root",
    key: KeyArg = None,
    chord_length: Annotated[float, Field(gt=0, description="QN per chord when chords is a string")] = 4.0,
    octave: Annotated[int, Field(ge=0, le=4, description="2 puts the bass around C2")] = 2,
    velocity: Annotated[int, Field(ge=1, le=127, description="Note velocity, 1-127")] = 100,
    start: Annotated[float, Field(ge=0, description="Where the bassline starts, in QN from the item start")] = 0.0,
    replace: Annotated[bool, Field(description="Delete the item's existing notes first")] = False,
    seed: Annotated[int | None, Field(description="Varies the line in styles with choices (walking, syncopated...); same seed, same line")] = None,
    feel: FeelArg = "natural",
) -> dict:
    """Composes a bassline into a MIDI item that follows a chord progression in a
    chosen style (walking, 808, one-drop, octaves, tumbao...), in the project's meter.
    Use it to have creaper write the bass from chords; add_midi_notes takes a bass
    line you've written note by note. It's played with a feel (in the pocket, leaning
    on the downbeats) unless feel is 'none'. Returns the key, the style and the first
    notes."""
    k = _key(key)
    events, k = _events(chords, k, chord_length, start)
    notes = composer.bassline(events, style, k, octave, meter=_project_meter(), velocity=velocity, seed=seed)
    notes = _perform(notes, "bass", feel, seed)
    result = _write(item_id, notes, replace)
    result.update({"key": k.name, "style": style, "first_bar": _note_names([n["pitch"] for n in notes[:8]])})
    return result


@tool()
def write_melody(
    item_id: ItemId,
    chords: TimedChordsArg,
    key: KeyArg = None,
    density: Annotated[Literal["sparse", "medium", "busy"], Field(description="How many notes per bar")] = "medium",
    low: Annotated[str | int, Field(description="Lowest note, e.g. C4 (vocal-like), A3")] = "C4",
    high: Annotated[str | int, Field(description="Highest note, e.g. G5")] = "G5",
    scale: Annotated[str | None, Field(description="Scale the melody uses, e.g. 'minor pentatonic', 'blues'; default: the key's")] = None,
    phrase_bars: Annotated[int, Field(ge=1, le=16, description="Phrase length: the motif repeats and the phrase closes every this many bars")] = 4,
    syncopation: Annotated[float, Field(ge=0, le=1, description="How often notes land off the beat, 0-1")] = 0.3,
    chord_length: Annotated[float, Field(gt=0, description="QN per chord when chords is a string")] = 4.0,
    velocity: Annotated[int, Field(ge=1, le=127, description="Note velocity, 1-127")] = 92,
    start: Annotated[float, Field(ge=0, description="Where the melody starts, in QN from the item start")] = 0.0,
    replace: Annotated[bool, Field(description="Delete the item's existing notes first")] = False,
    seed: Annotated[int | None, Field(description="Same seed, same melody; change it for another idea")] = None,
    feel: FeelArg = "natural",
) -> dict:
    """Composes a melody into a MIDI item over a chord progression: a rhythmic motif
    developed in phrases, chord tones on strong beats, stepwise lines with leaps
    recovered, a high point, a half-close at the end of the first phrase and the
    tonic at the end. Use it to have creaper invent a lead or topline; add_midi_notes
    writes a melody you've worked out note by note, and place_motif reuses a saved
    theme. Try several seeds. It's played with a feel (phrases louder toward their
    peak, strong beats leaning) unless feel is 'none'. Returns the notes and the
    non-chord tones used."""
    k = _key(key)
    events, k = _events(chords, k, chord_length, start)
    notes = composer.melody(events, k, density, theory.note_to_midi(low), theory.note_to_midi(high), scale,
                            _project_meter(), phrase_bars, seed, syncopation, velocity)
    played = _perform(notes, "lead", feel, seed)
    result = _write(item_id, played, replace)
    result.update({"key": k.name, "notes_written": len(notes), "melody": _note_names([n["pitch"] for n in notes][:32]),
                   "nonchord_tones": composer.nonchord_tones(notes, events)[:12]})
    return result


@tool()
def apply_feel(
    item_id: ItemId,
    role: Annotated[Literal["drums", "bass", "chords", "pad", "lead", "arp"], Field(description=(
        "What the part does: drums, bass, chords (comping/stabs: rolled, top voice sings), pad (held, kept "
        "smooth), lead (melody or vocal line: phrased), arp (sequenced: steady)"))],
    feel: FeelArg = "natural",
    amount: Annotated[float, Field(ge=0, le=2, description="How much: 1 = the feel as defined, 0.5 = subtle, 2 = exaggerated")] = 1.0,
    seed: Annotated[int | None, Field(description="Same seed, same performance")] = None,
) -> dict:
    """Plays an existing MIDI part like a musician would for its role: small timing
    offsets (a laid-back snare, a bass in the pocket, chords rolled low to high) and
    dynamics (beat accents, softer offbeats, phrases louder toward their peak). Use it
    on parts written note by note with add_midi_notes or a pasted MIDI file, which
    otherwise play dead on the grid; the composing tools already apply a feel. It adds
    to whatever feel the part has, so apply it once (undo takes it off). Pitches and
    the number of notes never change. Returns how much the timing and dynamics moved."""
    data = call("get_midi_notes", item_id=item_id, limit=20000)
    if data.get("truncated"):
        raise ValueError("that item has more than 20,000 notes; split it first")
    notes = data.get("notes", [])
    if not notes:
        raise ValueError("that item has no notes")
    if feel == "none":
        return {"item_id": item_id, "changed": 0, "note": "feel 'none' changes nothing"}
    played = _perform(notes, role, feel, seed, amount)
    result = _write(item_id, played, True)
    moved = [abs(a["start"] - b["start"]) for a, b in zip(notes, played)]
    bpm = float(call("get_project_overview").get("tempo_bpm") or 120)
    vel = [n["velocity"] for n in played]
    result.update({"role": role, "feel": feel, "notes": len(played),
                   "timing_moved_ms": {"average": round(sum(moved) / len(moved) * 60000 / bpm, 1),
                                       "most": round(max(moved) * 60000 / bpm, 1)},
                   "velocity_range": [min(vel), max(vel)]})
    return result


@tool()
def add_genre_groove(
    item_id: ItemId,
    genre: Annotated[str, Field(description="A genre from list_genres, e.g. 'house', 'boom bap', 'bossa nova'")],
    repeats: Annotated[int, Field(ge=1, le=256, description="Times to play the groove (it's 1, 2 or 4 bars)")] = 4,
    humanize: Annotated[float, Field(ge=0, le=1, description="Random velocity variation, 0-1")] = 0.15,
    start: Annotated[float, Field(ge=0, description="Start in QN from the item start")] = 0.0,
    replace: Annotated[bool, Field(description="Delete the item's existing notes first")] = False,
    feel: Annotated[FeelName | None, Field(description="How it's played; default: the genre's own feel (performance_feel)")] = None,
) -> dict:
    """Programs a genre's stock drum groove (from its genre profile, with the genre's
    swing) on the track's drum instrument in one call: a quick, idiomatic starting
    beat. For your own pattern, fills and variations use add_drum_pattern, which this
    calls. Returns the lanes and notes used, and how drums work in that genre."""
    g = genres.find(genre)
    groove = g.groove
    played_as = feel or feel_mod_for(g)
    result = add_drum_pattern(item_id=item_id, pattern=dict(groove["pattern"]), step=groove.get("step", 0.25),
                              repeats=repeats, swing=groove.get("swing", g.swing), humanize=humanize, start=start,
                              replace=replace, feel=played_as)
    result["genre"] = g.name
    result["feel"] = played_as
    result["how_the_drums_work"] = g.drums
    return result


@tool(annotations=READ_ONLY)
def analyze_harmony(
    item_id: ItemId,
    key: KeyArg = None,
    melody_item_id: Annotated[str | None, Field(description="Also analyze this melody against the chords: non-chord tones")] = None,
    resolution: Literal["auto", "bar", "half", "beat"] = "auto",
) -> dict:
    """Reads a MIDI item and explains its harmony: the key (detected), chords over time,
    Roman numerals and functions, cadences, notes outside the key, and (with a melody
    item) passing tones, suspensions, appoggiaturas and other non-chord tones."""
    raw = call("get_midi_notes", item_id=item_id, limit=20000)
    notes = raw["notes"]
    if not notes:
        raise ValueError("that item has no notes")
    meter = _project_meter()
    h = harmony.histogram_from_notes(notes)
    lowest = min(notes, key=lambda n: (n["start"], n["pitch"]))["pitch"] % 12
    candidates = harmony.detect_key(h, lowest)
    k = _key(key) or harmony.parse_key(candidates[0]["key"])
    segs = composer.chords_from_notes(notes, meter, resolution, k)
    rcs = []
    for s in segs:
        sc = harmony.spelled_from_symbol(s["chord"], k)
        rc = harmony.numeral_for(sc, k)
        s["numeral"], s["function"] = rc.numeral, rc.function
        if rc.labels:
            s["labels"] = list(rc.labels)
        rcs.append(rc)
    out: dict = {"key": k.name, "key_candidates": candidates, "chords": segs, "cadences": harmony.cadences(rcs)}
    named = _match_named([rc.chord for rc in rcs], k)
    if named:
        out["known_progressions"] = named
    if melody_item_id:
        mel = call("get_midi_notes", item_id=melody_item_id, limit=20000)["notes"]
        events = [composer.ChordEvent(rc.chord, s["start"], s["length"]) for rc, s in zip(rcs, segs)]
        out["melody_nonchord_tones"] = composer.nonchord_tones(mel, events)[:60]
    return out


@tool()
def harmonize_melody(
    item_id: Annotated[str, Field(description="The MIDI item with the melody")],
    key: KeyArg = None,
    chords_per_bar: Annotated[float, Field(description="Harmonic rhythm: 0.5, 1, 2 or 4")] = 1,
    palette: Annotated[Literal["diatonic", "colorful"], Field(description="colorful adds secondary dominants and borrowed chords")] = "diatonic",
    sevenths: bool = False,
    write_to_item_id: Annotated[str | None, Field(description="Write the chords into this item (e.g. on a piano track)")] = None,
    voicing: Voicing = "close",
    rhythm: Rhythm = "sustain",
    octave: Annotated[int, Field(ge=1, le=6)] = 3,
) -> dict:
    """Finds chords for an existing melody (strong-beat melody notes become chord tones,
    chords move tonic-predominant-dominant, the end cadences home), and optionally writes them."""
    notes = call("get_midi_notes", item_id=item_id, limit=20000)["notes"]
    if not notes:
        raise ValueError("that item has no notes")
    meter = _project_meter()
    k = _key(key)
    if k is None:
        found = harmony.detect_key(harmony.histogram_from_notes(notes), notes[-1]["pitch"] % 12)
        k = harmony.parse_key(found[0]["key"])
    events = composer.harmonize(notes, k, chords_per_bar, meter, palette, sevenths)
    out: dict = {"key": k.name, "chords": [{"chord": e.chord.symbol, "numeral": e.numeral, "start": e.start,
                                            "length": e.length} for e in events]}
    if write_to_item_id:
        voicings = composer.voice_chords([e.chord for e in events], voicing, octave, key=k)
        written = _write(write_to_item_id, composer.comp(events, voicings, rhythm, meter=meter), False)
        out["written"] = written
    return out


@tool()
def sketch_song(
    genre: Annotated[str, Field(description="Any genre from list_genres")],
    key: KeyArg = None,
    bars: Annotated[int, Field(ge=1, le=256, description="Length of the sketch in bars (the loop repeats)")] = 8,
    tempo: Annotated[float | None, Field(gt=20, le=400, description="BPM; default: the genre's typical tempo if the project is empty, else the project's")] = None,
    progression: Annotated[str | None, Field(description="Chords or numerals to use instead of the genre's favourite")] = None,
    parts: Annotated[list[Literal["drums", "bass", "chords", "melody"]] | None, Field(description="Default: all four")] = None,
    instruments: Annotated[dict[str, str] | None, Field(description=(
        "Plugin per part from list_installed_fx, e.g. {'drums': 'SILA', 'bass': 'Mini V', 'chords': 'Analog Lab V', "
        "'melody': 'Pigments'}; parts without one get an empty track"))] = None,
    start_bar: Annotated[int, Field(ge=1)] = 1,
    seed: Annotated[int | None, Field(description="Change for a different melody and variations")] = None,
) -> dict:
    """Builds a genre sketch in one call: tempo, then tracks with a drum groove,
    bassline, voiced and comped chords and a melody, all following the genre's
    profile (progression, harmonic rhythm, voicing, comping, bass style, melody
    density and scale, swing). Every part is ordinary MIDI to edit afterwards. It's
    one loop repeated: a starting point for a song, not the arrangement."""
    g = genres.find(genre)
    played_as = feel_mod_for(g)
    k = _key(key) or (harmony.parse_key(g.keys[0]) if g.keys else harmony.parse_key(f"A {g.modes[0]}"))
    overview = call("get_project_overview")
    num, den = (int(x) for x in g.meter.split("/"))
    tempo_set = None
    if tempo is not None or not overview.get("tracks"):
        tempo_set = call("set_tempo", bpm=tempo or g.tempo_default, numerator=num, denominator=den)
        meter = g.meter
    else:
        meter = overview.get("time_signature") or "4/4"
    bar = composer._bar_len(meter)
    rng = random.Random(seed)
    if progression:
        parsed, nums, _ = _parse_list(progression, k)
        chords = parsed
    else:
        p = g.progressions[rng.randrange(len(g.progressions))] if seed is not None else g.progressions[0]
        body = p if ":" in p else f"{g.modes[0]}: {p}"
        chords = [rc.chord for rc in composer.realize(body, k)]
        progression = p
    chord_len = bar / g.harmonic_rhythm
    total = bars * bar
    events, t, i = [], 0.0, 0
    while t < total - 1e-6:
        length = min(chord_len, total - t)
        events.append(composer.ChordEvent(chords[i % len(chords)], t, length))
        t += length
        i += 1
    wanted = parts or ["drums", "bass", "chords", "melody"]
    if g.bass_style == "none" and not parts:
        wanted = [w for w in wanted if w != "bass"]
    if g.comping == "none" and not parts:
        wanted = [w for w in wanted if w != "chords"]
    instruments = instruments or {}
    made: dict[str, dict] = {}
    for part in wanted:
        name = f"{g.name.title()} {part.title()}"
        track = call("create_track", timeout=60.0, name=name, instrument=instruments.get(part))
        number = track["track"]["number"]
        item = call("create_midi_item", track=number, start_bar=start_bar, length_bars=bars, name=f"{g.name} {part}")
        entry: dict = {"track": number, "item_id": item["id"]}
        if track.get("warning"):
            entry["warning"] = track["warning"]
        if part == "drums":
            groove = g.groove
            cells = [c for c in next(iter(groove["pattern"].values())) if c not in " |"]
            groove_qn = len(cells) * groove.get("step", 0.25)
            res = add_drum_pattern(item_id=item["id"], pattern=dict(groove["pattern"]), step=groove.get("step", 0.25),
                                   repeats=max(1, round(total / groove_qn)), swing=groove.get("swing", g.swing),
                                   humanize=0.15, feel=played_as)
            entry["lanes"] = res.get("lanes")
        elif part == "bass":
            notes = composer.bassline(events, g.bass_style if g.bass_style != "none" else "root", k, 2, meter, seed=seed)
            entry["notes"] = _write(item["id"], _perform(notes, "bass", played_as, seed), False).get("note_count")
            entry["style"] = g.bass_style
        elif part == "chords":
            voicings = composer.voice_chords([e.chord for e in events], g.voicing, 4, key=k)
            comping = g.comping if g.comping != "none" else "sustain"
            notes = composer.comp(events, voicings, comping, meter=meter, seed=seed)
            role = "pad" if comping == "sustain" else "arp" if comping.startswith(("arpeggio", "alberti", "pulse")) else "chords"
            entry["notes"] = _write(item["id"], _perform(notes, role, played_as, seed), False).get("note_count")
            entry["voicing"], entry["comping"] = g.voicing, g.comping
        elif part == "melody":
            notes = composer.melody(events, k, g.melody_density, 62, 81, g.melody_scale, meter, 4, seed,
                                    0.5 if g.swing > 54 else 0.3)
            entry["notes"] = _write(item["id"], _perform(notes, "lead", played_as, seed), False).get("note_count")
            entry["scale"] = g.melody_scale or k.scale.name
        made[part] = entry
    result = {
        "genre": g.name, "key": k.name, "progression": progression,
        "chords": [e.chord.symbol for e in events[: max(1, len(chords))]],
        "tempo": tempo_set or {"tempo_bpm": overview.get("tempo_bpm"), "note": "kept the project's tempo"},
        "bars": bars, "parts": made, "feel": played_as,
        "next": ("Pick sounds for each part (load_sound, or program the synths), adjust the groove, and build the "
                 "arrangement from the genre's form: " + ", ".join(f"{s} {b}" for s, b in g.form)),
    }
    if not instruments:
        result["note"] = "No instruments were given, so the tracks are empty of plugins: add instruments to hear them."
    return result


# ---------------------------------------------------------------- listening

def _render_track(track: str | int, start_bar: float, end_bar: float):
    """Renders a track's range and returns (mono audio, sample rate); deletes the file."""
    import os
    from pathlib import Path

    import soundfile as sf

    from .server import BridgeError, bridge

    render = call("render_audio", timeout=900.0, track=track, start_bar=start_bar, end_bar=end_bar)
    renders = (bridge.directory / "renders").resolve()
    for f in render["files"]:
        if renders not in Path(f).resolve().parents:
            raise BridgeError(f"refusing to use a render outside {renders}: {f}")
    try:
        audio, fs = sf.read(render["files"][0], dtype="float32", always_2d=True)
    finally:
        if not os.environ.get("CREAPER_KEEP_RENDERS"):
            for f in render["files"]:
                Path(f).unlink(missing_ok=True)
    return audio.mean(axis=1), fs


def _listen(track: str | int, pitches: list[int], channel: int | list[int], note_seconds: float, gap_seconds: float,
            velocity: int, one_shots: bool = False, chord: list[int] | None = None) -> tuple[list[dict], dict]:
    """Plays each pitch once on the track (in a temporary item after the end of the
    project), renders it, measures every note, and removes the item again. With chord,
    a held chord is played after them in the same render and the context gets
    'chord_motion' (does the patch hold it, or play its notes as a pattern)."""
    from . import listen

    overview = call("get_project_overview")
    bpm = float(overview.get("tempo_bpm") or 120)
    num, den = (int(x) for x in (overview.get("time_signature") or "4/4").split("/"))
    qn_per_bar = num * 4 / den
    slot_s = note_seconds + gap_seconds
    slot_qn = slot_s * bpm / 60
    start_bar = int(overview["length"]["bar"]) + 2
    slots = len(pitches) + (1 if chord else 0)
    length_bars = math.ceil(slot_qn * slots / qn_per_bar) + 1
    item = call("create_midi_item", track=track, start_bar=start_bar, length_bars=length_bars, name="creaper listening")
    try:
        channels = channel if isinstance(channel, list) else [channel] * len(pitches)
        notes = [{"pitch": p, "start": round(i * slot_qn, 6), "length": round(note_seconds * bpm / 60, 6),
                  "velocity": velocity, "channel": c} for i, (p, c) in enumerate(zip(pitches, channels))]
        notes += [{"pitch": p, "start": round(len(pitches) * slot_qn, 6), "length": round(note_seconds * bpm / 60, 6),
                   "velocity": velocity, "channel": channels[0]} for p in chord or []]
        call("add_midi_notes", item_id=item["id"], notes=notes, replace=True)
        context = call("get_instrument_notes", item_id=item["id"], channel=channels[0])
        audio, fs = _render_track(track, start_bar, start_bar + length_bars)
    finally:
        call("delete_item", item_id=item["id"])
    results = []
    slot = int(slot_s * fs)
    for i, p in enumerate(pitches):
        f = listen.features(audio[i * slot: (i + 1) * slot], fs, note_off=None if one_shots else note_seconds,
                            expected_hz=None if one_shots else listen.note_freq(p))
        f.update({"note": theory.midi_to_note(p), "pitch": p, "channel": channels[i]})
        results.append(f)
    if chord:
        x = audio[len(pitches) * slot: (len(pitches) + 1) * slot]
        context["chord_motion"] = listen.chord_motion(x, fs, note_seconds, listen.note_freq(min(chord)))
    return results, context


LATE_MS = 8.0


def _late_warning(results: list[dict]) -> str | None:
    """A note about sounds that start noticeably after their note-on."""
    late = [r for r in results if not r.get("silent") and r.get("starts_late_ms", 0) >= LATE_MS
            and r.get("attack_ms", 0) < 25]
    if not late:
        return None
    worst = max(late, key=lambda r: r["starts_late_ms"])
    where = f"ch {worst['channel']}" if len(results) == 16 and len({r.get("channel") for r in results}) > 1 else worst["note"]
    spread = {round(r["starts_late_ms"]) for r in late}
    kind = ("the plugin seems to add latency it doesn't report to REAPER" if len(late) == len(results) and max(spread) - min(spread) < 3
            else "those samples probably have silence at the start")
    return (f"{len(late)} sound(s) start late after the note (worst: {worst['starts_late_ms']:.0f} ms on {where}), so "
            f"they'll sound behind the beat: {kind}. Fix it at the source (trim the sample start in the "
            "instrument), or as a stopgap move those notes earlier by that much.")


def _short_name(fx: str | None) -> str | None:
    import re

    if not fx:
        return None
    name = re.sub(r"^(VSTi?3?|CLAPi?|AUi?|JS|DXi?)\s*:\s*", "", fx)
    return re.sub(r"\s*\([^)]*\)\s*$", "", name).strip() or fx


@tool()
def map_drum_kit(
    track: Annotated[str | int, Field(description="The drum track (number or name)")],
    low: Annotated[str | int, Field(description="Lowest key to try")] = "C0",
    high: Annotated[str | int, Field(description="Highest key to try")] = "C6",
    channel: Annotated[int, Field(ge=1, le=16, description="MIDI channel to play on (most kits listen on all; GM kits use 10)")] = 10,
    per_channel: Annotated[bool, Field(description=(
        "For kits that put each drum on its own MIDI channel (SILA, drum machines, multitimbral setups): "
        "play one note (`low`, default C4) on channels 1-16 instead of a range of keys"))] = False,
    save: Annotated[bool, Field(description="Save the result as this instrument's drum map")] = True,
    overwrite: Annotated[bool, Field(description="Replace a drum map you saved for this instrument before")] = False,
) -> dict:
    """Works out a drum kit by ear: plays every key in the range through the track's
    instrument (offline, in a temporary item that's removed afterwards), measures each
    sound and identifies it (kick, snare, clap, rim, closed/open hat, crash, ride, toms,
    shaker, cowbell, percussion). Saves the layout as a drum map so add_drum_pattern and
    genre grooves land on the right sounds. Use it whenever a kit's layout is unknown,
    instead of asking the user. Kits inside one plugin can differ: map again after
    changing kit."""
    from . import listen
    from .server import drum_maps

    lo, hi = theory.note_to_midi(low), theory.note_to_midi(high)
    if hi < lo or hi - lo > 96:
        raise ValueError("give a range of up to 8 octaves, low to high")
    if per_channel:
        lo = 60 if low == "C0" else lo  # per-channel kits usually trigger on C4
        results, context = _listen(track, [lo] * 16, list(range(1, 17)), 0.3, 1.5, 110, one_shots=True)
    else:
        results, context = _listen(track, list(range(lo, hi + 1)), channel, 0.3, 1.5, 110, one_shots=True)
    instrument = context.get("instrument")
    names = {n["pitch"]: n["name"] for n in context.get("note_names", [])}
    if instrument is None:
        raise ValueError("that track has no instrument to listen to")
    for r in results:
        if r.get("silent"):
            r["kind"], r["confidence"] = "silent", 1.0
    sounding = [r for r in results if not r.get("silent")]
    if not sounding:
        return {"instrument": instrument, "sounding_keys": 0,
                "note": f"Nothing sounded on channel {channel}. Try another channel (some kits put each drum on its own "
                        "channel), check the track isn't muted, or load a kit first."}
    follows, _ = listen.tracks_pitch(sounding)
    if per_channel:
        for r in sounding:
            r["pitch"], r["_note"] = r["channel"], r["pitch"]  # assign lanes by channel
    lanes, labels = listen.map_kit(sounding, gm=not per_channel)
    for r in sounding:
        r["kind"], r["confidence"] = labels.get(r["pitch"], ("percussion", 0.3))
    if per_channel:
        for r in sounding:
            r["pitch"] = r.pop("_note")
    # The plugin's own key names, when it reports them, beat any guess by ear.
    named_lanes = {}
    if names and not per_channel:
        for lane in ("kick", "snare", "clap", "rim", "closed hat", "open hat", "crash", "ride", "low tom", "mid tom", "high tom"):
            hit = theory.best_name_match(lane, names)
            if hit is not None:
                named_lanes[lane] = hit
        for lane, pitch in named_lanes.items():
            lanes[lane] = pitch
    gm_layout = not per_channel and listen.follows_gm(lanes)
    out: dict = {
        "instrument": instrument,
        "sounding_keys": len(sounding),
        "layout": ("named by the plugin" if len(named_lanes) >= 3 else
                   "General MIDI (kick 36/C2, snare 38/D2, closed hat 42/F#2): reliable" if gm_layout else
                   "custom: lanes are educated guesses from the sound, so check them by ear"),
        "keys": [{"note": r["note"], **({"channel": r["channel"]} if per_channel else {}),
                  "sound": r["kind"], "confidence": r["confidence"],
                  "decay_s": r["decay_s"], "brightness_hz": r["centroid_hz"],
                  **({"pitch_hz": r["pitch_hz"]} if r.get("pitch_hz") else {}),
                  **({"starts_late_ms": r["starts_late_ms"]} if r.get("starts_late_ms", 0) >= LATE_MS else {}),
                  **({"plugin_calls_it": names[r["pitch"]]} if r["pitch"] in names and not per_channel else {})}
                 for r in sounding],
    }
    late = _late_warning(sounding)
    if late:
        out["timing"] = late
    out["drum_map"] = ({lane: f"{theory.midi_to_note(lo)} ch {ch}" for lane, ch in lanes.items()} if per_channel
                       else {lane: theory.midi_to_note(p) for lane, p in lanes.items()})
    if follows and len(sounding) > 24:
        out["warning"] = ("The sound follows the keys chromatically, so this looks like a pitched instrument (or one "
                          "sample across the keyboard) rather than a kit; the map is probably meaningless.")
        save = False
    name = _short_name(instrument)
    if save and lanes:
        existing = drum_maps.find(instrument)
        if existing and existing[0] in drum_maps.all() and not overwrite:
            out["not_saved"] = f"You already have a drum map for {existing[0]}; pass overwrite=True to replace it."
        else:
            if per_channel:
                mapping = {lane: {"note": lo, "channel": ch} for lane, ch in lanes.items()}
            else:
                mapping = {lane: ({"note": p, "channel": channel} if channel != 10 else p) for lane, p in lanes.items()}
            drum_maps.save(name, mapping)
            out["saved_as"] = name
    out["tip"] = ("For a custom layout, play the main lanes back (a short add_drum_pattern and transport) and ask the "
                  "user only if something sounds wrong; fix a lane with save_drum_map.")
    return out


@tool()
def audition_instrument(
    track: Annotated[str | int, Field(description="The track whose instrument to listen to")],
    notes: Annotated[list[str | int] | None, Field(description="Notes to play; default C1 to C7, one per octave")] = None,
    note_seconds: Annotated[float, Field(gt=0.05, le=8)] = 1.0,
    channel: Annotated[int, Field(ge=1, le=16)] = 1,
    velocity: Annotated[int, Field(ge=1, le=127)] = 100,
) -> dict:
    """Listens to the track's current sound: plays notes across the range offline (in a
    temporary item that's removed afterwards) and reports its playable range, whether
    it follows pitch (and any transposition), attack, sustain, release, brightness and
    character (bright/dark, plucky/sustained, pad-like, noisy), each note's tuning, and
    a warning when held notes play a pattern of their own (a built-in arpeggiator,
    sequencer or gate, which would re-play every written part). Use it to check a patch
    you designed, or any preset before writing parts on it."""
    from . import listen

    pitches = [theory.note_to_midi(n) for n in notes] if notes else [24 + 12 * i for i in range(7)]
    results, context = _listen(track, pitches, channel, note_seconds, 1.5, velocity,
                               chord=[60, 64, 67] if note_seconds >= 0.6 else None)
    instrument = context.get("instrument")
    if instrument is None:
        raise ValueError("that track has no instrument to listen to")
    per_note = []
    for r in results:
        entry: dict = {"note": r["note"], "level_db": r["peak_db"]}
        if r.get("starts_late_ms", 0) >= LATE_MS:
            entry["starts_late_ms"] = r["starts_late_ms"]
        if r.get("silent"):
            entry["silent"] = True
        else:
            entry.update({k: r[k] for k in ("attack_ms", "decay_s", "sustain_db", "release_s", "centroid_hz")
                          if r.get(k) is not None})
            if r.get("pitch_hz"):
                entry["sounds_as"] = theory.midi_to_note(round(69 + 12 * math.log2(r["pitch_hz"] / 440)))
            if r.get("cents_off") is not None:
                entry["cents_off"] = r["cents_off"]
            if listen.plays_pattern(r):
                entry["plays_own_pattern"] = True
        per_note.append(entry)
    out = {"instrument": instrument, "summary": listen.describe_patch(results), "notes": per_note}
    patterned = [e["note"] for e in per_note if e.get("plays_own_pattern")]
    if listen.plays_pattern(context.get("chord_motion") or {}):
        patterned.append("a held C major chord")
    if patterned:
        out["warning"] = (f"held notes ({', '.join(patterned)}) play a pattern of their own: the patch has a built-in "
                          "arpeggiator, sequencer or gate. Turn it off in the plugin (get_fx_parameters search "
                          "'arp', 'seq', 'gate') or choose another sound; written parts would be re-played by it")
    cents = [r["cents_off"] for r in results if r.get("cents_off") is not None]
    if len(cents) >= 2 and max(cents) - min(cents) > 15:
        out["tuning_warning"] = (f"its notes are {max(cents) - min(cents):.0f} cents apart in tuning: out of tune "
                                 "unless a detuned sound is the point")
    late = _late_warning(results)
    if late:
        out["timing"] = late
    return out
