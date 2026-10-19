"""auto_mix: a whole first mix in one call.

Every track that reaches the master is rendered in one pass and measured; each gets a
role (kick, bass, vocal, keys...) from its name and its sound; then levels are set
for the genre, non-bass parts are high-passed and cleared of mud, the parts that need
it are compressed, the wide parts are panned, a reverb return is fed, and the bass
ducks under the kick in dance styles. Finally the mix is measured again and its
headroom set for mastering. A starting point that Claude then refines by measuring.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Annotated

import numpy as np
from pydantic import Field

from . import analysis, genres, plugin_profiles
from .server import DESTRUCTIVE, Bar, analyze_audio, call, confirm_with_user, setup_sidechain, tool

# Loudness of each role while it plays (max short-term LUFS), relative to the drums.
ROLE_LEVELS = {"kick": 0, "drums": 0, "snare": -3, "perc": -9, "bass": -2, "vocal": -1, "lead": -5,
               "keys": -7, "pad": -10, "fx": -12, "other": -7}
HIGHPASS_HZ = {"snare": 100, "perc": 300, "vocal": 110, "lead": 150, "keys": 140, "pad": 180, "fx": 150, "other": 120}
REVERB_DB = {"vocal": -12, "lead": -15, "keys": -15, "pad": -9, "snare": -21, "perc": -24, "other": -18}
PAN_WIDTH = {"perc": 0.35, "keys": 0.25, "pad": 0.2, "fx": 0.4, "other": 0.3, "lead": 0.0}
COMPRESS = {"vocal": (3.0, 5, 80), "bass": (4.0, 20, 120), "lead": (2.5, 10, 100)}  # ratio, attack ms, release ms
HEADROOM_PEAK_DB = -6.0
# The tone pass (shares of each part's own energy, %).
PRESENCE_LOW_PCT, PRESENCE_HIGH_PCT = 8.0, 30.0   # 2-6 kHz for vocals and leads: lift under, cut over
PRESENCE_LIFT_DB, PRESENCE_CUT_DB, PRESENCE_HZ = 1.5, -2.0, 3000
AIR_LOW_PCT, AIR_LIFT_DB, AIR_HZ = 2.0, 1.5, 10000
CARVE_DB = -2.5          # kick and bass each cut where the other is loudest below 120 Hz
LOW_HEAVY_KEYS_PCT = 15  # keys and pads with more of their energy under 250 Hz get a higher high pass
NO_HIGHPASS_HZ = 20      # ReaEQ's band 5 is a high pass that defaults to 100 Hz: parked here when unwanted
LOW_MONO_CORRELATION = 0.9   # a bass or kick whose lows correlate less than this gets narrowed
WIDEN_DB, WIDEN_MIN_CORRELATION = 4.0, 0.6   # pads/keys in wide genres; only while they stay safe in mono
WIDTH_FX = "JS: Stereo Width"
PEAKY_MIX_PLR_DB = 12.0  # a mix whose peaks sit further over its loudness needs density before mastering
# Loudness (K-weighted) underrates sub-bass, so a sustained sub drone measured "quiet"
# and got boosted +6 to +12 dB until it was most of the mix: boosts are capped.
MAX_BOOST_DB, MAX_BOOST_LOW_DB = 6.0, 2.0
LOW_HEAVY_PCT = 50   # sub + bass share above which a part counts as low-heavy

ROLE_WORDS = [
    ("kick", r"\bkick|\bbd\b|bass ?drum"),
    ("snare", r"snare|clap"),
    ("perc", r"hat|\bhh\b|cymbal|ride|crash|shaker|perc|conga|bongo|tamb|rim\b|tom"),
    ("bass", r"bass|\bsub\b|808 ?bass"),
    ("vocal", r"vocal|\bvox|voice|chops?\b|singer|acapella|talk ?box|vocoder|robot"),
    ("drums", r"drum|\bkit\b|909|808|beat"),
    ("pad", r"\bpad|string|choir|atmos|ambien"),
    ("keys", r"key|piano|rhodes|clav|organ|\bep\b|wurli|stab|brass|chord|guitar"),
    ("lead", r"lead|hook|arp|pluck|melody|synth|solo"),
    ("fx", r"\bfx\b|riser|sweep|impact|noise|downlifter|uplifter|whoosh|transition"),
]
DANCE_FAMILIES = {"electronic dance"}
MELODY_OVER_BED_FAMILIES = {"film and games", "ambient and experimental", "classical"}
BED_UNDER_LEAD_LU = 3


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


def _loudest_low_band(spectrum: dict | None) -> int | None:
    """The louder of a part's 31.5 Hz and 63 Hz octaves: where its weight sits under 120 Hz."""
    octaves = (spectrum or {}).get("octave_bands_db") or {}
    lows = [(hz, octaves.get(label)) for hz, label in ((31.5, "31.5 Hz"), (63, "63 Hz")) if octaves.get(label) is not None]
    return int(max(lows, key=lambda x: x[1])[0] * 1.0 + 0.5) if lows else None


def eq_changes(a: dict) -> list[dict]:
    """ReaEQ settings for a plan action: band 5 the high pass (parked at 20 Hz when none
    is wanted: it defaults to 100 Hz), band 2 the mud cut or the kick/bass carve, band 3
    presence, band 4's shelf the air."""
    changes = [{"parameter": "Freq-High Pass 5", "display_value": a.get("highpass_hz", NO_HIGHPASS_HZ)}]
    if "mud_cut_db" in a:
        changes += [{"parameter": "Freq-Band 2", "display_value": 350},
                    {"parameter": "Gain-Band 2", "display_value": a["mud_cut_db"]},
                    {"parameter": "BW-Band 2", "display_value": 1.0}]
    elif "carve" in a:
        changes += [{"parameter": "Freq-Band 2", "display_value": a["carve"]["hz"]},
                    {"parameter": "Gain-Band 2", "display_value": a["carve"]["db"]},
                    {"parameter": "BW-Band 2", "display_value": 1.0}]
    if "presence_db" in a:
        changes += [{"parameter": "Freq-Band 3", "display_value": PRESENCE_HZ},
                    {"parameter": "Gain-Band 3", "display_value": a["presence_db"]},
                    {"parameter": "BW-Band 3", "display_value": 1.5}]
    if "air_db" in a:
        changes += [{"parameter": "Freq-High Shelf 4", "display_value": AIR_HZ},
                    {"parameter": "Gain-High Shelf 4", "display_value": a["air_db"]}]
    return changes


