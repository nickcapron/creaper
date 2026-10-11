"""MCP tools for vocals: chopping real vocal samples into rhythmic, in-key chops, and
robot vocals (the computer's own voice speaks the lyrics, one clip per word under the
melody's notes, and a vocoder makes a synth playing the melody sing them)."""

from __future__ import annotations

import random
import re
import time
from pathlib import Path
from typing import Annotated, Callable

from pydantic import Field

from . import composer, harmony, samplelib, speech
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
    """The text-to-speech voices on this computer, for add_robot_vocal's voice."""
    return {"voices": speech.voices()}


@tool()
def add_robot_vocal(
    item_id: ItemId,
    lyrics: Annotated[str, Field(description=(
        "The words, one per note of the melody: 'all night long _ to-night'. Hyphenate to spread a word over "
        "several notes; a lone '_' holds the previous word over the next note"))],
    voice: Annotated[str | None, Field(description="A voice from list_speech_voices (part of its name), or 'female'/'male'")] = None,
    name: Annotated[str, Field(description="Name for the vocal track")] = "Robot Vocal",
    carrier: Annotated[str | None, Field(description="Synth that sings (any instrument; default ReaSynth). Bright, buzzy sounds (saws) give the clearest words")] = None,
    bands: Annotated[int, Field(ge=4, le=128, description="Vocoder bands: more = clearer words, fewer = more robotic")] = 32,
) -> dict:
    """Makes a synth sing words, vocoder style: the computer's text-to-speech voice
    speaks each word under its note of a melody item (top note of each chord), and
    ReaVocode shapes a synth playing the melody (chords too) with that speech. Each
    word's vowel is held over its notes while its consonants keep their natural speed.
    Builds three tracks after the melody's track: the vocal (the vocoder), its voice
    (the spoken words; it also plays their high-passed consonants for clarity) and its
    carrier (the synth).
    Robot vocals are only understood when they're sparse: a short hook of a few words,
    repeated (think "one more time", "around the world"), at most one syllable per beat,
    on quarter notes or longer. Dense, fast verses turn to mush. To make words clearer,
    raise the voice track's fader (consonants) or the band count; don't blend the raw
    voice in with ReaVocode's ModDry, which adds its out-of-key speaking pitch."""
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
    times = call("qn_to_times", qns=[q for w in words for q in (base + w["start"], base + w["end"])])
    clips, rushed = [], []
    for i, (f, w) in enumerate(zip(files, words)):
        # Hold the vowel over the notes; consonants keep their natural speed.
        speed = speech.fit_word(f, times[2 * i + 1] - times[2 * i])
        if speed > RUSHED:
            rushed.append(w["word"])
        clips.append({"path": str(f), "start_qn": base + w["start"], "end_qn": base + w["end"], "word": w["word"]})
    result = call("build_robot_vocal", timeout=120.0, melody_item=item_id, clips=clips, name=name,
                  carrier=carrier, bands=bands)
    result.pop("squeezed", None)
    result["speech_voice"] = chosen or "system default"
    result["word_files"] = str(folder)
    result["next"] = ("Play it. If words are hard to make out: more bands, a brighter carrier (saw, filter open), "
                      "or fewer syllables per beat. Mute the original melody track if it doubles the vocal.")
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
