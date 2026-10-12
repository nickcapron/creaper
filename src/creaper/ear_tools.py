"""MCP tools that stand in for ears: how understandable a vocal is (alone and in the
mix), whether a part is in tune, and a picture of the sound to look at."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

import numpy as np
import soundfile as sf
from pydantic import Field

from . import harmony, perception
from .server import READ_ONLY, Bar, BridgeError, bridge, call, tool
from .vocal_tools import melody_line

try:  # mcp 2.x
    from mcp.server.mcpserver import Image
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import Image


def _render(track: str | int, start_bar: float | None, end_bar: float | None) -> tuple[np.ndarray, int, dict]:
    """Renders a track (or "master") and returns its audio (frames x channels), sample
    rate and the render's range. Only files in creaper's own render folder are read."""
    render = call("render_audio", timeout=900.0, track=track, start_bar=start_bar, end_bar=end_bar)
    renders = (bridge.directory / "renders").resolve()
    try:
        for f in render["files"]:
            if renders not in Path(f).resolve().parents:
                raise BridgeError(f"refusing to use a render outside {renders}: {f}")
        audio, fs = sf.read(render["files"][0], always_2d=True)
    finally:
        if not os.environ.get("CREAPER_KEEP_RENDERS"):
            for f in render["files"]:
                Path(f).unlink(missing_ok=True)
    return audio, int(fs), render


def _bars_of(seconds: list[float]) -> list[dict]:
    return call("time_to_positions", times=seconds) if seconds else []


# ------------------------------------------------------------------ clarity

def _speech_clips(track: str | int) -> tuple[str, list[dict]]:
    """The clean spoken words behind a robot vocal track: (track measured, clips with
    start/length in seconds and the speech file)."""
    details = call("get_track_details", track=track)
    items = [i for i in details.get("items", []) if i.get("file")]
    measured = details["name"]
    if not items:  # a vocoder vocal: the words are on its Voice track
        voice = call("get_track_details", track=f"{details['name']} Voice")
        items = [i for i in voice.get("items", []) if i.get("file")]
    clips = []
    for i in items:
        f = Path(i["file"])
        clean = f.parent / "speech" / f.name
        clips.append({"start": i["start"]["seconds"], "length": i["length_seconds"],
                      "file": str(clean if clean.exists() else f)})
    if not clips:
        raise ValueError(f"'{measured}' has no spoken words to compare with (is it an add_robot_vocal track?)")
    return measured, clips


def _clean_timeline(clips: list[dict], start: float, frames: int, fs: int) -> np.ndarray:
    clean = np.zeros(frames)
    for c in clips:
        x, rate = sf.read(c["file"], always_2d=True)
        x = perception._resample(x.mean(axis=1), rate, fs)[: int(c["length"] * fs)]
        a = int(round((c["start"] - start) * fs))
        if a >= frames or a + len(x) <= 0:
            continue
        lo, hi = max(0, a), min(frames, a + len(x))
        clean[lo:hi] += x[lo - a: hi - a]
    return clean


def measure_vocal_clarity(track: str | int, start_bar: float | None = None, end_bar: float | None = None,
                          in_mix: bool = True) -> dict:
    measured, clips = _speech_clips(track)
    if start_bar is None and end_bar is None:
        first = min(c["start"] for c in clips)
        last = max(c["start"] + c["length"] for c in clips)
        span = _bars_of([first, last])
        start_bar, end_bar = span[0]["bar"], span[1]["bar"] + 1
    out: dict = {"track": measured}
    for label, source in (("alone", measured), ("in_mix", "master")):
        if label == "in_mix" and not in_mix:
            continue
        audio, fs, render = _render(source, start_bar, end_bar)
        heard = audio.mean(axis=1)
        clean = _clean_timeline(clips, render["start"]["seconds"], len(heard), fs)
        score = perception.intelligibility(clean, heard, fs)
        out[label] = {"score": None if score is None else round(score, 3)}
    alone = (out.get("alone") or {}).get("score")
    mixed = (out.get("in_mix") or {}).get("score")
    if alone is not None:
        out["alone"]["verdict"] = perception.robot_clarity_verdict(alone)
    if mixed is not None and alone is not None:
        out["in_mix"]["verdict"] = perception.masking_verdict(alone - mixed)
    tips = []
    if alone is not None and alone < 0.72:
        tips.append("the vocal itself is blurred: fewer, longer words; a lower melody (below about E4); "
                    "style='talkbox'; another voice (list_speech_voices)")
    if alone is not None and mixed is not None and alone - mixed > 0.03:
        tips.append("the mix is covering it: turn the vocal up, or turn down / cut 1-4 kHz on parts playing "
                    "with it (busy keys, leads, hats), or duck them under the vocal (setup_sidechain)")
    if tips:
        out["tips"] = tips
    out["scale"] = ("STOI against the clean words. Robot vocals score lower than plain speech even when understood: "
                    "a talk box of clear words scores about 0.72-0.78. In the mix, a drop of more than 0.03 from "
                    "'alone' means other parts are covering the words.")
    return out


@tool(annotations=READ_ONLY)
def check_vocal_clarity(
    track: Annotated[str | int, Field(description="A robot vocal track (from add_robot_vocal)")],
    start_bar: Bar = None,
    end_bar: Annotated[float | None, Field(description="Default: where its words are")] = None,
    in_mix: Annotated[bool, Field(description="Also measure it in the full mix (renders the master)")] = True,
) -> dict:
    """How understandable a robot vocal's words are, alone and in the full mix, using
    STOI (the standard intelligibility measure) against the clean spoken words. Use it
    instead of guessing: if it's clear alone but not in the mix, the mix is burying it;
    if it's unclear alone, change the words, notes, voice or style."""
    return measure_vocal_clarity(track, start_bar, end_bar, in_mix)


