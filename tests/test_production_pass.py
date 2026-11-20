"""add_production: the moves a first mix otherwise gets only after the user asks."""

import json

from creaper import server  # noqa: F401  (import order: server first)
from creaper import mix_tools, production_tools as pt, song_tools

FORM = [("Intro", 1, 9), ("Verse 1", 9, 25), ("Pre-chorus 1", 25, 33), ("Chorus 1", 33, 49), ("Verse 2", 49, 65),
        ("Chorus 2", 65, 81), ("Bridge", 81, 89), ("Chorus 3", 89, 105), ("Outro", 105, 113)]


def sections(form=FORM):
    return [{"name": n, "bar": float(a), "end": float(b)} for n, a, b in form]


def test_the_filter_moves_follow_the_form():
    """The values the user heard and kept on Glass Desert (2026-11-17)."""
    moves = {m["section"]: m for m in pt.plan_filter_moves(sections())}
    assert list(moves) == ["Intro", "Chorus 1", "Chorus 2", "Bridge"]
    assert moves["Intro"]["points"] == [(1.0, 450.0, "smooth"), (4.9, 6950.0, "linear"), (5.0, 20000.0, "linear")]
    assert moves["Chorus 1"]["points"] == [(30.99, 20000.0, "linear"), (31.0, 6950.0, "linear"),
                                           (32.95, 550.0, "linear"), (33.0, 20000.0, "linear")]
    assert moves["Bridge"]["points"][1:] == [(81.0, 850.0, "smooth"), (88.5, 6950.0, "linear"), (89.0, 20000.0, "linear")]
    # Chorus 3 comes out of the bridge, which is still opening: no dive on top of it.
    assert "Chorus 3" not in moves
    # Every move's points are in order, and so are the moves: one envelope, written in one go.
    bars = [p[0] for m in moves.values() for p in m["points"]]
    assert bars == sorted(bars)
    # A chorus after a 4-bar build dives over one bar; a first section that isn't an intro gets nothing.
    short = pt.plan_filter_moves(sections([("Verse", 1, 9), ("Build", 9, 13), ("Drop", 13, 29)]))
    assert [(m["section"], m["points"][1][0]) for m in short] == [("Drop", 12.0)]
    assert pt.plan_filter_moves(sections([("Chorus", 1, 17), ("Chorus 2", 17, 33)])) == []


TRACKS = [("Drums", 8, ["kick - 909 Kick", "snare - 909 Snare"]), ("Drums Parallel", 0, ["VST: ReaComp (Cockos)"]),
          ("Bass", 6, []), ("Bass Duck", 0, []), ("Pad", 6, ["VST3: Chorus JUN-6 (Arturia)"]), ("Lead", 4, []),
          ("Lead (MIDI)", 4, []), ("Guitar L", 4, []), ("Vox", 3, []), ("Transitions", 9, []),
          ("Reverb", 0, ["VST3: Rev PLATE-140 (Arturia)"]), ("Empty", 0, [])]


class Project:
    def __init__(self):
        self.tracks = [{"number": i + 1, "name": n, "guid": "{" + n + "}", "item_count": c, "fx": list(fx)}
                       for i, (n, c, fx) in enumerate(TRACKS)]
        next(t for t in self.tracks if t["name"] == "Lead (MIDI)")["hardware"] = {"role": "plays the synth (MIDI)"}
        self.calls: list[tuple[str, dict]] = []
        self.points = None

    def call(self, cmd, **kw):
        self.calls.append((cmd, kw))
        if cmd == "get_project_overview":
            return {"tracks": self.tracks,
                    "regions": [{"name": n, "start": {"bar": a}, "end": {"bar": b}} for n, a, b in FORM]}
        if cmd == "get_routing":
            return {"tracks": [{"name": t["name"], "to_master": t["name"] != "Bass",
                                **({"sends": [{"to": "Bass Duck"}]} if t["name"] == "Bass" else {})} for t in self.tracks]}
        if cmd == "create_bus":
            self.tracks.append({"number": 99, "name": kw["name"], "guid": "{Music}", "item_count": 0, "fx": list(kw["fx"])})
            return {"bus": {"number": 99, "guid": "{Music}"}, "fx": [{"index": 1, "name": kw["fx"][0]}]}
        if cmd == "read_automation":
            return {"point_count": len(self.points or [])}
        if cmd == "write_automation":
            self.points = kw["points"]
            return {"points_written": len(kw["points"])}
        if cmd == "get_track_details":
            t = next(t for t in self.tracks if kw["track"] in (t["guid"], t["number"], t["name"]))
            return {"name": t["name"], "number": t["number"], "sends": [],
                    "fx": [{"index": i + 1, "name": f} for i, f in enumerate(t["fx"])]}
        if cmd == "add_fx":
            return {"index": 3, "name": f"VST3: {kw['name']} (Arturia)"}
        if cmd in ("set_fx_parameters", "set_send"):
            return {"results": []}
        raise AssertionError(cmd)


