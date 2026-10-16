"""Choosing sounds by audition: instead of picking a preset by its name, creaper loads
each candidate, plays it the way the part will be played (low notes for a bass, held
notes for a pad), measures what comes out and keeps the one that best fits the role
and the character asked for. The same way a producer flicks through patches, but
measured, because Claude can't hear."""

from __future__ import annotations

import math
import statistics
from typing import Annotated, Literal

from pydantic import Field

from . import listen
from .server import READ_ONLY, TrackRef, call, sound_library, tool

Role = Literal["bass", "sub", "lead", "pad", "keys", "pluck", "bell", "arp", "strings", "brass"]
Character = Literal["bright", "dark", "punchy", "soft", "plucky", "sustained", "detuned"]
# A patch whose notes sit further apart than this, or drift this far while held, sounds
# out of tune (a pizzicato patch spread like that was heard as out of tune), unless detuned is
# the point.
IN_TUNE_CENTS = 15.0
# A held chord each audition ends with, in the role's register: an arpeggiator inside a
# patch shows itself on a chord (one held note it may just repeat).
CHORD_PROBE = {"bass": [36, 43, 48], "sub": [36, 43, 48], "lead": [60, 64, 67], "pad": [48, 55, 60, 64],
               "keys": [48, 55, 60, 64], "pluck": [55, 59, 62], "bell": [67, 71, 74], "arp": [55, 59, 62],
               "strings": [55, 59, 62, 67], "brass": [55, 59, 62]}

# How each role is auditioned (notes, seconds held) and what it should measure:
# attack_ms, richness (brightness relative to the note: centroid / fundamental),
# sustain_db (held level against the peak), decay_s (how fast it falls while held).
# Richness ranges are wide and calibrated on real synth patches (Arturia leads and basses
# measured 1.1-1.8): it separates a sub from a buzzy bass or a bell from a pad.
# "bright"/"dark" are judged against the other candidates instead (see audition_sounds).
ROLES: dict[str, dict] = {
    "bass": {"notes": [28, 36, 43], "seconds": 1.2, "attack_ms": (0, 25), "richness": (1.0, 4), "sustain_db": (-14, 0),
             "low_share": (0.35, 1.0)},
    "sub": {"notes": [28, 33, 40], "seconds": 1.2, "attack_ms": (0, 30), "richness": (0.8, 1.6), "sustain_db": (-10, 0),
            "low_share": (0.6, 1.0)},
    "lead": {"notes": [60, 67, 72], "seconds": 1.2, "attack_ms": (0, 25), "richness": (1.0, 6), "sustain_db": (-14, 0)},
    "pad": {"notes": [48, 55, 60], "seconds": 3.0, "attack_ms": (60, 1500), "richness": (0.8, 5), "sustain_db": (-10, 0)},
    "keys": {"notes": [48, 60, 67], "seconds": 2.0, "attack_ms": (0, 20), "richness": (1.0, 6), "decay_s": (0.3, 6)},
    "pluck": {"notes": [55, 62, 69], "seconds": 1.0, "attack_ms": (0, 15), "decay_s": (0.05, 0.6), "sustain_db": (-80, -15)},
    "bell": {"notes": [67, 72, 79], "seconds": 2.0, "attack_ms": (0, 15), "richness": (1.5, 12), "decay_s": (0.6, 8)},
    "arp": {"notes": [55, 62, 69], "seconds": 0.5, "attack_ms": (0, 15), "decay_s": (0.05, 1.2)},
    "strings": {"notes": [55, 62, 67], "seconds": 3.0, "attack_ms": (40, 700), "richness": (1.0, 5), "sustain_db": (-10, 0)},
    "brass": {"notes": [55, 62, 67], "seconds": 1.5, "attack_ms": (15, 150), "richness": (1.2, 6), "sustain_db": (-12, 0)},
}


