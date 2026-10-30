"""MCP tools for whole songs: build_song writes every section as its own variant,
song_map shows what each section plays, start_song / finish_stage / song_status keep a
song's stages honest (each stage's checks run and a failing stage refuses), check_song
is the scorecard (one render, every check, a score out of 10 and what changed since
last time), and compare_to_reference measures the mix against a reference track."""

from __future__ import annotations

import math
import random
import re
import time
from pathlib import Path
from typing import Annotated, Literal

import numpy as np
import soundfile as sf
from pydantic import Field

from . import analysis, arrange_tools, composer, genres, harmony, jsonstore, lyric_melody, songmap, structure, styles
from .server import DESTRUCTIVE, READ_ONLY, bridge, call, confirm_with_user, tool

STAGES = ("form", "sounds", "parts", "feel", "transitions", "mix", "master")
STAGE_CHECKS = {
    "form": "named regions for every section, the length against the genre's form, the tempo in its range",
    "sounds": "every unmuted MIDI track has an instrument",
    "parts": "no section copies another on every track, no track loops all song, choruses busier than verses, "
             "the lead over the chords, a part somewhere that keeps a pulse",
    "feel": "drums and bass aren't one velocity on the grid (check_groove); each lead in tune over its busiest "
            "section, with no portamento sliding into its notes (check_tuning, one short render per lead)",
    "transitions": "under 40% copied bars, no 16-bar loop, each section's level matches its energy (one render)",
    "mix": "the mix against the genre's targets: dynamics, low end, harshness, mud (one render)",
    "master": "loudness and true peak for the genre, no clipping (one render); the section balance again for "
              "tracks whose fader or effects changed since the mix was signed off",
}
PART_TRACK = {"drums": "Drums", "bass": "Bass", "chords": "Chords", "lead": "Lead", "counter": "Counter"}
PART_ROLES = {"drums": ("drums",), "bass": ("bass",), "chords": ("keys", "pad"), "lead": ("lead",), "counter": ()}
MAX_SONG_BARS = 512
VOICE_LOW, VOICE_HIGH = "E3", "E4"   # a lead for a robot or sung vocal: near a speaking voice


# ------------------------------------------------------------------ helpers

def _bar_qn(overview: dict) -> float:
    return composer._bar_len(overview.get("time_signature") or "4/4")


def _sections(overview: dict) -> list[dict]:
    """The song's sections from its regions, in order: regions inside a longer one
    (a 'vocals in' marker region) aren't sections."""
    regions = [r for r in overview.get("regions", []) if r.get("start", {}).get("qn") is not None]
    spans = [(r["name"], r["start"]["qn"], r["end"]["qn"], r["start"].get("bar"), r["end"].get("bar")) for r in regions]
    outer = [s for s in spans if not any(o is not s and o[1] <= s[1] and s[2] <= o[2] and (o[2] - o[1]) > (s[2] - s[1])
                                         for o in spans)]
    seen: set = set()
    outer = [s for s in outer if (s[1], s[2]) not in seen and not seen.add((s[1], s[2]))]
    return [{"name": n, "start_qn": a, "end_qn": b, "start_bar": sb, "end_bar": eb, "energy": arrange_tools.energy(n)}
            for n, a, b, sb, eb in sorted(outer, key=lambda s: s[1])]


def _midi_tracks(overview: dict, only: list[str] | None = None) -> dict[str, list[dict]]:
    """Every (or the named) track's unmuted MIDI notes, with absolute QN starts."""
    out: dict[str, list[dict]] = {}
    wanted = {w.lower() for w in only} if only else None
    for t in overview.get("tracks", []):
        if wanted and t["name"].lower() not in wanted:
            continue
        details = call("get_track_details", track=t.get("guid") or t["name"])
        items = [i for i in details.get("items", []) if i.get("type") == "midi" and not i.get("muted")]
        notes = []
        for item in items:
            for n in call("get_midi_notes", item_id=item["id"], limit=20000).get("notes", []):
                if not n.get("muted"):
                    notes.append({**n, "start": item["start"]["qn"] + n["start"]})
        if notes:
            out[t["name"]] = notes
    return out


def _song_paths() -> tuple[Path, Path] | None:
    """(song plan, checks baseline) next to the saved project; None when it's unsaved."""
    info = call("project_paths")
    if not info.get("project"):
        return None
    rpp = Path(info["project"])
    return rpp.with_name(rpp.stem + " - creaper song.json"), rpp.with_name(rpp.stem + " - creaper checks.json")


def _plan() -> tuple[dict, Path]:
    paths = _song_paths()
    if not paths or not paths[0].exists():
        raise ValueError("this project has no song plan: start_song first")
    return jsonstore.read(paths[0], dict), paths[0]


class _Context:
    """What the checks need, each measured once: the overview, the song map, and one
    master render (its analysis and its structure)."""

    def __init__(self, genre: str | None, plan: dict | None = None):
        self.genre = genre
        self.plan = plan or {}
        self.overview = call("get_project_overview")
        self._map = None
        self._render = None

    @property
    def song_map(self) -> dict:
        if self._map is None:
            self._map = songmap.song_map(_midi_tracks(self.overview), _sections(self.overview), _bar_qn(self.overview))
        return self._map

    def render(self) -> tuple[dict, dict]:
        """(analyze_audio-style measurements, measure_structure's report) of the master."""
        if self._render is None:
            from . import ear_tools
            from .export_tools import _check_renders, _cleanup

            render = call("render_audio", timeout=900.0, track="master")
            _check_renders(render["files"])
            try:
                measured = analysis.analyze_file(render["files"][0])
                audio, fs = sf.read(render["files"][0], always_2d=True)
            finally:
                _cleanup(render["files"])
            self.mono, self.fs = audio.mean(axis=1), int(fs)
            try:
                shape = ear_tools.structure_of(audio, int(fs), render, self.overview, call("get_tempo_map"), self.genre)
            except ValueError as e:      # shorter than two bars
                shape = {"findings": [str(e)]}
            self._render = (measured, shape)
        return self._render


def _form_rows(ctx: _Context) -> list[dict]:
    secs = _sections(ctx.overview)
    rows = [songmap.row("named sections", "pass" if len(secs) >= 2 else "fail", len(secs), 2,
                        "name every section as a region (add_marker with end_bar)")]
    bars = sum((s["end_bar"] or 0) - (s["start_bar"] or 0) for s in secs)
    planned = target_bars(ctx.plan.get("length"), float(ctx.overview.get("tempo_bpm") or 120), _bar_qn(ctx.overview))
    if planned and secs:
        rows.append(songmap.graded("length against the plan", round(bars / planned, 2), 0.9, 0.6,
                                   f"the plan says {ctx.plan['length']} (about {planned} bars)",
                                   higher_is_worse=False, bars=bars))
    if ctx.genre and secs:
        g = genres.find(ctx.genre)
        form = structure.form_bars(g)
        if form and not planned:
            rows.append(songmap.graded("length against the genre's form", round(bars / form, 2), 0.75, 0.5,
                                       f"the {g.name} form is {form} bars: don't shorten sections to save work",
                                       higher_is_worse=False, bars=bars))
        bpm = float(ctx.overview.get("tempo_bpm") or 0)
        lo, hi = g.tempo
        inside = lo - 3 <= bpm <= hi + 3
        rows.append(songmap.row("tempo", "pass" if inside else "warn", bpm, [lo, hi],
                                f"{g.name} usually runs {lo}-{hi} BPM"))
    return rows


NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
                "nine": 9, "ten": 10, "twelve": 12, "sixteen": 16, "thirty": 30, "sixty": 60}