# ------------------------------------------------------------------- tuning

@tool(annotations=READ_ONLY)
def check_tuning(
    track: Annotated[str | int, Field(description="The track to check")],
    start_bar: Bar = None,
    end_bar: Annotated[float | None, Field(description="Default: the end of the project")] = None,
    key: Annotated[str | None, Field(description="Audio tracks (no MIDI): the song's key, e.g. 'F# minor'")] = None,
    chords_item: Annotated[str | None, Field(description="Audio tracks: or a MIDI item with the chords to check against")] = None,
) -> dict:
    """Is a part in tune? Renders the track and measures what actually sounds. For a
    MIDI part: each held note's pitch against the note played (cents off; a detuned
    patch, vibrato or glide shows up). For audio (vocals, samples, chops): how far its
    pitches sit from the nearest semitone (a detuned sample) and how many fall outside
    the key or chords. Mono lines measure best; chords are judged by their top note."""
    details = call("get_track_details", track=track)
    audio, fs, render = _render(track, start_bar, end_bar)
    mono = audio.mean(axis=1)
    t0 = render["start"]["seconds"]
    midi_items = [i for i in details.get("items", []) if i.get("type") == "midi"]
    if midi_items:
        notes = []
        for it in midi_items:
            data = call("get_midi_notes", item_id=it["id"], limit=20000)
            line = melody_line(data.get("notes", []))
            base = data["start"]["qn"]
            qns = [q for n in line for q in (base + n["start"], base + n["start"] + n["length"])]
            times = call("qn_to_times", qns=qns) if qns else []
            notes += [{"start": times[2 * k] - t0, "end": times[2 * k + 1] - t0, "pitch": n["pitch"]}
                      for k, n in enumerate(line)]
        notes = [n for n in notes if n["start"] >= 0 and n["end"] <= len(mono) / fs]
        heard = perception.note_pitches(mono, fs, notes)
        if not heard:
            return {"track": details["name"], "result": "no held notes with a clear pitch in that range"}
        cents = [h["cents"] for h in heard]
        off = sorted((h for h in heard if abs(h["cents"]) > 25), key=lambda h: -abs(h["cents"]))
        positions = _bars_of([t0 + h["start"] for h in off[:8]])
        return {"track": details["name"], "notes_measured": len(heard), "median_cents": int(np.median(cents)),
                "spread_cents": [min(cents), max(cents)], "notes_off_by_25_cents_or_more": len(off),
                "worst": [{"bar": p["bar"], "beat": p["beat"], "cents": h["cents"]} for h, p in zip(off, positions)],
                "verdict": ("in tune" if not off and abs(np.median(cents)) <= 10 else
                            "the whole part is detuned (check the instrument's tune/fine controls)"
                            if abs(np.median(cents)) > 15 else "some notes are off (glide, vibrato, or bends?)")}
    frames = perception.pitch_classes_heard(mono, fs)
    if not frames:
        return {"track": details["name"], "result": "no clear pitches in that range (unpitched or too quiet)"}
    detune = [round((f["pitch"] - round(f["pitch"])) * 100) for f in frames]
    out = {"track": details["name"], "pitched_moments": len(frames), "median_detune_cents": int(np.median(detune))}
    allowed_at = None
    if chords_item:
        from .composer import chord_lookup
        data = call("get_midi_notes", item_id=chords_item, limit=20000)
        times = call("qn_to_times", qns=[data["start"]["qn"] + n["start"] for n in data["notes"]] or [0])
        ends = call("qn_to_times", qns=[data["start"]["qn"] + n["start"] + n["length"] for n in data["notes"]] or [0])
        lookup = chord_lookup([{"pitch": n["pitch"], "start": s - t0, "length": e - s}
                               for n, s, e in zip(data["notes"], times, ends)], hold=2.0)
        allowed_at = lookup
    elif key:
        scale = harmony.parse_key(key).pitch_classes()
        allowed_at = lambda t: scale  # noqa: E731
    if allowed_at:
        judged = [(f, allowed_at(f["time"])) for f in frames]
        outside = [f for f, pcs in judged if pcs and round(f["pitch"]) % 12 not in pcs]
        out["outside_share"] = round(len(outside) / max(1, sum(1 for _, p in judged if p)), 2)
        out["outside_at"] = [{"bar": p["bar"], "beat": p["beat"]} for p in _bars_of([t0 + f["time"] for f in outside[:8]])]
    detuned = abs(out["median_detune_cents"]) > 20
    clashing = out.get("outside_share", 0) > 0.25
    out["verdict"] = ("detuned by about %d cents: shift it (edit_item pitch_semitones, e.g. %.2f)"
                      % (out["median_detune_cents"], -out["median_detune_cents"] / 100) if detuned else
                      "many pitches fall outside the chords/key" if clashing else "in tune")
    return out