def targets(role: str, character: list[str] | None = None) -> dict[str, tuple[float, float]]:
    """The measurement ranges a role should hit, moved by the character asked for."""
    t = {k: v for k, v in ROLES[role].items() if k not in ("notes", "seconds")}
    for c in character or []:
        if c == "punchy":
            t["attack_ms"] = (0, min(10, t.get("attack_ms", (0, 10))[1]))
        elif c == "soft":
            lo, hi = t.get("attack_ms", (0, 50))
            t["attack_ms"] = (max(lo, 25), max(hi, 300))
        elif c == "plucky":
            t["decay_s"], t["sustain_db"] = (0.05, 0.5), (-80, -15)
        elif c == "sustained":
            t["sustain_db"] = (-8, 0)
            t.pop("decay_s", None)
    return t


def summarise(results: list[dict]) -> dict:
    """One sound's measurements across the auditioned notes (medians)."""
    sounding = [r for r in results if not r.get("silent")]
    out: dict = {"silent_notes": len(results) - len(sounding)}
    for key in ("attack_ms", "richness", "sustain_db", "decay_s", "release_s", "peak_db"):
        values = [r[key] for r in sounding if r.get(key) is not None]
        if values:
            out[key] = round(float(statistics.median(values)), 2)
    from .listen import plays_pattern

    patterned = sum(1 for r in sounding if plays_pattern(r) or r.get("chord_moves"))
    if patterned:  # a built-in arpeggiator, sequencer or gate plays over the part's own notes
        out["plays_own_pattern"] = patterned
    cents = [r["cents_off"] for r in sounding if r.get("cents_off") is not None]
    if len(cents) >= 2:  # how far apart the notes are tuned (one in tune, one 20 cents flat)
        out["tuning_spread_cents"] = round(max(cents) - min(cents), 1)
    if cents:
        out["tuning_off_cents"] = round(float(statistics.median(abs(c) for c in cents)), 1)
    drifts = [abs(r["drift_cents"]) for r in sounding if r.get("drift_cents") is not None]
    if drifts:
        out["drift_cents"] = round(max(drifts), 1)
    lows = [r["bands"]["sub"] + r["bands"]["low"] for r in sounding if r.get("bands")]
    if lows:  # weight under 250 Hz: a bass that's all upper harmonics sounds thin in a mix
        out["low_share"] = round(float(statistics.median(lows)), 2)
    return out


def relative_brightness(ranked: list[dict], character: list[str] | None) -> None:
    """'bright' or 'dark' compared with the other candidates: the brightest (or darkest)
    of what's there scores best, as a producer flicking through patches would judge it."""
    want = next((c for c in character or [] if c in ("bright", "dark")), None)
    rich = [r["measured"]["richness"] for r in ranked if r.get("measured", {}).get("richness")]
    if not want or len(rich) < 2:
        return
    top, bottom = max(rich), min(rich)
    for r in ranked:
        v = r.get("measured", {}).get("richness")
        if not v:
            continue
        miss = math.log(top / v) if want == "bright" else math.log(v / bottom)
        if miss > 0.05:
            r["score"] = round(r["score"] + miss * 2, 3)
            r["why"] = r["why"] + [f"{'less bright' if want == 'bright' else 'brighter'} than the best of these"]


