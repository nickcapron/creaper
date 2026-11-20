"""The production pass: what makes a balanced mix sound like a record.

Two songs running, the first export had every part in place and at its level and the
user still asked for "more produced" (Night Patrol, 2026-11-07: the chorus, phaser and
drum-bus moves "came only after notes"; Glass Desert, 2026-11-17: asked three times).
Each time the answer was the same handful of moves, made by hand. They are here as one
call, with the values the user heard and kept on Glass Desert:

- the pitched parts on one 'Music' bus with a low pass that opens over the intro, dives
  over the last bars before each chorus or drop and snaps open on its downbeat, and
  closes at a bridge or breakdown to open again through it (the drums stay outside, so
  the beat carries the dive);
- each synth part through the effects its role is known by (mix_tools.add_part_fx).
"""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import Field

from . import arrange_tools, mix_tools
from .server import DESTRUCTIVE, call, tool

MUSIC_BUS = "Music"
FILTER_FX, FILTER_PARAM = "JS: Resonant Lowpass Filter", "Frequency (Hz)"
OPEN_HZ = 20000.0
INTRO_FROM_HZ, BREAK_FROM_HZ = 450.0, 850.0   # where an intro and a bridge start from
DIVE_TOP_HZ, DIVE_FLOOR_HZ = 6950.0, 550.0    # a dive drops to the first at once, then slides to the second
MIN_SECTION_BARS = 4                          # shorter than this there's no room for a move
# What stays outside the bus (mix_tools.DRUM_ROLES, spelled out: that module may still be loading).
NOT_MUSIC = {"kick", "drums", "snare", "perc", "vocal", "fx"}
MODULATION = re.compile(r"chorus|phaser|flang|ensemble|dimension|rotary|tremolo", re.I)


def plan_filter_moves(sections: list[dict]) -> list[dict]:
    """The low-pass moves for a song's sections ([{'name', 'bar', 'end'}] in order; 'end'
    may be None for the last): [{'move', 'section', 'points': [(bar, hz, shape)]}].
    An intro opens over its first bars; a chorus or drop reached from below gets a dive
    over the last two bars before it (one after a short section); a bridge, breakdown or
    interlude after something bigger starts closed and opens through its length."""
    moves = []
    for i, sec in enumerate(sections):
        level = arrange_tools.energy(sec["name"])
        length = (sec["end"] - sec["bar"]) if sec.get("end") else None
        prev = sections[i - 1] if i else None
        before = arrange_tools.energy(prev["name"]) if prev else None
        if i == 0 and re.search(r"intro", sec["name"], re.I) and length and length >= MIN_SECTION_BARS:
            opens = sec["bar"] + min(4.0, length / 2)
            moves.append({"move": "opens over the intro", "section": sec["name"], "points": [
                (sec["bar"], INTRO_FROM_HZ, "smooth"), (opens - 0.1, DIVE_TOP_HZ, "linear"), (opens, OPEN_HZ, "linear")]})
        elif prev and level == 4 and before < 4 and sec["bar"] - prev["bar"] >= MIN_SECTION_BARS:
            bars = 2.0 if sec["bar"] - prev["bar"] >= 8 else 1.0
            start = sec["bar"] - bars
            if moves and moves[-1]["points"][-1][0] > start - 0.01:
                continue      # the bridge before it is still opening: that is the build
            moves.append({"move": f"dives over the {bars:g} bar(s) before it", "section": sec["name"], "points": [
                (start - 0.01, OPEN_HZ, "linear"), (start, DIVE_TOP_HZ, "linear"),
                (sec["bar"] - 0.05, DIVE_FLOOR_HZ, "linear"), (sec["bar"], OPEN_HZ, "linear")]})
        elif (prev and re.search(r"break|bridge|interlude", sec["name"], re.I) and before > level
              and length and length >= MIN_SECTION_BARS and i < len(sections) - 1):
            moves.append({"move": "starts closed and opens through it", "section": sec["name"], "points": [
                (sec["bar"] - 0.01, OPEN_HZ, "linear"), (sec["bar"], BREAK_FROM_HZ, "smooth"),
                (sec["end"] - 0.5, DIVE_TOP_HZ, "linear"), (sec["end"], OPEN_HZ, "linear")]})
    return moves


