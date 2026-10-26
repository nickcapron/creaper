"""Choosing sounds by audition: instead of picking a preset by its name, creaper loads
each candidate, plays it the way the part will be played (low notes for a bass, held
notes for a pad), measures what comes out and keeps the one that best fits the role
and the character asked for. The same way a producer flicks through patches, but
measured, because Claude can't hear."""

from __future__ import annotations

import math
import statistics
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from . import listen
from .server import READ_ONLY, TrackRef, call, sound_library, tool

Role = Literal["bass", "sub", "lead", "pad", "keys", "pluck", "bell", "arp", "strings", "brass"]
Character = Literal["bright", "dark", "punchy", "soft", "plucky", "sustained", "detuned", "wide", "thick", "moving"]
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
    if role in ROLE_TAIL_S:
        t["release_s"] = (0, ROLE_TAIL_S[role])
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
            t.pop("release_s", None)
        elif c == "wide":
            t["width_db"] = (-12, 0)
        elif c == "thick":
            t["partials"] = (15, 10000)
        elif c == "moving":
            t["brightness_motion_oct"] = (0.15, 5)
    return t


# Longest ring after the note-off (s) before a part sounds washed out: the reverb or
# delay inside a patch smears a bass line or a chop. Pads, strings and bells may ring.
ROLE_TAIL_S = {"bass": 0.6, "sub": 0.6, "lead": 1.2, "keys": 2.0, "pluck": 1.0, "arp": 0.8, "brass": 1.0}


def summarise(results: list[dict]) -> dict:
    """One sound's measurements across the auditioned notes (medians)."""
    sounding = [r for r in results if not r.get("silent")]
    out: dict = {"silent_notes": len(results) - len(sounding)}
    for key in ("attack_ms", "richness", "sustain_db", "decay_s", "release_s", "peak_db", "level_db", "width_db",
                "brightness_motion_oct", "level_motion_db", "partials"):
        values = [r[key] for r in sounding if r.get(key) is not None]
        if values:
            out[key] = round(float(statistics.median(values)), 2)
    from .listen import plays_pattern

    from .listen import transposition

    shifted = transposition(sounding)
    if shifted:
        out["transposed_semitones"] = shifted
    ringing = sum(1 for r in sounding if "release_s" in r and r["release_s"] is None)
    if ringing:  # measured, and still sounding a second after the note-off
        out["rings_on"] = ringing
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
    if measured.get("transposed_semitones"):
        # Every part would play in another key.
        total += 5.0
        why.append(f"sounds {measured['transposed_semitones']:+d} semitones from the notes played (the patch is "
                   "tuned to another key): fix its tune/transpose control or pick another sound")
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
        if key == "release_s" and measured.get("rings_on"):
            total += 1.0
            why.append(f"rings on past the note on {measured['rings_on']} notes (wanted under {hi:g} s): reverb or "
                       "delay in the patch; turn it down in the plugin or use a send")
            continue
        if v is None:
            if key == "decay_s" and lo >= 0.3:
                continue  # it simply doesn't fall away while held: fine for a slow decay target
            if key == "release_s":
                continue  # not measured
            total += 0.5
            continue
        if lo <= v <= hi:
            continue
        if key == "sustain_db":
            d = (lo - v if v < lo else v - hi) / 6
        elif key == "low_share":
            d = (lo - v if v < lo else v - hi) / 0.15
        elif key == "width_db":
            d = (lo - v if v < lo else v - hi) / 6
        elif key == "partials":
            d = abs(math.log(max(v, 1) / (lo if v < lo else hi)))
        elif key == "brightness_motion_oct":
            d = (lo - v) / 0.1 if v < lo else 0.0
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


# What Arturia's library calls each role (type, subtype words), for candidates="arturia".
ROLE_TYPES: dict[str, tuple[str, str | None]] = {
    "bass": ("Bass", None), "sub": ("Bass", "Sub"), "lead": ("Lead", None), "pad": ("Pad", None),
    "keys": ("Keys", None), "pluck": ("Keys", "Pluck"), "bell": ("Keys", "Bell"), "arp": ("Lead", "Pluck"),
    "strings": ("Strings", None), "brass": ("Brass", None),
}


