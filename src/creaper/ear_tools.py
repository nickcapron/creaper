"""MCP tools that stand in for ears: how understandable a vocal is (alone and in the
mix), whether a part is in tune, and a picture of the sound to look at."""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Annotated, Callable, Literal

import numpy as np
import soundfile as sf
from pydantic import Field

from . import analysis, genres, harmony, perception, structure
from .server import READ_ONLY, Bar, BridgeError, bridge, call, tool
from . import vocal_tools  # the module, not its names: it may still be loading (circular import)

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
            line = vocal_tools.melody_line(data.get("notes", []))
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


# ------------------------------------------------------------------- endings

@tool(annotations=READ_ONLY)
def check_ending(
    kind: Annotated[Literal["continuous", "ending", "stinger"], Field(description=(
        "continuous: the piece flows into the next one (a game crossfading tracks, a DJ mix): it must not fade out "
        "or end in silence. ending: a real ending that dies away. stinger: a short cue with a hard stop"))] = "continuous",
    tail_seconds: Annotated[float, Field(ge=0, le=30, description="The tail you'll export with (export_mix tail_seconds)")] = 0.0,
    region: Annotated[str | None, Field(description=(
        "Check this region (by name) instead of the whole project's end, e.g. one of several stingers in one "
        "project, exported with export_mix region="))] = None,
) -> dict:
    """Checks how the song ends against how it will be used, by rendering its last
    16 seconds (plus the export tail) and measuring the level: a fade-out, a quiet or
    silent end, a tail cut off mid-ring, or a stinger that lingers. Also reports the
    song's length. With region, checks that region (its length and its end) instead."""
    overview = call("get_project_overview")
    start, end = 0.0, overview["length"]["seconds"]
    if region:
        found = [r for r in overview.get("regions", []) if r.get("name", "").lower() == region.lower()]
        if not found:
            names = ", ".join(r["name"] for r in overview.get("regions", [])) or "none"
            raise ValueError(f"there's no region called '{region}' (regions: {names})")
        start, end = found[0]["start"]["seconds"], found[0]["end"]["seconds"]
    length = end - start
    if length <= 0:
        raise ValueError("the project is empty" if not region else f"the region '{region}' is empty")
    window = min(16.0, length)
    render = call("render_audio", timeout=600.0, track="master", start_seconds=end - window, end_seconds=end,
                  tail_seconds=tail_seconds)
    renders = (bridge.directory / "renders").resolve()
    try:
        for f in render["files"]:
            if renders not in Path(f).resolve().parents:
                raise BridgeError(f"refusing to use a render outside {renders}: {f}")
        audio, fs = sf.read(render["files"][0], always_2d=True)
    finally:
        for f in render["files"]:
            Path(f).unlink(missing_ok=True)
    prof = perception.ending_profile(audio, int(fs))
    total = length + tail_seconds
    out: dict = {"kind": kind, "length": f"{int(total // 60)}:{int(total % 60):02d}",
                 **({"region": region, "length_seconds": round(total, 2)} if region else {}), **prof}
    problems, tips = [], []
    drop = prof.get("end_vs_loudest_db")
    silence = prof.get("trailing_silence_s", 0)
    if kind == "continuous":
        if silence >= 0.5:
            problems.append(f"it ends with {silence:g} s of silence")
            tips.append("end the project on the last bar line (or trim the silence) and export with tail_seconds=0")
        if drop is not None and drop < -6:
            problems.append(f"its final 2 seconds are {-drop:g} dB quieter than its loudest moment just before: "
                            "a fade-out")
            tips.append("keep the last section's parts playing to the end at full level; remove fade-out "
                        "automation or item fades on the final bar (if the end is meant to be a quieter section, "
                        "it still mustn't die away)")
    elif kind == "ending":
        if prof.get("abrupt"):
            problems.append("it stops while still ringing: the tail is cut off")
            tips.append("export with a longer tail_seconds (4-8 s for a long final chord), or let the last chord "
                        "ring longer before the project's end")
        elif silence < 0.3 and prof.get("final_50ms_db_below_peak", 99) < 40:
            problems.append("it doesn't quite reach silence")
            tips.append("give the final chord time to die away (a longer tail or a fade on the last chord)")
    else:
        if not 5 <= total <= 15:
            problems.append(f"it's {total:.1f} s long; stingers are usually 5-15 s")
        if silence >= 0.3:
            problems.append(f"{silence:g} s of silence after the hit")
            tips.append("trim the end right after the final hit's decay")
    out["verdict"] = "fine for its use" if not problems else "; ".join(problems)
    if tips:
        out["tips"] = tips
    return out


