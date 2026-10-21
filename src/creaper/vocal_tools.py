"""MCP tools for vocals: chopping real vocal samples into rhythmic, in-key chops, and
robot vocals (the computer's own voice speaks the lyrics, one clip per word under the
melody's notes, and a vocoder makes a synth playing the melody sing them)."""

from __future__ import annotations

import base64
import os
import random
import re
import struct
import time
from pathlib import Path
from typing import Annotated, Callable, Literal

import numpy as np
from pydantic import Field

from . import analysis, asr, composer, harmony, samplelib, singing, speech, talkbox
from . import sample_tools  # the module, not its names: it may still be loading (circular import)
from .server import READ_ONLY, ItemId, TrackRef, bridge, call, tool

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


# Robot vocals are only understood when sparse: at most this many syllables per beat
# in any stretch of DENSITY_WINDOW_QN.
MAX_SYLLABLES_PER_BEAT = 1.0
DENSITY_WINDOW_QN = 4.0


def syllables(word: str) -> int:
    """A rough syllable count from vowel groups ('tonight' 2, 'more' 1, 'little' 2)."""
    w = re.sub(r"[^a-z]", "", word.lower())
    groups = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and not w.endswith(("le", "ee", "ye")) and groups > 1:
        groups -= 1  # a silent final e
    elif re.search(r"[^aeiouysxzcgh]es$", w) and groups > 1:
        groups -= 1  # lines, tires, times (but places, roses, changes keep theirs)
    elif re.search(r"[^aeiouytd]ed$", w) and groups > 1:
        groups -= 1  # burned, turned (but waited, faded keep theirs)
    return max(1, groups)


def assign_lyrics(lyrics: str, line: list[dict], max_per_beat: float | None = MAX_SYLLABLES_PER_BEAT) -> list[dict]:
    """Matches words to notes: one word per note; 'to-night' sings over two notes; a
    lone '_' (or '-') holds the previous word over one more note. Returns each word
    with the text to speak and its span in QN from the item start. Refuses lyrics
    denser than max_per_beat syllables per beat over any DENSITY_WINDOW_QN (None: no
    limit), because a robot voice turns fast words to mush."""
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
        words.append({"word": token, "text": spoken, "notes": max(1, len(parts)),
                      "syllables": max(len(parts), sum(syllables(p) for p in parts))})
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
        out.append({"word": w["word"], "text": w["text"], "start": first["start"], "end": end,
                    "syllables": w["syllables"]})
    if max_per_beat is not None:
        _check_density(out, max_per_beat)
    for w in out:
        del w["syllables"]
    return out