def _kick_bass_carve(channels: list[dict]) -> dict[str, dict]:
    """Room for kick and bass: the bass cut where the kick is loudest under 120 Hz, and the
    kick cut where the bass is, when that's a different octave (if they share one, the
    kick keeps it). {track name: {'hz', 'db'}}."""
    kick = next((c for c in channels if c["role"] == "kick" and not c.get("has_eq")), None)
    bass = next((c for c in channels if c["role"] == "bass" and not c.get("has_eq")), None)
    if not kick or not bass:
        return {}
    kb, bb = _loudest_low_band(kick.get("spectrum")), _loudest_low_band(bass.get("spectrum"))
    out = {}
    if kb:
        out[bass["name"]] = {"hz": kb, "db": CARVE_DB}
    if bb and kb and bb != kb:
        out[kick["name"]] = {"hz": bb, "db": CARVE_DB}
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
    if style.get("family") in MELODY_OVER_BED_FAMILIES:
        # A cue's solo melody leads over its drone: the dance-music bass level (3 LU over
        # the lead) put a solo flute under the drone in an ambient game cue.
        offsets["bass"] = min(offsets["bass"], offsets["lead"] - BED_UNDER_LEAD_LU)
    playing = [c for c in channels if c.get("level") is not None]
    carve = _kick_bass_carve(playing)
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
            if c["role"] in ("keys", "pad") and low_share(c.get("spectrum")) > LOW_HEAVY_KEYS_PCT:
                # Too much of it under 250 Hz: it crowds the bass, whatever its lowest note.
                hp = max(hp or 0, min(250, int(HIGHPASS_HZ[c["role"]] * 1.5)))
            if hp:
                a["highpass_hz"] = hp
            bands = (c.get("spectrum") or {}).get("bands", {})
            mud = (bands.get("low mids (250-500 Hz)") or {}).get("share_pct", 0)
            if c["role"] in ("keys", "pad", "lead", "vocal", "other") and mud > 25:
                a["mud_cut_db"] = -3.0 if mud > 35 else -2.0
        if not c.get("has_eq"):
            bands = (c.get("spectrum") or {}).get("bands", {})
            if c["role"] in ("vocal", "lead"):
                presence = sum((bands.get(k) or {}).get("share_pct", 0) for k in ("upper mids (2-4 kHz)", "presence (4-6 kHz)"))
                if presence and presence < PRESENCE_LOW_PCT:
                    a["presence_db"] = PRESENCE_LIFT_DB
                elif presence > PRESENCE_HIGH_PCT:
                    a["presence_db"] = PRESENCE_CUT_DB
                air = (bands.get("air (6-20 kHz)") or {}).get("share_pct")
                if air is not None and air < AIR_LOW_PCT:
                    a["air_db"] = AIR_LIFT_DB
            if c["name"] in carve:
                a["carve"] = carve[c["name"]]
        if c["role"] in COMPRESS and not c.get("has_comp") and (c.get("crest_db") or 0) > 12:
            ratio, attack, release = COMPRESS[c["role"]]
            a["compress"] = {"ratio": ratio, "attack_ms": attack, "release_ms": release,
                             "threshold_db": round((c.get("peak_db") or -6) - 10, 1)}
        stereo_info = c.get("stereo") or {}
        low_corr = stereo_info.get("low_end_correlation_below_150hz")
        if c["role"] in ("bass", "kick") and low_corr is not None and low_corr < LOW_MONO_CORRELATION:
            a["mono_low"] = True        # a bass or kick whose lows spread: they belong in the middle
        elif c["role"] == "drums" and low_corr is not None and low_corr < LOW_MONO_CORRELATION:
            a["low_end_not_mono"] = round(low_corr, 2)   # a whole kit: narrowing it would close the hats too
        if (c["role"] in ("pad", "keys") and (style.get("mix") or {}).get("width") == "wide"
                and (stereo_info.get("correlation") or 0) >= WIDEN_MIN_CORRELATION
                and (stereo_info.get("side_to_mid_db") if stereo_info.get("side_to_mid_db") is not None else -60) < -9):
            a["widen_db"] = WIDEN_DB
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


def _glue_drums(channels: list[dict], start_bar: float | None, end_bar: float | None,
                span: tuple[float, float] | None = None) -> dict | None:
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
    if str(target) in ADDED_COMPRESSORS:
        # The dynamics stage just compressed this kit: that compressor glues it.
        return {"where": how, "compressor": "the dynamics stage's ReaComp", "track": target}
    if any("comp" in f["name"].lower() or "glue" in f["name"].lower() for f in existing):
        return {"skipped": f"there's already a compressor where the drum glue would go ({how[3:]})"}
    comp = call("add_fx", track=target, name="ReaComp", **({"position": position} if position else {}))
    profile = plugin_profiles.find_profile(comp["name"])
    changes = [dict(c) for c in profile.setup] if profile else []
    changes += [{"parameter": "Ratio", "display_value": 4}, {"parameter": "Attack", "display_value": 10},
                {"parameter": "Release", "display_value": 80}]
    call("set_fx_parameters", track=target, fx=comp["index"], changes=changes)
    result = {"where": how, "compressor": comp["name"], "track": target}
    if profile and profile.drive:
        from . import batch

        with batch.span_hints({target: span} if span and start_bar is None and end_bar is None else {}):
            result["calibration"] = _calibrate_compressor(target, comp["index"], profile, DRUM_GLUE_DB, start_bar,
                                                          end_bar)
    return result


