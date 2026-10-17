"""MCP tools for the user's samples and loops: find them, hear what they are, place
loops in time and key, and build drum kits from samples in REAPER's own sampler."""

from __future__ import annotations

import math

import os
import re
from pathlib import Path
from typing import Annotated, Literal

import numpy as np
import soundfile as sf
from pydantic import BaseModel, Field

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
    """Shows, adds to or removes from the list of folders creaper indexes for samples
    and loops (by default the ones it finds: Arturia's sample library, SILA's, Music,
    REAPER Media). With no arguments it only lists them. Use it when the user's
    samples live somewhere else; find_samples searches what's indexed. Returns the
    folder list."""
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
    max_results: Annotated[int, Field(ge=1, le=100, description="Most files to return")] = 15,
    refresh: Annotated[bool, Field(description="Re-scan the folders for new files")] = False,
    style: Annotated[str | None, Field(description=(
        "The song's genre: drum hits (role kick, snare, clap, closed/open hat) are ranked by how well they "
        "measure against its drums (weight under 90 Hz, decay, brightness, punch), best first"))] = None,
) -> dict:
    """Searches the audio files in the user's sample folders (sample_folders) by
    name, role, loop tempo and key, and (by default) listens to the top results to
    say what each actually is. With style and a drum role, the hits are ranked by fit to
    the genre's drums, and lo-fi files (8-bit, or recorded under 32 kHz) are flagged unless
    the style is lo-fi. Use it to find drum hits, loops, risers or vocals;
    place_loop puts a loop in time and key, build_drum_kit and
    build_sampled_instrument turn hits into playable instruments. (Saved plugin
    sounds are in list_sounds.) Read-only."""
    if refresh:
        library.index(refresh=True)
    hits = library.search(search, role, kind, bpm, key)
    target, lofi_ok = None, False
    if style and role:
        from . import genres
        from .genres import palettes

        g = genres.find(style)
        lane = {"closed hat": "hat", "open hat": "hat", "hat": "hat", "hats": "hat", "hihat": "hat", "hi-hat": "hat",
                "hh": "hat", "rim": "snare"}.get(role.lower(), role.lower())
        p = palettes.palette(g)
        target = (p.drums.get(lane) if p else None)
        lofi_ok = any(w in f"{g.name} {g.family} {' '.join(g.aliases)}".lower()
                      for w in ("lo-fi", "lofi", "chiptune", "boom bap", "8-bit", "vaporwave"))
    if target is not None and listen:
        # Rank by fit: listen to a wider pool first (results are remembered).
        pool = hits[: max(max_results * 3, 30)]
        fresh = {}
        for f in pool:
            if (f.get("analysis") or {}).get("v") != samplelib.ANALYSIS_VERSION:
                try:
                    f["analysis"] = fresh[f["path"]] = samplelib.analyze(f["path"])
                except Exception as e:  # noqa: BLE001
                    f["analysis"] = {"error": str(e)}
        library.remember_many(fresh)
        for f in pool:
            heard = f["analysis"]
            if heard.get("kind") != "one-shot" or "sub_share" not in heard:
                f["_fit"], f["_why"] = 99.0, ["not a single hit that could be measured (a loop, silent or unreadable)"]
                continue
            fit, why = samplelib.drum_fit(heard, target)
            if f["analysis"].get("lofi") and not lofi_ok:
                fit += 2.0
                why = why + ["lo-fi file (8-bit, or recorded under 32 kHz): sounds dated for this style"]
            f["_fit"], f["_why"] = fit, why
        hits = sorted(pool, key=lambda f: f["_fit"]) + hits[len(pool):]
    shown = []
    for f in hits[:max_results]:
        entry = {"path": f["path"], "name": f["name"], "folder": f["folder"], "duration_s": f.get("duration_s"),
                 **({"roles_from_name": f["roles"]} if f.get("roles") else {}),
                 **({"bpm_from_name": f["bpm"]} if f.get("bpm") else {}),
                 **({"key_from_name": f["key"]} if f.get("key") else {})}
        if "_fit" in f:
            # score: 0 fits the genre's drums, lower is better; off: what falls outside its ranges.
            entry["fit"] = {"score": f["_fit"], "off": f["_why"]} if f["_why"] else {"score": 0.0}
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
    if target is not None:
        out["fit"] = "ranked by fit to the genre's drums: score 0 fits, lower is better; off says what's outside"

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
    bar: Annotated[float, Field(ge=1, description="Bar where the loop starts, 1-based")] = 1,
    bars: Annotated[float | None, Field(gt=0, description="Repeat it to fill this many bars")] = None,
    match_tempo: Annotated[bool, Field(description="Stretch it to the project tempo (pitch kept)")] = True,
    loop_bpm: Annotated[float | None, Field(gt=0, description="The loop's own tempo, if known; else it's measured")] = None,
    to_key: Annotated[str | None, Field(description="Transpose it into this key (needs its key: from the name or by ear)")] = None,
    semitones: Annotated[float | None, Field(ge=-24, le=24, description="Or transpose by this much")] = None,
) -> dict:
    """Puts an audio loop on a track in time: stretched from its own tempo to the
    project's (pitch preserved), optionally moved into a key, and repeated to fill a
    number of bars. Use it for loops found with find_samples; insert_audio_file
    imports a file as it is, without stretching. Returns the item, the loop's and the
    project's tempo, and notes on what was changed."""
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