def _check_density(words: list[dict], max_per_beat: float) -> None:
    # Each word's syllables spread evenly over its span; then the busiest window.
    onsets = sorted(w["start"] + i * (w["end"] - w["start"]) / w["syllables"]
                    for w in words for i in range(w["syllables"]))
    allowed = max_per_beat * DENSITY_WINDOW_QN
    for i, t in enumerate(onsets):
        count = sum(1 for u in onsets[i:] if u < t + DENSITY_WINDOW_QN - 1e-6)
        if count > allowed:
            beat = t + 1
            voice = "a robot voice" if max_per_beat <= 1 else "a sung voice"
            raise ValueError(
                f"too many words for {voice}: {count} syllables in the {DENSITY_WINDOW_QN:g} beats from beat "
                f"{beat:g} of the melody (at most {allowed:g}: "
                f"{'one per beat' if max_per_beat <= 1 else f'{max_per_beat:g} a beat'}). Fast words turn to mush; "
                "use fewer words (a short hook, repeated), hold words over notes with '_', or write longer notes")


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
    name: Annotated[str | None, Field(description="Name for the vocal track; default: Robot Vocal (Sung Vocal)")] = None,
    style: Annotated[Literal["talkbox", "vocoder", "sung"], Field(description=(
        "talkbox (default): a synth shaped by the speech's mouth shapes, the clearest words (Zapp, Chromeo, "
        "Daft Punk leads); one audio track. vocoder: ReaVocode over a synth you can change and play chords on; "
        "more robotic and harder to understand. sung: the voice itself sings the melody (the whole line spoken "
        "in one go, each word moved to its notes keeping the voice's character, vibrato on held notes, a "
        "double); a guide vocal or a synthetic singer, not a robot. Up to two syllables a beat. Words are "
        "clearest within about 7 semitones of the voice's speaking pitch (the result's shift_semitones)"))] = "talkbox",
    carrier: Annotated[str | None, Field(description="vocoder: synth that sings (default ReaSynth saw)")] = None,
    bands: Annotated[int, Field(ge=4, le=128, description="vocoder: bands; more = clearer words")] = 32,
    double: Annotated[bool, Field(description=(
        "sung: add a double (a second take 10 ms late, a few cents apart, left and right) for width; "
        "off is a little clearer"))] = True,
    tuning: Annotated[Literal["natural", "hard"], Field(description=(
        "sung: natural (glides into notes, vibrato on long ones) or hard: snapped dead onto each note like a "
        "hard pitch corrector, the Daft Punk / T-Pain sound"))] = "natural",
    octave: Annotated[Literal["auto", "as written"], Field(description=(
        "sung: auto sings the line an octave nearer the voice when the melody sits more than 7 semitones from "
        "its speaking pitch (much clearer words, like a lower or higher singer); as written keeps the notes"))]
    = "auto",
    replace: Annotated[bool, Field(description=(
        "Re-sing onto the existing vocal track of that name: its clips are swapped and its effects, sends and "
        "ducking stay (talkbox and sung). Use it for every new take of the same part"))] = False,
) -> dict:
    """Makes a synth sing words: the computer's text-to-speech voice speaks each word
    under its note of a melody item (top note of each chord), each word's vowel held
    over its notes while its consonants keep their natural speed.
    talkbox (default) shapes a sawtooth playing the melody with the speech's formants,
    with noise for the consonants, and puts the result on one audio track after the
    melody's track. vocoder builds three tracks (the vocal with ReaVocode, its voice,
    and a carrier synth that can play the melody's chords).
    sung (style='sung') speaks the whole line once, so the words keep a sentence's
    shape, finds each word in it (aligned against the words spoken alone), and sings
    each on its notes holding its voiced part; one stereo audio track with a double,
    its harmonics-to-noise ratio, clarity and pitch shift measured.
    Robot vocals are only understood when they're sparse: a short hook of a few words,
    repeated (think "one more time", "around the world"), at most one syllable per beat,
    on quarter notes or longer (denser lyrics are refused). Dense, fast verses turn to
    mush. Keep the melody low: words are clearest below about E4 (measured clarity falls
    about 0.1 per octave above). Harmonies only once the hook has been heard alone, as
    every extra voice blurs the words: for a talk box, sing the same words on a harmony
    copy of the melody (edit_midi_notes add_harmony with chords_item); for the vocoder,
    add_harmony with chords_item on its Carrier track's item. It speaks with the user's
    default voice (set_default_voice), else the best from list_speech_voices. The result
    includes a measured clarity score (alone and in the mix). That can't tell which lines
    a listener will mishear (a robot voice keeps the words' shape while they still
    sound like other words); with the optional creaper[asr] extra installed, a speech
    recogniser transcribes each line (talkbox and sung) and the result's heard and
    unclear_lines name the lines to rewrite. Otherwise ask the user what they hear.
    Sing new takes with replace=True.
    Writing words a voice can carry: common, predictable words with open vowels ('into
    the night', 'down the mountain road', 'all night long'); short lines of 3-6
    syllables; few consonant clusters ('street lights', 'wheels', 'motor' smear) and no
    key word that starts on a soft h or l ('downhill' came out 'ground'). Put words in
    speech rhythm: notes about 0.9 of their slot long (a breath before each word), only
    the last word of a phrase held; unstressed syllables ('-ing', 'the') on short
    notes."""
    data = call("get_midi_notes", item_id=item_id)
    line = melody_line(data.get("notes", []))
    if not line:
        raise ValueError("that MIDI item has no notes to sing")
    name = name or ("Sung Vocal" if style == "sung" else "Robot Vocal")
    words = assign_lyrics(lyrics, line, SUNG_MAX_PER_BEAT if style == "sung" else MAX_SYLLABLES_PER_BEAT)
    chosen = speech.choose_voice(voice)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    slug = re.sub(r"[^\w-]+", "-", name).strip("-") or "vocal"
    folder = Path(call("project_paths")["default_folder"]) / "creaper vocals" / f"{slug}-{stamp}"
    base = data["start"]["qn"]
    qns = [q for w in words for q in (base + w["start"], base + w["end"])] + [base + n["start"] for n in line]
    times = call("qn_to_times", qns=qns)
    note_times = times[2 * len(words):]
    if style == "sung":
        clips, rushed, sung = _sing(words, line, times, note_times, base, folder, chosen, double,
                                    hard=tuning == "hard", auto_octave=octave == "auto")
        files = []
    else:
        files = speech.speak([w["text"] for w in words], folder, chosen)
        clips, rushed, sung = [], [], {}
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
    if style in ("talkbox", "sung"):
        tracks = call("get_project_overview").get("tracks", [])
        names = {t["name"] for t in tracks}
        track_name, k = name, 2
        if replace and name in names:
            # A new take onto the same track: its effects, sends and ducking stay.
            target = next(t for t in tracks if t["name"] == name)
            for item in call("get_track_details", track=target.get("guid") or name).get("items", []):
                call("delete_item", item_id=item["id"])
        else:
            while track_name in names:
                track_name, k = f"{name} {k}", k + 1
            call("create_track", name=track_name, position=int(data["track"]) + 1)
        placed = call("place_audio_clips", timeout=120.0, track=track_name, clips=clips,
                      name=f"{'sung' if style == 'sung' else 'talk box'} {track_name}")
        high = sum(1 for n in line if talkbox.sub_octave_level(n["pitch"]) > 0) if style == "talkbox" else 0
        result = {"vocal": placed["track"], "style": style, "words_placed": placed["placed"],
                  "next": ("Play it. It's audio now: add EQ, compression, chorus or reverb like any vocal. For "
                           "another melody or words, run it again. Mute the original melody track if it doubles it.")}
        if replace and name in names:
            result["replaced"] = f"the clips on '{name}' (its effects and sends kept)"
        if sung.get("octave"):
            result["sung_octave"] = (f"sung an octave {'down' if sung['octave'] < 0 else 'up'}, nearer the voice's "
                                     "own pitch, so the words stay clear (octave='as written' keeps the notes)")
        hnr, shift = sung.get("hnr"), sung.get("shift")
        if hnr is not None:
            result["harmonics_to_noise_db"] = hnr
            result["hnr_verdict"] = ("clean tone" if hnr >= 15 else "a little rough" if hnr >= 8 else
                                     "breathy or buzzy: another voice, or a lower melody")
        if shift is not None:
            result["shift_semitones"] = shift
            if abs(shift) > singing.WIDE_SHIFT:
                result["shift_note"] = (f"the melody sits {abs(shift):g} semitones {'above' if shift > 0 else 'below'} "
                                        "the voice's own pitch, which blurs words: a voice nearer the melody "
                                        f"({'a higher' if shift > 0 else 'a lower'} one, list_speech_voices), or "
                                        "the melody an octave nearer the voice")
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
    if style in ("talkbox", "sung") and asr.available():
        try:  # which lines a listener would mishear, from a speech recogniser (creaper[asr])
            result.update(asr.check_lines(clips, [(times[2 * i], times[2 * i + 1]) for i in range(len(clips))]))
        except Exception as e:  # noqa: BLE001  (nor a failed check)
            result["heard"] = {"error": f"couldn't check the words: {e}"}
    if rushed:
        result["note"] = (f"{len(rushed)} of {len(words)} words had to be sped up more than {RUSHED:g}x to fit "
                          "their notes, which blurs them: " + ", ".join(rushed[:12]) + (" ..." if len(rushed) > 12
                          else "") + ". Give them longer notes, or fewer words.")
    return result