# The dynamics stage: peaky parts compressed (and drums soft-clipped) before mastering,
# so the master doesn't have to crush them. Genres that should breathe keep their dynamics.
GENTLE_FAMILIES = {"classical", "film and games", "jazz", "blues", "ambient and experimental", "european folk",
                   "country and folk"}
# Peak-to-loudness (peak minus max short-term LUFS) over which a part is compressed: the
# number the master's limiter has to deal with. (Crest factor against the whole file's RMS
# read a steady four-on-the-floor kit with 17 dB of it as under 14.)
DRUM_PLR_DB, DRUM_COMP_DB, DRUM_SHAVE_DB = 12.0, 2.5, 2.5
TONAL_PLR_DB, TONAL_COMP_DB = 10.0, 1.5
TONAL_ROLES = ("keys", "pad", "lead", "other")
SOFT_CLIPPER = "JS: Soft Clipper/Limiter"   # Boost (dB) into a soft knee that rounds peaks over 0 dBFS


def _shape_dynamics(channels: list[dict], actions: list[dict], family: str | None, start_bar: float | None,
                    end_bar: float | None) -> list[dict]:
    """Compression where a part's peaks stand far over its loudness: drums with a
    peak-to-loudness over DRUM_PLR_DB get ReaComp (4:1, 15/80 ms) calibrated to take
    DRUM_COMP_DB off, then a soft clipper that rounds the last DRUM_SHAVE_DB of peaks (the
    fader comes down by the clipper's boost, so the part's loudness stays); keys, pads
    and leads over TONAL_PLR_DB get 2:1 calibrated to TONAL_COMP_DB. Parts the user (or the plan)
    already compresses are left alone. Skipped for genres that should breathe. Every
    compressor is added first and they're calibrated together (shared renders)."""
    from . import server

    if family in GENTLE_FAMILIES:
        return [{"skipped": f"{family} keeps its dynamics: no extra compression"}]
    planned = {a["ref"] for a in actions if "compress" in a or a.get("skipped")}
    work = []
    for c in channels:
        if c.get("level") is None or c.get("has_comp") or c["ref"] in planned:
            continue
        drum = c["role"] in DRUM_ROLES
        plr = (c["peak_db"] - c["level"]) if c.get("peak_db") is not None else None
        if plr is None or not ((drum and plr > DRUM_PLR_DB) or (c["role"] in TONAL_ROLES and plr > TONAL_PLR_DB)):
            continue
        entry: dict = {"track": c["name"], "peak_to_loudness_db": round(plr, 1)}
        try:
            comp = call("add_fx", track=c["ref"], name="ReaComp")
            ratio, attack, release, target = (4, 15, 80, DRUM_COMP_DB) if drum else (2, 20, 150, TONAL_COMP_DB)
            call("set_fx_parameters", track=c["ref"], fx=comp["index"], changes=[
                {"parameter": "Ratio", "display_value": ratio}, {"parameter": "Attack", "display_value": attack},
                {"parameter": "Release", "display_value": release}])
            entry["compressor"] = {"ratio": ratio}
            work.append({"c": c, "entry": entry, "comp": comp, "drum": drum, "target": target,
                         "profile": plugin_profiles.find_profile(comp["name"])})
        except Exception as e:  # noqa: BLE001 - one part's trouble shouldn't stop the mix
            entry["error"] = str(e)
            work.append({"c": c, "entry": entry, "comp": None, "drum": drum})
    jobs = [w for w in work if w.get("comp") and w["profile"] and w["profile"].drive]
    results = server._calibrate_compressors([
        {"track": w["c"]["ref"], "fx": w["comp"]["index"], "profile": w["profile"], "target": w["target"],
         "span": None} for w in jobs], start_bar, end_bar)
    for w, cal in zip(jobs, results):
        if "error" in cal:
            w["entry"]["error"] = cal["error"]
            try:  # a half-calibrated compressor would squash at whatever step it stopped on
                call("remove_fx", track=w["c"]["ref"], fx=w["comp"]["index"])
                w["entry"]["removed"] = "its compressor, since calibration failed"
            except Exception:  # noqa: BLE001
                pass
            w["comp"] = None
            w["entry"].pop("compressor", None)
            continue
        w["entry"]["compressor"].update(reduction_db=cal.get("loud_part_reduction_db"), threshold_db=cal.get("value"))
    clip_tracks = [w for w in work if w.get("comp") and w["drum"]]
    peaks = _peaks_now([w["c"]["ref"] for w in clip_tracks], start_bar, end_bar) if len(clip_tracks) > 1 else {}
    for w in clip_tracks:
        try:
            w["entry"]["soft_clip"] = _soft_clip(w["c"]["ref"], start_bar, end_bar, peaks.get(w["c"]["ref"]))
        except Exception as e:  # noqa: BLE001
            w["entry"]["error"] = str(e)
    done = []
    for w in work:
        if w.get("comp"):
            ADDED_COMPRESSORS.add(str(w["c"]["ref"]))
        done.append(w["entry"])
    return done


def _peaks_now(tracks: list, start_bar: float | None, end_bar: float | None) -> dict:
    """Each track's sample peak (dBFS) over the range, from one render pass of them all."""
    from . import batch

    audio = batch.render_group(tracks, start_bar, end_bar)
    out = {}
    for t in tracks:
        x = audio.get(t)
        if x is not None and x.size:
            peak = float(abs(x).max())
            out[t] = analysis._db(peak) if peak > 0 else None
    return out


# Tracks whose compressor this run's dynamics stage added: the drum glue may reuse it.
ADDED_COMPRESSORS: set[str] = set()