# --------------------------------------------------------------- spectrogram

@tool(annotations=READ_ONLY)
def show_spectrogram(
    track: Annotated[str | int, Field(description='"master" for the mix, or a track')] = "master",
    start_bar: Bar = None,
    end_bar: Annotated[float | None, Field(description="Default: the end of the project")] = None,
):
    """A picture of the sound to look at, since you can't hear it: time left to right,
    frequency bottom (30 Hz) to top (16 kHz, log scale), loudness as colour (black
    quiet, purple/orange mid, yellow loud). Faint horizontal lines mark 100 Hz, 1 kHz
    and 10 kHz; white vertical lines mark section starts. Read it for: mud (a solid
    band at 200-500 Hz), harshness (bright 2-5 kHz), empty or crowded sections,
    clipping or pumping, a vocal masked by other parts, sections that look identical."""
    audio, fs, render = _render(track, start_bar, end_bar)
    t0, t1 = render["start"]["seconds"], render["end"]["seconds"]
    overview = call("get_project_overview")
    sections = [r for r in overview.get("regions", []) + overview.get("markers", [])
                if t0 <= r["start"]["seconds"] < t1]
    sections.sort(key=lambda r: r["start"]["seconds"])
    png = perception.spectrogram_png(audio, fs, lines=[r["start"]["seconds"] - t0 for r in sections])
    legend = {
        "measured": render.get("track"), "from": render["start"], "to": render["end"],
        "width_is": f"{t1 - t0:.1f} s, left to right",
        "white_lines": [{"section": r["name"], "bar": r["start"]["bar"],
                         "at_fraction": round((r["start"]["seconds"] - t0) / (t1 - t0), 3)} for r in sections],
        "rows": "bottom 30 Hz, lines at 100 Hz (lower), 1 kHz (middle), 10 kHz (upper), top 16 kHz",
    }
    return [legend, Image(data=png, format="png")]
