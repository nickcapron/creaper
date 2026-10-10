"""MCP tools for the user's samples and loops: find them, hear what they are, place
loops in time and key, and build drum kits from samples in REAPER's own sampler."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

from . import harmony, samplelib, theory
from .server import READ_ONLY, bridge, call, tool

library = samplelib.SampleLibrary(bridge.directory)


def _check_audio(path: str) -> str:
    p = Path(path)
    if p.suffix.lower() not in samplelib.AUDIO_EXTENSIONS:
        raise ValueError(f"not an audio file creaper can use: {path}")
    if not p.is_file():
        raise ValueError(f"there's no file at {path}")
    return str(p)


@tool()
def sample_folders(
    add: Annotated[str | None, Field(description="A folder of samples to add, e.g. 'D:/Samples'")] = None,
    remove: Annotated[str | None, Field(description="A folder to stop indexing")] = None,
) -> dict:
    """Lists, adds or removes the folders creaper searches for samples and loops (by
    default the ones it finds: Arturia's sample library, SILA's, Music, REAPER Media)."""
    folders = library.folders()
    if add:
        if not Path(add).is_dir():
            raise ValueError(f"there's no folder at {add}")
        folders = library.set_folders(folders + [str(Path(add))])
    if remove:
        folders = library.set_folders([f for f in folders if os.path.normcase(f) != os.path.normcase(str(Path(remove)))])
    return {"folders": folders}


@tool(annotations=READ_ONLY)
def find_samples(
    search: Annotated[str | None, Field(description="Words in the file or folder name, e.g. '808 kick', 'vinyl', 'amen'")] = None,
    role: Annotated[str | None, Field(description=(
        "kick, snare, clap, closed hat, open hat, crash, ride, tom, rim, shaker, percussion, 808, bass, pad, lead, "
        "keys, pluck, chord, arp, vocal, fx, guitar, strings, brass, loop"))] = None,
    kind: Annotated[Literal["loop", "one-shot"] | None, Field(description="Loops (with a tempo) or single hits")] = None,
    bpm: Annotated[float | None, Field(description="Loops at (or double/half) this tempo")] = None,
    key: Annotated[str | None, Field(description="Loops in this key, e.g. 'A minor'")] = None,
    listen: Annotated[bool, Field(description="Also analyse the top results by ear (type, pitch, tempo, key)")] = True,
    max_results: Annotated[int, Field(ge=1, le=100)] = 15,
    refresh: Annotated[bool, Field(description="Re-scan the folders for new files")] = False,
) -> dict:
    """Searches the user's sample folders by name, role, loop tempo and key, and (by
    default) listens to the top results to say what each actually is."""
    if refresh:
        library.index(refresh=True)
    hits = library.search(search, role, kind, bpm, key)
    shown = []
    for f in hits[:max_results]:
        entry = {"path": f["path"], "name": f["name"], "folder": f["folder"], "duration_s": f.get("duration_s"),
                 **({"roles_from_name": f["roles"]} if f.get("roles") else {}),
                 **({"bpm_from_name": f["bpm"]} if f.get("bpm") else {}),
                 **({"key_from_name": f["key"]} if f.get("key") else {})}
        if listen:
            analysis = f.get("analysis")
            if analysis is None:
                try:
                    analysis = samplelib.analyze(f["path"])
                    library.remember(f["path"], analysis)
                except Exception as e:  # noqa: BLE001 - one unreadable file shouldn't sink the search
                    analysis = {"error": str(e)}
            entry["heard"] = analysis
        shown.append(entry)
    total = len(library.index().get("files", []))
    out = {"matches": len(hits), "shown": shown, "library_files": total}
    if not hits:
        out["tip"] = ("Nothing matched. Try fewer words, a role instead of a name, or sample_folders(add=...) to "
                      "index another folder.")
    return out


@tool(annotations=READ_ONLY)
def analyze_sample(path: Annotated[str, Field(description="Full path of an audio file")]) -> dict:
    """Listens to one sample: loop or one-shot, what drum it sounds like or what pitch it
    plays, a loop's tempo and length in bars and its key, and whether it starts late."""
    path = _check_audio(path)
    result = samplelib.analyze(path)
    library.remember(path, result)
    return {"path": path, **result}