def _soft_clip(track, start_bar: float | None, end_bar: float | None, peak: float | None = None) -> dict:
    """The soft clipper after the track's compressor, its boost set so the peaks reach
    DRUM_SHAVE_DB over its knee at 0 dBFS, and the fader down by the same boost. peak:
    the track's sample peak if it was just measured (else it's rendered here)."""
    from .server import analyze_audio

    if peak is None:
        m = analyze_audio(track=track, start_bar=start_bar, end_bar=end_bar)
        peak = (m.get("levels") or {}).get("sample_peak_dbfs")
    details = call("get_track_details", track=track)
    fader = details.get("volume_db") or 0.0
    if peak is None:
        return {"skipped": "silent in that range"}
    pre_fader_peak = peak - fader
    boost = round(max(0.0, min(9.0, DRUM_SHAVE_DB - pre_fader_peak)), 1)
    if boost < 0.5:
        return {"skipped": "its peaks already sit at the clipper's knee"}
    if pre_fader_peak + boost <= 0.5:
        return {"skipped": f"its peaks sit {-pre_fader_peak:g} dB under the clipper's knee: too far to round"}
    clip = call("add_fx", track=track, name=SOFT_CLIPPER)
    call("set_fx_parameters", track=track, fx=clip["index"], changes=[
        {"parameter": "Boost (dB)", "display_value": boost}, {"parameter": "Output Brickwall (dB)", "display_value": 0}])
    call("set_track_properties", track=track, volume_db=round(fader - boost, 1))
    shaved = round(min(DRUM_SHAVE_DB, pre_fader_peak + boost), 1)
    return {"boost_db": boost, "peaks_rounded_db": shaved, "fader_db": round(fader - boost, 1)}


SECTION_GAIN_FX, SECTION_GAIN_PARAM = "JS: Volume Adjustment", "Adjustment (dB)"   # first on the master
SECTION_LIFT_LU = 1.5    # a chorus or drop should come out about this much over the calmer section before it
MIN_LIFT_LU = 1.0        # under this it doesn't feel like a lift
MAX_SECTION_GAIN_DB = 2.5


def plan_section_lifts(sections: list[dict]) -> list[dict]:
    """Per section: its loudness and the gain to add so each section that should lift
    (its name promises more energy than the one before) comes out about SECTION_LIFT_LU
    over it, at most MAX_SECTION_GAIN_DB. sections: [{'name', 'lufs'}] in order."""
    from . import arrange_tools

    out = []
    for i, sec in enumerate(sections):
        row = {"section": sec["name"], "lufs": sec.get("lufs"), "energy": arrange_tools.energy(sec["name"]), "gain_db": 0.0}
        if i and sec.get("lufs") is not None and out[-1]["lufs"] is not None and row["energy"] > out[-1]["energy"]:
            lift = (sec["lufs"] + 0.0) - (out[-1]["lufs"] + out[-1]["gain_db"])
            if lift < MIN_LIFT_LU:
                row["gain_db"] = round(min(MAX_SECTION_GAIN_DB, SECTION_LIFT_LU - lift), 1)
        out.append(row)
    return out


def _section_moves(start_bar: float | None, end_bar: float | None) -> dict | None:
    """Rides the whole mix up in the sections that should lift but don't (a chorus or drop
    less than 1 LU over the verse before it), with a gain plugin on the master after its
    glue and before its limiter, so the limiter still catches it. Needs the sections named as regions; an earlier run's
    ride is kept."""
    from . import analysis
    from .ear_tools import _sections
    from .server import _render_array

    overview = call("get_project_overview")
    regions = overview.get("regions") or []
    if len(regions) < 2:
        return None
    master_fx = call("get_track_details", track="master").get("fx", [])
    if any("volume adjustment" in f["name"].lower() for f in master_fx):
        return {"skipped": "the master already has a section ride (Volume Adjustment) from an earlier pass"}
    audio, fs, render = _render_array("master", start_bar, end_bar)
    offset = render["start"]["seconds"]
    sections = _sections(regions, offset, offset + audio.shape[0] / fs)
    for sec in sections:
        a, b = int((sec["start"] - offset) * fs), int((sec["end"] - offset) * fs)
        sec["lufs"] = analysis.loudness(audio[max(0, a):b], fs).get("integrated_lufs")
    table = plan_section_lifts(sections)
    if not any(r["gain_db"] for r in table):
        return {"sections": table, "note": "every section already lifts where it should"}
    limiter = next((f["index"] for f in master_fx if re.search(r"limit", f["name"], re.I)), None)
    # After the mix-bus glue (which would compress the lift back) and before a limiter.
    gain = call("add_fx", track="master", name=SECTION_GAIN_FX, **({"position": limiter} if limiter else {}))
    call("set_fx_parameters", track="master", fx=gain["index"],
         changes=[{"parameter": SECTION_GAIN_PARAM, "display_value": 0}])
    starts = call("time_to_positions", times=[sec["start"] for sec in sections])
    points = [{"bar": pos["bar"], "beat": pos.get("beat") or 1, "value": row["gain_db"], "shape": "square"}
              for pos, row in zip(starts, table)]
    from .server import AutomationPoint, write_automation

    write_automation(track="master", target="fx", fx=gain["index"], parameter=SECTION_GAIN_PARAM,
                     points=[AutomationPoint(**p) for p in points])
    return {"sections": table, "how": f"{SECTION_GAIN_FX} on the master before its limiter, stepped at each section start"}


SATURATION_FX, SATURATION_PARAM = "JS: Saturation", "Amount (%)"
COLOUR_RISE_DB = (2.0, 4.0)     # how much the 2-8 kHz band should come up: audible grit, not fizz
COLOUR_MAX_CREST_DROP_DB = 1.0  # more punch lost than this and it's distortion, not colour
COLOUR_STEPS = (5, 15, 30, 45, 60, 80)
COLOUR_HOPELESS_AT, COLOUR_HOPELESS_DB = 30, 0.5   # at 30% with under 0.5 dB of rise, more won't reach 2 dB


def band_db(audio, fs: float, lo: float = 2000, hi: float = 8000) -> float:
    """Energy (dB) in a band of a render."""
    import numpy as np
    from scipy import signal as sg

    mono = audio.mean(axis=1) if audio.ndim > 1 else audio
    freqs, psd = sg.welch(mono, fs=fs, nperseg=min(8192, mono.size))
    return 10 * float(np.log10(psd[(freqs >= lo) & (freqs < hi)].sum() + 1e-30))