# ------------------------------------------------------------ many tracks

def _parts(overview: dict) -> list[int]:
    """Tracks to measure by default: every unmuted track with items, but a layered part
    ('<part> (layered)' folder) as one, through its folder."""
    names = {t["name"] for t in overview["tracks"]}
    layered = {n for n in names if n.endswith(" (layered)")}
    if not layered:
        return [t["number"] for t in overview["tracks"] if t.get("item_count") and not t.get("mute")]
    inside = {r["name"] for r in call("get_routing")["tracks"] if r.get("in_folder") in layered}
    return [t["number"] for t in overview["tracks"] if not t.get("mute") and (
        t["name"] in layered or (t.get("item_count") and t["name"] not in inside))]


def _playing_lufs(audio: np.ndarray, fs: int) -> float | None:
    """How loud a stretch is while it plays: max short-term LUFS (max momentary when
    it's under 3 s); None when it's silent."""
    loud = analysis.loudness(audio, fs)
    value = loud.get("max_short_term_lufs", loud.get("max_momentary_lufs"))
    return value if value is not None and value > -70 else None


def _sections(regions: list[dict], start: float, end: float) -> list[dict]:
    """Regions inside [start, end) seconds, clipped to it, with unique names (a second
    'Chorus' becomes 'Chorus (2)')."""
    out, seen = [], {}
    for r in sorted(regions, key=lambda r: r["start"]["seconds"]):
        a, b = max(r["start"]["seconds"], start), min(r["end"]["seconds"], end)
        if b - a < 0.4:
            continue
        name = r.get("name") or "(unnamed)"
        seen[name] = seen.get(name, 0) + 1
        out.append({"name": name if seen[name] == 1 else f"{name} ({seen[name]})", "start": a, "end": b})
    return out


def _lane_names(item_id: str) -> Callable[[int, int], str]:
    """Names a drum hit by its pitch and channel the way add_drum_pattern resolves
    lanes: a saved drum map, the instrument's own note names, then General MIDI."""
    from .server import drum_maps
    from .theory import GM_DRUMS, midi_to_note

    context = call("get_instrument_notes", item_id=item_id, channel=10)
    names = {n["pitch"]: n["name"] for n in context.get("note_names", []) if n.get("name")}
    saved = drum_maps.find(context.get("instrument"))
    by_key: dict[tuple, str] = {}
    for lane, entry in (saved[1] if saved else {}).items():
        by_key.setdefault((entry.get("pitch"), entry.get("channel")), lane)
    gm: dict[int, str] = {}
    for lane, pitch in GM_DRUMS.items():
        gm.setdefault(pitch, lane)

    def name(pitch: int, channel: int) -> str:
        return (by_key.get((pitch, channel)) or by_key.get((pitch, None)) or names.get(pitch) or gm.get(pitch)
                or midi_to_note(pitch))
    return name


def _kit_lanes(track: str | int, mono: np.ndarray, fs: int, offset: float, tempo: dict) -> dict | None:
    """Hit levels per drum on a one-track kit, from its MIDI notes and its rendered stem."""
    from . import mix_tools, structure

    items = [i for i in call("get_track_details", track=track).get("items", [])
             if i.get("type") == "midi" and not i.get("muted")]
    if not items:
        return None
    name = _lane_names(items[0]["id"])
    hits: dict[str, list[float]] = {}
    for item in items:
        for n in call("get_midi_notes", item_id=item["id"]).get("notes", []):
            if n.get("muted"):
                continue
            t = structure.qn_to_seconds(tempo, item["start"]["qn"] + n["start"]) - offset
            if 0 <= t < mono.size / fs:
                hits.setdefault(name(n["pitch"], n.get("channel", 1)), []).append(t)
    levels, lanes = mix_tools.hit_levels(mono, fs, hits)
    if len(levels) + len(lanes["silent"]) < 2:
        return None
    findings = mix_tools.lane_balance(levels, lanes["with_others"])
    if lanes["silent"]:
        findings.append(f"no sound from {', '.join(lanes['silent'])}: the kit has nothing on those notes (check "
                        "the layout with map_drum_kit, or move those notes to drums it has)")
    out = {"hit_level_db": levels, "findings": findings}
    if lanes["with_others"]:
        out["measured_with_other_drums"] = lanes["with_others"]
    return out


