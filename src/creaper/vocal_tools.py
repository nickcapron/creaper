"""MCP tools for vocals: chopping real vocal samples into rhythmic, in-key chops, and
robot vocals (the computer's own voice speaks the lyrics, one clip per word under the
melody's notes, and a vocoder makes a synth playing the melody sing them)."""

from __future__ import annotations

import random
import re
import time
from pathlib import Path
from typing import Annotated, Callable, Literal

from pydantic import Field

from . import composer, harmony, samplelib, speech, talkbox
from .sample_tools import _check_audio
from .server import READ_ONLY, ItemId, call, tool

# Notes starting this close together (in QN) count as one onset: the top one sings.
ONSET_TOLERANCE = 1 / 64
# Words spoken this much faster than natural to fit their notes start to blur.
RUSHED = 1.6


def melody_line(notes: list[dict]) -> list[dict]:
    """The singable line of a MIDI part: the highest note at each onset, in time order."""
    line: list[dict] = []
    for note in sorted((n for n in notes if not n.get("muted")), key=lambda n: (n["start"], -n["pitch"])):
        if line and abs(note["start"] - line[-1]["start"]) < ONSET_TOLERANCE:
            continue
        line.append(note)
    return line


def assign_lyrics(lyrics: str, line: list[dict]) -> list[dict]:
    """Matches words to notes: one word per note; 'to-night' sings over two notes; a
    lone '_' (or '-') holds the previous word over one more note. Returns each word
    with the text to speak and its span in QN from the item start."""
    tokens = lyrics.split()
    if not tokens:
        raise ValueError("give the lyrics to sing")
    words: list[dict] = []
    for token in tokens:
        if token in ("_", "-"):
            if not words:
                raise ValueError("the lyrics can't start with a hold ('_')")
            words[-1]["notes"] += 1
            continue
        parts = [p for p in token.split("-") if p]
        spoken = re.sub(r"[^\w']", "", "".join(parts))
        if not spoken:
            raise ValueError(f"'{token}' has nothing to sing")
        words.append({"word": token, "text": spoken, "notes": max(1, len(parts))})
    needed = sum(w["notes"] for w in words)
    if needed != len(line):
        raise ValueError(
            f"the lyrics cover {needed} notes but the melody has {len(line)}. One word per note; hyphenate a "
            "word to spread it over several notes ('to-night'), or add '_' to hold a word over the next note.")
    out, i = [], 0
    for w in words:
        first, last = line[i], line[i + w["notes"] - 1]
        i += w["notes"]
        end = last["start"] + last["length"]
        if i < len(line):
            end = min(end, line[i]["start"])  # never overlap the next word
        out.append({"word": w["word"], "text": w["text"], "start": first["start"], "end": end})
    return out


@tool(annotations=READ_ONLY)
def list_speech_voices() -> dict:
    """The text-to-speech voices on this computer, best first, for add_robot_vocal's
    voice. Piper voices (if installed) sound the most natural; each shows its license,
    and only public domain, CC0 or CC BY ones may go in released music."""
    return {"voices": speech.voices(), "default": speech.default_voice()}


@tool()
def set_default_voice(
    voice: Annotated[str, Field(description="A voice from list_speech_voices (part of its name), or 'female'/'male'")],
) -> dict:
    """Makes a voice the user's default for robot vocals (used whenever no voice is
    named), remembered across sessions."""
    name = speech.set_default_voice(voice)
    return {"default": name, "license": speech.voice_license(name) or "the operating system's own voice"}


