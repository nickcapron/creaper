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

from . import analysis, genres
from .server import DESTRUCTIVE, Bar, analyze_audio, call, confirm_with_user, setup_sidechain, tool

# Loudness of each role while it plays (max short-term LUFS), relative to the drums.
ROLE_LEVELS = {"kick": 0, "drums": 0, "snare": -3, "perc": -9, "bass": -2, "vocal": -1, "lead": -5,
               "keys": -7, "pad": -10, "fx": -12, "other": -7}
HIGHPASS_HZ = {"snare": 100, "perc": 300, "vocal": 110, "lead": 150, "keys": 140, "pad": 180, "fx": 150, "other": 120}
REVERB_DB = {"vocal": -14, "lead": -17, "keys": -18, "pad": -15, "snare": -21, "perc": -24, "other": -20}
PAN_WIDTH = {"perc": 0.35, "keys": 0.25, "pad": 0.2, "fx": 0.4, "other": 0.3, "lead": 0.0}
COMPRESS = {"vocal": (3.0, 5, 80), "bass": (4.0, 20, 120), "lead": (2.5, 10, 100)}  # ratio, attack ms, release ms
HEADROOM_PEAK_DB = -6.0

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
        a: dict = {"name": c["name"], "role": c["role"]}
        if c.get("level") is not None:
            want = anchor + offsets.get(c["role"], -7)
            a["gain_db"] = round(max(-18.0, min(12.0, want - c["level"])), 1)
        if c["role"] in HIGHPASS_HZ and not c.get("has_eq"):
            a["highpass_hz"] = HIGHPASS_HZ[c["role"]]
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
            if c["role"] == "bass" and not c.get("ducked"):
                duck.append({"source": kick["name"], "target": c["name"], "depth": "medium"})
            elif c["role"] == "pad" and not c.get("ducked"):
                duck.append({"source": kick["name"], "target": c["name"], "depth": "light"})
    return {"anchor_lufs": round(anchor, 1), "channels": actions, "sidechains": duck}


# ------------------------------------------------------------------ executing

def _channels() -> list[dict]:
    """The tracks whose sound reaches the master on their own: skips folders, muted and
    empty tracks, robot-vocal helpers and reverb returns; a track that plays through a
    sidechain 'Duck' bus is mixed on that bus."""
    overview = call("get_project_overview")
    routing = {t["name"]: t for t in call("get_routing")["tracks"]}
    by_name = {t["name"]: t for t in overview["tracks"]}
    out = []
    for t in overview["tracks"]:
        name = t["name"]
        r = routing.get(name, {})
        if t.get("mute") or r.get("folder") or re.search(r" (Voice|Carrier)$", name):
            continue
        if re.search(r"verb|reverb|delay|return", name, re.I) and not t.get("item_count"):
            continue  # an effects return
        source = name[:-5] if name.endswith(" Duck") else None
        if source is None and not t.get("item_count") and not any(
                s["to"] == name for other in routing.values() for s in other.get("sends") or []):
            continue  # nothing plays here
        if source is None and not (r.get("to_master") or r.get("to_parent_folder")):
            continue  # plays through a Duck bus or another track, which is mixed instead
        fx = " ".join(t.get("fx", [])).lower()
        out.append({"name": name, "track": t["number"], "pan": t.get("pan", 0), "volume_db": t.get("volume_db", 0),
                    "has_eq": "eq" in fx, "has_comp": "comp" in fx or "limit" in fx,
                    "ducked": source is not None or (by_name.get(f"{name} Duck") is not None)})
    return out