@tool(annotations=READ_ONLY)
def measure_tracks(
    tracks: Annotated[list[str | int] | None, Field(description="Tracks to measure; default: every track with items")] = None,
    start_bar: Bar = None,
    end_bar: Annotated[float | None, Field(description="Default: the end of the project")] = None,
    per_section: Annotated[bool, Field(description=(
        "Also each track's loudness in each section (the project's regions), judged against its role, and the "
        "level of each drum's hits on a one-track kit"))] = False,
) -> dict:
    """Measures many tracks in one render pass and returns a compact table: each track's
    loudness while it plays (max short-term LUFS), its peak, how bright it is, how harsh
    (its 2-5 kHz share in its harshest seconds), and where its energy sits (low / mid /
    high). Use it instead of analyze_audio track by track when balancing a mix: one call
    instead of dozens. With per_section, it also reports each track's level in every
    section (name the sections as regions first) and flags parts that are overpowering
    or buried against their role there (e.g. "Chorus: Snare is 6 LU over its place"),
    and on a kit that plays every drum from one track, each drum's hit level against the
    kick (a shaker or hat drowning the groove)."""
    overview = call("get_project_overview")
    chosen = tracks or _parts(overview)
    if not chosen:
        raise ValueError("no tracks with items to measure")
    stems = call("render_stems", timeout=900.0, tracks=chosen, start_bar=start_bar, end_bar=end_bar)
    renders = (bridge.directory / "renders").resolve()
    offset = (stems.get("start") or {}).get("seconds", 0.0)
    end = (stems.get("end") or {}).get("seconds", offset)
    sections = _sections(overview.get("regions", []), offset, end) if per_section else []
    no_sections = per_section and not sections
    tempo = call("get_tempo_map") if per_section else {}
    by_section: dict[str, dict[str, float | None]] = {s["name"]: {} for s in sections}
    roles: dict[str, str] = {}
    kits: dict[str, dict] = {}
    table = {}
    try:
        for stem in stems.get("stems", []):
            f = Path(stem["file"])
            if renders not in f.resolve().parents:
                raise BridgeError(f"refusing to use a render outside {renders}: {f}")
            m = analysis.analyze_file(f)
            name = stem["track"]["name"]
            if m.get("silent"):
                table[name] = "silent"
                continue
            bands = m["spectrum"].get("bands", {})

            def share(*keys: str) -> int:
                return int(round(sum((bands.get(k) or {}).get("share_pct", 0) for k in keys)))
            table[name] = {
                "lufs_playing": m["loudness"].get("max_short_term_lufs"),
                "peak_dbfs": m["levels"]["sample_peak_dbfs"],
                "brightness_hz": m["spectrum"].get("spectral_centroid_hz"),
                "harsh_pct_p95": (m.get("tone_over_time") or {}).get("harsh_2_5k_pct_p95"),
                "energy_pct": {"low": share("sub (20-60 Hz)", "bass (60-250 Hz)"),
                               "mid": share("low mids (250-500 Hz)", "mids (500 Hz-2 kHz)"),
                               "high": share("upper mids (2-4 kHz)", "presence (4-6 kHz)", "air (6-20 kHz)")},
            }
            if per_section:
                from . import mix_tools

                audio, fs = sf.read(str(f), always_2d=True)
                roles[name] = mix_tools.role_of(name, m["spectrum"])
                for sec in sections:
                    a, b = int((sec["start"] - offset) * fs), int((sec["end"] - offset) * fs)
                    by_section[sec["name"]][name] = _playing_lufs(audio[max(0, a):b], int(fs))
                if roles[name] == "drums":
                    kit = _kit_lanes(stem["track"].get("number", name), audio.mean(axis=1), int(fs), offset, tempo)
                    if kit:
                        kits[name] = kit
    finally:
        for f in stems.get("files", []):
            Path(f).unlink(missing_ok=True)
    out = {"range": {"from": stems.get("start"), "to": stems.get("end")}, "tracks": table,
           "how_to_read": "lufs_playing: how loud each part is while it plays (compare parts by it); energy_pct: "
                          "where its sound sits; brightness_hz: higher is brighter; harsh_pct_p95: share of its "
                          "energy at 2-5 kHz in its harshest seconds (the track to tame when the mix is piercing)"}
    if no_sections:
        out["note"] = ("no regions in this range, so there's no per-section table: name the sections as regions "
                       "(intro, verse, chorus...) to get it")
    if per_section and sections:
        from . import mix_tools

        out["sections"] = {sec: {t: v for t, v in levels.items()} for sec, levels in by_section.items()}
        out["roles"] = roles
        out["balance"] = mix_tools.section_balance(by_section, roles) or ["every part sits where its role puts it"]
        if kits:
            out["drum_kits"] = kits
    return out