def _installed_arturia() -> dict[str, str]:
    """Installed Arturia plugins: normalized name -> the name REAPER loads them by."""
    from . import arturia

    listed = call("list_installed_fx", developer="Arturia", limit=1000).get("plugins", [])
    return {arturia.normalize_plugin(p.get("name", "")): p.get("load_as") or p.get("name") for p in listed}


def _arturia_state(preset: dict, installed: dict[str, str]) -> dict:
    """A plugin state that loads an Arturia preset file (see arturia.preset_chunk)."""
    from . import arturia

    load_as = installed.get(arturia.normalize_plugin(preset["plugin"]))
    if not load_as:
        raise ValueError(f"{preset['plugin']} isn't installed in REAPER, so its presets can't be loaded")
    return {"plugin": load_as, "file": "", "instrument": True, "chunk": arturia.preset_chunk(preset["path"])}


def _by_plugin(found: list[dict], n: int, seed: int = 0) -> list[dict]:
    """n presets taken in turn from each instrument (the library lists by name, so the
    first n would all start with 'A' and come from whichever plugin has most). The seed
    shuffles each instrument's list first: another seed, another set to try."""
    import random

    groups: dict[str, list[dict]] = {}
    for p in found:
        groups.setdefault(p["plugin"], []).append(p)
    rng = random.Random(seed)
    for g in groups.values():
        if seed:
            rng.shuffle(g)
    # Each instrument offers up to n, spread through its list; they take turns, so one
    # with few presets leaves its turns to the others.
    lists = [_spread(g, n) for g in groups.values()]
    out: list[dict] = []
    while len(out) < n and any(lists):
        for g in lists:
            if g and len(out) < n:
                out.append(g.pop(0))
    return out


AUDITION_LEGEND = (
    "score: 0 fits everything, lower is better; why: what's off. measured: attack_ms, sustain_db, decay_s, "
    "release_s (ring after the note-off; rings_on = notes still sounding a second later: reverb or delay in the "
    "patch), level_db (loudness while held), low_share (weight under 250 Hz), width_db (side against mid: -40 "
    "mono, -15 slight, -6 and up wide), partials (spectral peaks: under 8 thin, 15+ thick), brightness_motion_oct "
    "(0 static, 0.15+ moving), tuning_spread_cents / drift_cents, plays_own_pattern, transposed_semitones")


