"""Motifs that carry across songs: save a theme's notes once (a game's signature, a
leitmotif), then place it in any project, in that song's key and mode, slower or
faster, an octave up or down. Kept in <resource>/creaper/motifs.json."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Annotated

from pydantic import Field

from . import harmony
from .server import READ_ONLY, ItemId, bridge, call, tool


def motifs_file() -> Path:
    return bridge.directory / "motifs.json"


def _load() -> dict:
    try:
        return json.loads(motifs_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save(data: dict) -> None:
    path = motifs_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    tmp.replace(path)


def _key(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def _names(notes: list[dict], key: str) -> list[str]:
    """Note names spelled in the key (Eb in C minor, F# in D major)."""
    k = harmony.parse_key(key)
    return [f"{k.spell_pc(n['pitch'] % 12)}{n['pitch'] // 12 - 1}" for n in notes]


def capture(notes: list[dict], start: float | None = None, end: float | None = None) -> list[dict]:
    """A motif's notes from an item's: those starting in [start, end), times from 0."""
    chosen = [n for n in notes if not n.get("muted") and (start is None or n["start"] >= start - 1e-6)
              and (end is None or n["start"] < end - 1e-6)]
    if not chosen:
        raise ValueError("no notes in that range")
    t0 = min(n["start"] for n in chosen)
    return [{"pitch": n["pitch"], "start": round(n["start"] - t0, 4), "length": round(n["length"], 4),
             "velocity": n.get("velocity", 100)} for n in sorted(chosen, key=lambda n: (n["start"], n["pitch"]))]


def transform(notes: list[dict], source_key: str, target_key: str | None = None, semitones: int = 0,
              octave: int = 0, stretch: float = 1.0) -> list[dict]:
    """The motif moved into `target_key` degree by degree (so D minor -> D major raises
    the 3rd, 6th and 7th; notes outside the scale move with the tonic), then shifted
    by semitones and octaves, and its rhythm stretched (2 = twice as slow)."""
    src = harmony.parse_key(source_key)
    out = []
    for n in notes:
        pitch = n["pitch"]
        if target_key:
            tgt = harmony.parse_key(target_key)
            shift = (tgt.tonic - src.tonic + 6) % 12 - 6
            rel = (pitch - src.tonic) % 12
            base = pitch - rel + shift
            degrees_src, degrees_tgt = src.degrees, tgt.degrees
            new_rel = degrees_tgt[degrees_src.index(rel)] if rel in degrees_src else rel
            pitch = base + new_rel
        pitch += semitones + 12 * octave
        out.append({**n, "pitch": max(0, min(127, pitch)), "start": round(n["start"] * stretch, 4),
                    "length": round(n["length"] * stretch, 4)})
    return out


@tool()
def save_motif(
    name: Annotated[str, Field(description="e.g. 'Earthfall title motif'")],
    item_id: ItemId,
    key: Annotated[str, Field(description="The key it's in, e.g. 'C minor' (so it can move to other keys)")],
    start: Annotated[float | None, Field(ge=0, description="Only notes from here (QN from the item start)")] = None,
    end: Annotated[float | None, Field(description="...up to here")] = None,
    description: Annotated[str | None, Field(description="What it's for, e.g. 'the game's signature; reuse in battle and victory'")] = None,
    overwrite: bool = False,
) -> dict:
    """Saves a motif (a theme's notes and rhythm) to reuse in other songs and projects,
    like a film or game score's leitmotif: place_motif puts it back in any key."""
    data = call("get_midi_notes", item_id=item_id, limit=5000)
    notes = capture(data.get("notes", []), start, end)
    harmony.parse_key(key)
    motifs = _load()
    if _key(name) in motifs and not overwrite:
        raise ValueError(f"there's already a motif called '{name}'; pick another name or set overwrite=true")
    motifs[_key(name)] = {"name": name.strip(), "key": key, "notes": notes, "description": description,
                          "saved": time.strftime("%Y-%m-%d")}
    _save(motifs)
    return {"saved": name.strip(), "key": key, "notes": _names(notes, key),
            "length_qn": max(n["start"] + n["length"] for n in notes)}


@tool(annotations=READ_ONLY)
def list_motifs() -> dict:
    """Lists the motifs (signature themes) saved with save_motif, in any project: each
    one's name, key, description, notes and length. Use it to pick a theme for
    place_motif, which puts it into a song in that song's key. Read-only."""
    return {"motifs": [{"name": m["name"], "key": m["key"], "description": m.get("description"),
                        "notes": _names(m["notes"], m["key"]),
                        "length_qn": max(n["start"] + n["length"] for n in m["notes"])} for m in _load().values()]}


@tool()
def place_motif(
    name: Annotated[str, Field(description="A motif from list_motifs")],
    item_id: ItemId,
    start: Annotated[float, Field(ge=0, description="Where it starts, in QN from the item start")] = 0.0,
    key: Annotated[str | None, Field(description="Move it into this key and mode, e.g. 'D minor', 'D major' (default: as saved)")] = None,
    octave: Annotated[int, Field(ge=-3, le=3, description="Octaves up (+) or down (-), e.g. -1 for low brass")] = 0,
    semitones: Annotated[int, Field(ge=-12, le=12, description="Extra transposition")] = 0,
    stretch: Annotated[float, Field(gt=0, le=8, description="Rhythm: 2 = twice as slow (a grand statement), 0.5 = twice as fast")] = 1.0,
    velocity: Annotated[int | None, Field(ge=1, le=127, description="Play every note at this velocity (default: as saved)")] = None,
) -> dict:
    """Puts a saved motif into a MIDI item (existing notes stay): in the song's key and
    mode, at an octave and speed that fit the moment."""
    motif = _load().get(_key(name))
    if not motif:
        names = ", ".join(m["name"] for m in _load().values()) or "none saved yet"
        raise ValueError(f"no motif called '{name}' (saved: {names})")
    notes = transform(motif["notes"], motif["key"], key, semitones, octave, stretch)
    payload = [{"pitch": n["pitch"], "start": round(start + n["start"], 4), "length": n["length"],
                "velocity": velocity or n["velocity"]} for n in notes]
    result = call("add_midi_notes", item_id=item_id, notes=payload)
    return {"placed": motif["name"], "in_key": key or motif["key"], "notes": _names(notes, key or motif["key"]),
            "starts_qn": start, "length_qn": max(n["start"] + n["length"] for n in notes), "item_notes": result.get("note_count")}