# The same keys add_drum_pattern and add_genre_groove use for these lanes (General MIDI).
GM_LANES = {"kick": 36, "kick 2": 35, "rim": 37, "snare": 38, "clap": 39, "snare 2": 40, "low tom": 45, "closed hat": 42,
            "floor tom": 43, "pedal hat": 44, "mid tom": 47, "open hat": 46, "high tom": 50, "crash": 49, "ride": 51,
            "china": 52, "ride bell": 53, "tambourine": 54, "splash": 55, "cowbell": 56, "crash 2": 57, "shaker": 70,
            "claves": 75, "conga": 63, "bongo": 60}


class Layer(BaseModel):
    path: str = Field(description="Sample file for the layer")
    gain_db: float = Field(-6.0, ge=-30, le=6, description=(
        "Its level against the lane's main sample (negative = quieter); a layer plays on every velocity"))


def velocity_bands(n: int) -> list[tuple[int, int]]:
    """MIDI velocity 1-127 split into n bands, softest first."""
    edges = [1 + round(i * 127 / n) for i in range(n + 1)]
    return [(edges[i], edges[i + 1] - 1 if i < n - 1 else 127) for i in range(n)]


@tool()
def build_drum_kit(
    track: Annotated[str | int, Field(description="An empty track, or one without another instrument")],
    samples: Annotated[dict[str, str | list[str]], Field(description=(
        "Drum lane -> sample file, or a list of 2-4 alternatives for the lane (velocity splits: the quietest "
        "sample on the softest hits, so a humanised part alternates between them and accents hit harder), e.g. "
        "{'kick': 'C:/.../kick1.wav', 'snare': ['.../snare a.wav', '.../snare b.wav'], 'closed hat': '...'}. "
        "Lanes: kick, snare, clap, rim, closed hat, pedal hat, open hat, low/mid/high tom, crash, ride, "
        "tambourine, cowbell, shaker, or any other name (placed from C4 up)"))],
    layers: Annotated[dict[str, list[Layer]] | None, Field(description=(
        "Extra samples that play with every hit of a lane, at their own level: a click or a sub under the kick, "
        "a clap on the snare, e.g. {'kick': [{'path': '.../click.wav', 'gain_db': -8}]}"))] = None,
    trim_silence: Annotated[bool, Field(description="Report samples that start late (silence at the start)")] = True,
    velocity_db: Annotated[float, Field(ge=-40, le=0, description="Level at the softest velocity: -18 lets ghost notes and accents work, 0 ignores velocity")] = -18.0,
    release_s: Annotated[float | None, Field(gt=0, le=10, description="Cut each hit this long after its note ends (for samples with long tails, e.g. 0.2 kicks, 0.45 taiko); default: play the whole sample")] = None,
) -> dict:
    """Builds a drum kit from sample files in REAPER's own sampler (ReaSamplOmatic5000
    on the General MIDI keys), so drum patterns and genre grooves land on the right
    sounds and every sample can be swapped by name later. A lane can have alternatives
    split by velocity (no machine-gun repeats, real dynamics) and layers that play with
    each hit (weight and snap a single sample lacks). Works with any samples, including
    the ones other instruments ship with; find_samples(role=..., style=...) picks ones
    that fit the genre. Building again on the same track adds samplers to it; to swap a
    lane's sample later, change its sampler (get_track_details lists them by lane)."""
    pads, used = [], set()
    extra = 60
    setup: list[dict] = []  # per pad: velocity band and level, set once the samplers exist
    for lane, given in samples.items():
        paths = [_check_audio(x) for x in (given if isinstance(given, list) else [given])]
        if not paths or len(paths) > 8:
            raise ValueError(f"give the '{lane}' lane 1 to 8 samples")
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
        if len(paths) > 1:
            # Softest sample on the lowest velocities: alternatives double as velocity layers.
            levels = {}
            for x in paths:
                try:
                    levels[x] = samplelib.analyze(x).get("level_db")
                    if levels[x] is None:
                        clip, fs, _ = samplelib._load(x, seconds=1.0)
                        levels[x] = 10 * math.log10(float(np.mean(np.square(clip[: int(0.3 * fs)]))) + 1e-20)
                except Exception:  # noqa: BLE001
                    levels[x] = 0.0
            paths.sort(key=lambda x: levels[x])
        for x, (lo, hi) in zip(paths, velocity_bands(len(paths)) if len(paths) > 1 else [(1, 127)]):
            pads.append({"note": note, "path": x, "name": f"{lane} - {Path(x).stem}"})
            setup.append({"lane": lane, "min_vel": lo, "max_vel": hi, "gain_db": 0.0, "layer": False})
        for layer in (layers or {}).get(lane, []):
            lp = _check_audio(layer.path)
            pads.append({"note": note, "path": lp, "name": f"{lane} layer - {Path(lp).stem}"})
            setup.append({"lane": lane, "min_vel": 1, "max_vel": 127, "gain_db": layer.gain_db, "layer": True})
    unknown = set(layers or {}) - set(samples)
    if unknown:
        raise ValueError(f"layers for lanes that have no sample: {', '.join(sorted(unknown))}")
    if isinstance(track, str) and not any(t["name"] == track for t in call("get_project_overview").get("tracks", [])):
        call("create_track", name=track)
    result = call("build_sampler_kit", timeout=120.0, track=track, pads=pads, velocity_db=velocity_db, release_s=release_s)
    for pad, cfg in zip(result.get("pads", []), setup):
        changes = []
        if (cfg["min_vel"], cfg["max_vel"]) != (1, 127):
            changes += [{"parameter": "Minimum velocity", "display_value": cfg["min_vel"]},
                        {"parameter": "Maximum velocity", "display_value": cfg["max_vel"]}]
        if cfg["gain_db"]:
            changes.append({"parameter": "Volume", "display_value": cfg["gain_db"]})
        if changes:
            call("set_fx_parameters", track=track, fx=pad["fx"], changes=changes)
    kit: dict = {}
    for p, cfg in zip(pads, setup):
        entry = kit.setdefault(cfg["lane"], {"key": f"{theory.midi_to_note(p['note'])} ({p['note']})", "samples": []})
        entry["samples"].append(Path(p["path"]).stem + (
            f" (layer, {cfg['gain_db']:+g} dB)" if cfg["layer"] else
            f" (velocity {cfg['min_vel']}-{cfg['max_vel']})" if (cfg["min_vel"], cfg["max_vel"]) != (1, 127) else ""))
    out = {"track": result.get("track"), "kit": kit,
           "note": "Lanes sit on General MIDI keys, so add_drum_pattern and add_genre_groove find them without a drum map."}
    if any(len(v["samples"]) > 1 for v in kit.values()):
        out["tip"] = ("lanes with alternatives switch sample by velocity: give the part a feel (apply_feel) or "
                      "varied velocities so they alternate")
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