def _spread(names: list, n: int) -> list:
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
        "How it should sound: bright, dark, punchy, soft, plucky, sustained; wide (stereo spread), thick (many "
        "partials: unison, saw stacks), moving (a filter or LFO changes it while held); detuned when a wobbly or "
        "detuned sound is wanted (otherwise patches out of tune by more than 15 cents score worse)"))] = None,
    candidates: Annotated[Literal["presets", "library", "both", "arturia"], Field(description=(
        "Where to look: the instrument's presets REAPER can see, the user's saved sounds, both, or arturia: "
        "factory presets from Arturia's library for every installed Arturia instrument, chosen by the role "
        "(and type, subtype, characteristics, genre); the track's instrument is swapped for each"))] = "both",
    search: Annotated[str | None, Field(description="Words in preset or sound names to narrow it, e.g. 'bass', 'warm pad'; default: candidates spread evenly through all of them")] = None,
    limit: Annotated[int, Field(ge=2, le=20, description="Most sounds to audition (each takes a few seconds)")] = 8,
    keep_best: Annotated[bool, Field(description="Leave the best sound loaded; False puts the original back")] = True,
    match_level: Annotated[bool, Field(description=(
        "Move the track fader so the chosen sound plays as loud as the original did (the mix balance stays)"))] = True,
    type: Annotated[str | None, Field(description="arturia: the library's type instead of the role's (Bass, Pad, Lead, Keys, Electric Piano, Organ, Strings...)")] = None,
    subtype: Annotated[str | None, Field(description="arturia: e.g. 'Sub Bass', 'Evolving Pad', 'Classic EP'")] = None,
    characteristics: Annotated[list[str] | None, Field(description="arturia: sound words every candidate must have, e.g. ['warm', 'analog']")] = None,
    genre: Annotated[str | None, Field(description=(
        "arturia: the library's own genre tag (find_arturia_presets known_words, e.g. '80s', 'Synthwave'); "
        "usually leave it and give style, the song's genre"))] = None,
    seed: Annotated[int, Field(ge=0, description="arturia: another number draws another set of candidates")] = 0,
    style: Annotated[str | None, Field(description=(
        "arturia: the song's genre (list_genres); its sound palette (get_genre_profile) fills in the type, "
        "subtype, characteristics and genre tag for this role. Anything you give wins (an explicit type drops the "
        "palette's subtype); if nothing matches, the search loosens: subtype, then sound words, then genre tag"))] = None,
) -> dict:
    """Finds the right sound for a part by listening, not by name: loads each candidate
    (the instrument's presets and/or the user's saved sounds), plays it the way the
    part will be played (low notes for a bass, held notes for a pad), measures attack,
    brightness, sustain, decay and tuning (notes out of tune with each other or drifting
    while held), scores it against what the role and character need,
    and keeps the best (or puts the original back). Use it before programming a sound
    from scratch. Arturia's presets live in its own browser: candidates="arturia" loads
    them straight from Arturia's library instead, across every installed Arturia
    instrument. Patches that play a pattern of their own (a built-in arpeggiator or
    sequence) or are tuned to another key score far down. The track fader is moved so
    the chosen sound plays as loud as the original did, by its loudness while held
    (match_level). Returns the ranking with the measurements behind it."""
    track_info = call("get_track_details", track=track)
    fx = next((f for f in track_info.get("fx", []) if f.get("instrument")), None)
    if fx is None and candidates != "arturia":
        raise ValueError("that track has no instrument to audition sounds on (candidates='arturia' loads its own)")
    arturia_only = [name for name, v in (("type", type), ("subtype", subtype), ("characteristics", characteristics),
                                         ("genre", genre), ("style", style)) if v] + (["seed"] if seed else [])
    if arturia_only and candidates != "arturia":
        raise ValueError(f"{', '.join(arturia_only)} only apply with candidates='arturia'")
    # By listening, not by name: without search words, candidates are spread evenly
    # through everything (a role word in preset names misses most of them: "keys" finds
    # no Grand Piano, Rhodes or Clav).
    words = search
    presets: list[str] = []
    sounds: list[str] = []
    preset_note = None
    pool: list[dict] = []
    installed: dict[str, str] = {}
    if candidates == "arturia":
        from . import arturia

        installed = _installed_arturia()
        role_type, role_subtype = ROLE_TYPES[role]
        wanted_sound = None
        if style:
            from . import genres
            from .genres import palettes

            wanted_sound = palettes.sound_for(genres.find(style), role)
        t = type or (wanted_sound.type if wanted_sound else role_type)
        st = subtype or (wanted_sound.subtype if wanted_sound and not type else None if type else role_subtype)
        ch = characteristics if characteristics is not None else (list(wanted_sound.characteristics)
                                                                    if wanted_sound else None)
        gt = genre or (wanted_sound.genre if wanted_sound else None)
        conn = arturia.connect()
        try:
            # Loosen the search until something matches: the subtype first, then the
            # sound words, then the genre tag, but only what the palette or the role filled
            # in: the caller's own words stay in every try.
            tries = [(st, ch, gt)]
            st_, ch_, gt_ = st, ch, gt
            for given, which in ((subtype, 0), (characteristics, 1), (genre, 2)):
                if given is None and (st_, ch_, gt_)[which]:
                    st_, ch_, gt_ = [None if k == which else v for k, v in enumerate((st_, ch_, gt_))]
                    tries.append((st_, ch_, gt_))
            found = []
            for st_, ch_, gt_ in tries:
                found = arturia.find(conn, None, t, st_, ch_, gt_, words, set(installed), limit=400)
                if found:
                    break
        finally:
            conn.close()
        pool = [{"kind": "arturia", "name": p["name"], "plugin": p["plugin"], "browser_path": p["browser_path"],
                 "_preset": p} for p in _by_plugin(found, limit, seed)]
        if not pool:
            raise ValueError("no Arturia presets match that for the installed instruments; drop a filter, or "
                             "find_arturia_presets to see the library's words")
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
    elif not pool:
        pool = ([{"kind": "preset", "name": n} for n in _spread(presets, limit)]
                + [{"kind": "sound", "name": n} for n in _spread(sounds, limit)])
    if not pool:
        raise ValueError(f"no sounds to audition{f' for {words!r}' if words else ''}"
                         + (f" ({preset_note})" if preset_note else "")
                         + "; save some with save_sound, try other search words, or program one with set_fx_parameters")
    from .music_tools import _listen

    # A bare track: candidates bring their own instrument, and nothing kept means none again.
    original = call("capture_fx_state", timeout=60.0, track=track, fx=fx["index"]) if fx else None
    spec = ROLES[role]
    wanted = targets(role, character)
    ranked = []
    # Audition the patch, not the track's effects: a reverb made every candidate sound
    # sustained, a compressor flattened their attacks. Bypassed now, re-enabled after.
    bypassed = [f["name"] for f in track_info.get("fx", [])
                if f["index"] > (fx["index"] if fx else 0) and not f.get("instrument") and "(bypassed)" not in f["name"]]
    for name in bypassed:
        call("update_fx", track=track, fx=name, enabled=False)
    base_level = None
    try:
        if match_level and keep_best and fx:
            base = summarise(_listen(track, spec["notes"], 1, spec["seconds"], 1.0, 100)[0])
            base_level = base.get("level_db", base.get("peak_db"))
        for c in pool:
            try:
                if c["kind"] == "preset":
                    loaded = call("update_fx", track=track, fx=fx["index"], preset=c["name"])
                    if loaded.get("warning"):  # it didn't load: measuring now would credit the last sound
                        raise ValueError(loaded["warning"])
                elif c["kind"] == "arturia":
                    _apply(track, c["name"], _arturia_state(c["_preset"], installed))
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
        if original:
            _apply(track, "original sound", original)
        elif not (keep_best and best):
            added = next((f for f in call("get_track_details", track=track).get("fx", []) if f.get("instrument")), None)
            if added:
                call("remove_fx", track=track, fx=added["index"])
        if keep_best and best and best["kind"] == "preset":
            call("update_fx", track=track, fx=_instrument_index(track), preset=best["name"])
        elif keep_best and best and best["kind"] == "arturia":
            _apply(track, best["name"], _arturia_state(best["_preset"], installed))
        elif keep_best and best:
            _, entry = sound_library.find(best["name"])
            _apply(track, entry["name"], sound_library.state(entry))
        for name in bypassed:
            try:
                call("update_fx", track=track, fx=name, enabled=True)
            except Exception:  # noqa: BLE001 - keep restoring the rest
                pass
    matched = None
    best_level = (best or {}).get("measured", {}).get("level_db", (best or {}).get("measured", {}).get("peak_db"))
    if keep_best and best and base_level is not None and best_level is not None:
        # Patches differ by 10 dB or more in output: keep the track as loud as before.
        gain = max(-12.0, min(12.0, base_level - best_level))
        if abs(gain) >= 1.0:
            now = call("get_track_details", track=track).get("volume_db") or 0.0
            call("set_track_properties", track=track, volume_db=round(min(12.0, now + gain), 1))
            matched = round(gain, 1)
    return {"role": role, "character": character or [], "wanted": {k: list(v) for k, v in wanted.items()},
            **({"effects_bypassed_while_listening": bypassed} if bypassed else {}),
            **({"fader_moved_db_to_match_level": matched} if matched is not None else {}),
            "loaded": best["name"] if (keep_best and best) else "the original sound",
            "ranking": [{k: r[k] for k in ("kind", "name", "plugin", "score", "why", "measured") if k in r}
                        for r in ranked],
            "how_to_read": AUDITION_LEGEND}


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
    genre tags. Browse here to see what the library has; audition_sounds(candidates=
    "arturia") is the usual way to choose, by listening. A designed factory preset
    sounds finished where a patch built from a default rarely does. Each result names its plugin and where it sits in the plugin's browser;
    load_arturia_preset loads one, audition_sounds(candidates="arturia") picks among
    them by listening. With no matches it returns the words the library knows.
    Read-only."""
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
        found = [{k: v for k, v in p.items() if k != "path"}
                 for p in arturia.find(conn, instrument, type, subtype, characteristics, genre, search, installed, limit,
                                       patterns)]
        out: dict = {"count": len(found), "presets": found}
        if not found:
            out["known_words"] = arturia.vocabulary(conn)
            out["tip"] = "nothing matched every filter: drop one, or use the library's own words above"
    finally:
        conn.close()
    if note:
        out["note"] = note
    out["how_to_use"] = ("load_arturia_preset(track, preset=<browser_path>) loads one and checks it by ear; "
                         "audition_sounds(candidates='arturia', role=..., type/subtype/characteristics/genre) "
                         "auditions several and keeps the best fit; save_sound the ones that work in the song")
    return out


@tool()
def load_arturia_preset(
    track: TrackRef,
    preset: Annotated[str, Field(description=(
        "The preset's name ('Doomsday Sub') or its browser_path from find_arturia_presets "
        "('Jup-8 V4 > Factory > Doomsday Sub')"))],
    plugin: Annotated[str | None, Field(description="The Arturia instrument, when several have a preset of that name")] = None,
    check: Annotated[bool, Field(description=(
        "Then listen to it (audition_instrument on a few notes and a chord): its tuning, and whether it plays a "
        "pattern of its own"))] = True,
) -> dict:
    """Loads an Arturia factory preset onto a track, straight from Arturia's library: the
    track's Arturia instrument takes it, or the instrument is swapped for the preset's
    (one undo step). Find presets with find_arturia_presets, or let audition_sounds
    (candidates="arturia") choose by listening. It confirms the plugin took the preset
    and, with check, listens for a patch tuned to another key or playing a built-in
    arpeggio or sequence. save_sound it once it works in the song."""
    from . import arturia

    installed = _installed_arturia()
    conn = arturia.connect()
    try:
        found = arturia.resolve(conn, preset, plugin, set(installed))
        found["browser_path"] = next((p["browser_path"] for p in arturia.find(conn, search=found["name"],
                                                                                instrument=found["plugin"], limit=5,
                                                                                patterns=True)
                                      if p["name"] == found["name"]), f"{found['plugin']} > {found['name']}")
    finally:
        conn.close()
    _apply(track, found["name"], _arturia_state(found, installed))
    after = call("capture_fx_state", timeout=60.0, track=track)
    holds = arturia.chunk_preset_name(after.get("chunk"))
    out: dict = {"track": track, "plugin": after.get("plugin"), "preset": found["name"],
                 "browser_path": found["browser_path"],
                 "confirmed": holds == found["name"]}
    if holds != found["name"]:
        out["warning"] = (f"the plugin reports '{holds}' after loading, not '{found['name']}': it may not have taken "
                          "the preset; open its window (update_fx show) to check")
    if check:
        from .music_tools import audition_instrument

        heard = audition_instrument(track=track, notes=["C2", "C3", "C4"], note_seconds=1.2)
        out["sound"] = heard.get("summary")
        for key in ("warning", "tuning_warning", "transposed_warning"):
            if heard.get(key):
                out.setdefault("problems", []).append(heard[key])
        slow = _swells_where_it_should_speak(track, out["sound"])
        if slow:
            out.setdefault("problems", []).append(slow)
    return out


SPEAKING_ATTACK_MS = 120.0   # a hook, bass or strummed part has to land on the beat


def _swells_where_it_should_speak(track, summary: dict | None) -> str | None:
    """A preset whose notes swell in (a pad) on a track whose name says lead, bass, guitar
    or keys: the Jup-8 'Harmonica' (264 ms attack, dark) went on a country song's hook track
    by name and buried it."""
    from . import mix_tools

    attack = (summary or {}).get("median_attack_ms")
    role = mix_tools.role_of(str(track))
    if attack is None or role not in ("lead", "bass", "guitar", "keys") or attack <= SPEAKING_ATTACK_MS:
        return None
    return (f"its notes swell in over {attack:g} ms (a pad), but a {role} part has to speak on the beat: a hook or "
            "bass played this way blurs and sinks. Pick a preset with a quick attack (find_arturia_presets by type, "
            "or audition_sounds with character 'plucky' or 'sharp'), or use this sound as the pad")


# ------------------------------------------------------------------- layering

LAYERED = " (layered)"  # a folder named "<part> (layered)" is one part: mixed and measured as one


class SoundLayer(BaseModel):
    instrument: str | None = Field(None, description="A plugin to load, e.g. 'Mini V3', 'ReaSynth'")
    arturia_preset: str | None = Field(None, description="Or an Arturia factory preset (name or browser_path)")
    sound: str | None = Field(None, description="Or one of the user's saved sounds (list_sounds)")
    octave: int = Field(0, ge=-3, le=3, description="Play it this many octaves up or down")
    volume_db: float = Field(-6.0, ge=-40, le=6, description="Its level under the main sound")
    pan: float = Field(0.0, ge=-1, le=1)
    highpass_hz: float | None = Field(None, ge=20, le=1000, description="Cut its lows (e.g. 120 for a mid layer over a sub)")
    lowpass_hz: float | None = Field(None, ge=100, le=20000, description="Cut its highs (e.g. 200 for a sub layer)")
    name: str | None = Field(None, description="Track name; default from the part and the sound")


# REAPER's own filters. The RBJ filter's high pass reaches 1000 Hz but its low pass stops
# at 1000 Hz, so a sub layer's low pass is the Resonant Lowpass (20 Hz-20 kHz), with its
# resonance down so it doesn't add a peak.
HIGHPASS_FX, HIGHPASS_PARAM = "JS: RBJ Highpass/Lowpass Filters", "HPF"
LOWPASS_FX, LOWPASS_PARAM = "JS: Resonant Lowpass Filter", "Frequency (Hz)"


def _filters(track, highpass_hz: float | None, lowpass_hz: float | None) -> list[str]:
    """A high and/or low pass after the layer's instrument (an EQ before a synth does
    nothing), read back so a value the plugin couldn't take is reported, not hidden."""
    if not highpass_hz and not lowpass_hz:
        return []
    done = []
    for hz, name, param, extra, label in (
            (highpass_hz, HIGHPASS_FX, HIGHPASS_PARAM, [], "high pass"),
            (lowpass_hz, LOWPASS_FX, LOWPASS_PARAM, [{"parameter": "Resonance", "display_value": 0.1}], "low pass")):
        if not hz:
            continue
        fx = call("get_track_details", track=track).get("fx", [])
        last = max((f["index"] for f in fx if f.get("instrument")), default=0)
        flt = call("add_fx", track=track, name=name, position=last + 1 + len(done))
        # The low pass slider runs linearly 20-20000 Hz: set its exact position (finding it
        # by display value lands on a coarse step, 200 for 180).
        setting = ({"parameter": param, "value": (hz - 20) / 19980} if name == LOWPASS_FX
                   else {"parameter": param, "display_value": hz})
        call("set_fx_parameters", track=track, fx=flt["index"], changes=[setting] + extra)
        got = next((p for p in call("get_fx_parameters", track=track, fx=flt["index"], search=param)["parameters"]
                    if p["name"] == param), None)
        try:
            value = float(str(got["display"]).split()[0]) if got else None
        except ValueError:
            value = None
        if value is None or abs(value - hz) <= 0.5:
            done.append(f"{label} {hz:g} Hz")
        elif abs(value - hz) <= max(25.0, 0.15 * hz):
            # The plugin keeps its cutoff in coarse steps (200 for 180): close enough to hear the same.
            done.append(f"{label} {value:g} Hz (the filter's nearest to {hz:g})")
        else:
            done.append(f"{label} wanted {hz:g} Hz but {name} set {value:g} Hz: set it by hand")
    return done