def score(measured: dict, wanted: dict[str, tuple[float, float]], detuned: bool = False) -> tuple[float, list[str]]:
    """Distance from the wanted ranges (0 = fits everything) and the reasons it's off.
    Times and brightness count by ratio (twice too slow is as far as half as slow);
    levels in dB by 6 dB steps; tuning by IN_TUNE_CENTS steps past IN_TUNE_CENTS (not
    when detuned is wanted). A sound with silent notes can't win."""
    if measured.get("silent_notes"):
        return 100.0 + measured["silent_notes"], [f"{measured['silent_notes']} test notes made no sound"]
    total, why = 0.0, []
    if measured.get("plays_own_pattern"):
        # The part's notes would be re-played as the patch's own arpeggio or sequence.
        total += 5.0
        why.append(f"plays a pattern of its own on {measured['plays_own_pattern']} held notes (a built-in "
                   "arpeggiator, sequencer or gate): turn it off in the plugin, or pick another sound")
    if not detuned:
        for key, label in (("tuning_spread_cents", "notes tuned"), ("tuning_off_cents", "off pitch by"),
                           ("drift_cents", "drifts")):
            v = measured.get(key)
            if v is not None and v > IN_TUNE_CENTS:
                total += (v - IN_TUNE_CENTS) / IN_TUNE_CENTS
                why.append(f"out of tune: {label} {v:g} cents (wanted under {IN_TUNE_CENTS:g})")
    for key, (lo, hi) in wanted.items():
        v = measured.get(key)
        if v is None:
            if key == "decay_s" and lo >= 0.3:
                continue  # it simply doesn't fall away while held: fine for a slow decay target
            total += 0.5
            continue
        if lo <= v <= hi:
            continue
        if key == "sustain_db":
            d = (lo - v if v < lo else v - hi) / 6
        elif key == "low_share":
            d = (lo - v if v < lo else v - hi) / 0.15
        else:
            # Times are measured in 5 ms steps (attack 0 means "under 5 ms"), so compare
            # from half a step: a 0 vs 60 ms attack mustn't outweigh everything else.
            floor = 2.5 if key == "attack_ms" else 1e-3
            edge = lo if v < lo else hi
            d = abs(math.log(max(v, floor) / max(edge, floor)))
        total += d
        why.append(f"{key.replace('_', ' ')} {v:g} (wanted {lo:g}-{hi:g})")
    return round(total, 3), why


def _apply(track, name: str, state: dict) -> None:
    """Loads a captured or saved plugin state onto the track: into the same plugin if
    it's there, otherwise swapping the track's instrument for it."""
    call("apply_fx_state", timeout=60.0, track=track, replace_instrument=True, sound_name=name, state=state)


def _spread(names: list[str], n: int) -> list[str]:
    """n names spread evenly through a list (a plugin's presets run by category)."""
    if len(names) <= n:
        return names
    return [names[round(i * (len(names) - 1) / (n - 1))] for i in range(n)] if n > 1 else names[:1]


def _instrument_index(track) -> int:
    return next(f["index"] for f in call("get_track_details", track=track).get("fx", []) if f.get("instrument"))