def test_one_call_gathers_the_pitched_parts_and_writes_the_moves(tmp_path, monkeypatch):
    project = Project()
    monkeypatch.setattr(pt, "call", project.call)
    monkeypatch.setattr(mix_tools, "call", project.call)
    plan = tmp_path / "song - creaper song.json"
    plan.write_text(json.dumps({"auto_mix": {"at": "now", "tracks": ["Drums"], "buses": ["Drums Parallel"]}}))
    monkeypatch.setattr(song_tools, "_song_paths", lambda: (plan, tmp_path / "checks.json"))

    dry = pt.add_production(dry_run=True)
    assert dry["filter_moves"]["would_gather"] == ["Bass Duck", "Pad", "Lead", "Guitar L"]
    assert not any(c in ("create_bus", "write_automation", "add_fx") for c, _ in project.calls)

    out = pt.add_production()
    # The bass plays through its Duck bus, so that is what's gathered; drums, the vocal, the
    # transitions, the reverb return, the synth's MIDI half and an empty track stay outside.
    made = next(kw for c, kw in project.calls if c == "create_bus")
    assert made["tracks"] == ["{Bass Duck}", "{Pad}", "{Lead}", "{Guitar L}"] and made["fx"] == [pt.FILTER_FX]
    assert [m["section"] for m in out["filter_moves"]["moves"]] == ["Intro", "Chorus 1", "Chorus 2", "Bridge"]
    assert project.points[0] == {"bar": 1.0, "display_value": 450.0, "shape": "smooth"}
    assert [p["bar"] for p in project.points] == sorted(p["bar"] for p in project.points)
    # The lead gets its chorus; the pad already has one; a guitar isn't a synth part.
    by = {r["track"]: r for r in out["part_fx"]}
    assert by["Lead"]["chorus"]["plugin"].startswith("VST3: Chorus DIMENSION-D") and "already has" in by["Pad"]["left"]
    assert set(by) == {"Pad", "Lead"}
    marked = json.loads(plan.read_text())
    assert marked["production"]["at"] and marked["auto_mix"]["buses"] == ["Drums Parallel", "Music"]

    # A second run leaves the written moves alone.
    again = pt.add_production(part_fx=False)
    assert "already has moves" in again["filter_moves"]["skipped"]
    assert sum(1 for c, _ in project.calls if c == "create_bus") == 1


def test_the_mix_stage_asks_for_the_production_pass_once(monkeypatch):
    monkeypatch.setattr(song_tools, "call", lambda cmd, **kw: {"tracks": []})
    asked = song_tools._production_rows(song_tools._Context("new wave", {"auto_mix": {"at": "now"}}))
    assert [(r["check"], r["status"]) for r in asked] == [("production pass", "warn")] and "add_production()" in asked[0]["fix"]
    for plan in ({}, {"brief": "no mix yet"}, {"auto_mix": {"at": "now"}, "production": {"at": "now"}},
                 {"auto_mix": {"at": "now"}, "stages": {"mix": {"done": True}}}):
        assert song_tools._production_rows(song_tools._Context("new wave", plan)) == []