SUNG_MAX_PER_BEAT = 2.0   # a sung line keeps its words clear at up to two syllables a beat


def _sing(words: list[dict], line: list[dict], times: list[float], note_times: list[float], base: float,
          folder: Path, voice: str | None, doubled: bool = True, hard: bool = False,
          auto_octave: bool = True) -> tuple[list[dict], list[str], dict]:
    """The sung clips: the whole line spoken once, cut into words, each word sung on
    its notes (singing.sing_word) with a double, and the clean word stretched the same
    way kept in speech/ for check_vocal_clarity. Returns (clips, rushed words,
    {'hnr': the median harmonics-to-noise ratio, 'shift': semitones from the voice's
    own pitch to the melody's median})."""
    import soundfile as sf

    phrase = speech.speak_phrase(" ".join(w["text"] for w in words), folder / "phrase.wav", voice)
    x, fs = speech._read(phrase)
    spoken_at = singing.own_pitch(x, fs)
    # Connected speech has no gaps to cut at: find the words by aligning the phrase with
    # the same words spoken one at a time.
    try:
        alone = [speech._read(f) for f in speech.speak([w["text"] for w in words], folder / "words", voice)]
        spans = singing.align_words(x, fs, [singing.resample(a, rate, fs) for a, rate in alone])
    except (speech.SpeechError, ValueError):
        spans = singing.split_phrase(x, fs, [0.6 * syllables(w["text"]) + 0.1 * len(w["text"]) for w in words])
    (folder / "speech").mkdir(exist_ok=True)
    median = float(np.median([n["pitch"] for n in line]))
    octave = 0
    if auto_octave and spoken_at is not None and abs(median - spoken_at) > singing.WIDE_SHIFT:
        octave = -int(round((median - spoken_at) / 12)) or (-1 if median > spoken_at else 1)
    clips, rushed, sung_all = [], [], []
    for i, (w, (a, b)) in enumerate(zip(words, spans)):
        seg = x[a:b]
        start_s, end_s = times[2 * i], times[2 * i + 1]
        seconds = max(0.05, end_s - start_s)
        notes = [(max(0.0, t - start_s), n["pitch"] + 12 * octave) for n, t in zip(line, note_times)
                 if w["start"] - 1e-6 <= n["start"] < w["end"] - 1e-6] or [(0.0, line[0]["pitch"] + 12 * octave)]
        # Hold the voiced part (a fricative held and pitched turns into a buzz).
        vowel = singing.voiced_span(seg, fs) or speech.vowel_span(seg, fs)
        sung = singing.voice_eq(singing.sing_word(seg, fs, seconds, notes, vowel, hard=hard), fs)
        if len(seg) / fs / seconds > RUSHED:
            rushed.append(w["word"])
        f = folder / f"{i + 1:03d} {speech._safe(w['text'])}.wav"
        clean = singing.psola(seg, fs, len(sung), singing.vowel_map(seg, fs, len(sung), vowel), lambda t: None)
        speech._write(folder / "speech" / f.name, clean / max(1e-9, float(abs(clean).max())) * 0.8, fs)
        sf.write(str(f), singing.double(sung, fs) if doubled else sung * 0.8 / max(1e-9, float(abs(sung).max())),
                 fs, subtype="PCM_16")
        sung_all.append(sung)
        clips.append({"path": str(f), "start_qn": base + w["start"], "end_qn": base + w["end"], "word": w["word"]})
    hnr = singing.hnr_db(np.concatenate(sung_all), fs) if sung_all else None
    shift = round(median + 12 * octave - spoken_at, 1) if spoken_at is not None else None
    return clips, rushed, {"hnr": hnr, "shift": shift, "octave": octave}