def choose_colour(trials: list[dict]) -> dict | None:
    """The first amount whose 2-8 kHz rise reaches COLOUR_RISE_DB with the crest within
    COLOUR_MAX_CREST_DROP_DB, else the closest under the crest limit. trials: [{'amount',
    'rise_db', 'crest_drop_db'}] in rising order."""
    lo, hi = COLOUR_RISE_DB
    ok = [t for t in trials if t["crest_drop_db"] <= COLOUR_MAX_CREST_DROP_DB and t["rise_db"] <= hi + 1]
    inside = [t for t in ok if t["rise_db"] >= lo]
    if inside:
        return inside[0]
    if not ok and trials and trials[0]["crest_drop_db"] <= COLOUR_MAX_CREST_DROP_DB:
        return trials[0]  # the gentlest setting already overshoots: keep it rather than none
    return max(ok, key=lambda t: t["rise_db"]) if ok and max(t["rise_db"] for t in ok) >= 0.5 else None


def _add_colour(targets: list[tuple[str, object]], start_bar: float | None, end_bar: float | None,
                spans: dict | None = None) -> list[dict]:
    """Saturation on the bass and the drum bus, its amount found by measurement: raised
    until the 2-8 kHz band comes up COLOUR_RISE_DB (harmonics a small speaker can play)
    while the crest factor drops less than COLOUR_MAX_CREST_DROP_DB. Measured on the
    loudest 16 bars (spans: {track: (start_bar, end_bar)} when auto_mix already knows
    them). Targets on the same span share their renders: one pass per trial amount for
    all of them. targets: [(label, track ref)]."""
    from . import batch
    from .server import _loudest_bars, _render_array

    done: dict = {}
    live = []
    for label, track in targets:
        entry: dict = {"track": label}
        done[label] = entry
        try:
            fx = call("get_track_details", track=track).get("fx", [])
            if any("satur" in f["name"].lower() for f in fx):
                entry["skipped"] = "it already has a saturator"
                continue
            sat = call("add_fx", track=track, name=SATURATION_FX)
            span = (spans or {}).get(track) if start_bar is None and end_bar is None else None
            if span is None and start_bar is None and end_bar is None:
                call("update_fx", track=track, fx=sat["index"], enabled=False)
                try:
                    full, fs, render = _render_array(track, None, None)
                    span = _loudest_bars(track, full, fs, render)
                finally:
                    call("update_fx", track=track, fx=sat["index"], enabled=True)
            live.append({"label": label, "track": track, "sat": sat, "span": span or (start_bar, end_bar),
                         "entry": entry, "trials": []})
        except Exception as e:  # noqa: BLE001
            entry["error"] = str(e)
    groups: dict = {}
    for t in live:
        groups.setdefault(tuple(t["span"]), []).append(t)
    for (lo_bar, hi_bar), group in groups.items():
        try:
            for t in group:
                call("update_fx", track=t["track"], fx=t["sat"]["index"], enabled=False)
            try:
                dry = batch.render_group([t["track"] for t in group], lo_bar, hi_bar)
            finally:
                for t in group:
                    call("update_fx", track=t["track"], fx=t["sat"]["index"], enabled=True)
            fs = dry["_fs"]
            for t in group:
                t["dry"] = dry[t["track"]]
                t["base_band"] = band_db(t["dry"], fs)
                t["base_crest"] = analysis.envelope_range(t["dry"], fs) or 0.0
            for amount in COLOUR_STEPS:
                searching = [t for t in group if not t.get("finished")]
                if not searching:
                    break
                for t in searching:
                    call("set_fx_parameters", track=t["track"], fx=t["sat"]["index"],
                         changes=[{"parameter": SATURATION_PARAM, "display_value": amount}])
                wet = batch.render_group([t["track"] for t in searching], lo_bar, hi_bar)
                for t in searching:
                    w, d = wet[t["track"]], t["dry"]
                    # Level-matched: the rise is the band's share going up, not the part getting louder.
                    level_change = 10 * math.log10(float((w ** 2).mean() + 1e-20) / float((d ** 2).mean() + 1e-20))
                    t["trials"].append({"amount": amount,
                                        "rise_db": round(band_db(w, fs) - t["base_band"] - level_change, 2),
                                        "crest_drop_db": round(t["base_crest"] - (analysis.envelope_range(w, fs) or 0.0), 2)})
                    last = t["trials"][-1]
                    if last["rise_db"] >= COLOUR_RISE_DB[0] or last["crest_drop_db"] > COLOUR_MAX_CREST_DROP_DB:
                        t["finished"] = True
                    elif amount >= COLOUR_HOPELESS_AT and last["rise_db"] < COLOUR_HOPELESS_DB:
                        t["finished"] = True   # a third of the way up and barely a change: it won't get there
            for t in group:
                pick = choose_colour(t["trials"])
                t["entry"]["trials"] = t["trials"]
                if pick is None:
                    call("remove_fx", track=t["track"], fx=t["sat"]["index"])
                    t["entry"]["skipped"] = "saturation added no useful harmonics here (already rich, or it cost punch)"
                else:
                    call("set_fx_parameters", track=t["track"], fx=t["sat"]["index"],
                         changes=[{"parameter": SATURATION_PARAM, "display_value": pick["amount"]}])
                    t["entry"].update(amount_pct=pick["amount"], presence_rise_db=pick["rise_db"],
                                      crest_drop_db=pick["crest_drop_db"])
        except Exception as e:  # noqa: BLE001
            for t in group:
                if "amount_pct" in t["entry"]:
                    continue
                t["entry"]["error"] = str(e)
                try:  # don't leave it driven at a trial setting
                    call("remove_fx", track=t["track"], fx=t["sat"]["index"])
                except Exception:  # noqa: BLE001
                    pass
    return [done[label] for label, _ in targets]