# ------------------------------------------------------- sampled instruments

NOTE_IN_NAME = re.compile(r"(?<![A-Za-z])([A-Ga-g])([#b]?)(-?\d)(?![0-9])")


def note_from_name(name: str) -> int | None:
    """The note a sample's file name claims (the last one in it): 'CS_Violas_Sus_F_CL2_F#3_D' -> F#3."""
    found = NOTE_IN_NAME.findall(Path(name).stem.replace("-", "_"))
    if not found:
        return None
    letter, accidental, octave = found[-1]
    try:
        return theory.note_to_midi(f"{letter.upper()}{accidental}{octave}")
    except ValueError:
        return None


def measure_root(path: str) -> float | None:
    """The pitch a sample actually plays (MIDI, with cents), measured on its steady part."""
    x, fs, _ = samplelib._load(path, seconds=12.0)
    if not len(x):
        return None
    level = np.abs(x)
    sounding = np.nonzero(level > level.max() * 0.05)[0]
    if not len(sounding):
        return None
    a, b = sounding[0], sounding[-1]
    span = b - a
    readings = []
    for k in range(5):
        start = a + int(span * (0.15 + 0.1 * k))
        seg = x[start: start + int(0.2 * fs)]
        hz, clarity = samplelib.vocal_pitch(seg, fs, fmin=28.0, fmax=2200.0)
        if hz and clarity >= 0.8:
            readings.append(69 + 12 * np.log2(hz / 440))
    if not readings:
        return None
    root = float(np.median(readings))
    # A reading an octave low has no odd harmonics (1x, 3x, 5x of it): then it's an octave up.
    seg = x[a + int(span * 0.2): a + int(span * 0.2) + int(min(1.0, span / fs * 0.6) * fs)]
    if len(seg) > fs // 10:
        spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
        freqs = np.fft.rfftfreq(len(seg), 1 / fs)
        f0 = 440 * 2 ** ((root - 69) / 12)

        def peak(h: float) -> float:
            band = (freqs > h * 0.97) & (freqs < h * 1.03)
            return float(spec[band].max()) if band.any() else 0.0
        odd, even = max(peak(f0), peak(3 * f0), peak(5 * f0)), max(peak(2 * f0), peak(4 * f0), peak(6 * f0))
        if even > 0 and odd < even * 0.03:
            root += 12
    return round(root, 2)