# ---------------------------------------------------------------- vocal chops

STEP_QN = 0.25  # one pattern step: a 16th note
MAX_SHIFT = 6   # semitones; further and a voice turns chipmunk or monster
# Chops come only from the sung (pitched) slices when there are at least this many: with
# one, every chop played that one slice (72 copies of one syllable).
MIN_PITCHED_SLICES = 3
# A sample this dark (spectral centroid, Hz) makes chops that sound like grunts or burps
# (Emulator II "Vocaloid", 720 Hz): they go up an octave unless the caller says otherwise.
DARK_CHOPS_HZ = 1000


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
    pitched = [i for i in usable if "pitch" in slices[i]]
    order = pitched[:] if len(pitched) >= MIN_PITCHED_SLICES else usable[:]
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
    octave: Annotated[Literal[-1, 0, 1, 2] | None, Field(description=(
        "Pitch the chops track up or down by octaves (ReaPitch, formants lifted with it). Default: up one "
        "when the sample is dark, since low dull chops sound like grunts; 0 keeps them as sung"))] = None,
    glitch: Annotated[bool, Field(description="Also bitcrush them (8-bit, half wet): glitchy, digital chops")] = False,
) -> dict:
    """Turns a real vocal sample into rhythmic vocal chops, the house / future-bass
    way: slices it at its syllables, lays the slices on a 16th-note pattern, and
    shifts each one (at most a tritone, correcting its tuning) onto the chord or key.
    A new chops track (or one with no effects) gets a chop chain: the octave shift,
    a high-pass and a low-mid dip so they sit above the bass, a little bite, and with
    glitch a bitcrusher. Later calls on that track keep its chain. Real voices beat
    robot vocals, so use this first when the user's samples have vocals. One item per
    chop, all ordinary audio to edit afterwards."""
    path = sample_tools._check_audio(path)
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
    existing = next((t for t in overview.get("tracks", []) if t["name"] == track), None)
    if existing is None:
        call("create_track", name=track)
    centroid = (analysis.analyze_file(path).get("spectrum") or {}).get("spectral_centroid_hz")
    if octave is None:
        octave = 1 if centroid and centroid < DARK_CHOPS_HZ else 0
    chain = None if existing and existing.get("fx") else chop_chain(track, octave, glitch)
    clips = []
    for c in plan:
        sl = slices[c["slice"]]
        clips.append({"path": path, "start_qn": start_qn + c["start"], "end_qn": start_qn + c["start"] + c["length"],
                      "offset": sl["start"], "semitones": c["semitones"], "word": f"chop {c['slice'] + 1}"})
    result = call("place_audio_clips", timeout=120.0, track=track, clips=clips, name="vocal chops")
    shifts = [abs(c["semitones"]) for c in plan]
    result.update({"slices_found": len(slices), "pitched_slices": sum("pitch" in s for s in slices),
                   "slices_used": len({c["slice"] for c in plan}),
                   "chops": len(plan), "largest_shift": max(shifts) if shifts else 0,
                   "fit_to": "chords" if (chords or chords_item) else ("key" if key else "unchanged pitch"),
                   "sample_brightness_hz": round(centroid) if centroid else None})
    if chain is not None:
        result["chain"] = chain
        if octave > 0 and centroid and centroid < DARK_CHOPS_HZ:
            result["why_octave"] = (f"the sample is dark ({centroid:.0f} Hz centroid): low, dull chops sound like "
                                    "grunts. octave=0 keeps them as sung")
    else:
        result["chain"] = "kept the track's own effects"
    return result