# ---------------------------------------------------------------- structure

MAX_RING_OUT_BARS = 2

@tool(annotations=READ_ONLY)
def measure_structure(
    genre: Annotated[str | None, Field(description="The song's genre (list_genres), to compare its length with the genre's form")] = None,
    start_bar: Bar = None,
    end_bar: Annotated[float | None, Field(description="Default: the end of the project")] = None,
) -> dict:
    """Measures how the song develops, the thing listeners call "boring" or "repetitive"
    when it's missing. Renders the mix and fingerprints every bar (its sound and rhythm),
    then reports: the share of bars that are copies of other bars (a developing song
    stays under 0.4; one loop repeated scores near 1), the longest run of the same 4
    bars, each section's loudness against the energy its name promises (a chorus should
    lift 1 LU or more over a verse; a breakdown should drop), sections that play like
    an earlier one bar for bar, and the length against the genre's form. Name sections
    as regions first (intro, verse, chorus, drop...). Read-only."""
    overview = call("get_project_overview")
    tempo = call("get_tempo_map")
    audio, fs, render = _render("master", start_bar, end_bar)
    return structure_of(audio, fs, render, overview, tempo, genre, start_bar, end_bar)


def structure_of(audio: np.ndarray, fs: int, render: dict, overview: dict, tempo: dict, genre: str | None,
                 start_bar: float | None = None, end_bar: float | None = None) -> dict:
    """measure_structure's report from a master render already made (check_song renders
    once); start_bar and end_bar as the render was asked for."""
    offset = render["start"]["seconds"]
    end = offset + audio.shape[0] / fs
    every = structure.bar_starts(tempo, end + 1e-3)
    first_bar = sum(1 for s in every if s < offset - 1e-3) + 1
    starts = [s - offset for s in every if s >= offset - 1e-3]
    # Whole bars only: a partial last bar would look like a new idea.
    bounds = starts + [math.inf]
    full = [a for a, b in zip(bounds, bounds[1:]) if b <= audio.shape[0] / fs + 1e-3]
    if len(full) < 2:
        raise ValueError("that range is shorter than two bars; measure a longer stretch")
    stop = starts[len(full)] if len(starts) > len(full) else audio.shape[0] / fs
    mono = audio.mean(axis=1)
    tail = structure.tail_bars(mono, fs, full, stop)
    if tail:
        stop, full = full[-tail], full[:-tail]
    # A bar or two past the last section is the last notes ringing out (REAPER's project
    # end often runs past the music), not more song.
    if overview.get("regions") and end_bar is None:
        last = max(r["end"]["seconds"] for r in overview["regions"]) - offset
        after = [a for a in full if a >= last - 1e-3]
        if 0 < len(after) <= MAX_RING_OUT_BARS and len(full) - len(after) >= 2:
            stop, full = after[0], full[: len(full) - len(after)]
    silent = structure.silent_bars(mono, fs, full, stop)
    features = structure.bar_features(mono, fs, full, stop)
    rep = structure.repetition(features, silent)
    sections = _sections(overview.get("regions", []), offset, offset + stop)
    table = structure.section_table(sections, full, features, audio, fs, offset, silent)
    # The form's length only means something for the whole song.
    form = structure.form_bars(genres.find(genre)) if genre and start_bar is None and end_bar is None else None
    findings = structure.judge(rep, table, len(full), form)
    out: dict = {"bars": {"from": first_bar, "to": first_bar + len(full) - 1, "count": len(full)},
                 **{k: v for k, v in rep.items() if k != "bars"}}
    if form:
        out["genre_form_bars"] = form
    if table:
        out["sections"] = table
    else:
        out["note"] = "no regions in this range: name the sections as regions to get the per-section energy arc"
    out["findings"] = findings or ["it develops: no long loops, copied sections or flat energy found"]
    out["how_to_read"] = ("near_duplicate_share: bars that are copies of another bar (under 0.4 develops; near 1 is "
                          "one loop); longest_loop_bars: longest stretch of the same 4 bars (16 or more reads as a "
                          "loop: change something every 8 bars); sections: lufs per section and the energy its name "
                          "promises (1 calm .. 4 peak); same_as: plays like that section bar for bar (give it new "
                          "material: a different groove, bass line, voicing or a part in or out)")
    return out


