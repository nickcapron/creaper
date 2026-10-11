"""MCP tools for robot vocals: the computer's own voice speaks the lyrics, one clip per
word under the melody's notes, and a vocoder makes a synth playing the melody sing
them (the talk-box / vocoder hook of house, French touch and electro)."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Annotated

from pydantic import Field

from . import speech
from .server import READ_ONLY, ItemId, call, tool

# Notes starting this close together (in QN) count as one onset: the top one sings.
ONSET_TOLERANCE = 1 / 64


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
    ReaVocode shapes a synth playing the melody (chords too) with that speech.
    Builds three tracks after the melody's track: the vocal (the one you hear), its
    voice (the spoken words, stretched to the notes) and its carrier (the synth). Write
    the melody first: a clear, mostly one-note-per-syllable line sings best."""
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
    clips = [{"path": str(f), "start_qn": base + w["start"], "end_qn": base + w["end"], "word": w["word"]}
             for f, w in zip(files, words)]
    result = call("build_robot_vocal", timeout=120.0, melody_item=item_id, clips=clips, name=name,
                  carrier=carrier, bands=bands)
    result["speech_voice"] = chosen or "system default"
    result["word_files"] = str(folder)
    result["next"] = ("Play it. If words are hard to make out: more bands, a brighter carrier (saw, filter open), "
                      "or fewer syllables per beat. Mute the original melody track if it doubles the vocal.")
    if result.get("squeezed"):
        result["note"] = ("These words are long for their notes and got cut short: "
                          + ", ".join(result["squeezed"]) + ". Give them longer notes or more notes.")
    return result