def plan_zones(roots: list[tuple[str, float]], reach: int = 6, low: int | None = None,
               high: int | None = None) -> list[dict]:
    """Key ranges for samples with known roots: split halfway between neighbours, the
    outer ones reaching `reach` semitones beyond their roots (or to low/high)."""
    ordered = sorted(roots, key=lambda r: r[1])
    zones = []
    for i, (path, root) in enumerate(ordered):
        lo = (round(root) - reach if low is None else low) if i == 0 else zones[-1]["hi"] + 1
        if i + 1 < len(ordered):
            hi = int((round(root) + round(ordered[i + 1][1])) // 2)
        else:
            hi = round(root) + reach if high is None else high
        zones.append({"path": path, "root": root, "lo": max(0, int(lo)), "hi": min(127, int(hi))})
    return [z for z in zones if z["lo"] <= z["hi"]]


def _frames(path: str) -> tuple[int, int]:
    info = sf.info(path)
    return info.frames, info.samplerate


def layered_zones(roots: list[tuple[str, float]], names: dict[str, tuple[str, int | None, int | None]],
                  reach: int, low: int | None, high: int | None) -> list[dict]:
    """Zones for samples whose names mark velocity layers (pp, mf, ff, soft, v2...) and
    round robins (rr1, rr2...): the key ranges from one sample of each pitch, each of a
    pitch's layers its share of the velocities, the round robins of a zone in turn."""
    by_base: dict[str, list[tuple[str, float, int | None, int | None]]] = {}
    for path, root in roots:
        base, rank, rr = names[path]
        by_base.setdefault(base, []).append((path, root, rank, rr))
    reps = [(base, takes[0][1]) for base, takes in by_base.items()]
    out = []
    for zone in plan_zones(reps, reach, low, high):
        takes = by_base[zone["path"]]
        layers: dict[int | None, list] = {}
        for t in takes:
            layers.setdefault(t[2], []).append(t)
        # Split among the layers this pitch has, so a note recorded soft only still plays loud.
        ranges = velocity_ranges_for([r for r in layers if r is not None])
        for rank, group in layers.items():
            group.sort(key=lambda t: t[3] or 0)
            z = {"path": group[0][0], "root": group[0][1], "lo": zone["lo"], "hi": zone["hi"]}
            if rank is not None and len(ranges) > 1:
                z["lovel"], z["hivel"] = ranges[rank]
            if len(group) > 1:
                z["files"] = [t[0] for t in group]
            out.append(z)
    return out


def velocity_ranges_for(ranks: list[int]) -> dict[int, tuple[int, int]]:
    from .sfz import velocity_ranges

    return velocity_ranges(ranks) if ranks else {}


@tool()
def build_sampled_instrument(
    track: Annotated[str, Field(description="Track to put it on (created if there's none by that name)")],
    samples: Annotated[list[str] | None, Field(max_length=96, description=(
        "Pitched samples of one instrument and articulation, e.g. a multisample set from find_samples "
        "(cello sustains at several pitches); one sample works too, over a smaller range. Names marking "
        "velocity layers (pp, mf, ff, soft, loud, v1-v4) and round robins (rr1, rr2) are layered"))] = None,
    sfz_path: Annotated[str | None, Field(description=(
        "Or an .sfz instrument file of the user's: its key and velocity zones, round robins and loops"))] = None,
    reach: Annotated[int, Field(ge=1, le=12, description="Semitones the lowest and highest samples stretch beyond their pitch (past ~6 they sound unnatural)")] = 6,
    low_note: Annotated[str | int | None, Field(description="Or the lowest note to cover, e.g. 'C2'")] = None,
    high_note: Annotated[str | int | None, Field(description="And the highest, e.g. 'G5'")] = None,
    release_s: Annotated[float, Field(ge=0.01, le=10, description="Release after note-off (strings ~0.3, pizzicato/plucks ~0.15, pads ~1)")] = 0.3,
    velocity_db: Annotated[float, Field(ge=-40, le=0, description="Level at the softest velocity: -18 is expressive, 0 ignores velocity")] = -18.0,
) -> dict:
    """Builds a playable instrument from pitched sample files (strings, brass,
    pizzicato, choir, a sampled synth...): each sample covers a stretch of keys and
    follows the keyboard, tuned from the pitch it actually plays (measured by ear,
    with cents; sample file names are sometimes an octave off), with velocity
    response, note-offs and a release. Better than build_drum_kit for melodic parts,
    which plays each sample on one key at its own pitch. An .sfz file (sfz_path) gives
    its own zones; samples' names give velocity layers and round robins; WAV loop points
    (the smpl chunk) keep sustains going while a note is held."""
    from . import sfz

    if sfz_path:
        zones = sfz.load(sfz_path, _frames)
        return _build(track, zones, release_s, velocity_db, [], source=Path(sfz_path).name)
    if not samples:
        raise ValueError("give the samples, or an .sfz file (sfz_path)")
    roots, report = [], []
    names = {}
    for path in (_check_audio(p) for p in samples):
        names[path] = sfz.name_layers(Path(path).name)
        measured = measure_root(path)
        named = note_from_name(path)
        entry: dict = {"sample": Path(path).name}
        if measured is None and named is None:
            entry["skipped"] = "no clear pitch, and none in its name"
        else:
            root = measured if measured is not None else float(named)
            entry["plays"] = theory.midi_to_note(round(root))
            if measured is not None:
                entry["cents_off"] = int(round((measured - round(measured)) * 100))
            else:
                entry["note"] = "pitch taken from the file name (couldn't measure it)"
            if measured is not None and named is not None and round(measured) != named:
                diff = round(measured) - named
                entry["name_says"] = theory.midi_to_note(named) + (
                    " (an octave off)" if abs(diff) == 12 else f" ({diff:+d} semitones off)")
            roots.append((path, root))
        report.append(entry)
    if not roots:
        raise ValueError("none of those samples has a pitch to build an instrument from")
    low = theory.note_to_midi(low_note) if low_note is not None else None
    high = theory.note_to_midi(high_note) if high_note is not None else None
    if any(rank is not None or rr is not None for _, rank, rr in names.values()):
        zones = layered_zones(roots, names, reach, low, high)
    else:
        zones = plan_zones(roots, reach, low, high)
    for z in zones:
        if z["path"].lower().endswith(".wav"):
            found = sfz.wav_loop(z["path"])
            if found and "start" in found:
                z.update(sfz.loop_fields((found["start"], found["end"]), *_frames(z["path"])))
    return _build(track, zones, release_s, velocity_db, report)


def _build(track: str, zones: list[dict], release_s: float, velocity_db: float, report: list[dict],
           source: str | None = None) -> dict:
    overview = call("get_project_overview")
    if not any(t["name"] == track for t in overview.get("tracks", [])):
        call("create_track", name=track)
    for z in zones:
        z["name"] = f"{Path(z['path']).stem[:24]} {theory.midi_to_note(z['lo'])}-{theory.midi_to_note(z['hi'])}" + (
            f" v{z['lovel']}-{z['hivel']}" if "lovel" in z else "")
    result = call("build_sampled_instrument", timeout=180.0, track=track, zones=zones,
                  release_s=release_s, velocity_db=velocity_db)
    stretched = [z for z in zones if max(round(z["root"]) - z["lo"], z["hi"] - round(z["root"])) > 6]
    lo, hi = min(z["lo"] for z in zones), max(z["hi"] for z in zones)

    def describe(z: dict) -> dict:
        d = {"keys": f"{theory.midi_to_note(z['lo'])}-{theory.midi_to_note(z['hi'])}",
             "root": theory.midi_to_note(round(z["root"])), "sample": Path(z["path"]).name}
        if "lovel" in z:
            d["velocity"] = f"{z['lovel']}-{z['hivel']}"
        if z.get("files"):
            d["round_robin"] = len(z["files"])
        if z.get("loop"):
            d["loops"] = True
        return d

    out = {"track": result["track"], "plays": f"{theory.midi_to_note(lo)} to {theory.midi_to_note(hi)}",
           "zones": [describe(z) for z in zones][:48]}
    if len(zones) > 48:
        out["zones_shown"] = f"48 of {len(zones)}"
    if source:
        out["sfz"] = source
    if report:
        out["samples"] = report
    layers = sorted({(z["lovel"], z["hivel"]) for z in zones if "lovel" in z})
    if layers:
        out["velocity_layers"] = len(layers)
    if stretched:
        out["note"] = ("some zones stretch a sample more than 6 semitones, which can sound unnatural: "
                       + ", ".join(Path(z["path"]).name for z in stretched) + ". More samples in between help.")
    return out