def target_bars(length: str | None, bpm: float, bar_qn: float) -> int | None:
    """Bars a length from the brief asks for: '16 bars', 'a 30 s loop', '3-4 minutes'
    (the shorter end of a range), 'a 3-minute song', 'three minutes', '3:30'; None when
    it gives no number."""
    if not length:
        return None
    text = length.lower()
    for word, n in NUMBER_WORDS.items():
        text = re.sub(rf"\b{word}\b", str(n), text)
    clock = re.search(r"(\d+):([0-5]\d)", text)
    if clock:
        seconds = int(clock.group(1)) * 60 + int(clock.group(2))
        return max(1, int(round(seconds * bpm / 60 / bar_qn)))
    m = re.search(r"(\d+(?:\.\d+)?)(?:\s*-\s*\d+(?:\.\d+)?)?\s*-?\s*(bars?|s\b|secs?|seconds?|m\b|mins?|minutes?)",
                  text)
    if not m:
        return None
    n, unit = float(m.group(1)), m.group(2)
    if unit.startswith("bar"):
        return int(round(n))
    seconds = n * 60 if unit.startswith("m") else n
    return max(1, int(round(seconds * bpm / 60 / bar_qn)))


# Synthesizers (not Analog Lab, which hosts pianos and organs too, nor samplers). In an
# acoustic style a synth on the bass, guitar or lead passed the sounds stage unremarked: a
# Prophet-VS bass and a Jup-8 pad called 'Harmonica' made a Zach Bryan-style song "more
# pop than country".
SYNTH_PLUGINS = re.compile(r"mini v|prophet|jup-8|jun-6|op-xa|cs-80|dx7|\bsem v|matrix-12|pigments|buchla|arp 2600|"
                           r"modular v|synthi|\bcz v|\bcmi v|acid v|ms-20|polymoog|korg|serum|massive|vital|sylenth|"
                           r"spire|\bdiva\b|repro|phase ?plant|vocoder|synclavier v", re.I)
REAL_INSTRUMENT_ROLES = ("bass", "guitar", "lead")


def _instrument_name(details: dict) -> str | None:
    index = details.get("instrument_fx")
    if index is None:
        return None
    for f in details.get("fx") or []:
        if isinstance(f, dict) and f.get("index") == index:
            return f.get("name")
    return None


def _sounds_rows(ctx: _Context) -> list[dict]:
    """Every MIDI track has an instrument; before the parts are written, the tracks with
    their sounds chosen count (the sounds stage comes before the parts). In an acoustic
    style (country and folk, blues) a synth on the bass, guitar or lead is a warning that
    names the real instruments the style and the sample library have."""
    from . import mix_tools

    rows = []
    acoustic = None
    try:
        genre = getattr(ctx, "genre", None)
        acoustic = genres.find(genre) if genre else None
        if acoustic is not None and acoustic.family not in mix_tools.ACOUSTIC_FAMILIES:
            acoustic = None
    except Exception:  # noqa: BLE001 - an unknown genre: no style to hold the sounds to
        acoustic = None
    for t in ctx.overview.get("tracks", []):
        if t.get("mute"):
            continue      # a muted guide (a robot vocal's melody) plays nothing: it needs no instrument
        details = call("get_track_details", track=t.get("guid") or t["name"])
        # An empty MIDI item plays nothing, so it needs no instrument (one on a noise
        # generator's track failed this check though the generator sounded fine).
        midi = [i for i in details.get("items", []) if i.get("type") == "midi" and not i.get("muted")
                and i.get("note_count", 1) > 0]
        has = details.get("instrument_fx") is not None
        if midi or has:
            rows.append(songmap.row("instrument", "pass" if has else "fail", None, None,
                                    "load a sound: audition_sounds or load_arturia_preset", track=t["name"]))
        name = _instrument_name(details)
        role = mix_tools.role_of(t["name"])
        if acoustic is not None and name and role in REAL_INSTRUMENT_ROLES and SYNTH_PLUGINS.search(name):
            how = {"bass": acoustic.bass, "lead": acoustic.melody, "guitar": acoustic.harmony}.get(role) or ""
            rows.append(songmap.row(
                "instrument fits the style", "warn", None, None,
                f"a real {role}: find_samples(role='{role}') or search 'acoustic bass', 'banjo', 'mandolin', 'violin', "
                "'steel' and build_sampled_instrument from the hits (the library has them), or an Analog Lab acoustic "
                "preset; keep the synth only if the user asked for one",
                track=t["name"], detail=f"{name} is a synthesizer playing the {role} in {acoustic.name}"
                + (f": {how}" if how else "")))
    return rows or [songmap.row("instrument", "fail", None, None,
                                "no sounds yet: a track per part with its sound (audition_sounds)")]


def _parts_rows(ctx: _Context) -> list[dict]:
    m = ctx.song_map
    if not any(s["tracks"] for s in m["sections"]):
        return [songmap.row("parts", "fail", None, None, "no notes in any section: write the parts (build_song)")]
    rows = [songmap.row(f["check"], f["status"], f.get("value"), f.get("threshold"), f.get("fix"),
                        section=f.get("section"), track=f.get("track"), detail=f.get("detail"))
            for f in m["findings"]]
    if not any(r["status"] == "fail" for r in rows):
        rows.insert(0, songmap.row("section copies", "pass", None, None))
    if m["sections"] and not any(r["check"] == "density arc" for r in rows):
        rows.append(songmap.row("density arc", "pass", None, None))
    return rows


def _feel_rows(ctx: _Context) -> list[dict]:
    from . import ear_tools, mix_tools

    rows = []
    for t in ctx.overview.get("tracks", []):
        role = mix_tools.role_of(t["name"])
        if role not in ("drums", "kick", "snare", "perc", "bass"):
            continue
        try:
            report = ear_tools.check_groove(track=t.get("guid") or t["name"], genre=ctx.genre)
        except ValueError:
            continue      # no MIDI on it
        verdict = report.get("verdict")
        if verdict == "n/a":
            continue
        status = {"pass": "pass", "check": "warn"}.get(verdict, "fail")
        rows.append(songmap.row("groove", status, None, None,
                                "; ".join(report.get("findings", [])[:2]) or "apply_feel with the part's role",
                                track=t["name"]))
    if not rows and not any(s["tracks"] for s in ctx.song_map["sections"]):
        return [songmap.row("groove", "fail", None, None, "no parts written yet")]
    rows = rows or [songmap.row("groove", "warn", None, None, "no MIDI drums or bass to check")]
    return rows + _lead_tuning_rows(ctx)


TUNING_BARS = 16    # the lead is checked over its busiest section, up to this many bars (one short render)


def _lead_tuning_rows(ctx: _Context) -> list[dict]:
    """check_tuning on each lead over its busiest section: a patch with portamento on or
    detuned oscillators reached the user as "a bit out of tune" while every other check
    passed (the sounds stage plays single notes, which can't show a glide)."""
    from . import ear_tools, mix_tools

    sections = {s["name"]: s for s in _sections(ctx.overview)}
    rows = []
    for t in ctx.overview.get("tracks", []):
        if t.get("mute") or mix_tools.role_of(t["name"]) != "lead":
            continue
        busiest = max(((row["tracks"][t["name"]].get("notes_per_bar", 0) * row.get("bars", 0), row["section"])
                       for row in ctx.song_map["sections"] if t["name"] in row["tracks"]), default=None)
        span = sections.get(busiest[1]) if busiest and busiest[0] > 0 else None
        if not span or span.get("start_bar") is None or span.get("end_bar") is None:
            continue
        start = span["start_bar"]
        try:
            report = ear_tools.check_tuning(track=t.get("guid") or t["name"], start_bar=start,
                                            end_bar=min(span["end_bar"], start + TUNING_BARS))
        except Exception:  # noqa: BLE001 - a check that can't run isn't a finding
            continue
        verdict = report.get("verdict")
        if not verdict:
            continue
        ok = verdict == "in tune" or verdict.startswith("no clean")
        rows.append(songmap.row("tuning", "pass" if ok else "warn", report.get("median_cents"), None,
                                None if ok else verdict, track=t["name"], section=span["name"]))
    return rows


def _silent(ctx: _Context) -> list[dict] | None:
    measured, _ = ctx.render()
    if measured.get("silent"):
        return [songmap.row("sound", "fail", None, None, "the master is silent: load instruments, unmute the tracks")]
    return None