def _reverb_return() -> str:
    overview = call("get_project_overview")
    for t in overview["tracks"]:
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
    dry_run: Annotated[bool, Field(description="Only report what it would do")] = False,
) -> dict:
    """A whole first mix in one call: measures every track (one render pass), works out
    each one's role, then sets levels for the genre, high-passes everything that isn't
    bass and cuts low-mid mud, compresses vocals/bass/leads that need it, pans the wide
    parts, sends to a reverb return, ducks bass under the kick (dance styles), and sets
    -6 dBFS of headroom for mastering. Saves a copy of the project first when it has a
    file. Leaves tracks the user already set up (EQ, compression, panning) alone on those
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
        backup = str(Path(paths["project"]).with_name(Path(paths["project"]).stem + " (before auto_mix).rpp"))
        call("save_project", mode="copy", path=backup)
        report["backup"] = backup
    else:
        report["backup"] = "the project isn't saved, so there's no copy: Ctrl+Z steps back through the changes"
    verb = _reverb_return() if reverb and any("reverb_send_db" in a for a in plan["channels"]) else None
    numbers = {c["name"]: c for c in channels}
    for a in plan["channels"]:
        c = numbers[a["name"]]
        if "gain_db" in a:
            call("set_track_properties", track=a["name"], volume_db=round(c.get("volume_db", 0) + a["gain_db"], 1))
        if "pan" in a:
            call("set_track_properties", track=a["name"], pan=a["pan"])
        if "highpass_hz" in a:
            eq = call("add_fx", track=a["name"], name="ReaEQ", position=1)
            changes = [{"parameter": "Freq-High Pass 5", "display_value": a["highpass_hz"]}]
            if "mud_cut_db" in a:
                changes += [{"parameter": "Freq-Band 2", "display_value": 350},
                            {"parameter": "Gain-Band 2", "display_value": a["mud_cut_db"]},
                            {"parameter": "BW-Band 2", "display_value": 1.0}]
            call("set_fx_parameters", track=a["name"], fx=eq["index"], changes=changes)
        if "compress" in a:
            k = a["compress"]
            comp = call("add_fx", track=a["name"], name="ReaComp")
            call("set_fx_parameters", track=a["name"], fx=comp["index"], changes=[
                {"parameter": "Threshold", "display_value": k["threshold_db"]},
                {"parameter": "Ratio", "display_value": k["ratio"]},
                {"parameter": "Attack", "display_value": k["attack_ms"]},
                {"parameter": "Release", "display_value": k["release_ms"]}])
        if verb and "reverb_send_db" in a:
            call("set_send", source=a["name"], destination=verb, volume_db=a["reverb_send_db"])
    if sidechain:
        for d in plan["sidechains"]:
            try:
                setup_sidechain(source=d["source"], target=d["target"], depth=d["depth"])
            except Exception as e:  # noqa: BLE001
                report.setdefault("warnings", []).append(f"sidechain {d['source']} -> {d['target']}: {e}")
    # Headroom: move every fader together so the mix peaks around -6 dBFS.
    master = analyze_audio(track="master", start_bar=start_bar, end_bar=end_bar)
    peak = master.get("levels", {}).get("sample_peak_dbfs")
    if peak is not None and abs(peak - HEADROOM_PEAK_DB) > 1.0:
        shift = round(HEADROOM_PEAK_DB - peak, 1)
        for c in channels:
            now = call("get_track_details", track=c["name"])["volume_db"]
            call("set_track_properties", track=c["name"], volume_db=round(now + shift, 1))
        if verb:
            now = call("get_track_details", track=verb)["volume_db"]
            call("set_track_properties", track=verb, volume_db=round(now + shift, 1))
        report["headroom_shift_db"] = shift
        master = analyze_audio(track="master", start_bar=start_bar, end_bar=end_bar)
    report["result"] = {"peak_dbfs": master.get("levels", {}).get("sample_peak_dbfs"),
                        "integrated_lufs": master.get("loudness", {}).get("integrated_lufs"),
                        "next": "Look and measure: show_spectrogram, check_vocal_clarity on vocals, "
                                "compare_mix_to_style; then master_to_target."}
    if verb:
        report["reverb_return"] = verb
    return report
