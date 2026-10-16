"""Transitions and ear candy: the small touches that carry a listener from one section
to the next. At each section change creaper adds what a producer would: a riser or
reverse swell building into a bigger section, an impact and a crash on its downbeat,
a drum fill, the kick dropping out just before a drop; or a downlifter into a quieter
one. The sounds are synthesised (ear_candy.py), so they're original and fit the bars
exactly; fills, crashes and drop-outs go on the drum track's MIDI."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Annotated, Literal

import soundfile as sf
from pydantic import Field

from . import ear_candy, theory
from .server import bridge, call, drum_maps, tool

# How much energy a section name suggests (1 quiet .. 4 the peak).
ENERGY = [  # in order: "pre-chorus" is a build, not a chorus
    (r"pre[- ]?chorus|build|lift|rise|riser", 3),
    (r"drop|chorus|hook|refrain|climax|final", 4),
    (r"verse|main|groove|a section|b section|solo", 2),
    (r"break|bridge|interlude|outro|intro|ending|calm|ambient", 1),
]
Element = Literal["riser", "reverse", "impact", "downlifter", "crash", "fill", "dropout"]
FILLS = {  # (steps per lane, 16th steps) ending on the downbeat
    "subtle": {"snare": "..57"},
    "build": {"snare": "3456789X"},
    "epic": {"snare": "x.x.x.x.", "high tom": "........x.x.....", "mid tom": "............x.x.", "low tom": "..............xX"},
}


def energy(name: str) -> int:
    n = name.lower()
    return next((level for pattern, level in ENERGY if re.search(pattern, n)), 2)


def plan(sections: list[dict], intensity: str) -> list[dict]:
    """What each section change gets. sections: [{'name', 'bar'}] in order. A change into
    more energy builds (riser/reverse, impact, crash, fill, and a kick drop-out before a
    drop or chorus); into less energy falls (downlifter); level changes get a crash and
    a small fill."""
    out = []
    for prev, nxt in zip(sections, sections[1:]):
        if nxt["bar"] <= 1:
            continue
        before, after = energy(prev["name"]), energy(nxt["name"])
        if after > before:
            direction = "up"
            elements = {"subtle": ["reverse", "crash", "fill"],
                        "build": ["riser", "impact", "crash", "fill"],
                        "epic": ["riser", "reverse", "impact", "crash", "fill"]}[intensity]
            if after == 4 and intensity != "subtle":
                elements = elements + ["dropout"]
        elif after < before:
            direction = "down"
            elements = {"subtle": ["crash"], "build": ["downlifter", "crash"],
                        "epic": ["impact", "downlifter", "crash"]}[intensity]
        else:
            direction = "level"
            elements = ["crash", "fill"] if intensity != "subtle" else ["crash"]
        out.append({"bar": nxt["bar"], "into": nxt["name"], "from": prev["name"], "direction": direction,
                    "elements": elements})
    return out


RISER_BARS = {"subtle": 1, "build": 2, "epic": 4}


def _fx_folder() -> Path:
    project = call("project_paths").get("project")
    folder = Path(project).parent / "creaper transitions" if project else bridge.directory / "transitions"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _write(audio, folder: Path, name: str) -> str:
    path = folder / f"{name}_{time.strftime('%H%M%S')}_{abs(hash((name, time.time()))) % 10000:04d}.wav"
    sf.write(str(path), audio, ear_candy.FS, subtype="PCM_24")
    return str(path)


def _seconds(start_qn: float, end_qn: float) -> float:
    a, b = call("qn_to_times", qns=[start_qn, end_qn])
    return max(0.05, b - a)


def _drum_items(track) -> list[dict]:
    return [i for i in call("get_track_details", track=track).get("items", []) if i.get("type") == "midi"]


def _item_at(items: list[dict], qn: float) -> dict | None:
    return next((i for i in items if i["start"]["qn"] - 1e-6 <= qn < i["end"]["qn"] - 1e-6), None)


def _lane_pitch(item_id: str, lane: str) -> int:
    """The note a drum lane plays on this item's instrument: its own note names, a saved
    drum map, then General MIDI (as add_drum_pattern does)."""
    context = call("get_instrument_notes", item_id=item_id, channel=10)
    names = {n["pitch"]: n["name"] for n in context.get("note_names", [])}
    saved = drum_maps.find(context.get("instrument"))
    return theory.resolve_drum_lane(lane, saved[1] if saved else None, names).pitch


def _find_drum_track(tracks: list[dict]) -> dict | None:
    for t in tracks:
        if re.search(r"drum|kit|beat|groove", t["name"], re.I) and t.get("item_count"):
            return t
    return None


@tool()
def add_transitions(
    intensity: Annotated[Literal["subtle", "build", "epic"], Field(description=(
        "subtle: a reverse swell, crash and small fill; build (default): a 2-bar riser, impact, crash, fill, and "
        "the kick dropping out before a drop or chorus; epic: a 4-bar riser, reverse swell, impact and tom fill"))] = "build",
    sections: Annotated[list[dict] | None, Field(description=(
        "Section starts as [{'name': 'Chorus', 'bar': 17}, ...]; default: the project's regions (or markers)"))] = None,
    elements: Annotated[list[Element] | None, Field(description=(
        "Only these touches: riser, reverse, impact, downlifter, crash, fill, dropout; default: chosen per change"))] = None,
    drum_track: Annotated[str | int | None, Field(description="Track for fills, crashes and drop-outs; default: the one named Drums/Kit/Beat")] = None,
) -> dict:
    """Adds transitions and ear candy at every section change, as a producer would: into
    a bigger section a riser (or reverse swell) building to it, an impact and a crash on
    its downbeat, a drum fill, and the kick dropping out just before a drop or chorus;
    into a quieter one a downlifter. Section energy comes from the names (intro, verse,
    pre-chorus, chorus/drop, breakdown, outro), so name the regions. The sounds are
    synthesised by creaper (original, no samples) on a 'Transitions' track; fills,
    crashes and drop-outs go into the drum track's MIDI. Run it once the arrangement
    is laid out; undo removes it. Returns what was added at each change."""
    overview = call("get_project_overview")
    if sections is None:
        marks = overview.get("regions") or overview.get("markers") or []
        sections = [{"name": m["name"], "bar": m["start"]["bar"] if "start" in m else m["position"]["bar"]}
                    for m in marks]
    sections = sorted(({"name": str(s["name"]), "bar": float(s["bar"])} for s in sections), key=lambda s: s["bar"])
    if len(sections) < 2:
        raise ValueError("there are no section changes to mark: name the sections with regions (add_marker with "
                         "end_bar), or pass sections=[{'name': 'Chorus', 'bar': 17}, ...]")
    changes = plan(sections, intensity)
    if elements:
        for c in changes:
            c["elements"] = [e for e in c["elements"] if e in elements] or list(elements)
    tracks = overview["tracks"]
    drums = None
    if drum_track is not None:
        drums = call("describe_track", track=drum_track)
    else:
        drums = _find_drum_track(tracks)
    drum_ref = (drums or {}).get("guid") or (drums or {}).get("number")
    fx_track = next((t for t in tracks if t["name"] == "Transitions"), None)
    if fx_track is None:
        fx_track = call("create_track", name="Transitions")["track"]
        call("set_track_properties", track=fx_track["guid"], volume_db=-4.0)
    fx_ref = fx_track.get("guid") or fx_track["number"]
    folder = _fx_folder()
    bar_qn = _bar_qn(overview.get("time_signature"))
    report, notes = [], []
    drum_items = _drum_items(drum_ref) if drum_ref else []
    for c in changes:
        done: list[str] = []
        at_qn = call("bar_to_qn", bar=c["bar"])["qn"]
        bars = RISER_BARS[intensity]
        for e in c["elements"]:
            if e in ("riser", "reverse", "downlifter", "impact"):
                if e == "riser":
                    start_bar = max(1.0, c["bar"] - bars)
                    seconds = _seconds(at_qn - (c["bar"] - start_bar) * bar_qn, at_qn)
                    audio = ear_candy.riser(seconds, seed=int(c["bar"]))
                elif e == "reverse":
                    start_bar = max(1.0, c["bar"] - 1)
                    seconds = _seconds(at_qn - (c["bar"] - start_bar) * bar_qn, at_qn)
                    audio = ear_candy.reverse_swell(seconds, seed=int(c["bar"]) + 7)
                elif e == "downlifter":
                    start_bar = c["bar"]
                    audio = ear_candy.downlifter(_seconds(at_qn, at_qn + 2 * bar_qn), seed=int(c["bar"]) + 3)
                else:
                    start_bar = c["bar"]
                    audio = ear_candy.impact(seed=int(c["bar"]) + 11)
                path = _write(audio, folder, e)
                call("insert_audio_file", timeout=120.0, path=path, track=fx_ref, start_bar=start_bar)
                done.append(e)
            elif drum_items:
                if e == "crash":
                    item = _item_at(drum_items, at_qn)
                    if item:
                        call("add_midi_notes", item_id=item["id"], notes=[{
                            "pitch": _lane_pitch(item["id"], "crash"), "start": at_qn - item["start"]["qn"],
                            "length": 1.0, "velocity": 112, "channel": 10}])
                        done.append(e)
                elif e == "fill":
                    pattern = FILLS[intensity]
                    steps = max(len(s) for s in pattern.values())
                    fill_start = at_qn - steps * 0.25
                    item = _item_at(drum_items, fill_start)
                    if item:
                        from .server import add_drum_pattern
                        add_drum_pattern(item_id=item["id"], pattern=dict(pattern), step=0.25,
                                         start=max(0.0, fill_start - item["start"]["qn"]), feel="natural")
                        done.append(e)
                elif e == "dropout":
                    gap_start = at_qn - (bar_qn if intensity == "epic" else 2.0)
                    item = _item_at(drum_items, gap_start)
                    if item:
                        call("delete_midi_notes", item_id=item["id"], start=gap_start - item["start"]["qn"],
                             end=at_qn - item["start"]["qn"], pitch=_lane_pitch(item["id"], "kick"))
                        done.append(e)
        if any(e in ("crash", "fill", "dropout") for e in c["elements"]) and not drum_items:
            notes.append("no drum track was found (name it Drums, or pass drum_track), so fills, crashes and "
                         "drop-outs were skipped")
        report.append({"bar": c["bar"], "into": c["into"], "direction": c["direction"], "added": done})
    result = {"intensity": intensity, "changes": report, "transitions_track": fx_track.get("name", "Transitions"),
              "sounds_folder": str(folder)}
    if notes:
        result["note"] = notes[0]
    return result


def _bar_qn(meter: str | None) -> float:
    from .composer import _bar_len
    return _bar_len(meter or "4/4")