def _transitions_rows(ctx: _Context) -> list[dict]:
    if (silent := _silent(ctx)) is not None:
        return silent
    _, shape = ctx.render()
    rows = []
    if "near_duplicate_share" in shape:
        rows.append(songmap.graded("copied bars", shape["near_duplicate_share"], 0.4, 0.6,
                                   "change something every 8 bars: a part in or out, a variation, a new voicing"))
        rows.append(songmap.graded("longest loop (bars)", shape.get("longest_loop_bars"), 16, 32,
                                   "the same 4 bars run too long: vary the drums and bass by section"))
    else:
        rows.append(songmap.row("structure", "warn", None, None, "; ".join(shape.get("findings", []))
                                or shape.get("note") or "too short to judge"))
        return rows
    for f in shape.get("findings", []):
        if f.startswith("it develops") or "copies of other bars" in f or "bars run with" in f or "form runs to" in f:
            continue      # the graded rows above and the form stage cover these
        if " plays like " in f:
            rows.append(songmap.row("section repeats", "warn", None, None, "vary it: new parts, another groove or "
                                    "voicing (a returning chorus can share its hook, not everything)", detail=f))
        elif " should lift " in f or " should drop " in f:
            rows.append(songmap.row("energy arc", "warn", None, None, "add_transitions, write_automation ramps, "
                                    "thin the verse or lift the chorus", detail=f))
        else:
            rows.append(songmap.row("structure", "warn", None, None, f))
    if not any(r["check"] == "energy arc" for r in rows):
        rows.append(songmap.row("energy arc", "pass", None, None))
    return rows


_MASTER_AREAS = ("integrated loudness", "true peak")
# A fader this far (dB) from where the mix was signed off, or a new effect on a track,
# means the balance the mix stage checked may be gone: mastering once added limiters
# to five parts and raised the lead 3 dB, and the user heard it as overpowering.
MOVED_DB = 1.0


def _mix_snapshot(overview: dict) -> dict:
    """Each track's fader and effects when the mix is signed off."""
    return {t.get("guid") or t["name"]: {"name": t["name"], "volume_db": t.get("volume_db"),
                                         "fx": list(t.get("fx") or [])} for t in overview.get("tracks", [])}


def _moved_since_mix(ctx: _Context) -> dict[str, str]:
    """{track: what changed} for tracks whose fader or effects changed since finish_stage('mix')."""
    snap = ((ctx.plan.get("stages") or {}).get("mix") or {}).get("tracks") or {}
    moved = {}
    for t in ctx.overview.get("tracks", []):
        was = snap.get(t.get("guid") or t["name"])
        if not was:
            continue
        changes = []
        if None not in (t.get("volume_db"), was.get("volume_db")) and abs(t["volume_db"] - was["volume_db"]) >= MOVED_DB:
            changes.append(f"fader {t['volume_db'] - was['volume_db']:+.1f} dB")
        added = [f for f in t.get("fx") or [] if f not in was.get("fx", [])]
        if added:
            changes.append("added " + ", ".join(added))
        if changes:
            moved[t["name"]] = "; ".join(changes)
    return moved


def _balance_rows(ctx: _Context) -> list[dict]:
    """The section balance again (measure_tracks per_section), for the tracks changed
    since the mix was signed off; nothing to render when none were."""
    moved = _moved_since_mix(ctx)
    if not moved:
        return []
    from . import ear_tools

    lines = ear_tools.measure_tracks(per_section=True).get("balance", [])
    rows = []
    for name, change in moved.items():
        flagged = [line for line in lines if f": {name} is " in line]
        rows.append(songmap.row(
            "balance since the mix", "warn" if flagged else "pass", None, None,
            "put it back near its place (fader or the new effect), then measure_tracks(per_section=True)",
            track=name, detail=f"{change} since the mix was signed off" + (": " + "; ".join(flagged[:3]) if flagged else "")))
    return rows


# Mix effects set by hand before auto_mix (not instruments: 'Equator', 'Compact Grand').
HAND_MIX_FX = re.compile(r"rea(eq|comp|xcomp|limit|gate)|pro-[qcl]\b|fet-76|bus force|\beq\b|compressor|limiter", re.I)
VOCAL_PROBE_S = 6.0     # how much of a vocal track is rendered to hear whether it has a take


def mark_mixed(channels: list[str]) -> None:
    """auto_mix records that it ran (and which tracks it mixed) in the song plan, when
    there is one: finish_stage("mix") asks for it."""
    paths = _song_paths()
    if not paths or not paths[0].exists():
        return
    with jsonstore.updating(paths[0], dict, indent=2) as data:
        data["auto_mix"] = {"at": time.strftime("%Y-%m-%d %H:%M"), "tracks": channels}


def _mix_rows(ctx: _Context) -> list[dict]:
    """What the mix stage needs before the style checks: an auto_mix run (one pass that
    balances, EQs and glues every track from measurements; the model otherwise hand-EQs
    track by track, 6-39 parameter edits a song, and the mix never gets its balance) and
    a sung vocal that sounds (a Donny Benet session stopped the song to wait for one)."""
    from . import vocal_tools

    rows: list[dict] = []
    if not ctx.plan:
        return rows      # no song plan (unsaved, or no start_song): nothing holds the mix to a run
    tracks = ctx.overview.get("tracks", [])
    mixed_before = bool(((ctx.plan.get("stages") or {}).get("mix") or {}).get("done"))   # a plan from before v0.48
    mark = ctx.plan.get("auto_mix") or {}
    if not mark and not mixed_before:
        by_hand = [t["name"] for t in tracks if any(HAND_MIX_FX.search(f or "") for f in t.get("fx") or [])]
        rows.append(songmap.row(
            "auto_mix", "fail", None, None,
            "auto_mix(style, roles=) first: one pass balances, EQs and glues every track from what it measures"
            + (f"; the hand-set effects on {', '.join(by_hand[:6])} are what it does, from the measured mix" if by_hand else "")
            + "; then refine what measure_tracks still flags"))
    elif mark.get("tracks"):
        unmixed = [t["name"] for t in tracks if t["name"] not in mark["tracks"] and not t.get("mute")
                   and not str(t.get("name", "")).lower().startswith(("reverb", "delay", "fx "))]
        if unmixed:
            rows.append(songmap.row(
                "auto_mix", "warn", None, None,
                "auto_mix again (or measure_tracks them and set their levels and EQ to match the rest)",
                detail=f"added since the auto_mix run, so unbalanced: {', '.join(unmixed[:6])}"))
    for t in tracks:
        if not any("vocalvst" in (f or "").lower() for f in t.get("fx") or []) or t.get("mute"):
            continue
        try:
            details = call("get_track_details", track=t.get("guid") or t["name"])
            items = [i for i in details.get("items", []) if i.get("type") == "midi" and not i.get("muted")]
            if not items:
                continue
            # Only the seconds where the singing starts: a take sounds there, and a whole-song
            # render per vocal on every check_song would cost more than the check is worth.
            # The first note, not the item's start: a country song's vocal item began at bar 1
            # with eight bars of intro before the first word, and the probe called it silent.
            first_qn = None
            for item in items:
                notes = call("get_midi_notes", item_id=item["id"], limit=20000).get("notes", [])
                starts = [float(item["start"]["qn"]) + float(n["start"]) for n in notes if not n.get("muted")]
                if starts and (first_qn is None or min(starts) < first_qn):
                    first_qn = min(starts)
            if first_qn is None:
                continue      # no notes: nothing to sing yet
            start = float(call("qn_to_times", qns=[first_qn])[0])
            end = min(max(i["end"]["seconds"] for i in items) + 1.0, start + VOCAL_PROBE_S)
            sounding = vocal_tools._track_audio(t.get("guid") or t["name"], start, end)[0]
        except Exception as e:  # noqa: BLE001 - say so rather than pass a vocal nobody heard
            rows.append(songmap.row("vocal take", "warn", None, None, "analyze_audio the track to hear whether it has a take",
                                    track=t["name"], detail=f"couldn't be checked: {e}"))
            continue
        if not sounding:
            rows.append(songmap.row(
                "vocal take", "warn", None, None,
                "render_vocalvst it, or mute the track and finish the song without it; the mix doesn't wait for a "
                "vocal, and the user isn't asked to", track=t["name"],
                detail="VocalVST has no take on this track: it plays silence over its notes"))
    return rows