def _loud_spans(channels: list[dict], envelopes: dict, offset_s: float) -> dict:
    """Where each stage calibrates, from auto_mix's first pass: the mix's loudest
    CALIBRATE_BARS bars ('_mix', from the parts' summed power) for every part that plays
    there (within 6 dB of its own loudest), so their calibrations share renders; a
    part's own loudest bars when it sits out the mix's peak; the drums' ('_drums') for
    the drum bus. {ref (and name): (start_bar, end_bar)}."""
    from . import batch
    from .server import CALIBRATE_BARS

    if not envelopes:
        return {}
    overview = call("get_project_overview")
    bpm = float(overview.get("tempo_bpm") or 120)
    num, den = (int(x) for x in (overview.get("time_signature") or "4/4").split("/"))
    span_s = CALIBRATE_BARS * num * 4 / den * 60 / bpm
    width = max(1, int(round(span_s / batch.ENV_HOP_S)))
    size = max(e.size for e in envelopes.values())
    mix = np.zeros(size)
    drums = np.zeros(size)
    by_ref = {c["ref"]: c for c in channels}
    for ref, e in envelopes.items():
        mix[: e.size] += e
        if by_ref.get(ref, {}).get("role") in DRUM_ROLES:
            drums[: e.size] += e
    starts = {}
    mix_start = batch.loudest_start_s(mix, span_s)
    if mix_start is None:
        return {}
    starts["_mix"] = mix_start
    i0 = int(round(mix_start / batch.ENV_HOP_S))

    def plays_at_mix_peak(e: np.ndarray, own: float) -> bool:
        at_mix = e[i0: i0 + width].mean() if e[i0: i0 + width].size else 0.0
        o = int(round(own / batch.ENV_HOP_S))
        at_own = e[o: o + width].mean()
        return at_own > 0 and at_mix >= at_own * 10 ** (-6 / 10)

    if drums.any():
        own = batch.loudest_start_s(drums, span_s)
        starts["_drums"] = mix_start if own is not None and plays_at_mix_peak(drums, own) else own
    for ref, e in envelopes.items():
        own = batch.loudest_start_s(e, span_s)
        if own is not None:
            starts[ref] = mix_start if plays_at_mix_peak(e, own) else own
    keys = [k for k, v in starts.items() if v is not None]
    positions = call("time_to_positions", times=[offset_s + starts[k] for k in keys])
    out = {}
    for k, pos in zip(keys, positions):
        first = max(1, int(pos["bar"]))
        span = (float(first), float(first + CALIBRATE_BARS))
        out[k] = span
        c = by_ref.get(k)
        if c:  # by name too; never by number: a sidechain's Duck bus shifts the numbers after it
            out[c["name"]] = span
    return out


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
        {"parameter": "Room size", "value": 0.18}, {"parameter": "Dampening", "value": 0.65},
        {"parameter": "Hipass", "display_value": ROOM_FILTER_HZ[0]},
        {"parameter": "Lowpass", "display_value": ROOM_FILTER_HZ[1]}])
    return {"track": ref, "name": "Drum Room", "reused": False}


def _mix_bus_glue(start_bar: float | None, end_bar: float | None,
                  span: tuple[float, float] | None = None) -> dict | None:
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
        from . import batch

        with batch.span_hints({"master": span} if span and start_bar is None and end_bar is None else {}):
            result["calibration"] = _calibrate_compressor("master", comp["index"], profile, MIX_GLUE_DB, start_bar,
                                                          end_bar)
    return result


# The shared reverb's size by genre family: a tight plate-like room for pop and R&B
# vocals, a hall for pads, film and classical; in between for the rest.
REVERB_SIZE = {"pop": 0.35, "r&b and soul": 0.35, "hip-hop": 0.35, "classical": 0.65, "film and games": 0.65,
               "ambient and experimental": 0.7}
REVERB_FILTER_HZ = (280, 7000)   # a reverb without its lows (mud) and highs (hiss, sibilance) sits behind
ROOM_FILTER_HZ = (150, 8000)


def _predelay_ms(bpm: float) -> float:
    """A 64th note (31 ms at 120 BPM), kept to 20-40 ms: the dry hit lands before its
    reverb, so it stays clear."""
    return round(max(20.0, min(40.0, 60000 / bpm / 16)), 1)


def _reverb_return(bpm: float = 120.0, family: str | None = None) -> str:
    """The shared reverb: an existing return (left as the user set it), or ReaVerbate
    sized for the genre, with a tempo-aware pre-delay and its lows and highs filtered
    off so it gives depth without mud."""
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
        {"parameter": "Room size", "value": REVERB_SIZE.get(family or "", 0.5)},
        {"parameter": "Dampening", "value": 0.5},
        {"parameter": "Delay", "display_value": _predelay_ms(bpm)},
        {"parameter": "Hipass", "display_value": REVERB_FILTER_HZ[0]},
        {"parameter": "Lowpass", "display_value": REVERB_FILTER_HZ[1]}])
    return "Reverb"