# ------------------------------------------------------------------- groove

@tool(annotations=READ_ONLY)
def check_groove(
    track: Annotated[str | int, Field(description="A drum, bass or other MIDI track")],
    genre: Annotated[str | None, Field(description="The song's genre, to compare the swing with its profile")] = None,
    start_bar: Bar = None,
    end_bar: Annotated[float | None, Field(description="Default: the end of the project")] = None,
) -> dict:
    """Checks whether a MIDI part plays like a performance or a machine, the thing
    listeners call "stiff": how far notes sit off the grid (a histogram in ms), how much
    each drum's (or the part's) velocities vary, the swing of its 8ths and 16ths, the
    share of bars that repeat the bar before note for note, and whether the bar before
    each section (the regions) changes for a fill. Notes all on the grid at one velocity
    fail; on the grid with accents is right for programmed electronic music. Read-only."""
    from . import feel, mix_tools

    overview = call("get_project_overview")
    bar, beats, _ = feel.pulses(overview.get("time_signature") or "4/4")
    beat = beats[1] - beats[0] if len(beats) > 1 else bar
    bpm = float(overview.get("tempo_bpm") or 120)
    details = call("get_track_details", track=track)
    items = [i for i in details.get("items", []) if i.get("type") == "midi" and not i.get("muted")]
    if not items:
        raise ValueError(f"'{details.get('name', track)}' has no MIDI items to check")
    lo = (start_bar - 1) * bar if start_bar else -1e9
    hi = (end_bar - 1) * bar if end_bar else 1e9
    notes = []
    for item in items:
        for n in call("get_midi_notes", item_id=item["id"]).get("notes", []):
            qn = item["start"]["qn"] + n["start"]
            if lo - 1e-6 <= qn < hi:
                notes.append({**n, "start": qn})
    role = mix_tools.role_of(details.get("name", ""))
    drum_like = role in ("drums", "kick", "snare", "perc")
    jobs = None
    if drum_like:
        name = _lane_names(items[0]["id"])
        jobs = {}
        for n in notes:
            lane = name(n["pitch"], n.get("channel", 1))
            jobs[n["pitch"]] = feel.drum_job(lane) or lane
    sections = [(r["name"], int(round(r["start"]["bar"]))) for r in overview.get("regions", [])
                if r.get("start", {}).get("bar")]
    swing = genres.find(genre).swing if genre else None
    report = feel.check_groove(notes, bar, beat, bpm, jobs, sections, swing)
    return {"track": details.get("name", track), "role": role, **({"genre_swing": swing} if swing else {}), **report,
            "how_to_read": ("fail: one velocity throughout, apply_feel with the part's role (drums, bass...) and the "
                            "genre's feel; on_grid_share near 1 with accents is fine for electronic music; "
                            "bars_same_as_previous 0.9 or more: vary bars every 4 and fill every 8; no_fill_into: "
                            "sections with nothing changing in the bar before")}