def _style_rows(ctx: _Context, master: bool) -> list[dict]:
    if (silent := _silent(ctx)) is not None:
        return silent
    measured, _ = ctx.render()
    rows = [] if master else _mix_rows(ctx)
    if master:
        problems = styles.gate_problems(measured, styles.find_style(ctx.genre) if ctx.genre else None)
        rows.append(songmap.row("release gates", "fail" if problems else "pass", None, None, "; ".join(problems)))
        rows += _balance_rows(ctx)
    if not ctx.genre:
        return rows or [songmap.row("style", "warn", None, None, "give the genre to judge the mix against it")]
    for f in styles.compare(measured, styles.find_style(ctx.genre)):
        is_master = f["area"].startswith(_MASTER_AREAS)
        if is_master != master or f["verdict"] == "info":
            continue
        status = {"ok": "pass", "fail": "fail"}.get(f["verdict"], "warn")
        rows.append(songmap.row(f["area"], status, f.get("measured"), f.get("typical"), f.get("advice")))
    return rows


def _rows_for(stage: str, ctx: _Context) -> list[dict]:
    return {"form": _form_rows, "sounds": _sounds_rows, "parts": _parts_rows, "feel": _feel_rows,
            "transitions": _transitions_rows, "mix": lambda c: _style_rows(c, False),
            "master": lambda c: _style_rows(c, True)}[stage](ctx)


# --------------------------------------------------------------- song map

@tool(annotations=READ_ONLY)
def song_map(
    tracks: Annotated[list[str] | None, Field(description="Track names to include; default: every MIDI track")] = None,
) -> dict:
    """Maps what each section plays, track by track, from the MIDI (no render): notes
    per bar, the share of bars that are distinct, the register, whether a section plays
    exactly like an earlier one on that track (same_as) and how much of it repeats bars
    heard before (copied_share). Findings name what listeners hear as "it loops": a
    section that copies another on every track, a track that loops all song, choruses
    no busier than the verses, a lead under the chords. Name sections as regions first.
    Read-only."""
    overview = call("get_project_overview")
    sections = _sections(overview)
    if not sections:
        raise ValueError("name the sections as regions first (add_marker with end_bar)")
    notes = _midi_tracks(overview, tracks)
    if not notes:
        raise ValueError("no MIDI notes on " + (", ".join(tracks) if tracks else "any track"))
    out = songmap.song_map(notes, sections, _bar_qn(overview))
    out["how_to_read"] = ("notes_per_bar: how busy; distinct_bars: share of its bars that differ (1 = every bar new); "
                          "same_as: plays that section's part note for note; copied_share: share of its bars heard "
                          "earlier on that track; per_beat: strikes a beat on the section's busiest track (under 1.5 "
                          "nothing keeps a pulse). A returning chorus hook is meant to repeat; the parts around it "
                          "shouldn't all.")
    return out


# ------------------------------------------------------------- build_song

def _parse_sections(sections: list[str], form: list[tuple[str, int]]) -> list[tuple[str, int]]:
    out = []
    for s in sections:
        m = re.match(r"^\s*(.+?)\s*[:=]\s*(\d+)\s*$", s)
        if m:
            out.append((m.group(1), int(m.group(2))))
            continue
        name = s.strip()
        kind = composer.section_kind(name)
        bars = next((b for n, b in form if composer.section_kind(n) == kind), 8)
        out.append((name, bars))
    return out