@tool(annotations=DESTRUCTIVE)
def auto_mix(
    style: Annotated[str | None, Field(description="Genre (get_genre_profile) to balance for, e.g. 'house', 'pop'")] = None,
    start_bar: Bar = None,
    end_bar: Annotated[float | None, Field(description="Measure this range (default: the whole song)")] = None,
    reverb: Annotated[bool, Field(description="Feed a reverb return (an existing one, or a new ReaVerbate)")] = True,
    sidechain: Annotated[bool, Field(description="Duck bass (and pads) under the kick in dance styles, depth measured")] = True,
    glue: Annotated[bool, Field(description=(
        "Glue the mix together: the drums through one calibrated bus compressor and a shared short room, leads "
        "and vocals into a shared tempo-synced delay, and gentle compression on the whole mix"))] = True,
    dynamics: Annotated[bool, Field(description=(
        "Compress peaky parts before mastering (drums 2-3 dB plus a soft clipper, keys/pads 1-2 dB, parallel "
        "compression on the drum bus) so the master doesn't have to crush them; off for genres that breathe"))] = True,
    colour: Annotated[bool, Field(description=(
        "Saturate the bass and the drum bus, by measurement (2-8 kHz up 2-4 dB, punch kept), so they're heard "
        "on small speakers; off for genres that breathe"))] = True,
    section_moves: Annotated[bool, Field(description=(
        "Ride the mix up in sections that should lift but don't (a chorus or drop under 1 LU over the verse "
        "before it), with a gain plugin first on the master; needs the sections as regions"))] = True,
    dry_run: Annotated[bool, Field(description="Only report what it would do")] = False,
) -> dict:
    """A whole first mix in one call: measures every track (one render pass), works out
    each one's role, then sets levels for the genre; EQ (high-passes what isn't bass,
    a higher one for keys and pads heavy in the lows, low-mid mud cut, kick and bass
    each cut where the other is loudest, presence and air for vocals and leads by their
    measured top end); compresses vocals/bass/leads that need it; narrows a bass or kick
    whose lows spread and widens pads and keys in wide genres; pans the wide parts; a
    reverb sized for the genre (tempo pre-delay, lows and highs filtered off) and a
    tempo-synced delay; ducks bass under the kick (dance styles, depth measured).
    The dynamics stage compresses peaky drums 2-3 dB (plus a soft clipper on their
    last peaks) and keys/pads 1-2 dB, calibrated by measuring gain reduction, so the
    master doesn't have to crush them. Then -6 dBFS of headroom, the drums glued on one
    bus (plus parallel compression), saturation on the bass and the drum bus set by
    measurement, gentle compression on the whole mix, and a level ride lifting
    choruses and drops that don't come out over the section before. Robot vocals
    covered by other parts are raised and cleared. Reports the mix's peak-to-loudness
    and its peakiest parts. Genres that should breathe (classical, film, jazz...) skip
    the dynamics stage and saturation. Saves a copy of the project first when it has a
    file. Leaves tracks the user already set up (EQ, compression, panning) alone on
    those points. Then check it: show_spectrogram, check_vocal_clarity,
    compare_mix_to_style."""
    profile = None
    if style:
        g = genres.find(style)
        profile = {"family": g.family, "mix": {"low_end": g.mix.low_end, "width": g.mix.width}, "name": g.name}
    channels = _channels()
    if not channels:
        raise ValueError("no tracks with sound to mix")
    ADDED_COMPRESSORS.clear()
    stems = call("render_stems", timeout=900.0, tracks=[c["track"] for c in channels],
                 start_bar=start_bar, end_bar=end_bar)
    by_track = {s["track"]["number"]: s["file"] for s in stems.get("stems", [])}
    envelopes: dict = {}
    try:
        for c in channels:
            f = by_track.get(c["track"])
            if not f:
                continue
            m = analysis.analyze_file(f, detail=False)
            if m.get("silent"):
                continue
            try:  # each part's loudness over time: where every later stage calibrates
                import soundfile as sf

                from . import batch

                audio, fs_ = sf.read(f, always_2d=True)
                envelopes[c["ref"]] = batch.track_envelope(audio, int(fs_))
                del audio
            except Exception:  # noqa: BLE001
                pass
            c["level"] = m["loudness"].get("max_short_term_lufs") or m["loudness"].get("integrated_lufs")
            c["peak_db"] = m["levels"]["sample_peak_dbfs"]
            c["crest_db"] = m["levels"]["crest_factor_db"]
            c["spectrum"] = m["spectrum"]
            c["stereo"] = m.get("stereo")
            c["role"] = role_of(c["name"], m["spectrum"])
    finally:
        for f in stems.get("files", []):
            Path(f).unlink(missing_ok=True)
    for c in channels:
        c.setdefault("role", role_of(c["name"]))
    spans = _loud_spans(channels, envelopes, stems.get("start", {}).get("seconds", 0.0)) \
        if start_bar is None and end_bar is None else {}
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
    bpm = float(call("get_project_overview").get("tempo_bpm") or 120)
    verb = None
    if reverb and any("reverb_send_db" in a and not (room and a["role"] in DRUM_ROLES) for a in plan["channels"]):
        try:
            verb = _reverb_return(bpm, (profile or {}).get("family"))
        except Exception as e:  # noqa: BLE001
            report.setdefault("warnings", []).append(f"reverb return: {e}")
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
        if any(k in a for k in ("highpass_hz", "mud_cut_db", "carve", "presence_db", "air_db")):
            # After the last instrument: an EQ before a synth does nothing, and one between
            # sampler slots filters only the slots before it.
            fx = call("get_track_details", track=track).get("fx", [])
            last_instrument = max((f["index"] for f in fx if f.get("instrument")), default=0)
            eq = call("add_fx", track=track, name="ReaEQ", position=last_instrument + 1)
            call("set_fx_parameters", track=track, fx=eq["index"], changes=eq_changes(a))
        if a.get("mono_low") or a.get("widen_db"):
            w = call("add_fx", track=track, name=WIDTH_FX)
            call("set_fx_parameters", track=track, fx=w["index"], changes=[
                {"parameter": "Width Boost (dB)", "display_value": -20 if a.get("mono_low") else a["widen_db"]}])
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
    from . import batch

    with batch.span_hints({k: v for k, v in spans.items() if not str(k).startswith("_")}):
        return _mix_stages(report, plan, channels, profile, spans, room, verb, start_bar, end_bar, dynamics,
                           sidechain, glue, colour, section_moves)


