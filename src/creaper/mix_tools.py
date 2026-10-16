"""auto_mix: a whole first mix in one call.

Every track that reaches the master is rendered in one pass and measured; each gets a
role (kick, bass, vocal, keys...) from its name and its sound; then levels are set
for the genre, non-bass parts are high-passed and cleared of mud, the parts that need
it are compressed, the wide parts are panned, a reverb return is fed, and the bass
ducks under the kick in dance styles. Finally the mix is measured again and its
headroom set for mastering. A starting point that Claude then refines by measuring.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated

from pydantic import Field

from . import analysis, genres, plugin_profiles
from .server import DESTRUCTIVE, Bar, analyze_audio, call, confirm_with_user, setup_sidechain, tool

# Loudness of each role while it plays (max short-term LUFS), relative to the drums.
ROLE_LEVELS = {"kick": 0, "drums": 0, "snare": -3, "perc": -9, "bass": -2, "vocal": -1, "lead": -5,
               "keys": -7, "pad": -10, "fx": -12, "other": -7}
HIGHPASS_HZ = {"snare": 100, "perc": 300, "vocal": 110, "lead": 150, "keys": 140, "pad": 180, "fx": 150, "other": 120}
REVERB_DB = {"vocal": -14, "lead": -17, "keys": -18, "pad": -15, "snare": -21, "perc": -24, "other": -20}
PAN_WIDTH = {"perc": 0.35, "keys": 0.25, "pad": 0.2, "fx": 0.4, "other": 0.3, "lead": 0.0}
COMPRESS = {"vocal": (3.0, 5, 80), "bass": (4.0, 20, 120), "lead": (2.5, 10, 100)}  # ratio, attack ms, release ms
HEADROOM_PEAK_DB = -6.0
# Loudness (K-weighted) underrates sub-bass, so a sustained sub drone measured "quiet"
# and got boosted +6 to +12 dB until it was most of the mix: boosts are capped.
MAX_BOOST_DB, MAX_BOOST_LOW_DB = 6.0, 2.0
LOW_HEAVY_PCT = 50   # sub + bass share above which a part counts as low-heavy

ROLE_WORDS = [
    ("kick", r"\bkick|\bbd\b"),
    ("snare", r"snare|clap"),
    ("perc", r"hat|\bhh\b|cymbal|ride|crash|shaker|perc|conga|bongo|tamb|rim\b|tom"),
    ("bass", r"bass|\bsub\b|808 ?bass"),
    ("vocal", r"vocal|\bvox|voice|chops?\b|singer|acapella|talk ?box|vocoder|robot"),
    ("drums", r"drum|\bkit\b|909|808|beat"),
    ("pad", r"\bpad|string|choir|atmos|ambien"),
    ("keys", r"key|piano|rhodes|clav|organ|\bep\b|wurli|stab|brass|chord|guitar"),
    ("lead", r"lead|hook|arp|pluck|melody|synth|solo"),
    ("fx", r"\bfx\b|riser|sweep|impact|noise|downlifter|uplifter|whoosh"),
]
DANCE_FAMILIES = {"electronic dance"}


def role_of(name: str, spectrum: dict | None = None) -> str:
    """A track's job in the mix, from its name, else from its sound."""
    n = re.sub(r"\s+(duck|bus)$", "", name.lower())
    for role, pattern in ROLE_WORDS:
        if re.search(pattern, n):
            return role
    bands = (spectrum or {}).get("bands", {})
    low = sum((bands.get(k) or {}).get("share_pct", 0) for k in ("sub (20-60 Hz)", "bass (60-250 Hz)"))
    if low > 60:
        return "bass"
    centroid = (spectrum or {}).get("spectral_centroid_hz") or 0
    if centroid > 4000:
        return "perc"
    return "other"


def low_share(spectrum: dict | None) -> float:
    bands = (spectrum or {}).get("bands", {})
    return sum((bands.get(k) or {}).get("share_pct", 0) for k in ("sub (20-60 Hz)", "bass (60-250 Hz)"))


def lowest_strong_hz(spectrum: dict | None, within_db: float = 18.0) -> float | None:
    """The bottom edge of the lowest octave band within `within_db` of the strongest:
    roughly the part's lowest fundamental, which a high-pass must stay under."""
    octaves = (spectrum or {}).get("octave_bands_db") or {}
    levels = []
    for label, db in octaves.items():
        if db is None:
            continue
        number = float(label.split()[0]) * (1000 if label.endswith("kHz") else 1)
        levels.append((number, db))
    if not levels:
        return None
    top = max(db for _, db in levels)
    lowest = min(f for f, db in levels if db >= top - within_db)
    return lowest / 2 ** 0.5


def highpass_for(role: str, spectrum: dict | None) -> int | None:
    """The role's usual high-pass, but never above about 0.6x the part's lowest strong
    content (so low cellos, brass and pulse basses keep their fundamentals), and none at
    all when that would be under 40 Hz."""
    if role not in HIGHPASS_HZ:
        return None
    hz = float(HIGHPASS_HZ[role])
    lowest = lowest_strong_hz(spectrum)
    if lowest is not None:
        hz = min(hz, 0.6 * lowest)
    return int(round(hz)) if hz >= 40 else None