@tool()
def place_loop(
    path: Annotated[str, Field(description="The loop's file (from find_samples)")],
    track: Annotated[str | int, Field(description="Track to put it on")],
    bar: Annotated[float, Field(ge=1)] = 1,
    bars: Annotated[float | None, Field(gt=0, description="Repeat it to fill this many bars")] = None,
    match_tempo: Annotated[bool, Field(description="Stretch it to the project tempo (pitch kept)")] = True,
    loop_bpm: Annotated[float | None, Field(gt=0, description="The loop's own tempo, if known; else it's measured")] = None,
    to_key: Annotated[str | None, Field(description="Transpose it into this key (needs its key: from the name or by ear)")] = None,
    semitones: Annotated[float | None, Field(ge=-24, le=24, description="Or transpose by this much")] = None,
) -> dict:
    """Puts a loop on a track in time: stretched from its own tempo to the project's
    (pitch preserved), optionally moved into the project's key, and repeated to fill
    a number of bars."""
    path = _check_audio(path)
    analysis = None
    if (match_tempo and not loop_bpm) or (to_key and semitones is None):
        analysis = samplelib.analyze(path)
        library.remember(path, analysis)
    own_bpm = loop_bpm or samplelib.bpm_from_name(Path(path).name) or (analysis or {}).get("bpm")
    item = call("insert_audio_file", timeout=120.0, path=path, track=track, start_bar=bar)
    overview = call("get_project_overview")
    project_bpm = float(overview.get("tempo_bpm") or 120)
    changes: dict = {}
    notes = []
    if match_tempo:
        if own_bpm:
            rate = project_bpm / own_bpm
            if rate > 1.6:
                rate /= 2
            elif rate < 0.62:
                rate *= 2
            changes.update(playrate=round(rate, 5), preserve_pitch=True)
            notes.append(f"stretched from {own_bpm:g} to {project_bpm:g} BPM (rate {rate:.3f}, pitch kept)")
        else:
            notes.append("couldn't tell the loop's tempo, so it plays at its own speed; give loop_bpm")
    shift = semitones
    if shift is None and to_key:
        source_key = samplelib.key_from_name(Path(path).stem) or (analysis or {}).get("key")
        if source_key:
            a, b = harmony.parse_key(source_key), harmony.parse_key(to_key)
            shift = ((b.tonic - a.tonic + 6) % 12) - 6
            notes.append(f"moved from {source_key} to {to_key}")
        else:
            notes.append("couldn't tell the loop's key, so it wasn't transposed")
    if shift:
        changes["pitch_semitones"] = shift
    if bars:
        changes.update(loop=True, length_bars=bars)
    if changes:
        item = call("edit_item", item_id=item["id"], **changes)
    return {"item": item, "loop_bpm": own_bpm, "project_bpm": project_bpm, "notes": notes}


GM_LANES = {"kick": 36, "kick 2": 35, "rim": 37, "snare": 38, "clap": 39, "snare 2": 40, "low tom": 41, "closed hat": 42,
            "floor tom": 43, "pedal hat": 44, "mid tom": 45, "open hat": 46, "high tom": 48, "crash": 49, "ride": 51,
            "china": 52, "ride bell": 53, "tambourine": 54, "splash": 55, "cowbell": 56, "crash 2": 57, "shaker": 70,
            "claves": 75, "conga": 63, "bongo": 60}


@tool()
def build_drum_kit(
    track: Annotated[str | int, Field(description="An empty track, or one without another instrument")],
    samples: Annotated[dict[str, str], Field(description=(
        "Drum lane -> sample file, e.g. {'kick': 'C:/.../XOX kick1.wav', 'snare': '...', 'closed hat': '...'}. "
        "Lanes: kick, snare, clap, rim, closed hat, pedal hat, open hat, low/mid/high tom, crash, ride, "
        "tambourine, cowbell, shaker, or any other name (placed from C4 up)"))],
    trim_silence: Annotated[bool, Field(description="Report samples that start late (silence at the start)")] = True,
) -> dict:
    """Builds a drum kit from sample files in REAPER's own sampler (one
    ReaSamplOmatic5000 per drum, on the General MIDI keys), so drum patterns and genre
    grooves land on the right sounds and every sample can be swapped by name later.
    Works with any samples, including the ones other instruments ship with."""
    pads, used = [], set()
    extra = 60
    for lane, path in samples.items():
        path = _check_audio(path)
        key = lane.strip().lower()
        note = GM_LANES.get(key)
        if note is None:
            try:
                note = theory.drum_pitch(key)
            except ValueError:
                note = None
        if note is None or note in used:
            while extra in used:
                extra += 1
            note = extra
        used.add(note)
        pads.append({"note": note, "path": path, "name": f"{lane} - {Path(path).stem}"})
    result = call("build_sampler_kit", timeout=120.0, track=track, pads=pads)
    out = {"track": result.get("track"),
           "kit": {p["name"].split(" - ")[0]: f"{theory.midi_to_note(p['note'])} ({p['note']})" for p in pads},
           "note": "Lanes sit on General MIDI keys, so add_drum_pattern and add_genre_groove find them without a drum map."}
    if trim_silence:
        late = []
        for p in pads:
            try:
                a = samplelib.analyze(p["path"])
            except Exception:  # noqa: BLE001
                continue
            if a.get("starts_late_ms", 0) >= 8:
                late.append(f"{p['name']} starts {a['starts_late_ms']:.0f} ms late")
        if late:
            out["timing"] = late + ["Trim the sample start in ReaSamplOmatic5000 (or pick another sample)."]
    return out