def _mix_stages(report: dict, plan: dict, channels: list[dict], profile: dict | None, spans: dict, room, verb,
                start_bar, end_bar, dynamics: bool, sidechain: bool, glue: bool, colour: bool,
                section_moves: bool) -> dict:
    """auto_mix after the levels, EQ and sends: the measured stages, with the loud
    spans from its first pass. The master is rendered for the headroom and once at the
    end; the stages in between measure their own tracks."""
    # Before the sidechain: the soft clipper's boost changes the kick's level into the
    # sidechain send, which is calibrated next.
    if dynamics:
        try:
            shaped = _shape_dynamics(channels, plan["channels"], (profile or {}).get("family"), start_bar, end_bar)
            if shaped:
                report["dynamics"] = shaped
        except Exception as e:  # noqa: BLE001
            report.setdefault("warnings", []).append(f"dynamics: {e}")
    if sidechain:
        for d in plan["sidechains"]:
            try:
                done_sc = setup_sidechain(source=d.get("source_ref", d["source"]), target=d.get("target_ref", d["target"]),
                                          depth=d["depth"])
                d.update({k: done_sc[k] for k in ("measured_ducking_db", "threshold_db", "detector_lowpass_hz", "note")
                          if k in done_sc})
            except Exception as e:  # noqa: BLE001
                report.setdefault("warnings", []).append(f"sidechain {d['source']} -> {d['target']}: {e}")
    # Headroom: move every fader together so the mix peaks around -6 dBFS. No master
    # effects yet and post-fader sends, so the mix moves by exactly the shift: no second
    # render to confirm it.
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
    changed = False
    if glue:
        # The drums compressed together as a kit. After the headroom move: the drum bus
        # is fed after the drum faders, so moving them later would undo the calibration.
        try:
            drum_glue = _glue_drums(channels, start_bar, end_bar, spans.get("_drums"))
            if drum_glue:
                changed = True
                report["drum_glue"] = drum_glue
                drum_glue["_track"] = drum_glue.pop("track", None)
                if dynamics and drum_glue.get("_track") and (profile or {}).get("family") not in GENTLE_FAMILIES:
                    from .server import add_parallel_compression

                    try:
                        drum_glue["parallel"] = add_parallel_compression(track=drum_glue["_track"], blend_db=-10)
                    except Exception as e:  # noqa: BLE001
                        report.setdefault("warnings", []).append(f"drum parallel compression: {e}")
        except Exception as e:  # noqa: BLE001
            report.setdefault("warnings", []).append(f"drum bus: {e}")
        try:
            mix_glue = _mix_bus_glue(start_bar, end_bar, spans.get("_mix"))
            if mix_glue:
                report["mix_bus_glue"] = mix_glue
                changed = True
        except Exception as e:  # noqa: BLE001
            report.setdefault("warnings", []).append(f"mix bus glue: {e}")
    if colour and (profile or {}).get("family") not in GENTLE_FAMILIES:
        targets = [(c["name"], c["ref"]) for c in channels if c.get("role") == "bass" and c.get("level") is not None]
        glue_track = (report.get("drum_glue") or {}).get("_track")
        if glue_track:
            targets.append(("drum bus", glue_track))
        colour_spans = {ref: spans[ref] for _, ref in targets if ref in spans}
        if glue_track and spans.get("_drums"):
            colour_spans[glue_track] = spans["_drums"]
        if targets:
            try:
                report["colour"] = _add_colour(targets, start_bar, end_bar, colour_spans)
                changed = True
            except Exception as e:  # noqa: BLE001
                report.setdefault("warnings", []).append(f"saturation: {e}")
    if report.get("drum_glue"):
        report["drum_glue"].pop("_track", None)
    if room:
        report["drum_room"] = room
    if section_moves:
        try:
            moves = _section_moves(start_bar, end_bar)
            if moves:
                report["section_moves"] = moves
                changed = True
        except Exception as e:  # noqa: BLE001
            report.setdefault("warnings", []).append(f"section moves: {e}")
    vocal_fixes = _clear_robot_vocals(plan["channels"], start_bar, end_bar)
    if vocal_fixes:
        report["vocal_clarity"] = vocal_fixes
        changed = True
    if changed or "headroom_shift_db" in report or dynamics or sidechain:
        master = analyze_audio(track="master", start_bar=start_bar, end_bar=end_bar)   # the mix as it now stands
    peak = master.get("levels", {}).get("sample_peak_dbfs")
    lufs = master.get("loudness", {}).get("integrated_lufs")
    report["result"] = {"peak_dbfs": peak, "integrated_lufs": lufs,
                        "next": "Look and measure: show_spectrogram, check_vocal_clarity on vocals, "
                                "compare_mix_to_style; then master_to_target."}
    if peak is not None and lufs is not None:
        # Peak-to-loudness: how far the hits stand over the mix. Over about 12 dB the
        # master's limiter has to crush them to reach a modern level.
        plr = round(peak - lufs, 1)
        report["result"]["peak_to_loudness_db"] = plr
        if plr > PEAKY_MIX_PLR_DB:
            report["result"]["dynamics_note"] = (
                f"the mix's peaks sit {plr:g} dB over its loudness: master_to_target will stop short of a loud "
                "target. Compress the peakiest parts (measure_tracks shows them now), or keep the master quieter")
    spread = [a["name"] for a in plan["channels"] if a.get("low_end_not_mono")]
    if spread:
        report["result"]["low_end_not_mono"] = (
            f"{', '.join(spread)}: the kit's lows spread across the speakers (kick or toms panned, stereo samples); "
            "keep the kick in the middle (build_drum_kit puts each sample centred)")
    peaky = sorted(({"track": c["name"], "peak_to_loudness_db": round(c["peak_db"] - c["level"], 1)}
                    for c in channels if c.get("peak_db") is not None and c.get("level") is not None),
                   key=lambda r: -r["peak_to_loudness_db"])
    if peaky:
        # From the first measurement, before the levels and the dynamics stage changed them.
        report["result"]["peakiest_parts_before_mixing"] = peaky[:3]
    if verb:
        report["reverb_return"] = verb
    # The faders as they now stand (the headroom move shifted every one of them).
    tracks = {t["name"]: t for t in call("get_project_overview")["tracks"]}
    report["faders_db"] = {name: tracks[name].get("volume_db") for name in [c["name"] for c in channels] + ([verb] if verb else [])
                           if name in tracks}
    return report