@tool()
def add_robot_vocal(
    item_id: ItemId,
    lyrics: Annotated[str, Field(description=(
        "The words, one per note of the melody: 'all night long _ to-night'. Hyphenate to spread a word over "
        "several notes; a lone '_' holds the previous word over the next note"))],
    voice: Annotated[str | None, Field(description="A voice from list_speech_voices (part of its name), or 'female'/'male'")] = None,
    name: Annotated[str, Field(description="Name for the vocal track")] = "Robot Vocal",
    style: Annotated[Literal["talkbox", "vocoder"], Field(description=(
        "talkbox (default): a synth shaped by the speech's mouth shapes, the clearest words (Zapp, Chromeo, "
        "Daft Punk leads); one audio track. vocoder: ReaVocode over a synth you can change and play chords on; "
        "more robotic and harder to understand"))] = "talkbox",
    carrier: Annotated[str | None, Field(description="vocoder: synth that sings (default ReaSynth saw)")] = None,
    bands: Annotated[int, Field(ge=4, le=128, description="vocoder: bands; more = clearer words")] = 32,
) -> dict:
    """Makes a synth sing words: the computer's text-to-speech voice speaks each word
    under its note of a melody item (top note of each chord), each word's vowel held
    over its notes while its consonants keep their natural speed.
    talkbox (default) shapes a sawtooth playing the melody with the speech's formants,
    with noise for the consonants, and puts the result on one audio track after the
    melody's track. vocoder builds three tracks (the vocal with ReaVocode, its voice,
    and a carrier synth that can play the melody's chords).
    Robot vocals are only understood when they're sparse: a short hook of a few words,
    repeated (think "one more time", "around the world"), at most one syllable per beat,
    on quarter notes or longer. Dense, fast verses turn to mush. The result includes a
    measured clarity score (alone and in the mix): act on it rather than guessing."""
    data = call("get_midi_notes", item_id=item_id)
    line = melody_line(data.get("notes", []))
    if not line:
        raise ValueError("that MIDI item has no notes to sing")
    words = assign_lyrics(lyrics, line)
    chosen = speech.choose_voice(voice)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    slug = re.sub(r"[^\w-]+", "-", name).strip("-") or "vocal"
    folder = Path(call("project_paths")["default_folder"]) / "creaper vocals" / f"{slug}-{stamp}"
    files = speech.speak([w["text"] for w in words], folder, chosen)
    base = data["start"]["qn"]
    qns = [q for w in words for q in (base + w["start"], base + w["end"])] + [base + n["start"] for n in line]
    times = call("qn_to_times", qns=qns)
    note_times = times[2 * len(words):]
    clips, rushed = [], []
    for i, (f, w) in enumerate(zip(files, words)):
        # Hold the vowel over the notes; consonants keep their natural speed.
        start_s, end_s = times[2 * i], times[2 * i + 1]
        speed = speech.fit_word(f, end_s - start_s)
        if speed > RUSHED:
            rushed.append(w["word"])
        if style == "talkbox":
            pitches = [(max(0.0, t - start_s), n["pitch"]) for n, t in zip(line, note_times)
                       if w["start"] - 1e-6 <= n["start"] < w["end"] - 1e-6] or [(0.0, line[0]["pitch"])]
            x, fs = speech._read(f)
            (folder / "speech").mkdir(exist_ok=True)
            speech._write(folder / "speech" / f.name, x, fs)  # the clean words, for check_vocal_clarity
            speech._write(f, talkbox.cross_synthesize(x, fs, pitches, seed=i), talkbox.RATE)
        clips.append({"path": str(f), "start_qn": base + w["start"], "end_qn": base + w["end"], "word": w["word"]})
    if style == "talkbox":
        names = {t["name"] for t in call("get_project_overview").get("tracks", [])}
        track_name, k = name, 2
        while track_name in names:
            track_name, k = f"{name} {k}", k + 1
        call("create_track", name=track_name, position=int(data["track"]) + 1)
        placed = call("place_audio_clips", timeout=120.0, track=track_name, clips=clips, name=f"talk box {track_name}")
        high = sum(1 for n in line if talkbox.sub_octave_level(n["pitch"]) > 0)
        result = {"vocal": placed["track"], "style": "talkbox", "words_placed": placed["placed"],
                  "next": ("Play it. It's audio now: add EQ, compression, chorus or reverb like any vocal. For "
                           "another melody or words, run it again. Mute the original melody track if it doubles it.")}
        if high:
            result["octave_doubled"] = (f"{high} of {len(line)} notes are above E4, where words blur, so they're "
                                        "doubled an octave down for clarity. Write the melody lower to avoid it.")
    else:
        result = call("build_robot_vocal", timeout=120.0, melody_item=item_id, clips=clips, name=name,
                      carrier=carrier, bands=bands)
        result.pop("squeezed", None)
        result["style"] = "vocoder"
        result["next"] = ("Play it. If words are hard to make out: more bands, a brighter carrier (saw, filter "
                          "open), fewer syllables per beat, or style='talkbox'. Mute the original melody track if "
                          "it doubles the vocal.")
    result["speech_voice"] = chosen or "system default"
    license_ = speech.voice_license(chosen)
    if license_:
        result["voice_license"] = license_ + ("" if license_.startswith(speech.COMMERCIAL_OK)
                                              else ": don't use it in music that will be released")
    result["word_files"] = str(folder)
    try:  # how understandable it came out, alone and with everything else playing
        from .ear_tools import measure_vocal_clarity
        others = len(call("get_project_overview").get("tracks", [])) > 4
        result["clarity"] = measure_vocal_clarity(result["vocal"]["name"], in_mix=others)
    except Exception as e:  # noqa: BLE001  (a failed measurement mustn't undo the vocal)
        result["clarity"] = {"error": f"couldn't measure clarity: {e}"}
    if rushed:
        result["note"] = (f"{len(rushed)} of {len(words)} words had to be sped up more than {RUSHED:g}x to fit "
                          "their notes, which blurs them: " + ", ".join(rushed[:12]) + (" ..." if len(rushed) > 12
                          else "") + ". Give them longer notes, or fewer words.")
    return result