def chop_chain(track: str, octave: int, glitch: bool) -> list[str]:
    """Effects for a chops track: ReaPitch by octaves (formants lifted part of the way,
    so they turn machine-like rather than chipmunk), ReaEQ (high-pass 300 Hz, -4 dB at
    600 Hz where a dull voice burps, +2 dB at 3.5 kHz) and with glitch an 8-bit crusher
    half wet. What fixed chops the user heard as burping."""
    chain = []
    if octave:
        fx = call("add_fx", track=track, name="ReaPitch")
        call("set_fx_parameters", track=track, fx=fx["index"], changes=[
            {"parameter": "1: Shift (oct)", "display_value": octave},
            {"parameter": "1: Formant adjust (semitones)", "display_value": 5 * (1 if octave > 0 else -1)}])
        chain.append(f"{fx['name']}: {octave:+d} octave")
    fx = call("add_fx", track=track, name="ReaEQ")
    call("set_fx_parameters", track=track, fx=fx["index"], changes=[
        {"parameter": "Freq-High Pass 5", "display_value": 300},
        {"parameter": "Freq-Band 2", "display_value": 600}, {"parameter": "Gain-Band 2", "display_value": -4},
        {"parameter": "BW-Band 2", "display_value": 1.2},
        {"parameter": "Freq-Band 3", "display_value": 3500}, {"parameter": "Gain-Band 3", "display_value": 2}])
    chain.append(f"{fx['name']}: high-pass 300 Hz, -4 dB at 600 Hz, +2 dB at 3.5 kHz")
    if glitch:
        fx = call("add_fx", track=track, name="JS: Bit Reduction/Dither")
        call("set_fx_parameters", track=track, fx=fx["index"], changes=[
            {"parameter": "Resolution (bits)", "display_value": 8}, {"parameter": "Dither", "display_text": "Off"},
            {"parameter": "Wet", "display_value": 55}])
        chain.append(f"{fx['name']}: 8-bit, 55% wet")
    return chain


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
    "VocalVST": ("vocalvst", "load it as the melody track's instrument and call render_vocalvst(track, lyrics): nothing to import"),
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


# ------------------------------------------------------------------ VocalVST

# VocalVST (the user's own singing plugin) can't sing live: it records the notes that
# pass through it while the transport plays, keeps them with the lyrics in its state,
# and renders the phrase offline when its Render switch is set. The rendered vocal then
# plays wherever the transport (or an offline render) crosses the captured region.
JUCE_STATE_MAGIC = b"VC2!"     # JUCE's copyXmlToBinary header, as REAPER stores it in the VST3 state
VOCALVST_LOG = Path(os.environ.get("APPDATA") or (Path.home() / "AppData/Roaming")) / "VocalVST" / "host.log"
_sleep = time.sleep