# A part this far over its role's level (LU, against the drums in the same section) is
# overpowering; this far under, buried.
OVER_LU, UNDER_LU = 4.0, 8.0


def section_balance(levels: dict[str, dict[str, float | None]], roles: dict[str, str]) -> list[str]:
    """Parts out of place in each section. levels: {section: {track: LUFS while it
    plays}}; roles: {track: role}. Each part is judged against ROLE_LEVELS from the
    drums in that section (a section without drums: from the parts' median)."""
    out = []
    for section, tracks in levels.items():
        playing = {t: v for t, v in tracks.items() if v is not None}
        if len(playing) < 2:
            continue
        drums = [v for t, v in playing.items() if roles.get(t) in ("kick", "drums")]
        anchor = max(drums) if drums else float(sorted(v - ROLE_LEVELS.get(roles.get(t, "other"), -7)
                                                       for t, v in playing.items())[len(playing) // 2])
        for t, v in playing.items():
            role = roles.get(t, "other")
            if drums and role in ("kick", "drums") and v == anchor:
                continue
            off = v - (anchor + ROLE_LEVELS.get(role, -7))
            where = (f"{-ROLE_LEVELS.get(role, -7):g} LU under the drums" if drums else "with the rest")
            if off > OVER_LU:
                out.append(f"{section}: {t} is {off:.1f} LU over its place (a {role} part sits about {where})")
            elif off < -UNDER_LU:
                out.append(f"{section}: {t} is {-off:.1f} LU under its place (a {role} part sits about {where}): buried")
    return out


# Level of each drum's hits (RMS over its first 60 ms) against the kick's, in dB. Rough
# rules of thumb for a modern mix; lanes are matched by name.
DRUM_LANE_DB = [
    (r"kick|\bbd\b|bass drum", 0), (r"snare|clap|rim|stick", -2), (r"tom", -4),
    (r"crash|ride|cymbal|china|splash", -8), (r"conga|bongo|perc|cowbell|wood|clave|timbale", -8),
    (r"hat|\bhh\b", -10), (r"shaker|tamb|cabasa|maraca", -12),
]
HIT_WINDOW_S = 0.06
COLLISION_S = 0.03


def lane_target(lane: str) -> float | None:
    return next((db for pattern, db in DRUM_LANE_DB if re.search(pattern, lane.lower())), None)


SILENT_LANE_DB = 60.0  # a lane this far under the loudest one plays nothing on that kit


def hit_levels(mono, fs: float, hits: dict[str, list[float]]) -> tuple[dict[str, float], dict[str, list[str]]]:
    """Median level (dB RMS over HIT_WINDOW_S) of each lane's hits. hits: {lane: onset
    seconds in the audio}. Hits with another lane within COLLISION_S are left out (a
    kick under a hat would count as the hat). Returns the levels of the lanes that sound,
    and which lanes are 'silent' (the kit has nothing on that note) or measured only
    'with_others' (every hit lands with another drum, so the level is theirs together)."""
    import bisect

    import numpy as np

    def measure(sounding: dict[str, list[float]]) -> tuple[dict[str, float], list[str]]:
        every = sorted((t, lane) for lane, ts in sounding.items() for t in ts)
        times = [t for t, _ in every]

        def crowded(t: float, lane: str) -> bool:
            lo, hi = bisect.bisect_left(times, t - COLLISION_S), bisect.bisect_right(times, t + COLLISION_S)
            return any(o != lane for _, o in every[lo:hi])

        measured, shared = {}, []
        for lane, ts in sounding.items():
            alone = [t for t in ts if not crowded(t, lane)]
            if not alone:
                shared.append(lane)
            levels = []
            for t in alone or ts:
                a, b = int(t * fs), int((t + HIT_WINDOW_S) * fs)
                seg = mono[max(0, a):min(len(mono), b)]
                if seg.size:
                    levels.append(10 * np.log10(float(np.mean(np.square(seg))) + 1e-20))
            if levels:
                measured[lane] = round(float(np.median(levels)), 1)
        return measured, shared

    measured, _ = measure(hits)
    loudest = max(measured.values(), default=None)
    silent = [lane for lane, v in measured.items() if loudest is None or v < loudest - SILENT_LANE_DB]
    # Again without the lanes that make no sound: landing with one isn't landing with a drum.
    out, shared = measure({lane: ts for lane, ts in hits.items() if lane not in silent})
    return out, {"silent": silent, "with_others": [lane for lane in shared if lane in out]}


def lane_balance(levels: dict[str, float], approximate: list[str] | None = None) -> list[str]:
    """Drums in a one-track kit that are out of place against the kick. Without a kick
    lane there's nothing to judge by: the levels are reported on their own. Lanes in
    approximate (only ever heard with another drum) aren't judged."""
    kick = max((v for lane, v in levels.items() if lane_target(lane) == 0), default=None)
    if kick is None:
        return []
    out = []
    for lane, v in levels.items():
        target = lane_target(lane)
        if target is None or target == 0 or lane in (approximate or ()):
            continue
        off = v - kick - target
        if off > OVER_LU:
            out.append(f"{lane} hits are {v - kick:+.1f} dB against the kick (usually about {target:g}): overpowering")
        elif off < -UNDER_LU:
            out.append(f"{lane} hits are {v - kick:+.1f} dB against the kick (usually about {target:g}): buried")
    return out


def plan_mix(channels: list[dict], style: dict | None = None) -> dict:
    """What to do to each channel. channels: name, role, level (max short-term LUFS),
    peak_db, crest_db, spectrum, pan, has_eq, has_comp. style: a genre profile's mix
    (low_end) and family. Returns per-channel actions and project-wide ones."""
    style = style or {}
    offsets = dict(ROLE_LEVELS)
    low_end = (style.get("mix") or {}).get("low_end")
    if low_end in ("heavy", "very heavy"):
        offsets["bass"] += 1 if low_end == "heavy" else 2
        offsets["kick"] += 0 if low_end == "heavy" else 1
    elif low_end == "light":
        offsets["bass"] -= 2
    if style.get("family") in ("pop", "hip-hop", "r&b and soul", "country and folk"):
        offsets["vocal"] += 2
    playing = [c for c in channels if c.get("level") is not None]
    anchors = [c for c in playing if c["role"] in ("kick", "drums")]
    anchor = max(c["level"] for c in anchors) if anchors else max((c["level"] for c in playing), default=-20.0)
    actions = []
    side = 1
    for c in channels:
        a: dict = {"name": c["name"], "role": c["role"], "ref": c.get("ref", c["name"])}
        if c.get("level") is None:
            actions.append({**a, "skipped": "silent in this range"})
            continue
        want = anchor + offsets.get(c["role"], -7)
        boost = MAX_BOOST_LOW_DB if (c["role"] == "bass" or low_share(c.get("spectrum")) > LOW_HEAVY_PCT)             else MAX_BOOST_DB
        a["gain_db"] = round(max(-18.0, min(boost, want - c["level"])), 1)
        if c["role"] in HIGHPASS_HZ and not c.get("has_eq"):
            hp = highpass_for(c["role"], c.get("spectrum"))
            if hp:
                a["highpass_hz"] = hp
            bands = (c.get("spectrum") or {}).get("bands", {})
            mud = (bands.get("low mids (250-500 Hz)") or {}).get("share_pct", 0)
            if c["role"] in ("keys", "pad", "lead", "vocal", "other") and mud > 25:
                a["mud_cut_db"] = -3.0 if mud > 35 else -2.0
        if c["role"] in COMPRESS and not c.get("has_comp") and (c.get("crest_db") or 0) > 12:
            ratio, attack, release = COMPRESS[c["role"]]
            a["compress"] = {"ratio": ratio, "attack_ms": attack, "release_ms": release,
                             "threshold_db": round((c.get("peak_db") or -6) - 10, 1)}
        width = PAN_WIDTH.get(c["role"], 0.0)
        if width and abs(c.get("pan") or 0) < 0.01:
            a["pan"] = round(side * width, 2)
            side = -side
        if c["role"] in REVERB_DB:
            a["reverb_send_db"] = REVERB_DB[c["role"]]
        actions.append(a)
    kick = next((c for c in channels if c["role"] == "kick"), None) or \
        next((c for c in channels if c["role"] == "drums"), None)
    duck = []
    if kick and style.get("family") in DANCE_FAMILIES:
        for c in channels:
            refs = {"source_ref": kick.get("ref", kick["name"]), "target_ref": c.get("ref", c["name"])}
            if c["role"] == "bass" and not c.get("ducked"):
                duck.append({"source": kick["name"], "target": c["name"], "depth": "medium", **refs})
            elif c["role"] == "pad" and not c.get("ducked"):
                duck.append({"source": kick["name"], "target": c["name"], "depth": "light", **refs})
    return {"anchor_lufs": round(anchor, 1), "channels": actions, "sidechains": duck}


# ------------------------------------------------------------------ executing

def _channels() -> list[dict]:
    """The tracks to mix: each source of sound, wherever it's routed. Skips folders,
    muted and empty tracks, robot-vocal helpers and effects returns. A track that plays
    through a sidechain 'Duck' bus is mixed on that bus; a submix bus (a track fed by
    others) isn't mixed like an instrument, its sources are."""
    overview = call("get_project_overview")
    routing = {t["name"]: t for t in call("get_routing")["tracks"]}
    by_name = {t["name"]: t for t in overview["tracks"]}
    feeds: dict[str, list[str]] = {}
    for src, r in routing.items():
        for snd in r.get("sends") or []:
            if not snd.get("note"):  # not a sidechain input
                feeds.setdefault(snd["to"], []).append(src)
    out = []
    layered = {name for name in by_name if name.endswith(" (layered)")}
    for t in overview["tracks"]:
        name = t["name"]
        r = routing.get(name, {})
        if r.get("in_folder") in layered:
            continue  # a layered part is mixed as one, on its folder
        if name in layered and not t.get("mute"):
            fx = " ".join(t.get("fx", [])).lower()
            out.append({"name": name, "track": t["number"], "ref": t.get("guid") or t["number"],
                        "volume_db": t.get("volume_db", 0.0), "pan": t.get("pan", 0.0),
                        "has_eq": "eq" in fx, "has_comp": "comp" in fx or "limit" in fx,
                        "ducked": "duck" in fx, "layered": True})
            continue
        if t.get("mute") or r.get("folder") or re.search(r" (Voice|Carrier)$", name):
            continue
        if re.search(r"verb|reverb|delay|return", name, re.I) and not t.get("item_count"):
            continue  # an effects return
        source = name[:-5] if name.endswith(" Duck") else None
        robot_vocal = f"{name} Voice" in by_name or f"{name} Carrier" in by_name
        if source is None and not robot_vocal and not t.get("item_count"):
            continue  # nothing plays here itself: empty, or a bus whose sources are mixed instead
        if f"{name} Duck" in by_name:
            continue  # plays through its Duck bus, which is mixed instead
        fx = " ".join(t.get("fx", [])).lower()
        # ref: the track's GUID, so every change reaches this exact track even when
        # names repeat, look like numbers ("808") or are empty, and when tracks move.
        out.append({"name": name, "track": t["number"], "ref": t.get("guid") or t["number"],
                    "pan": t.get("pan", 0), "volume_db": t.get("volume_db", 0),
                    "has_eq": "eq" in fx, "has_comp": "comp" in fx or "limit" in fx,
                    "ducked": source is not None or (by_name.get(f"{name} Duck") is not None)})
    return out


COVERING_ROLES = ("keys", "lead", "pad", "other")
COVERED = 0.03   # clarity lost to the mix beyond which the words count as covered


def _clear_robot_vocals(actions: list[dict], start_bar: float | None, end_bar: float | None) -> list[dict]:
    """Measures each robot vocal's clarity in the mix and, while the rest of the mix
    covers the words, fixes it the way that measured best: the vocal up 2 dB, then the
    parts covering it most (found by muting each in turn) ducked under it. In a test,
    ducking the lead synth and chords took clarity in the mix from 0.588 to 0.650
    against 0.662 alone; dipping them at 2.5 kHz barely moved it."""
    from .ear_tools import measure_vocal_clarity
    out = []
    candidates = [a for a in actions if a["role"] in COVERING_ROLES and not a.get("skipped")]
    for a in actions:
        if a["role"] != "vocal" or a.get("skipped"):
            continue
        vocal = a.get("ref", a["name"])
        try:
            now = measure_vocal_clarity(vocal, start_bar, end_bar)
        except ValueError:
            continue  # not a robot vocal: no clean words to compare with
        entry: dict = {"vocal": a["name"], "before": {k: now.get(k, {}).get("score") for k in ("alone", "in_mix")}}

        def covered(m: dict) -> float:
            alone, mixed = m.get("alone", {}).get("score"), m.get("in_mix", {}).get("score")
            return 0.0 if alone is None or mixed is None else alone - mixed

        if covered(now) > COVERED:
            vol = call("get_track_details", track=vocal)["volume_db"]
            call("set_track_properties", track=vocal, volume_db=round(vol + 2, 1))
            entry["raised_db"] = 2
            now = measure_vocal_clarity(vocal, start_bar, end_bar)
        if covered(now) > COVERED and candidates:
            base = now["in_mix"]["score"]
            gains = []
            for c in candidates:
                other = c.get("ref", c["name"])
                call("set_track_properties", track=other, mute=True)
                try:
                    without = measure_vocal_clarity(vocal, start_bar, end_bar, in_mix=True)["in_mix"]["score"]
                finally:
                    call("set_track_properties", track=other, mute=False)
                gains.append((without - base, c))
            ducked = []
            for gain, c in sorted(gains, key=lambda g: -g[0]):
                if gain < 0.01 or covered(now) <= COVERED:
                    break
                setup_sidechain(source=vocal, target=c.get("ref", c["name"]),
                                depth="heavy" if c["role"] == "lead" else "medium")
                ducked.append(c["name"])
                now = measure_vocal_clarity(vocal, start_bar, end_bar)
            entry["covering"] = {c["name"]: round(g, 3) for g, c in sorted(gains, key=lambda g: -g[0]) if g > 0.005}
            if ducked:
                entry["ducked_under_vocal"] = ducked
            leads = [c["name"] for g, c in gains if c["role"] == "lead" and g >= 0.02]
            if leads:
                entry["arrangement"] = (", ".join(leads) + " plays a lead line while the vocal sings; consider "
                                        "dropping it out under the vocal or moving it an octave away")
        entry["after"] = {k: now.get(k, {}).get("score") for k in ("alone", "in_mix")}
        entry["verdict"] = now.get("in_mix", {}).get("verdict")
        out.append(entry)
    return out


DRUM_ROLES = ("kick", "drums", "snare", "perc")
DRUM_GLUE_DB = 1.5           # loud-vs-average drop on the drum bus (its 10 ms attack lets hits through, so this
                             # understates the real gain reduction; more fights the anti-crush floor)
DELAY_DB = {"vocal": -20, "lead": -18}   # send levels to the shared delay


def _glue_drums(channels: list[dict], start_bar: float | None, end_bar: float | None) -> dict | None:
    """Puts the drums through one compressor so they hit as a kit, calibrated by
    measurement to take about 1.5 dB off the hits (ReaComp at 4:1 with a 10 ms attack
    that lets them through). Where it goes:
    - a bus the drums already all send to (an earlier run's 'Drum Bus', or the user's);
    - else the folder they share, if that folder holds only drums;
    - else, for a single drum track (a whole kit), that track, after its instrument;
    - else a new 'Drum Bus' the drums play through.
    Run after the headroom move: the bus is fed after the drum faders, so moving them
    afterwards would undo the calibration."""
    from .server import _calibrate_compressor

    drums = [c for c in channels if c.get("role") in DRUM_ROLES and c.get("level") is not None
             and not c["name"].endswith(" Duck")]
    if not drums:
        return None
    overview = call("get_project_overview")
    tracks = {t.get("guid"): t for t in overview["tracks"]}
    by_name = {t["name"]: t for t in overview["tracks"]}
    routing = {t["name"]: t for t in call("get_routing")["tracks"]}
    # A bus every drum already sends to (not a sidechain input): use it, never add another.
    def is_return(name: str) -> bool:  # the reverb/delay returns the drums send to aren't buses
        fx = " ".join(by_name.get(name, {}).get("fx", [])).lower()
        return bool(re.search(r"verb|delay|echo|return", name, re.I) or re.search(r"verb|delay|echo", fx))

    dests = [{s["to"] for s in routing.get(c["name"], {}).get("sends") or []
              if not s.get("note") and not is_return(s["to"])} for c in drums]
    shared_bus = set.intersection(*dests) if dests else set()
    position = None
    if shared_bus:
        bus = by_name.get(sorted(shared_bus)[0])
        target, how = (bus.get("guid") or bus["number"]), f"on '{bus['name']}', the bus the drums already feed"
    elif len(drums) == 1:
        target, how = drums[0]["ref"], f"on '{drums[0]['name']}' itself, after its instrument (a whole kit on one track)"
        fx = call("get_track_details", track=target).get("fx", [])
        position = max((f["index"] for f in fx if f.get("instrument")), default=0) + 1
    else:
        parents = {tracks.get(c["ref"], {}).get("parent") for c in drums}
        if len(parents) == 1 and None not in parents:
            folder = parents.pop()
            members = [t for t in overview["tracks"] if t.get("parent") == folder]
            drum_refs = {c["ref"] for c in drums}
            if any(t.get("guid") not in drum_refs and t.get("item_count") for t in members):
                return {"skipped": "the drums' folder also holds other parts, so it wasn't compressed as a drum bus"}
            target, how = folder, "on the drums' folder track"
        elif parents == {None}:
            bus = call("create_bus", name="Drum Bus", tracks=[c["ref"] for c in drums])
            target, how = bus["bus"]["guid"], "on a new Drum Bus the drums now play through"
        else:
            return {"skipped": "the drums are spread over different folders, so they weren't put on one bus"}
    existing = call("get_track_details", track=target).get("fx", [])
    if any("comp" in f["name"].lower() or "glue" in f["name"].lower() for f in existing):
        return {"skipped": f"there's already a compressor where the drum glue would go ({how[3:]})"}
    comp = call("add_fx", track=target, name="ReaComp", **({"position": position} if position else {}))
    profile = plugin_profiles.find_profile(comp["name"])
    changes = [dict(c) for c in profile.setup] if profile else []
    changes += [{"parameter": "Ratio", "display_value": 4}, {"parameter": "Attack", "display_value": 10},
                {"parameter": "Release", "display_value": 80}]
    call("set_fx_parameters", track=target, fx=comp["index"], changes=changes)
    result = {"where": how, "compressor": comp["name"]}
    if profile and profile.drive:
        result["calibration"] = _calibrate_compressor(target, comp["index"], profile, DRUM_GLUE_DB, start_bar, end_bar)
    return result


def _delay_return(bpm: float) -> dict:
    """A shared delay return (an existing one, or ReaDelay): a dotted-8th echo, darkened
    and thinned so it sits behind what feeds it. One space for leads and vocals, like
    the shared reverb, is part of what makes a mix sound like one record."""
    for t in call("get_project_overview")["tracks"]:
        has_delay = any(re.search(r"delay|echo", f, re.I) for f in t.get("fx", []))
        if re.search(r"\b(delay|echo)\b", t["name"], re.I) and not t.get("item_count") and has_delay:
            return {"track": t["guid"], "name": t["name"], "reused": True}
    made = call("create_track", name="Delay")
    guid = made["track"].get("guid") or "Delay"
    call("add_fx", track=guid, name="ReaDelay")
    dotted_eighth_ms = round(0.75 * 60000 / bpm, 1)
    set_result = call("set_fx_parameters", track=guid, fx=1, changes=[
        {"parameter": "Wet", "display_value": 0}, {"parameter": "Dry", "display_value": -150},
        {"parameter": "Length (time)", "display_value": dotted_eighth_ms},
        {"parameter": "Length (musical)", "display_value": 0},
        {"parameter": "Feedback", "display_value": -9},
        {"parameter": "Lowpass", "display_value": 5000}, {"parameter": "Hipass", "display_value": 300}])
    failed = [c for c in set_result.get("results", []) if isinstance(c, dict) and c.get("error")]
    out = {"track": guid, "name": "Delay", "time_ms": dotted_eighth_ms, "reused": False}
    if failed:
        out["not_set"] = [c.get("parameter") for c in failed]
    return out


ROOM_DB = {"snare": -14, "perc": -18, "drums": -16, "kick": -24}   # drum sends to the short room
MIX_GLUE_DB = 1.0        # what the mix-bus compressor takes off (gentle: glue, not squash)


def _drum_room() -> dict:
    """A short, dark room for the drums (an existing 'Drum Room', or ReaVerbate set
    small): a kit sounds like one kit when it shares a space, and a small room keeps
    the drums tight where the long reverb would wash them out."""
    for t in call("get_project_overview")["tracks"]:
        if t["name"].lower() == "drum room" and not t.get("item_count"):
            return {"track": t.get("guid") or t["number"], "name": t["name"], "reused": True}
    made = call("create_track", name="Drum Room")["track"]
    ref = made.get("guid") or made["number"]
    call("add_fx", track=ref, name="ReaVerbate")
    call("set_fx_parameters", track=ref, fx=1, changes=[
        {"parameter": "Wet", "display_value": 0}, {"parameter": "Dry", "display_value": -150},
        {"parameter": "Room size", "value": 0.18}, {"parameter": "Dampening", "value": 0.65}])
    return {"track": ref, "name": "Drum Room", "reused": False}


def _mix_bus_glue(start_bar: float | None, end_bar: float | None) -> dict | None:
    """Gentle glue on the whole mix: ReaComp on the master (before any limiter) at its
    glue settings (2:1, slow attack), calibrated to take about 1 dB off. master_to_target
    reuses and recalibrates it when mastering."""
    from .server import _calibrate_compressor

    fx = call("get_track_details", track="master").get("fx", [])
    if any("comp" in f["name"].lower() or "glue" in f["name"].lower() or "bus force" in f["name"].lower() for f in fx):
        return {"skipped": "the master already has a compressor"}
    limiter = next((f["index"] for f in fx if re.search(r"limit", f["name"], re.I)), None)
    comp = call("add_fx", track="master", name="ReaComp", **({"position": limiter} if limiter else {}))
    profile = plugin_profiles.find_profile(comp["name"])
    changes = [dict(c) for c in profile.setup + profile.glue] if profile else []
    if changes:
        call("set_fx_parameters", track="master", fx=comp["index"], changes=changes)
    result = {"compressor": comp["name"]}
    if profile and profile.drive:
        result["calibration"] = _calibrate_compressor("master", comp["index"], profile, MIX_GLUE_DB, start_bar, end_bar)
    return result


def _reverb_return() -> str:
    overview = call("get_project_overview")
    for t in overview["tracks"]:
        if t["name"].lower() == "drum room":
            continue  # the drums' short room isn't the main reverb
        if re.search(r"verb", t["name"], re.I) or any("verb" in f.lower() for f in t.get("fx", [])):
            if not t.get("item_count"):
                return t["name"]
    call("create_track", name="Reverb")
    call("add_fx", track="Reverb", name="ReaVerbate")
    call("set_fx_parameters", track="Reverb", fx=1, changes=[
        {"parameter": "Wet", "display_value": 0}, {"parameter": "Dry", "display_value": -150},
        {"parameter": "Room size", "value": 0.6}, {"parameter": "Dampening", "value": 0.5}])
    return "Reverb"


@tool(annotations=DESTRUCTIVE)
def auto_mix(
    style: Annotated[str | None, Field(description="Genre (get_genre_profile) to balance for, e.g. 'house', 'pop'")] = None,
    start_bar: Bar = None,
    end_bar: Annotated[float | None, Field(description="Measure this range (default: the whole song)")] = None,
    reverb: Annotated[bool, Field(description="Feed a reverb return (an existing one, or a new ReaVerbate)")] = True,
    sidechain: Annotated[bool, Field(description="Duck bass (and pads) under the kick in dance styles")] = True,
    glue: Annotated[bool, Field(description=(
        "Glue the mix together: the drums through one calibrated bus compressor and a shared short room, leads "
        "and vocals into a shared tempo-synced delay, and gentle compression on the whole mix"))] = True,
    dry_run: Annotated[bool, Field(description="Only report what it would do")] = False,
) -> dict:
    """A whole first mix in one call: measures every track (one render pass), works out
    each one's role, then sets levels for the genre, high-passes everything that isn't
    bass and cuts low-mid mud, compresses vocals/bass/leads that need it, pans the wide
    parts, sends to a reverb return, ducks bass under the kick (dance styles), and sets
    -6 dBFS of headroom for mastering, glues the mix (the drums through one calibrated bus
    compressor and a short shared room; leads and vocals into a shared tempo-synced delay;
    about 1 dB of gentle compression on the whole mix), then measures robot
    vocals' clarity in the mix and,
    if other parts cover the words, raises the vocal and ducks the parts covering it.
    Saves a copy of the project first when it has a file. Leaves tracks the user already set up (EQ, compression, panning) alone on those
    points. Then check it: show_spectrogram, check_vocal_clarity, compare_mix_to_style."""
    profile = None
    if style:
        g = genres.find(style)
        profile = {"family": g.family, "mix": {"low_end": g.mix.low_end}, "name": g.name}
    channels = _channels()
    if not channels:
        raise ValueError("no tracks with sound to mix")
    stems = call("render_stems", timeout=900.0, tracks=[c["track"] for c in channels],
                 start_bar=start_bar, end_bar=end_bar)
    by_track = {s["track"]["number"]: s["file"] for s in stems.get("stems", [])}
    try:
        for c in channels:
            f = by_track.get(c["track"])
            if not f:
                continue
            m = analysis.analyze_file(f)
            if m.get("silent"):
                continue
            c["level"] = m["loudness"].get("max_short_term_lufs") or m["loudness"].get("integrated_lufs")
            c["peak_db"] = m["levels"]["sample_peak_dbfs"]
            c["crest_db"] = m["levels"]["crest_factor_db"]
            c["spectrum"] = m["spectrum"]
            c["role"] = role_of(c["name"], m["spectrum"])
    finally:
        for f in stems.get("files", []):
            Path(f).unlink(missing_ok=True)
    for c in channels:
        c.setdefault("role", role_of(c["name"]))
    plan = plan_mix(channels, profile)
    report = {"style": (profile or {}).get("name"), "plan": plan["channels"], "sidechains": plan["sidechains"]}
    if dry_run:
        return report
    confirm_with_user("mix every track (levels, EQ, compression, panning, reverb, sidechain)")
    paths = call("project_paths")
    if paths.get("project"):
        project = Path(paths["project"])
        backup = project.with_name(project.stem + " (before auto_mix).rpp")
        n = 2
        while backup.exists():  # a second run keeps the first run's "before" copy
            backup = project.with_name(f"{project.stem} (before auto_mix {n}).rpp")
            n += 1
        backup = str(backup)
        call("save_project", mode="copy", path=backup)
        report["backup"] = backup
    else:
        report["backup"] = "the project isn't saved, so there's no copy: Ctrl+Z steps back through the changes"
    # With glue, the drums go to their own short room instead of the long reverb.
    room = None
    if glue and reverb and any(a["role"] in DRUM_ROLES and not a.get("skipped") for a in plan["channels"]):
        room = _drum_room()
    verb = _reverb_return() if reverb and any("reverb_send_db" in a and not (room and a["role"] in DRUM_ROLES)
                                              for a in plan["channels"]) else None
    room_sending = ({src for src, r in ((t["name"], t) for t in call("get_routing")["tracks"])
                     for snd in r.get("sends") or [] if snd["to"] == room["name"]} if room else set())
    already_sending = {src for src, r in ((t["name"], t) for t in call("get_routing")["tracks"])
                       for snd in r.get("sends") or [] if verb and snd["to"] == verb}
    by_ref = {c["ref"]: c for c in channels}
    for a in plan["channels"]:
        c = by_ref[a["ref"]]
        track = a["ref"]
        if "gain_db" in a:
            call("set_track_properties", track=track, volume_db=round(c.get("volume_db", 0) + a["gain_db"], 1))
        if "pan" in a:
            call("set_track_properties", track=track, pan=a["pan"])
        if a.get("skipped"):
            continue
        if "highpass_hz" in a or "mud_cut_db" in a:
            # After the last instrument: an EQ before a synth does nothing, and one between
            # sampler slots filters only the slots before it.
            fx = call("get_track_details", track=track).get("fx", [])
            last_instrument = max((f["index"] for f in fx if f.get("instrument")), default=0)
            eq = call("add_fx", track=track, name="ReaEQ", position=last_instrument + 1)
            changes = [{"parameter": "Freq-High Pass 5", "display_value": a["highpass_hz"]}] if "highpass_hz" in a else []
            if "mud_cut_db" in a:
                changes += [{"parameter": "Freq-Band 2", "display_value": 350},
                            {"parameter": "Gain-Band 2", "display_value": a["mud_cut_db"]},
                            {"parameter": "BW-Band 2", "display_value": 1.0}]
            call("set_fx_parameters", track=track, fx=eq["index"], changes=changes)
        if "compress" in a:
            k = a["compress"]
            comp = call("add_fx", track=track, name="ReaComp")
            call("set_fx_parameters", track=track, fx=comp["index"], changes=[
                {"parameter": "Threshold", "display_value": k["threshold_db"]},
                {"parameter": "Ratio", "display_value": k["ratio"]},
                {"parameter": "Attack", "display_value": k["attack_ms"]},
                {"parameter": "Release", "display_value": k["release_ms"]}])
        if room and a["role"] in DRUM_ROLES:
            if a["name"] not in room_sending:  # a level set earlier stays
                call("set_send", source=track, destination=room["track"], volume_db=ROOM_DB[a["role"]])
        elif verb and "reverb_send_db" in a and a["name"] not in already_sending:
            call("set_send", source=track, destination=verb, volume_db=a["reverb_send_db"])
        elif a["name"] in already_sending:
            a["reverb_send_kept"] = True  # the user's (or an earlier pass's) send level stays
    delay = None
    if glue:
        # Leads and vocals share one echo, as they share the reverb. Busy sequenced parts
        # (arps, plucks, sequences) stay dry: a dotted-8th echo turns them to mush.
        senders = [a for a in plan["channels"] if a["role"] in DELAY_DB and not a.get("skipped")
                   and not re.search(r"arp|pluck|seq", a["name"], re.I)]
        if senders:
            try:
                delay = _delay_return(float(call("get_project_overview").get("tempo_bpm") or 120))
                sending = {name for name, r in ((t["name"], t) for t in call("get_routing")["tracks"])
                           for snd in r.get("sends") or [] if snd["to"] == delay["name"]}
                for a in senders:
                    if a["name"] not in sending:  # a level set earlier (by the user or a run) stays
                        call("set_send", source=a["ref"], destination=delay["track"], volume_db=DELAY_DB[a["role"]])
                report["delay_return"] = {**delay, "fed_by": [a["name"] for a in senders]}
            except Exception as e:  # noqa: BLE001
                report.setdefault("warnings", []).append(f"delay return: {e}")
    if sidechain:
        for d in plan["sidechains"]:
            try:
                setup_sidechain(source=d.get("source_ref", d["source"]), target=d.get("target_ref", d["target"]),
                                depth=d["depth"])
            except Exception as e:  # noqa: BLE001
                report.setdefault("warnings", []).append(f"sidechain {d['source']} -> {d['target']}: {e}")
    # Headroom: move every fader together so the mix peaks around -6 dBFS.
    master = analyze_audio(track="master", start_bar=start_bar, end_bar=end_bar)
    peak = master.get("levels", {}).get("sample_peak_dbfs")
    if peak is not None and abs(peak - HEADROOM_PEAK_DB) > 1.0:
        shift = round(HEADROOM_PEAK_DB - peak, 1)
        for c in (c for c in channels if c.get("level") is not None):
            now = call("get_track_details", track=c["ref"])["volume_db"]
            call("set_track_properties", track=c["ref"], volume_db=round(now + shift, 1))
        # The reverb and delay returns stay put: their sends follow the track faders
        # (post-fader), so moving the returns too shifted the effects twice.
        report["headroom_shift_db"] = shift
        master = analyze_audio(track="master", start_bar=start_bar, end_bar=end_bar)
    if glue:
        # The drums compressed together as a kit. After the headroom move: the drum bus
        # is fed after the drum faders, so moving them later would undo the calibration.
        try:
            drum_glue = _glue_drums(channels, start_bar, end_bar)
            if drum_glue:
                report["drum_glue"] = drum_glue
                master = analyze_audio(track="master", start_bar=start_bar, end_bar=end_bar)
        except Exception as e:  # noqa: BLE001
            report.setdefault("warnings", []).append(f"drum bus: {e}")
        try:
            mix_glue = _mix_bus_glue(start_bar, end_bar)
            if mix_glue:
                report["mix_bus_glue"] = mix_glue
                master = analyze_audio(track="master", start_bar=start_bar, end_bar=end_bar)
        except Exception as e:  # noqa: BLE001
            report.setdefault("warnings", []).append(f"mix bus glue: {e}")
    if room:
        report["drum_room"] = room
    vocal_fixes = _clear_robot_vocals(plan["channels"], start_bar, end_bar)
    if vocal_fixes:
        report["vocal_clarity"] = vocal_fixes
        master = analyze_audio(track="master", start_bar=start_bar, end_bar=end_bar)
    report["result"] = {"peak_dbfs": master.get("levels", {}).get("sample_peak_dbfs"),
                        "integrated_lufs": master.get("loudness", {}).get("integrated_lufs"),
                        "next": "Look and measure: show_spectrogram, check_vocal_clarity on vocals, "
                                "compare_mix_to_style; then master_to_target."}
    if verb:
        report["reverb_return"] = verb
    # The faders as they now stand (the headroom move shifted every one of them).
    tracks = {t["name"]: t for t in call("get_project_overview")["tracks"]}
    report["faders_db"] = {name: tracks[name].get("volume_db") for name in [c["name"] for c in channels] + ([verb] if verb else [])
                           if name in tracks}
    return report