# ---------------------------------------------------------------- vocal chops

STEP_QN = 0.25  # one pattern step: a 16th note
MAX_SHIFT = 6   # semitones; further and a voice turns chipmunk or monster


def parse_pattern(pattern: str) -> list[str]:
    steps = [c for c in pattern if c in "xX-."]
    if not steps or "x" not in pattern.lower():
        raise ValueError("a pattern is 16th-note steps: x starts a chop, - holds it, . is a rest (e.g. 'x..x..x.x-..x...')")
    return steps


def plan_chops(slices: list[dict], pattern: str, bars: float, chord_at: Callable[[float], set[int] | None] | None,
               seconds_per_qn: float, seed: int = 1, qn_per_bar: float = 4.0) -> list[dict]:
    """Where each chop goes (QN from the first bar), which slice it plays, and how far
    it's shifted: to the nearest note of the chord (or scale) in force, at most a
    tritone, correcting the slice's own tuning too. Slices are used in a shuffled
    order that repeats, so a phrase comes back like a hook."""
    usable = [i for i, sl in enumerate(slices) if sl["end"] - sl["start"] >= 0.06]
    if not usable:
        raise ValueError("no usable slices: the sample is too short or too quiet")
    pitched = [i for i in usable if "pitch" in slices[i]] or usable
    order = pitched[:]
    random.Random(seed).shuffle(order)
    steps = parse_pattern(pattern)
    total = int(round(bars * qn_per_bar / STEP_QN))
    chops = []
    k = 0
    for step in range(total):
        if steps[step % len(steps)] not in "xX":
            continue
        hold = 1
        while step + hold < total and steps[(step + hold) % len(steps)] == "-":
            hold += 1
        index = order[k % len(order)]
        k += 1
        sl = slices[index]
        start = step * STEP_QN
        natural = (sl["end"] - sl["start"]) / seconds_per_qn
        length = min(hold * STEP_QN, natural)
        shift = 0.0
        pcs = chord_at(start) if chord_at else None
        if pcs and "pitch" in sl:
            p = sl["pitch"]
            targets = [round(p) + d for d in range(-MAX_SHIFT, MAX_SHIFT + 1) if (round(p) + d) % 12 in pcs]
            if targets:
                shift = round(min(targets, key=lambda t: (abs(t - p), t)) - p, 2)
        chops.append({"slice": index, "start": start, "length": round(length, 4), "semitones": shift})
    return chops