@tool()
def layer_instrument(
    track: TrackRef,
    layers: Annotated[list[SoundLayer], Field(min_length=1, max_length=4, description=(
        "Sounds to play with the track's part: each loads an instrument, an Arturia preset or a saved sound, with "
        "its own octave, level, pan and filters. E.g. a bass: [{'instrument': 'ReaSynth', 'octave': -1, "
        "'lowpass_hz': 180, 'volume_db': -4}]"))],
) -> dict:
    """Thickens one part with layers that play its notes: a sub under a bass, a second
    pad high-passed and wide, an octave-down double under a lead. Each layer is its own
    track that gets the part's MIDI (a MIDI-only send) through its own instrument,
    octave, level, pan and filters; the part and its layers go in a folder named
    '<part> (layered)', which auto_mix and measure_tracks treat as one part (to duck it,
    setup_sidechain on the folder track). Edit the part's notes as usual: the layers
    follow. To change a layer: set_track_properties (level, pan), set_fx_parameters on
    its 'JS: RBJ Highpass/Lowpass Filters' (HPF, Hz), 'JS: Resonant Lowpass Filter'
    (Frequency (Hz)) or 'JS: MIDI Transpose Notes'; to drop one, delete its track. Keep the folder's ' (layered)' name: the
    mixing tools go by it. Several undo steps."""
    details = call("get_track_details", track=track)
    part = details["name"]
    if not [i for i in details.get("items", []) if i.get("type") == "midi"]:
        raise ValueError(f"'{part}' has no MIDI part for the layers to play")
    number = details.get("number") or details.get("track", {}).get("number")
    installed = None
    made = []
    for i, layer in enumerate(layers, 1):
        if sum(bool(x) for x in (layer.instrument, layer.arturia_preset, layer.sound)) != 1:
            raise ValueError("give each layer exactly one of instrument, arturia_preset or sound")
        label = layer.name or f"{part} layer {i}"
        if label == part:
            raise ValueError(f"a layer can't be named '{part}', the part's own name")
        made_track = call("create_track", name=label, instrument=layer.instrument or "ReaSynth",
                          position=(number + i) if number else None)
        # Its GUID, not its name: another track may already be called that.
        target = (made_track.get("track") or {}).get("guid") or label
        if layer.arturia_preset:
            installed = installed or _installed_arturia()
            from . import arturia

            conn = arturia.connect()
            try:
                found = arturia.resolve(conn, layer.arturia_preset, None, set(installed))
            finally:
                conn.close()
            _apply(target, found["name"], _arturia_state(found, installed))
            what = found["name"]
        elif layer.sound:
            _, entry = sound_library.find(layer.sound)
            _apply(target, entry["name"], sound_library.state(entry))
            what = entry["name"]
        else:
            what = layer.instrument
        if layer.octave:
            tr = call("add_fx", track=target, name="JS: MIDI Transpose Notes", position=1)
            call("set_fx_parameters", track=target, fx=tr["index"],
                 changes=[{"parameter": "Transpose Semitones", "display_value": 12 * layer.octave}])
        filters = _filters(target, layer.highpass_hz, layer.lowpass_hz)
        call("set_track_properties", track=target, volume_db=layer.volume_db, pan=layer.pan)
        call("set_send", source=track, destination=target, midi_only=True)
        made.append({"track": label, "_ref": target, "sound": what, "octave": layer.octave,
                     "volume_db": layer.volume_db,
                     "pan": layer.pan, **({"filters": filters} if filters else {})})
    folder = call("create_folder", tracks=[track] + [m.pop("_ref") for m in made], name=part + LAYERED)
    return {"part": part, "folder": folder.get("folder", {}).get("name", part + LAYERED), "layers": made,
            "note": "the layers play the part's MIDI; mute a layer track to hear without it"}