def _sections(overview: dict) -> list[dict]:
    regions = overview.get("regions") or []
    out = arrange_tools.sections_from_regions(regions) if regions else []
    ends = {(r["name"], r["start"]["bar"]): (r.get("end") or {}).get("bar") for r in regions}
    for sec, nxt in zip(out, out[1:] + [None]):
        sec["end"] = nxt["bar"] if nxt else ends.get((sec["name"], sec["bar"]))
    return out


def music_sources(overview: dict, routing: dict) -> list[dict]:
    """The tracks that play the song's pitched parts straight into the master: what a
    Music bus gathers. Drums, vocals, effects, transitions, returns and a hardware part's
    MIDI half stay outside; a part that plays through a Duck bus or a layered folder is
    gathered there, where its sound reaches the master."""
    routes = {t["name"]: t for t in routing.get("tracks", [])}
    fed = {s["to"] for r in routes.values() for s in r.get("sends") or [] if not s.get("note")}
    out = []
    for t in overview.get("tracks", []):
        name, r = t["name"], routes.get(t["name"], {})
        if t.get("mute") or not r.get("to_master") or name == MUSIC_BUS:
            continue
        if "MIDI" in str((t.get("hardware") or {}).get("role", "")) or re.search(r" (Voice|Carrier)$", name):
            continue
        if re.search(r"verb|reverb|delay|return|\broom\b", name, re.I) and not t.get("item_count"):
            continue
        if not (t.get("item_count") or name in fed or r.get("folder")):
            continue
        role = mix_tools.role_of(name, kit=mix_tools.is_kit(t.get("fx", [])))
        if role in NOT_MUSIC:
            continue
        out.append({"name": name, "number": t["number"], "ref": t.get("guid") or t["number"], "role": role,
                    "fx": t.get("fx", []), "plays": bool(t.get("item_count"))})
    return out


def _filter_on(track: dict) -> int | None:
    return next((i + 1 for i, f in enumerate(track.get("fx", [])) if re.search(r"low ?pass", f, re.I)), None)


@tool(annotations=DESTRUCTIVE)
def add_production(
    filter_moves: Annotated[bool, Field(description=(
        "The pitched parts on a 'Music' bus whose low pass opens over the intro, dives into each chorus or drop "
        "and opens through a bridge or breakdown"))] = True,
    part_fx: Annotated[bool, Field(description=(
        "Each synth part (bass, pad, keys, arp, lead) with no chorus or phaser of its own through the effects "
        "its role is known by (add_part_fx)"))] = True,
    dry_run: Annotated[bool, Field(description="Only say what it would do")] = False,
) -> dict:
    """The production pass, once, after auto_mix: the moves that make a balanced mix sound
    produced, which users otherwise ask for after the first export ("more FX", "more
    produced"). The pitched parts go through one 'Music' bus with a low-pass filter that
    opens over the intro, dives over the last two bars before every chorus or drop and
    snaps open on its downbeat, and starts a bridge or breakdown closed to open through
    it; drums, vocals and transitions stay outside, so the beat and the riser carry each
    dive. Synth parts without a chorus or phaser get the one their role is known by,
    and their reverb and delay sends. Needs the sections named as regions. A second run
    leaves a bus that already has its moves and parts that already have their effect
    alone. Returns each move with its bars and what each part got. Then measure_tracks
    once: nothing should have become louder than its role. For more on top, by hand:
    write_automation on the bus's filter, a delay throw on a phrase's last note."""
    overview = call("get_project_overview")
    sources = music_sources(overview, call("get_routing"))
    out: dict = {}
    if filter_moves:
        out["filter_moves"] = _filter_moves(overview, sources, dry_run)
    if part_fx:
        out["part_fx"] = _part_fx(sources, dry_run)
    if dry_run:
        out["dry_run"] = True
        return out
    try:
        from . import song_tools
        song_tools.mark_produced(MUSIC_BUS if "bus" in (out.get("filter_moves") or {}) else None)
    except Exception as e:  # noqa: BLE001 - the moves stand whether or not the plan could be marked
        out["warning"] = f"song plan not marked: {e}"
    return out