def _numbered(form: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """Section names from a genre's form, numbered when they repeat: Verse 1, Verse 2."""
    counts: dict[str, int] = {}
    for n, _ in form:
        counts[n.lower()] = counts.get(n.lower(), 0) + 1
    seen: dict[str, int] = {}
    out = []
    for n, b in form:
        title = n[:1].upper() + n[1:]
        if counts[n.lower()] > 1:
            seen[n.lower()] = seen.get(n.lower(), 0) + 1
            title = f"{title} {seen[n.lower()]}"
        out.append((title, b))
    return out


def _kick_positions(g, bar_qn: float) -> list[float]:
    pattern = g.groove.get("pattern", {})
    step = g.groove.get("step", 0.25)
    lane = pattern.get("kick")
    if not lane:
        return []
    cells = [c for c in lane if c not in " |"][: max(1, int(round(bar_qn / step)))]
    return [round(i * step, 6) for i, c in enumerate(cells) if c not in ".-"]


def _find_tracks(overview: dict, parts: list[str]) -> dict[str, dict]:
    """The existing track for each part: one named exactly (Drums, Bass, Chords, Lead,
    Counter), else one whose role fits (mix_tools.role_of: 'Bass Drum' is a kick, 'Pad
    Lead' a pad). A track serves one part only; a 'counter' track only the counter."""
    from .mix_tools import role_of

    tracks = overview.get("tracks", [])
    claimed: set = set()
    out: dict[str, dict] = {}
    for part in parts:
        t = next((t for t in tracks if t["name"].lower() == PART_TRACK[part].lower()), None)
        if t is not None:
            out[part] = t
            claimed.add(t["name"])
    for part in [p for p in ("counter", "drums", "bass", "chords", "lead") if p in parts and p not in out]:
        for t in tracks:
            name = t["name"].lower()
            if t["name"] in claimed or ("counter" in name) != (part == "counter"):
                continue
            if part == "counter" or role_of(t["name"]) in PART_ROLES[part]:
                out[part] = t
                claimed.add(t["name"])
                break
    return out


@tool(annotations=DESTRUCTIVE)
def build_song(
    genre: Annotated[str, Field(description="A genre from list_genres")],
    key: Annotated[str | None, Field(description="e.g. 'A minor'; default: the genre's first key")] = None,
    sections: Annotated[list[str] | None, Field(description=(
        "Sections in order as 'Name:bars', e.g. ['Intro:4', 'Verse 1:16', 'Chorus 1:8', ...] (a name alone takes "
        "the genre form's length for that kind); default: the project's regions, else the genre's form"))] = None,
    instruments: Annotated[dict[str, str] | None, Field(description=(
        "Plugin for parts whose track doesn't exist yet: {'drums', 'bass', 'chords', 'lead', 'counter'}. Tracks "
        "already named Drums/Kit, Bass, Chords/Pad/Keys, Lead/Melody, Counter (with the sounds chosen) are reused"))] = None,
    tempo: Annotated[float | None, Field(gt=20, le=400, description="BPM; default: the genre's when the project is empty")] = None,
    lift_last_chorus: Annotated[bool, Field(description=(
        "The last chorus a whole step up: cheesy outside ballads, gospel and musicals, so only when the user asks"))] = False,
    seed: Annotated[int | None, Field(description="Same seed, same song; default: a new one (returned)")] = None,
    replace: Annotated[bool, Field(description=(
        "Delete MIDI items already on those tracks inside the song first (asks the user); without it, refuses"))] = False,
    lead_for: Annotated[Literal["instrument", "voice"], Field(description=(
        "voice: the lead is for add_robot_vocal to sing, so it's written low (E3-E4) and sparse, where words stay "
        "clear, with no counter-melody under it"))] = "instrument",
) -> dict:
    """Writes a whole song, section by section, each section its own variant: the
    harmony planned per section (plan_harmony: a verse, a chorus that turns, a
    pre-chorus that leans in, a reharmonised bridge), drums at each section's energy with
    their own variations and fills, bass and chords on each section's seed, a new
    verse line each verse and the same hook in every chorus, a counter-melody from the
    second chorus on, and thinner intros, breakdowns and outros. Creates the regions
    when the sections come from the genre's form or the list. One MIDI item per
    section and part, so each can be edited, re-written or swapped. Sounds, transitions
    and the mix are separate steps. Returns the plan and the song map."""
    from . import music_tools

    g = genres.find(genre)
    k = harmony.parse_key(key) if key else harmony.parse_key(
        g.keys[0] if g.keys else f"{'A' if 'minor' in g.modes[0] else 'C'} {g.modes[0]}")
    seed = seed if seed is not None else random.randrange(1, 10 ** 4)
    overview = call("get_project_overview")
    existing = _sections(overview)
    fresh = not overview.get("tracks") and not existing
    num, den = (int(x) for x in g.meter.split("/"))
    bar_qn = composer._bar_len(g.meter) if fresh else _bar_qn(overview)
    if sections and existing:
        raise ValueError("the project already has regions: leave sections out to write into them, or delete them "
                         "first (delete_marker)")
    if sections:
        layout = _parse_sections(sections, list(g.form))
        make_regions = True
    elif existing:
        layout = [(s["name"], int(round((s["end_qn"] - s["start_qn"]) / bar_qn))) for s in existing]
        make_regions = False
    else:
        layout = _numbered(list(g.form))
        make_regions = True
    total = sum(b for _, b in layout)
    if total > MAX_SONG_BARS or any(b < 1 for _, b in layout):
        raise ValueError(f"the song would be {total} bars; keep it to {MAX_SONG_BARS} with every section a bar or more")
    # The genre's meter only in an empty project: regions already laid out keep theirs.
    if fresh:
        call("set_tempo", bpm=tempo or g.tempo_default, numerator=num, denominator=den)
    elif tempo is not None:
        call("set_tempo", bpm=tempo)
    overview = call("get_project_overview")
    plan = songmap.plan_song(g, layout, seed, [arrange_tools.energy(n) for n, _ in layout])
    if lead_for == "voice":
        for row in plan:
            row["parts"].pop("counter", None)
    if not make_regions:   # each section where its region is (there can be gaps between them)
        for row, s in zip(plan, existing):
            row["start_bar"] = int(s["start_bar"])
    harmony_rows = composer.plan_harmony(list(g.progressions), k, [n for n, _ in layout], lift_last_chorus, seed,
                                         default_mode=g.modes[0])
    chord_qn = round(bar_qn / g.harmonic_rhythm, 6)

    # Tracks: reuse the ones with sounds already chosen, make the rest.
    used = [p for p in songmap.PARTS if any(p in row["parts"] for row in plan)]
    found = _find_tracks(overview, used)
    tracks: dict[str, dict] = {}
    for part in used:
        t = found.get(part)
        if t is None:
            made = call("create_track", timeout=60.0, name=PART_TRACK[part], instrument=(instruments or {}).get(part))
            t = {"name": PART_TRACK[part], "guid": made["track"].get("guid"), "number": made["track"]["number"],
                 "created": True, "warning": made.get("warning")}
        tracks[part] = t
    spans = [((row["start_bar"] - 1) * bar_qn, (row["start_bar"] - 1 + row["bars"]) * bar_qn) for row in plan]
    in_the_way: dict[str, str] = {}      # item id -> track name
    for part, t in tracks.items():
        if t.get("created"):
            continue
        for item in call("get_track_details", track=t.get("guid") or t["name"]).get("items", []):
            if item.get("type") == "midi" and any(item["start"]["qn"] < hi - 1e-6 and item["end"]["qn"] > lo + 1e-6
                                                  for lo, hi in spans):
                in_the_way[item["id"]] = t["name"]
    if in_the_way and not replace:
        names = sorted(set(in_the_way.values()))
        raise ValueError(f"{', '.join(names)} already {'has' if len(names) == 1 else 'have'} MIDI inside the song's "
                         "sections: pass replace=True to delete it first, or move it")
    if in_the_way:
        confirm_with_user(f"delete {len(in_the_way)} MIDI items on {', '.join(sorted(set(in_the_way.values())))}")
        for item_id in in_the_way:
            call("delete_item", item_id=item_id)
    if make_regions:
        for row in plan:
            call("add_marker", name=row["section"], start_bar=row["start_bar"], end_bar=row["start_bar"] + row["bars"])

    kicks = _kick_positions(g, bar_qn)
    played_as = music_tools.feel_mod_for(g)
    written = []
    for row, chords in zip(plan, harmony_rows):
        fill = music_tools.section_fill(dict(chords), row["bars"] * bar_qn, chord_qn)
        sec_key = chords["key"]
        items: dict[str, str] = {}
        report = {"section": row["section"], "bars": row["bars"], "start_bar": row["start_bar"],
                  "energy": row["energy"], "chords": chords["chords"], "key": sec_key, "parts": {}}
        for part in songmap.PARTS:
            p = row["parts"].get(part)
            if p is None:
                continue
            t = tracks[part]
            item = call("create_midi_item", track=t.get("guid") or t["number"], start_bar=row["start_bar"],
                        length_bars=row["bars"], name=f"{row['section']} {part}")
            items[part] = item["id"]
            if part == "drums":
                r = music_tools.add_genre_groove(item_id=item["id"], genre=g.name, bars=row["bars"],
                                                 energy=p["energy"], seed=p["seed"])
                report["parts"][part] = {"energy": p["energy"], "distinct_bars": r.get("distinct_bars")}
            elif part == "bass":
                r = music_tools.write_bassline(item_id=item["id"], chords=fill, key=sec_key, style=p["style"],
                                               seed=p["seed"], groove=kicks or None, kick="lock", feel=played_as)
                report["parts"][part] = {"style": p["style"], "distinct_bars": r.get("distinct_bars")}
            elif part == "chords":
                rhythm = p["rhythm"]
                r = music_tools.add_chord_progression(item_id=item["id"], chords=fill, key=sec_key, voicing=g.voicing,
                                                      rhythm=rhythm, seed=p["seed"], feel=played_as)
                report["parts"][part] = {"rhythm": rhythm}
            elif part == "lead":
                voice = {"low": VOICE_LOW, "high": VOICE_HIGH, "density": "sparse"} if lead_for == "voice" else {}
                r = music_tools.write_melody(item_id=item["id"], chords=fill, key=sec_key, shape=p["shape"],
                                             register_lift=p["register_lift"], seed=p["seed"], candidates=3,
                                             feel=played_as, **voice)
                report["parts"][part] = {"shape": p["shape"], "hook_score": (r.get("hook_score") or {}).get("score")}
                if p.get("double") and lead_for != "voice":
                    report["parts"][part]["double"] = _double_lead(item["id"], sec_key, p["double"])
            elif part == "counter" and "lead" in items:
                r = music_tools.write_counter_melody(item_id=item["id"], melody_item_id=items["lead"],
                                                     chords_item_id=items.get("chords"), key=sec_key, seed=p["seed"],
                                                     feel=played_as)
                report["parts"][part] = {"notes": r.get("notes_written")}
        for part, item_id in items.items():   # after every part, so the counter heard the whole chords
            rests = row["parts"][part].get("rests")
            if rests and part in report["parts"]:
                _rest(item_id, rests, bar_qn)
                report["parts"][part]["sits_out_bars"] = [[row["start_bar"] + a, row["start_bar"] + b] for a, b in rests]
        written.append(report)
    mapped = song_map()
    needs = [t["name"] for p, t in tracks.items() if t.get("created") and not (instruments or {}).get(p)]
    return {
        **({"needs_sound": needs} if needs else {}),
        "genre": g.name, "key": k.name, "seed": seed, "bars": total, "sections": written,
        "tracks": {p: t["name"] + (" (new)" if t.get("created") else "") for p, t in tracks.items()},
        "song_map": {"findings": mapped["findings"],
                     "density": {s["section"]: s["notes_per_bar"] for s in mapped["sections"]}},
        "next": ("Listen, then: a sound for each track in needs_sound (audition_sounds), add_transitions(style), "
                 "write_automation into the peaks, auto_mix(style), check_song. Re-write one section's part with "
                 "its tool (a new seed) rather than copying another section."),
    }


def _rest(item_id: str, rests: list[list[int]], bar_qn: float) -> None:
    """Takes the notes out of an item's rest bars (0-based [from, to) within it); a note
    ringing into a rest stops where the rest begins."""
    notes = call("get_midi_notes", item_id=item_id, limit=20000).get("notes", [])
    kept = []
    for n in notes:
        start, length = n["start"], n["length"]
        if any(a * bar_qn - 1e-6 <= start < b * bar_qn - 1e-6 for a, b in rests):
            continue
        for a, _ in rests:
            if start < a * bar_qn - 1e-6 < start + length:
                length = a * bar_qn - start
        kept.append({"pitch": n["pitch"], "start": start, "length": round(length, 6),
                     "velocity": n.get("velocity", 96), "channel": n.get("channel", 1)})
    call("add_midi_notes", item_id=item_id, notes=kept, replace=True)


LEAD_DOUBLE_STEPS = {"third": 2, "octave": 7}   # scale steps over the hook
LEAD_DOUBLE_VELOCITY = -15                       # under the hook, not beside it


def _double_lead(item_id: str, key: str, how: str) -> str:
    """Adds the hook again a third or an octave over itself, quieter, in the same item:
    a later chorus grows instead of repeating the first."""
    k = harmony.parse_key(key)
    notes = call("get_midi_notes", item_id=item_id, limit=20000).get("notes", [])
    if not notes or k is None:
        return "not doubled: no notes or no key"
    steps = LEAD_DOUBLE_STEPS[how]
    extra = [{"pitch": n["pitch"] + 12 if how == "octave" else lyric_melody.diatonic_shift(n["pitch"], k, steps),
              "start": n["start"], "length": n["length"], "velocity": max(1, n.get("velocity", 96) + LEAD_DOUBLE_VELOCITY),
              "channel": n.get("channel", 1)} for n in notes]
    call("add_midi_notes", item_id=item_id, notes=[n for n in extra if n["pitch"] <= 127], replace=False)
    return f"{how} over the hook, {LEAD_DOUBLE_VELOCITY} velocity"


# ------------------------------------------------------------- stage gates

@tool()
def start_song(
    brief: Annotated[str, Field(description="What the song is: the user's words, mood, references")],
    genre: Annotated[str, Field(description="A genre from list_genres")],
    length: Annotated[str | None, Field(description="e.g. '3-4 minutes', 'a 30 s loop'")] = None,
    use: Annotated[str | None, Field(description="What it's for: a release, a game level loop, a video bed...")] = None,
    name: Annotated[str | None, Field(description="Project name for the first save, when it hasn't been saved yet")] = None,
) -> dict:
    """Starts a song's plan, kept next to the project (<project> - creaper song.json):
    the brief, the genre and the stages (form, sounds, parts, feel, transitions, mix,
    master). finish_stage checks each stage before it counts as done, and song_status
    says what's left. An unsaved project is saved first (under name), since the plan
    lives next to it. The creative calls stay yours: this only keeps score."""
    g = genres.find(genre)
    if _song_paths() is None:
        from .export_tools import save_project

        save_project(name=name or f"{g.name} song")
    plan_path, _ = _song_paths()
    if plan_path.exists():
        confirm_with_user(f"start over the song plan in {plan_path.name}")
    plan = {"version": 1, "brief": brief, "genre": g.name, "length": length, "use": use,
            "created": time.strftime("%Y-%m-%d %H:%M"), "stages": {s: {"done": False} for s in STAGES}}
    jsonstore.write(plan_path, plan, indent=2)
    return {"plan": str(plan_path), "genre": g.name, "stages": [{"stage": s, "checks": STAGE_CHECKS[s]} for s in STAGES],
            "next": "form: new regions for every section from the genre's form, then finish_stage('form')"}


@tool()
def finish_stage(
    stage: Annotated[Literal["form", "sounds", "parts", "feel", "transitions", "mix", "master"], Field(
        description="The stage to sign off")],
    force: Annotated[bool, Field(description=(
        "Mark it done despite failing checks; only after telling the user what failed and getting a yes"))] = False,
) -> dict:
    """Runs a stage's checks (song_status lists them) and marks the stage done when
    nothing fails; warnings are reported but don't block. It refuses on a fail, with
    each failing check's number, limit and fix: fix it and finish the stage again.
    transitions, mix and master render the song once."""
    plan, path = _plan()
    ctx = _Context(plan.get("genre"), plan)
    rows = _rows_for(stage, ctx)
    fails = [r for r in rows if r["status"] == "fail"]
    if fails and not force:
        detail = "; ".join(
            f"{r['check']}{' (' + str(r.get('track') or r.get('section')) + ')' if r.get('track') or r.get('section') else ''}"
            f"{': ' + str(r['value']) if 'value' in r else ''}{' (limit ' + str(r['threshold']) + ')' if 'threshold' in r else ''}"
            f"{' - ' + r['fix'] if r.get('fix') else ''}" for r in fails)
        raise ValueError(f"'{stage}' isn't finished: {detail}. Fix it and finish the stage again, or pass force=True "
                         "if the user wants it as it is.")
    with jsonstore.updating(path, dict, indent=2) as data:
        data.setdefault("stages", {})[stage] = {"done": True, "at": time.strftime("%Y-%m-%d %H:%M"),
                                                "forced": bool(fails), "checks": rows,
                                                **({"tracks": _mix_snapshot(ctx.overview)} if stage == "mix" else {})}
    left = [s for s in STAGES if not data["stages"].get(s, {}).get("done")]
    return {"stage": stage, "done": True, **({"forced_past": [r["check"] for r in fails]} if fails else {}),
            "checks": rows, "next": left[0] if left else "all stages done: check_song for the scorecard"}


@tool(annotations=READ_ONLY)
def song_status() -> dict:
    """The song plan's state: the brief, each stage done or not (with its checks), and
    the next stage to work on. Read-only."""
    plan, path = _plan()
    stages = []
    for s in STAGES:
        st = plan.get("stages", {}).get(s, {})
        entry = {"stage": s, "done": bool(st.get("done")), "checks": STAGE_CHECKS[s]}
        if st.get("done"):
            entry["at"] = st.get("at")
            if st.get("forced"):
                entry["forced"] = True
            warn = [r["check"] for r in st.get("checks", []) if r.get("status") == "warn"]
            if warn:
                entry["warnings"] = warn
        stages.append(entry)
    left = [e["stage"] for e in stages if not e["done"]]
    return {"plan": str(path), "brief": plan.get("brief"), "genre": plan.get("genre"), "length": plan.get("length"),
            "use": plan.get("use"), "stages": stages, "next": left[0] if left else "all done"}


# --------------------------------------------------------------- scorecard

def _fingerprint(measured: dict, overview: dict) -> dict:
    return {"curve": (measured.get("spectrum") or {}).get("octave_bands_db", {}),
            "tempo": float(overview.get("tempo_bpm") or 0), "meter": overview.get("time_signature") or "4/4"}


@tool()
def check_song(
    genre: Annotated[str | None, Field(description="The song's genre; default: the song plan's")] = None,
) -> dict:
    """The song's scorecard: renders the master once (and each lead's busiest section,
    for its tuning) and runs every check (form,
    instruments, the song map, groove, copied bars and loops, the energy arc, the mix
    against the genre, the release gates), each pass / warn / fail with its number,
    limit and fix, and a score out of 10 (a warning counts half). The result is kept next
    to the saved project, so the next run reports what changed (score_change, and 'was'
    and 'change' per check). It also warns when the song sounds like the last song
    checked (the same tempo and nearly the same tone curve). With the optional music
    model installed (creaper[ml]), a 'character' line says how it comes across
    (realistic or synthetic, modern or dated). Changes nothing in the project; writes
    its baseline file next to it."""
    paths = _song_paths()
    plan = jsonstore.read(paths[0], dict) if paths and paths[0].exists() else {}
    genre = genre or plan.get("genre")
    ctx = _Context(genre, plan)
    rows = []
    for stage in STAGES:
        for r in _rows_for(stage, ctx):
            if r["check"] == "sound" and any(x["check"] == "sound" for x in rows):
                continue      # a silent master is one problem, not one per stage
            rows.append({"stage": stage, **r})
    measured, shape = ctx.render()
    fp = _fingerprint(measured, ctx.overview)
    store = bridge.directory / "fingerprints.json"
    me = str(paths[0].parent / paths[0].name.replace(" - creaper song.json", "")) if paths else "unsaved project"
    others = {k: v for k, v in jsonstore.read(store, dict).items() if k != me} if store.exists() else {}
    last = max(others.items(), key=lambda kv: kv[1].get("at", ""), default=None)
    if last:
        d = songmap.fingerprint_distance(fp, last[1])
        if d is not None:
            rows.append({"stage": "mix", **songmap.row(
                "like the last song", "warn" if d < 1.5 else "pass", d, 1.5,
                f"same tempo and tone as {Path(last[0]).name}: change the tempo, the key sounds or the lead colour",
                )})
    if paths:
        with jsonstore.updating(store, dict, indent=None) as data:
            data[me] = {**fp, "at": time.strftime("%Y-%m-%d %H:%M:%S")}
    previous = jsonstore.read(paths[1], dict) if paths and paths[1].exists() else None
    card = songmap.scorecard(rows, previous)
    card["genre"] = genre
    card["measured"] = {"lufs": (measured.get("loudness") or {}).get("integrated_lufs"),
                        "loudness_range_lu": (measured.get("loudness") or {}).get("loudness_range_lu"),
                        "true_peak_dbtp": (measured.get("levels") or {}).get("true_peak_dbtp"),
                        "copied_bars": shape.get("near_duplicate_share")}
    from . import embeddings

    if embeddings.available() and not measured.get("silent"):
        try:  # one line from the opt-in model, never a check or a gate
            card["character"] = embeddings.describe(ctx.mono, ctx.fs)
        except Exception as e:  # noqa: BLE001
            card["character"] = {"error": f"the music model couldn't run: {e}"}
    if paths:
        jsonstore.write(paths[1], {"at": time.strftime("%Y-%m-%d %H:%M"), "score": card["score"],
                                   "checks": [{k: v for k, v in r.items() if k in ("check", "status", "value", "track",
                                                                                     "section")} for r in rows]},
                        indent=1)
    else:
        card["note"] = "save the project to keep this scorecard and see the changes next time"
    return card


# ----------------------------------------------------------- reference

THIRD_OCTAVES = [25 * 2 ** (i / 3) for i in range(30)]   # 25 Hz .. 16 kHz
MATCH_BANDS = [("low shelf", 100, 0, 200), ("low mids", 400, 200, 800), ("presence", 2500, 1200, 5000),
               ("air shelf", 10000, 6000, 18000)]   # name, centre Hz, measured from, to (Hz)
MATCH_MAX_DB = 3.0
MONO_SIDE_DB = -40.0   # side/mid of a mono band
MATCH_FX_NAME = "creaper reference match"


def third_octave_curve(mono: np.ndarray, fs: float) -> dict[str, float]:
    """Level per 1/3-octave band in dB relative to the whole spectrum (so levels don't matter)."""
    from scipy import signal

    freqs, psd = signal.welch(mono, fs=fs, nperseg=min(16384, mono.size))
    total = float(psd[(freqs >= 20) & (freqs <= 20000)].sum())
    out = {}
    for fc in THIRD_OCTAVES:
        lo, hi = fc / 2 ** (1 / 6), fc * 2 ** (1 / 6)
        if hi > fs / 2:
            break
        e = float(psd[(freqs >= lo) & (freqs < hi)].sum())
        out[f"{fc:.0f}"] = round(10 * math.log10(e / total), 1) if e > 0 and total > 0 else None
    return out


def width_by_band(audio: np.ndarray, fs: float) -> dict[str, float | None]:
    """Side against mid (dB) in four bands: how wide the lows, mids, upper mids and highs are."""
    from scipy import signal

    if audio.shape[1] < 2:
        return {}
    mid, side = audio[:, 0] + audio[:, 1], audio[:, 0] - audio[:, 1]
    out = {}
    for name, lo, hi in (("below 150 Hz", 20, 150), ("150 Hz-1 kHz", 150, 1000), ("1-5 kHz", 1000, 5000),
                         ("above 5 kHz", 5000, min(18000, fs / 2 - 1))):
        sos = signal.butter(4, [lo, hi], btype="bandpass", fs=fs, output="sos")
        m, s = signal.sosfilt(sos, mid), signal.sosfilt(sos, side)
        em, es = float(np.dot(m, m)), float(np.dot(s, s))
        # A mono band reads as MONO_SIDE_DB rather than minus infinity.
        out[name] = max(MONO_SIDE_DB, round(10 * math.log10(es / em), 1)) if em > 0 and es > 0 else             (MONO_SIDE_DB if em > 0 else None)
    return out


def _arc(mono: np.ndarray, fs: float, parts: int = 8) -> list[float]:
    """Loudness of each eighth of the track against its loudest eighth (dB)."""
    n = mono.size // parts
    if n == 0:
        return []
    levels = [10 * math.log10(float(np.mean(np.square(mono[i * n:(i + 1) * n]))) + 1e-12) for i in range(parts)]
    top = max(levels)
    return [round(v - top, 1) for v in levels]


def estimate_bars(mono: np.ndarray, fs: float, beats_per_bar: int = 4) -> tuple[list[float], float | None]:
    """Bar starts (s) for audio with no tempo map: the beat from the onset envelope's
    autocorrelation (60-180 BPM), the downbeat phase where onsets line up best. Returns
    (starts, BPM); a track with no clear pulse gets 2 s windows and None. librosa's beat
    tracker (creaper[analysis]) is used when it's installed."""
    import importlib.util

    if importlib.util.find_spec("librosa") is not None:
        import librosa

        y = mono.astype(np.float32)
        env = librosa.onset.onset_strength(y=y, sr=fs)
        tempo, beats = librosa.beat.beat_track(onset_envelope=env, sr=fs)
        bpm = float(np.atleast_1d(tempo)[0])
        if len(beats) >= beats_per_bar * 8 and 50 <= bpm <= 200:
            # The downbeat: the beat of the bar where onsets are strongest.
            phase = max(range(beats_per_bar), key=lambda k: float(env[beats[k::beats_per_bar]].sum()))
            times = librosa.frames_to_time(beats[phase::beats_per_bar], sr=fs)
            return [float(t) for t in times], round(bpm, 1)
    hop = int(fs * 0.01)
    frames = mono[: mono.size // hop * hop].reshape(-1, hop)
    energy = np.log10(np.mean(frames ** 2, axis=1) + 1e-10)
    onset = np.maximum(0.0, np.diff(energy, prepend=energy[0]))
    onset -= onset.mean()
    end = mono.size / fs
    if onset.size > 400:
        ac = np.correlate(onset, onset, mode="full")[onset.size - 1:]
        lo, hi = int(60 / 180 / 0.01), int(60 / 60 / 0.01)
        lag = lo + int(np.argmax(ac[lo:hi]))
        if ac[lag] > 0.1 * ac[0]:
            bar_s = lag * 0.01 * beats_per_bar
            bar_frames = int(round(bar_s / 0.01))
            phase = max(range(min(bar_frames, onset.size)), key=lambda k: float(onset[k::bar_frames].sum()))
            return list(np.arange(phase * 0.01, end - bar_s, bar_s)), round(60 / (lag * 0.01), 1)
    return list(np.arange(0, end - 2.0, 2.0)), None


def _repetition(mono: np.ndarray, fs: float, starts: list[float]) -> float | None:
    if len(starts) < 8:
        return None
    length = starts[-1] - starts[-2]
    feats = structure.bar_features(mono, fs, starts, starts[-1] + length)
    return structure.repetition(feats).get("near_duplicate_share")


def features(audio: np.ndarray, fs: float, measured: dict, bar_starts: list[float] | None = None) -> dict:
    """compare_to_reference's measurements; bar_starts (s) from the project's tempo map
    for the mix, estimated from the audio when None (a reference file)."""
    mono = audio.mean(axis=1)
    bpm = None
    if bar_starts is None:
        bar_starts, bpm = estimate_bars(mono, fs)
    loud = measured.get("loudness") or {}
    lufs = loud.get("integrated_lufs")
    tp = (measured.get("levels") or {}).get("true_peak_dbtp")
    return {"lufs": lufs, "peak_to_loudness_db": round(tp - lufs, 1) if tp is not None and lufs is not None else None,
            "loudness_range_lu": loud.get("loudness_range_lu"),
            "crest_factor_db": (measured.get("levels") or {}).get("crest_factor_db"),
            "curve": third_octave_curve(mono, fs), "width": width_by_band(audio, fs),
            "repetition": _repetition(mono, fs, bar_starts), "arc": _arc(mono, fs),
            **({"estimated_bpm": bpm} if bpm else {})}


def diff_table(ref: dict, mix: dict) -> list[dict]:
    rows = []
    for key, label, tol, more, less in (
            ("lufs", "loudness (LUFS)", 1.0, "louder than the reference", "quieter than the reference"),
            ("peak_to_loudness_db", "peak to loudness (dB)", 1.5, "more open, less dense", "more squashed"),
            ("loudness_range_lu", "loudness range (LU)", 2.0, "more level change", "flatter"),
            ("crest_factor_db", "crest factor (dB)", 2.0, "punchier peaks", "fewer peaks"),
            ("repetition", "copied bars", 0.15, "more repetitive", "changes more")):
        a, b = ref.get(key), mix.get(key)
        if a is None or b is None:
            continue
        d = round(b - a, 2)
        rows.append({"feature": label, "reference": a, "mix": b, "difference": d,
                     "verdict": "close" if abs(d) <= tol else (more if d > 0 else less)})
    bands = [k for k in ref["curve"] if ref["curve"].get(k) is not None and mix["curve"].get(k) is not None]
    for name, _, lo, hi in MATCH_BANDS:
        inside = [k for k in bands if lo <= float(k) < hi]
        if inside:
            d = round(float(np.mean([mix["curve"][k] - ref["curve"][k] for k in inside])), 1)
            rows.append({"feature": f"tone: {name} ({lo}-{hi} Hz)", "difference": d,
                         "verdict": "close" if abs(d) <= 1.0 else ("more than the reference" if d > 0 else
                                                                    "less than the reference")})
    for band, a in (ref.get("width") or {}).items():
        b = (mix.get("width") or {}).get(band)
        if a is None or b is None:
            continue
        d = round(b - a, 1)
        rows.append({"feature": f"width {band} (side/mid dB)", "reference": a, "mix": b, "difference": d,
                     "verdict": "close" if abs(d) <= 2.0 else ("wider" if d > 0 else "narrower")})
    return rows


def match_gains(ref: dict, mix: dict) -> list[dict]:
    """The bounded master EQ that moves the mix's tone toward the reference: four broad
    bands, each the mean difference over its range, capped at MATCH_MAX_DB and skipped
    under 0.5 dB."""
    out = []
    for name, hz, lo, hi in MATCH_BANDS:
        inside = [k for k in ref["curve"] if lo <= float(k) < hi and ref["curve"].get(k) is not None
                  and mix["curve"].get(k) is not None]
        if not inside:
            continue
        d = float(np.mean([ref["curve"][k] - mix["curve"][k] for k in inside]))
        gain = round(max(-MATCH_MAX_DB, min(MATCH_MAX_DB, d)), 1)
        if abs(gain) >= 0.5:
            out.append({"band": name, "hz": hz, "gain_db": gain})
    return out


@tool()
def compare_to_reference(
    file: Annotated[str, Field(description="A reference track (WAV, FLAC, MP3, OGG), e.g. a song in the style you want")],
    apply: Annotated[bool, Field(description=(
        f"Also put a gentle corrective EQ on the master toward the reference's tone (4 broad bands, at most "
        f"±{MATCH_MAX_DB:g} dB each, replaced on each run)"))] = False,
) -> dict:
    """Measures the current master against a reference track: loudness, peak to
    loudness, loudness range, crest, the 1/3-octave tone curve (levels matched), stereo
    width by band, how repetitive it is and its energy arc, and returns a table of the
    differences with what each means. With apply=True a bounded EQ on the master moves
    the tone toward the reference; the loudness is master_to_target's job."""
    from .export_tools import _check_renders, _cleanup

    from .sample_tools import _check_audio

    path = Path(_check_audio(str(Path(file).expanduser())))
    try:
        ref_audio, ref_fs = sf.read(str(path), always_2d=True)
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"can't read {path.name} as audio: {e}") from e
    ref = features(ref_audio, ref_fs, analysis.analyze_file(path))
    if ref["lufs"] is None or not any(v is not None for v in ref["curve"].values()):
        raise ValueError(f"couldn't measure {path.name}: it's silent or too short")
    render = call("render_audio", timeout=900.0, track="master")
    _check_renders(render["files"])
    try:
        mix_measured = analysis.analyze_file(render["files"][0])
        mix_audio, mix_fs = sf.read(render["files"][0], always_2d=True)
    finally:
        _cleanup(render["files"])
    offset = render["start"]["seconds"]
    every = structure.bar_starts(call("get_tempo_map"), offset + mix_audio.shape[0] / mix_fs)
    mix = features(mix_audio, mix_fs, mix_measured, [t - offset for t in every if t >= offset - 1e-3])
    out = {"reference": path.name, "differences": diff_table(ref, mix),
           "energy_arc": {"reference": ref["arc"], "mix": mix["arc"]},
           **({"reference_bpm_estimated": ref["estimated_bpm"]} if ref.get("estimated_bpm") else {})}
    from . import embeddings

    if embeddings.available():
        try:  # how alike they sound to the opt-in music model
            out["sounds_alike"] = embeddings.similarity(embeddings.audio_embedding(ref_audio.mean(axis=1), ref_fs),
                                                        embeddings.audio_embedding(mix_audio.mean(axis=1), mix_fs))
        except Exception as e:  # noqa: BLE001
            out["sounds_alike"] = f"the music model couldn't run: {e}"
    gains = match_gains(ref, mix)
    out["suggested_eq"] = gains or "the tone is within 0.5 dB of the reference in every band"
    if apply and gains:
        out["applied"] = _apply_match(gains)
    return out


def _apply_match(gains: list[dict]) -> dict:
    """ReaEQ first on the master (before any limiter), named MATCH_FX_NAME and replaced
    when it's already there: band 1 the low shelf, 2 and 3 bells, 4 the high shelf, the
    band-5 high pass parked at 20 Hz; bands with no change stay flat."""
    from .mix_tools import NO_HIGHPASS_HZ

    for f in reversed(call("get_track_details", track="master").get("fx", [])):
        if MATCH_FX_NAME in (f.get("name") or ""):
            call("remove_fx", track="master", fx=f["index"])
    eq = call("add_fx", track="master", name="ReaEQ", position=1)
    call("update_fx", track="master", fx=eq["index"], rename=MATCH_FX_NAME)
    names = {"low shelf": ("Freq-Low Shelf 1", "Gain-Low Shelf 1", None),
             "low mids": ("Freq-Band 2", "Gain-Band 2", "BW-Band 2"),
             "presence": ("Freq-Band 3", "Gain-Band 3", "BW-Band 3"),
             "air shelf": ("Freq-High Shelf 4", "Gain-High Shelf 4", None)}
    changes = [{"parameter": "Freq-High Pass 5", "display_value": NO_HIGHPASS_HZ}]
    for name, (freq, gain, bw) in names.items():
        g = next((x for x in gains if x["band"] == name), None)
        changes.append({"parameter": gain, "display_value": g["gain_db"] if g else 0.0})
        if g:
            changes.append({"parameter": freq, "display_value": g["hz"]})
            if bw:
                changes.append({"parameter": bw, "display_value": 1.5})
    call("set_fx_parameters", track="master", fx=eq["index"], changes=changes)
    return {"fx": MATCH_FX_NAME, "bands": gains}