@tool()
def audition_sounds(
    track: TrackRef,
    role: Annotated[Role, Field(description="What the sound has to do in the song: bass, sub, lead, pad, keys, pluck, bell, arp, strings, brass")],
    character: Annotated[list[Character] | None, Field(description=(
        "How it should sound: bright, dark, punchy, soft, plucky, sustained; detuned when a wobbly or detuned "
        "sound is wanted (otherwise patches out of tune by more than 15 cents score worse)"))] = None,
    candidates: Annotated[Literal["presets", "library", "both"], Field(description=(
        "Where to look: the instrument's presets REAPER can see, the user's saved sounds, or both"))] = "both",
    search: Annotated[str | None, Field(description="Words in preset or sound names to narrow it, e.g. 'bass', 'warm pad'; default: candidates spread evenly through all of them")] = None,
    limit: Annotated[int, Field(ge=2, le=20, description="Most sounds to audition (each takes a few seconds)")] = 8,
    keep_best: Annotated[bool, Field(description="Leave the best sound loaded; False puts the original back")] = True,
    match_level: Annotated[bool, Field(description=(
        "Move the track fader so the chosen sound plays as loud as the original did (the mix balance stays)"))] = True,
) -> dict:
    """Finds the right sound for a part by listening, not by name: loads each candidate
    (the instrument's presets and/or the user's saved sounds), plays it the way the
    part will be played (low notes for a bass, held notes for a pad), measures attack,
    brightness, sustain, decay and tuning (notes out of tune with each other or drifting
    while held), scores it against what the role and character need,
    and keeps the best (or puts the original back). Use it before programming a sound
    from scratch. Plugins that keep presets in their own browser (Arturia) only offer
    saved sounds here. The track fader is moved so the chosen sound plays as loud as
    the original did (match_level). Returns the ranking with the measurements behind
    it."""
    track_info = call("get_track_details", track=track)
    fx = next((f for f in track_info.get("fx", []) if f.get("instrument")), None)
    if fx is None:
        raise ValueError("that track has no instrument to audition sounds on")
    # By listening, not by name: without search words, candidates are spread evenly
    # through everything (a role word in preset names misses most of them: "keys" finds
    # no Grand Piano, Rhodes or Clav).
    words = search
    presets: list[str] = []
    sounds: list[str] = []
    preset_note = None
    if candidates in ("presets", "both"):
        listed = call("list_fx_presets", timeout=120.0, track=track, fx=fx["index"], search=words,
                      limit=limit if words else 500)
        presets = [p["name"] if isinstance(p, dict) else str(p) for p in listed.get("presets", [])]
        preset_note = listed.get("note")
    if candidates in ("library", "both"):
        sounds = [e["name"] for e in sound_library.search(words, None, None, "instrument")]
    if presets and sounds:  # both: half each, so presets don't crowd out the user's own sounds
        take_sounds = min(len(sounds), max(limit // 2, limit - len(presets)))
        pool = ([{"kind": "preset", "name": n} for n in _spread(presets, limit - take_sounds)]
                + [{"kind": "sound", "name": n} for n in _spread(sounds, take_sounds)])
    else:
        pool = ([{"kind": "preset", "name": n} for n in _spread(presets, limit)]
                + [{"kind": "sound", "name": n} for n in _spread(sounds, limit)])
    if not pool:
        raise ValueError(f"no sounds to audition{f' for {words!r}' if words else ''}"
                         + (f" ({preset_note})" if preset_note else "")
                         + "; save some with save_sound, try other search words, or program one with set_fx_parameters")
    from .music_tools import _listen

    original = call("capture_fx_state", timeout=60.0, track=track, fx=fx["index"])
    spec = ROLES[role]
    wanted = targets(role, character)
    ranked = []
    # Audition the patch, not the track's effects: a reverb made every candidate sound
    # sustained, a compressor flattened their attacks. Bypassed now, re-enabled after.
    bypassed = [f["name"] for f in track_info.get("fx", [])
                if f["index"] > fx["index"] and not f.get("instrument") and "(bypassed)" not in f["name"]]
    for name in bypassed:
        call("update_fx", track=track, fx=name, enabled=False)
    base_level = None
    try:
        if match_level and keep_best:
            base = summarise(_listen(track, spec["notes"], 1, spec["seconds"], 1.0, 100)[0])
            base_level = base.get("peak_db")
        for c in pool:
            try:
                if c["kind"] == "preset":
                    loaded = call("update_fx", track=track, fx=fx["index"], preset=c["name"])
                    if loaded.get("warning"):  # it didn't load: measuring now would credit the last sound
                        raise ValueError(loaded["warning"])
                else:
                    _, entry = sound_library.find(c["name"])
                    _apply(track, entry["name"], sound_library.state(entry))
                results, context = _listen(track, spec["notes"], 1, spec["seconds"], 1.0, 100,
                                           chord=CHORD_PROBE[role])
                if listen.plays_pattern(context.get("chord_motion") or {}):
                    results[0]["chord_moves"] = True  # counted by summarise
            except Exception as e:  # noqa: BLE001 - one bad candidate shouldn't stop the audition
                ranked.append({**c, "score": 999.0, "why": [f"couldn't audition it: {e}"]})
                continue
            measured = summarise(results)
            s, why = score(measured, wanted, detuned="detuned" in (character or []))
            ranked.append({**c, "score": s, "measured": measured, "why": why})
    finally:
        relative_brightness(ranked, character)
        ranked.sort(key=lambda r: r["score"])
        best = ranked[0] if ranked and ranked[0]["score"] < 100 else None
        # Back to the original plugin and sound first (a saved sound may have swapped
        # the instrument), then the winner on top of it.
        _apply(track, "original sound", original)
        if keep_best and best and best["kind"] == "preset":
            call("update_fx", track=track, fx=_instrument_index(track), preset=best["name"])
        elif keep_best and best:
            _, entry = sound_library.find(best["name"])
            _apply(track, entry["name"], sound_library.state(entry))
        for name in bypassed:
            try:
                call("update_fx", track=track, fx=name, enabled=True)
            except Exception:  # noqa: BLE001 - keep restoring the rest
                pass
    matched = None
    if keep_best and best and base_level is not None and best.get("measured", {}).get("peak_db") is not None:
        # Patches differ by 10 dB or more in output: keep the track as loud as before.
        gain = max(-12.0, min(12.0, base_level - best["measured"]["peak_db"]))
        if abs(gain) >= 1.0:
            now = call("get_track_details", track=track).get("volume_db") or 0.0
            call("set_track_properties", track=track, volume_db=round(min(12.0, now + gain), 1))
            matched = round(gain, 1)
    return {"role": role, "character": character or [], "wanted": {k: list(v) for k, v in wanted.items()},
            **({"effects_bypassed_while_listening": bypassed} if bypassed else {}),
            **({"fader_moved_db_to_match_level": matched} if matched is not None else {}),
            "loaded": best["name"] if (keep_best and best) else "the original sound",
            "ranking": [{k: r[k] for k in ("kind", "name", "score", "why", "measured") if k in r} for r in ranked]}


@tool(annotations=READ_ONLY)
def find_arturia_presets(
    type: Annotated[str | None, Field(description="Bass, Pad, Lead, Keys, Electric Piano, Piano, Organ, Strings, Brass & Winds, Sequence, Drums, Vocal, Sound Effects")] = None,
    subtype: Annotated[str | None, Field(description="e.g. 'Sub Bass', 'Evolving Pad', 'Big Lead', 'Plucked Keys', 'Classic EP' (part of the name is enough)")] = None,
    characteristics: Annotated[list[str] | None, Field(description="Sound words the preset must all have, e.g. ['warm', 'wide'], ['dark', 'punchy'], ['analog']")] = None,
    genre: Annotated[str | None, Field(description="A genre tag, e.g. 'synthwave', 'house', 'hip hop', 'cinematic', 'techno'")] = None,
    instrument: Annotated[str | None, Field(description="Only this Arturia instrument, e.g. 'Jup-8 V4', 'Mini V3', 'CMI'")] = None,
    search: Annotated[str | None, Field(description="Words in the preset's name or description")] = None,
    installed_only: Annotated[bool, Field(description="Only presets for Arturia plugins installed in REAPER")] = True,
    patterns: Annotated[bool, Field(description=(
        "Include presets that play a pattern of their own (arpeggiated, sequenced, gated); only when the part "
        "should be that pattern, since any notes written on them are re-played by it"))] = False,
    limit: Annotated[int, Field(ge=1, le=100)] = 20,
) -> dict:
    """Finds sounds in Arturia's factory library (about 15,000 presets across the user's
    Arturia instruments) by what they are, the way a producer browses: type and subtype
    (Bass > Sub Bass), sound characteristics (warm, dark, wide, analog, punchy...) and
    genre tags. Start here for any part before programming a synth from scratch: a
    designed factory preset sounds finished where a patch built from a default rarely
    does. Each result names its plugin and where it sits in the plugin's browser.
    With no matches it returns the words the library knows. Read-only."""
    from . import arturia

    conn = arturia.connect()
    try:
        installed, note = None, None
        if installed_only:
            try:
                listed = call("list_installed_fx", developer="Arturia", limit=1000).get("plugins", [])
                installed = {arturia.normalize_plugin(p.get("name", "")) for p in listed}
            except Exception as e:  # noqa: BLE001 - still useful without REAPER's plugin list
                note = f"couldn't read the installed plugins ({e}), so presets for every Arturia instrument are listed"
        found = arturia.find(conn, instrument, type, subtype, characteristics, genre, search, installed, limit,
                             patterns)
        out: dict = {"count": len(found), "presets": found}
        if not found:
            out["known_words"] = arturia.vocabulary(conn)
            out["tip"] = "nothing matched every filter: drop one, or use the library's own words above"
    finally:
        conn.close()
    if note:
        out["note"] = note
    out["how_to_use"] = ("creaper can't load these presets itself yet: add the plugin (create_track or add_fx with "
                         "its name), open its window (update_fx show) and ask the user to pick the preset at "
                         "browser_path, then audition_instrument to check it and save_sound it so audition_sounds "
                         "can try it next time")
    return out