@tool()
def chop_vocal(
    path: Annotated[str, Field(description="A vocal sample: a phrase, acapella or vocal one-shot (find_samples role='vocal')")],
    track: Annotated[str, Field(description="Track for the chops (created if there's none by that name)")],
    bar: Annotated[float, Field(ge=1)] = 1,
    bars: Annotated[float, Field(gt=0, le=64)] = 4,
    pattern: Annotated[str, Field(description=(
        "Rhythm in 16th steps, repeating: x = a chop, - = hold it, . = rest. e.g. 'x..x..x.x-..x...' "
        "(house), 'x.x.x.x.' (stutter), 'x---..x-x---....' (longer phrases)"))] = "x..x..x.x-..x...",
    chords: Annotated[str | None, Field(description="Chord symbols, one per bar and repeating ('Fm9 Dbmaj7 Ab Eb'): chops move to their notes")] = None,
    chords_item: Annotated[str | None, Field(description="Or a MIDI item playing the song's chords: chops follow them")] = None,
    key: Annotated[str | None, Field(description="Or just keep chops in this key ('F minor')")] = None,
    seed: Annotated[int, Field(description="Another seed picks the slices in another order")] = 1,
) -> dict:
    """Turns a real vocal sample into rhythmic vocal chops, the house / future-bass
    way: slices it at its syllables, lays the slices on a 16th-note pattern, and
    shifts each one (at most a tritone, correcting its tuning) onto the chord or key.
    Real voices beat robot vocals, so use this first when the user's samples have
    vocals. One item per chop, all ordinary audio to edit afterwards."""
    path = _check_audio(path)
    slices = samplelib.slice_vocal(path)
    if not slices:
        raise ValueError("couldn't find any sung or spoken parts in that sample")
    overview = call("get_project_overview")
    seconds_per_qn = 60 / float(overview.get("tempo_bpm") or 120)
    num, den = (int(x) for x in str(overview.get("time_signature") or "4/4").split("/"))
    qn_per_bar = num * 4 / den
    start_qn = call("bar_to_qn", bar=bar)["qn"]
    chord_at = None
    if chords_item:
        chord_notes = call("get_midi_notes", item_id=chords_item, limit=20000)
        offset = chord_notes["start"]["qn"] - start_qn
        chord_at = composer.chord_lookup([dict(n, start=n["start"] + offset) for n in chord_notes["notes"]
                                          if not n.get("muted")])
    elif chords:
        sets = [harmony.spelled_from_symbol(c).pitch_classes() for c in chords.split()]
        chord_at = lambda qn: sets[int(qn // qn_per_bar) % len(sets)]  # noqa: E731
    elif key:
        scale = harmony.parse_key(key).pitch_classes()
        chord_at = lambda qn: scale  # noqa: E731
    plan = plan_chops(slices, pattern, bars, chord_at, seconds_per_qn, seed, qn_per_bar)
    if not any(t["name"] == track for t in overview.get("tracks", [])):
        call("create_track", name=track)
    clips = []
    for c in plan:
        sl = slices[c["slice"]]
        clips.append({"path": path, "start_qn": start_qn + c["start"], "end_qn": start_qn + c["start"] + c["length"],
                      "offset": sl["start"], "semitones": c["semitones"], "word": f"chop {c['slice'] + 1}"})
    result = call("place_audio_clips", timeout=120.0, track=track, clips=clips, name="vocal chops")
    shifts = [abs(c["semitones"]) for c in plan]
    result.update({"slices_found": len(slices), "pitched_slices": sum("pitch" in s for s in slices),
                   "chops": len(plan), "largest_shift": max(shifts) if shifts else 0,
                   "fit_to": "chords" if (chords or chords_item) else ("key" if key else "unchanged pitch")})
    return result


# ------------------------------------------------------- singing synthesizers

# Singing synths creaper recognizes, as plugins or installed apps, and how each takes
# a MIDI file with lyrics.
SINGERS = {
    "Synthesizer V": ("synthesizer v|synthv|dreamtonics", "File > Import (or drag the .mid in); lyrics come in on the notes"),
    "ACE Studio": ("ace studio|ace bridge", "drag the .mid onto a track; lyrics come in on the notes"),
    "VOCALOID": ("vocaloid", "File > Import > MIDI; lyrics come in on the notes"),
    "OpenUtau": ("openutau|utau", "drag the .mid into the window; set the hold symbol to '+' for OpenUtau"),
    "Alter/Ego": ("alter.?ego|plogue", "load it as an instrument on the melody's track and type the lyrics in its window"),
    "Emvoice": ("emvoice", "load it as an instrument on the melody's track and type the lyrics in its window"),
}
_APP_DIRS = {
    "Synthesizer V": ["Dreamtonics", "Synthesizer V Studio 2 Pro", "Synthesizer V Studio Pro"],
    "ACE Studio": ["ACE Studio"],
    "VOCALOID": ["VOCALOID6", "VOCALOID5"],
    "OpenUtau": ["OpenUtau"],
}


def singing_synths() -> list[str]:
    """The singing synths installed here: as plugins REAPER knows, or as apps."""
    found = set()
    names = " ".join(p.get("name", "") for p in call("list_installed_fx", search=None, limit=2000).get("plugins", []))
    for singer, (pattern, _) in SINGERS.items():
        if re.search(pattern, names, re.I):
            found.add(singer)
    roots = [Path(p) for p in (r"C:\Program Files", r"C:\Program Files (x86)", str(Path.home() / "AppData/Local"),
                               "/Applications", str(Path.home() / "Applications"))]
    for singer, dirs in _APP_DIRS.items():
        for root in roots:
            if any((root / d).exists() or (root / f"{d}.app").exists() for d in dirs):
                found.add(singer)
    return sorted(found)


def singer_syllables(lyrics: str, line: list[dict], hold: str = "-") -> list[str]:
    """One lyric per note for a singing synth: each syllable of 'to-night' on its own
    note, and `hold` (the singer's melisma mark) where '_' holds the previous word."""
    out: list[str] = []
    for token in lyrics.split():
        if token in ("_", "-"):
            if not out:
                raise ValueError("the lyrics can't start with a hold ('_')")
            out.append(hold)
        else:
            out += [p for p in token.split("-") if p] or [token]
    if len(out) != len(line):
        raise ValueError(f"the lyrics have {len(out)} syllables and holds but the melody has {len(line)} notes. "
                         "One syllable per note: hyphenate words ('to-night'), '_' holds the previous one.")
    return out


def _vlq(n: int) -> bytes:
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append(0x80 | (n & 0x7F))
        n >>= 7
    return bytes(reversed(out))


def _chunk(kind: bytes, data: bytes) -> bytes:
    return kind + len(data).to_bytes(4, "big") + data


def _track(events: list[tuple[int, int, bytes]]) -> bytes:
    """events: (tick, order, data); order puts note-offs before note-ons on one tick."""
    out, last = bytearray(), 0
    for tick, _, data in sorted(events, key=lambda e: (e[0], e[1])):
        out += _vlq(tick - last) + data
        last = tick
    out += _vlq(0) + b"\xff\x2f\x00"
    return _chunk(b"MTrk", bytes(out))


def _meta(kind: int, data: bytes) -> bytes:
    return bytes([0xFF, kind]) + _vlq(len(data)) + data


def midi_with_lyrics(notes: list[dict], tempos: list[tuple[float, float]], meter: tuple[int, int],
                     name: str = "Vocal", ppq: int = 480) -> bytes:
    """A standard MIDI file (type 1) singing synths import: a tempo track (tempos as
    (QN, BPM)) and one track whose notes each carry their lyric. Notes: pitch, start
    and length in QN from the song's start, velocity, lyric."""
    num, den = meter
    conductor = [(0, 0, _meta(0x03, b"Tempo")),
                 (0, 1, _meta(0x58, bytes([num, max(0, den.bit_length() - 1), 24, 8])))]
    for qn, bpm in tempos:
        conductor.append((int(round(qn * ppq)), 2, _meta(0x51, int(round(60_000_000 / bpm)).to_bytes(3, "big"))))
    voice = [(0, 0, _meta(0x03, name.encode("utf-8")))]
    for n in notes:
        on, off = int(round(n["start"] * ppq)), int(round((n["start"] + n["length"]) * ppq))
        voice.append((on, 2, _meta(0x05, n["lyric"].encode("utf-8"))))
        voice.append((on, 3, bytes([0x90, n["pitch"], max(1, min(127, n.get("velocity", 100)))])))
        voice.append((max(on + 1, off), 1, bytes([0x80, n["pitch"], 0])))
    header = _chunk(b"MThd", (1).to_bytes(2, "big") + (2).to_bytes(2, "big") + ppq.to_bytes(2, "big"))
    return header + _track(conductor) + _track(voice)


@tool()
def export_vocal_midi(
    item_id: ItemId,
    lyrics: Annotated[str, Field(description="One syllable per note: 'dan-cing in the dark _' (hyphens split syllables, '_' holds)")],
    name: Annotated[str, Field(description="File and part name")] = "Lead Vocal",
    hold: Annotated[str, Field(description="The singer's melisma mark: '-' (Synthesizer V, ACE Studio, VOCALOID) or '+' (OpenUtau)")] = "-",
) -> dict:
    """For a real singing voice: writes a melody item and its lyrics as a MIDI file
    that singing synths (Synthesizer V, ACE Studio, VOCALOID, OpenUtau) import with
    the words on the notes, at the song's tempo and positions. Says which singers are
    installed and how to load it. The singer renders the vocal; then insert_audio_file
    it at bar 1 (the file starts at the song's start) and mix it like any vocal."""
    data = call("get_midi_notes", item_id=item_id, limit=20000)
    line = melody_line(data.get("notes", []))
    if not line:
        raise ValueError("that MIDI item has no notes to sing")
    words = singer_syllables(lyrics, line, hold)
    base = data["start"]["qn"]
    notes = [{"pitch": n["pitch"], "start": base + n["start"], "length": n["length"], "velocity": n.get("velocity", 100),
              "lyric": w} for n, w in zip(line, words)]
    tempo = call("get_tempo_map")
    tempos = [(0.0, float(tempo["start_tempo_bpm"]))]
    ramps = False
    for change in tempo.get("changes", []):
        tempos.append((float(change["position"]["qn"]), float(change["bpm"])))
        ramps = ramps or bool(change.get("ramp_to_next"))
    num, den = (int(x) for x in tempo["start_time_signature"].split("/"))
    folder = Path(call("project_paths")["default_folder"]) / "creaper vocals"
    folder.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^\w-]+", "-", name).strip("-") or "vocal"
    path = folder / f"{slug}-{time.strftime('%Y%m%d-%H%M%S')}.mid"
    path.write_bytes(midi_with_lyrics(notes, sorted(tempos), (num, den), name))
    singers = singing_synths()
    result = {"file": str(path), "notes": len(notes), "starts_at": "the song's start (bar 1)",
              "singers_installed": singers or None,
              "how_to_load": {s: SINGERS[s][1] for s in singers} or None}
    if not singers:
        result["note"] = ("No singing synth found. Free: OpenUtau with a DiffSinger voice; paid: Synthesizer V, ACE "
                          "Studio. Meanwhile, add_robot_vocal can sing these lyrics robot-style.")
    if ramps:
        result["warning"] = "the song has tempo ramps; the file steps between tempos, so check the timing there"
    return result