def _xml_attr(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def vocalvst_state(chunk: str) -> tuple[bytes, int, int, str]:
    """REAPER's base64 state of a VocalVST instance, taken apart: the raw bytes, where
    the plugin's XML block starts and how long it is, and the XML text."""
    raw = base64.b64decode(chunk)
    at = raw.find(JUCE_STATE_MAGIC)
    if at < 0 or at + 8 > len(raw):
        raise ValueError("VocalVST's state isn't in the form creaper knows (a JUCE XML block)")
    (n,) = struct.unpack_from("<I", raw, at + 4)
    xml = raw[at + 8: at + 8 + n].rstrip(b"\x00").decode("utf-8", errors="replace")
    if "<VocalVST" not in xml:
        raise ValueError("that plugin's state isn't VocalVST's")
    return raw, at, n, xml


def vocalvst_state_with(chunk: str, **attrs: str) -> str:
    """The same state with its top-level attributes (lyrics, bank) replaced; everything
    else (the captured notes, the parameters) stays. REAPER's leading length word
    covers the XML block, so it grows or shrinks with it."""
    raw, at, n, xml = vocalvst_state(chunk)
    for name, value in attrs.items():
        pattern = r'(<VocalVST[^>]*\s' + name + r'=)"[^"]*"'
        if not re.search(pattern, xml):
            raise ValueError(f"VocalVST's state has no {name} field; is this a newer plugin?")
        xml = re.sub(pattern, lambda m: m.group(1) + '"' + _xml_attr(value) + '"', xml, count=1)
    block = xml.encode("utf-8") + b"\x00"
    out = bytearray(raw[: at + 4])
    out += struct.pack("<I", len(block)) + block + raw[at + 8 + n:]
    if at >= 4:
        (first,) = struct.unpack_from("<I", raw, 0)
        if first >= 8 + n:
            struct.pack_into("<I", out, 0, first + len(block) - n)
    return base64.b64encode(bytes(out)).decode("ascii")


def vocalvst_state_with_lyrics(chunk: str, lyrics: str) -> str:
    return vocalvst_state_with(chunk, lyrics=lyrics)


def vocalvst_attr(chunk: str, name: str) -> str:
    m = re.search(r'<VocalVST[^>]*\s' + name + r'="([^"]*)"', vocalvst_state(chunk)[3])
    text = m.group(1) if m else ""
    return text.replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def vocalvst_lyrics(chunk: str) -> str:
    return vocalvst_attr(chunk, "lyrics")


def vocalvst_bank(chunk: str) -> str:
    """The voicebank folder the plugin instance uses ("" when it has none: then Render
    does nothing and says so only in its window)."""
    return vocalvst_attr(chunk, "bank")


VOICEBANK_ROOT = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData/Local")) / "VocalVST" / "voicebanks"


def voicebank_roots() -> list[Path]:
    """Where voicebanks can be: VocalVST's own folder, and the same folder inside a
    packaged app's AppData cache. The Claude desktop app is one: files its sessions
    write under AppData land in %LOCALAPPDATA%\\Packages\\<app>\\LocalCache, which those
    sessions read back at the normal path while REAPER sees only the real one."""
    roots = [VOICEBANK_ROOT]
    local = VOICEBANK_ROOT.parents[1]
    try:
        roots += sorted(local.glob("Packages/*/LocalCache/Local/VocalVST/voicebanks"))
    except OSError:
        pass
    return roots


def find_voicebanks() -> list[Path]:
    """DiffSinger voicebanks (a folder whose dsconfig.yaml names an acoustic model), in
    every root, VocalVST's own folder first."""
    found: list[Path] = []
    for root in voicebank_roots():
        if not root.is_dir():
            continue
        for folder in [root, *sorted(root.iterdir())]:
            cfg = folder / "dsconfig.yaml"
            try:
                if cfg.is_file() and "acoustic" in cfg.read_text(encoding="utf-8", errors="replace"):
                    found.append(folder)
            except OSError:
                continue
    return found


def find_voicebank() -> Path | None:
    banks = find_voicebanks()
    return banks[0] if banks else None


def vocalvst_captured(chunk: str) -> dict:
    """The notes the plugin has recorded from the transport: how many, and their span
    in seconds."""
    xml = vocalvst_state(chunk)[3]
    starts = [float(s) for s in re.findall(r'<n s="([^"]+)"', xml)]
    ends = [float(e) for e in re.findall(r'<n s="[^"]+" e="([^"]+)"', xml)]
    return {"notes": len(starts), "from_seconds": round(min(starts), 3) if starts else None,
            "to_seconds": round(max(ends), 3) if ends else None}


def _vocalvst_fx(track: str | int) -> tuple[dict, list[dict]]:
    details = call("get_track_details", track=track)
    fx = next((f for f in details.get("fx", []) if "vocalvst" in (f.get("name") or "").lower()), None)
    if fx is None:
        raise ValueError(f"track {details.get('number', track)} \"{details.get('name', '')}\" has no VocalVST on it: "
                         "create_track(name, instrument='VocalVST') or add_fx it first")
    items = sorted((i for i in details.get("items", []) if i.get("type") == "midi" and not i.get("muted")),
                   key=lambda i: i["start"]["seconds"])
    if not items:
        raise ValueError("the track has no (unmuted) MIDI item for VocalVST to sing: write the melody first "
                         "(one note per syllable, no chords)")
    return fx, items


def _wait_for_stop(expected_seconds: float) -> None:
    deadline = time.monotonic() + expected_seconds + 20
    while time.monotonic() < deadline:
        _sleep(0.5)
        if not call("recording_status").get("playing"):
            return
    call("transport", action="stop")
    raise ValueError("REAPER didn't reach the end of the pass in time; it was stopped. Try again")


def _track_audio(track: str | int, start: float, end: float) -> tuple[bool, bytes]:
    """Whether the track sounds over a span (rendered offline), and a digest of that audio."""
    import hashlib

    import soundfile as sf

    # Straight to the bridge: server.call treats an all-silent render as offline media and
    # re-renders after a slow action, but silence is expected here before the first take.
    render = bridge.call("render_audio", {"track": track, "start_seconds": start, "end_seconds": end}, timeout=300.0)
    files = list(render.get("files") or [])
    renders = (bridge.directory / "renders").resolve()
    sounding, digest = False, hashlib.sha1()
    try:
        for f in files:
            if renders not in Path(f).resolve().parents:
                raise ValueError(f"refusing to read a render outside {renders}: {f}")
            audio, _ = sf.read(f, dtype="float32", always_2d=True)
            sounding = sounding or bool(np.abs(audio).max() > 10 ** (-60 / 20))
            digest.update(np.round(audio, 4).tobytes())
    finally:
        if not os.environ.get("CREAPER_KEEP_RENDERS"):
            for f in files:
                Path(f).unlink(missing_ok=True)
    return sounding, digest.digest()


def _new_log_line(log_size: int) -> str | None:
    if not VOCALVST_LOG.exists():
        return None
    with VOCALVST_LOG.open("rb") as f:
        f.seek(log_size)
        new = f.read().decode("utf-8", errors="replace")
    for line in new.splitlines():
        line = line.strip()
        if line and " loaded in " not in line:
            return line.split(" ", 1)[1] if " " in line else line
    return None


def _wait_for_render_switch(track: str | int, fx: int, seconds: float = 10.0) -> None:
    """The plugin's Render switch resets itself the moment its timer sees it; one that
    stays on isn't running, and waiting for its result would be a waste."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        _sleep(1.0)
        params = call("get_fx_parameters", track=track, fx=fx, search="Render").get("parameters", [])
        render = next((p for p in params if p.get("name") == "Render"), None)
        if render is None or str(render.get("display", "")).lower() == "off" or float(render.get("value") or 0) < 0.5:
            return
    raise ValueError("VocalVST never took its Render switch (it stays On), so the plugin isn't running its timer "
                     "in this REAPER and no render will come. Open its window (update_fx with show=True) and press "
                     "Render there, or restart REAPER; its own host.log says whether a render happened")


def _wait_for_render(log_size: int, timeout: float, before: tuple[bool, bytes], audio) -> str:
    """The plugin's result line from its log; failing that, the track's audio changing
    (a plugin that can't write its log still plays what it rendered)."""
    deadline = time.monotonic() + timeout
    next_render = time.monotonic() + 15
    while time.monotonic() < deadline:
        _sleep(1.0)
        line = _new_log_line(log_size)
        if line:
            return line
        if time.monotonic() >= next_render:
            next_render = time.monotonic() + 10
            sounding, digest = audio()
            if (sounding and not before[0]) or (sounding and digest != before[1]):
                return "Rendered (the track plays the new take; the plugin wrote nothing to its log)"
    raise ValueError(f"VocalVST reported nothing in {timeout:.0f} s and the track's audio didn't change. Open its "
                     "window (update_fx with show=True) to read its status: 'No voicebank' means its Voicebank "
                     "button needs the voicebank folder (under %LOCALAPPDATA%\\VocalVST\\voicebanks); "
                     "'Rendering...' or 'Loading voicebank...' means it needs longer (timeout_seconds, more on the "
                     "first render). Calling again without changing anything only waits again")


@tool()
def render_vocalvst(
    track: TrackRef,
    lyrics: Annotated[str | None, Field(description=(
        "The words, one syllable per note: 'dan-cing in the dark _' (hyphens split syllables, '_' holds the note "
        "before). Leave it out for a wordless line: scat syllables in scat mode, 'la' otherwise"))] = None,
    mode: Annotated[Literal["sing", "rap", "scat"], Field(description="sing: pitched, vibrato on held notes; rap: spoken contour, syllables cut to about 220 ms; scat: nonsense syllables when there are no lyrics")] = "sing",
    timeout_seconds: Annotated[float, Field(ge=30, le=900, description="How long to wait for the render")] = 240,
) -> dict:
    """Makes VocalVST (the user's singing plugin) sing the MIDI on its track: sets the
    lyrics and mode, plays the transport over the item so the plugin records the notes
    (it can't sing live: audition_instrument hears silence), then renders the phrase
    offline and waits for the result. Afterwards the vocal plays in sync with the
    transport and in offline renders (analyze_audio, export_mix). It's a clean sung
    voice: for growls or shrieks add distortion after it. Call it again after the notes
    or lyrics change, and after reopening a saved project (the capture is saved, the
    rendered audio isn't). Needs a monophonic line: one note per syllable, no chords."""
    fx, items = _vocalvst_fx(track)
    line: list[dict] = []
    for item in items:
        line += melody_line(call("get_midi_notes", item_id=item["id"], limit=20000).get("notes", []))
    if not line:
        raise ValueError("the track's MIDI items have no notes to sing")
    text = " ".join(singer_syllables(lyrics, line, hold="+")) if lyrics else ""

    state = call("capture_fx_state", track=track, fx=fx["index"])
    if not state.get("chunk"):
        raise ValueError("REAPER gave no state for VocalVST, so its lyrics can't be set")
    changes: dict[str, str] = {}
    if vocalvst_lyrics(state["chunk"]) != text:
        changes["lyrics"] = text
    bank = vocalvst_bank(state["chunk"])
    candidates: list[str] = []
    if not bank or not (Path(bank) / "dsconfig.yaml").is_file():
        # Without a voicebank Render does nothing, and the plugin says so only in its
        # window; it takes the folder from its state, like the lyrics. The plugin keeps
        # only a folder it can see itself, so each candidate is offered until one sticks.
        candidates = [str(b) for b in find_voicebanks()]
        if not candidates:
            raise ValueError(f"VocalVST has no voicebank, so it can't render: none found under {VOICEBANK_ROOT} "
                             "(the plugin's setup script installs Canary there), and its window's Voicebank "
                             "button is the other way to choose one. Don't call again until one is in place")
    for attempt, candidate in enumerate(candidates or [None]):
        if candidate:
            changes["bank"] = candidate
        if not changes:
            break
        call("apply_fx_state", track=track, fx=fx["index"], sound_name="VocalVST " + " and ".join(changes),
             state={"plugin": state.get("plugin"), "file": state.get("file"),
                    "chunk": vocalvst_state_with(state["chunk"], **changes)})
        after = call("capture_fx_state", track=track, fx=fx["index"])["chunk"]
        if vocalvst_lyrics(after) != text:
            raise ValueError("VocalVST didn't take the lyrics; type them in its window (update_fx show=True) "
                             "and call again without lyrics")
        if not candidate:
            break
        bank = vocalvst_bank(after)
        if bank:
            break
        if attempt == len(candidates) - 1:
            raise ValueError("VocalVST didn't accept any voicebank folder it was given (" + ", ".join(candidates)
                             + "): the plugin can't see them from REAPER. Move the voicebank to "
                             + str(VOICEBANK_ROOT) + " in Explorer, or choose it with the Voicebank button in "
                             "the plugin's window (update_fx with show=True), then call again")
    call("set_fx_parameter", track=track, fx=fx["index"], parameter="Mode", display_text=mode.capitalize())

    # The pass: the plugin records only what the transport plays through it, by position.
    start = max(0.0, items[0]["start"]["seconds"] - 0.3)
    end = max(i["end"]["seconds"] for i in items) + 0.5
    call("transport", action="play", start_seconds=start, end_seconds=end)
    _wait_for_stop(end - start)
    captured = vocalvst_captured(call("capture_fx_state", track=track, fx=fx["index"])["chunk"])
    if not captured["notes"]:
        raise ValueError("VocalVST recorded no notes during the pass: check the track isn't muted, the item is "
                         "on it and the plugin is enabled, then call again")

    log_size = VOCALVST_LOG.stat().st_size if VOCALVST_LOG.exists() else 0
    span = (captured["from_seconds"], captured["to_seconds"] + 1.0)
    before = _track_audio(track, *span)
    call("set_fx_parameter", track=track, fx=fx["index"], parameter="Render", display_text="On")
    _wait_for_render_switch(track, fx["index"])
    report = _wait_for_render(log_size, timeout_seconds, before, lambda: _track_audio(track, *span))
    out = {"track": track, "mode": mode, "lyrics": text or None, "written_notes": len(line), "captured": captured,
           "voicebank": Path(bank).name, "result": report,
           "plays": "in sync with the transport over the captured region, and in offline renders (analyze_audio, "
                    "measure_tracks, export_mix); not in audition_instrument",
           "next": "check it with analyze_audio(track) or check_vocal_clarity; render again after any change "
                   "to the notes or lyrics"}
    if not report.startswith("Rendered"):
        out["warning"] = "the plugin reports: " + report
    if captured["notes"] != len(line):
        out["note"] = (f"the plugin captured {captured['notes']} notes but the items hold {len(line)}: overlapping "
                       "notes are cut and chords keep their top note, so the syllables may have shifted")
    without = re.search(r"(\d+) notes without lyrics", report)
    if lyrics and without and int(without.group(1)):
        out["warning"] = without.group(1) + " notes got no syllable and sing la: fewer syllables than captured notes"
    return out
