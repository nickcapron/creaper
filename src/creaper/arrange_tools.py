"""Transitions and ear candy: the small touches that carry a listener from one section
to the next. At each section change creaper adds what a producer would: a riser or
reverse swell building into a bigger section, an impact and a crash on its downbeat,
a drum fill, the kick dropping out just before a drop; or a downlifter into a quieter
one. The sounds are synthesised (ear_candy.py), so they're original and fit the bars
exactly; fills, crashes and drop-outs go on the drum track's MIDI."""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Annotated, Literal

import soundfile as sf
from pydantic import Field

from . import ear_candy, theory
from .server import bridge, call, drum_maps, tool

# How much energy a section name suggests (1 quiet .. 4 the peak).
ENERGY = [  # in order: "pre-chorus" is a build and "post-chorus" a step down, not a chorus
    (r"pre[- ]?chorus|post[- ]?chorus|build|lift|rise|riser", 3),
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


# The same fills in a genre's own style (genres' fill_style, grooves.fill_style_for).
STYLED_FILLS = {
    "snare_roll": {"subtle": {"snare": "..57"}, "build": {"snare": "3456789X"},
                   "epic": {"snare": "o.o.o.o.xxxxXXXX"}},
    "clap_roll": {"subtle": {"clap": "..57"}, "build": {"clap": "3456789X"},
                  "epic": {"clap": "o.o.o.o.xxxxXXXX"}},
    "tom": {"subtle": {"low tom": "..5X"}, "build": {"high tom": "x.x.....", "mid tom": "....x...", "low tom": "......xX"},
            "epic": FILLS["epic"]},
}


def fill_for(intensity: str, fill_style: str | None) -> dict[str, str] | None:
    """The fill to write: in the genre's style when one is given (None for a genre
    whose fill is a drop-out or nothing), else the stock fills."""
    if not fill_style:
        return FILLS[intensity]
    if fill_style in ("dropout", "none"):
        return None
    return STYLED_FILLS.get(fill_style, STYLED_FILLS["snare_roll"])[intensity]


def energy(name: str) -> int:
    n = name.lower()
    return next((level for pattern, level in ENERGY if re.search(pattern, n)), 2)


def plan(sections: list[dict], intensity: str) -> list[dict]:
    """What each section change gets, scaled by how big a change it is. sections:
    [{'name', 'bar'}] in order.
    - A big lift (two energy levels, or into the peak: a chorus or drop) builds: a riser,
      a crash and a fill, an impact into the peak, and the kick dropping out before it.
      Repeated peaks alternate (riser and drop-out the first time, reverse swell and
      impact the next) so the song doesn't play the same trick every 16 bars.
    - A small lift (intro to verse) gets a reverse swell, a crash and (except subtle) a fill.
    - A fall gets a crash, and a downlifter when it's a big one (chorus to breakdown).
    - A change between equal sections gets a crash (and a small fill)."""
    out = []
    peaks = 0
    for prev, nxt in zip(sections, sections[1:]):
        if nxt["bar"] <= 1:
            continue
        before, after = energy(prev["name"]), energy(nxt["name"])
        jump = after - before
        into_peak = after == 4
        if jump > 0:
            direction = "up"
            big = jump >= 2 or into_peak
            if into_peak:
                peaks += 1
            alternate = into_peak and peaks % 2 == 0  # every other peak: a different build-up
            if intensity == "subtle":
                elements = ["reverse", "crash"] + (["fill"] if big else [])
            elif not big:
                elements = ["reverse", "crash", "fill"]
            elif intensity == "build":
                elements = (["reverse", "impact", "crash", "fill"] if alternate else
                            ["riser", "impact", "crash", "fill"] + (["dropout"] if into_peak else []))
            else:  # epic
                elements = ["riser", "reverse", "impact", "crash", "fill"] + (["dropout"] if into_peak and not alternate else [])
            if not into_peak:
                elements = [e for e in elements if e != "impact"]  # impacts are for the peaks
        elif jump < 0:
            direction = "down"
            big = jump <= -2
            elements = {"subtle": ["crash"], "build": (["downlifter", "crash"] if big else ["crash"]),
                        "epic": (["impact", "downlifter", "crash"] if big else ["downlifter", "crash"])}[intensity]
        else:
            direction = "level"
            elements = ["crash", "fill"] if intensity != "subtle" else ["crash"]
        out.append({"bar": nxt["bar"], "into": nxt["name"], "from": prev["name"], "from_bar": prev["bar"],
                    "direction": direction, "elements": elements})
    return out


RISER_BARS = {"subtle": 1, "build": 2, "epic": 4}


def _fx_folder() -> Path:
    project = call("project_paths").get("project")
    folder = Path(project).parent / "creaper transitions" if project else bridge.directory / "transitions"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def sections_from_regions(regions: list[dict]) -> list[dict]:
    """The song's sections from its regions: a region inside another (a 'vocals in' or a
    sound-effect region) isn't a section, and two regions starting on one bar are one
    change (the longer one names it), so no change gets two contradictory transitions."""
    spans = [(r["name"], r["start"]["bar"], r.get("end", {}).get("bar", r["start"]["bar"])) for r in regions]
    outer = [s for s in spans if not any(o is not s and o[1] <= s[1] and s[2] <= o[2] and (o[2] - o[1]) > (s[2] - s[1])
                                         for o in spans)]
    by_bar: dict[float, tuple] = {}
    for name, start, end in outer:
        if start not in by_bar or end - start > by_bar[start][2] - by_bar[start][1]:
            by_bar[start] = (name, start, end)
    return [{"name": n, "bar": b} for n, b, _ in sorted(by_bar.values(), key=lambda s: s[1])]


def _write(audio, folder: Path, name: str) -> str:
    path = folder / f"{name}_{uuid.uuid4().hex[:10]}.wav"
    sf.write(str(path), audio, ear_candy.FS, subtype="PCM_24")
    return str(path)


def _seconds(start_qn: float, end_qn: float) -> float:
    a, b = call("qn_to_times", qns=[start_qn, end_qn])
    return max(0.05, b - a)


def _drum_items(track) -> list[dict]:
    return [i for i in call("get_track_details", track=track).get("items", []) if i.get("type") == "midi"]


def _item_at(items: list[dict], qn: float) -> dict | None:
    return next((i for i in items if i["start"]["qn"] - 1e-6 <= qn < i["end"]["qn"] - 1e-6), None)


def _lane(item_id: str, lane: str) -> tuple[int, int]:
    """The note and MIDI channel a drum lane plays on this item's instrument: its own
    note names, a saved drum map (which may put each drum on its own channel), then
    General MIDI, as add_drum_pattern does."""
    context = call("get_instrument_notes", item_id=item_id, channel=10)
    names = {n["pitch"]: n["name"] for n in context.get("note_names", [])}
    saved = drum_maps.find(context.get("instrument"))
    found = theory.resolve_drum_lane(lane, saved[1] if saved else None, names)
    return found.pitch, found.channel or 10


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
    style: Annotated[str | None, Field(description=(
        "The song's genre: fills follow its fill style (a clap roll for house, toms for rock, no fill where the "
        "genre drops out instead)"))] = None,
) -> dict:
    """Adds transitions and ear candy at every section change, as a producer would: into
    a bigger section a riser (or reverse swell) building to it, an impact and a crash on
    its downbeat, a drum fill, and the kick dropping out just before a drop or chorus;
    into a quieter one a downlifter. Section energy comes from the names (intro, verse,
    pre-chorus, chorus/drop, breakdown, outro), so name the regions; regions inside
    another region aren't sections. The sounds are synthesised by creaper (original, no
    samples) on a 'Transitions' track; fills (replacing the groove under them), crashes
    and drop-outs go into the drum track's MIDI. Run it once the arrangement is laid
    out; a second run skips changes that already have transitions. Each change is
    several undo steps: to take it all off, delete the Transitions items and undo the
    drum edits. Returns what was added at each change."""
    overview = call("get_project_overview")
    fill_style = None
    if style:
        from . import genres, grooves

        fill_style = grooves.fill_style_for(genres.find(style))
    if sections is None:
        if overview.get("regions"):
            sections = sections_from_regions(overview["regions"])
        else:
            sections = [{"name": m["name"], "bar": m["position"]["bar"]} for m in overview.get("markers") or []]
    sections = sorted(({"name": str(s["name"]), "bar": float(s["bar"])} for s in sections), key=lambda s: s["bar"])
    if len(sections) < 2:
        raise ValueError("there are no section changes to mark: name the sections with regions (add_marker with "
                         "end_bar), or pass sections=[{'name': 'Chorus', 'bar': 17}, ...]")
    changes = plan(sections, intensity)
    if elements:  # only these of what each change was planned to get (no riser into an outro)
        for c in changes:
            c["elements"] = [e for e in c["elements"] if e in elements]
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
    placed = [i["start"]["bar"] for i in call("get_track_details", track=fx_ref).get("items", [])]
    for c in changes:
        done: list[str] = []
        at_qn = call("bar_to_qn", bar=c["bar"])["qn"]
        # Never reach back into the section before the one this change leaves.
        bars = max(1, min(RISER_BARS[intensity], int(c["bar"] - c.get("from_bar", 1)) or 1))
        if any(c["bar"] - bars - 0.01 <= b <= c["bar"] + 0.01 for b in placed):
            report.append({"bar": c["bar"], "into": c["into"], "direction": c["direction"], "added": [],
                           "skipped": "this change already has transitions (an earlier run)"})
            continue
        for e in c["elements"]:
            if e in ("riser", "reverse", "downlifter", "impact"):
                if e == "riser":
                    start_bar = max(1.0, c["bar"] - bars, c.get("from_bar", 1.0))
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
                    # The sub only for epic: at build intensity the kick and bass already land
                    # on this downbeat, and a sub drop on top piles up the low end.
                    audio = ear_candy.impact(seed=int(c["bar"]) + 11, sub=intensity == "epic")
                path = _write(audio, folder, e)
                call("insert_audio_file", timeout=120.0, path=path, track=fx_ref, start_bar=start_bar)
                done.append(e)
            elif drum_items:
                if e == "crash":
                    item = _item_at(drum_items, at_qn)
                    if item:
                        pitch, channel = _lane(item["id"], "crash")
                        call("add_midi_notes", item_id=item["id"], notes=[{
                            "pitch": pitch, "start": at_qn - item["start"]["qn"],
                            "length": 1.0, "velocity": 112, "channel": channel}])
                        done.append(e)
                elif e == "fill":
                    pattern = fill_for(intensity, fill_style)
                    if pattern is None:
                        continue  # this genre drops out (or plays on) instead of filling
                    steps = max(len(s) for s in pattern.values())
                    fill_start = at_qn - steps * 0.25
                    item = _item_at(drum_items, fill_start)
                    if item:
                        from .server import add_drum_pattern
                        rel = max(0.0, fill_start - item["start"]["qn"])
                        # The fill replaces the groove under it (the backbeat snare, and for
                        # a tom fill the hats), or the two play at once and flam.
                        toms = any("tom" in lane for lane in pattern)
                        clear = list(pattern) + (["closed hat", "open hat"] if toms and intensity == "epic" else []) + \
                            (["snare"] if toms else [])
                        for lane in clear:
                            call("delete_midi_notes", item_id=item["id"], start=rel, end=at_qn - item["start"]["qn"],
                                 pitch=_lane(item["id"], lane)[0])
                        add_drum_pattern(item_id=item["id"], pattern=dict(pattern), step=0.25, start=rel, feel="natural")
                        done.append(e)
                elif e == "dropout":
                    gap_start = at_qn - (bar_qn if intensity == "epic" else 2.0)
                    item = _item_at(drum_items, gap_start)
                    if item:
                        call("delete_midi_notes", item_id=item["id"], start=gap_start - item["start"]["qn"],
                             end=at_qn - item["start"]["qn"], pitch=_lane(item["id"], "kick")[0])
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