def _filter_moves(overview: dict, sources: list[dict], dry_run: bool) -> dict:
    sections = _sections(overview)
    moves = plan_filter_moves(sections)
    if not moves:
        return {"skipped": "no section here calls for one (an intro, a chorus or drop after a calmer section, a bridge "
                           "or breakdown): name the sections as regions, or write_automation by hand"}
    bus = next((t for t in overview.get("tracks", []) if t["name"] == MUSIC_BUS and not t.get("item_count")), None)
    described = [{"section": m["section"], "move": m["move"], "bars": [round(m["points"][0][0], 1), m["points"][-1][0]]}
                 for m in moves]
    if bus is None and len(sources) < 2:
        return {"skipped": "fewer than two pitched parts play into the master: a filter on one part is its own sound "
                           "design (write_automation on that track)"}
    if dry_run:
        return {"bus": MUSIC_BUS, "would_gather": [s["name"] for s in sources] if bus is None else "already there",
                "moves": described}
    if bus is None:
        made = call("create_bus", name=MUSIC_BUS, tracks=[s["ref"] for s in sources], fx=[FILTER_FX])
        fx = (made.get("fx") or [{}])[0].get("index")
        ref = made["bus"].get("guid") or made["bus"]["number"]
        gathered = [s["name"] for s in sources]
        if fx is None:
            return {"bus": MUSIC_BUS, "gathered": gathered,
                    "problem": f"the bus is made but {FILTER_FX} couldn't be added: add a low-pass filter to it "
                               "(add_fx) and write its cutoff with write_automation at these bars", "moves": described}
    else:
        ref, fx, gathered = bus.get("guid") or bus["number"], _filter_on(bus), "already there"
        if fx is None:
            fx = call("add_fx", track=ref, name=FILTER_FX)["index"]
        written = call("read_automation", track=ref, target={"kind": "fx", "fx": fx, "parameter": FILTER_PARAM})
        if written.get("point_count") or written.get("points"):
            return {"bus": MUSIC_BUS, "skipped": "its filter already has moves written: they are left as they are "
                                                 "(clear_automation on it first to write them again)"}
    call("set_fx_parameters", track=ref, fx=fx, changes=[{"parameter": FILTER_PARAM, "display_value": OPEN_HZ}])
    points = [p for m in moves for p in m["points"]]
    if points[0][0] > 1:
        points.insert(0, (1.0, OPEN_HZ, "linear"))      # open from the top, not wherever the first move leaves it
    call("write_automation", track=ref, target={"kind": "fx", "fx": fx, "parameter": FILTER_PARAM}, replace=True,
         points=[{"bar": max(1.0, bar), "display_value": hz, "shape": shape} for bar, hz, shape in points])
    return {"bus": MUSIC_BUS, "gathered": gathered, "filter": FILTER_FX, "moves": described,
            "note": "the drums, vocals and transitions play past the bus, so they carry each dive; the parts' reverb "
                    "and delay sends go around it too, so their tails stay open"}


def _part_fx(sources: list[dict], dry_run: bool) -> list[dict]:
    rows = []
    for s in sources:
        if s["role"] not in mix_tools.PART_FX or not s["plays"]:
            continue
        have = next((f for f in s["fx"] if MODULATION.search(f)), None)
        if have:
            rows.append({"track": s["name"], "left": f"already has {have}"})
        elif dry_run:
            rows.append({"track": s["name"], "would_add": mix_tools.PART_FX[s["role"]]["chorus"]})
        else:
            try:
                rows.append(mix_tools.add_part_fx(track=s["ref"], role=s["role"]))
            except Exception as e:  # noqa: BLE001 - one part's effect failing doesn't stop the others
                rows.append({"track": s["name"], "not_added": str(e)[:160]})
    return rows
